"""Поиск корня проекта."""
import os


def get_project_root() -> str:
    """Возвращает абсолютный путь к корню проекта (где лежит main.py)."""
    current_file = os.path.abspath(__file__)
    # mod/reports/utils/paths.py -> mod/reports/utils -> mod/reports -> mod -> project_root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
