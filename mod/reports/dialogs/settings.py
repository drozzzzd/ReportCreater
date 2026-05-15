"""Application settings dialog."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from ..utils.app_assets import apply_windows_dark_frame


class SettingsDialog(QDialog):
    THEME_ITEMS = [
        ("Светлая", "light"),
        ("Темная", "dark"),
    ]

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsDialog")
        self.setWindowTitle("Настройки")
        self.setModal(True)
        self.resize(460, 260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        title = QLabel("Настройки")
        title.setObjectName("settingsDialogTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(10)
        layout.addLayout(form)

        self.theme_combo = QComboBox()
        for label, value in self.THEME_ITEMS:
            self.theme_combo.addItem(label, value)
        theme = str(settings.get("theme", "light"))
        index = self.theme_combo.findData(theme)
        self.theme_combo.setCurrentIndex(max(index, 0))
        form.addRow("Тема по умолчанию:", self.theme_combo)

        self.performer_input = QLineEdit(str(settings.get("default_performer", "")))
        self.performer_input.setPlaceholderText("Например QA")
        form.addRow("Исполнитель:", self.performer_input)

        self.output_dir_input = QLineEdit(str(settings.get("default_output_dir", "")))
        self.output_dir_input.setPlaceholderText("Папка для TXT-отчетов")
        browse_btn = QPushButton("...")
        browse_btn.setObjectName("browseBtn")
        browse_btn.setFixedWidth(36)
        browse_btn.clicked.connect(self._select_output_dir)
        path_row = QHBoxLayout()
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.setSpacing(6)
        path_row.addWidget(self.output_dir_input, 1)
        path_row.addWidget(browse_btn)
        form.addRow("Путь выгрузки:", path_row)

        self.remember_check = QCheckBox("Запомнить данные и скрыть заполненные поля в конструкторе")
        self.remember_check.setChecked(bool(settings.get("remember_defaults", False)))
        layout.addWidget(self.remember_check)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 4, 0, 0)
        buttons.addStretch(1)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setProperty("buttonType", "secondary")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self.accept)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    def values(self) -> dict:
        return {
            "theme": self.theme_combo.currentData(),
            "default_performer": self.performer_input.text().strip(),
            "default_output_dir": self.output_dir_input.text().strip(),
            "remember_defaults": self.remember_check.isChecked(),
        }

    def _select_output_dir(self) -> None:
        dialog = QFileDialog(self, "Выберите папку для сохранения отчетов")
        dialog.setStyleSheet(self.styleSheet())
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dark = getattr(self.parent(), "_current_theme", "light") == "dark"
        apply_windows_dark_frame(dialog, dark)
        QTimer.singleShot(0, lambda: apply_windows_dark_frame(dialog, dark))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.selectedFiles()
            if selected:
                self.output_dir_input.setText(selected[0])
