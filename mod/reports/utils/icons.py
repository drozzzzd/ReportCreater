"""Загрузка иконок для mode-кнопок и Tax Reference."""
import os

from PyQt6.QtGui import QIcon

from .action_icons import make_mode_icon
from .paths import get_project_root

BASE_MODE_ICON_COUNT = 6


def load_mode_icons() -> list[QIcon]:
    """Return seven polished mode icons rendered from the app palette."""
    return [make_mode_icon(index) for index in range(BASE_MODE_ICON_COUNT + 1)]


def load_tax_reference_icon() -> QIcon:
    icon_path = os.path.join(get_project_root(), "image", "FNS.png")
    return QIcon(icon_path)
