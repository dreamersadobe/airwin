"""macOS Control Center style AirPods panel."""

from airwin.config import AppConfig
from airwin.core.device_manager import DeviceManager
from airwin.core.models import AirPodsState, NoiseControlMode
from airwin.core.windows_audio import AudioController
from airwin.ui.components import (
    BatteryItem,
    DeviceBadge,
    MacPopover,
    NoiseButton,
    SettingRow,
    SettingsCard,
)
from airwin.ui.qt_compat import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPoint,
    QPushButton,
    QtCore,
    QVBoxLayout,
    Qt,
    Signal,
)
from airwin.ui.styles import MacTheme, get_theme
from airwin.utils.autostart import set_launch_on_startup


class ControlCenterFlyout(MacPopover):
    """Translucent AirPods panel opened from the system tray."""

    theme_changed = Signal(bool)

    def __init__(
        self,
        device_manager: DeviceManager,
        config: AppConfig,
        theme: MacTheme = None,
        parent=None,
    ):
        theme = theme or get_theme(config.dark_mode)
        super().__init__(
            theme,
            panel_width=360,
            radius=20,
            shadow=18,
            no_activate=False,
        )
        self.device_manager = device_manager
        self.config = config
        self._state = None

        self._init_ui()
        self.auto_size()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _init_ui(self) -> None:
        s = self.shadow
        layout = QVBoxLayout(self)
        layout.setContentsMargins(s + 18, s + 16, s + 18, s + 14)
        layout.setSpacing(14)

        # Header --------------------------------------------------------
        header = QHBoxLayout()
        header.setSpacing(12)

        self.badge = DeviceBadge(self.theme, self)
        header.addWidget(self.badge)

        text_column = QVBoxLayout()
        text_column.setSpacing(1)
        text_column.setContentsMargins(0, 0, 0, 0)

        self.lbl_device_name = QLabel("AirPods", self)
        self.lbl_device_name.setObjectName("HeaderDeviceName")

        self.lbl_status = QLabel("", self)
        self.lbl_status.setObjectName("HeaderStatus")
        self.lbl_status.setTextFormat(Qt.TextFormat.RichText)

        text_column.addWidget(self.lbl_device_name)
        text_column.addWidget(self.lbl_status)

        header.addLayout(text_column)
        header.addStretch()
        layout.addLayout(header)

        # Battery -------------------------------------------------------
        battery_row = QHBoxLayout()
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

        # Noise control -------------------------------------------------
        noise_group = QVBoxLayout()
        noise_group.setSpacing(8)
        noise_group.addWidget(self._section_title("Шумоподавление"))

        noise_row = QHBoxLayout()
        noise_row.setSpacing(8)
        noise_row.addStretch()

        self.noise_buttons = {}
        noise_options = (
            (NoiseControlMode.NOISE_CANCELLATION, "Шумоподавление"),
            (NoiseControlMode.TRANSPARENCY, "Прозрачность"),
            (NoiseControlMode.OFF, "Выкл"),
        )
        for mode, caption in noise_options:
            button = NoiseButton(mode, caption, self.theme, self)
            button.clicked.connect(self.on_noise_mode_selected)
            self.noise_buttons[mode] = button
            noise_row.addWidget(button)

        noise_row.addStretch()
        noise_group.addLayout(noise_row)
        layout.addLayout(noise_group)

        # Settings ------------------------------------------------------
        settings_group = QVBoxLayout()
        settings_group.setSpacing(8)
        settings_group.addWidget(self._section_title("Параметры"))

        self.row_autopause = SettingRow(
            "Автопауза при снятии наушника",
            self.config.auto_pause_enabled,
            self.theme,
            last=False,
            parent=self,
        )
        self.row_popup = SettingRow(
            "Окно при открытии кейса",
            self.config.popup_on_case_open,
            self.theme,
            last=False,
            parent=self,
        )
        self.row_autostart = SettingRow(
            "Запуск вместе с Windows",
            self.config.launch_on_startup,
            self.theme,
            last=False,
            parent=self,
        )
        self.row_dark = SettingRow(
            "Тёмное оформление",
            self.config.dark_mode,
            self.theme,
            last=True,
            parent=self,
        )

        self.settings_card = SettingsCard(
            [
                self.row_autopause,
                self.row_popup,
                self.row_autostart,
                self.row_dark,
            ],
            self.theme,
            self,
        )
        settings_group.addWidget(self.settings_card)
        layout.addLayout(settings_group)

        # Actions -------------------------------------------------------
        self.btn_audio_fix = QPushButton("Исправить качество звука Windows", self)
        self.btn_audio_fix.setObjectName("MacActionButton")
        self.btn_audio_fix.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_audio_fix.clicked.connect(self.on_audio_fix_clicked)
        layout.addWidget(self.btn_audio_fix)

        self.btn_exit = QPushButton("Завершить AirWin", self)
        self.btn_exit.setObjectName("MacGhostButton")
        self.btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit.clicked.connect(QApplication.instance().quit)
        layout.addWidget(self.btn_exit, 0, Qt.AlignmentFlag.AlignHCenter)

        # Signals -------------------------------------------------------
        self.row_autopause.switch.toggled.connect(self.on_autopause_toggled)
        self.row_popup.switch.toggled.connect(self.on_popup_toggled)
        self.row_autostart.switch.toggled.connect(self.on_autostart_toggled)
        self.row_dark.switch.toggled.connect(self.on_dark_mode_toggled)

        self._refresh_status()

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text, self)
        label.setObjectName("SectionTitle")
        return label

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def apply_theme(self, theme: MacTheme) -> None:
        self.badge.set_theme(theme)
        self.card_left.set_theme(theme)
        self.card_right.set_theme(theme)
        self.card_case.set_theme(theme)
        for button in self.noise_buttons.values():
            button.set_theme(theme)
        self.settings_card.set_theme(theme)
        self._refresh_status()

    def on_dark_mode_toggled(self, checked: bool) -> None:
        self.config.dark_mode = checked
        self.config.save()
        self.set_theme(get_theme(checked))
        self.theme_changed.emit(checked)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    def _refresh_status(self) -> None:
        state = self._state
        if state is not None and state.connected:
            dot = self.theme.green.name()
            text = "Подключено"
        else:
            dot = self.theme.text_tertiary.name()
            text = "Не подключено"

        self.lbl_status.setText(
            f'<span style="color:{dot};">●</span>&nbsp; {text}'
        )

    def update_state(self, state: AirPodsState) -> None:
        self._state = state
        self.lbl_device_name.setText(state.device_name)
        self._refresh_status()

        self.card_left.set_data(state.left_battery, state.left_charging, state.left_in_ear)
        self.card_right.set_data(state.right_battery, state.right_charging, state.right_in_ear)
        self.card_case.set_data(state.case_battery, state.case_charging, False)

        for mode, button in self.noise_buttons.items():
            button.set_active(mode == state.noise_mode)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def on_noise_mode_selected(self, mode: NoiseControlMode) -> None:
        for current, button in self.noise_buttons.items():
            button.set_active(current == mode)
        self.device_manager.set_noise_mode(mode)

    def on_autopause_toggled(self, checked: bool) -> None:
        self.config.auto_pause_enabled = checked
        self.config.save()

    def on_popup_toggled(self, checked: bool) -> None:
        self.config.popup_on_case_open = checked
        self.config.save()

    def on_autostart_toggled(self, checked: bool) -> None:
        self.config.launch_on_startup = checked
        self.config.save()
        set_launch_on_startup(checked)

    def on_audio_fix_clicked(self) -> None:
        device_name = ""
        if self.device_manager.current_state:
            device_name = self.device_manager.current_state.device_name
        success, message = AudioController.fix_handsfree_audio(device_name)
        self.btn_audio_fix.setText(
            "✓ Качество зафиксировано" if success else f"Инфо: {message}"
        )

    # ------------------------------------------------------------------
    # Window placement
    # ------------------------------------------------------------------
    def open_at(self, pos: QPoint) -> None:
        screen = QApplication.primaryScreen()
        if screen is not None:
            geom = screen.availableGeometry()
            x = min(pos.x() - self.width() // 2, geom.right() - self.width() - 12)
            x = max(12, x)
            y = geom.bottom() - self.height() - 12
            self.move(x, y)

        self._closing = False
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()
        self.fade_in(150)

    def toggle_at_position(self, pos: QPoint) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.open_at(pos)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.ActivationChange:
            if self.isVisible() and not self._closing and not self.isActiveWindow():
                self.hide()
