"""macOS-style AirPods battery card shown when the case lid opens."""

from airwin.config import AppConfig
from airwin.core.models import AirPodsState
from airwin.ui.components import BatteryItem, MacPopover
from airwin.ui.qt_compat import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPoint,
    QTimer,
    QVBoxLayout,
    Qt,
)
from airwin.ui.styles import MacTheme, get_theme


class AirPodsPopupCard(MacPopover):
    """Compact translucent card that mirrors the macOS AirPods popup."""

    def __init__(self, config: AppConfig, theme: MacTheme = None, parent=None):
        theme = theme or get_theme(config.dark_mode)
        super().__init__(
            theme,
            panel_width=340,
            radius=20,
            shadow=18,
            no_activate=True,
        )
        self.config = config

        self._auto_dismiss_timer = QTimer(self)
        self._auto_dismiss_timer.setSingleShot(True)
        self._auto_dismiss_timer.timeout.connect(self.dismiss)

        self._init_ui()
        self.auto_size()

    def _init_ui(self) -> None:
        s = self.shadow
        layout = QVBoxLayout(self)
        layout.setContentsMargins(s + 16, s + 14, s + 16, s + 14)
        layout.setSpacing(6)

        self.lbl_title = QLabel("AirPods", self)
        self.lbl_title.setObjectName("PopupTitle")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_status = QLabel("", self)
        self.lbl_status.setObjectName("PopupStatus")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setTextFormat(Qt.TextFormat.RichText)

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_status)

        battery_row = QHBoxLayout()
        battery_row.setContentsMargins(0, 6, 0, 0)
        battery_row.setSpacing(10)

        self.card_left = BatteryItem("Левый", "left", self.theme, self)
        self.card_right = BatteryItem("Правый", "right", self.theme, self)
        self.card_case = BatteryItem("Кейс", "case", self.theme, self)

        battery_row.addStretch()
        battery_row.addWidget(self.card_left)
        battery_row.addWidget(self.card_right)
        battery_row.addWidget(self.card_case)
        battery_row.addStretch()
        layout.addLayout(battery_row)

    def apply_theme(self, theme: MacTheme) -> None:
        self.card_left.set_theme(theme)
        self.card_right.set_theme(theme)
        self.card_case.set_theme(theme)
        if self.lbl_status.text():
            self._refresh_status()

    def _refresh_status(self) -> None:
        state = getattr(self, "_state", None)
        if state is None:
            return

        if state.case_open:
            dot = self.theme.accent.name()
            text = "Кейс открыт"
        elif state.connected:
            dot = self.theme.green.name()
            text = "Подключено"
        else:
            dot = self.theme.text_tertiary.name()
            text = "Поиск…"

        self.lbl_status.setText(
            f'<span style="color:{dot};">●</span>&nbsp; {text}'
        )

    def show_for_state(self, state: AirPodsState) -> None:
        self._state = state
        self.lbl_title.setText(state.device_name)
        self._refresh_status()

        self.card_left.set_data(state.left_battery, state.left_charging, state.left_in_ear)
        self.card_right.set_data(state.right_battery, state.right_charging, state.right_in_ear)
        self.card_case.set_data(state.case_battery, state.case_charging, False)

        screen = QApplication.primaryScreen()
        if screen is None:
            self.show()
            return

        geom = screen.availableGeometry()
        target = QPoint(
            geom.right() - self.width() - 12,
            geom.bottom() - self.height() - 12,
        )

        self._auto_dismiss_timer.stop()
        self.setWindowOpacity(0.0)
        self.move(target.x(), target.y() + 10)
        self.show()
        self.raise_()
        self.fade_in()
        self.slide_in(target)

        if self.config.popup_duration_sec > 0:
            self._auto_dismiss_timer.start(self.config.popup_duration_sec * 1000)

    def dismiss(self) -> None:
        self._auto_dismiss_timer.stop()
        if not self.isVisible():
            return
        self.fade_out(on_finished=self._finish_hide)

    def _finish_hide(self) -> None:
        self.hide()
        self.setWindowOpacity(1.0)
        self._closing = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dismiss()
        else:
            super().mousePressEvent(event)
