"""
Standalone launcher for the report builder application.
"""
from __future__ import annotations

import json
import os
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from mod.reports.reports_window import ReportsWindow


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def load_config() -> dict:
    default_config = {
        "general": {
            "reports_dir": "reports",
        }
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
    return loaded


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Report Builder")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))

    window = ReportsWindow(load_config(), CONFIG_PATH)
    window.setWindowTitle("Конструктор отчетов")
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
