"""Форматирование строк-вставок меню в текст отчёта."""
from ..data.menu_catalog import MenuCatalog


class MenuFormatter:
    """Превращает (menu, tab, item) в строку формата 'режим' - 'X' - tabmenu 'Y' - 'Z'."""

    def __init__(self, catalog: MenuCatalog):
        self._catalog = catalog

    def format_mode_entry(self, index: int) -> str:
        return self.format_mode_menu_entry(self._catalog.MODE_MENU_ITEMS[index])

    def format_mode_button_entry(self, index: int) -> str:
        return f"'режим' - '{self._catalog.get_mode_name(index)}'"

    def format_mode_menu_entry(self, item: str) -> str:
        return f"'режим' - tabmenu '{self._catalog.MODE_MENU_NAME}' - '{item}'"

    @staticmethod
    def format_attachment(sir_value: str) -> str:
        return f"attachment:{sir_value}" if sir_value else "attachment:"

    def format_tax_reference_entry(
        self, tax_reference_value: str, path: str | tuple[str, ...]
    ) -> str:
        title = tax_reference_value.strip() or self._catalog.TAX_REFERENCE_SYSTEM_NAME
        path_parts = (path,) if isinstance(path, str) else path
        formatted_path = " - ".join(f"'{part}'" for part in path_parts)
        return f"'{title}' - tabmenu '{self._catalog.TAX_REFERENCE_MENU_NAME}' - {formatted_path}"

    def format_appointment_entry(self, menu_name: str, item: str) -> str:
        return (
            f"'режим' - '{self._catalog.APPOINTMENT_MODE_NAME}' - tabmenu '{menu_name}' - '{item}'"
        )

    def format_appointment_tab_entry(self, menu_name: str) -> str:
        return f"'режим' - '{self._catalog.APPOINTMENT_MODE_NAME}' - tabmenu '{menu_name}'"

    def format_patient_section_entry(self, menu_name: str) -> str:
        return f"'режим' - 'Пациенты' - '{menu_name}'"

    def format_patient_item_entry(self, menu_name: str, item: str) -> str:
        tab_name = self._catalog.patient_tab_mapping.get(menu_name, menu_name)
        return f"'режим' - 'Пациенты' - '{menu_name}' - tabmenu '{tab_name}' - '{item}'"

    def format_patient_tab_entry(self, menu_name: str, tab_name: str) -> str:
        return f"'режим' - 'Пациенты' - '{menu_name}' - tabmenu '{tab_name}'"

    def format_patient_tab_item_entry(self, menu_name: str, tab_name: str, item: str) -> str:
        return f"'режим' - 'Пациенты' - '{menu_name}' - tabmenu '{tab_name}' - '{item}'"

    def format_practice_section_entry(self, menu_name: str) -> str:
        return f"'режим' - 'Практика' - '{menu_name}'"

    def format_practice_item_entry(self, menu_name: str, item: str) -> str:
        return f"'режим' - 'Практика' - '{menu_name}' - '{item}'"

    def format_practice_tab_entry(self, menu_name: str, tab_name: str) -> str:
        return f"'режим' - 'Практика' - '{menu_name}' - tabmenu '{tab_name}'"

    def format_practice_tab_item_entry(self, menu_name: str, tab_name: str, item: str) -> str:
        return f"'режим' - 'Практика' - '{menu_name}' - tabmenu '{tab_name}' - '{item}'"

    def format_marketing_section_entry(self, menu_name: str) -> str:
        return f"'режим' - 'Маркетинг' - '{menu_name}'"

    def format_marketing_tab_entry(self, menu_name: str, tab_name: str) -> str:
        return f"'режим' - 'Маркетинг' - '{menu_name}' - tabmenu '{tab_name}'"

    def format_marketing_tab_item_entry(self, menu_name: str, tab_name: str, item: str) -> str:
        return f"'режим' - 'Маркетинг' - '{menu_name}' - tabmenu '{tab_name}' - '{item}'"

    def format_insurance_section_entry(self, menu_name: str) -> str:
        return f"'режим' - 'Страхование' - '{menu_name}'"

    def format_insurance_tab_entry(self, menu_name: str, tab_name: str) -> str:
        return f"'режим' - 'Страхование' - '{menu_name}' - tabmenu '{tab_name}'"

    def format_insurance_tab_item_entry(self, menu_name: str, tab_name: str, item: str) -> str:
        return f"'режим' - 'Страхование' - '{menu_name}' - tabmenu '{tab_name}' - '{item}'"

    def format_settings_section_entry(self, menu_name: str) -> str:
        return f"'режим' - 'Настройки' - '{menu_name}'"

    def format_settings_tab_entry(self, menu_name: str, tab_name: str) -> str:
        return f"'режим' - 'Настройки' - '{menu_name}' - tabmenu '{tab_name}'"

    def format_settings_tab_item_entry(self, menu_name: str, tab_name: str, item: str) -> str:
        return f"'режим' - 'Настройки' - '{menu_name}' - tabmenu '{tab_name}' - '{item}'"

    def format_laboratories_section_entry(self, menu_name: str) -> str:
        return f"'режим' - 'Лаборатории' - '{menu_name}'"

    def format_laboratories_tab_entry(self, menu_name: str, tab_name: str) -> str:
        return f"'режим' - 'Лаборатории' - '{menu_name}' - tabmenu '{tab_name}'"

    def format_laboratories_tab_item_entry(self, menu_name: str, tab_name: str, item: str) -> str:
        return f"'режим' - 'Лаборатории' - '{menu_name}' - tabmenu '{tab_name}' - '{item}'"
