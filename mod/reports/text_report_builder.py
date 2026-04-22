"""
Сохранение текстовых отчетов.
"""
import os
import re
from dataclasses import dataclass
from datetime import datetime


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
