"""Small polished icon set rendered with Qt primitives."""
from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF


ICON_SIZES = (16, 20, 24, 32, 48, 64)


def make_action_icon(name: str, theme: str = "light") -> QIcon:
    """Return a crisp multi-size icon using the app's existing palette."""
    drawer = _ACTION_DRAWERS.get(name)
    if drawer is None:
        return QIcon()
    return _render_icon(lambda painter, colors: drawer(painter, colors), theme)


def make_mode_icon(index: int, theme: str = "light") -> QIcon:
    drawer = _MODE_DRAWERS[index] if 0 <= index < len(_MODE_DRAWERS) else None
    if drawer is None:
        return QIcon()
    return _render_icon(lambda painter, colors: _draw_mode_shell(painter, colors, drawer), theme)


def _render_icon(drawer: Callable[[QPainter, dict[str, QColor]], None], theme: str) -> QIcon:
    colors = _colors(theme)
    icon = QIcon()
    for size in ICON_SIZES:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(size / 24, size / 24)
        drawer(painter, colors)
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def _colors(theme: str) -> dict[str, QColor]:
    dark = theme == "dark"
    return {
        "ink": QColor("#F4F7FB" if dark else "#273044"),
        "muted": QColor("#B7C2D4" if dark else "#697386"),
        "line": QColor("#3A4558" if dark else "#DDE3EC"),
        "surface": QColor("#202633" if dark else "#FFFFFF"),
        "soft": QColor("#2C3546" if dark else "#F7F9FC"),
        "blue": QColor("#2F6FEA"),
        "blue_soft": QColor("#6EA2FF" if dark else "#D9E7FF"),
        "danger": QColor("#EF4444"),
        "white": QColor("#FFFFFF"),
    }


def _pen(color: QColor, width: float = 1.5) -> QPen:
    pen = QPen(color, width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _line(painter: QPainter, x1: float, y1: float, x2: float, y2: float) -> None:
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def _draw_document(painter: QPainter, colors: dict[str, QColor], rect: QRectF) -> None:
    painter.setPen(_pen(colors["line"], 1.1))
    painter.setBrush(colors["surface"])
    painter.drawRoundedRect(rect, 2.2, 2.2)
    fold = QPolygonF(
        [
            QPointF(rect.right() - 4.8, rect.top()),
            QPointF(rect.right(), rect.top() + 4.8),
            QPointF(rect.right() - 4.8, rect.top() + 4.8),
        ]
    )
    painter.setBrush(colors["blue_soft"])
    painter.drawPolygon(fold)
    painter.setPen(_pen(colors["muted"], 1.1))
    _line(painter, rect.left() + 4, rect.top() + 8, rect.right() - 4, rect.top() + 8)
    _line(painter, rect.left() + 4, rect.top() + 12, rect.right() - 5, rect.top() + 12)


def _draw_save(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["line"], 1.1))
    painter.setBrush(colors["surface"])
    painter.drawRoundedRect(QRectF(5, 3, 14, 18), 2.4, 2.4)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(colors["blue"])
    painter.drawRoundedRect(QRectF(7, 4.8, 8.8, 5.2), 1.2, 1.2)
    painter.setBrush(colors["soft"])
    painter.drawRoundedRect(QRectF(8, 13.2, 8, 5.4), 1.1, 1.1)
    painter.setPen(_pen(colors["muted"], 1.0))
    _line(painter, 9.5, 15.5, 14.5, 15.5)


def _draw_open(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["line"], 1.1))
    painter.setBrush(colors["surface"])
    painter.drawRoundedRect(QRectF(3.5, 8, 17, 10.5), 2.4, 2.4)
    painter.setBrush(colors["blue_soft"])
    painter.drawRoundedRect(QRectF(5, 5.5, 7.8, 4.8), 1.8, 1.8)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(colors["blue"])
    painter.drawRoundedRect(QRectF(4.8, 10.4, 14.4, 6.3), 1.8, 1.8)


def _draw_file_open(painter: QPainter, colors: dict[str, QColor]) -> None:
    _draw_document(painter, colors, QRectF(5.2, 3.2, 12.8, 17.2))
    painter.setPen(_pen(colors["blue"], 1.7))
    _line(painter, 8.2, 16.2, 14.7, 16.2)
    _line(painter, 12.3, 13.8, 14.7, 16.2)
    _line(painter, 12.3, 18.6, 14.7, 16.2)


def _draw_reset(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["blue"], 1.8))
    painter.drawArc(QRectF(5, 5, 14, 14), 40 * 16, 260 * 16)
    _line(painter, 6.5, 7.7, 6, 3.9)
    _line(painter, 6.5, 7.7, 10.1, 7.1)
    painter.setPen(_pen(colors["muted"], 1.5))
    _line(painter, 9, 12, 15, 12)
    _line(painter, 12, 9, 12, 15)


