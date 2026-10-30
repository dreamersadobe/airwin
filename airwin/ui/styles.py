"""macOS Big Sur / Sonoma design system styling and color palette."""

MACOS_DARK_PALETTE = {
    "bg": "rgba(32, 33, 36, 0.94)",
    "card_bg": "rgba(48, 49, 53, 0.85)",
    "card_bg_hover": "rgba(62, 63, 68, 0.95)",
    "card_border": "rgba(255, 255, 255, 0.12)",
    "text_primary": "#FFFFFF",
    "text_secondary": "rgba(235, 235, 245, 0.6)",
    "text_tertiary": "rgba(235, 235, 245, 0.38)",
    "accent_blue": "#0A84FF",
    "accent_blue_hover": "#409CFF",
    "battery_green": "#30D158",
    "battery_amber": "#FF9F0A",
    "battery_red": "#FF453A",
    "separator": "rgba(255, 255, 255, 0.08)",
    "pill_inactive": "rgba(255, 255, 255, 0.08)",
    "pill_active": "#0A84FF",
    "pill_text_active": "#FFFFFF",
    "pill_text_inactive": "rgba(255, 255, 255, 0.75)",
}

POPUP_CARD_STYLE = """
QDialog, QWidget#PopupRoot {
    background-color: transparent;
}

QFrame#PopupContainer {
    background-color: rgba(30, 32, 35, 0.96);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 24px;
}

QLabel#PopupTitle {
    color: #FFFFFF;
    font-size: 18px;
    font-weight: 700;
    font-family: "Segoe UI", -apple-system, "SF Pro Display", sans-serif;
}

QLabel#PopupSubtitle {
    color: #30D158;
    font-size: 13px;
    font-weight: 500;
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
}

QPushButton#DoneButton {
    background-color: #0A84FF;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 600;
    border: none;
    border-radius: 12px;
    padding: 8px 24px;
}

QPushButton#DoneButton:hover {
    background-color: #409CFF;
}

QPushButton#DoneButton:pressed {
    background-color: #0071E3;
}
"""

CONTROL_CENTER_STYLE = """
QDialog#ControlCenterRoot, QWidget#ControlCenterRoot {
    background-color: transparent;
}

QFrame#ControlCenterCard {
    background-color: rgba(30, 32, 36, 0.96);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 20px;
}

QLabel#HeaderDeviceName {
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 700;
    font-family: "Segoe UI", -apple-system, "SF Pro Display", sans-serif;
}

QLabel#HeaderSubtitle {
    color: rgba(235, 235, 245, 0.6);
    font-size: 12px;
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
}

QFrame#SectionCard {
    background-color: rgba(48, 50, 54, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
}

QLabel#SectionTitle {
    color: rgba(235, 235, 245, 0.5);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
}

QPushButton#PillButton {
    background-color: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.75);
    border: none;
    border-radius: 10px;
    padding: 7px 12px;
    font-size: 12px;
    font-weight: 500;
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
}

QPushButton#PillButton:hover {
    background-color: rgba(255, 255, 255, 0.14);
    color: #FFFFFF;
}

QPushButton#PillButton[active="true"] {
    background-color: #0A84FF;
    color: #FFFFFF;
    font-weight: 600;
}

QCheckBox {
    color: rgba(255, 255, 255, 0.85);
    font-size: 13px;
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    background-color: rgba(255, 255, 255, 0.05);
}

QCheckBox::indicator:checked {
    background-color: #0A84FF;
    border: 1px solid #0A84FF;
}

QPushButton#ActionButton {
    background-color: rgba(255, 255, 255, 0.08);
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#ActionButton:hover {
    background-color: rgba(255, 255, 255, 0.15);
}

QPushButton#DangerButton {
    background-color: rgba(255, 69, 58, 0.15);
    color: #FF453A;
    border: none;
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#DangerButton:hover {
    background-color: rgba(255, 69, 58, 0.25);
}
"""
