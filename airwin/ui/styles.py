"""Windows 11 Fluent Design System styling, typography, and color palette."""

WIN11_DARK_PALETTE = {
    "bg_acrylic": "rgba(32, 32, 32, 0.94)",
    "card_bg": "rgba(255, 255, 255, 0.05)",
    "card_bg_hover": "rgba(255, 255, 255, 0.08)",
    "card_border": "rgba(255, 255, 255, 0.08)",
    "card_border_hover": "rgba(255, 255, 255, 0.14)",
    "text_primary": "#FFFFFF",
    "text_secondary": "rgba(255, 255, 255, 0.70)",
    "text_tertiary": "rgba(255, 255, 255, 0.45)",
    "accent_blue": "#0067C0",
    "accent_light": "#4CC2FF",
    "accent_hover": "#1975C5",
    "battery_green": "#6CCB5F",
    "battery_amber": "#FCE100",
    "battery_red": "#FF99A4",
}

POPUP_CARD_STYLE = """
QLabel#PopupTitle {
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 600;
    font-family: "Segoe UI Variable Display", "Segoe UI", sans-serif;
}

QLabel#PopupSubtitle {
    color: #4CC2FF;
    font-size: 12px;
    font-weight: 500;
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
}

QPushButton#DoneButton {
    background-color: #0067C0;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 7px 24px;
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
}

QPushButton#DoneButton:hover {
    background-color: #1975C5;
}

QPushButton#DoneButton:pressed {
    background-color: #005A9E;
}
"""

CONTROL_CENTER_STYLE = """
QLabel#HeaderDeviceName {
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 600;
    font-family: "Segoe UI Variable Display", "Segoe UI", sans-serif;
}

QLabel#HeaderSubtitle {
    color: rgba(255, 255, 255, 0.65);
    font-size: 12px;
    font-weight: 400;
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
}

QFrame#SectionCard {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 8px;
}

QLabel#SectionTitle {
    color: rgba(255, 255, 255, 0.6);
    font-size: 12px;
    font-weight: 600;
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
}

QPushButton#PillButton {
    background-color: transparent;
    color: rgba(255, 255, 255, 0.75);
    border: none;
    border-radius: 5px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 500;
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
}

QPushButton#PillButton:hover {
    background-color: rgba(255, 255, 255, 0.08);
    color: #FFFFFF;
}

QPushButton#PillButton[active="true"] {
    background-color: #0067C0;
    color: #FFFFFF;
    font-weight: 600;
}

QPushButton#ActionButton {
    background-color: rgba(255, 255, 255, 0.06);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
}

QPushButton#ActionButton:hover {
    background-color: rgba(255, 255, 255, 0.10);
    border: 1px solid rgba(255, 255, 255, 0.15);
}

QPushButton#DangerButton {
    background-color: rgba(255, 69, 58, 0.12);
    color: #FF99A4;
    border: 1px solid rgba(255, 69, 58, 0.2);
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 600;
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
}

QPushButton#DangerButton:hover {
    background-color: rgba(255, 69, 58, 0.22);
}

QPushButton#CloseToolButton {
    background-color: transparent;
    color: rgba(255, 255, 255, 0.65);
    border: none;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    font-family: "Segoe UI", sans-serif;
}

QPushButton#CloseToolButton:hover {
    background-color: rgba(255, 255, 255, 0.12);
    color: #FFFFFF;
}
"""
