"""QPlainTextEdit, который сам подстраивает высоту под содержимое."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPlainTextEdit


class ResizablePlainTextEdit(QPlainTextEdit):
    MIN_EDITOR_HEIGHT = 42
    HEIGHT_PADDING = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        self._base_height = self.MIN_EDITOR_HEIGHT
        self.setMinimumHeight(self._base_height)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.textChanged.connect(self.adjust_height_to_content)
        self.document().documentLayout().documentSizeChanged.connect(
            lambda *_: self.adjust_height_to_content()
        )

    def set_base_height(self, height: int):
        self._base_height = max(self.MIN_EDITOR_HEIGHT, height)
        self.setMinimumHeight(self._base_height)
        self.adjust_height_to_content()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_height_to_content()

    def adjust_height_to_content(self):
        document_width = max(1, self.viewport().width())
        if int(self.document().textWidth()) != document_width:
            self.document().setTextWidth(document_width)

        document_height = 0
        block = self.document().firstBlock()
        while block.isValid():
            document_height += max(
                self.blockBoundingRect(block).height(),
                self.fontMetrics().lineSpacing(),
            )
            block = block.next()

        frame_height = self.frameWidth() * 2
        target_height = max(self._base_height, int(document_height) + frame_height + self.HEIGHT_PADDING)
        if self.height() != target_height:
            self.setFixedHeight(target_height)
