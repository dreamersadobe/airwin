"""Custom vector UI components inspired by macOS Big Sur and iOS."""

from airwin.core.models import NoiseControlMode
from airwin.ui.qt_compat import (
    QBrush,
    QColor,
    QFont,
    QHBoxLayout,
    QLabel,
    QPainter,
    QPainterPath,
    QPen,
    QPushButton,
    QRectF,
    Qt,
    Signal,
    QVBoxLayout,
    QWidget,
)


def get_battery_color(percent: int) -> QColor:
    if percent > 20:
        return QColor(48, 209, 88)  # Apple Green
    elif percent > 10:
        return QColor(255, 159, 10)  # Apple Amber
    else:
        return QColor(255, 69, 58)  # Apple Red


class BatteryCardWidget(QWidget):
    """An Apple-style battery status tile for Left, Right, or Case."""

    def __init__(self, title: str, icon_symbol: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon_symbol = icon_symbol
        self.battery_percent = -1
        self.is_charging = False
        self.in_ear = False

        self.setFixedHeight(82)
        self.setMinimumWidth(100)

    def set_data(self, percent: int, charging: bool, in_ear: bool = False):
        self.battery_percent = percent
        self.is_charging = charging
        self.in_ear = in_ear
        self.update()

    setData = set_data

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background card
        rect = QRectF(0, 0, self.width(), self.height())
        bg_path = QPainterPath()
        bg_path.addRoundedRect(rect, 14, 14)
        painter.fillPath(bg_path, QBrush(QColor(45, 47, 51, 190)))

        # Border
        painter.setPen(QPen(QColor(255, 255, 255, 25), 1))
        painter.drawPath(bg_path)

        # Icon / Symbol at top left
        painter.setFont(QFont("Segoe UI", 14))
        painter.setPen(QColor(255, 255, 255, 220))
        painter.drawText(QRectF(12, 10, 30, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.icon_symbol)

        # Title (Левый / Правый / Кейс)
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        painter.setPen(QColor(235, 235, 245, 160))
        painter.drawText(QRectF(40, 10, self.width() - 48, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.title)

        # Percentage or Not Connected
        y_text = 36
        if self.battery_percent >= 0:
            pct_str = f"{self.battery_percent}%"
            painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(QRectF(12, y_text, 60, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, pct_str)

            # Charging bolt ⚡ or In-ear badge 👂
            badge_x = 72
            if self.is_charging:
                painter.setFont(QFont("Segoe UI", 13))
                painter.setPen(QColor(48, 209, 88))
                painter.drawText(QRectF(badge_x, y_text, 24, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "⚡")
                badge_x += 20

            if self.in_ear:
                painter.setFont(QFont("Segoe UI", 12))
                painter.setPen(QColor(10, 132, 255))
                painter.drawText(QRectF(badge_x, y_text, 24, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "👂")

            # Battery level bar at bottom
            bar_w = self.width() - 24
            bar_h = 5
            bar_y = self.height() - 13

            # Bar background track
            track_path = QPainterPath()
            track_path.addRoundedRect(QRectF(12, bar_y, bar_w, bar_h), 2.5, 2.5)
            painter.fillPath(track_path, QBrush(QColor(255, 255, 255, 30)))

            # Filled level
            fill_w = max(4.0, (self.battery_percent / 100.0) * bar_w)
            fill_path = QPainterPath()
            fill_path.addRoundedRect(QRectF(12, bar_y, fill_w, bar_h), 2.5, 2.5)
            color = get_battery_color(self.battery_percent)
            painter.fillPath(fill_path, QBrush(color))
        else:
            painter.setFont(QFont("-apple-system", 13))
            painter.setPen(QColor(235, 235, 245, 90))
            painter.drawText(QRectF(12, y_text, self.width() - 24, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "Отключено")


class NoiseSegmentedControl(QWidget):
    """macOS-style segmented pill selector for Noise Control."""

    mode_changed = Signal(object)  # Emits NoiseControlMode

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = NoiseControlMode.OFF

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

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
