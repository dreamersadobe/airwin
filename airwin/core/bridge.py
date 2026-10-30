"""Qt Thread-Safe Event Bridge for AirWin.

Ensures all background telemetry and Bluetooth events are delivered safely
to the Qt GUI thread via queued signal connections.
"""

from airwin.core.models import AirPodsState
from airwin.ui.qt_compat import QObject, Signal


class AirWinBridge(QObject):
    """Bridge for cross-thread signals between core device manager and Qt UI."""

    state_changed = Signal(object)      # Emits AirPodsState
    case_opened = Signal(object)        # Emits AirPodsState
    connection_changed = Signal(bool)   # Emits True/False
