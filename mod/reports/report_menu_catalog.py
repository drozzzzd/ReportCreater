"""Совместимость: объединяет MenuCatalog (данные) и MenuFormatter (логика)."""
from .core.menu_formatter import MenuFormatter
from .data.menu_catalog import MenuCatalog


class DropdownMenuManager(MenuCatalog):
    """Тонкая обёртка для обратной совместимости: каталог + форматтер в одном объекте."""

    def __init__(self, parent_frame=None):
        super().__init__()
        self.parent = parent_frame
        self._formatter = MenuFormatter(self)

    def __getattr__(self, name: str):
        # Делегируем все format_* методы форматтеру
        if name.startswith("format_"):
            return getattr(self._formatter, name)
        raise AttributeError(name)


__all__ = ["DropdownMenuManager"]
