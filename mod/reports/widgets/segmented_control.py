"""Сегментный переключатель (chip-row) — замена QComboBox для коротких списков."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget


class IssueTypeSegmentedControl(QWidget):
    currentTextChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        self._values: list[str] = []
        self._current_text = ""

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

    def addItems(self, values: list[str]):
        for value in values:
            self._add_item(value)
        if values:
            self.setCurrentText(values[0])

    def findText(self, value: str) -> int:
        try:
            return self._values.index(value)
        except ValueError:
            return -1

    def currentText(self) -> str:
        return self._current_text

    def setCurrentText(self, value: str):
        if value not in self._buttons:
            return

        previous = self._current_text
        self._current_text = value
        self._buttons[value].setChecked(True)
        self._refresh_button_state()
        if previous != value:
            self.currentTextChanged.emit(value)

    def _add_item(self, value: str):
        button = QPushButton(value)
        button.setObjectName("issueTypeSegmentButton")
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(28)
        button.clicked.connect(lambda _, current=value: self.setCurrentText(current))

        self._values.append(value)
        self._buttons[value] = button
        self._group.addButton(button)
        self.layout().addWidget(button)

    def _refresh_button_state(self):
        last_index = len(self._values) - 1
        for index, value in enumerate(self._values):
            button = self._buttons[value]
            if len(self._values) == 1:
                position = "single"
            elif index == 0:
                position = "first"
            elif index == last_index:
                position = "last"
            else:
                position = "middle"
            button.setProperty("segmentPosition", position)
            button.style().unpolish(button)
            button.style().polish(button)
