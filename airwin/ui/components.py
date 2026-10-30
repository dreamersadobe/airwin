"""Windows 11 Fluent UI components (Battery tiles, Noise control, Toggle switch)."""

from airwin.core.models import NoiseControlMode
from airwin.ui.qt_compat import (
    QEasingCurve,
    QBrush,
    QColor,
    QFont,
    QHBoxLayout,
    QLabel,
    QPainter,
    QPainterPath,
    QPen,
    QPointF,
    QPropertyAnimation,
    QPushButton,
    QRectF,
    Qt,
    Signal,
    Slot,
    QVBoxLayout,
    QWidget,
)


def get_battery_color(percent: int) -> QColor:
    """Returns Windows 11 Fluent battery indicator color."""
    if percent > 20:
        return QColor(108, 203, 95)   # Fluent Soft Green
    elif percent > 10:
        return QColor(252, 225, 0)    # Fluent Amber
    else:
        return QColor(255, 153, 164)  # Fluent Red


class BatteryCardWidget(QWidget):
    """Windows 11 Fluent tile displaying battery level and state for Left, Right, or Case."""

    def __init__(self, title: str, icon_symbol: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon_symbol = icon_symbol
        self.battery_percent = -1
        self.is_charging = False
        self.in_ear = False

        self.setFixedHeight(82)
        self.setMinimumWidth(96)

    def set_data(self, percent: int, charging: bool, in_ear: bool = False):
        self.battery_percent = percent
        self.is_charging = charging
        self.in_ear = in_ear
        self.update()

    setData = set_data

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)

        # Windows 11 Card plate: 8px corner radius
        path = QPainterPath()
        path.addRoundedRect(rect, 8, 8)

        # Subtle translucent surface
        painter.fillPath(path, QBrush(QColor(255, 255, 255, 14)))

        # Fluent 1px border
        painter.setPen(QPen(QColor(255, 255, 255, 22), 1))
        painter.drawPath(path)

        # Header: Icon & Title
        painter.setFont(QFont("Segoe UI", 12))
        painter.setPen(QColor(255, 255, 255, 220))
        painter.drawText(
            QRectF(10, 8, 22, 20),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.icon_symbol,
        )

        painter.setFont(QFont("Segoe UI Variable Text", 10, QFont.Weight.Medium))
        painter.setPen(QColor(255, 255, 255, 175))
        painter.drawText(
            QRectF(34, 8, self.width() - 42, 20),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.title,
        )

        # Battery percentage & indicators
        y_text = 32
        if self.battery_percent >= 0:
            pct_str = f"{self.battery_percent}%"
            painter.setFont(QFont("Segoe UI Variable Display", 15, QFont.Weight.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(
                QRectF(10, y_text, 56, 22),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                pct_str,
            )

            # Badges
            badge_x = 64
            if self.is_charging:
                painter.setFont(QFont("Segoe UI", 11))
                painter.setPen(QColor(108, 203, 95))
                painter.drawText(
                    QRectF(badge_x, y_text, 18, 22),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    "⚡",
                )
                badge_x += 16

            if self.in_ear:
                painter.setFont(QFont("Segoe UI", 10))
                painter.setPen(QColor(76, 194, 255))
                painter.drawText(
                    QRectF(badge_x, y_text, 18, 22),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    "👂",
                )

            # Battery level progress capsule at bottom
            bar_w = self.width() - 20
            bar_h = 4
            bar_y = self.height() - 11

            track_path = QPainterPath()
            track_path.addRoundedRect(QRectF(10, bar_y, bar_w, bar_h), 2, 2)
            painter.fillPath(track_path, QBrush(QColor(255, 255, 255, 30)))

            fill_w = max(4.0, (self.battery_percent / 100.0) * bar_w)
            fill_path = QPainterPath()
            fill_path.addRoundedRect(QRectF(10, bar_y, fill_w, bar_h), 2, 2)
            painter.fillPath(fill_path, QBrush(get_battery_color(self.battery_percent)))
        else:
            painter.setFont(QFont("Segoe UI Variable Text", 11))
            painter.setPen(QColor(255, 255, 255, 80))
            painter.drawText(
                QRectF(10, y_text, self.width() - 20, 22),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                "Отключено",
            )


class NoiseSegmentedControl(QWidget):
    """Windows 11 Fluent segmented selector for Noise Control."""

    mode_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = NoiseControlMode.OFF

        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(4)

        self.btn_anc = QPushButton("Шумоподавление")
        self.btn_transparency = QPushButton("Прозрачность")
        self.btn_off = QPushButton("Выкл")

        self.buttons = {
            NoiseControlMode.NOISE_CANCELLATION: self.btn_anc,
            NoiseControlMode.TRANSPARENCY: self.btn_transparency,
            NoiseControlMode.OFF: self.btn_off,
        }

        for mode, btn in self.buttons.items():
            btn.setObjectName("PillButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, m=mode: self.set_mode(m, user_click=True))
            layout.addWidget(btn)

        self.update_buttons_ui()

    def set_mode(self, mode: NoiseControlMode, user_click: bool = False):
        self.current_mode = mode
        self.update_buttons_ui()
        if user_click:
            self.mode_changed.emit(mode)

    def update_buttons_ui(self):
        for mode, btn in self.buttons.items():
            is_active = (mode == self.current_mode)
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)


class FluentToggleSwitch(QWidget):
    """Native Windows 11 style animated pill toggle switch."""

    toggled = Signal(bool)

    def __init__(self, label_text: str = "", checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._label_text = label_text
        self._knob_pos = 18.0 if checked else 3.0

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(28)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Label on left
        self.label = QLabel(self._label_text, self)
        self.label.setFont(QFont("Segoe UI Variable Text", 11))
        self.label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        layout.addWidget(self.label)
        layout.addStretch()

        # Switch container
        self.switch_widget = _SwitchPill(self)
        self.switch_widget.setChecked(self._checked)
        self.switch_widget.toggled.connect(self._on_switch_toggled)
        layout.addWidget(self.switch_widget)

    def isChecked(self) -> bool:
        return self.switch_widget.isChecked()

    def setChecked(self, checked: bool) -> None:
        self.switch_widget.setChecked(checked)

    def _on_switch_toggled(self, checked: bool):
        self._checked = checked
        self.toggled.emit(checked)


class _SwitchPill(QWidget):
    """The pill track and knob for FluentToggleSwitch."""

    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._knob_x = 3.0
        self.setFixedSize(38, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        if self._checked != checked:
            self._checked = checked
            self._knob_x = 21.0 if checked else 3.0
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self._knob_x = 21.0 if self._checked else 3.0
            self.update()
            self.toggled.emit(self._checked)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0.5, 0.5, 37, 19)
        track_path = QPainterPath()
        track_path.addRoundedRect(rect, 9.5, 9.5)

        if self._checked:
            # Windows 11 Accent fill
            painter.fillPath(track_path, QColor(0, 103, 192))
            painter.setPen(QPen(QColor(0, 103, 192), 1))
            painter.drawPath(track_path)
            # Knob (White)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(QRectF(self._knob_x, 3.0, 14.0, 14.0))
        else:
            # Inactive dark track with border
            painter.fillPath(track_path, QColor(255, 255, 255, 15))
            painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
            painter.drawPath(track_path)
            # Knob (Light Gray)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(200, 200, 200))
            painter.drawEllipse(QRectF(self._knob_x, 3.0, 14.0, 14.0))
