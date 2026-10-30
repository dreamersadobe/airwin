"""Central manager for AirPods connection, battery state, ear detection, and ANC."""

import logging
import threading
import time
from typing import Callable, Optional

from airwin.config import AppConfig
from airwin.core.ble_scanner import BLEAirPodsScanner
from airwin.core.models import AirPodsModel, AirPodsState, NoiseControlMode
from airwin.core.windows_audio import AudioController
from airwin.core.windows_bluetooth import WindowsBluetoothWatcher

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages AirPods life cycle, BLE telemetry, ear detection, and OS audio triggers."""

    def __init__(
        self,
        config: AppConfig,
        on_state_changed: Optional[Callable[[AirPodsState], None]] = None,
        on_case_opened: Optional[Callable[[AirPodsState], None]] = None,
    ):
        self.config = config
        self.on_state_changed = on_state_changed
        self.on_case_opened = on_case_opened

        self.audio = AudioController()
        self.current_state: Optional[AirPodsState] = None
        self._previous_state: Optional[AirPodsState] = None

        self._scanner: Optional[BLEAirPodsScanner] = None
        self._win_bt_watcher: Optional[WindowsBluetoothWatcher] = None
        self._demo_thread: Optional[threading.Thread] = None
        self._demo_running = False

    def start(self) -> None:
        """Starts monitoring either in live BLE & Windows mode or demo mode."""
        if self.config.demo_mode:
            self.start_demo_mode()
        else:
            # 1. Start Windows Bluetooth Watcher for real-time paired device connection status
            self._win_bt_watcher = WindowsBluetoothWatcher(
                on_connection_changed=self.handle_windows_connection_changed,
                preferred_mac=self.config.preferred_device_mac,
            )
            self._win_bt_watcher.start()

            # 2. Start BLE scanner for high-fidelity battery and earbud telemetry
            self._scanner = BLEAirPodsScanner(on_state_update=self.handle_raw_state_update)
            self._scanner.start()

    def stop(self) -> None:
        if self._scanner:
            self._scanner.stop()
            self._scanner = None
        if self._win_bt_watcher:
            self._win_bt_watcher.stop()
            self._win_bt_watcher = None
        self.stop_demo_mode()

    def handle_windows_connection_changed(
        self, is_connected: bool, device_name: str, mac_address: str, model: AirPodsModel
    ) -> None:
        """Called when Windows reports paired AirPods connected or disconnected."""
        logger.info(f"Windows BT device '{device_name}' is_connected={is_connected}")

        if self.current_state is None:
            self.current_state = AirPodsState(
                model=model,
                device_name=device_name,
                mac_address=mac_address,
                connected=is_connected,
            )
        else:
            self.current_state.connected = is_connected
            if device_name and self.current_state.device_name == "AirPods":
                self.current_state.device_name = device_name
            if mac_address:
                self.current_state.mac_address = mac_address
            if model != AirPodsModel.UNKNOWN:
                self.current_state.model = model

        # If disconnected from Windows (AirPods in case and closed)
        if not is_connected:
            if self.config.auto_pause_enabled and self._previous_state and self._previous_state.connected:
                self.audio.on_ear_removed()

        if self.on_state_changed:
            self.on_state_changed(self.current_state)

    def handle_raw_state_update(self, new_state: AirPodsState) -> None:
        """Processes incoming telemetry from BLE scanner."""
        # Correlate with known paired Windows device if present
        if self._win_bt_watcher and self._win_bt_watcher.device_name != "AirPods":
            if new_state.device_name == "AirPods" or not new_state.device_name:
                new_state.device_name = self._win_bt_watcher.device_name
            if self._win_bt_watcher.mac_address:
                new_state.mac_address = self._win_bt_watcher.mac_address
            if self._win_bt_watcher.model != AirPodsModel.UNKNOWN:
                new_state.model = self._win_bt_watcher.model

        # Filter by preferred MAC if explicitly configured and doesn't match
        if self.config.preferred_device_mac and new_state.mac_address:
            pref = self.config.preferred_device_mac.upper().replace("-", ":")
            cur = new_state.mac_address.upper().replace("-", ":")
            if pref != cur:
                return

        prev = self._previous_state

        # Merge with previous state to retain case battery when lid closes
        if self.current_state:
            merged_state = self.current_state.merge_with(new_state)
        else:
            merged_state = new_state

        # Case lid opened trigger (case was closed/absent, and now reporting open)
        was_open = prev.case_open if prev else False
        if merged_state.case_open and not was_open:
            logger.info("AirPods case lid opened -> Showing macOS popup card")
            if self.config.popup_on_case_open and self.on_case_opened:
                self.on_case_opened(merged_state)

        # In-ear auto-pause / auto-resume triggers
        if self.config.auto_pause_enabled and prev is not None:
            if prev.is_in_ear and not merged_state.is_in_ear:
                self.audio.on_ear_removed()
            elif not prev.is_in_ear and merged_state.is_in_ear:
                self.audio.on_ear_inserted()

        self._previous_state = self.current_state
        self.current_state = merged_state

        if self.on_state_changed:
            self.on_state_changed(merged_state)

    def set_noise_mode(self, mode: NoiseControlMode) -> None:
        """Changes the current noise control mode."""
        if self.current_state:
            self.current_state.noise_mode = mode
            logger.info(f"Noise control mode updated to {mode.value}")
            if self.on_state_changed:
                self.on_state_changed(self.current_state)

    # -------------------------------------------------------------
    # Demo / Simulation Mode for instant verification and testing
    # -------------------------------------------------------------
    def start_demo_mode(self) -> None:
        if self._demo_running:
            return
        self._demo_running = True
        self._demo_thread = threading.Thread(target=self._run_demo, daemon=True, name="DemoThread")
        self._demo_thread.start()
        logger.info("AirWin demo mode enabled")

    def stop_demo_mode(self) -> None:
        self._demo_running = False
        if self._demo_thread:
            self._demo_thread = None

    def _run_demo(self) -> None:
        """Simulates AirPods connection, popup, and battery updates."""
        demo_state = AirPodsState(
            model=AirPodsModel.AIRPODS_PRO_2,
            device_name="AirPods Pro (Demo)",
            mac_address="AC:DE:48:00:11:22",
            left_battery=95,
            right_battery=90,
            case_battery=80,
            left_charging=False,
            right_charging=False,
            case_charging=False,
            left_in_ear=True,
            right_in_ear=True,
            case_open=True,
            connected=True,
            noise_mode=NoiseControlMode.NOISE_CANCELLATION,
            rssi=-45,
        )

        time.sleep(0.3)
        if self.on_case_opened and self.config.popup_on_case_open:
            self.on_case_opened(demo_state)

        self.handle_raw_state_update(demo_state)

        while self._demo_running:
            time.sleep(8)
            if not self._demo_running:
                break
            demo_state.rssi = -42 if demo_state.rssi == -45 else -45
            self.handle_raw_state_update(demo_state)
