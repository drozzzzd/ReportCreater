"""
Вспомогательные утилиты для конструктора отчетов.
"""
import os

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QAction, QColor, QIcon, QPixmap
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QLineEdit, QPlainTextEdit, QWidget

BASE_MODE_ICON_COUNT = 6


def get_project_root() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(current_dir))


def load_mode_icons() -> list[QIcon]:
    project_root = get_project_root()
    sprite_candidates = [
        os.path.join(project_root, "modes.png"),
        os.path.join(project_root, "image", "modes.png"),
    ]
    laboratory_candidates = [
        os.path.join(project_root, "laboratories.png"),
        os.path.join(project_root, "image", "laboratories.png"),
    ]

    pixmap = QPixmap()
    for path in sprite_candidates:
        if os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                break

    icons: list[QIcon] = []
    if pixmap.isNull():
        icons.extend(QIcon() for _ in range(BASE_MODE_ICON_COUNT))
    else:
        icon_width = pixmap.width() // BASE_MODE_ICON_COUNT
        for index in range(BASE_MODE_ICON_COUNT):
            icons.append(QIcon(pixmap.copy(index * icon_width, 0, icon_width, pixmap.height())))

    laboratory_icon = QIcon()
    for path in laboratory_candidates:
        if os.path.exists(path):
            laboratory_icon = QIcon(path)
            if not laboratory_icon.isNull():
                break

    icons.append(laboratory_icon)
    return icons


def install_clearable_context_menu(widget: QWidget):
    widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    widget.customContextMenuRequested.connect(lambda pos, w=widget: _show_context_menu(w, pos))


def set_invalid_state(widget: QWidget, invalid: bool):
    widget.setProperty("invalid", invalid)
    style = widget.style()
    if style is not None:
        style.unpolish(widget)
        style.polish(widget)
    widget.update()


def apply_shadow(
    widget: QWidget,
    *,
    blur_radius: int = 28,
    x_offset: int = 0,
    y_offset: int = 8,
    color: str = "#0F172A",
    alpha: int = 28,
):
    effect = QGraphicsDropShadowEffect(widget)
    shadow_color = QColor(color)
    shadow_color.setAlpha(alpha)
    effect.setBlurRadius(blur_radius)
    effect.setOffset(x_offset, y_offset)
    effect.setColor(shadow_color)
    widget.setGraphicsEffect(effect)


def _show_context_menu(widget: QWidget, pos: QPoint):
    if isinstance(widget, QPlainTextEdit):
        menu = widget.createStandardContextMenu()
        menu.addSeparator()
        clear_action = QAction("Очистить поле", widget)
        clear_action.triggered.connect(widget.clear)
        menu.addAction(clear_action)
        menu.exec(widget.mapToGlobal(pos))
        return

    if isinstance(widget, QLineEdit):
        menu = widget.createStandardContextMenu()
        menu.addSeparator()
        clear_action = QAction("Очистить поле", widget)
        clear_action.triggered.connect(widget.clear)
        menu.addAction(clear_action)
        menu.exec(widget.mapToGlobal(pos))
