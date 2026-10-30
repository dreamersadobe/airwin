"""Desktop Window Manager (DWM) integration for Windows 10/11."""

import logging
import sys

logger = logging.getLogger(__name__)


def enable_dwm_transparency(widget) -> None:
    """Enables hardware-accelerated DWM glass/acrylic/alpha transparency on Windows."""
    if sys.platform != "win32":
        return

    try:
        import ctypes
        from ctypes import wintypes

        class MARGINS(ctypes.Structure):
            _fields_ = [
                ("cxLeftWidth", wintypes.INT),
                ("cxRightWidth", wintypes.INT),
                ("cyTopHeight", wintypes.INT),
                ("cyBottomHeight", wintypes.INT),
            ]

        hwnd = int(widget.winId())
        if not hwnd:
            return

        # 1. Extend frame into entire client area so DWM treats the window as alpha-blended
        margins = MARGINS(-1, -1, -1, -1)
        ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

        # 2. Enable Windows 11 rounded corners if supported
        # DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2
        try:
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            val = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(val),
                ctypes.sizeof(val),
            )
        except Exception:
            pass

    except Exception as e:
        logger.debug(f"Failed to enable DWM transparency: {e}")
