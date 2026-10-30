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
            # macOS testing fallback
            try:
                script = """
                tell application "System Events"
                    key code 16 using {command down}
                end tell
                """
                # Or Spotify / Music check
                cmd = [
                    "osascript",
                    "-e",
                    'tell application "Music" to playpause',
                ]
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
    def fix_handsfree_audio() -> tuple[bool, str]:
        """Disables Windows Bluetooth Hands-Free Telephony service for AirPods.

        Prevents audio quality from dropping to muffled 8kHz mono when apps query mic.
        """
        if sys.platform != "win32":
            return False, "Функция доступна только в Windows"

        try:
            # PowerShell command to disable Hands-Free Telephony audio device
            ps_cmd = (
                'Get-PnpDevice -Class "AudioEndpoint" | '
                'Where-Object {$_.FriendlyName -like "*Hands-Free*" -and $_.FriendlyName -like "*AirPods*"} | '
                "Disable-PnpDevice -Confirm:$false"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                return True, "Служба Hands-Free отключена! Качество стерео зафиксировано."
            else:
                return False, res.stderr or "Не удалось изменить параметры устройства."
        except Exception as e:
            return False, str(e)

