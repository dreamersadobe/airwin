"""Windows media control and audio optimization helpers."""

import logging
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)

# Virtual key code for Windows Media Play/Pause
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002


class AudioController:
    """Controls media playback (pause/resume) and audio optimizations."""

    def __init__(self):
        self._is_windows = sys.platform == "win32"
        self._is_paused_by_airwin = False

    def toggle_play_pause(self) -> bool:
        """Sends a universal Media Play/Pause command to the OS."""
        if self._is_windows:
            try:
                import ctypes

                # Send Key Down then Key Up
                ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)
                logger.info("Sent Windows VK_MEDIA_PLAY_PAUSE key event")
                return True
            except Exception as e:
                logger.error(f"Failed to send Windows media key: {e}")
                return False
        elif sys.platform == "darwin":
            try:
                cmd = ["osascript", "-e", 'tell application "Music" to playpause']
                subprocess.run(cmd, capture_output=True, timeout=1)
                return True
            except Exception:
                return False
        return False

    def on_ear_removed(self) -> None:
        """Called when AirPods earbud is removed from ear."""
        if not self._is_paused_by_airwin:
            logger.info("Earbud removed from ear -> Auto-pausing media")
            self.toggle_play_pause()
            self._is_paused_by_airwin = True

    def on_ear_inserted(self) -> None:
        """Called when AirPods earbud is inserted back into ear."""
        if self._is_paused_by_airwin:
            logger.info("Earbud re-inserted -> Auto-resuming media")
            self.toggle_play_pause()
            self._is_paused_by_airwin = False

    def reset_pause_state(self) -> None:
        self._is_paused_by_airwin = False

    @staticmethod
    def fix_handsfree_audio(device_name: str = "") -> tuple[bool, str]:
        """Disables Windows Bluetooth Hands-Free Telephony service for AirPods.

        Prevents audio quality from dropping to muffled 8kHz mono when apps query mic.
        """
        if sys.platform != "win32":
            return False, "Функция доступна только в Windows"

        try:
            # Match any Hands-Free endpoint related to Apple or specific device
            patterns = ["*Hands-Free*"]
            if device_name:
                clean_name = device_name.replace("'", "").replace('"', "")
                name_filter = f"($_.FriendlyName -like '*{clean_name}*') -and "
            else:
                name_filter = ""

            ps_cmd = (
                f'Get-PnpDevice -Class "AudioEndpoint" | '
                f'Where-Object {{ {name_filter} ($_.FriendlyName -like "*Hands-Free*" -or $_.FriendlyName -like "*Головной телефон*") }} | '
                f'ForEach-Object {{ Disable-PnpDevice -InputObject $_ -Confirm:$false; $_.FriendlyName }}'
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=8,
            )
            output = res.stdout.strip()
            if output:
                return True, f"Служба Hands-Free отключена: {output}"
            elif res.returncode == 0:
                return True, "Служба Hands-Free уже отключена или не активна."
            else:
                return False, res.stderr or "Не удалось отключить службу Hands-Free."
        except Exception as e:
            return False, str(e)
