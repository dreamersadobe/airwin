"""Windows Bluetooth and WinRT integration for paired AirPods management."""

import asyncio
import logging
import re
import threading
import time
from typing import Callable, Optional

from airwin.core.models import AirPodsModel

logger = logging.getLogger(__name__)

# Standard Apple Bluetooth Vendor ID
APPLE_VID = 0x004C


class WindowsBluetoothWatcher:
    """Monitors paired Windows Apple AirPods connection status in real-time using WinRT."""

    def __init__(
        self,
        on_connection_changed: Callable[[bool, str, str, AirPodsModel], None],
        preferred_mac: str = "",
    ):
        self.on_connection_changed = on_connection_changed
        self.preferred_mac = preferred_mac.upper().replace("-", ":") if preferred_mac else ""

        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self.device_name = "AirPods"
        self.mac_address = ""
        self.model = AirPodsModel.AIRPODS_PRO_2
        self.is_connected = False

    def start(self) -> None:
        if self._is_running:
            return
        self._is_running = True
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="WinBluetoothWatcher"
        )
        self._thread.start()
        logger.info("Windows Bluetooth Watcher started")

    def stop(self) -> None:
        self._is_running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("Windows Bluetooth Watcher stopped")

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._monitor())
        except Exception as e:
            logger.error(f"Error in WindowsBluetoothWatcher loop: {e}", exc_info=True)
        finally:
            self._loop.close()

    async def _monitor(self) -> None:
        try:
            from winrt.windows.devices.bluetooth import BluetoothDevice
            from winrt.windows.devices.enumeration import DeviceInformation
        except ImportError:
            logger.warning("WinRT Bluetooth not available. Skipping Windows Bluetooth watcher.")
            return

        last_known_status = None

        while self._is_running:
            try:
                apple_dev = await self._find_paired_apple_device()
                if apple_dev:
                    curr_conn = (int(apple_dev.connection_status) == 1)
                    if last_known_status is None or curr_conn != last_known_status:
                        last_known_status = curr_conn
                        self.is_connected = curr_conn
                        logger.info(
                            f"Windows device '{self.device_name}' connection status: {curr_conn}"
                        )
                        self.on_connection_changed(
                            curr_conn, self.device_name, self.mac_address, self.model
                        )
            except Exception as e:
                logger.debug(f"Bluetooth device poll error: {e}")

            await asyncio.sleep(2.0)

    async def _find_paired_apple_device(self):
        """Discovers paired Apple AirPods / Beats device using Windows WinRT."""
        try:
            from winrt.windows.devices.bluetooth import BluetoothDevice
            from winrt.windows.devices.enumeration import DeviceInformation

            selector = BluetoothDevice.get_device_selector()
            devices = await DeviceInformation.find_all_async_aqs_filter(selector)

            for i in range(devices.size):
                d = devices.get_at(i)
                d_name = d.name or ""
                d_id = d.id or ""

                # Check for Apple keywords or ID patterns
                is_apple = (
                    "airpod" in d_name.lower()
                    or "beats" in d_name.lower()
                    or "utopia" in d_name.lower()
                    or "004c" in d_id.lower()
                )

                if is_apple:
                    dev = await BluetoothDevice.from_id_async(d.id)
                    if dev:
                        mac_raw = f"{dev.bluetooth_address:012X}"
                        formatted_mac = ":".join(mac_raw[j : j + 2] for j in range(0, 12, 2))

                        if self.preferred_mac and formatted_mac != self.preferred_mac:
                            continue

                        self.device_name = dev.name
                        self.mac_address = formatted_mac

                        # Identify Model
                        name_lower = dev.name.lower()
                        if "pro 2" in name_lower:
                            self.model = AirPodsModel.AIRPODS_PRO_2
                        elif "pro" in name_lower:
                            self.model = AirPodsModel.AIRPODS_PRO
                        elif "max" in name_lower:
                            self.model = AirPodsModel.AIRPODS_MAX
                        elif "4" in name_lower or "utopia" in name_lower:
                            self.model = AirPodsModel.AIRPODS_4_ANC
                        elif "3" in name_lower:
                            self.model = AirPodsModel.AIRPODS_3
                        else:
                            self.model = AirPodsModel.AIRPODS_4_ANC

                        return dev
        except Exception as e:
            logger.debug(f"Error finding paired Apple device: {e}")

        return None
