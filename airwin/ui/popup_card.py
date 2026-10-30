"""macOS-inspired animated AirPods connection and battery popup card."""

import sys
from airwin.config import AppConfig
from airwin.core.models import AirPodsState
from airwin.ui.components import BatteryCardWidget
from airwin.ui.dwm import enable_dwm_transparency
from airwin.ui.qt_compat import (
    QApplication,
    QColor,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPainter,
    QPainterPath,
    QPen,
    QPoint,
    QPropertyAnimation,
    QPushButton,
    QRectF,
    Qt,
    QTimer,
    QVBoxLayout,
)
from airwin.ui.styles import POPUP_CARD_STYLE


class AirPodsPopupCard(QDialog):
    """Animated macOS-style card shown upon AirPods case lid opening or connection."""

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config

        self.setObjectName("PopupRoot")
        self.setStyleSheet(POPUP_CARD_STYLE)

        # Frameless, translucent, always on top, tool window (no taskbar button)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._auto_dismiss_timer = QTimer(self)
        self._auto_dismiss_timer.setSingleShot(True)
        self._auto_dismiss_timer.timeout.connect(self.animate_hide)

        self._anim = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # Header: Device Name & Subtitle
        header_layout = QVBoxLayout()
        header_layout.setSpacing(3)

        self.lbl_title = QLabel("AirPods", self)
        self.lbl_title.setObjectName("PopupTitle")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_subtitle = QLabel("Подключено", self)
        self.lbl_subtitle.setObjectName("PopupSubtitle")
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(self.lbl_title)
        header_layout.addWidget(self.lbl_subtitle)
        layout.addLayout(header_layout)

        # Battery Cards Row (Left, Right, Case)
        self.battery_layout = QHBoxLayout()
        self.battery_layout.setSpacing(10)

        self.card_left = BatteryCardWidget("Левый", "🎧", self)
        self.card_right = BatteryCardWidget("Правый", "🎧", self)
        self.card_case = BatteryCardWidget("Кейс", "🔋", self)

        self.battery_layout.addWidget(self.card_left)
        self.battery_layout.addWidget(self.card_right)
        self.battery_layout.addWidget(self.card_case)
        layout.addLayout(self.battery_layout)

        # Done button
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_done = QPushButton("Готово", self)
        self.btn_done.setObjectName("DoneButton")
        self.btn_done.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_done.clicked.connect(self.animate_hide)
        btn_layout.addWidget(self.btn_done)

        layout.addLayout(btn_layout)
        self.setFixedSize(360, 225)

    def paintEvent(self, event):
        """Draws the smooth macOS Big Sur dark glass card background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, 20, 20)

        # Rich dark background
        painter.fillPath(path, QColor(28, 30, 34, 252))

        # Elegant subtle glass border
        painter.setPen(QPen(QColor(255, 255, 255, 36), 1.2))
        painter.drawPath(path)

    def showEvent(self, event):
        super().showEvent(event)
        enable_dwm_transparency(self)

    def show_for_state(self, state: AirPodsState):
        """Populates state and shows card with smooth slide-up animation."""
        self.lbl_title.setText(state.device_name)
        if state.case_open:
            self.lbl_subtitle.setText("Кейс открыт")
        else:
            self.lbl_subtitle.setText("Подключено" if state.connected else "Поиск...")

        self.card_left.setData(state.left_battery, state.left_charging, state.left_in_ear)
        self.card_right.setData(state.right_battery, state.right_charging, state.right_in_ear)
        self.card_case.setData(state.case_battery, state.case_charging, False)

        # Position at bottom-right corner above taskbar
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            target_x = geom.right() - self.width() - 24
            target_y = geom.bottom() - self.height() - 20
            start_y = target_y + 15

            self.move(target_x, start_y)
            self.show()

            # Smooth slide-up animation
            self._anim = QPropertyAnimation(self, b"pos")
            self._anim.setDuration(260)
            self._anim.setStartValue(QPoint(target_x, start_y))
            self._anim.setEndValue(QPoint(target_x, target_y))
            self._anim.start()
        else:
            self.show()

        # Reset auto-dismiss timer
        if self.config.popup_duration_sec > 0:
            self._auto_dismiss_timer.start(self.config.popup_duration_sec * 1000)

    def animate_hide(self):
        """Hides the card smoothly."""
        self._auto_dismiss_timer.stop()
        self.hide()
