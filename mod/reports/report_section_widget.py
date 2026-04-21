"""
Виджет одного раздела в конструкторе отчетов.
"""
from collections.abc import Callable
import os

from PyQt6.QtCore import QPoint, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from .flow_layout import FlowLayout
from .report_menu_catalog import DropdownMenuManager
from .report_utils import apply_shadow, get_project_root, install_clearable_context_menu, set_invalid_state
from .text_report_builder import ReportSectionData


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


class ResizablePlainTextEdit(QPlainTextEdit):
    HANDLE_SIZE = 14
    MIN_EDITOR_HEIGHT = 72

    def __init__(self, parent=None):
        super().__init__(parent)
        self._resizing = False
        self._resize_origin = QPoint()
        self._start_height = 0
        self.setMouseTracking(True)
        self.setMinimumHeight(self.MIN_EDITOR_HEIGHT)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._is_in_resize_corner(event.position().toPoint()):
            self._resizing = True
            self._resize_origin = event.globalPosition().toPoint()
            self._start_height = self.height()
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._resizing:
            delta = event.globalPosition().toPoint() - self._resize_origin
            new_height = max(self.MIN_EDITOR_HEIGHT, self._start_height + delta.y())
            self.setFixedHeight(new_height)
            event.accept()
            return

        if self._is_in_resize_corner(event.position().toPoint()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._resizing and event.button() == Qt.MouseButton.LeftButton:
            self._resizing = False
            if not self._is_in_resize_corner(event.position().toPoint()):
                self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        if not self._resizing:
            self.unsetCursor()
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        pen = QPen(QColor("#94A3B8"))
        pen.setWidth(1)
        painter.setPen(pen)

        rect = self.viewport().rect()
        right = rect.right() - 4
        bottom = rect.bottom() - 4
        for offset in (0, 4, 8):
            painter.drawLine(right - offset - 4, bottom, right, bottom - offset - 4)

    def _is_in_resize_corner(self, pos: QPoint) -> bool:
        rect = self.viewport().rect()
        return pos.x() >= rect.right() - self.HANDLE_SIZE and pos.y() >= rect.bottom() - self.HANDLE_SIZE


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
        self.menu_manager = DropdownMenuManager()
        self.section_number = section_number
        self.mode_buttons: list[QToolButton] = []
        self.helper_buttons: list[QPushButton] = []
        self._dense_mode: bool | None = None

        self.setObjectName("reportSectionCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self._build_ui()
        self.set_section_number(section_number)
        apply_shadow(self, blur_radius=18, y_offset=5, alpha=14)
        self.set_ui_density(True)

    def _build_ui(self):
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(12, 12, 12, 12)
        self.root_layout.setSpacing(8)

        self.header_layout = QHBoxLayout()
        self.number_label = QLabel()
        self.number_label.setObjectName("sectionNumber")
        self.header_layout.addWidget(self.number_label)

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

        self.pre_text = self._create_editor_group(self.root_layout, "Pre-Condition", with_modes=True)
        self.scenario_text = self._create_editor_group(self.root_layout, "Scenario", with_modes=True)
        self.issue_text = self._create_issue_group(self.root_layout)

        for widget in [self.title_input, self.pre_text, self.scenario_text, self.issue_text]:
            install_clearable_context_menu(widget)

        self.title_input.textChanged.connect(self.content_changed.emit)
        self.pre_text.textChanged.connect(self.content_changed.emit)
        self.scenario_text.textChanged.connect(self.content_changed.emit)
        self.issue_text.textChanged.connect(self.content_changed.emit)
        self.issue_type_combo.currentTextChanged.connect(self.content_changed.emit)

    def _create_editor_group(self, parent_layout: QVBoxLayout, title: str, with_modes: bool) -> QPlainTextEdit:
        group = QGroupBox(title)
        group.setObjectName("sectionEditorGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        editor = ResizablePlainTextEdit()
        editor.setPlaceholderText(f"Заполните блок {title}")
        editor.setFixedHeight(84)

        if with_modes:
            layout.addLayout(self._create_modes_row(editor))

        helper_row = FlowLayout(spacing=6)
        rus_button = self._create_small_button("Rus", lambda: None)
        dash_button = self._create_small_button("Прочерк", lambda: None)
        attachment_button = self._create_small_button("Вложение", lambda: None)
        remove_attachment_button = self._create_small_button("-вложение", lambda: None)
        helper_row.addWidget(rus_button)
        helper_row.addWidget(dash_button)
        helper_row.addWidget(attachment_button)
        helper_row.addWidget(remove_attachment_button)
        self.helper_buttons.extend([rus_button, dash_button, attachment_button, remove_attachment_button])

        rus_button.clicked.connect(lambda: self._insert_text(editor, "' '"))
        dash_button.clicked.connect(lambda: self._insert_text(editor, " - "))
        attachment_button.clicked.connect(lambda: self._insert_attachment(editor))
        remove_attachment_button.clicked.connect(lambda: self._remove_last_attachment(editor))

        layout.addLayout(helper_row)
        layout.addWidget(editor)
        parent_layout.addWidget(group)
        return editor

    def _create_issue_group(self, parent_layout: QVBoxLayout) -> QPlainTextEdit:
        group = QGroupBox("Ошибка / Вопрос / Текст")
        self.issue_group = group
        group.setObjectName("sectionIssueGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        actions_row = FlowLayout(spacing=6)
        rus_button = self._create_small_button("Rus", lambda: None)
        dash_button = self._create_small_button("Прочерк", lambda: None)
        attachment_button = self._create_small_button("Вложение", lambda: None)
        remove_attachment_button = self._create_small_button("-вложение", lambda: None)
        actions_row.addWidget(rus_button)
        actions_row.addWidget(dash_button)
        actions_row.addWidget(attachment_button)
        actions_row.addWidget(remove_attachment_button)
        self.helper_buttons.extend([rus_button, dash_button, attachment_button, remove_attachment_button])

        type_row = QHBoxLayout()
        type_row.setSpacing(8)
        type_row.addWidget(QLabel("Тип:"))
        self.issue_type_combo = IssueTypeSegmentedControl()
        self.issue_type_combo.setObjectName("issueTypeCombo")
        self.issue_type_combo.addItems(["Error", "Question", "Текст"])
        self.issue_type_combo.setFixedWidth(230)
        self.issue_type_combo.setMinimumHeight(30)
        type_row.addWidget(self.issue_type_combo)
        type_row.addStretch()

        self.attachment_hint_label = QLabel("Следующее вложение: attachment:")
        self.attachment_hint_label.setObjectName("attachmentHintLabel")
        self.attachment_hint_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        type_row.addWidget(self.attachment_hint_label)

        editor = ResizablePlainTextEdit()
        editor.setPlaceholderText("Опишите ошибку или сформулируйте вопрос")
        editor.setFixedHeight(78)

        rus_button.clicked.connect(lambda: self._insert_text(editor, "' '"))
        dash_button.clicked.connect(lambda: self._insert_text(editor, " - "))
        attachment_button.clicked.connect(lambda: self._insert_attachment(editor))
        remove_attachment_button.clicked.connect(lambda: self._remove_last_attachment(editor))

        layout.addLayout(actions_row)
        layout.addLayout(type_row)
        layout.addWidget(editor)
        parent_layout.addWidget(group)
        return editor

    def _create_modes_row(self, editor: QPlainTextEdit) -> FlowLayout:
        layout = FlowLayout(spacing=6)

        for index, mode_name in enumerate(self.menu_manager.get_mode_names()):
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

            mode_menu = self._build_mode_menu(index, editor)
            if mode_menu is not None:
                button.setMenu(mode_menu)
                button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

            layout.addWidget(button)
            self.mode_buttons.append(button)
            button.clicked.connect(
                lambda _, idx=index, target=editor: self._insert_line(
                    target,
                    self.menu_manager.format_mode_button_entry(idx),
                )
            )

        self._add_tax_reference_button(layout, editor)
        return layout

    def _add_tax_reference_button(self, layout: FlowLayout, editor: QPlainTextEdit):
        button = QToolButton()
        button.setObjectName("modeButton")
        button.setToolTip(self.menu_manager.TAX_REFERENCE_BUTTON_NAME)
        button.setText(self.menu_manager.TAX_REFERENCE_BUTTON_NAME)
        button.setIcon(self._create_tax_reference_icon())
        button.setIconSize(QSize(20, 20))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setMenu(self._build_tax_reference_menu(editor))
        button.setFixedHeight(34)
        button.setMinimumWidth(142)

        layout.addWidget(button)
        self.mode_buttons.append(button)

    def _build_tax_reference_menu(self, editor: QPlainTextEdit) -> QMenu:
        menu = self._create_popup_menu(self)
        for label, path in self.menu_manager.get_tax_reference_entries():
            self._add_leaf_menu_row(
                menu,
                label,
                lambda value=path: self._insert_tax_reference_entry(editor, value),
            )
        return menu

    def _insert_tax_reference_entry(self, editor: QPlainTextEdit, path: str | tuple[str, ...]):
        self._insert_line(
            editor,
            self.menu_manager.format_tax_reference_entry(self.tax_reference_provider(), path),
        )

    @staticmethod
    def _create_tax_reference_icon() -> QIcon:
        icon_path = os.path.join(get_project_root(), "image", "FNS.png")
        return QIcon(icon_path)

    def set_ui_density(self, dense_mode: bool):
        if self._dense_mode == dense_mode and hasattr(self, "pre_text"):
            return

        self._dense_mode = dense_mode
        self.setProperty("denseMode", dense_mode)

        if dense_mode:
            self.root_layout.setContentsMargins(10, 10, 10, 10)
            self.root_layout.setSpacing(4)
            self.header_layout.setSpacing(8)
            self.title_input.setMinimumHeight(30)
            self.remove_btn.setMinimumHeight(30)
            self.issue_type_combo.setFixedWidth(228)
            self.pre_text.setFixedHeight(58)
            self.scenario_text.setFixedHeight(58)
            self.issue_text.setFixedHeight(174)
            for button in self.mode_buttons:
                button.setFixedHeight(28)
                button.setMinimumWidth(116)
            for button in self.helper_buttons:
                button.setMinimumHeight(22)
        else:
            self.root_layout.setContentsMargins(14, 14, 14, 14)
            self.root_layout.setSpacing(10)
            self.header_layout.setSpacing(10)
            self.title_input.setMinimumHeight(38)
            self.remove_btn.setMinimumHeight(36)
            self.issue_type_combo.setFixedWidth(250)
            self.pre_text.setFixedHeight(92)
            self.scenario_text.setFixedHeight(92)
            self.issue_text.setFixedHeight(240)
            for button in self.mode_buttons:
                button.setFixedHeight(38)
                button.setMinimumWidth(156)
            for button in self.helper_buttons:
                button.setMinimumHeight(32)

    def _build_mode_menu(self, index: int, editor: QPlainTextEdit) -> QMenu | None:
        if index == 0:
            return self._build_appointment_menu(editor)

        if index == 1:
            return self._build_patient_menu(editor)

        if index == 2:
            return self._build_practice_menu(editor)

        if index == 3:
            return self._build_marketing_menu(editor)

        if index == 4:
            return self._build_insurance_menu(editor)

        if index == 5:
            return self._build_settings_menu(editor)

        if index == 6:
            return self._build_laboratories_menu(editor)

        return None

    def _build_appointment_menu(self, editor: QPlainTextEdit) -> QMenu:
        menu = self._create_popup_menu(self)
        for menu_name in self.menu_manager.get_appointment_menu_names():
            items = self.menu_manager.get_appointment_items(menu_name)
            self._add_split_menu_row(
                menu,
                menu_name,
                lambda name=menu_name: self._insert_line(
                    editor,
                    self.menu_manager.format_appointment_tab_entry(name),
                ),
                lambda parent_menu, name=menu_name, values=items: self._build_leaf_menu(
                    parent_menu,
                    values,
                    lambda value, current=name: self.menu_manager.format_appointment_entry(current, value),
                    editor,
                ),
            )
        return menu

    def _build_patient_menu(self, editor: QPlainTextEdit) -> QMenu:
        menu = self._create_popup_menu(self)
        for menu_name in self.menu_manager.get_patient_menu_names():
            if self.menu_manager.has_patient_tabs(menu_name):
                self._add_split_menu_row(
                    menu,
                    menu_name,
                    lambda name=menu_name: self._insert_line(
                        editor,
                        self.menu_manager.format_patient_section_entry(name),
                    ),
                    lambda parent_menu, name=menu_name: self._build_patient_tabs_menu(parent_menu, editor, name),
                )
                continue

            items = self.menu_manager.get_patient_items(menu_name)
            if items:
                self._add_split_menu_row(
                    menu,
                    menu_name,
                    lambda name=menu_name: self._insert_line(
                        editor,
                        self.menu_manager.format_patient_section_entry(name),
                    ),
                    lambda parent_menu, name=menu_name, values=items: self._build_leaf_menu(
                        parent_menu,
                        values,
                        lambda value, current=name: self.menu_manager.format_patient_item_entry(current, value),
                        editor,
                    ),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                menu_name,
                lambda name=menu_name: self._insert_line(
                    editor,
                    self.menu_manager.format_patient_section_entry(name),
                ),
            )

        return menu

    def _build_practice_menu(self, editor: QPlainTextEdit) -> QMenu:
        menu = self._create_popup_menu(self)
        for menu_name in self.menu_manager.get_practice_menu_names():
            direct_items = self.menu_manager.get_practice_items(menu_name)
            tabs = self.menu_manager.get_practice_tabs(menu_name)

            if direct_items or tabs:
                self._add_split_menu_row(
                    menu,
                    menu_name,
                    lambda name=menu_name: self._insert_line(
                        editor,
                        self.menu_manager.format_practice_section_entry(name),
                    ),
                    lambda parent_menu, name=menu_name, values=direct_items: self._build_practice_section_menu(
                        parent_menu,
                        editor,
                        name,
                        values,
                    ),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                menu_name,
                lambda name=menu_name: self._insert_line(
                    editor,
                    self.menu_manager.format_practice_section_entry(name),
                ),
            )

        return menu

    def _build_marketing_menu(self, editor: QPlainTextEdit) -> QMenu:
        menu = self._create_popup_menu(self)
        for menu_name in self.menu_manager.get_marketing_menu_names():
            if self.menu_manager.has_marketing_tabs(menu_name):
                self._add_split_menu_row(
                    menu,
                    menu_name,
                    lambda name=menu_name: self._insert_line(
                        editor,
                        self.menu_manager.format_marketing_section_entry(name),
                    ),
                    lambda parent_menu, name=menu_name: self._build_marketing_tabs_menu(parent_menu, editor, name),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                menu_name,
                lambda name=menu_name: self._insert_line(
                    editor,
                    self.menu_manager.format_marketing_section_entry(name),
                ),
            )

        return menu

    def _build_insurance_menu(self, editor: QPlainTextEdit) -> QMenu:
        menu = self._create_popup_menu(self)
        for menu_name in self.menu_manager.get_insurance_menu_names():
            if self.menu_manager.has_insurance_tabs(menu_name):
                self._add_split_menu_row(
                    menu,
                    menu_name,
                    lambda name=menu_name: self._insert_line(
                        editor,
                        self.menu_manager.format_insurance_section_entry(name),
                    ),
                    lambda parent_menu, name=menu_name: self._build_insurance_tabs_menu(parent_menu, editor, name),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                menu_name,
                lambda name=menu_name: self._insert_line(
                    editor,
                    self.menu_manager.format_insurance_section_entry(name),
                ),
            )

        return menu

    def _build_settings_menu(self, editor: QPlainTextEdit) -> QMenu:
        menu = self._create_popup_menu(self)
        for menu_name in self.menu_manager.get_settings_menu_names():
            if self.menu_manager.has_settings_tabs(menu_name):
                self._add_split_menu_row(
                    menu,
                    menu_name,
                    lambda name=menu_name: self._insert_line(
                        editor,
                        self.menu_manager.format_settings_section_entry(name),
                    ),
                    lambda parent_menu, name=menu_name: self._build_settings_tabs_menu(parent_menu, editor, name),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                menu_name,
                lambda name=menu_name: self._insert_line(
                    editor,
                    self.menu_manager.format_settings_section_entry(name),
                ),
            )

        return menu

    def _build_laboratories_menu(self, editor: QPlainTextEdit) -> QMenu:
        menu = self._create_popup_menu(self)
        for menu_name in self.menu_manager.get_laboratories_menu_names():
            if self.menu_manager.has_laboratories_tabs(menu_name):
                self._add_split_menu_row(
                    menu,
                    menu_name,
                    lambda name=menu_name: self._insert_line(
                        editor,
                        self.menu_manager.format_laboratories_section_entry(name),
                    ),
                    lambda parent_menu, name=menu_name: self._build_laboratories_tabs_menu(parent_menu, editor, name),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                menu_name,
                lambda name=menu_name: self._insert_line(
                    editor,
                    self.menu_manager.format_laboratories_section_entry(name),
                ),
            )

        return menu

    def _build_patient_tabs_menu(self, parent_menu: QMenu, editor: QPlainTextEdit, menu_name: str) -> QMenu:
        menu = self._create_popup_menu(parent_menu)
        for tab_name in self.menu_manager.get_patient_tabs(menu_name):
            nested_items = self.menu_manager.get_patient_tab_items(menu_name, tab_name)
            if nested_items:
                self._add_split_menu_row(
                    menu,
                    tab_name,
                    lambda name=menu_name, tab=tab_name: self._insert_line(
                        editor,
                        self.menu_manager.format_patient_tab_entry(name, tab),
                    ),
                    lambda child_parent, name=menu_name, tab=tab_name, values=nested_items: self._build_leaf_menu(
                        child_parent,
                        values,
                        lambda value, current=name, current_tab=tab: self.menu_manager.format_patient_tab_item_entry(
                            current,
                            current_tab,
                            value,
                        ),
                        editor,
                    ),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                tab_name,
                lambda name=menu_name, tab=tab_name: self._insert_line(
                    editor,
                    self.menu_manager.format_patient_tab_entry(name, tab),
                ),
            )
        return menu

    def _build_practice_section_menu(
        self,
        parent_menu: QMenu,
        editor: QPlainTextEdit,
        menu_name: str,
        direct_items: list[str],
    ) -> QMenu:
        menu = self._create_popup_menu(parent_menu)
        for item in direct_items:
            self._add_leaf_menu_row(
                menu,
                item,
                lambda name=menu_name, value=item: self._insert_line(
                    editor,
                    self.menu_manager.format_practice_item_entry(name, value),
                ),
            )

        tabs = self.menu_manager.get_practice_tabs(menu_name)
        if direct_items and tabs:
            menu.addSeparator()

        for tab_name in tabs:
            nested_items = self.menu_manager.get_practice_tab_items(menu_name, tab_name)
            if nested_items:
                self._add_split_menu_row(
                    menu,
                    tab_name,
                    lambda name=menu_name, tab=tab_name: self._insert_line(
                        editor,
                        self.menu_manager.format_practice_tab_entry(name, tab),
                    ),
                    lambda child_parent, name=menu_name, tab=tab_name, values=nested_items: self._build_leaf_menu(
                        child_parent,
                        values,
                        lambda value, current=name, current_tab=tab: self.menu_manager.format_practice_tab_item_entry(
                            current,
                            current_tab,
                            value,
                        ),
                        editor,
                    ),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                tab_name,
                lambda name=menu_name, tab=tab_name: self._insert_line(
                    editor,
                    self.menu_manager.format_practice_tab_entry(name, tab),
                ),
            )
        return menu

    def _build_marketing_tabs_menu(self, parent_menu: QMenu, editor: QPlainTextEdit, menu_name: str) -> QMenu:
        menu = self._create_popup_menu(parent_menu)
        for tab_name in self.menu_manager.get_marketing_tabs(menu_name):
            nested_items = self.menu_manager.get_marketing_tab_items(menu_name, tab_name)
            if nested_items:
                self._add_split_menu_row(
                    menu,
                    tab_name,
                    lambda name=menu_name, tab=tab_name: self._insert_line(
                        editor,
                        self.menu_manager.format_marketing_tab_entry(name, tab),
                    ),
                    lambda child_parent, name=menu_name, tab=tab_name, values=nested_items: self._build_leaf_menu(
                        child_parent,
                        values,
                        lambda value, current=name, current_tab=tab: self.menu_manager.format_marketing_tab_item_entry(
                            current,
                            current_tab,
                            value,
                        ),
                        editor,
                    ),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                tab_name,
                lambda name=menu_name, tab=tab_name: self._insert_line(
                    editor,
                    self.menu_manager.format_marketing_tab_entry(name, tab),
                ),
            )
        return menu

    def _build_insurance_tabs_menu(self, parent_menu: QMenu, editor: QPlainTextEdit, menu_name: str) -> QMenu:
        menu = self._create_popup_menu(parent_menu)
        for tab_name in self.menu_manager.get_insurance_tabs(menu_name):
            nested_items = self.menu_manager.get_insurance_tab_items(menu_name, tab_name)
            if nested_items:
                self._add_split_menu_row(
                    menu,
                    tab_name,
                    lambda name=menu_name, tab=tab_name: self._insert_line(
                        editor,
                        self.menu_manager.format_insurance_tab_entry(name, tab),
                    ),
                    lambda child_parent, name=menu_name, tab=tab_name, values=nested_items: self._build_leaf_menu(
                        child_parent,
                        values,
                        lambda value, current=name, current_tab=tab: self.menu_manager.format_insurance_tab_item_entry(
                            current,
                            current_tab,
                            value,
                        ),
                        editor,
                    ),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                tab_name,
                lambda name=menu_name, tab=tab_name: self._insert_line(
                    editor,
                    self.menu_manager.format_insurance_tab_entry(name, tab),
                ),
            )
        return menu

    def _build_settings_tabs_menu(self, parent_menu: QMenu, editor: QPlainTextEdit, menu_name: str) -> QMenu:
        menu = self._create_popup_menu(parent_menu)
        for tab_name in self.menu_manager.get_settings_tabs(menu_name):
            nested_items = self.menu_manager.get_settings_tab_items(menu_name, tab_name)
            if nested_items:
                self._add_split_menu_row(
                    menu,
                    tab_name,
                    lambda name=menu_name, tab=tab_name: self._insert_line(
                        editor,
                        self.menu_manager.format_settings_tab_entry(name, tab),
                    ),
                    lambda child_parent, name=menu_name, tab=tab_name, values=nested_items: self._build_leaf_menu(
                        child_parent,
                        values,
                        lambda value, current=name, current_tab=tab: self.menu_manager.format_settings_tab_item_entry(
                            current,
                            current_tab,
                            value,
                        ),
                        editor,
                    ),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                tab_name,
                lambda name=menu_name, tab=tab_name: self._insert_line(
                    editor,
                    self.menu_manager.format_settings_tab_entry(name, tab),
                ),
            )
        return menu

    def _build_laboratories_tabs_menu(self, parent_menu: QMenu, editor: QPlainTextEdit, menu_name: str) -> QMenu:
        menu = self._create_popup_menu(parent_menu)
        for tab_name in self.menu_manager.get_laboratories_tabs(menu_name):
            nested_items = self.menu_manager.get_laboratories_tab_items(menu_name, tab_name)
            if nested_items:
                self._add_split_menu_row(
                    menu,
                    tab_name,
                    lambda name=menu_name, tab=tab_name: self._insert_line(
                        editor,
                        self.menu_manager.format_laboratories_tab_entry(name, tab),
                    ),
                    lambda child_parent, name=menu_name, tab=tab_name, values=nested_items: self._build_leaf_menu(
                        child_parent,
                        values,
                        lambda value, current=name, current_tab=tab: self.menu_manager.format_laboratories_tab_item_entry(
                            current,
                            current_tab,
                            value,
                        ),
                        editor,
                    ),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                tab_name,
                lambda name=menu_name, tab=tab_name: self._insert_line(
                    editor,
                    self.menu_manager.format_laboratories_tab_entry(name, tab),
                ),
            )
        return menu

    def _build_leaf_menu(
        self,
        parent_menu: QMenu,
        items: list[str],
        formatter,
        editor: QPlainTextEdit,
    ) -> QMenu:
        menu = self._create_popup_menu(parent_menu)
        for item in items:
            self._add_leaf_menu_row(
                menu,
                item,
                lambda value=item: self._insert_line(editor, formatter(value)),
            )
        return menu

    @staticmethod
    def _create_popup_menu(parent: QWidget) -> QMenu:
        menu = QMenu(parent)
        menu.setObjectName("splitDropdownMenu")
        menu.setSeparatorsCollapsible(False)
        return menu

    def _add_leaf_menu_row(self, menu: QMenu, label: str, callback):
        action = QWidgetAction(menu)
        button = QPushButton(label)
        button.setObjectName("menuItemButton")
        button.setFlat(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setMinimumWidth(220)
        button.setMinimumHeight(30)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.clicked.connect(lambda: self._trigger_menu_callback(menu, callback))
        action.setDefaultWidget(button)
        menu.addAction(action)

    def _add_split_menu_row(self, menu: QMenu, label: str, callback, submenu_builder):
        submenu = submenu_builder(menu)

        row = QWidget(menu)
        row.setObjectName("menuSplitRow")
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row.setMinimumWidth(220)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        main_button = QPushButton(label)
        main_button.setObjectName("menuSplitMainButton")
        main_button.setFlat(True)
        main_button.setCursor(Qt.CursorShape.PointingHandCursor)
        main_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        main_button.setMinimumHeight(30)
        main_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        main_button.clicked.connect(lambda: self._trigger_menu_callback(menu, callback))

        arrow_button = QToolButton()
        arrow_button.setObjectName("menuSplitArrowButton")
        arrow_button.setText(">")
        arrow_button.setAutoRaise(False)
        arrow_button.setCursor(Qt.CursorShape.PointingHandCursor)
        arrow_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        arrow_button.setFixedSize(28, 30)
        arrow_button.clicked.connect(lambda: self._popup_child_menu(submenu, arrow_button))

        layout.addWidget(main_button, 1)
        layout.addWidget(arrow_button)

        action = QWidgetAction(menu)
        action.setDefaultWidget(row)
        menu.addAction(action)

    def _trigger_menu_callback(self, menu: QMenu, callback):
        callback()
        self._close_menu_chain(menu)

    def _popup_child_menu(self, menu: QMenu, anchor: QWidget):
        anchor_row = anchor.parentWidget() or anchor
        menu.popup(anchor_row.mapToGlobal(QPoint(anchor_row.width(), 0)))

    @staticmethod
    def _close_menu_chain(menu: QMenu):
        current = menu
        while isinstance(current, QMenu):
            current.close()
            parent = current.parent()
            current = parent if isinstance(parent, QMenu) else None

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

    def set_section_number(self, number: int):
        self.section_number = number
        self.number_label.setText(f"#{number}")

    def set_attachment_hint(self, attachment_text: str):
        self.attachment_hint_label.setText(f"Следующее вложение: {attachment_text}")

    def get_section_data(self) -> ReportSectionData:
        return ReportSectionData(
            number=self.section_number,
            title=self.title_input.text().strip(),
            precondition=self.pre_text.toPlainText().strip(),
            scenario=self.scenario_text.toPlainText().strip(),
            issue_type=self.issue_type_combo.currentText(),
            issue_text=self.issue_text.toPlainText().strip(),
        )

    def set_validation_state(
        self,
        *,
        title_invalid: bool,
        precondition_invalid: bool,
        scenario_invalid: bool,
        issue_invalid: bool,
    ):
        set_invalid_state(self.title_input, title_invalid)
        set_invalid_state(self.pre_text, precondition_invalid)
        set_invalid_state(self.scenario_text, scenario_invalid)
        set_invalid_state(self.issue_text, issue_invalid)
