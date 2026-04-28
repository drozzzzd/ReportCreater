"""Структуры данных отчёта (без зависимости от Qt)."""
from dataclasses import dataclass


@dataclass(slots=True)
class ReportMetadata:
    build: str
    database: str
    sir: str
    performer: str
    include_sql: bool
    sql_value: str
    include_doc: bool
    doc_value: str
    include_tax_reference: bool
    tax_reference_value: str


@dataclass(slots=True)
class ReportSectionData:
    number: str
    title: str
    precondition: str
    scenario: str
    issue_type: str
    issue_text: str

    def is_empty(self) -> bool:
        return not any(
            [
                self.title.strip(),
                self.precondition.strip(),
                self.scenario.strip(),
                self.issue_text.strip(),
            ]
        )

    def is_plain_text_block(self) -> bool:
        if self.issue_type == "Текст":
            return True
        return bool(self.issue_text.strip()) and not any(
            [
                self.title.strip(),
                self.precondition.strip(),
                self.scenario.strip(),
            ]
        )
