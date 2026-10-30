"""macOS-inspired visual language for AirWin.

Defines the translucent "vibrancy" palette, typography helpers and the Qt
style sheet used by the popup card and the Control Center flyout.
"""

from dataclasses import dataclass

from airwin.ui.qt_compat import QColor, QFont

FONT_TEXT = '"SF Pro Text", "Segoe UI Variable Text", "Segoe UI", sans-serif'
FONT_DISPLAY = '"SF Pro Display", "SF Pro Text", "Segoe UI Variable Display", "Segoe UI", sans-serif'


def css(color: QColor) -> str:
    """Converts a QColor to a CSS rgba() string for Qt style sheets."""
    return (
        f"rgba({color.red()}, {color.green()}, {color.blue()}, "
        f"{color.alphaF():.3f})"
    )


def mac_font(size: float, weight: QFont.Weight = QFont.Weight.Normal, display: bool = False) -> QFont:
    """Builds a font with macOS SF Pro first and Segoe UI as fallback."""
    font = QFont()
    families = (
        ["SF Pro Display", "SF Pro Text", "Segoe UI Variable Display", "Segoe UI"]
        if display
        else ["SF Pro Text", "Segoe UI Variable Text", "Segoe UI"]
    )
    try:
        font.setFamilies(families)
    except Exception:
        font.setFamily(families[-1])
    font.setPixelSize(max(1, int(round(size))))
    font.setWeight(weight)
    return font


def with_alpha(color: QColor, alpha: int) -> QColor:
    result = QColor(color)
    result.setAlpha(max(0, min(255, alpha)))
    return result


def blend(first: QColor, second: QColor, t: float) -> QColor:
    """Linear interpolation between two colors (including alpha)."""
    t = max(0.0, min(1.0, t))
    return QColor(
        int(first.red() + (second.red() - first.red()) * t),
        int(first.green() + (second.green() - first.green()) * t),
        int(first.blue() + (second.blue() - first.blue()) * t),
        int(first.alpha() + (second.alpha() - first.alpha()) * t),
    )


@dataclass(frozen=True)
class MacTheme:
    dark: bool

    panel_top: QColor
    panel_bottom: QColor
    panel_border: QColor
    panel_highlight: QColor

    text_primary: QColor
    text_secondary: QColor
    text_tertiary: QColor

    separator: QColor
    card_bg: QColor
    card_bg_hover: QColor
    card_border: QColor

    control_bg: QColor
    control_bg_hover: QColor

    accent: QColor
    accent_text: QColor
    green: QColor
    amber: QColor
    red: QColor

    switch_off: QColor
    switch_knob: QColor

    def qss(self) -> str:
        primary = css(self.text_primary)
        secondary = css(self.text_secondary)
        tertiary = css(self.text_tertiary)
        card_bg = css(self.card_bg)
        card_border = css(self.card_border)
        card_hover = css(self.card_bg_hover)
        accent = css(self.accent)
        accent_text = css(self.accent_text)
        red = css(self.red)
        return f"""
        QWidget {{
            font-family: {FONT_TEXT};
            font-size: 13px;
            color: {primary};
        }}

        QLabel {{
            background: transparent;
            color: {primary};
        }}

        QLabel#PopupTitle {{
            font-family: {FONT_DISPLAY};
            font-size: 17px;
            font-weight: 600;
            color: {primary};
        }}

        QLabel#PopupStatus {{
            font-size: 11px;
            font-weight: 500;
            color: {secondary};
        }}

        QLabel#HeaderDeviceName {{
            font-family: {FONT_DISPLAY};
            font-size: 16px;
            font-weight: 600;
            color: {primary};
        }}

        QLabel#HeaderStatus {{
            font-size: 11px;
            font-weight: 500;
            color: {secondary};
        }}

        QLabel#SectionTitle {{
            font-size: 11px;
            font-weight: 600;
            color: {tertiary};
        }}

        QLabel#SettingLabel {{
            font-size: 13px;
            font-weight: 400;
            color: {primary};
        }}

        QPushButton#MacActionButton {{
            background-color: {card_bg};
            color: {primary};
            border: 1px solid {card_border};
            border-radius: 10px;
            padding: 8px 14px;
            font-size: 13px;
            font-weight: 500;
        }}

        QPushButton#MacActionButton:hover {{
            background-color: {card_hover};
        }}

        QPushButton#MacActionButton:pressed {{
            background-color: {css(with_alpha(self.text_primary, 26))};
        }}

        QPushButton#MacGhostButton {{
            background: transparent;
            color: {secondary};
            border: none;
            border-radius: 8px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 500;
        }}

        QPushButton#MacGhostButton:hover {{
            color: {red};
            background-color: {css(with_alpha(self.red, 22))};
        }}

        QPushButton#MacGhostButton:pressed {{
            background-color: {css(with_alpha(self.red, 36))};
        }}

        QToolTip {{
            background-color: {css(self.panel_bottom)};
            color: {primary};
            border: 1px solid {css(self.panel_border)};
            padding: 5px 8px;
        }}
        """


def light_theme() -> MacTheme:
    return MacTheme(
        dark=False,
        panel_top=QColor(252, 252, 253, 244),
        panel_bottom=QColor(238, 238, 243, 246),
        panel_border=QColor(0, 0, 0, 26),
        panel_highlight=QColor(255, 255, 255, 230),
        text_primary=QColor(29, 29, 31),
        text_secondary=QColor(60, 60, 67, 150),
        text_tertiary=QColor(60, 60, 67, 105),
        separator=QColor(60, 60, 67, 34),
        card_bg=QColor(255, 255, 255, 168),
        card_bg_hover=QColor(255, 255, 255, 220),
        card_border=QColor(0, 0, 0, 16),
        control_bg=QColor(120, 120, 128, 28),
        control_bg_hover=QColor(120, 120, 128, 48),
        accent=QColor(0, 122, 255),
        accent_text=QColor(255, 255, 255),
        green=QColor(52, 199, 89),
        amber=QColor(255, 159, 10),
        red=QColor(255, 59, 48),
        switch_off=QColor(120, 120, 128, 78),
        switch_knob=QColor(255, 255, 255),
    )


def dark_theme() -> MacTheme:
    return MacTheme(
        dark=True,
        panel_top=QColor(46, 46, 49, 244),
        panel_bottom=QColor(28, 28, 30, 246),
        panel_border=QColor(255, 255, 255, 26),
        panel_highlight=QColor(255, 255, 255, 34),
        text_primary=QColor(245, 245, 247),
        text_secondary=QColor(235, 235, 245, 150),
        text_tertiary=QColor(235, 235, 245, 105),
        separator=QColor(235, 235, 245, 32),
        card_bg=QColor(255, 255, 255, 20),
        card_bg_hover=QColor(255, 255, 255, 34),
        card_border=QColor(255, 255, 255, 18),
        control_bg=QColor(255, 255, 255, 20),
        control_bg_hover=QColor(255, 255, 255, 38),
        accent=QColor(10, 132, 255),
        accent_text=QColor(255, 255, 255),
        green=QColor(48, 209, 88),
        amber=QColor(255, 214, 10),
        red=QColor(255, 69, 58),
        switch_off=QColor(120, 120, 128, 110),
        switch_knob=QColor(255, 255, 255),
    )


def get_theme(dark: bool = False) -> MacTheme:
    return dark_theme() if dark else light_theme()
