"""Построитель Qt-меню для всех режимов (приём, пациенты, практика, ...).

Превращает данные MenuCatalog + форматтер MenuFormatter в QMenu-деревья,
вставляющие сформированные строки в указанный QPlainTextEdit.
"""
from collections.abc import Callable

from PyQt6.QtCore import QPoint, QSize, Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QWidget,
    QWidgetAction,
)

from ..core.menu_formatter import MenuFormatter
from ..data.menu_catalog import MenuCatalog
from ..utils.action_icons import make_action_icon


class MenuBuilder:
    """Собирает QMenu для одной из 7 mode-кнопок и для Tax Reference.

    parent_widget — владелец QMenu (QWidget, обычно секция).
    catalog/formatter — источник данных и логика форматирования.
    tax_reference_provider — лямбда, возвращающая текущее значение Tax Reference.
    """

    def __init__(
        self,
        parent_widget: QWidget,
        catalog: MenuCatalog,
        formatter: MenuFormatter,
        tax_reference_provider: Callable[[], str],
    ):
        self._parent = parent_widget
        self._catalog = catalog
        self._formatter = formatter
        self._tax_reference_provider = tax_reference_provider

    # ---- Публичный API: построение меню по индексу mode-кнопки ----

    def build_mode_menu(self, index: int, editor: QPlainTextEdit) -> QMenu | None:
        builders = [
            self._build_appointment_menu,
            self._build_patient_menu,
            self._build_practice_menu,
            self._build_marketing_menu,
            self._build_insurance_menu,
            self._build_settings_menu,
            self._build_laboratories_menu,
        ]
        if 0 <= index < len(builders):
            return builders[index](editor)
        return None

    def build_tax_reference_menu(self, editor: QPlainTextEdit) -> QMenu:
        menu = self._create_popup_menu(self._parent)
        for label, path in self._catalog.get_tax_reference_entries():
            self._add_split_menu_row(
                menu,
                label,
                lambda value=path[:1]: self._insert_tax_reference_entry(editor, value),
                lambda parent_menu, value=path: self._build_tax_reference_path_menu(
                    parent_menu, editor, value
                ),
            )
        return menu

    # ---- Билдеры по разделам ----

    def _build_appointment_menu(self, editor: QPlainTextEdit) -> QMenu:
        menu = self._create_popup_menu(self._parent)
        for menu_name in self._catalog.get_appointment_menu_names():
            items = self._catalog.get_appointment_items(menu_name)
            self._add_split_menu_row(
                menu,
                menu_name,
                lambda name=menu_name: self._insert_line(
                    editor, self._formatter.format_appointment_tab_entry(name)
                ),
                lambda parent_menu, name=menu_name, values=items: self._build_leaf_menu(
                    parent_menu,
                    values,
                    lambda value, current=name: self._formatter.format_appointment_entry(
                        current, value
                    ),
                    editor,
                ),
            )
        return menu

    def _build_patient_menu(self, editor: QPlainTextEdit) -> QMenu:
        menu = self._create_popup_menu(self._parent)
        for menu_name in self._catalog.get_patient_menu_names():
            if self._catalog.has_patient_tabs(menu_name):
                self._add_split_menu_row(
                    menu,
                    menu_name,
                    lambda name=menu_name: self._insert_line(
                        editor, self._formatter.format_patient_section_entry(name)
                    ),
                    lambda parent_menu, name=menu_name: self._build_patient_tabs_menu(
                        parent_menu, editor, name
                    ),
                )
                continue

            items = self._catalog.get_patient_items(menu_name)
            if items:
                self._add_split_menu_row(
                    menu,
                    menu_name,
                    lambda name=menu_name: self._insert_line(
                        editor, self._formatter.format_patient_section_entry(name)
                    ),
                    lambda parent_menu, name=menu_name, values=items: self._build_leaf_menu(
                        parent_menu,
                        values,
                        lambda value, current=name: self._formatter.format_patient_item_entry(
                            current, value
                        ),
                        editor,
                    ),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                menu_name,
                lambda name=menu_name: self._insert_line(
                    editor, self._formatter.format_patient_section_entry(name)
                ),
            )
        return menu

    def _build_practice_menu(self, editor: QPlainTextEdit) -> QMenu:
        menu = self._create_popup_menu(self._parent)
        for menu_name in self._catalog.get_practice_menu_names():
            direct_items = self._catalog.get_practice_items(menu_name)
            tabs = self._catalog.get_practice_tabs(menu_name)

            if direct_items or tabs:
                self._add_split_menu_row(
                    menu,
                    menu_name,
                    lambda name=menu_name: self._insert_line(
                        editor, self._formatter.format_practice_section_entry(name)
                    ),
                    lambda parent_menu, name=menu_name, values=direct_items: self._build_practice_section_menu(
                        parent_menu, editor, name, values
                    ),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                menu_name,
                lambda name=menu_name: self._insert_line(
                    editor, self._formatter.format_practice_section_entry(name)
                ),
            )
        return menu

    def _build_marketing_menu(self, editor: QPlainTextEdit) -> QMenu:
        return self._build_simple_tabbed_menu(
            editor,
            menu_names=self._catalog.get_marketing_menu_names(),
            has_tabs=self._catalog.has_marketing_tabs,
            section_formatter=self._formatter.format_marketing_section_entry,
            tabs_builder=self._build_marketing_tabs_menu,
        )

    def _build_insurance_menu(self, editor: QPlainTextEdit) -> QMenu:
        return self._build_simple_tabbed_menu(
            editor,
            menu_names=self._catalog.get_insurance_menu_names(),
            has_tabs=self._catalog.has_insurance_tabs,
            section_formatter=self._formatter.format_insurance_section_entry,
            tabs_builder=self._build_insurance_tabs_menu,
        )

    def _build_settings_menu(self, editor: QPlainTextEdit) -> QMenu:
        return self._build_simple_tabbed_menu(
            editor,
            menu_names=self._catalog.get_settings_menu_names(),
            has_tabs=self._catalog.has_settings_tabs,
            section_formatter=self._formatter.format_settings_section_entry,
            tabs_builder=self._build_settings_tabs_menu,
        )

    def _build_laboratories_menu(self, editor: QPlainTextEdit) -> QMenu:
        return self._build_simple_tabbed_menu(
            editor,
            menu_names=self._catalog.get_laboratories_menu_names(),
            has_tabs=self._catalog.has_laboratories_tabs,
            section_formatter=self._formatter.format_laboratories_section_entry,
            tabs_builder=self._build_laboratories_tabs_menu,
        )

    def _build_simple_tabbed_menu(
        self,
        editor: QPlainTextEdit,
        *,
        menu_names: list[str],
        has_tabs,
        section_formatter,
        tabs_builder,
    ) -> QMenu:
        """Общий шаблон marketing/insurance/settings/laboratories: либо вкладки, либо leaf."""
        menu = self._create_popup_menu(self._parent)
        for menu_name in menu_names:
            if has_tabs(menu_name):
                self._add_split_menu_row(
                    menu,
                    menu_name,
                    lambda name=menu_name: self._insert_line(editor, section_formatter(name)),
                    lambda parent_menu, name=menu_name: tabs_builder(parent_menu, editor, name),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                menu_name,
                lambda name=menu_name: self._insert_line(editor, section_formatter(name)),
            )
        return menu

    # ---- Построение вложенных вкладок ----

    def _build_patient_tabs_menu(
        self, parent_menu: QMenu, editor: QPlainTextEdit, menu_name: str
    ) -> QMenu:
        return self._build_tabs_menu(
            parent_menu,
            editor,
            tabs=self._catalog.get_patient_tabs(menu_name),
            get_items=lambda tab: self._catalog.get_patient_tab_items(menu_name, tab),
            tab_formatter=lambda tab: self._formatter.format_patient_tab_entry(menu_name, tab),
            item_formatter=lambda tab, item: self._formatter.format_patient_tab_item_entry(
                menu_name, tab, item
            ),
        )

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
                    editor, self._formatter.format_practice_item_entry(name, value)
                ),
            )

        tabs = self._catalog.get_practice_tabs(menu_name)
        if direct_items and tabs:
            menu.addSeparator()

        for tab_name in tabs:
            nested_items = self._catalog.get_practice_tab_items(menu_name, tab_name)
            if nested_items:
                self._add_split_menu_row(
                    menu,
                    tab_name,
                    lambda name=menu_name, tab=tab_name: self._insert_line(
                        editor, self._formatter.format_practice_tab_entry(name, tab)
                    ),
                    lambda child_parent, name=menu_name, tab=tab_name, values=nested_items: self._build_leaf_menu(
                        child_parent,
                        values,
                        lambda value, current=name, current_tab=tab: self._formatter.format_practice_tab_item_entry(
                            current, current_tab, value
                        ),
                        editor,
                    ),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                tab_name,
                lambda name=menu_name, tab=tab_name: self._insert_line(
                    editor, self._formatter.format_practice_tab_entry(name, tab)
                ),
            )
        return menu

    def _build_marketing_tabs_menu(
        self, parent_menu: QMenu, editor: QPlainTextEdit, menu_name: str
    ) -> QMenu:
        return self._build_tabs_menu(
            parent_menu,
            editor,
            tabs=self._catalog.get_marketing_tabs(menu_name),
            get_items=lambda tab: self._catalog.get_marketing_tab_items(menu_name, tab),
            tab_formatter=lambda tab: self._formatter.format_marketing_tab_entry(menu_name, tab),
            item_formatter=lambda tab, item: self._formatter.format_marketing_tab_item_entry(
                menu_name, tab, item
            ),
        )

    def _build_insurance_tabs_menu(
        self, parent_menu: QMenu, editor: QPlainTextEdit, menu_name: str
    ) -> QMenu:
        return self._build_tabs_menu(
            parent_menu,
            editor,
            tabs=self._catalog.get_insurance_tabs(menu_name),
            get_items=lambda tab: self._catalog.get_insurance_tab_items(menu_name, tab),
            tab_formatter=lambda tab: self._formatter.format_insurance_tab_entry(menu_name, tab),
            item_formatter=lambda tab, item: self._formatter.format_insurance_tab_item_entry(
                menu_name, tab, item
            ),
        )

    def _build_settings_tabs_menu(
        self, parent_menu: QMenu, editor: QPlainTextEdit, menu_name: str
    ) -> QMenu:
        return self._build_tabs_menu(
            parent_menu,
            editor,
            tabs=self._catalog.get_settings_tabs(menu_name),
            get_items=lambda tab: self._catalog.get_settings_tab_items(menu_name, tab),
            tab_formatter=lambda tab: self._formatter.format_settings_tab_entry(menu_name, tab),
            item_formatter=lambda tab, item: self._formatter.format_settings_tab_item_entry(
                menu_name, tab, item
            ),
        )

    def _build_laboratories_tabs_menu(
        self, parent_menu: QMenu, editor: QPlainTextEdit, menu_name: str
    ) -> QMenu:
        return self._build_tabs_menu(
            parent_menu,
            editor,
            tabs=self._catalog.get_laboratories_tabs(menu_name),
            get_items=lambda tab: self._catalog.get_laboratories_tab_items(menu_name, tab),
            tab_formatter=lambda tab: self._formatter.format_laboratories_tab_entry(menu_name, tab),
            item_formatter=lambda tab, item: self._formatter.format_laboratories_tab_item_entry(
                menu_name, tab, item
            ),
        )

    def _build_tabs_menu(
        self,
        parent_menu: QMenu,
        editor: QPlainTextEdit,
        *,
        tabs: list[str],
        get_items,
        tab_formatter,
        item_formatter,
    ) -> QMenu:
        """Общий шаблон вложенных вкладок: вкладка → leaf-меню с пунктами."""
        menu = self._create_popup_menu(parent_menu)
        for tab_name in tabs:
            nested_items = get_items(tab_name)
            if nested_items:
                self._add_split_menu_row(
                    menu,
                    tab_name,
                    lambda tab=tab_name: self._insert_line(editor, tab_formatter(tab)),
                    lambda child_parent, tab=tab_name, values=nested_items: self._build_leaf_menu(
                        child_parent,
                        values,
                        lambda value, current_tab=tab: item_formatter(current_tab, value),
                        editor,
                    ),
                )
                continue

            self._add_leaf_menu_row(
                menu,
                tab_name,
                lambda tab=tab_name: self._insert_line(editor, tab_formatter(tab)),
            )
        return menu

    def _build_tax_reference_path_menu(
        self, parent_menu: QMenu, editor: QPlainTextEdit, path: tuple[str, ...]
    ) -> QMenu:
        menu = self._create_popup_menu(parent_menu)
        self._add_leaf_menu_row(
            menu,
            "Просмотр",
            lambda value=path: self._insert_tax_reference_entry(editor, value),
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

    # ---- Низкоуровневые UI-хелперы ----

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
        arrow_button.setText("")
        arrow_button.setIcon(make_action_icon("chevron-right"))
        arrow_button.setIconSize(QSize(13, 13))
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

    @staticmethod
    def _popup_child_menu(menu: QMenu, anchor: QWidget):
        anchor_row = anchor.parentWidget() or anchor
        menu.popup(anchor_row.mapToGlobal(QPoint(anchor_row.width(), 0)))

    @staticmethod
    def _close_menu_chain(menu: QMenu):
        current = menu
        while isinstance(current, QMenu):
            current.close()
            parent = current.parent()
            current = parent if isinstance(parent, QMenu) else None

    def _insert_tax_reference_entry(self, editor: QPlainTextEdit, path):
        self._insert_line(
            editor,
            self._formatter.format_tax_reference_entry(self._tax_reference_provider(), path),
        )

    @staticmethod
    def _insert_line(editor: QPlainTextEdit, text: str):
        cursor = editor.textCursor()
        content = editor.toPlainText()
        prefix = "\n" if content and not content.endswith("\n") else ""
        cursor.insertText(f"{prefix}{text}\n")
        editor.setTextCursor(cursor)
        editor.setFocus()
