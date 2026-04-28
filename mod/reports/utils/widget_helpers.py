"""Мелкие хелперы для UI-виджетов."""
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QLineEdit, QPlainTextEdit, QWidget


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


def _show_context_menu(widget: QWidget, pos: QPoint):
    if not isinstance(widget, (QLineEdit, QPlainTextEdit)):
        return
    menu = widget.createStandardContextMenu()
    menu.addSeparator()
    clear_action = QAction("Очистить поле", widget)
    clear_action.triggered.connect(widget.clear)
    menu.addAction(clear_action)
    menu.exec(widget.mapToGlobal(pos))
