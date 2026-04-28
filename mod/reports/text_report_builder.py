"""Совместимость: реэкспорт из core/. Новый код должен импортировать напрямую."""
from .core.report_builder import TextReportBuilder
from .core.report_data import ReportMetadata, ReportSectionData
from .core.report_parser import TextReportParser

__all__ = ["ReportMetadata", "ReportSectionData", "TextReportBuilder", "TextReportParser"]
