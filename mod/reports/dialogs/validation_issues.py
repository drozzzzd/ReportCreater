"""Диалог со списком незаполненных полей перед сохранением."""
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)


class ValidationIssuesDialog(QDialog):
    def __init__(self, issues: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Не все поля заполнены")
        self.setModal(True)
        self.resize(540, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Перед сохранением найдены незаполненные или некорректные поля:")
        title.setWordWrap(True)
        layout.addWidget(title)

        issues_box = QPlainTextEdit()
        issues_box.setReadOnly(True)
        issues_box.setPlainText("\n".join(f"- {issue}" for issue in issues))
        layout.addWidget(issues_box, 1)

        hint = QLabel("Можно вернуться к редактированию или сохранить отчет в текущем виде.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QHBoxLayout()
        buttons.addStretch()

        continue_btn = QPushButton("Продолжить редактирование")
        continue_btn.clicked.connect(self.reject)
        buttons.addWidget(continue_btn)

        save_anyway_btn = QPushButton("Все равно сохранить")
        save_anyway_btn.setObjectName("saveBtn")
        save_anyway_btn.clicked.connect(self.accept)
        buttons.addWidget(save_anyway_btn)

        layout.addLayout(buttons)
