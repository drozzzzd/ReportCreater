"""Поиск корня проекта."""
import os
import sys


def get_project_root() -> str:
    """Возвращает абсолютный путь к корню проекта (где лежит main.py)."""
    current_file = os.path.abspath(__file__)
    # mod/reports/utils/paths.py -> mod/reports/utils -> mod/reports -> mod -> project_root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))


def get_writable_app_root() -> str:
    """Writable app data root for runtime files in packaged builds."""
    if getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(local_app_data, "ReportCreater")
    return get_project_root()
