"""Конструктор TXT-отчётов: главное окно и публичные классы."""
from .core.report_builder import TextReportBuilder
from .core.report_data import ReportMetadata, ReportSectionData
from .core.report_parser import TextReportParser
from .ui.reports_window import ReportsWindow
from .ui.section_widget import ReportSectionWidget

__all__ = [
    "ReportMetadata",
    "ReportSectionData",
    "ReportSectionWidget",
    "ReportsWindow",
    "TextReportBuilder",
    "TextReportParser",
]
