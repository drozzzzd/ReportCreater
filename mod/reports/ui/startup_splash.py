"""Full-window startup veil with a soft fade-out."""
from __future__ import annotations

from PyQt6.QtCore import QEvent, QEasingCurve, QPropertyAnimation, QSize, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget


class StartupVeilOverlay(QWidget):
    def __init__(self, parent: QWidget, image_path: str):
        super().__init__(parent)
        self.setObjectName("startupVeilOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        self._pixmap = QPixmap(image_path)
        if self._pixmap.isNull():
            self._pixmap = _fallback_pixmap()
        self._blurred_background = QPixmap()

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)
        self._fade_animation: QPropertyAnimation | None = None

        parent.installEventFilter(self)
        self.cover_parent()

    def cover_parent(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        self.setGeometry(parent.rect())

    def show_over_parent(self) -> None:
        self.cover_parent()
        self._capture_blurred_background()
        self.show()
        self.raise_()
        self.update()

    def fade_out(self, duration_ms: int = 2200) -> None:
        if not self.isVisible():
            return

        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_animation.setDuration(duration_ms)
        self._fade_animation.setStartValue(self._opacity_effect.opacity())
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_animation.finished.connect(self._finish_fade)
        self._fade_animation.start()

    def eventFilter(self, watched, event):
        if watched is self.parentWidget() and event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            self.cover_parent()
            self.raise_()
        return super().eventFilter(watched, event)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._blurred_background.isNull():
            painter.drawPixmap(self.rect(), self._blurred_background)

        overlay = QLinearGradient(0, 0, 0, max(self.height(), 1))
        overlay.setColorAt(0.0, QColor(248, 250, 255, 188))
        overlay.setColorAt(0.45, QColor(243, 247, 253, 168))
        overlay.setColorAt(1.0, QColor(236, 242, 251, 184))
        painter.fillRect(self.rect(), overlay)

        painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
        painter.drawRoundedRect(self.rect().adjusted(8, 8, -8, -8), 18, 18)

        max_width = max(320, int(self.width() * 0.72))
        max_height = max(260, int(self.height() * 0.58))
        splash = self._pixmap.scaled(
            max_width,
            max_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (self.width() - splash.width()) // 2
        y = (self.height() - splash.height()) // 2
        painter.drawPixmap(x, y, splash)

    def _finish_fade(self) -> None:
        self.hide()
        self.deleteLater()

    def _capture_blurred_background(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return

        was_visible = self.isVisible()
        if was_visible:
            self.hide()
        source = parent.grab()
        if was_visible:
            self.show()
        if source.isNull():
            self._blurred_background = QPixmap()
            return

        small_size = QSize(max(1, int(source.width() * 0.075)), max(1, int(source.height() * 0.075)))
        if small_size.width() < 1 or small_size.height() < 1:
            self._blurred_background = source
            return

        small = source.scaled(
            small_size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._blurred_background = small.scaled(
            source.size(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )


def _fallback_pixmap() -> QPixmap:
    pixmap = QPixmap(900, 520)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#364154"), 1))
    painter.setBrush(QColor(32, 36, 45, 228))
    painter.drawRoundedRect(74, 64, 752, 372, 40, 40)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#2F6FEA"))
    painter.drawRoundedRect(398, 156, 104, 132, 16, 16)
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(418, 182, 64, 8, 4, 4)
    painter.drawRoundedRect(418, 208, 64, 8, 4, 4)
    painter.drawRoundedRect(418, 234, 48, 8, 4, 4)
    painter.end()

    return pixmap
