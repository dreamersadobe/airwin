"""System Tray integration with dynamic AirPods battery icon and menu."""

from typing import Optional

from airwin.config import AppConfig
from airwin.core.device_manager import DeviceManager
from airwin.core.models import AirPodsState
from airwin.ui.components import get_battery_color
from airwin.ui.control_center import ControlCenterFlyout
from airwin.ui.popup_card import AirPodsPopupCard
from airwin.ui.qt_compat import (
    QAction,
    QApplication,
    QColor,
    QCursor,
    QFont,
    QIcon,
    QMenu,
    QPainter,
    QPixmap,
    QRect,
    QRectF,
    QSystemTrayIcon,
    Qt,
)


class AirPodsTrayIcon(QSystemTrayIcon):
    """System Tray icon with live battery badge and macOS-like flyout."""

    def __init__(
        self,
        device_manager: DeviceManager,
        config: AppConfig,
        control_center: ControlCenterFlyout,
        popup_card: AirPodsPopupCard,
        parent=None,
    ):
        super().__init__(parent)
        self.device_manager = device_manager
        self.config = config
        self.control_center = control_center
        self.popup_card = popup_card

        self._current_state: Optional[AirPodsState] = None

        self._init_menu()
        self._update_icon()

        self.activated.connect(self._on_tray_activated)

    def _init_menu(self):
        menu = QMenu()

        act_control = menu.addAction("Центр управления AirPods")
        act_control.triggered.connect(self._open_control_center)

        act_popup = menu.addAction("Показать карточку статуса")
        act_popup.triggered.connect(self._show_popup_card)

        menu.addSeparator()

        self.act_demo = menu.addAction("Режим демонстрации (Тест)")
        self.act_demo.setCheckable(True)
        self.act_demo.setChecked(self.config.demo_mode)
        self.act_demo.triggered.connect(self._toggle_demo)

        menu.addSeparator()

        act_quit = menu.addAction("Выход")
        act_quit.triggered.connect(QApplication.instance().quit)

        self.setContextMenu(menu)

    def update_state(self, state: AirPodsState):
        """Updates tooltip and dynamic tray icon."""
        self._current_state = state

        # Tooltip
        if state.connected:
            bat_parts = []
            if state.left_battery >= 0:
                bat_parts.append(f"L: {state.left_battery}%{'⚡' if state.left_charging else ''}")
            if state.right_battery >= 0:
                bat_parts.append(f"R: {state.right_battery}%{'⚡' if state.right_charging else ''}")
            if state.case_battery >= 0:
                bat_parts.append(f"Кейс: {state.case_battery}%{'⚡' if state.case_charging else ''}")

            bat_str = " | ".join(bat_parts) if bat_parts else "Подключено"
            tooltip = f"{state.device_name}\n{bat_str}\nШумоподавление: {state.noise_mode.value}"
        else:
            tooltip = f"AirWin — {state.device_name} (Не подключено)"

        self.setToolTip(tooltip)
        self._update_icon()

    def _update_icon(self):
        """Generates dynamic crisp 64x64 tray icon."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Base AirPods earbud glyph
        painter.setPen(Qt.PenStyle.NoPen)
        alpha = 240 if (self._current_state and self._current_state.connected) else 120
        painter.setBrush(QColor(255, 255, 255, alpha))

        # Draw left earbud shape
        painter.drawRoundedRect(QRectF(14, 12, 14, 20), 7, 7)
        painter.drawRoundedRect(QRectF(19, 24, 6, 26), 3, 3)

        # Draw right earbud shape
        painter.drawRoundedRect(QRectF(36, 12, 14, 20), 7, 7)
        painter.drawRoundedRect(QRectF(39, 24, 6, 26), 3, 3)

        # Battery percentage badge overlay
        if self._current_state and self._current_state.connected and self.config.tray_show_percentage:
            avg_bat = self._current_state.average_earbud_battery
            if avg_bat >= 0:
                # Pill badge at bottom
                badge_rect = QRectF(2, 42, 60, 20)
                painter.setBrush(get_battery_color(avg_bat))
                painter.drawRoundedRect(badge_rect, 10, 10)

                painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"{avg_bat}%")

        painter.end()
        self.setIcon(QIcon(pixmap))

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            cursor_pos = QCursor.pos()
            self.control_center.toggle_at_position(cursor_pos)

    def _open_control_center(self):
        cursor_pos = QCursor.pos()
        self.control_center.toggle_at_position(cursor_pos)

    def _show_popup_card(self):
        state = self._current_state or AirPodsState(connected=False, device_name="AirPods")
        self.popup_card.show_for_state(state)

    def _toggle_demo(self, checked: bool):
        self.config.demo_mode = checked
        self.config.save()
        if checked:
            self.device_manager.start_demo_mode()
        else:
            self.device_manager.stop_demo_mode()
