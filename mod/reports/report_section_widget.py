"""Совместимость: реэкспорт из ui/."""
from .ui.section_widget import ReportSectionWidget
from .widgets.resizable_text_edit import ResizablePlainTextEdit
from .widgets.segmented_control import IssueTypeSegmentedControl

__all__ = ["IssueTypeSegmentedControl", "ReportSectionWidget", "ResizablePlainTextEdit"]