def _draw_add(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(colors["blue"])
    painter.drawEllipse(QRectF(5, 5, 14, 14))
    painter.setPen(_pen(colors["white"], 2.0))
    _line(painter, 12, 8.2, 12, 15.8)
    _line(painter, 8.2, 12, 15.8, 12)


def _draw_remove(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["danger"], 1.4))
    painter.setBrush(QColor(colors["danger"].red(), colors["danger"].green(), colors["danger"].blue(), 24))
    painter.drawEllipse(QRectF(5, 5, 14, 14))
    painter.setPen(_pen(colors["danger"], 2.0))
    _line(painter, 8.2, 12, 15.8, 12)


def _draw_trash(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["danger"], 1.35))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    _line(painter, 8, 7, 16, 7)
    _line(painter, 10, 5, 14, 5)
    painter.drawRoundedRect(QRectF(8.5, 8.8, 7, 10), 1.4, 1.4)
    _line(painter, 10.8, 11, 10.8, 16.8)
    _line(painter, 13.2, 11, 13.2, 16.8)


def _draw_settings(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["muted"], 1.6))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for angle in range(0, 360, 45):
        painter.save()
        painter.translate(12, 12)
        painter.rotate(angle)
        _line(painter, 0, -8.7, 0, -6.5)
        painter.restore()
    painter.setPen(_pen(colors["ink"], 1.8))
    painter.drawEllipse(QRectF(7.3, 7.3, 9.4, 9.4))
    painter.setPen(_pen(colors["blue"], 1.9))
    painter.drawEllipse(QRectF(10, 10, 4, 4))


def _draw_sun(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["blue"], 1.6))
    for angle in range(0, 360, 45):
        painter.save()
        painter.translate(12, 12)
        painter.rotate(angle)
        _line(painter, 0, -9.2, 0, -7.1)
        painter.restore()
    painter.setBrush(colors["blue_soft"])
    painter.drawEllipse(QRectF(7.4, 7.4, 9.2, 9.2))


def _draw_moon(painter: QPainter, colors: dict[str, QColor]) -> None:
    path = QPainterPath()
    path.moveTo(16.8, 18.4)
    path.cubicTo(10.2, 18.4, 5.6, 13.5, 6.7, 7.5)
    path.cubicTo(8.7, 10.2, 12.2, 12.6, 16.3, 12.6)
    path.cubicTo(18.0, 12.6, 19.4, 12.2, 20.4, 11.5)
    path.cubicTo(20.2, 14.4, 18.7, 16.9, 16.8, 18.4)
    painter.setPen(_pen(colors["blue"], 1.3))
    painter.setBrush(colors["blue_soft"])
    painter.drawPath(path)


def _draw_attachment(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["blue"], 1.7))
    painter.drawArc(QRectF(6, 4, 10, 15), 225 * 16, 280 * 16)
    painter.drawArc(QRectF(8.5, 6.5, 6.5, 10.5), 225 * 16, 280 * 16)
    painter.setPen(_pen(colors["muted"], 1.25))
    _line(painter, 15.2, 15.2, 18.2, 18.2)


def _draw_attachment_remove(painter: QPainter, colors: dict[str, QColor]) -> None:
    _draw_attachment(painter, colors)
    painter.setPen(_pen(colors["danger"], 1.8))
    _line(painter, 14.8, 18, 20.2, 18)


def _draw_quote(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(colors["blue"])
    painter.drawRoundedRect(QRectF(5.5, 6.5, 5.4, 8.8), 1.5, 1.5)
    painter.drawRoundedRect(QRectF(13.1, 6.5, 5.4, 8.8), 1.5, 1.5)
    painter.setBrush(colors["surface"])
    painter.drawRect(QRectF(8, 11.5, 3, 4))
    painter.drawRect(QRectF(15.6, 11.5, 3, 4))


def _draw_dash(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["blue"], 2.3))
    _line(painter, 6.5, 12, 17.5, 12)


def _draw_chevron_right(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["muted"], 1.8))
    _line(painter, 9.2, 6.8, 14.8, 12)
    _line(painter, 14.8, 12, 9.2, 17.2)


def _draw_window_minimize(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["ink"], 1.9))
    _line(painter, 7, 14, 17, 14)


def _draw_window_maximize(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["ink"], 1.65))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(QRectF(7.2, 7.2, 9.6, 9.6), 1.4, 1.4)


def _draw_window_restore(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["ink"], 1.45))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(QRectF(8.4, 9, 7.6, 7.6), 1.2, 1.2)
    painter.drawRoundedRect(QRectF(10.2, 7.2, 7.6, 7.6), 1.2, 1.2)


def _draw_window_close(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["danger"], 1.9))
    _line(painter, 8, 8, 16, 16)
    _line(painter, 16, 8, 8, 16)


