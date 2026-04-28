"""Сборка и сохранение TXT-отчёта."""
import os
import re
from datetime import datetime

from .report_data import ReportMetadata, ReportSectionData


class TextReportBuilder:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def ensure_output_dir(self):
        os.makedirs(self.output_dir, exist_ok=True)

    def build_content(self, metadata: ReportMetadata, sections: list[ReportSectionData]) -> str:
        lines: list[str] = []

        build = metadata.build.strip()
        database = metadata.database.strip()

        lines.append(f"Build {build}")
        lines.append(f"BD - {database}")

        if metadata.include_sql:
            lines.append(f"SQL - {metadata.sql_value.strip()}")

        if metadata.include_doc:
            lines.append(f"DOC - {metadata.doc_value.strip()}")

        if metadata.include_tax_reference:
            lines.append(f"Tax Referens - {metadata.tax_reference_value.strip()}")

        lines.append("")

        for section in sections:
            if section.is_plain_text_block():
                if section.issue_text.strip():
                    lines.append(section.issue_text.strip())
                    lines.append("")
                continue

            if section.is_empty():
                continue

            title = section.title.strip()
            number = str(section.number).strip() or "?"
            lines.append(f"# {number} - {title}")

            if section.precondition.strip():
                lines.append("Pre-Condition:")
                lines.extend(self._normalize_block(section.precondition))
                lines.append("")

            if section.scenario.strip():
                lines.append("Scenario:")
                lines.extend(self._normalize_block(section.scenario))
                lines.append("")

            if section.issue_text.strip():
                lines.append(f"{section.issue_type}: {section.issue_text.strip()}")
                lines.append("")

        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines)

    def save(self, metadata: ReportMetadata, sections: list[ReportSectionData]) -> str:
        self.ensure_output_dir()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        sir = self._sanitize_filename_part(metadata.sir.strip() or "SIR")
        filename = f"{timestamp}-{sir}.txt"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(self.build_content(metadata, sections))

        return filepath

    @staticmethod
    def _sanitize_filename_part(value: str) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value).strip(" .")
        return cleaned or "SIR"

    @staticmethod
    def _normalize_block(text: str) -> list[str]:
        result: list[str] = []
        for line in text.splitlines():
            cleaned = line.strip()
            if cleaned:
                result.append(cleaned)
        return result
