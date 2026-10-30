"""Central manager for AirPods connection, battery state, ear detection, and ANC."""

import logging
import threading
import time
from typing import Callable, Optional

from airwin.config import AppConfig
from airwin.core.ble_scanner import BLEAirPodsScanner
from airwin.core.models import AirPodsModel, AirPodsState, NoiseControlMode
from airwin.core.windows_audio import AudioController

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
        self._demo_thread: Optional[threading.Thread] = None
        self._demo_running = False

    def start(self) -> None:
        """Starts monitoring either in live BLE mode or demo mode."""
        if self.config.demo_mode:
            self.start_demo_mode()
        else:
            self._scanner = BLEAirPodsScanner(on_state_update=self.handle_raw_state_update)
            self._scanner.start()

    def stop(self) -> None:
        if self._scanner:
            self._scanner.stop()
            self._scanner = None
        self.stop_demo_mode()

    def handle_raw_state_update(self, new_state: AirPodsState) -> None:
        """Processes incoming telemetry from BLE scanner."""
        # Filter by preferred MAC if configured
        if self.config.preferred_device_mac and new_state.mac_address:
            if new_state.mac_address.upper() != self.config.preferred_device_mac.upper():
                return

        prev = self._previous_state

        # Check if case was opened (case was closed or disconnected, and is now open)
        if new_state.case_open and (prev is None or not prev.case_open or not prev.connected):
            if self.config.popup_on_case_open and self.on_case_opened:
                self.on_case_opened(new_state)

        # Check in-ear status for auto-pause / auto-resume
        if self.config.auto_pause_enabled and prev is not None:
            # Earbud removed: was in ear, now neither or fewer earbuds are in ear
            if prev.is_in_ear and not new_state.is_in_ear:
                self.audio.on_ear_removed()
            # Earbud re-inserted
            elif not prev.is_in_ear and new_state.is_in_ear:
                self.audio.on_ear_inserted()

        self._previous_state = self.current_state
        self.current_state = new_state

        if self.on_state_changed:
            self.on_state_changed(new_state)

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
        """Simulates AirPods Pro connection, popup, and battery updates."""
        # Initial simulated state
        demo_state = AirPodsState(
            model=AirPodsModel.AIRPODS_PRO_2,
            device_name="AirPods Pro (Yaroslav)",
            mac_address="AC:DE:48:00:11:22",
            left_battery=90,
            right_battery=85,
            case_battery=75,
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

        time.sleep(0.5)
        # Trigger case open popup
        if self.on_case_opened and self.config.popup_on_case_open:
            self.on_case_opened(demo_state)

        self.handle_raw_state_update(demo_state)

        # Gentle periodic updates
        while self._demo_running:
            time.sleep(10)
            if not self._demo_running:
                break
            # Slightly vary RSSI
            demo_state.rssi = -42 if demo_state.rssi == -45 else -45
            self.handle_raw_state_update(demo_state)
