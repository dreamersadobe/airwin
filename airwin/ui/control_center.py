"""Windows 11 Quick Settings style flyout window for AirPods management."""

import sys
from typing import Optional

from airwin.config import AppConfig
from airwin.core.device_manager import DeviceManager
from airwin.core.models import AirPodsState, NoiseControlMode
from airwin.core.windows_audio import AudioController
from airwin.ui.components import BatteryCardWidget, FluentToggleSwitch, NoiseSegmentedControl
from airwin.ui.dwm import enable_dwm_transparency
from airwin.ui.qt_compat import (
    QtCore,
    QApplication,
    QColor,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPainter,
    QPainterPath,
    QPen,
    QPoint,
    QPushButton,
    QRectF,
    Qt,
    QVBoxLayout,
)
from airwin.ui.styles import CONTROL_CENTER_STYLE
from airwin.utils.autostart import set_launch_on_startup


class ControlCenterFlyout(QDialog):
    """Windows 11 Quick Settings style flyout opened when clicking the tray icon."""

    def __init__(self, device_manager: DeviceManager, config: AppConfig, parent=None):
        super().__init__(parent)
        self.device_manager = device_manager
        self.config = config

        self.setObjectName("ControlCenterRoot")
        self.setStyleSheet(CONTROL_CENTER_STYLE)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # 1. Header (Device Name, Status, and Close Button)
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

        self.btn_close = QPushButton("✕", self)
        self.btn_close.setObjectName("CloseToolButton")
        self.btn_close.setFixedSize(26, 26)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.hide)
        header_layout.addWidget(self.btn_close)

        layout.addLayout(header_layout)

        # 2. Battery Grid (Left, Right, Case)
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
        layout.addWidget(battery_frame)

        # 3. Noise Control (Шумоподавление) Section
        anc_section = QFrame(self)
        anc_section.setObjectName("SectionCard")
        anc_layout = QVBoxLayout(anc_section)
        anc_layout.setContentsMargins(10, 8, 10, 8)
        anc_layout.setSpacing(6)

        lbl_anc_title = QLabel("Управление шумом", self)
        lbl_anc_title.setObjectName("SectionTitle")
        anc_layout.addWidget(lbl_anc_title)

        self.noise_selector = NoiseSegmentedControl(self)
        self.noise_selector.mode_changed.connect(self.on_noise_mode_selected)
        anc_layout.addWidget(self.noise_selector)

        layout.addWidget(anc_section)

        # 4. Settings Section with Native Windows 11 Toggle Switches
        settings_section = QFrame(self)
        settings_section.setObjectName("SectionCard")
        settings_layout = QVBoxLayout(settings_section)
        settings_layout.setContentsMargins(12, 10, 12, 10)
        settings_layout.setSpacing(6)

        lbl_settings_title = QLabel("Параметры", self)
        lbl_settings_title.setObjectName("SectionTitle")
        settings_layout.addWidget(lbl_settings_title)

        self.sw_autopause = FluentToggleSwitch("Автопауза при снятии наушника", self.config.auto_pause_enabled, self)
        self.sw_autopause.toggled.connect(self.on_autopause_toggled)
        settings_layout.addWidget(self.sw_autopause)

        self.sw_popup = FluentToggleSwitch("Всплывающее окно при открытии кейса", self.config.popup_on_case_open, self)
        self.sw_popup.toggled.connect(self.on_popup_toggled)
        settings_layout.addWidget(self.sw_popup)

        self.sw_autostart = FluentToggleSwitch("Запуск вместе с Windows", self.config.launch_on_startup, self)
        self.sw_autostart.toggled.connect(self.on_autostart_toggled)
        settings_layout.addWidget(self.sw_autostart)

        self.sw_demo = FluentToggleSwitch("Режим демонстрации (Тест)", self.config.demo_mode, self)
        self.sw_demo.toggled.connect(self.on_demo_toggled)
        settings_layout.addWidget(self.sw_demo)

        layout.addWidget(settings_section)

        # 5. Fix Windows Hands-Free Audio Button
        self.btn_audio_fix = QPushButton("Оптимизировать звук Windows (Стерео)", self)
        self.btn_audio_fix.setObjectName("ActionButton")
        self.btn_audio_fix.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_audio_fix.clicked.connect(self.on_audio_fix_clicked)
        layout.addWidget(self.btn_audio_fix)

        # 6. Exit Button Row
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        self.btn_exit = QPushButton("Выход из AirWin", self)
        self.btn_exit.setObjectName("DangerButton")
        self.btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit.clicked.connect(QApplication.instance().quit)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_exit)
        layout.addLayout(btn_row)

        self.setFixedSize(350, 480)

    def paintEvent(self, event):
        """Draws clean Windows 11 Fluent dark Acrylic background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)

        # Windows 11 Dark Acrylic
        painter.fillPath(path, QColor(32, 32, 32, 248))

        # Windows 11 1px border
        painter.setPen(QPen(QColor(255, 255, 255, 26), 1))
        painter.drawPath(path)

    def showEvent(self, event):
        super().showEvent(event)
        enable_dwm_transparency(self)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                self.hide()

    def update_state(self, state: AirPodsState):
        """Refreshes the UI with the latest AirPodsState."""
        self.lbl_device_name.setText(state.device_name)
        status_txt = "● Подключено" if state.connected else "● Не подключено"
        if state.connected and state.rssi != -100:
            status_txt += f"  ({state.rssi} dBm)"
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
                x = min(pos.x() - self.width() // 2, geom.right() - self.width() - 12)
                x = max(12, x)
                # Position above taskbar
                y = geom.bottom() - self.height() - 12
                self.move(x, y)
            self.show()
            self.activateWindow()
