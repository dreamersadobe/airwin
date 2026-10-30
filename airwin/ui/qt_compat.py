"""Qt compatibility wrapper supporting both PySide6 and PyQt6."""

import sys

try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import (
        Property,
        QEasingCurve,
        QObject,
        QPoint,
        QPointF,
        QPropertyAnimation,
        QRect,
        QRectF,
        QSize,
        Qt,
        QTimer,
        Signal,
        Slot,
    )
    from PySide6.QtGui import (
        QAction,
        QBrush,
        QColor,
        QCursor,
        QFont,
        QFontMetrics,
        QIcon,
        QLinearGradient,
        QPainter,
        QPainterPath,
        QPen,
        QPixmap,
    )
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QDialog,
        QFrame,
        QGraphicsDropShadowEffect,
        QGraphicsOpacityEffect,
        QHBoxLayout,
        QLabel,
        QMenu,
        QPushButton,
        QSystemTrayIcon,
        QVBoxLayout,
        QWidget,
    )
    QT_LIB = "PySide6"
except ImportError:
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets
        from PyQt6.QtCore import (
            QEasingCurve,
            QObject,
            QPoint,
            QPointF,
            QPropertyAnimation,
            QRect,
            QRectF,
            QSize,
            Qt,
            QTimer,
            pyqtSignal as Signal,
            pyqtSlot as Slot,
        )
        from PyQt6.QtGui import (
            QAction,
            QBrush,
            QColor,
            QCursor,
            QFont,
            QFontMetrics,
            QIcon,
            QLinearGradient,
            QPainter,
            QPainterPath,
            QPen,
            QPixmap,
        )
        from PyQt6.QtWidgets import (
            QApplication,
            QCheckBox,
            QDialog,
            QFrame,
            QGraphicsDropShadowEffect,
            QGraphicsOpacityEffect,
            QHBoxLayout,
            QLabel,
            QMenu,
            QPushButton,
            QSystemTrayIcon,
            QVBoxLayout,
            QWidget,
        )
        QT_LIB = "PyQt6"
    except ImportError:
        raise ImportError(
            "Neither PySide6 nor PyQt6 is installed. Please run: pip install PySide6"
        )
