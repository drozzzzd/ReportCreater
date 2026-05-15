"""
Standalone launcher for the report builder application.
"""
from __future__ import annotations

import json
import os
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from mod.reports.reports_window import ReportsWindow
from mod.reports.ui.startup_splash import StartupVeilOverlay
from mod.reports.utils.app_assets import (
    apply_windows_dark_frame,
    get_image_path,
    load_app_icon,
    set_windows_app_user_model_id,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def load_config() -> dict:
    default_config = {
        "general": {
            "reports_dir": "reports",
        },
        "ui": {
            "theme": "light",
            "default_theme": "light",
        },
        "preferences": {
            "default_performer": "",
            "default_output_dir": "",
            "remember_defaults": False,
        },
    }

    if not os.path.exists(CONFIG_PATH):
        return default_config

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            loaded = json.load(file)
    except Exception:
        return default_config

    general = loaded.setdefault("general", {})
    general.setdefault("reports_dir", "reports")
    ui = loaded.setdefault("ui", {})
    ui.setdefault("theme", "light")
    ui.setdefault("default_theme", ui.get("theme", "light"))
    preferences = loaded.setdefault("preferences", {})
    preferences.setdefault("default_performer", "")
    preferences.setdefault("default_output_dir", "")
    preferences.setdefault("remember_defaults", False)
    return loaded


def main() -> int:
    set_windows_app_user_model_id()

    app = QApplication(sys.argv)
    app.setApplicationName("Report Builder")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))

    app_icon = load_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    window = ReportsWindow(load_config(), CONFIG_PATH)
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)

    tray_icon = create_tray_icon(window, app_icon)
    if tray_icon is not None:
        window._tray_icon = tray_icon
        window._close_to_tray = True
    window.setWindowTitle("Конструктор отчетов")
    window.show()
    apply_windows_dark_frame(window, getattr(window, "_current_theme", "light") == "dark")
    app.processEvents()
    startup_overlay = StartupVeilOverlay(window, get_image_path("splash.png"))
    startup_overlay.show_over_parent()
    window._startup_splash = startup_overlay
    app.processEvents()
    QTimer.singleShot(650, startup_overlay.fade_out)
    return app.exec()


def create_tray_icon(window: ReportsWindow, icon) -> QSystemTrayIcon | None:
    if icon.isNull() or not QSystemTrayIcon.isSystemTrayAvailable():
        return None

    tray_icon = QSystemTrayIcon(icon, window)
    tray_icon.setToolTip("Конструктор отчетов")

    tray_menu = QMenu(window)
    open_action = tray_menu.addAction("Открыть")
    open_action.triggered.connect(lambda: restore_window(window))
    tray_menu.addSeparator()
    quit_action = tray_menu.addAction("Выход")
    quit_action.triggered.connect(lambda: quit_from_tray(window))

    tray_icon.setContextMenu(tray_menu)
    tray_icon.activated.connect(
        lambda reason: restore_window(window)
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick)
        else None
    )
    tray_icon.show()
    return tray_icon


def restore_window(window: ReportsWindow) -> None:
    window.show()
    if window.windowState() & Qt.WindowState.WindowMinimized:
        window.setWindowState(window.windowState() & ~Qt.WindowState.WindowMinimized)
    window.raise_()
    window.activateWindow()


def quit_from_tray(window: ReportsWindow) -> None:
    window._force_quit = True
    window.save_session_cache()
    app = QApplication.instance()
    if app is not None:
        app.quit()


if __name__ == "__main__":
    sys.exit(main())
