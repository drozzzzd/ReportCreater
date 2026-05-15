"""Мелкие хелперы для UI-виджетов."""
from PyQt6.QtCore import QEasingCurve, QEvent, QObject, QPoint, QPropertyAnimation, Qt
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QLineEdit,
    QPlainTextEdit,
    QWidget,
)


def install_clearable_context_menu(widget: QWidget):
    """Добавляет в контекстное меню QLineEdit/QPlainTextEdit пункт 'Очистить поле'."""
    widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    widget.customContextMenuRequested.connect(lambda pos, w=widget: _show_context_menu(w, pos))


def set_invalid_state(widget: QWidget, invalid: bool):
    """Помечает виджет CSS-свойством invalid=true для подсветки в QSS."""
    widget.setProperty("invalid", invalid)
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


def apply_soft_shadow(
    widget: QWidget,
    *,
    blur_radius: float = 22,
    y_offset: float = 8,
    color: QColor | None = None,
) -> None:
    """Applies a restrained production-style shadow to framed surfaces."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur_radius)
    effect.setOffset(0, y_offset)
    effect.setColor(color or QColor(30, 42, 64, 28))
    widget.setGraphicsEffect(effect)


def install_press_feedback(widget: QWidget) -> None:
    """Adds a short opacity animation on press/release without touching callbacks."""
    if getattr(widget, "_press_feedback_filter", None) is not None:
        return
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(1.0)
    widget.setGraphicsEffect(effect)
    feedback_filter = _PressFeedbackFilter(widget, effect)
    widget.installEventFilter(feedback_filter)
    widget._press_feedback_filter = feedback_filter


def _show_context_menu(widget: QWidget, pos: QPoint):
    if not isinstance(widget, (QLineEdit, QPlainTextEdit)):
        return
    menu = widget.createStandardContextMenu()
    menu.addSeparator()
    clear_action = QAction("Очистить поле", widget)
    clear_action.triggered.connect(widget.clear)
    menu.addAction(clear_action)
    menu.exec(widget.mapToGlobal(pos))


class _PressFeedbackFilter(QObject):
    def __init__(self, widget: QWidget, effect: QGraphicsOpacityEffect):
        super().__init__(widget)
        self._effect = effect
        self._animation = QPropertyAnimation(effect, b"opacity", self)
        self._animation.setDuration(90)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def eventFilter(self, watched, event):
        event_type = event.type()
        if event_type == QEvent.Type.MouseButtonPress and watched.isEnabled():
            self._animate_to(0.88)
        elif event_type in (
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.Leave,
            QEvent.Type.EnabledChange,
        ):
            self._animate_to(1.0)
        return super().eventFilter(watched, event)

    def _animate_to(self, target: float) -> None:
        self._animation.stop()
        self._animation.setStartValue(self._effect.opacity())
        self._animation.setEndValue(target)
        self._animation.start()
