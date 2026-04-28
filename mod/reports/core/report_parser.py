"""Парсинг сохранённого TXT-отчёта обратно в данные."""
import os
import re

from .report_data import ReportMetadata, ReportSectionData


class TextReportParser:
    FILENAME_SIR_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-(.+)\.txt$", re.IGNORECASE)

    def parse_file(self, filepath: str) -> tuple[ReportMetadata, list[ReportSectionData]]:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
        sir = self.extract_sir_from_filename(filepath)
        return self.parse_content(content, sir=sir)

    def parse_content(self, content: str, *, sir: str = "") -> tuple[ReportMetadata, list[ReportSectionData]]:
        lines = content.splitlines()
        metadata_lines, body_start = self._split_metadata(lines)

        metadata_values = {
            "build": "",
            "database": "",
            "sql_value": "",
            "doc_value": "",
            "tax_reference_value": "",
        }
        include_sql = False
        include_doc = False
        include_tax_reference = False

        for line in metadata_lines:
            if line.startswith("Build "):
                metadata_values["build"] = line.removeprefix("Build ").strip()
            elif line.startswith("BD - "):
                metadata_values["database"] = line.removeprefix("BD - ").strip()
            elif line.startswith("SQL - "):
                include_sql = True
                metadata_values["sql_value"] = line.removeprefix("SQL - ").strip()
            elif line.startswith("DOC - "):
                include_doc = True
                metadata_values["doc_value"] = line.removeprefix("DOC - ").strip()
            elif line.startswith("Tax Referens - "):
                include_tax_reference = True
                metadata_values["tax_reference_value"] = line.removeprefix("Tax Referens - ").strip()

        body_lines = lines[body_start:]
        sections = self._parse_sections(body_lines)
        performer = self._infer_performer(sir, sections)

        return (
            ReportMetadata(
                build=metadata_values["build"],
                database=metadata_values["database"],
                sir=sir,
                performer=performer,
                include_sql=include_sql,
                sql_value=metadata_values["sql_value"],
                include_doc=include_doc,
                doc_value=metadata_values["doc_value"],
                include_tax_reference=include_tax_reference,
                tax_reference_value=metadata_values["tax_reference_value"],
            ),
            sections,
        )

    def extract_sir_from_filename(self, filepath: str) -> str:
        filename = os.path.basename(filepath)
        match = self.FILENAME_SIR_PATTERN.fullmatch(filename)
        return match.group(1) if match else ""

    @staticmethod
    def _split_metadata(lines: list[str]) -> tuple[list[str], int]:
        for index, line in enumerate(lines):
            if not line.strip():
                return lines[:index], index + 1
        return lines, len(lines)

    def _parse_sections(self, lines: list[str]) -> list[ReportSectionData]:
        sections: list[ReportSectionData] = []
        index = 0
        next_number = 1

        while index < len(lines):
            while index < len(lines) and not lines[index].strip():
                index += 1
            if index >= len(lines):
                break

            header_match = re.match(r"^#\s+(\d+)\s+-\s*(.*)$", lines[index])
            if header_match:
                section, index = self._parse_numbered_section(lines, index)
                sections.append(section)
                section_number = str(section.number).strip()
                if section_number.isdigit():
                    next_number = max(next_number, int(section_number) + 1)
                continue

            text_lines: list[str] = []
            while index < len(lines) and lines[index].strip() and not lines[index].startswith("# "):
                text_lines.append(lines[index].strip())
                index += 1
            if text_lines:
                sections.append(
                    ReportSectionData(
                        number=str(next_number),
                        title="",
                        precondition="",
                        scenario="",
                        issue_type="Текст",
                        issue_text="\n".join(text_lines),
                    )
                )
                next_number += 1

        return sections or [
            ReportSectionData(
                number="1",
                title="",
                precondition="",
                scenario="",
                issue_type="Error",
                issue_text="",
            )
        ]

    def _parse_numbered_section(self, lines: list[str], index: int) -> tuple[ReportSectionData, int]:
        header_match = re.match(r"^#\s+(\d+)\s+-\s*(.*)$", lines[index])
        number = header_match.group(1) if header_match else "1"
        title = header_match.group(2).strip() if header_match else ""
        index += 1

        precondition: list[str] = []
        scenario: list[str] = []
        issue_type = "Error"
        issue_text: list[str] = []

        while index < len(lines):
            line = lines[index]
            if line.startswith("# "):
                break
            if not line.strip():
                index += 1
                continue
            if line == "Pre-Condition:":
                precondition, index = self._collect_block(lines, index + 1)
                continue
            if line == "Scenario:":
                scenario, index = self._collect_block(lines, index + 1)
                continue
            issue_match = re.match(r"^(Error|Question):\s*(.*)$", line)
            if issue_match:
                issue_type = issue_match.group(1)
                issue_text = [issue_match.group(2).strip()] if issue_match.group(2).strip() else []
                tail, index = self._collect_block(lines, index + 1)
                issue_text.extend(tail)
                continue
            issue_text.append(line.strip())
            index += 1

        return (
            ReportSectionData(
                number=number,
                title=title,
                precondition="\n".join(precondition),
                scenario="\n".join(scenario),
                issue_type=issue_type,
                issue_text="\n".join(issue_text),
            ),
            index,
        )

    @staticmethod
    def _collect_block(lines: list[str], index: int) -> tuple[list[str], int]:
        result: list[str] = []
        while index < len(lines):
            line = lines[index]
            if not line.strip() or line.startswith("# ") or line in {"Pre-Condition:", "Scenario:"}:
                break
            if re.match(r"^(Error|Question):\s*", line):
                break
            result.append(line.strip())
            index += 1
        return result, index

    @staticmethod
    def _infer_performer(sir: str, sections: list[ReportSectionData]) -> str:
        if not sir:
            return ""
        pattern = re.compile(rf"attachment:{re.escape(sir)}_([^_\s]+)_\d+\.jpg", re.IGNORECASE)
        for section in sections:
            for block in (section.precondition, section.scenario, section.issue_text):
                match = pattern.search(block)
                if match:
                    return match.group(1)
        return ""