def _draw_mode_shell(
    painter: QPainter,
    colors: dict[str, QColor],
    drawer: Callable[[QPainter, dict[str, QColor]], None],
) -> None:
    painter.setPen(_pen(colors["line"], 0.9))
    painter.setBrush(colors["surface"])
    painter.drawRoundedRect(QRectF(3, 3, 18, 18), 5, 5)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(colors["blue_soft"])
    painter.drawEllipse(QRectF(5.3, 5.3, 4.2, 4.2))
    drawer(painter, colors)


def _mode_calendar(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["ink"], 1.1))
    painter.drawRoundedRect(QRectF(6.5, 7.5, 11, 9.8), 1.6, 1.6)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(colors["blue"])
    painter.drawRoundedRect(QRectF(6.7, 7.6, 10.6, 3), 1.2, 1.2)
    painter.setPen(_pen(colors["muted"], 0.9))
    _line(painter, 8.8, 12.6, 15.2, 12.6)
    _line(painter, 8.8, 15, 13, 15)


def _mode_patient(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["ink"], 1.1))
    painter.setBrush(colors["blue_soft"])
    painter.drawEllipse(QRectF(7, 6.5, 10, 10))
    painter.setPen(_pen(colors["ink"], 1.0))
    painter.drawPoint(QPointF(10, 11))
    painter.drawPoint(QPointF(14, 11))
    painter.drawArc(QRectF(9, 10.8, 6, 4), 205 * 16, 130 * 16)


def _mode_practice(painter: QPainter, colors: dict[str, QColor]) -> None:
    _draw_document(painter, colors, QRectF(7, 5.5, 10.5, 13.5))
    painter.setPen(_pen(colors["blue"], 1.3))
    _line(painter, 9.4, 14, 11.3, 15.7)
    _line(painter, 11.3, 15.7, 15.2, 10.8)


def _mode_marketing(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["line"], 1.0))
    painter.setBrush(colors["soft"])
    painter.drawRoundedRect(QRectF(7, 9.5, 10.5, 7.5), 1.6, 1.6)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(colors["blue"])
    painter.drawRoundedRect(QRectF(8.8, 13.4, 2.1, 3.1), 0.8, 0.8)
    painter.drawRoundedRect(QRectF(11.6, 11.1, 2.1, 5.4), 0.8, 0.8)
    painter.drawRoundedRect(QRectF(14.4, 7.2, 2.1, 9.3), 0.8, 0.8)


def _mode_insurance(painter: QPainter, colors: dict[str, QColor]) -> None:
    shield = QPainterPath()
    shield.moveTo(12, 5.5)
    shield.lineTo(17.1, 7.6)
    shield.lineTo(16.3, 14.2)
    shield.cubicTo(15.5, 16.1, 13.9, 17.4, 12, 18.5)
    shield.cubicTo(10.1, 17.4, 8.5, 16.1, 7.7, 14.2)
    shield.lineTo(6.9, 7.6)
    shield.closeSubpath()
    painter.setPen(_pen(colors["blue"], 1.2))
    painter.setBrush(colors["blue_soft"])
    painter.drawPath(shield)
    painter.setPen(_pen(colors["ink"], 1.2))
    _line(painter, 9.6, 11.8, 11.3, 13.5)
    _line(painter, 11.3, 13.5, 14.9, 9.7)


def _mode_settings(painter: QPainter, colors: dict[str, QColor]) -> None:
    _draw_settings(painter, colors)


def _mode_lab(painter: QPainter, colors: dict[str, QColor]) -> None:
    painter.setPen(_pen(colors["ink"], 1.1))
    _line(painter, 10, 6.2, 14, 6.2)
    _line(painter, 11, 6.5, 11, 11.5)
    _line(painter, 13, 6.5, 13, 11.5)
    painter.setBrush(colors["blue_soft"])
    painter.drawRoundedRect(QRectF(8.2, 11, 7.6, 6.8), 2.8, 2.8)
    painter.setPen(_pen(colors["blue"], 1.0))
    _line(painter, 9.4, 14.1, 14.6, 14.1)


_ACTION_DRAWERS: dict[str, Callable[[QPainter, dict[str, QColor]], None]] = {
    "add": _draw_add,
    "attachment": _draw_attachment,
    "attachment-remove": _draw_attachment_remove,
    "chevron-right": _draw_chevron_right,
    "dash": _draw_dash,
    "file-open": _draw_file_open,
    "moon": _draw_moon,
    "open": _draw_open,
    "quote": _draw_quote,
    "remove": _draw_remove,
    "reset": _draw_reset,
    "save": _draw_save,
    "settings": _draw_settings,
    "sun": _draw_sun,
    "trash": _draw_trash,
    "window-close": _draw_window_close,
    "window-maximize": _draw_window_maximize,
    "window-minimize": _draw_window_minimize,
    "window-restore": _draw_window_restore,
}

_MODE_DRAWERS: tuple[Callable[[QPainter, dict[str, QColor]], None], ...] = (
    _mode_calendar,
    _mode_patient,
    _mode_practice,
    _mode_marketing,
    _mode_insurance,
    _mode_settings,
    _mode_lab,
)
