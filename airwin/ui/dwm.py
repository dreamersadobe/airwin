"""Desktop Window Manager (DWM) integration for Windows 11 Fluent Design."""

import logging
import sys

logger = logging.getLogger(__name__)


def enable_dwm_transparency(widget) -> None:
    """Enables native Windows 11 Fluent Acrylic/Mica backdrop, dark mode, and rounded corners."""
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

        # 1. Extend frame into entire client area so DWM treats the window as an alpha-blended surface
        margins = MARGINS(-1, -1, -1, -1)
        ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

        # 2. Force Windows 11 Immersive Dark Mode for window (DWMWA_USE_IMMERSIVE_DARK_MODE = 20)
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            val_dark = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(val_dark),
                ctypes.sizeof(val_dark),
            )
        except Exception:
            pass

        # 3. Enable Windows 11 Native Rounded Corners (DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2)
        try:
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            val_round = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(val_round),
                ctypes.sizeof(val_round),
            )
        except Exception:
            pass

        # 4. Enable Windows 11 Acrylic Material (DWMWA_SYSTEMBACKDROP_TYPE = 38, DWMSBT_TRANSIENTWINDOW = 3)
        try:
            DWMWA_SYSTEMBACKDROP_TYPE = 38
            val_acrylic = ctypes.c_int(3)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_SYSTEMBACKDROP_TYPE,
                ctypes.byref(val_acrylic),
                ctypes.sizeof(val_acrylic),
            )
        except Exception:
            pass

    except Exception as e:
        logger.debug(f"Failed to enable Windows 11 DWM effects: {e}")
