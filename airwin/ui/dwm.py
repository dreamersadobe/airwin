"""Windows window-attribute integration for the custom painted popovers.

The panels draw their own translucent material, rounded corners and shadow,
so the DWM only needs to be told about the appearance (dark/light) and that
the system must not clip the window with its own corner rounding.
"""

import logging
import sys

logger = logging.getLogger(__name__)

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_DONOTROUND = 1


def apply_window_appearance(widget, dark: bool) -> None:
    """Applies dark-mode metadata and disables DWM corner clipping."""
    if sys.platform != "win32":
        return

    try:
        import ctypes

        hwnd = int(widget.winId())
        if not hwnd:
            return

        dwmapi = ctypes.windll.dwmapi

        dark_value = ctypes.c_int(1 if dark else 0)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(dark_value),
            ctypes.sizeof(dark_value),
        )

        corner_value = ctypes.c_int(DWMWCP_DONOTROUND)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(corner_value),
            ctypes.sizeof(corner_value),
        )
    except Exception as error:
        logger.debug(f"Failed to apply DWM appearance: {error}")
