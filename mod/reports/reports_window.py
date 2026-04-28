"""Совместимость: реэкспорт из ui/."""
from .dialogs.validation_issues import ValidationIssuesDialog
from .ui.reports_window import ReportsWindow
from .widgets.smooth_scroll_area import SmoothScrollArea

__all__ = ["ReportsWindow", "SmoothScrollArea", "ValidationIssuesDialog"]
