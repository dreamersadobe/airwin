"""AirWin - macOS-like AirPods Manager for Windows.

Main application entry point.
"""

import argparse
import logging
import signal
import sys

from airwin.config import AppConfig
from airwin.core.bridge import AirWinBridge
from airwin.core.device_manager import DeviceManager
from airwin.core.models import AirPodsState
from airwin.ui.control_center import ControlCenterFlyout
from airwin.ui.popup_card import AirPodsPopupCard
from airwin.ui.qt_compat import QApplication, QSystemTrayIcon
from airwin.ui.styles import get_theme, mac_font
from airwin.ui.tray_icon import AirPodsTrayIcon

logger = logging.getLogger("airwin")


def parse_args():
    parser = argparse.ArgumentParser(
        description="AirWin — Управление AirPods в стиле macOS для Windows."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Запустить в режиме демонстрации (симуляция AirPods Pro).",
    )
    parser.add_argument(
        "--no-popup",
        action="store_true",
        help="Отключить всплывающее окно при открытии кейса.",
    )
    parser.add_argument(
        "--mac",
        type=str,
        default="",
        help="MAC-адрес конкретных AirPods для фильтрации BLE-сигналов.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Включить подробный вывод отладочных сообщений.",
    )
    appearance = parser.add_mutually_exclusive_group()
    appearance.add_argument(
        "--light",
        action="store_true",
        help="Принудительно использовать светлое оформление macOS.",
    )
    appearance.add_argument(
        "--dark",
        action="store_true",
        help="Принудительно использовать тёмное оформление macOS.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%H:%M:%S",
    )

    logger.info("Initializing AirWin...")

    # Load configuration
    config = AppConfig.load()
    if args.demo:
        config.demo_mode = True
    if args.no_popup:
        config.popup_on_case_open = False
    if args.mac:
        config.preferred_device_mac = args.mac
    if args.light:
        config.dark_mode = False
    if args.dark:
        config.dark_mode = True

    theme = get_theme(config.dark_mode)

    # Create Qt Application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("AirWin")
    app.setOrganizationName("AirWin")
    app.setFont(mac_font(13))

    # Check for System Tray support
    if not QSystemTrayIcon.isSystemTrayAvailable():
        logger.warning("System tray is not available on this system.")

    # UI Components
    popup_card = AirPodsPopupCard(config, theme)

    # Thread-Safe Qt Bridge: bridges background threads to Qt Main GUI Thread
    bridge = AirWinBridge()

    def on_state_updated_gui(state: AirPodsState):
        try:
            tray_icon.update_state(state)
            control_center.update_state(state)
        except Exception as e:
            logger.debug(f"GUI state update error: {e}")

    def on_case_opened_gui(state: AirPodsState):
        try:
            popup_card.show_for_state(state)
        except Exception as e:
            logger.debug(f"GUI case popup error: {e}")

    bridge.state_changed.connect(on_state_updated_gui)
    bridge.case_opened.connect(on_case_opened_gui)

    # Core Device Manager (emits thread-safe signals via bridge)
    device_manager = DeviceManager(
        config=config,
        on_state_changed=bridge.state_changed.emit,
        on_case_opened=bridge.case_opened.emit,
    )

    control_center = ControlCenterFlyout(
        device_manager=device_manager,
        config=config,
        theme=theme,
    )
    control_center.theme_changed.connect(
        lambda dark: popup_card.set_theme(get_theme(dark))
    )
    tray_icon = AirPodsTrayIcon(
        device_manager=device_manager,
        config=config,
        control_center=control_center,
        popup_card=popup_card,
    )
    control_center.theme_changed.connect(
        lambda dark: tray_icon.set_theme(get_theme(dark))
    )

    tray_icon.show()

    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, lambda *_: app.quit())

    # Start BLE listening or demo mode
    device_manager.start()

    logger.info("AirWin is running in system tray. Press Ctrl+C or use tray menu to exit.")

    try:
        ret = app.exec()
    finally:
        device_manager.stop()

    sys.exit(ret)


if __name__ == "__main__":
    main()
