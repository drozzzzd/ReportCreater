"""Виджет одного раздела в конструкторе отчетов."""
from collections.abc import Callable

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from ..core.menu_formatter import MenuFormatter
from ..core.report_data import ReportSectionData
from ..data.menu_catalog import MenuCatalog
from ..utils.icons import load_tax_reference_icon
from ..utils.widget_helpers import install_clearable_context_menu, set_invalid_state
from ..widgets.flow_layout import FlowLayout
from ..widgets.resizable_text_edit import ResizablePlainTextEdit
from ..widgets.segmented_control import IssueTypeSegmentedControl
from .menu_builder import MenuBuilder


class ReportSectionWidget(QFrame):
    remove_requested = pyqtSignal(object)
    content_changed = pyqtSignal()

    def __init__(
        self,
        section_number: int,
        attachment_provider: Callable[[], str],
        tax_reference_provider: Callable[[], str],
        mode_icons: list,
        parent=None,
    ):
        super().__init__(parent)
        self.attachment_provider = attachment_provider
        self.tax_reference_provider = tax_reference_provider
        self.mode_icons = mode_icons
        self._catalog = MenuCatalog()
        self._formatter = MenuFormatter(self._catalog)
        self._menu_builder = MenuBuilder(
            parent_widget=self,
            catalog=self._catalog,
            formatter=self._formatter,
            tax_reference_provider=tax_reference_provider,
        )

        # Совместимость со старым API (используется в тестах/внешнем коде)
        self.menu_manager = _DropdownMenuManagerCompat(self._catalog, self._formatter)

        self.section_number = section_number
        self.mode_buttons: list[QToolButton] = []
        self.helper_buttons: list[QPushButton] = []
        self._dense_mode: bool | None = None

        self.setObjectName("reportSectionCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self._build_ui()
        self.set_section_number(section_number)
        self.set_ui_density(True)

    # ---- Построение UI ----

    def _build_ui(self):
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(10, 10, 10, 10)
        self.root_layout.setSpacing(6)

        self.header_layout = QHBoxLayout()
        self.number_input = QLineEdit()
        self.number_input.setObjectName("sectionNumberInput")
        self.number_input.setValidator(QIntValidator(1, 999999, self))
        self.number_input.setPlaceholderText("№")
        self.number_input.setToolTip("Номер ошибки в итоговом отчете")
        self.number_input.setFixedWidth(56)
        self.number_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_layout.addWidget(self.number_input)

        self.title_input = QLineEdit()
        self.title_input.setObjectName("sectionTitleInput")
        self.title_input.setPlaceholderText("Ошибка в тексте")
        self.header_layout.addWidget(self.title_input, 1)

        self.remove_btn = QPushButton("Удалить")
        self.remove_btn.setProperty("buttonType", "secondary")
        self.remove_btn.setProperty("buttonRole", "danger")
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        self.header_layout.addWidget(self.remove_btn)
        self.root_layout.addLayout(self.header_layout)

        self.pre_text = self._create_editor_group("Pre-Condition", with_modes=True)
        self.scenario_text = self._create_editor_group("Scenario", with_modes=True)
        self.issue_text = self._create_issue_group()

        for widget in [self.number_input, self.title_input, self.pre_text, self.scenario_text, self.issue_text]:
            install_clearable_context_menu(widget)

        self.number_input.textChanged.connect(self.content_changed.emit)
        self.title_input.textChanged.connect(self.content_changed.emit)
        self.pre_text.textChanged.connect(self.content_changed.emit)
        self.scenario_text.textChanged.connect(self.content_changed.emit)
        self.issue_text.textChanged.connect(self.content_changed.emit)
        self.issue_type_combo.currentTextChanged.connect(self.content_changed.emit)

    def _create_editor_group(self, title: str, with_modes: bool) -> QPlainTextEdit:
        group = QGroupBox(title)
        group.setObjectName("sectionEditorGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        editor = ResizablePlainTextEdit()
        editor.setPlaceholderText(f"Заполните блок {title}")
        editor.set_base_height(84)

        if with_modes:
            layout.addLayout(self._create_modes_row(editor))

        layout.addLayout(self._create_helpers_row(editor))
        layout.addWidget(editor)
        self.root_layout.addWidget(group)
        return editor

    def _create_issue_group(self) -> QPlainTextEdit:
        group = QGroupBox("Ошибка / Вопрос / Текст")
        self.issue_group = group
        group.setObjectName("sectionIssueGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        editor = ResizablePlainTextEdit()
        editor.setPlaceholderText("Опишите ошибку или сформулируйте вопрос")
        editor.set_base_height(78)

        layout.addLayout(self._create_helpers_row(editor))

        type_row = QHBoxLayout()
        type_row.setSpacing(8)
        self.issue_type_combo = IssueTypeSegmentedControl()
        self.issue_type_combo.setObjectName("issueTypeCombo")
        self.issue_type_combo.addItems(["Error", "Question", "Текст"])
        self.issue_type_combo.setFixedWidth(258)
        self.issue_type_combo.setMinimumHeight(28)
        type_row.addWidget(self.issue_type_combo)
        type_row.addStretch()

        self.attachment_hint_label = QLabel("Следующее вложение: attachment:")
        self.attachment_hint_label.setObjectName("attachmentHintLabel")
        self.attachment_hint_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        type_row.addWidget(self.attachment_hint_label)

        layout.addLayout(type_row)
        layout.addWidget(editor)
        self.root_layout.addWidget(group)
        return editor

    def _create_helpers_row(self, editor: QPlainTextEdit) -> FlowLayout:
        row = FlowLayout(spacing=6)
        for label, action in [
            ("Rus", lambda: self._insert_text(editor, "' '")),
            ("Прочерк", lambda: self._insert_text(editor, " - ")),
            ("Вложение", lambda: self._insert_attachment(editor)),
            ("-вложение", lambda: self._remove_last_attachment(editor)),
        ]:
            button = self._create_small_button(label, action)
            row.addWidget(button)
            self.helper_buttons.append(button)
        return row

    def _create_modes_row(self, editor: QPlainTextEdit) -> FlowLayout:
        layout = FlowLayout(spacing=6)

        for index, mode_name in enumerate(self._catalog.get_mode_names()):
            button = QToolButton()
            button.setObjectName("modeButton")
            button.setToolTip(mode_name)
            button.setAutoRaise(False)
            button.setText(mode_name)
            button.setFixedHeight(34)
            button.setMinimumWidth(142)
            if index < len(self.mode_icons) and not self.mode_icons[index].isNull():
                button.setIcon(self.mode_icons[index])
                button.setIconSize(QSize(18, 18))
                button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            else:
                button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)

            mode_menu = self._menu_builder.build_mode_menu(index, editor)
            if mode_menu is not None:
                button.setMenu(mode_menu)
                button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

            layout.addWidget(button)
            self.mode_buttons.append(button)
            button.clicked.connect(
                lambda _, idx=index, target=editor: self._insert_line(
                    target, self._formatter.format_mode_button_entry(idx)
                )
            )

        self._add_tax_reference_button(layout, editor)
        return layout

    def _add_tax_reference_button(self, layout: FlowLayout, editor: QPlainTextEdit):
        button = QToolButton()
        button.setObjectName("modeButton")
        button.setToolTip(self._catalog.TAX_REFERENCE_BUTTON_NAME)
        button.setText(self._catalog.TAX_REFERENCE_BUTTON_NAME)
        button.setIcon(load_tax_reference_icon())
        button.setIconSize(QSize(20, 20))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setMenu(self._menu_builder.build_tax_reference_menu(editor))
        button.setFixedHeight(34)
        button.setMinimumWidth(142)

        layout.addWidget(button)
        self.mode_buttons.append(button)

    # ---- UI density ----

    def set_ui_density(self, dense_mode: bool):
        if self._dense_mode == dense_mode and hasattr(self, "pre_text"):
            return

        self._dense_mode = dense_mode
        self.setProperty("denseMode", dense_mode)

        if dense_mode:
            self.root_layout.setContentsMargins(8, 8, 8, 8)
            self.root_layout.setSpacing(5)
            self.header_layout.setSpacing(6)
            self.title_input.setMinimumHeight(30)
            self.remove_btn.setMinimumHeight(30)
            self.issue_type_combo.setFixedWidth(248)
            self.pre_text.set_base_height(58)
            self.scenario_text.set_base_height(58)
            self.issue_text.set_base_height(58)
            for button in self.mode_buttons:
                button.setFixedHeight(28)
                button.setMinimumWidth(116)
            for button in self.helper_buttons:
                button.setMinimumHeight(24)
        else:
            self.root_layout.setContentsMargins(12, 12, 12, 12)
            self.root_layout.setSpacing(8)
            self.header_layout.setSpacing(8)
            self.title_input.setMinimumHeight(34)
            self.remove_btn.setMinimumHeight(34)
            self.issue_type_combo.setFixedWidth(268)
            self.pre_text.set_base_height(70)
            self.scenario_text.set_base_height(70)
            self.issue_text.set_base_height(64)
            for button in self.mode_buttons:
                button.setFixedHeight(32)
                button.setMinimumWidth(128)
            for button in self.helper_buttons:
                button.setMinimumHeight(28)

    # ---- Helper-кнопки и attachment'ы ----

    @staticmethod
    def _create_small_button(text: str, callback) -> QPushButton:
        button = QPushButton(text)
        button.setProperty("small", "true")
        button.setMinimumHeight(28)
        button.clicked.connect(callback)
        return button

    @staticmethod
    def _insert_text(editor: QPlainTextEdit, text: str):
        editor.insertPlainText(text)
        editor.setFocus()

    @staticmethod
    def _insert_line(editor: QPlainTextEdit, text: str):
        cursor = editor.textCursor()
        content = editor.toPlainText()
        prefix = "\n" if content and not content.endswith("\n") else ""
        cursor.insertText(f"{prefix}{text}\n")
        editor.setTextCursor(cursor)
        editor.setFocus()

    def _insert_attachment(self, editor: QPlainTextEdit):
        self._insert_line(editor, self.attachment_provider())

    @staticmethod
    def _remove_last_attachment(editor: QPlainTextEdit):
        lines = editor.toPlainText().splitlines()
        for index in range(len(lines) - 1, -1, -1):
            if lines[index].strip().lower().startswith("attachment:"):
                del lines[index]
                editor.setPlainText("\n".join(lines))
                cursor = editor.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                editor.setTextCursor(cursor)
                editor.setFocus()
                return

    # ---- Публичный API секции ----

    def set_section_number(self, number: int | str, *, overwrite: bool = False):
        self.section_number = str(number)
        self.number_input.setPlaceholderText(f"№ {number}")
        if overwrite:
            self.number_input.setText(str(number))

    def set_attachment_hint(self, attachment_text: str):
        self.attachment_hint_label.setText(f"Следующее вложение: {attachment_text}")

    def get_section_data(self) -> ReportSectionData:
        return ReportSectionData(
            number=self.number_input.text().strip(),
            title=self.title_input.text().strip(),
            precondition=self.pre_text.toPlainText().strip(),
            scenario=self.scenario_text.toPlainText().strip(),
            issue_type=self.issue_type_combo.currentText(),
            issue_text=self.issue_text.toPlainText().strip(),
        )

    def set_validation_state(
        self,
        *,
        number_invalid: bool = False,
        title_invalid: bool,
        precondition_invalid: bool,
        scenario_invalid: bool,
        issue_invalid: bool,
    ):
        set_invalid_state(self.number_input, number_invalid)
        set_invalid_state(self.title_input, title_invalid)
        set_invalid_state(self.pre_text, precondition_invalid)
        set_invalid_state(self.scenario_text, scenario_invalid)
        set_invalid_state(self.issue_text, issue_invalid)

    # ---- Совместимость с тестами ----

    def _insert_tax_reference_entry(self, editor: QPlainTextEdit, path):
        self._menu_builder._insert_tax_reference_entry(editor, path)

    def _build_tax_reference_path_menu(self, parent_menu, editor: QPlainTextEdit, path):
        return self._menu_builder._build_tax_reference_path_menu(parent_menu, editor, path)

    @staticmethod
    def _create_popup_menu(parent):
        return MenuBuilder._create_popup_menu(parent)

    @staticmethod
    def _create_tax_reference_icon():
        return load_tax_reference_icon()


class _DropdownMenuManagerCompat:
    """Обёртка для совместимости — внешний код всё ещё ждёт self.menu_manager."""

    def __init__(self, catalog: MenuCatalog, formatter: MenuFormatter):
        self._catalog = catalog
        self._formatter = formatter

    def __getattr__(self, name: str):
        if name.startswith("format_"):
            return getattr(self._formatter, name)
        return getattr(self._catalog, name)
