"""Загрузка иконок для mode-кнопок и Tax Reference."""
import os

from PyQt6.QtGui import QIcon, QPixmap

from .paths import get_project_root

BASE_MODE_ICON_COUNT = 6


def load_mode_icons() -> list[QIcon]:
    """Возвращает 7 иконок: 6 нарезанных из modes.png + отдельная laboratories.png."""
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


def load_tax_reference_icon() -> QIcon:
    icon_path = os.path.join(get_project_root(), "image", "FNS.png")
    return QIcon(icon_path)
