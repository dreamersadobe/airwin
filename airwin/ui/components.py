"""Custom-painted macOS-style widgets for AirWin.

Everything here is drawn with QPainter so the UI stays crisp at any DPI and
does not depend on platform icon fonts or emoji rendering.
"""

from airwin.core.models import NoiseControlMode
from airwin.ui.dwm import apply_window_appearance
from airwin.ui.qt_compat import (
    Property,
    QEasingCurve,
    QBrush,
    QColor,
    QDialog,
    QFont,
    QHBoxLayout,
    QLabel,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    QVBoxLayout,
    QWidget,
    Signal,
)
from airwin.ui.styles import MacTheme, blend, mac_font, with_alpha


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------

def draw_earbud(painter: QPainter, rect: QRectF, color: QColor) -> None:
    """Filled AirPods earbud silhouette (bud + stem)."""
    w, h = rect.width(), rect.height()
    head = QRectF(rect.x() + w * 0.12, rect.y(), w * 0.76, h * 0.62)
    stem = QRectF(rect.x() + w * 0.38, rect.y() + h * 0.44, w * 0.24, h * 0.56)

    path = QPainterPath()
    path.addEllipse(head)
    stem_path = QPainterPath()
    stem_path.addRoundedRect(stem, w * 0.14, w * 0.14)

    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawPath(path.united(stem_path))
    painter.restore()


def draw_case(painter: QPainter, rect: QRectF, color: QColor) -> None:
    """Filled charging case silhouette with a lid seam."""
    w, h = rect.width(), rect.height()
    radius = w * 0.26

    lid = QPainterPath()
    lid.addRoundedRect(QRectF(rect.x(), rect.y(), w, h * 0.34), radius, radius)
    body = QPainterPath()
    body.addRoundedRect(
        QRectF(rect.x(), rect.y() + h * 0.40, w, h * 0.60), radius, radius
    )

    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawPath(lid)
    painter.drawPath(body)
    painter.restore()


def draw_bolt(painter: QPainter, rect: QRectF, color: QColor) -> None:
    w, h = rect.width(), rect.height()
    points = [
        QPointF(rect.x() + w * 0.58, rect.y()),
        QPointF(rect.x() + w * 0.16, rect.y() + h * 0.56),
        QPointF(rect.x() + w * 0.46, rect.y() + h * 0.56),
        QPointF(rect.x() + w * 0.38, rect.y() + h),
        QPointF(rect.x() + w * 0.84, rect.y() + h * 0.42),
        QPointF(rect.x() + w * 0.54, rect.y() + h * 0.42),
    ]
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawPolygon(points)
    painter.restore()


def _draw_waveform(painter: QPainter, rect: QRectF, color: QColor) -> None:
    fractions = (0.34, 0.62, 0.94, 0.62, 0.34)
    bar_w = rect.width() * 0.10
    gap = (rect.width() - bar_w * len(fractions)) / (len(fractions) - 1)
    center_y = rect.center().y()

    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    for index, fraction in enumerate(fractions):
        bar_h = rect.height() * fraction
        bar = QRectF(
            rect.x() + index * (bar_w + gap),
            center_y - bar_h / 2,
            bar_w,
            bar_h,
        )
        painter.drawRoundedRect(bar, bar_w / 2, bar_w / 2)
    painter.restore()


