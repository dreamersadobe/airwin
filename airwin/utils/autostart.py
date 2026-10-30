"""Windows autostart configuration via Registry."""

import logging
import os
import sys

logger = logging.getLogger(__name__)

REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "AirWin"


def set_launch_on_startup(enable: bool) -> bool:
    """Configures AirWin to start on Windows user logon."""
    if sys.platform != "win32":
        logger.info("Autostart registry configuration is Windows-only.")
        return False

    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_KEY,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
        )

        if enable:
            if getattr(sys, "frozen", False):
                app_path = f'"{sys.executable}"'
            else:
                script_path = os.path.abspath(sys.argv[0])
                python_exe = sys.executable.replace("python.exe", "pythonw.exe")
                app_path = f'"{python_exe}" "{script_path}"'

            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, app_path)
            logger.info(f"Registered autostart: {app_path}")
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
                logger.info("Removed autostart registry entry")
            except FileNotFoundError:
                pass

        winreg.CloseKey(key)
        return True
    except Exception as e:
        logger.error(f"Failed to update Windows autostart: {e}")
        return False
