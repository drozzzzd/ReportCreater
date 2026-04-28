"""Runtime application assets and Windows shell integration."""
from __future__ import annotations

import ctypes
import os
import sys

from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QWidget

from .paths import get_project_root


APP_USER_MODEL_ID = "Divan.ReportCreater"


def get_runtime_root() -> str:
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return frozen_root
    return get_project_root()


def get_image_path(filename: str) -> str:
    return os.path.join(get_runtime_root(), "image", filename)


def load_app_icon() -> QIcon:
    return QIcon(get_image_path("app_icon.ico"))


def set_windows_app_user_model_id() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        return


def apply_windows_dark_frame(widget: QWidget, dark: bool = True) -> None:
    if sys.platform != "win32":
        return

    try:
        hwnd = int(widget.winId())
        dwmapi = ctypes.windll.dwmapi
    except Exception:
        return

    def set_attribute(attribute: int, value: ctypes.c_int) -> None:
        try:
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                attribute,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
        except Exception:
            return

    dark_mode_enabled = ctypes.c_int(1 if dark else 0)
    set_attribute(20, dark_mode_enabled)
    set_attribute(19, dark_mode_enabled)

    # Windows 11+ visual polish. Older Windows versions ignore unsupported attrs.
    set_attribute(33, ctypes.c_int(2))
    if dark:
        set_attribute(34, ctypes.c_int(_colorref("#222733")))
        set_attribute(35, ctypes.c_int(_colorref("#20242D")))
        set_attribute(36, ctypes.c_int(_colorref("#F4F7FB")))
    else:
        set_attribute(34, ctypes.c_int(_colorref("#D7DCE6")))
        set_attribute(35, ctypes.c_int(_colorref("#F7F9FC")))
        set_attribute(36, ctypes.c_int(_colorref("#172033")))


def _colorref(hex_color: str) -> int:
    color = QColor(hex_color)
    return color.red() | (color.green() << 8) | (color.blue() << 16)