def draw_noise_icon(
    painter: QPainter, rect: QRectF, mode: NoiseControlMode, color: QColor
) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if mode == NoiseControlMode.NOISE_CANCELLATION:
        _draw_waveform(painter, rect, color)
        painter.setPen(
            QPen(color, max(1.5, rect.width() * 0.09), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawLine(
            QPointF(rect.x() + rect.width() * 0.18, rect.y() + rect.height() * 0.82),
            QPointF(rect.x() + rect.width() * 0.82, rect.y() + rect.height() * 0.18),
        )
    elif mode == NoiseControlMode.TRANSPARENCY:
        _draw_waveform(painter, rect, color)
    else:
        arc = rect.adjusted(
            rect.width() * 0.12,
            rect.height() * 0.12,
            -rect.width() * 0.12,
            -rect.height() * 0.12,
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(
            QPen(color, max(1.5, rect.width() * 0.10), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawArc(arc, 60 * 16, -300 * 16)
        painter.drawLine(
            QPointF(rect.center().x(), rect.y() + rect.height() * 0.06),
            QPointF(rect.center().x(), rect.center().y()),
        )
    painter.restore()


def battery_color(theme: MacTheme, percent: int) -> QColor:
    if percent > 20:
        return theme.green
    if percent > 10:
        return theme.amber
    return theme.red


# ---------------------------------------------------------------------------
# Battery tile
# ---------------------------------------------------------------------------

class BatteryItem(QWidget):
    """macOS-style battery capsule for the left bud, right bud or case."""

    def __init__(self, title: str, side: str, theme: MacTheme, parent=None):
        super().__init__(parent)
        self.title = title
        self.side = side
        self.theme = theme
        self.percent = -1
        self.charging = False
        self.in_ear = False
        self.setFixedSize(96, 54)

    def set_data(self, percent: int, charging: bool, in_ear: bool = False) -> None:
        self.percent = percent
        self.charging = charging
        self.in_ear = in_ear
        self.update()

    setData = set_data

    def set_theme(self, theme: MacTheme) -> None:
        self.theme = theme
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setFont(mac_font(10, QFont.Weight.Medium))
        painter.setPen(self.theme.text_tertiary)
        painter.drawText(
            QRectF(0, 0, self.width(), 14),
            Qt.AlignmentFlag.AlignCenter,
            self.title,
        )

        pill = QRectF(0, 18, self.width(), 36)
        pill_path = QPainterPath()
        pill_path.addRoundedRect(pill, 11, 11)

        painter.fillPath(pill_path, QBrush(self.theme.card_bg))
        painter.setPen(QPen(self.theme.card_border, 1))
        painter.drawPath(pill_path)

        if self.percent < 0:
            painter.setFont(mac_font(14, QFont.Weight.Medium))
            painter.setPen(self.theme.text_tertiary)
            painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, "—")
            return

        color = battery_color(self.theme, self.percent)

        painter.save()
        painter.setClipPath(pill_path)
        fill_width = max(0.0, pill.width() * self.percent / 100.0)
        painter.fillRect(
            QRectF(pill.x(), pill.y(), fill_width, pill.height()),
            QBrush(with_alpha(color, 46 if self.theme.dark else 34)),
        )
        painter.restore()

        glyph_rect = QRectF(pill.x() + 10, pill.y() + 9, 12, 18)
        if self.side == "case":
            draw_case(painter, glyph_rect, self.theme.text_primary)
        else:
            draw_earbud(painter, glyph_rect, self.theme.text_primary)

        text_rect = QRectF(pill.x() + 28, pill.y(), pill.width() - 40, pill.height())
        painter.setFont(mac_font(14, QFont.Weight.DemiBold))
        painter.setPen(self.theme.text_primary)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f"{self.percent}%",
        )

        if self.charging:
            draw_bolt(
                painter,
                QRectF(pill.right() - 19, pill.y() + 11, 10, 14),
                color,
            )
        elif self.in_ear:
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.theme.accent)
            painter.drawEllipse(
                QRectF(pill.right() - 15, pill.y() + 9, 6, 6)
            )
            painter.restore()


# ---------------------------------------------------------------------------
# Noise control
# ---------------------------------------------------------------------------

class NoiseButton(QWidget):
    """Circular noise-control button with an SF-style glyph and caption."""

    clicked = Signal(object)

    def __init__(self, mode: NoiseControlMode, caption: str, theme: MacTheme, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.caption = caption
        self.theme = theme
        self._active = False
        self._hover = False

        self.setFixedSize(100, 86)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.update()

    def is_active(self) -> bool:
        return self._active

    def set_theme(self, theme: MacTheme) -> None:
        self.theme = theme
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.mode)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        diameter = 56.0
        circle = QRectF((self.width() - diameter) / 2, 0, diameter, diameter)

        if self._active:
            fill = self.theme.accent
        elif self._hover:
            fill = self.theme.control_bg_hover
        else:
            fill = self.theme.control_bg

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        painter.drawEllipse(circle)

        if not self._active:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(self.theme.card_border, 1))
            painter.drawEllipse(circle.adjusted(0.5, 0.5, -0.5, -0.5))

        icon_color = self.theme.accent_text if self._active else self.theme.text_primary
        icon_rect = QRectF(
            circle.center().x() - 13,
            circle.center().y() - 13,
            26,
            26,
        )
        draw_noise_icon(painter, icon_rect, self.mode, icon_color)

        painter.setFont(mac_font(10, QFont.Weight.Medium))
        painter.setPen(self.theme.text_primary if self._active else self.theme.text_secondary)
        painter.drawText(
            QRectF(0, 60, self.width(), 26),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            self.caption,
        )


# ---------------------------------------------------------------------------
# Switch + settings rows
# ---------------------------------------------------------------------------

class MacSwitch(QWidget):
    """Animated macOS/iOS style switch."""

    toggled = Signal(bool)

    def __init__(self, checked: bool = False, theme: MacTheme = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._checked = checked
        self._knob = 1.0 if checked else 0.0

        self.setFixedSize(40, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._anim = QPropertyAnimation(self, b"knob", self)
        self._anim.setDuration(170)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _get_knob(self) -> float:
        return self._knob

    def _set_knob(self, value: float) -> None:
        self._knob = value
        self.update()

    knob = Property(float, _get_knob, _set_knob)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool, animate: bool = True) -> None:
        if self._checked == checked:
            return
        self._checked = checked
        target = 1.0 if checked else 0.0
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._knob)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._set_knob(target)

    def set_theme(self, theme: MacTheme) -> None:
        self.theme = theme
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            self.toggled.emit(self._checked)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.setChecked(not self._checked)
            self.toggled.emit(self._checked)
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        if self.theme is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track = QRectF(0.5, 1.5, 39, 21)
        track_color = blend(self.theme.switch_off, self.theme.green, self._knob)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track, 10.5, 10.5)

        knob_x = 3.0 + self._knob * 16.0
        painter.setBrush(QColor(0, 0, 0, 38))
        painter.drawEllipse(QRectF(knob_x, 4.0, 18, 18))
        painter.setBrush(self.theme.switch_knob)
        painter.drawEllipse(QRectF(knob_x, 3.0, 18, 18))


