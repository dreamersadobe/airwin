"""macOS Big Sur / Sonoma design system styling and color palette."""

MACOS_DARK_PALETTE = {
    "bg": "rgba(30, 32, 36, 0.98)",
    "card_bg": "rgba(45, 47, 51, 0.85)",
    "card_bg_hover": "rgba(60, 62, 68, 0.95)",
    "card_border": "rgba(255, 255, 255, 0.12)",
    "text_primary": "#FFFFFF",
    "text_secondary": "rgba(235, 235, 245, 0.6)",
    "text_tertiary": "rgba(235, 235, 245, 0.38)",
    "accent_blue": "#0A84FF",
    "accent_blue_hover": "#409CFF",
    "battery_green": "#30D158",
    "battery_amber": "#FF9F0A",
    "battery_red": "#FF453A",
}

POPUP_CARD_STYLE = """
QLabel#PopupTitle {
    color: #FFFFFF;
    font-size: 17px;
    font-weight: 700;
    font-family: "Segoe UI", -apple-system, "SF Pro Display", sans-serif;
}

QLabel#PopupSubtitle {
    color: #30D158;
    font-size: 13px;
    font-weight: 600;
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
}

QPushButton#DoneButton {
    background-color: #0A84FF;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 600;
    border: none;
    border-radius: 12px;
    padding: 8px 28px;
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
}

QPushButton#DoneButton:hover {
    background-color: #409CFF;
}

QPushButton#DoneButton:pressed {
    background-color: #0071E3;
}
"""

CONTROL_CENTER_STYLE = """
QLabel#HeaderDeviceName {
    color: #FFFFFF;
    font-size: 17px;
    font-weight: 700;
    font-family: "Segoe UI", -apple-system, "SF Pro Display", sans-serif;
}

QLabel#HeaderSubtitle {
    color: rgba(235, 235, 245, 0.65);
    font-size: 12px;
    font-weight: 500;
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
}

QFrame#SectionCard {
    background-color: rgba(45, 47, 51, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
}

QLabel#SectionTitle {
    color: rgba(235, 235, 245, 0.55);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
}

QPushButton#PillButton {
    background-color: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.05);
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
    border: 1px solid #0A84FF;
    color: #FFFFFF;
    font-weight: 600;
}

QCheckBox {
    color: rgba(255, 255, 255, 0.9);
    font-size: 13px;
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border-radius: 5px;
    border: 1px solid rgba(255, 255, 255, 0.35);
    background-color: rgba(255, 255, 255, 0.06);
}

QCheckBox::indicator:hover {
    border: 1px solid rgba(255, 255, 255, 0.55);
}

QCheckBox::indicator:checked {
    background-color: #0A84FF;
    border: 1px solid #0A84FF;
}

QPushButton#ActionButton {
    background-color: rgba(255, 255, 255, 0.08);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
}

QPushButton#ActionButton:hover {
    background-color: rgba(255, 255, 255, 0.16);
}

QPushButton#DangerButton {
    background-color: rgba(255, 69, 58, 0.15);
    color: #FF453A;
    border: 1px solid rgba(255, 69, 58, 0.25);
    border-radius: 10px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 600;
    font-family: "Segoe UI", -apple-system, "SF Pro Text", sans-serif;
}

QPushButton#DangerButton:hover {
    background-color: rgba(255, 69, 58, 0.28);
}

QPushButton#CloseToolButton {
    background-color: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.7);
    border: none;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 700;
}

QPushButton#CloseToolButton:hover {
    background-color: rgba(255, 255, 255, 0.18);
    color: #FFFFFF;
}
"""
