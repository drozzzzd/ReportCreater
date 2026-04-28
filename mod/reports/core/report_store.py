"""SQLite-backed report history."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from dataclasses import asdict
from datetime import datetime
from typing import Any

from .report_data import ReportMetadata, ReportSectionData


class ReportStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def ensure_schema(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with closing(self._connect()) as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        saved_at TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        filepath TEXT NOT NULL,
                        sir TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata_json TEXT NOT NULL,
                        sections_json TEXT NOT NULL
                    )
                    """
                )
                connection.execute("CREATE INDEX IF NOT EXISTS idx_reports_saved_at ON reports(saved_at DESC)")

    def save(
        self,
        *,
        metadata: ReportMetadata,
        sections: list[ReportSectionData],
        filepath: str,
        content: str,
    ) -> int:
        self.ensure_schema()
        title = self._build_title(metadata, sections)
        saved_at = datetime.now().isoformat(timespec="seconds")
        with closing(self._connect()) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO reports (
                        saved_at, filename, filepath, sir, title, content, metadata_json, sections_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        saved_at,
                        os.path.basename(filepath),
                        filepath,
                        metadata.sir,
                        title,
                        content,
                        json.dumps(asdict(metadata), ensure_ascii=False),
                        json.dumps([asdict(section) for section in sections], ensure_ascii=False),
                    ),
                )
                return int(cursor.lastrowid)

    def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        self.ensure_schema()
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT id, saved_at, filename, filepath, sir, title
                FROM reports
                ORDER BY saved_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, report_id: int) -> dict[str, Any] | None:
        self.ensure_schema()
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT id, saved_at, filename, filepath, sir, title, content, metadata_json, sections_json
                FROM reports
                WHERE id = ?
                """,
                (report_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    @staticmethod
    def decode_record(record: dict[str, Any]) -> tuple[ReportMetadata, list[ReportSectionData]]:
        metadata_values = json.loads(record["metadata_json"])
        section_values = json.loads(record["sections_json"])
        metadata = ReportMetadata(**metadata_values)
        sections = [ReportSectionData(**section) for section in section_values]
        return metadata, sections

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _build_title(metadata: ReportMetadata, sections: list[ReportSectionData]) -> str:
        first_title = next((section.title.strip() for section in sections if section.title.strip()), "")
        if metadata.sir and first_title:
            return f"{metadata.sir} - {first_title}"
        return metadata.sir or first_title or "Без названия"