class SettingRow(QWidget):
    """A single settings row: label on the left, switch on the right."""

    def __init__(
        self,
        label: str,
        checked: bool,
        theme: MacTheme,
        last: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.theme = theme
        self.last = last
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        self.label = QLabel(label, self)
        self.label.setObjectName("SettingLabel")
        layout.addWidget(self.label)
        layout.addStretch()

        self.switch = MacSwitch(checked, theme, self)
        layout.addWidget(self.switch)

    def set_theme(self, theme: MacTheme) -> None:
        self.theme = theme
        self.switch.set_theme(theme)
        self.update()

    def paintEvent(self, event):
        if self.last:
            return
        painter = QPainter(self)
        painter.setPen(QPen(self.theme.separator, 1))
        painter.drawLine(14, self.height() - 1, self.width() - 14, self.height() - 1)


class SettingsCard(QWidget):
    """Rounded grouped settings container with separators between rows."""

    def __init__(self, rows, theme: MacTheme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.rows = rows

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for row in rows:
            layout.addWidget(row)
        self.setFixedHeight(44 * len(rows))

    def set_theme(self, theme: MacTheme) -> None:
        self.theme = theme
        for row in self.rows:
            row.set_theme(theme)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 12, 12)
        painter.fillPath(path, QBrush(self.theme.card_bg))
        painter.setPen(QPen(self.theme.card_border, 1))
        painter.drawPath(path)


class DeviceBadge(QWidget):
    """Rounded product tile showing the AirPods silhouette."""

    def __init__(self, theme: MacTheme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setFixedSize(46, 46)

    def set_theme(self, theme: MacTheme) -> None:
        self.theme = theme
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, 13, 13)
        painter.fillPath(path, QBrush(self.theme.card_bg))
        painter.setPen(QPen(self.theme.card_border, 1))
        painter.drawPath(path)

        glyph_color = with_alpha(self.theme.text_primary, 230)
        draw_earbud(painter, QRectF(11, 12, 10, 22), glyph_color)
        draw_earbud(painter, QRectF(25, 12, 10, 22), glyph_color)


# ---------------------------------------------------------------------------
# Popover base window
# ---------------------------------------------------------------------------

class MacPopover(QDialog):
    """Frameless translucent panel with a soft painted shadow."""

    def __init__(
        self,
        theme: MacTheme,
        panel_width: int,
        panel_height: int = 0,
        radius: int = 20,
        shadow: int = 18,
        no_activate: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.theme = theme
        self.radius = radius
        self.shadow = shadow

        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        if no_activate:
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setWindowTitle("AirWin")
        self.setStyleSheet(theme.qss())

        self.setFixedWidth(panel_width + shadow * 2)
        if panel_height > 0:
            self.setFixedHeight(panel_height + shadow * 2)

        self._fade_anim = None
        self._pos_anim = None
        self._closing = False

    # -- geometry -----------------------------------------------------------
    def panel_rect(self) -> QRectF:
        return QRectF(
            self.shadow,
            self.shadow,
            self.width() - self.shadow * 2,
            self.height() - self.shadow * 2,
        )

    def auto_size(self) -> None:
        layout = self.layout()
        if layout is None:
            return
        layout.activate()
        self.setFixedHeight(layout.sizeHint().height())

    # -- painting -----------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        panel = self.panel_rect()
        self._paint_shadow(painter, panel)

        gradient = QLinearGradient(panel.topLeft(), panel.bottomLeft())
        gradient.setColorAt(0.0, self.theme.panel_top)
        gradient.setColorAt(1.0, self.theme.panel_bottom)

        path = QPainterPath()
        path.addRoundedRect(panel, self.radius, self.radius)
        painter.fillPath(path, QBrush(gradient))

        painter.setPen(QPen(self.theme.panel_border, 1))
        painter.drawPath(path)

        painter.setPen(QPen(self.theme.panel_highlight, 1))
        painter.drawLine(
            QPointF(panel.left() + self.radius, panel.top() + 1.2),
            QPointF(panel.right() - self.radius, panel.top() + 1.2),
        )

    def _paint_shadow(self, painter: QPainter, panel: QRectF) -> None:
        painter.save()
        painter.setBrush(Qt.BrushStyle.NoBrush)
        layers = 16
        for index in range(layers, 0, -1):
            t = index / layers
            alpha = int(14 * (1.0 - t) ** 2)
            if alpha <= 0:
                continue
            painter.setPen(QPen(QColor(0, 0, 0, alpha), 1.4))
            spread = float(index)
            painter.drawRoundedRect(
                panel.adjusted(-spread, -spread + 3, spread, spread + 3),
                self.radius + spread * 0.5,
                self.radius + spread * 0.5,
            )
        painter.restore()

    # -- theming ------------------------------------------------------------
    def set_theme(self, theme: MacTheme) -> None:
        self.theme = theme
        self.setStyleSheet(theme.qss())
        self.apply_theme(theme)
        self.update()

    def apply_theme(self, theme: MacTheme) -> None:
        """Subclasses refresh their custom-painted children here."""

    # -- window events ------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        apply_window_appearance(self, self.theme.dark)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.dismiss()
        else:
            super().keyPressEvent(event)

    # -- animations ---------------------------------------------------------
    def fade_in(self, duration: int = 180) -> None:
        self._closing = False
        self.setWindowOpacity(0.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_anim.setDuration(duration)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.start()

    def slide_in(self, target, duration: int = 220) -> None:
        start = target + QPointF(0, 10).toPoint()
        self.move(start)
        self._pos_anim = QPropertyAnimation(self, b"pos", self)
        self._pos_anim.setDuration(duration)
        self._pos_anim.setStartValue(start)
        self._pos_anim.setEndValue(target)
        self._pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._pos_anim.start()

    def dismiss(self) -> None:
        self.hide()

    def fade_out(self, duration: int = 130, on_finished=None) -> None:
        if self._closing:
            return
        self._closing = True
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_anim.setDuration(duration)
        self._fade_anim.setStartValue(self.windowOpacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        if on_finished is not None:
            self._fade_anim.finished.connect(on_finished)
        self._fade_anim.start()
