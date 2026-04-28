"""ScrollArea с анимированной прокруткой колесом."""
from PyQt6.QtCore import QAbstractAnimation, QEasingCurve, QPropertyAnimation
from PyQt6.QtWidgets import QScrollArea


class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scroll_target = 0
        self._scroll_animation = QPropertyAnimation(self.verticalScrollBar(), b"value", self)
        self._scroll_animation.setDuration(180)
        self._scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.verticalScrollBar().setSingleStep(24)

    def wheelEvent(self, event):
        pixel_delta = event.pixelDelta().y()
        angle_delta = event.angleDelta().y()
        if pixel_delta == 0 and angle_delta == 0:
            super().wheelEvent(event)
            return

        bar = self.verticalScrollBar()
        if self._scroll_animation.state() == QAbstractAnimation.State.Running:
            base_target = self._scroll_target
        else:
            base_target = bar.value()

        if pixel_delta:
            distance = -pixel_delta
        else:
            distance = int(-(angle_delta / 120) * 72)

        self._scroll_target = max(bar.minimum(), min(bar.maximum(), base_target + distance))
        self._scroll_animation.stop()
        self._scroll_animation.setStartValue(bar.value())
        self._scroll_animation.setEndValue(self._scroll_target)
        self._scroll_animation.start()
        event.accept()
