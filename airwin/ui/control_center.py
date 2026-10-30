"""macOS Big Sur style Control Center flyout window for AirPods management."""

import sys
from typing import Optional

from airwin.config import AppConfig
from airwin.core.device_manager import DeviceManager
from airwin.core.models import AirPodsState, NoiseControlMode
from airwin.core.windows_audio import AudioController
from airwin.ui.components import BatteryCardWidget, NoiseSegmentedControl
from airwin.ui.qt_compat import (
    QApplication,
    QCheckBox,
    QColor,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPoint,
    QPushButton,
    Qt,
    QVBoxLayout,
)
from airwin.ui.styles import CONTROL_CENTER_STYLE
from airwin.utils.autostart import set_launch_on_startup


class ControlCenterFlyout(QDialog):
    """The macOS-style flyout menu opened when clicking the tray icon."""

    def __init__(self, device_manager: DeviceManager, config: AppConfig, parent=None):
        super().__init__(parent)
        self.device_manager = device_manager
        self.config = config

        self.setObjectName("ControlCenterRoot")
        self.setStyleSheet(CONTROL_CENTER_STYLE)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Popup
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)

        # Card Container
        self.card = QFrame(self)
        self.card.setObjectName("ControlCenterCard")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(14)

        # 1. Header (Device Name & Status)
        header_layout = QHBoxLayout()

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.lbl_device_name = QLabel("AirPods", self)
        self.lbl_device_name.setObjectName("HeaderDeviceName")

        self.lbl_status = QLabel("Поиск AirPods...", self)
        self.lbl_status.setObjectName("HeaderSubtitle")

        text_layout.addWidget(self.lbl_device_name)
        text_layout.addWidget(self.lbl_status)
        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        card_layout.addLayout(header_layout)

        # 2. Battery Grid
        battery_frame = QFrame(self)
        battery_layout = QHBoxLayout(battery_frame)
        battery_layout.setContentsMargins(0, 0, 0, 0)
        battery_layout.setSpacing(8)

        self.card_left = BatteryCardWidget("Левый", "🎧", self)
        self.card_right = BatteryCardWidget("Правый", "🎧", self)
        self.card_case = BatteryCardWidget("Кейс", "🔋", self)

        battery_layout.addWidget(self.card_left)
        battery_layout.addWidget(self.card_right)
        battery_layout.addWidget(self.card_case)
        card_layout.addWidget(battery_frame)

        # 3. Noise Control (Шумоподавление) Section
        anc_section = QFrame(self)
        anc_section.setObjectName("SectionCard")
        anc_layout = QVBoxLayout(anc_section)
        anc_layout.setContentsMargins(12, 10, 12, 10)
        anc_layout.setSpacing(8)

        lbl_anc_title = QLabel("Управление шумом", self)
        lbl_anc_title.setObjectName("SectionTitle")
        anc_layout.addWidget(lbl_anc_title)

        self.noise_selector = NoiseSegmentedControl(self)
        self.noise_selector.mode_changed.connect(self.on_noise_mode_selected)
        anc_layout.addWidget(self.noise_selector)

        card_layout.addWidget(anc_section)

        # 4. Settings & Features Section
        settings_section = QFrame(self)
        settings_section.setObjectName("SectionCard")
        settings_layout = QVBoxLayout(settings_section)
        settings_layout.setContentsMargins(12, 10, 12, 10)
        settings_layout.setSpacing(10)

        lbl_settings_title = QLabel("Настройки и функции", self)
        lbl_settings_title.setObjectName("SectionTitle")
        settings_layout.addWidget(lbl_settings_title)

        self.cb_autopause = QCheckBox("Автопауза при снятии наушника", self)
        self.cb_autopause.setChecked(self.config.auto_pause_enabled)
        self.cb_autopause.toggled.connect(self.on_autopause_toggled)
        settings_layout.addWidget(self.cb_autopause)

        self.cb_popup = QCheckBox("Всплывающее окно при открытии кейса", self)
        self.cb_popup.setChecked(self.config.popup_on_case_open)
        self.cb_popup.toggled.connect(self.on_popup_toggled)
        settings_layout.addWidget(self.cb_popup)

        self.cb_autostart = QCheckBox("Запуск вместе с Windows", self)
        self.cb_autostart.setChecked(self.config.launch_on_startup)
        self.cb_autostart.toggled.connect(self.on_autostart_toggled)
        settings_layout.addWidget(self.cb_autostart)

        self.cb_demo = QCheckBox("Режим демонстрации (Тест)", self)
        self.cb_demo.setChecked(self.config.demo_mode)
        self.cb_demo.toggled.connect(self.on_demo_toggled)
        settings_layout.addWidget(self.cb_demo)

        card_layout.addWidget(settings_section)

        # 5. Fix Windows Hands-Free Audio Button
        self.btn_audio_fix = QPushButton("Оптимизировать звук Windows (Стерео)", self)
        self.btn_audio_fix.setObjectName("ActionButton")
        self.btn_audio_fix.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_audio_fix.clicked.connect(self.on_audio_fix_clicked)
        card_layout.addWidget(self.btn_audio_fix)

        # 6. Exit Button
        btn_row = QHBoxLayout()
        self.btn_exit = QPushButton("Выход", self)
        self.btn_exit.setObjectName("DangerButton")
        self.btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit.clicked.connect(QApplication.instance().quit)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_exit)
        card_layout.addLayout(btn_row)

        root_layout.addWidget(self.card)
        self.setFixedSize(360, 480)

    def update_state(self, state: AirPodsState):
        """Refreshes the UI with the latest AirPodsState."""
        self.lbl_device_name.setText(state.device_name)
        status_txt = "Подключено" if state.connected else "Не подключено"
        if state.connected and state.rssi != -100:
            status_txt += f" • {state.rssi} dBm"
        self.lbl_status.setText(status_txt)

        self.card_left.setData(state.left_battery, state.left_charging, state.left_in_ear)
        self.card_right.setData(state.right_battery, state.right_charging, state.right_in_ear)
        self.card_case.setData(state.case_battery, state.case_charging, False)

        self.noise_selector.set_mode(state.noise_mode, user_click=False)

    def on_noise_mode_selected(self, mode: NoiseControlMode):
        self.device_manager.set_noise_mode(mode)

    def on_autopause_toggled(self, checked: bool):
        self.config.auto_pause_enabled = checked
        self.config.save()

    def on_popup_toggled(self, checked: bool):
        self.config.popup_on_case_open = checked
        self.config.save()

    def on_autostart_toggled(self, checked: bool):
        self.config.launch_on_startup = checked
        self.config.save()
        set_launch_on_startup(checked)

    def on_demo_toggled(self, checked: bool):
        self.config.demo_mode = checked
        self.config.save()
        if checked:
            self.device_manager.start_demo_mode()
        else:
            self.device_manager.stop_demo_mode()

    def on_audio_fix_clicked(self):
        dev_name = ""
        if self.device_manager.current_state:
            dev_name = self.device_manager.current_state.device_name
        success, msg = AudioController.fix_handsfree_audio(dev_name)
        self.btn_audio_fix.setText("✓ Качество зафиксировано!" if success else f"Инфо: {msg}")

    def toggle_at_position(self, pos: QPoint):
        """Shows or hides the flyout positioned neatly near tray icon."""
        if self.isVisible():
            self.hide()
        else:
            screen = QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                x = min(pos.x() - self.width() // 2, geom.right() - self.width() - 10)
                x = max(10, x)
                # Position above taskbar
                y = geom.bottom() - self.height() - 10
                self.move(x, y)
            self.show()
            self.activateWindow()
