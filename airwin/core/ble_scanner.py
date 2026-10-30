"""Bluetooth Low Energy (BLE) scanner for AirPods broadcast signals using Bleak."""

import asyncio
import logging
import threading
import time
from typing import Callable, Optional

from airwin.core.airpods_parser import APPLE_COMPANY_ID, AirPodsParser
from airwin.core.models import AirPodsState

logger = logging.getLogger(__name__)


class BLEAirPodsScanner:
    """Scans for Apple Continuity BLE advertisement packets and yields parsed AirPodsState."""

    def __init__(self, on_state_update: Callable[[AirPodsState], None]):
        self.on_state_update = on_state_update
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._scanner = None

    def start(self) -> None:
        """Starts the BLE scanner thread."""
        if self._is_running:
            return
        self._is_running = True
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True, name="BLEScannerThread")
        self._thread.start()
        logger.info("BLE Scanner thread started")

    def stop(self) -> None:
        """Stops the BLE scanner."""
        self._is_running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("BLE Scanner stopped")

    def _run_async_loop(self) -> None:
        """Thread worker creating an asyncio event loop for BleakScanner."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._scan_coroutine())
        except Exception as e:
            logger.error(f"Error in BLE scanner loop: {e}", exc_info=True)
        finally:
            self._loop.close()

    async def _scan_coroutine(self) -> None:
        """Bleak scanner loop with continuous detection."""
        try:
            from bleak import BleakScanner
        except ImportError:
            logger.warning("Bleak is not installed. BLE scanning will be unavailable.")
            return

        def detection_callback(device, advertisement_data):
            if not self._is_running:
                return

            mfg_data = advertisement_data.manufacturer_data
            if not mfg_data:
                return

            # Check for Apple Company ID (0x004C)
            apple_payload = mfg_data.get(APPLE_COMPANY_ID)
            if not apple_payload:
                return

            state = AirPodsParser.parse_manufacturer_data(
                raw_data=apple_payload,
                rssi=advertisement_data.rssi,
                device_name=device.name,
                mac_address=device.address,
            )

            if state:
                self.on_state_update(state)

        try:
            async with BleakScanner(detection_callback=detection_callback) as scanner:
                self._scanner = scanner
                logger.info("BleakScanner active, listening for Apple proximity beacons...")
                while self._is_running:
                    await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"BleakScanner exception: {e}")
