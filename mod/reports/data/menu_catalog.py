"""Загрузчик статичного каталога меню из menu_catalog.json."""
import json
from pathlib import Path

CATALOG_PATH = Path(__file__).with_name("menu_catalog.json")


def _load_catalog() -> dict:
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _nested_to_tuple_keys(nested: dict) -> dict[tuple[str, str], list[str]]:
    """{a: {b: [...]}} -> {(a, b): [...]}"""
    return {(k1, k2): items for k1, sub in nested.items() for k2, items in sub.items()}


class MenuCatalog:
    """Хранит структуру меню и предоставляет аксессоры. Без зависимости от Qt."""

    def __init__(self):
        raw = _load_catalog()

        constants = raw["constants"]
        self.APPOINTMENT_MODE_NAME = constants["appointment_mode_name"]
        self.MODE_MENU_NAME = constants["mode_menu_name"]
        self.TAX_REFERENCE_BUTTON_NAME = constants["tax_reference_button_name"]
        self.TAX_REFERENCE_SYSTEM_NAME = constants["tax_reference_system_name"]
        self.TAX_REFERENCE_MENU_NAME = constants["tax_reference_menu_name"]

        self.TAX_REFERENCE_ENTRIES: list[tuple[str, tuple[str, ...]]] = [
            (entry["label"], tuple(entry["path"])) for entry in raw["tax_reference_entries"]
        ]
        self.MODE_MENU_ITEMS: list[str] = list(raw["mode_menu_items"])
        self.MODE_NAMES: list[str] = list(raw["mode_names"])
        self.search_view_items: list[str] = list(raw["search_view_items"])

        appointment = raw["appointment"]
        self.sub_menu_names: list[str] = list(appointment["menu_names"])
        self.submenu_items: dict[str, list[str]] = {
            k: list(v) for k, v in appointment["items"].items()
        }
        self.appointment_mode_items: list[str] = list(appointment["mode_items"])

        patient = raw["patient"]
        self.patient_menu_names: list[str] = list(patient["menu_names"])
        self.patient_tabs: dict[str, list[str]] = {k: list(v) for k, v in patient["tabs"].items()}
        self.patient_tab_mapping: dict[str, str] = dict(patient["tab_mapping"])
        self.patient_nested_items = _nested_to_tuple_keys(patient["nested_items"])
        self.patient_submenu_items: dict[str, list[str]] = self._augment_with_search_view(
            patient["submenu_items"], self.search_view_items
        )

        practice = raw["practice"]
        self.practice_menu_names: list[str] = list(practice["menu_names"])
        self.practice_menu_items: dict[str, list[str]] = {
            k: list(v) for k, v in practice["items"].items()
        }
        self.practice_tabs: dict[str, list[str]] = {k: list(v) for k, v in practice["tabs"].items()}
        self.practice_nested_items = _nested_to_tuple_keys(practice["nested_items"])

        marketing = raw["marketing"]
        self.marketing_menu_names: list[str] = list(marketing["menu_names"])
        self.marketing_tabs: dict[str, list[str]] = {
            k: list(v) for k, v in marketing["tabs"].items()
        }
        self.marketing_nested_items = _nested_to_tuple_keys(marketing["nested_items"])

        insurance = raw["insurance"]
        self.insurance_menu_names: list[str] = list(insurance["menu_names"])
        self.insurance_tabs: dict[str, list[str]] = {
            k: list(v) for k, v in insurance["tabs"].items()
        }
        self.insurance_nested_items = _nested_to_tuple_keys(insurance["nested_items"])

        settings = raw["settings"]
        self.settings_menu_names: list[str] = list(settings["menu_names"])
        self.settings_tabs: dict[str, list[str]] = {k: list(v) for k, v in settings["tabs"].items()}
        self.settings_nested_items = _nested_to_tuple_keys(settings["nested_items"])

        laboratories = raw["laboratories"]
        self.laboratories_menu_names: list[str] = list(laboratories["menu_names"])
        self.laboratories_tabs: dict[str, list[str]] = {
            k: list(v) for k, v in laboratories["tabs"].items()
        }
        self.laboratories_nested_items = _nested_to_tuple_keys(laboratories["nested_items"])

    @staticmethod
    def _augment_with_search_view(
        submenu_items: dict, search_view_items: list[str]
    ) -> dict[str, list[str]]:
        """Добавляет search_view_items в каждый список, удаляя финальную 'Отмена'."""
        result: dict[str, list[str]] = {}
        for key, value in submenu_items.items():
            items = list(value)
            if items and items[-1] == "Отмена":
                items.pop()
            items.extend(search_view_items)
            result[key] = items
        return result

    # ---- Аксессоры ----

    def get_mode_names(self) -> list[str]:
        return list(self.MODE_NAMES)

    def get_mode_name(self, index: int) -> str:
        return self.MODE_NAMES[index]

    def get_mode_menu_name(self) -> str:
        return self.MODE_MENU_NAME

    def get_mode_menu_items(self) -> list[str]:
        return list(self.MODE_MENU_ITEMS)

    def get_appointment_menu_names(self) -> list[str]:
        return list(self.sub_menu_names)

    def get_appointment_items(self, menu_name: str) -> list[str]:
        return [item for item in self.submenu_items.get(menu_name, []) if item != "Отмена"]

    def get_patient_menu_names(self) -> list[str]:
        return list(self.patient_menu_names)

    def get_patient_items(self, menu_name: str) -> list[str]:
        return [item for item in self.patient_submenu_items.get(menu_name, []) if item != "Отмена"]

    def get_patient_tabs(self, menu_name: str) -> list[str]:
        return list(self.patient_tabs.get(menu_name, []))

    def get_patient_tab_items(self, menu_name: str, tab_name: str) -> list[str]:
        return [
            item
            for item in self.patient_nested_items.get((menu_name, tab_name), [])
            if item != "Отмена"
        ]

    def has_patient_tabs(self, menu_name: str) -> bool:
        return menu_name in self.patient_tabs

    def get_practice_menu_names(self) -> list[str]:
        return list(self.practice_menu_names)

    def get_practice_items(self, menu_name: str) -> list[str]:
        return list(self.practice_menu_items.get(menu_name, []))

    def get_practice_tabs(self, menu_name: str) -> list[str]:
        return list(self.practice_tabs.get(menu_name, []))

    def get_practice_tab_items(self, menu_name: str, tab_name: str) -> list[str]:
        return list(self.practice_nested_items.get((menu_name, tab_name), []))

    def has_practice_tabs(self, menu_name: str) -> bool:
        return menu_name in self.practice_tabs

    def get_marketing_menu_names(self) -> list[str]:
        return list(self.marketing_menu_names)

    def get_marketing_tabs(self, menu_name: str) -> list[str]:
        return list(self.marketing_tabs.get(menu_name, []))

    def get_marketing_tab_items(self, menu_name: str, tab_name: str) -> list[str]:
        return list(self.marketing_nested_items.get((menu_name, tab_name), []))

    def has_marketing_tabs(self, menu_name: str) -> bool:
        return menu_name in self.marketing_tabs

    def get_insurance_menu_names(self) -> list[str]:
        return list(self.insurance_menu_names)

    def get_insurance_tabs(self, menu_name: str) -> list[str]:
        return list(self.insurance_tabs.get(menu_name, []))

    def get_insurance_tab_items(self, menu_name: str, tab_name: str) -> list[str]:
        return list(self.insurance_nested_items.get((menu_name, tab_name), []))

    def has_insurance_tabs(self, menu_name: str) -> bool:
        return menu_name in self.insurance_tabs

    def get_settings_menu_names(self) -> list[str]:
        return list(self.settings_menu_names)

    def get_settings_tabs(self, menu_name: str) -> list[str]:
        return list(self.settings_tabs.get(menu_name, []))

    def get_settings_tab_items(self, menu_name: str, tab_name: str) -> list[str]:
        return list(self.settings_nested_items.get((menu_name, tab_name), []))

    def has_settings_tabs(self, menu_name: str) -> bool:
        return menu_name in self.settings_tabs

    def get_laboratories_menu_names(self) -> list[str]:
        return list(self.laboratories_menu_names)

    def get_laboratories_tabs(self, menu_name: str) -> list[str]:
        return list(self.laboratories_tabs.get(menu_name, []))

    def get_laboratories_tab_items(self, menu_name: str, tab_name: str) -> list[str]:
        return list(self.laboratories_nested_items.get((menu_name, tab_name), []))

    def has_laboratories_tabs(self, menu_name: str) -> bool:
        return menu_name in self.laboratories_tabs

    def get_tax_reference_items(self) -> list[str]:
        return [label for label, _ in self.TAX_REFERENCE_ENTRIES]

    def get_tax_reference_entries(self) -> list[tuple[str, tuple[str, ...]]]:
        return [(label, tuple(path)) for label, path in self.TAX_REFERENCE_ENTRIES]
