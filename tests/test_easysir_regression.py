import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextOption
from PyQt6.QtWidgets import QApplication, QMessageBox, QPlainTextEdit

import main as app_main
from mod.reports.report_section_widget import ResizablePlainTextEdit
from mod.reports.reports_window import ReportsWindow, SmoothScrollArea


class ReportBuilderStandaloneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle("Fusion")

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.window = ReportsWindow({"general": {"reports_dir": self.temp_dir.name}}, "")
        self.window.output_dir_input.setText(self.temp_dir.name)
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.temp_dir.cleanup()

    def fill_required_fields(self):
        section = self.window.sections[0]
        self.window.build_input.setText("5917")
        self.window.database_input.setText("Test")
        self.window.sir_input.setText("SIR-2026-001")
        section.title_input.setText("Проверка отчета")
        section.pre_text.setPlainText("Открыть режим")
        section.scenario_text.setPlainText("Выполнить шаг")
        section.issue_text.setPlainText("Ошибка в тексте")
        self.app.processEvents()
        return section

    def test_load_config_has_minimal_general_section(self):
        config = app_main.load_config()
        self.assertIn("general", config)
        self.assertIn("reports_dir", config["general"])

    def test_window_starts_with_empty_main_fields_and_zero_progress(self):
        self.assertEqual(self.window.windowTitle(), "Конструктор отчетов")
        self.assertEqual(len(self.window.sections), 1)
        self.assertLessEqual(self.window.width(), 1120)
        self.assertIsNotNone(self.window.preview_shell)
        self.assertIsNotNone(self.window.progress_shell)
        self.assertIsNotNone(self.window.hero_panel)
        self.assertFalse(self.window.hero_panel.isHidden())
        self.assertIs(self.window.scroll_area.widget(), self.window.workflow_content)
        self.assertIsInstance(self.window.scroll_area, SmoothScrollArea)
        self.assertIs(self.window.hero_panel.parentWidget(), self.window.workflow_content)
        self.assertIs(self.window.meta_group.parentWidget(), self.window.workflow_content)
        self.assertIs(self.window.sections_host.parentWidget(), self.window.workflow_content)
        self.assertEqual(self.window.build_input.text(), "")
        self.assertEqual(self.window.database_input.text(), "")
        self.assertEqual(self.window.sir_input.text(), "")
        self.assertEqual(self.window.performer_input.text(), "")
        self.assertTrue(self.window.sql_check.isChecked())
        self.assertTrue(self.window.doc_check.isChecked())
        self.assertTrue(self.window.sql_input.isEnabled())
        self.assertTrue(self.window.doc_input.isEnabled())
        self.assertTrue(self.window.tax_reference_check.isChecked())
        self.assertTrue(self.window.tax_reference_input.isEnabled())
        self.assertEqual(self.window.completion_bar.value(), 0)
        self.assertEqual(self.window.preview_text.lineWrapMode(), QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.assertEqual(
            self.window.preview_text.wordWrapMode(),
            QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere,
        )

    def test_section_editors_are_compact_and_resizable(self):
        section = self.window.sections[0]
        self.assertIsInstance(section.pre_text, ResizablePlainTextEdit)
        self.assertIsInstance(section.scenario_text, ResizablePlainTextEdit)
        self.assertIsInstance(section.issue_text, ResizablePlainTextEdit)
        self.assertEqual(section.pre_text.height(), 58)
        self.assertEqual(section.scenario_text.height(), 58)
        self.assertEqual(section.issue_text.height(), 58)
        section.issue_text.setPlainText("\n".join(f"line {index}" for index in range(12)))
        self.app.processEvents()
        self.assertGreater(section.issue_text.height(), 58)
        section.issue_text.clear()
        self.app.processEvents()
        self.assertEqual(section.issue_text.height(), 58)
        self.assertIs(self.window.sections_layout.itemAt(0).widget(), section)
        self.assertIs(section.root_layout.itemAt(3).widget(), section.issue_group)

    def test_issue_type_is_segmented_and_updates_preview(self):
        section = self.fill_required_fields()
        section.issue_type_combo.setCurrentText("Question")
        self.app.processEvents()

        self.assertEqual(section.issue_type_combo.currentText(), "Question")
        self.assertIn("Question: Ошибка в тексте", self.window.preview_text.toPlainText())

    def test_text_issue_type_outputs_plain_text_without_prefix(self):
        section = self.fill_required_fields()
        section.issue_type_combo.setCurrentText("Текст")
        section.issue_text.setPlainText("plain text only")
        self.app.processEvents()

        preview = self.window.preview_text.toPlainText()
        self.assertIn("\nplain text only", preview)
        self.assertNotIn("# 1 - Проверка отчета", preview)
        self.assertNotIn("Pre-Condition:", preview)
        self.assertNotIn("Scenario:", preview)
        self.assertNotIn("Текст: plain text only", preview)
        self.assertNotIn("Error: plain text only", preview)

    def test_text_issue_type_ignores_empty_section_fields(self):
        section = self.window.sections[0]
        self.window.build_input.setText("5917")
        self.window.database_input.setText("Test")
        self.window.sir_input.setText("SIR-2026-001")
        self.window.sql_input.setText("select 1")
        self.window.doc_input.setText("doc-1")
        self.window.tax_reference_input.setText("tax-reference-1")
        section.issue_type_combo.setCurrentText("Текст")
        section.issue_text.setPlainText("free text")
        self.app.processEvents()

        preview = self.window.preview_text.toPlainText()
        self.assertIn("\nfree text", preview)
        self.assertNotIn("# 1 - ", preview)
        self.assertEqual(self.window.completion_bar.value(), 100)
        self.assertNotIn("Раздел #1: Название", self.window.collect_validation_issues())

    def test_issue_only_section_does_not_emit_empty_section_header(self):
        section = self.window.sections[0]
        section.issue_text.setPlainText("123")
        self.app.processEvents()

        preview = self.window.preview_text.toPlainText()
        self.assertIn("\n123", preview)
        self.assertNotIn("# 1 -", preview)
        self.assertNotIn("Error: 123", preview)

    def test_live_preview_updates_with_everything_user_types(self):
        section = self.fill_required_fields()
        preview = self.window.preview_text.toPlainText()
        self.assertIn("Build 5917", preview)
        self.assertIn("BD - Test", preview)
        self.assertNotIn("SIR - SIR-2026-001", preview)
        self.assertIn("SQL - ", preview)
        self.assertIn("DOC - ", preview)
        self.assertIn("Tax Referens - ", preview)
        self.assertIn("# 1 - Проверка отчета", preview)
        self.assertIn("Pre-Condition:\nОткрыть режим", preview)
        self.assertIn("Scenario:\nВыполнить шаг", preview)
        self.assertIn("Error: Ошибка в тексте", preview)

        section.issue_text.setPlainText("Новый текст ошибки")
        self.app.processEvents()
        self.assertIn("Error: Новый текст ошибки", self.window.preview_text.toPlainText())

    def test_sql_and_doc_are_added_to_preview_and_saved_file(self):
        self.fill_required_fields()
        self.window.sql_input.setText("select 1")
        self.window.doc_input.setText("doc-1")
        self.window.tax_reference_input.setText("tax-reference-1")
        self.app.processEvents()

        preview = self.window.preview_text.toPlainText()
        self.assertIn("DOC - doc-1", preview)
        self.assertIn("SQL - select 1", preview)
        self.assertIn("Tax Referens - tax-reference-1", preview)
        self.assertLess(preview.index("DOC - doc-1"), preview.index("Tax Referens - tax-reference-1"))
        self.assertLess(preview.index("Tax Referens - tax-reference-1"), preview.index("# 1 - Проверка отчета"))

        with (
            patch.object(self.window, "confirm_save_with_issues", return_value=True) as confirm_mock,
            patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No),
        ):
            self.window.save_report()

        confirm_mock.assert_not_called()
        files = sorted(Path(self.temp_dir.name).glob("*.txt"))
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.endswith("-SIR-2026-001.txt"))
        content = files[0].read_text(encoding="utf-8")
        self.assertIn("SQL - select 1", content)
        self.assertIn("DOC - doc-1", content)
        self.assertIn("Tax Referens - tax-reference-1", content)
        self.assertLess(content.index("DOC - doc-1"), content.index("Tax Referens - tax-reference-1"))
        self.assertLess(content.index("Tax Referens - tax-reference-1"), content.index("# 1 - Проверка отчета"))

    def test_tax_reference_can_be_excluded_from_report(self):
        self.fill_required_fields()
        self.window.sql_input.setText("select 1")
        self.window.doc_input.setText("doc-1")
        self.window.tax_reference_input.setText("tax-reference-1")
        self.window.tax_reference_check.setChecked(False)
        self.app.processEvents()

        preview = self.window.preview_text.toPlainText()
        self.assertIn("DOC - doc-1", preview)
        self.assertNotIn("Tax Referens - tax-reference-1", preview)

    def test_tax_reference_user_help_menu_uses_tax_reference_field_value(self):
        section = self.window.sections[0]
        self.window.tax_reference_input.setText("Tax User Value")
        entry = next(
            path
            for label, path in section.menu_manager.get_tax_reference_entries()
            if label == "Справка для налоговой"
        )
        section._insert_tax_reference_entry(section.pre_text, entry)
        self.app.processEvents()

        text = section.pre_text.toPlainText()
        self.assertIn(
            "'Tax User Value' - tabmenu 'Документы' - 'Справка для налоговой' - '№ карты' - "
            "'Найти' - 'Год справки' - 'Показать платежи пациента'",
            text,
        )
        self.assertNotIn("'Tax Reference'", text)

    def test_tax_reference_user_help_menu_uses_split_rows_and_partial_paths(self):
        section = self.window.sections[0]
        self.window.tax_reference_input.setText("Tax User Value")
        document_name = "Журнал сформированных справок для налоговых"

        self.assertEqual(
            section.menu_manager.get_tax_reference_items(),
            [
                document_name,
                document_name,
                "Отчет по сформ.справкам в старой версии программы",
                "Отчет по предоставленным справкам",
                "Справка для налоговой",
            ],
        )

        section._insert_tax_reference_entry(section.pre_text, (document_name,))
        self.app.processEvents()

        self.assertEqual(
            section.pre_text.toPlainText().strip(),
            "'Tax User Value' - tabmenu 'Документы' - 'Журнал сформированных справок для налоговых'",
        )

    def test_tax_reference_user_help_menu_contains_required_paths(self):
        paths = [
            self.window.sections[0].menu_manager.format_tax_reference_entry("Tax User Value", path)
            for _, path in self.window.sections[0].menu_manager.get_tax_reference_entries()
        ]

        self.assertEqual(
            paths,
            [
                "'Tax User Value' - tabmenu 'Документы' - 'Журнал сформированных справок для налоговых' - "
                "'по году справки' - 'выбрать год' - 'Просмотр'",
                "'Tax User Value' - tabmenu 'Документы' - 'Журнал сформированных справок для налоговых' - "
                "'по дате справки' - 'выбрать период' - 'Просмотр'",
                "'Tax User Value' - tabmenu 'Документы' - 'Отчет по сформ.справкам в старой версии программы' - "
                "'выбрать период' - 'Просмотр'",
                "'Tax User Value' - tabmenu 'Документы' - 'Отчет по предоставленным справкам' - "
                "'выбрать период/пациента' - 'Просмотр'",
                "'Tax User Value' - tabmenu 'Документы' - 'Справка для налоговой' - '№ карты' - "
                "'Найти' - 'Год справки' - 'Показать платежи пациента'",
            ],
        )

    def test_tax_reference_icon_uses_fns_asset(self):
        self.assertFalse(self.window.sections[0]._create_tax_reference_icon().isNull())

    def test_window_switches_splitter_orientation_on_resize(self):
        self.window.resize(1380, 900)
        self.window._update_responsive_layout(force=True)
        self.app.processEvents()
        self.assertEqual(self.window.content_splitter.orientation(), Qt.Orientation.Horizontal)

        self.window.resize(980, 900)
        self.window._update_responsive_layout(force=True)
        self.app.processEvents()
        self.assertEqual(self.window.content_splitter.orientation(), Qt.Orientation.Vertical)

    def test_attachment_button_uses_sir_executor_and_counter(self):
        section = self.window.sections[0]
        self.window.sir_input.setText("43533")
        self.app.processEvents()
        self.assertEqual(self.window.build_attachment_text(), "attachment:43533")

        self.window.performer_input.setText("IM")
        section._insert_attachment(section.pre_text)
        section._insert_attachment(section.pre_text)
        self.app.processEvents()

        self.assertEqual(
            section.pre_text.toPlainText().strip(),
            "attachment:43533_IM_01.jpg\nattachment:43533_IM_02.jpg",
        )
        preview = self.window.preview_text.toPlainText()
        self.assertIn("attachment:43533_IM_01.jpg", preview)
        self.assertIn("attachment:43533_IM_02.jpg", preview)

    def test_attachment_counter_counts_inline_values_and_session_reservations(self):
        section = self.window.sections[0]
        self.window.sir_input.setText("43533")
        self.window.performer_input.setText("IM")
        section.issue_text.setPlainText("Ошибка уже содержит attachment:43533_IM_01.jpg")
        self.app.processEvents()

        self.assertEqual(self.window.build_attachment_text(), "attachment:43533_IM_02.jpg")
        self.assertEqual(self.window.build_attachment_text(), "attachment:43533_IM_03.jpg")

    def test_remove_attachment_button_deletes_last_attachment_line(self):
        section = self.window.sections[0]
        self.window.sir_input.setText("43533")
        self.window.performer_input.setText("IM")
        section._insert_attachment(section.issue_text)
        section._insert_attachment(section.issue_text)
        self.app.processEvents()

        section._remove_last_attachment(section.issue_text)
        self.app.processEvents()
        self.assertEqual(section.issue_text.toPlainText(), "attachment:43533_IM_01.jpg")

        section._remove_last_attachment(section.issue_text)
        self.app.processEvents()
        self.assertEqual(section.issue_text.toPlainText(), "")

    def test_completion_bar_reaches_100_when_all_required_fields_are_filled(self):
        self.fill_required_fields()
        self.window.sql_input.setText("select 1")
        self.window.doc_input.setText("doc-1")
        self.window.tax_reference_input.setText("tax-reference-1")
        self.app.processEvents()
        self.assertEqual(self.window.completion_bar.value(), 100)
        self.assertIn("100%", self.window.completion_label.text())

    def test_meta_panel_can_be_collapsed_to_give_sections_more_space(self):
        self.window.build_input.setText("5917")
        self.window.database_input.setText("Test")
        self.window.sir_input.setText("43533")
        self.window.performer_input.setText("IM")
        self.app.processEvents()
        expanded_height = self.window.meta_group.sizeHint().height()

        self.window.set_meta_collapsed(True)
        self.app.processEvents()

        self.assertTrue(self.window.meta_group.isHidden())
        self.assertFalse(self.window.meta_collapsed_bar.isHidden())
        self.assertLess(self.window.meta_collapsed_bar.sizeHint().height(), expanded_height)
        self.assertIn("5917", self.window.meta_collapsed_title.text())
        self.assertIn("Test", self.window.meta_collapsed_title.text())
        self.assertIn("attachment:43533_IM_01.jpg", self.window.meta_collapsed_title.text())

        self.window.set_meta_collapsed(False)
        self.app.processEvents()

        self.assertFalse(self.window.meta_group.isHidden())
        self.assertTrue(self.window.meta_collapsed_bar.isHidden())

    def test_top_constructor_panel_can_be_collapsed(self):
        self.window.set_hero_collapsed(True)
        self.app.processEvents()

        self.assertTrue(self.window.hero_panel.isHidden())
        self.assertFalse(self.window.hero_collapsed_bar.isHidden())
        self.assertIn("Конструктор отчетов скрыт", self.window.hero_collapsed_title.text())
        self.assertIn("Разделов: 1", self.window.hero_collapsed_title.text())

        self.window.add_section()
        self.app.processEvents()
        self.assertIn("Разделов: 2", self.window.hero_collapsed_title.text())

        self.window.set_hero_collapsed(False)
        self.app.processEvents()
        self.assertFalse(self.window.hero_panel.isHidden())
        self.assertTrue(self.window.hero_collapsed_bar.isHidden())

    def test_attachment_preview_labels_show_next_value_without_reserving_counter(self):
        section = self.window.sections[0]
        self.window.sir_input.setText("43533")
        self.window.performer_input.setText("IM")
        self.app.processEvents()

        self.assertEqual(self.window.next_attachment_label.text(), "attachment:43533_IM_01.jpg")
        self.assertIn("attachment:43533_IM_01.jpg", section.attachment_hint_label.text())
        self.assertEqual(self.window.build_attachment_text(), "attachment:43533_IM_01.jpg")

    def test_session_cache_restores_report_draft(self):
        section = self.fill_required_fields()
        self.window.performer_input.setText("IM")
        self.window.sql_input.setText("select 1")
        self.window.doc_input.setText("doc-1")
        self.window.tax_reference_input.setText("tax-reference-1")
        section._insert_attachment(section.issue_text)
        self.window.set_hero_collapsed(True)
        self.window.set_meta_collapsed(True)
        self.app.processEvents()

        cache_path = Path(self.window._session_cache_path)
        self.assertTrue(cache_path.exists())

        restored = ReportsWindow({"general": {"reports_dir": self.temp_dir.name}}, "")
        try:
            self.assertEqual(restored.build_input.text(), "5917")
            self.assertEqual(restored.database_input.text(), "Test")
            self.assertEqual(restored.sir_input.text(), "SIR-2026-001")
            self.assertEqual(restored.performer_input.text(), "IM")
            self.assertEqual(restored.sql_input.text(), "select 1")
            self.assertEqual(restored.doc_input.text(), "doc-1")
            self.assertEqual(restored.tax_reference_input.text(), "tax-reference-1")
            self.assertEqual(restored.sections[0].title_input.text(), "Проверка отчета")
            self.assertIn("attachment:SIR-2026-001_IM_01.jpg", restored.sections[0].issue_text.toPlainText())
            self.assertTrue(restored.hero_panel.isHidden())
            self.assertTrue(restored.meta_group.isHidden())
            self.assertEqual(restored.build_attachment_text(), "attachment:SIR-2026-001_IM_02.jpg")
        finally:
            restored.close()
            restored.deleteLater()
            self.app.processEvents()

    def test_reset_autosave_button_clears_draft_and_cached_fields(self):
        section = self.fill_required_fields()
        self.window.performer_input.setText("IM")
        self.window.sql_input.setText("select 1")
        self.window.doc_input.setText("doc-1")
        self.window.tax_reference_input.setText("tax-reference-1")
        section.issue_type_combo.setCurrentText("Question")
        section.issue_text.setPlainText("Вопрос в черновике")
        self.window.set_hero_collapsed(True)
        self.window.add_section()
        self.window.sections[1].title_input.setText("Лишний раздел")
        self.app.processEvents()

        cache_path = Path(self.window._session_cache_path)
        self.assertTrue(cache_path.exists())

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes) as question_mock:
            self.window.reset_cache_btn.click()
        self.app.processEvents()

        question_mock.assert_called_once()
        self.assertEqual(self.window.build_input.text(), "")
        self.assertEqual(self.window.database_input.text(), "")
        self.assertEqual(self.window.sir_input.text(), "")
        self.assertEqual(self.window.performer_input.text(), "")
        self.assertEqual(self.window.sql_input.text(), "")
        self.assertEqual(self.window.doc_input.text(), "")
        self.assertEqual(self.window.tax_reference_input.text(), "")
        self.assertFalse(self.window.hero_panel.isHidden())
        self.assertTrue(self.window.sql_check.isChecked())
        self.assertTrue(self.window.doc_check.isChecked())
        self.assertTrue(self.window.tax_reference_check.isChecked())
        self.assertEqual(len(self.window.sections), 1)
        self.assertEqual(self.window.sections[0].title_input.text(), "")
        self.assertEqual(self.window.sections[0].issue_text.toPlainText(), "")
        self.assertEqual(self.window.sections[0].issue_type_combo.currentText(), "Error")

        restored = ReportsWindow({"general": {"reports_dir": self.temp_dir.name}}, "")
        try:
            self.assertEqual(restored.build_input.text(), "")
            self.assertEqual(restored.database_input.text(), "")
            self.assertEqual(restored.sir_input.text(), "")
            self.assertEqual(restored.performer_input.text(), "")
            self.assertEqual(restored.sections[0].title_input.text(), "")
            self.assertEqual(restored.sections[0].issue_text.toPlainText(), "")
        finally:
            restored.close()
            restored.deleteLater()
            self.app.processEvents()

    def test_reset_autosave_cancel_keeps_draft(self):
        self.fill_required_fields()
        self.app.processEvents()

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No):
            self.window.reset_cache_btn.click()
        self.app.processEvents()

        self.assertEqual(self.window.build_input.text(), "5917")
        self.assertEqual(self.window.sections[0].issue_text.toPlainText(), "Ошибка в тексте")

    def test_sql_doc_and_tax_reference_affect_completion_when_enabled_by_default(self):
        self.fill_required_fields()
        self.app.processEvents()
        self.assertLess(self.window.completion_bar.value(), 100)

        self.window.sql_input.setText("select 1")
        self.assertLess(self.window.completion_bar.value(), 100)

        self.window.doc_input.setText("doc-1")
        self.assertLess(self.window.completion_bar.value(), 100)

        self.window.tax_reference_input.setText("tax-reference-1")
        self.app.processEvents()
        self.assertEqual(self.window.completion_bar.value(), 100)

    def test_last_section_cannot_be_removed(self):
        with patch.object(QMessageBox, "information", return_value=QMessageBox.StandardButton.Ok) as info_mock:
            self.window.remove_last_section()
        info_mock.assert_called_once()
        self.assertEqual(len(self.window.sections), 1)

    def test_continue_editing_stops_save_when_validation_fails(self):
        self.window.sir_input.setText("SIR-2026-001")
        with patch.object(self.window, "confirm_save_with_issues", return_value=False) as confirm_mock:
            self.window.save_report()

        confirm_mock.assert_called_once()
        issues = confirm_mock.call_args.args[0]
        self.assertIn("Build", issues)
        self.assertIn("BD", issues)
        self.assertNotIn("SIR", issues)
        self.assertIn("SQL", issues)
        self.assertIn("DOC", issues)
        self.assertIn("Tax Referens", issues)
        self.assertIn("Раздел #1: Название", issues)
        self.assertEqual(list(Path(self.temp_dir.name).glob("*.txt")), [])

    def test_save_report_requires_sir_before_validation_dialog(self):
        with (
            patch.object(self.window, "confirm_save_with_issues", return_value=True) as confirm_mock,
            patch.object(QMessageBox, "warning", return_value=QMessageBox.StandardButton.Ok) as warning_mock,
        ):
            self.window.save_report()

        confirm_mock.assert_not_called()
        warning_mock.assert_called_once()
        self.assertEqual(list(Path(self.temp_dir.name).glob("*.txt")), [])

    def test_load_report_from_file_restores_saved_fields(self):
        report_path = Path(self.temp_dir.name) / "2026-04-21_16-30-SIR-2026-777.txt"
        report_path.write_text(
            "\n".join(
                [
                    "Build 6328",
                    "BD - Demo",
                    "SQL - select 1",
                    "DOC - doc-1",
                    "Tax Referens - tax-reference-1",
                    "",
                    "# 1 - Loaded title",
                    "Pre-Condition:",
                    "pre line",
                    "",
                    "Scenario:",
                    "step line",
                    "",
                    "Question: issue line attachment:SIR-2026-777_QA_01.jpg",
                ]
            ),
            encoding="utf-8",
        )

        self.window.load_report_from_file(str(report_path))
        self.app.processEvents()

        section = self.window.sections[0]
        self.assertEqual(self.window.build_input.text(), "6328")
        self.assertEqual(self.window.database_input.text(), "Demo")
        self.assertEqual(self.window.sir_input.text(), "SIR-2026-777")
        self.assertEqual(self.window.performer_input.text(), "QA")
        self.assertEqual(self.window.sql_input.text(), "select 1")
        self.assertEqual(self.window.doc_input.text(), "doc-1")
        self.assertEqual(self.window.tax_reference_input.text(), "tax-reference-1")
        self.assertEqual(section.title_input.text(), "Loaded title")
        self.assertEqual(section.pre_text.toPlainText(), "pre line")
        self.assertEqual(section.scenario_text.toPlainText(), "step line")
        self.assertEqual(section.issue_type_combo.currentText(), "Question")
        self.assertEqual(section.issue_text.toPlainText(), "issue line attachment:SIR-2026-777_QA_01.jpg")

    def test_force_save_writes_txt_even_with_missing_fields(self):
        self.window.sir_input.setText("SIR-ONLY")
        with (
            patch.object(self.window, "confirm_save_with_issues", return_value=True) as confirm_mock,
            patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No),
        ):
            self.window.save_report()

        confirm_mock.assert_called_once()
        files = sorted(Path(self.temp_dir.name).glob("*.txt"))
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.endswith("-SIR-ONLY.txt"))
        content = files[0].read_text(encoding="utf-8")
        self.assertIn("Build ", content)
        self.assertIn("BD - ", content)
        self.assertNotIn("SIR - ", content)
        self.assertIn("SQL - ", content)
        self.assertIn("DOC - ", content)
        self.assertIn("Tax Referens - ", content)

    def test_save_report_creates_txt_without_validation_dialog_when_filled(self):
        self.fill_required_fields()
        self.window.sql_input.setText("select 1")
        self.window.doc_input.setText("doc-1")
        self.window.tax_reference_input.setText("tax-reference-1")
        self.app.processEvents()
        with (
            patch.object(self.window, "confirm_save_with_issues", return_value=True) as confirm_mock,
            patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No),
        ):
            self.window.save_report()

        confirm_mock.assert_not_called()
        files = sorted(Path(self.temp_dir.name).glob("*.txt"))
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.endswith("-SIR-2026-001.txt"))
        content = files[0].read_text(encoding="utf-8")
        self.assertNotIn("SIR - SIR-2026-001", content)
        self.assertIn("SQL - select 1", content)
        self.assertIn("DOC - doc-1", content)
        self.assertIn("Tax Referens - tax-reference-1", content)
        self.assertIn("# 1 - Проверка отчета", content)


if __name__ == "__main__":
    unittest.main()
