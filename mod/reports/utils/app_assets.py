"""Runtime application assets and Windows shell integration."""
from __future__ import annotations

import ctypes
import os
import sys

from PyQt6.QtCore import QEvent, QObject, QTimer
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QWidget

from .paths import get_project_root


APP_USER_MODEL_ID = "Divan.ReportCreater"
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_USE_IMMERSIVE_DARK_MODE_LEGACY = 19
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_BORDER_COLOR = 34
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36
DWMWCP_ROUND = 2
WINDOW_CORNER_RADIUS = 18


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
        user32 = ctypes.windll.user32
    except Exception:
        return

    def set_attribute(attribute: int, value: ctypes.c_int) -> bool:
        try:
            result = dwmapi.DwmSetWindowAttribute(
                hwnd,
                attribute,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
            return result == 0
        except Exception:
            return False

    dark_mode_enabled = ctypes.c_int(1 if dark else 0)
    set_attribute(DWMWA_USE_IMMERSIVE_DARK_MODE, dark_mode_enabled)
    set_attribute(DWMWA_USE_IMMERSIVE_DARK_MODE_LEGACY, dark_mode_enabled)

    # Windows 11+ visual polish. Older Windows versions ignore unsupported attrs.
    has_native_rounding = set_attribute(DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.c_int(DWMWCP_ROUND))
    if not has_native_rounding:
        _install_rounded_window_fallback(widget, hwnd, user32)

    if dark:
        set_attribute(DWMWA_BORDER_COLOR, ctypes.c_int(_colorref("#222733")))
        set_attribute(DWMWA_CAPTION_COLOR, ctypes.c_int(_colorref("#20242D")))
        set_attribute(DWMWA_TEXT_COLOR, ctypes.c_int(_colorref("#F4F7FB")))
    else:
        set_attribute(DWMWA_BORDER_COLOR, ctypes.c_int(_colorref("#D7DCE6")))
        set_attribute(DWMWA_CAPTION_COLOR, ctypes.c_int(_colorref("#F7F9FC")))
        set_attribute(DWMWA_TEXT_COLOR, ctypes.c_int(_colorref("#172033")))

    # Force Windows to repaint the non-client area after theme changes.
    try:
        swp_flags = 0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, swp_flags)
    except Exception:
        return


def _install_rounded_window_fallback(widget: QWidget, hwnd: int, user32) -> None:
    setattr(widget, "_windows_rounded_frame_hwnd", hwnd)
    _apply_rounded_window_region(widget, hwnd, user32)
    if getattr(widget, "_windows_rounded_frame_filter", None) is None:
        frame_filter = _RoundedWindowFrameFilter(widget)
        widget.installEventFilter(frame_filter)
        setattr(widget, "_windows_rounded_frame_filter", frame_filter)


class _RoundedWindowFrameFilter(QObject):
    def eventFilter(self, watched, event):
        if event.type() in {
            QEvent.Type.Resize,
            QEvent.Type.Show,
            QEvent.Type.WindowStateChange,
            QEvent.Type.WinIdChange,
        }:
            QTimer.singleShot(0, lambda target=watched: _refresh_rounded_window_region(target))
        return False


def _refresh_rounded_window_region(widget: QWidget) -> None:
    if sys.platform != "win32":
        return
    try:
        hwnd = int(getattr(widget, "_windows_rounded_frame_hwnd", 0) or widget.winId())
        user32 = ctypes.windll.user32
    except Exception:
        return
    _apply_rounded_window_region(widget, hwnd, user32)


def _apply_rounded_window_region(widget: QWidget, hwnd: int, user32) -> None:
    try:
        if widget.isMaximized() or widget.isFullScreen():
            user32.SetWindowRgn(hwnd, 0, True)
            return

        width, height = _window_rect_size(hwnd, user32)
        if width <= 0 or height <= 0:
            return

        gdi32 = ctypes.windll.gdi32
        region = gdi32.CreateRoundRectRgn(
            0,
            0,
            width + 1,
            height + 1,
            WINDOW_CORNER_RADIUS,
            WINDOW_CORNER_RADIUS,
        )
        if not region:
            return
        if not user32.SetWindowRgn(hwnd, region, True):
            gdi32.DeleteObject(region)
    except Exception:
        return


def _window_rect_size(hwnd: int, user32) -> tuple[int, int]:
    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return 0, 0
    return rect.right - rect.left, rect.bottom - rect.top


def _colorref(hex_color: str) -> int:
    color = QColor(hex_color)
    return color.red() | (color.green() << 8) | (color.blue() << 16)
