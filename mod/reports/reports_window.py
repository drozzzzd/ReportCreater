"""
Главное окно конструктора отчетов.
"""
from __future__ import annotations

import os
import re
import json
from datetime import datetime

from PyQt6.QtCore import QAbstractAnimation, QEasingCurve, QPropertyAnimation, Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QTextOption
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .flow_layout import FlowLayout
from .report_section_widget import ReportSectionWidget
from .report_utils import (
    get_project_root,
    install_clearable_context_menu,
    load_mode_icons,
    set_invalid_state,
)
from .text_report_builder import ReportMetadata, ReportSectionData, TextReportBuilder, TextReportParser


class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scroll_target = 0
        self._scroll_animation = QPropertyAnimation(self.verticalScrollBar(), b"value", self)
        self._scroll_animation.setDuration(180)
        self._scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.verticalScrollBar().setSingleStep(24)

    def wheelEvent(self, event):
        pixel_delta = event.pixelDelta().y()
        angle_delta = event.angleDelta().y()
        if pixel_delta == 0 and angle_delta == 0:
            super().wheelEvent(event)
            return

        bar = self.verticalScrollBar()
        if self._scroll_animation.state() == QAbstractAnimation.State.Running:
            base_target = self._scroll_target
        else:
            base_target = bar.value()

        if pixel_delta:
            distance = -pixel_delta
        else:
            distance = int(-(angle_delta / 120) * 72)

        self._scroll_target = max(bar.minimum(), min(bar.maximum(), base_target + distance))
        self._scroll_animation.stop()
        self._scroll_animation.setStartValue(bar.value())
        self._scroll_animation.setEndValue(self._scroll_target)
        self._scroll_animation.start()
        event.accept()


class ValidationIssuesDialog(QDialog):
    def __init__(self, issues: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Не все поля заполнены")
        self.setModal(True)
        self.resize(540, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Перед сохранением найдены незаполненные или некорректные поля:")
        title.setWordWrap(True)
        layout.addWidget(title)

        issues_box = QPlainTextEdit()
        issues_box.setReadOnly(True)
        issues_box.setPlainText("\n".join(f"- {issue}" for issue in issues))
        layout.addWidget(issues_box, 1)

        hint = QLabel("Можно вернуться к редактированию или сохранить отчет в текущем виде.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QHBoxLayout()
        buttons.addStretch()

        continue_btn = QPushButton("Продолжить редактирование")
        continue_btn.clicked.connect(self.reject)
        buttons.addWidget(continue_btn)

        save_anyway_btn = QPushButton("Все равно сохранить")
        save_anyway_btn.setObjectName("saveBtn")
        save_anyway_btn.clicked.connect(self.accept)
        buttons.addWidget(save_anyway_btn)

        layout.addLayout(buttons)


class ReportsWindow(QWidget):
    SESSION_CACHE_VERSION = 1

    def __init__(self, config: dict, config_path: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("ReportsWindow")
        self.config = config
        self.config_path = config_path
        self.mode_icons = load_mode_icons()
        self.sections: list[ReportSectionWidget] = []
        self._attachment_counters: dict[tuple[str, str], int] = {}
        self._base_stylesheet = ""
        self._dense_mode: bool | None = None
        self._hero_collapsed = False
        self._meta_collapsed = False
        self._session_cache_enabled = False
        self._session_cache_path = self.get_session_cache_path()

        self.setWindowTitle("Конструктор отчетов")
        self.resize(1120, 760)
        self.setMinimumSize(780, 560)

        self._load_styles()
        self._build_ui()
        self._connect_live_updates()
        self.add_section()
        self.restore_session_cache()
        self._session_cache_enabled = True
        self.refresh_live_state()

    def _load_styles(self):
        style_path = os.path.join(get_project_root(), "styles", "reports_window.qss")
        if not os.path.exists(style_path):
            return
        with open(style_path, "r", encoding="utf-8") as file:
            self._base_stylesheet = file.read()
        self.setStyleSheet(self._base_stylesheet)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self.main_tabs = QTabWidget()
        self.main_tabs.setObjectName("mainTabs")
        root.addWidget(self.main_tabs, 1)

        self.setup_tab = QWidget()
        self.setup_tab.setObjectName("setupTab")
        setup_layout = QVBoxLayout(self.setup_tab)
        setup_layout.setContentsMargins(0, 0, 0, 0)
        setup_layout.setSpacing(8)

        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setObjectName("setupScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        setup_layout.addWidget(self.scroll_area, 1)

        self.workflow_content = QWidget()
        self.workflow_content.setObjectName("setupScrollContent")
        self.scroll_area.setWidget(self.workflow_content)
        workflow_content_layout = QVBoxLayout(self.workflow_content)
        workflow_content_layout.setContentsMargins(0, 0, 0, 0)
        workflow_content_layout.setSpacing(8)

        self.main_tabs.addTab(self.setup_tab, "Конструктор отчетов")

        self.fill_tab = QWidget()
        self.fill_tab.setObjectName("fillTab")
        fill_layout = QVBoxLayout(self.fill_tab)
        fill_layout.setContentsMargins(0, 0, 0, 0)
        fill_layout.setSpacing(8)

        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_splitter.setObjectName("mainContentSplitter")
        self.content_splitter.setChildrenCollapsible(True)
        self.content_splitter.setHandleWidth(10)
        fill_layout.addWidget(self.content_splitter, 1)

        self.sections_panel = QWidget()
        self.sections_panel.setObjectName("sectionsPanel")
        self.sections_panel.setMinimumWidth(420)
        sections_panel_layout = QVBoxLayout(self.sections_panel)
        sections_panel_layout.setContentsMargins(0, 0, 0, 0)
        sections_panel_layout.setSpacing(8)
        self.workflow_panel = self.sections_panel

        self.side_panel = QWidget()
        self.side_panel.setObjectName("sidePanel")
        self.side_panel.setMinimumWidth(300)
        side_layout = QVBoxLayout(self.side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(8)

        top_panel = QHBoxLayout()
        top_panel.setSpacing(10)

        actions_host = QWidget()
        actions_host.setObjectName("topActionsHost")
        actions_layout = FlowLayout(actions_host, spacing=6)

        self.add_btn = QPushButton("+ Раздел")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self.add_section)

        self.remove_last_btn = QPushButton("- Последний")
        self.remove_last_btn.setProperty("buttonType", "secondary")
        self.remove_last_btn.clicked.connect(self.remove_last_section)

        self.save_btn = QPushButton("Сохранить отчет")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.clicked.connect(self.save_report)

        self.open_report_btn = QPushButton("Открыть отчет")
        self.open_report_btn.setProperty("buttonType", "secondary")
        self.open_report_btn.clicked.connect(self.select_report_file)

        self.reset_cache_btn = QPushButton("Сброс черновика")
        self.reset_cache_btn.setObjectName("resetCacheBtn")
        self.reset_cache_btn.clicked.connect(lambda: self.reset_autosave_draft())

        self.sections_label = QLabel("Разделов: 0")
        self.sections_label.setObjectName("summaryLabel")
        self.sections_label.setProperty("summaryBadge", "true")

        self.hero_collapse_btn = QPushButton("Свернуть")
        self.hero_collapse_btn.setProperty("buttonType", "secondary")
        self.hero_collapse_btn.setFixedHeight(32)
        self.hero_collapse_btn.clicked.connect(lambda: self.set_hero_collapsed(True))

        for button in (self.add_btn, self.remove_last_btn, self.save_btn, self.open_report_btn):
            button.setMinimumHeight(32)
            actions_layout.addWidget(button)
        self.reset_cache_btn.setMinimumHeight(32)

        self.hero_panel = QFrame()
        self.hero_panel.setObjectName("heroPanel")
        hero_layout = QHBoxLayout(self.hero_panel)
        hero_layout.setContentsMargins(12, 10, 12, 10)
        hero_layout.setSpacing(10)

        hero_copy = QVBoxLayout()
        hero_copy.setSpacing(2)
        hero_copy.setContentsMargins(0, 0, 0, 0)

        hero_title = QLabel("Конструктор отчетов")
        hero_title.setObjectName("heroTitle")
        hero_copy.addWidget(hero_title)

        hero_subtitle = QLabel("Собирайте шаги, проверяйте результат вживую и сохраняйте готовый TXT без лишней ручной правки.")
        hero_subtitle.setObjectName("heroSubtitle")
        hero_subtitle.setWordWrap(True)
        hero_copy.addWidget(hero_subtitle)

        hero_layout.addLayout(hero_copy, 1)
        top_panel.addWidget(actions_host, 1)
        top_panel.addWidget(self.sections_label, 0, Qt.AlignmentFlag.AlignTop)
        top_panel.addWidget(self.reset_cache_btn, 0, Qt.AlignmentFlag.AlignTop)
        top_panel.addWidget(self.hero_collapse_btn, 0, Qt.AlignmentFlag.AlignTop)
        hero_layout.addLayout(top_panel, 1)
        workflow_content_layout.addWidget(self.hero_panel)

        self.hero_collapsed_bar = QFrame()
        self.hero_collapsed_bar.setObjectName("heroCollapsedBar")
        self.hero_collapsed_bar.setVisible(False)
        hero_collapsed_layout = QHBoxLayout(self.hero_collapsed_bar)
        hero_collapsed_layout.setContentsMargins(10, 6, 10, 6)
        hero_collapsed_layout.setSpacing(8)

        self.hero_collapsed_title = QLabel("Конструктор отчетов скрыт")
        self.hero_collapsed_title.setObjectName("heroCollapsedTitle")
        self.hero_collapsed_title.setWordWrap(True)
        hero_collapsed_layout.addWidget(self.hero_collapsed_title, 1)

        self.hero_expand_btn = QPushButton("Развернуть")
        self.hero_expand_btn.setProperty("buttonType", "secondary")
        self.hero_expand_btn.setFixedHeight(24)
        self.hero_expand_btn.clicked.connect(lambda: self.set_hero_collapsed(False))
        hero_collapsed_layout.addWidget(self.hero_expand_btn)
        workflow_content_layout.addWidget(self.hero_collapsed_bar)

        self.meta_group = QGroupBox("Параметры отчета")
        self.meta_group.setObjectName("metaGroup")
        meta_layout = QFormLayout(self.meta_group)
        meta_layout.setSpacing(4)
        meta_layout.setHorizontalSpacing(8)
        meta_layout.setVerticalSpacing(4)
        meta_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        meta_layout.setContentsMargins(10, 8, 10, 8)

        meta_actions = QHBoxLayout()
        meta_actions.setContentsMargins(0, 0, 0, 0)
        meta_actions.addStretch()
        self.meta_collapse_btn = QPushButton("Свернуть")
        self.meta_collapse_btn.setProperty("buttonType", "secondary")
        self.meta_collapse_btn.setFixedHeight(24)
        self.meta_collapse_btn.clicked.connect(lambda: self.set_meta_collapsed(True))
        meta_actions.addWidget(self.meta_collapse_btn)

        self.build_input = QLineEdit()
        self.build_input.setPlaceholderText("Введите build")
        self.build_input.setFixedHeight(24)
        self.database_input = QLineEdit()
        self.database_input.setPlaceholderText("Введите BD")
        self.database_input.setFixedHeight(24)
        self.sir_input = QLineEdit()
        self.sir_input.setPlaceholderText("Введите SIR")
        self.sir_input.setFixedHeight(24)
        self.performer_input = QLineEdit()
        self.performer_input.setPlaceholderText("Введите исполнителя")
        self.performer_input.setFixedHeight(24)

        self.sql_check = QCheckBox("Добавить строку SQL")
        self.sql_check.setChecked(True)
        self.sql_input = QLineEdit()
        self.sql_input.setPlaceholderText("Введите SQL")
        self.sql_input.setEnabled(True)
        self.sql_input.setFixedHeight(24)

        self.doc_check = QCheckBox("Добавить строку DOC")
        self.doc_check.setChecked(True)
        self.doc_input = QLineEdit()
        self.doc_input.setPlaceholderText("Введите DOC")
        self.doc_input.setEnabled(True)
        self.doc_input.setFixedHeight(24)

        self.tax_reference_check = QCheckBox("Добавить Tax Referens")
        self.tax_reference_check.setChecked(True)
        self.tax_reference_input = QLineEdit()
        self.tax_reference_input.setPlaceholderText("Введите Tax Referens")
        self.tax_reference_input.setEnabled(True)
        self.tax_reference_input.setFixedHeight(24)

        path_row = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setReadOnly(True)
        self.output_dir_input.setText(self.get_output_dir())
        self.output_dir_input.setFixedHeight(24)
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(34)
        browse_btn.setFixedHeight(24)
        browse_btn.clicked.connect(self.select_output_dir)
        path_row.addWidget(self.output_dir_input)
        path_row.addWidget(browse_btn)

        report_fields_label = QLabel("Поля отчета")
        report_fields_label.setObjectName("metaSectionLabel")
        service_fields_label = QLabel("Служебные поля для вложений")
        service_fields_label.setObjectName("metaSectionLabel")
        self.next_attachment_label = QLabel("attachment:")
        self.next_attachment_label.setObjectName("attachmentPreviewLabel")
        self.next_attachment_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        meta_layout.addRow(meta_actions)
        meta_layout.addRow(report_fields_label)
        meta_layout.addRow("Build:", self.build_input)
        meta_layout.addRow("BD:", self.database_input)
        meta_layout.addRow(self.sql_check, self.sql_input)
        meta_layout.addRow(self.doc_check, self.doc_input)
        meta_layout.addRow(self.tax_reference_check, self.tax_reference_input)
        meta_layout.addRow("Папка сохранения:", path_row)
        meta_layout.addRow(service_fields_label)
        meta_layout.addRow("SIR:", self.sir_input)
        meta_layout.addRow("Исполнитель:", self.performer_input)
        meta_layout.addRow("Следующее вложение:", self.next_attachment_label)
        workflow_content_layout.addWidget(self.meta_group)

        self.meta_collapsed_bar = QFrame()
        self.meta_collapsed_bar.setObjectName("metaCollapsedBar")
        self.meta_collapsed_bar.setVisible(False)
        collapsed_layout = QHBoxLayout(self.meta_collapsed_bar)
        collapsed_layout.setContentsMargins(10, 6, 10, 6)
        collapsed_layout.setSpacing(8)

        self.meta_collapsed_title = QLabel("Параметры отчета скрыты")
        self.meta_collapsed_title.setObjectName("metaCollapsedTitle")
        self.meta_collapsed_title.setWordWrap(True)
        self.meta_collapsed_title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        collapsed_layout.addWidget(self.meta_collapsed_title, 1)
        collapsed_layout.addStretch()

        self.meta_expand_btn = QPushButton("Развернуть")
        self.meta_expand_btn.setProperty("buttonType", "secondary")
        self.meta_expand_btn.setFixedHeight(24)
        self.meta_expand_btn.clicked.connect(lambda: self.set_meta_collapsed(False))
        collapsed_layout.addWidget(self.meta_expand_btn)
        workflow_content_layout.addWidget(self.meta_collapsed_bar)

        for widget in [
            self.build_input,
            self.database_input,
            self.sir_input,
            self.performer_input,
            self.sql_input,
            self.doc_input,
            self.tax_reference_input,
            self.output_dir_input,
        ]:
            install_clearable_context_menu(widget)

        self.sections_host = QWidget()
        self.sections_layout = QVBoxLayout(self.sections_host)
        self.sections_layout.setContentsMargins(0, 0, 0, 0)
        self.sections_layout.setSpacing(10)
        self.sections_layout.addStretch()

        self.sections_scroll_area = SmoothScrollArea()
        self.sections_scroll_area.setObjectName("sectionsScrollArea")
        self.sections_scroll_area.setWidgetResizable(True)
        self.sections_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.sections_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sections_scroll_area.setWidget(self.sections_host)
        sections_panel_layout.addWidget(self.sections_scroll_area, 1)

        self.preview_shell = QFrame()
        self.preview_shell.setObjectName("previewShell")
        self.preview_shell.setMinimumWidth(320)
        preview_shell_layout = QVBoxLayout(self.preview_shell)
        preview_shell_layout.setContentsMargins(12, 12, 12, 12)
        preview_shell_layout.setSpacing(10)

        preview_bar = QFrame()
        preview_bar.setObjectName("previewWindowBar")
        preview_bar_layout = QHBoxLayout(preview_bar)
        preview_bar_layout.setContentsMargins(12, 10, 12, 10)
        preview_bar_layout.setSpacing(8)

        preview_title = QLabel("Предпросмотр отчета")
        preview_title.setObjectName("previewWindowTitle")
        preview_bar_layout.addWidget(preview_title)
        preview_bar_layout.addStretch()

        preview_state = QLabel("обновляется автоматически")
        preview_state.setObjectName("previewWindowState")
        preview_bar_layout.addWidget(preview_state)

        preview_shell_layout.addWidget(preview_bar)

        self.preview_panel = QFrame()
        self.preview_panel.setObjectName("previewPanel")
        preview_layout = QVBoxLayout(self.preview_panel)
        preview_layout.setContentsMargins(14, 14, 14, 14)
        preview_layout.setSpacing(8)

        preview_hint = QLabel("Здесь в реальном времени отображается весь текст отчета, который будет сохранен в TXT.")
        preview_hint.setWordWrap(True)
        preview_hint.setObjectName("previewHintLabel")
        preview_layout.addWidget(preview_hint)

        self.preview_text = QPlainTextEdit()
        self.preview_text.setObjectName("previewEditor")
        self.preview_text.setReadOnly(True)
        self.preview_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.preview_text.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.preview_text.setPlaceholderText("Предпросмотр отчета появится здесь автоматически.")
        preview_layout.addWidget(self.preview_text, 1)

        preview_shell_layout.addWidget(self.preview_panel, 1)
        side_layout.addWidget(self.preview_shell, 1)

        progress_group = QGroupBox("Заполненность отчета")
        progress_group.setObjectName("progressPanel")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setContentsMargins(12, 10, 12, 10)
        progress_layout.setSpacing(6)

        self.completion_label = QLabel("Заполненность: 0%")
        self.completion_label.setObjectName("summaryLabel")
        progress_layout.addWidget(self.completion_label)

        self.completion_bar = QProgressBar()
        self.completion_bar.setRange(0, 100)
        self.completion_bar.setValue(0)
        self.completion_bar.setTextVisible(True)
        progress_layout.addWidget(self.completion_bar)

        self.completion_hint = QLabel("Шкала растет по мере заполнения всех обязательных полей отчета.")
        self.completion_hint.setWordWrap(True)
        self.completion_hint.setObjectName("previewHintLabel")
        progress_layout.addWidget(self.completion_hint)

        self.progress_shell = QFrame()
        self.progress_shell.setObjectName("progressShell")
        self.progress_shell.setMinimumHeight(126)
        progress_shell_layout = QVBoxLayout(self.progress_shell)
        progress_shell_layout.setContentsMargins(10, 10, 10, 10)
        progress_shell_layout.setSpacing(8)
        progress_shell_layout.addWidget(progress_group)
        side_layout.addWidget(self.progress_shell, 0)

        self.content_splitter.addWidget(self.sections_panel)
        self.content_splitter.addWidget(self.side_panel)
        self.content_splitter.setStretchFactor(0, 3)
        self.content_splitter.setStretchFactor(1, 2)
        self.content_splitter.setSizes([910, 390])
        self.main_tabs.addTab(self.fill_tab, "Заполнение ошибок и предпросмотр")

        self._update_responsive_layout(force=True)

    def _connect_live_updates(self):
        line_edits = [
            self.build_input,
            self.database_input,
            self.sir_input,
            self.performer_input,
            self.sql_input,
            self.doc_input,
            self.tax_reference_input,
            self.output_dir_input,
        ]
        for widget in line_edits:
            widget.textChanged.connect(lambda *_: self.refresh_live_state())

        self.sql_check.toggled.connect(self._handle_sql_toggle)
        self.doc_check.toggled.connect(self._handle_doc_toggle)
        self.tax_reference_check.toggled.connect(self._handle_tax_reference_toggle)

    def _handle_sql_toggle(self, checked: bool):
        self.sql_input.setEnabled(checked)
        self.refresh_live_state()

    def _handle_doc_toggle(self, checked: bool):
        self.doc_input.setEnabled(checked)
        self.refresh_live_state()

    def _handle_tax_reference_toggle(self, checked: bool):
        self.tax_reference_input.setEnabled(checked)
        self.refresh_live_state()

    def set_hero_collapsed(self, collapsed: bool):
        self._hero_collapsed = collapsed
        self.hero_panel.setVisible(not collapsed)
        self.hero_collapsed_bar.setVisible(collapsed)
        self.scroll_area.updateGeometry()
        self.refresh_live_state()

    def set_meta_collapsed(self, collapsed: bool):
        self._meta_collapsed = collapsed
        self.meta_group.setVisible(not collapsed)
        self.meta_collapsed_bar.setVisible(collapsed)
        self.scroll_area.updateGeometry()
        self.refresh_live_state()

    def get_output_dir(self) -> str:
        general_config = self.config.get("general", {})
        base_dir = general_config.get("reports_dir", "reports")
        if not os.path.isabs(base_dir):
            base_dir = os.path.join(get_project_root(), base_dir)
        return os.path.join(base_dir, "text_reports")

    def get_session_cache_path(self) -> str:
        general_config = self.config.get("general", {})
        cache_path = general_config.get("session_cache_path")
        if cache_path:
            if not os.path.isabs(cache_path):
                cache_path = os.path.join(get_project_root(), cache_path)
            return cache_path

        base_dir = general_config.get("reports_dir", "reports")
        if not os.path.isabs(base_dir):
            base_dir = os.path.join(get_project_root(), base_dir)
        return os.path.join(base_dir, ".report_builder_session_cache.json")

    def select_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения отчетов")
        if folder:
            self.output_dir_input.setText(folder)

    def select_report_file(self):
        folder = self.output_dir_input.text().strip() or self.get_output_dir()
        os.makedirs(folder, exist_ok=True)
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть отчет",
            folder,
            "Текстовые отчеты (*.txt);;Все файлы (*)",
        )
        if filepath:
            self.load_report_from_file(filepath)

    def load_report_from_file(self, filepath: str):
        try:
            metadata, sections = TextReportParser().parse_file(filepath)
        except OSError as error:
            QMessageBox.warning(self, "Не удалось открыть отчет", str(error))
            return

        self.apply_loaded_report(metadata, sections)

    def apply_loaded_report(self, metadata: ReportMetadata, sections: list[ReportSectionData]):
        was_enabled = self._session_cache_enabled
        self._session_cache_enabled = False
        try:
            self.build_input.setText(metadata.build)
            self.database_input.setText(metadata.database)
            self.sir_input.setText(metadata.sir)
            self.performer_input.setText(metadata.performer)
            self.sql_check.setChecked(metadata.include_sql)
            self.sql_input.setText(metadata.sql_value)
            self.doc_check.setChecked(metadata.include_doc)
            self.doc_input.setText(metadata.doc_value)
            self.tax_reference_check.setChecked(metadata.include_tax_reference)
            self.tax_reference_input.setText(metadata.tax_reference_value)

            desired_count = max(1, len(sections))
            while len(self.sections) < desired_count:
                self.add_section()
            while len(self.sections) > desired_count and len(self.sections) > 1:
                section = self.sections.pop()
                self.sections_layout.removeWidget(section)
                section.deleteLater()
            self.renumber_sections()

            if not sections:
                sections = [
                    ReportSectionData(
                        number="1",
                        title="",
                        precondition="",
                        scenario="",
                        issue_type="Error",
                        issue_text="",
                    )
                ]

            for section, data in zip(self.sections, sections):
                section.set_section_number(data.number, overwrite=True)
                section.title_input.setText(data.title)
                section.pre_text.setPlainText(data.precondition)
                section.scenario_text.setPlainText(data.scenario)
                if section.issue_type_combo.findText(data.issue_type) >= 0:
                    section.issue_type_combo.setCurrentText(data.issue_type)
                else:
                    section.issue_type_combo.setCurrentText("Error")
                section.issue_text.setPlainText(data.issue_text)
        finally:
            self._session_cache_enabled = was_enabled

        self._attachment_counters = {}
        self._sync_attachment_counters_from_content()
        self.refresh_live_state()

    def add_section(self):
        section = ReportSectionWidget(
            section_number=len(self.sections) + 1,
            attachment_provider=self.build_attachment_text,
            tax_reference_provider=self.build_tax_reference_menu_prefix,
            mode_icons=self.mode_icons,
        )
        section.remove_requested.connect(self.remove_section)
        section.content_changed.connect(self.refresh_live_state)
        self.sections.append(section)
        self.sections_layout.insertWidget(self.sections_layout.count() - 1, section)
        if self._dense_mode is not None:
            section.set_ui_density(self._dense_mode)
        self.renumber_sections()
        self.refresh_live_state()

    def remove_last_section(self):
        if self.sections:
            self.remove_section(self.sections[-1])

    def remove_section(self, section: ReportSectionWidget):
        if len(self.sections) == 1:
            QMessageBox.information(self, "Информация", "В окне должен остаться хотя бы один раздел.")
            return

        if section in self.sections:
            self.sections.remove(section)
            section.deleteLater()
            self.renumber_sections()
            self.refresh_live_state()

    def renumber_sections(self):
        for index, section in enumerate(self.sections, start=1):
            section.set_section_number(index)
        self.sections_label.setText(f"Разделов: {len(self.sections)}")

    def collect_metadata(self) -> ReportMetadata:
        return ReportMetadata(
            build=self.build_input.text().strip(),
            database=self.database_input.text().strip(),
            sir=self.sir_input.text().strip(),
            performer=self.performer_input.text().strip(),
            include_sql=self.sql_check.isChecked(),
            sql_value=self.sql_input.text().strip(),
            include_doc=self.doc_check.isChecked(),
            doc_value=self.doc_input.text().strip(),
            include_tax_reference=self.tax_reference_check.isChecked(),
            tax_reference_value=self.tax_reference_input.text().strip(),
        )

    def collect_sections(self):
        return [section.get_section_data() for section in self.sections]

    def build_session_cache_payload(self) -> dict:
        metadata = self.collect_metadata()
        return {
            "version": self.SESSION_CACHE_VERSION,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "hero_collapsed": self._hero_collapsed,
            "meta_collapsed": self._meta_collapsed,
            "metadata": {
                "build": metadata.build,
                "database": metadata.database,
                "sir": metadata.sir,
                "performer": metadata.performer,
                "include_sql": metadata.include_sql,
                "sql_value": metadata.sql_value,
                "include_doc": metadata.include_doc,
                "doc_value": metadata.doc_value,
                "include_tax_reference": metadata.include_tax_reference,
                "tax_reference_value": metadata.tax_reference_value,
            },
            "output_dir": self.output_dir_input.text().strip(),
            "sections": [
                {
                    "number": section.number,
                    "title": section.title,
                    "precondition": section.precondition,
                    "scenario": section.scenario,
                    "issue_type": section.issue_type,
                    "issue_text": section.issue_text,
                }
                for section in self.collect_sections()
            ],
            "attachment_counters": [
                {
                    "sir": sir,
                    "performer": performer,
                    "index": index,
                }
                for (sir, performer), index in self._attachment_counters.items()
            ],
        }

    def save_session_cache(self):
        if not self._session_cache_enabled:
            return

        try:
            os.makedirs(os.path.dirname(self._session_cache_path), exist_ok=True)
            temp_path = f"{self._session_cache_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(self.build_session_cache_payload(), file, ensure_ascii=False, indent=2)
            os.replace(temp_path, self._session_cache_path)
        except OSError:
            return

    def reset_autosave_draft(self, confirm: bool = True):
        if confirm:
            reply = QMessageBox.question(
                self,
                "Сбросить черновик?",
                "Очистить autosave-кеш и все заполненные поля текущего черновика?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        was_enabled = self._session_cache_enabled
        self._session_cache_enabled = False
        try:
            for path in (self._session_cache_path, f"{self._session_cache_path}.tmp"):
                try:
                    os.remove(path)
                except FileNotFoundError:
                    pass
                except OSError:
                    pass

            self._attachment_counters = {}
            self.build_input.clear()
            self.database_input.clear()
            self.sir_input.clear()
            self.performer_input.clear()
            self.sql_check.setChecked(True)
            self.sql_input.clear()
            self.doc_check.setChecked(True)
            self.doc_input.clear()
            self.tax_reference_check.setChecked(True)
            self.tax_reference_input.clear()

            while len(self.sections) > 1:
                section = self.sections.pop()
                self.sections_layout.removeWidget(section)
                section.deleteLater()

            if self.sections:
                section = self.sections[0]
                section.number_input.clear()
                section.title_input.clear()
                section.pre_text.clear()
                section.scenario_text.clear()
                section.issue_type_combo.setCurrentText("Error")
                section.issue_text.clear()

            self.renumber_sections()
            self.set_hero_collapsed(False)
            self.set_meta_collapsed(False)
        finally:
            self._session_cache_enabled = was_enabled

        self.refresh_live_state()

    def restore_session_cache(self):
        if not os.path.exists(self._session_cache_path):
            return

        try:
            with open(self._session_cache_path, "r", encoding="utf-8") as file:
                cache = json.load(file)
        except (OSError, json.JSONDecodeError):
            return

        if not isinstance(cache, dict):
            return

        metadata = cache.get("metadata", {})
        if isinstance(metadata, dict):
            self.build_input.setText(str(metadata.get("build", "")))
            self.database_input.setText(str(metadata.get("database", "")))
            self.sir_input.setText(str(metadata.get("sir", "")))
            self.performer_input.setText(str(metadata.get("performer", "")))
            self.sql_check.setChecked(bool(metadata.get("include_sql", self.sql_check.isChecked())))
            self.sql_input.setText(str(metadata.get("sql_value", "")))
            self.doc_check.setChecked(bool(metadata.get("include_doc", self.doc_check.isChecked())))
            self.doc_input.setText(str(metadata.get("doc_value", "")))
            self.tax_reference_check.setChecked(
                bool(metadata.get("include_tax_reference", self.tax_reference_check.isChecked()))
            )
            self.tax_reference_input.setText(str(metadata.get("tax_reference_value", "")))

        output_dir = cache.get("output_dir")
        if isinstance(output_dir, str) and output_dir.strip():
            self.output_dir_input.setText(output_dir.strip())

        sections = cache.get("sections", [])
        if isinstance(sections, list):
            desired_count = max(1, len(sections))
            while len(self.sections) < desired_count:
                self.add_section()
            while len(self.sections) > desired_count and len(self.sections) > 1:
                section = self.sections.pop()
                section.deleteLater()
            self.renumber_sections()

            for section, section_cache in zip(self.sections, sections):
                if not isinstance(section_cache, dict):
                    continue
                number_value = str(section_cache.get("number", "")).strip()
                section.set_section_number(number_value or section.section_number, overwrite=True)
                section.title_input.setText(str(section_cache.get("title", "")))
                section.pre_text.setPlainText(str(section_cache.get("precondition", "")))
                section.scenario_text.setPlainText(str(section_cache.get("scenario", "")))
                issue_type = str(section_cache.get("issue_type", "Error"))
                if section.issue_type_combo.findText(issue_type) >= 0:
                    section.issue_type_combo.setCurrentText(issue_type)
                section.issue_text.setPlainText(str(section_cache.get("issue_text", "")))

        self._attachment_counters = {}
        counters = cache.get("attachment_counters", [])
        if isinstance(counters, list):
            for item in counters:
                if not isinstance(item, dict):
                    continue
                try:
                    index = int(item.get("index", 0))
                except (TypeError, ValueError):
                    continue
                if index <= 0:
                    continue
                key = self._attachment_counter_key(str(item.get("sir", "")), str(item.get("performer", "")))
                self._attachment_counters[key] = max(self._attachment_counters.get(key, 0), index)

        self._sync_attachment_counters_from_content()
        self.set_hero_collapsed(bool(cache.get("hero_collapsed", False)))
        self.set_meta_collapsed(bool(cache.get("meta_collapsed", False)))

    def _iter_attachment_values(self):
        attachment_pattern = re.compile(r"attachment:([^\s]+)", re.IGNORECASE)
        for section in self.collect_sections():
            for block in (section.precondition, section.scenario, section.issue_text):
                for line in block.splitlines():
                    for match in attachment_pattern.finditer(line):
                        yield match.group(1).strip()

    @staticmethod
    def _attachment_counter_key(sir: str, performer: str) -> tuple[str, str]:
        return sir.strip().casefold(), performer.strip().casefold()

    def _next_attachment_index(self, sir: str, performer: str) -> int:
        if not sir or not performer:
            return 1

        pattern = re.compile(rf"^{re.escape(sir)}_{re.escape(performer)}_(\d+)\.jpg$", re.IGNORECASE)
        max_index = 0
        for value in self._iter_attachment_values():
            match = pattern.fullmatch(value)
            if match:
                max_index = max(max_index, int(match.group(1)))
        return max_index + 1

    def _sync_attachment_counters_from_content(self):
        metadata = self.collect_metadata()
        if not metadata.sir or not metadata.performer:
            return

        counter_key = self._attachment_counter_key(metadata.sir, metadata.performer)
        existing_index = self._next_attachment_index(metadata.sir, metadata.performer) - 1
        if existing_index > 0:
            self._attachment_counters[counter_key] = max(
                self._attachment_counters.get(counter_key, 0),
                existing_index,
            )

    def build_attachment_text(self) -> str:
        sir = self.sir_input.text().strip()
        performer = self.performer_input.text().strip()
        if not sir:
            return "attachment:"
        if not performer:
            return f"attachment:{sir}"

        counter_key = self._attachment_counter_key(sir, performer)
        existing_index = self._next_attachment_index(sir, performer) - 1
        attachment_index = max(self._attachment_counters.get(counter_key, 0), existing_index) + 1
        self._attachment_counters[counter_key] = attachment_index
        return f"attachment:{sir}_{performer}_{attachment_index:02d}.jpg"

    def build_tax_reference_menu_prefix(self) -> str:
        return self.tax_reference_input.text().strip()

    def preview_attachment_text(self) -> str:
        sir = self.sir_input.text().strip()
        performer = self.performer_input.text().strip()
        if not sir:
            return "attachment:"
        if not performer:
            return f"attachment:{sir}"

        counter_key = self._attachment_counter_key(sir, performer)
        existing_index = self._next_attachment_index(sir, performer) - 1
        attachment_index = max(self._attachment_counters.get(counter_key, 0), existing_index) + 1
        return f"attachment:{sir}_{performer}_{attachment_index:02d}.jpg"

    def build_collapsed_meta_summary(self) -> str:
        metadata = self.collect_metadata()
        build = metadata.build or "Build не указан"
        database = metadata.database or "BD не указана"
        sir = metadata.sir or "SIR не указан"
        performer = metadata.performer or "исполнитель не указан"
        return (
            f"Параметры скрыты: {build} · {database} · "
            f"вложения {sir} / {performer} · следующее {self.preview_attachment_text()}"
        )

    def build_collapsed_hero_summary(self) -> str:
        return f"Конструктор отчетов скрыт · Разделов: {len(self.sections)}"

    def refresh_attachment_hints(self):
        attachment_text = self.preview_attachment_text()
        self.next_attachment_label.setText(attachment_text)
        self.hero_collapsed_title.setText(self.build_collapsed_hero_summary())
        self.meta_collapsed_title.setText(self.build_collapsed_meta_summary())
        for section in self.sections:
            section.set_attachment_hint(attachment_text)

    def _attachment_issues(self, section_number: str, block_name: str, text: str) -> list[str]:
        issues: list[str] = []
        for line in text.splitlines():
            if "attachment:" not in line.lower():
                continue
            _, _, value = line.partition(":")
            if not value.strip():
                issues.append(f"Раздел #{section_number}: {block_name} содержит attachment без значения")
        return issues

    def collect_validation_issues(self) -> list[str]:
        issues: list[str] = []
        metadata = self.collect_metadata()

        top_checks = [
            ("Build", self.build_input, bool(metadata.build)),
            ("BD", self.database_input, bool(metadata.database)),
            ("SIR", self.sir_input, bool(metadata.sir)),
        ]
        if metadata.include_sql:
            top_checks.append(("SQL", self.sql_input, bool(metadata.sql_value)))
        else:
            set_invalid_state(self.sql_input, False)

        if metadata.include_doc:
            top_checks.append(("DOC", self.doc_input, bool(metadata.doc_value)))
        else:
            set_invalid_state(self.doc_input, False)

        if metadata.include_tax_reference:
            top_checks.append(("Tax Referens", self.tax_reference_input, bool(metadata.tax_reference_value)))
        else:
            set_invalid_state(self.tax_reference_input, False)

        for label, widget, is_filled in top_checks:
            set_invalid_state(widget, not is_filled)
            if not is_filled:
                issues.append(label)

        for index, (section, data) in enumerate(zip(self.sections, self.collect_sections()), start=1):
            text_mode = data.is_plain_text_block()
            number_value = str(data.number).strip()
            number_invalid = False if text_mode else not number_value.isdigit()
            section_label = f"Раздел #{number_value}" if number_value else f"Раздел {index}"
            title_invalid = False if text_mode else not data.title
            precondition_invalid = False if text_mode else not data.precondition
            scenario_invalid = False if text_mode else not data.scenario
            issue_invalid = not data.issue_text

            section.set_validation_state(
                number_invalid=number_invalid,
                title_invalid=title_invalid,
                precondition_invalid=precondition_invalid,
                scenario_invalid=scenario_invalid,
                issue_invalid=issue_invalid,
            )

            if number_invalid:
                issues.append(f"{section_label}: Номер ошибки")
            if title_invalid:
                issues.append(f"{section_label}: Название")
            if precondition_invalid:
                issues.append(f"{section_label}: Предусловия")
            if scenario_invalid:
                issues.append(f"{section_label}: Сценарий")
            if issue_invalid:
                issues.append(f"{section_label}: Ошибка / вопрос / текст")

            if not text_mode:
                issues.extend(self._attachment_issues(data.number, "Предусловия", data.precondition))
                issues.extend(self._attachment_issues(data.number, "Сценарий", data.scenario))
            issues.extend(self._attachment_issues(data.number, "Ошибка / вопрос / текст", data.issue_text))

        return issues

    def calculate_completion(self) -> int:
        metadata = self.collect_metadata()
        filled = 0
        total = 0

        checks = [bool(metadata.build), bool(metadata.database), bool(metadata.sir)]
        if metadata.include_sql:
            checks.append(bool(metadata.sql_value))
        if metadata.include_doc:
            checks.append(bool(metadata.doc_value))
        if metadata.include_tax_reference:
            checks.append(bool(metadata.tax_reference_value))

        for check in checks:
            total += 1
            if check:
                filled += 1

        for data in self.collect_sections():
            if data.is_plain_text_block():
                section_checks = [bool(data.issue_text)]
            else:
                section_checks = [
                    bool(str(data.number).strip()),
                    bool(data.title),
                    bool(data.precondition),
                    bool(data.scenario),
                    bool(data.issue_text),
                ]
            for check in section_checks:
                total += 1
                if check:
                    filled += 1

        if total == 0:
            return 100
        return round((filled / total) * 100)

    def build_preview_text(self) -> str:
        builder = TextReportBuilder(self.output_dir_input.text().strip() or self.get_output_dir())
        return builder.build_content(self.collect_metadata(), self.collect_sections())

    def refresh_live_state(self):
        self.refresh_attachment_hints()

        preview_text = self.build_preview_text()
        current_text = self.preview_text.toPlainText()
        if current_text != preview_text:
            self.preview_text.setPlainText(preview_text)

        completion = self.calculate_completion()
        self.completion_bar.setValue(completion)
        self.completion_label.setText(f"Заполненность: {completion}%")

        issue_count = len(self.collect_validation_issues())
        if completion == 100:
            self.completion_hint.setText("Отчет заполнен полностью и готов к сохранению.")
        elif issue_count:
            self.completion_hint.setText(f"Сейчас найдено незаполненных или некорректных полей: {issue_count}.")
        else:
            self.completion_hint.setText("Продолжайте заполнять отчет. Предпросмотр обновляется автоматически.")

        self.save_session_cache()

    def confirm_save_with_issues(self, issues: list[str]) -> bool:
        dialog = ValidationIssuesDialog(issues, self)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def confirm_issue_numbers(self) -> bool:
        rows: list[str] = []
        for index, data in enumerate(self.collect_sections(), start=1):
            if data.is_empty() or data.is_plain_text_block():
                continue
            number = str(data.number).strip() or "не указан"
            title = data.title.strip() or "без названия"
            rows.append(f"Раздел {index}: ошибка № {number} - {title}")

        if not rows:
            return True

        message = (
            "Проверьте номер ошибки перед сохранением отчета.\n\n"
            + "\n".join(rows)
            + "\n\nНомер ошибки указан правильно?"
        )
        return (
            QMessageBox.question(
                self,
                "Проверка номера ошибки",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )

    def save_report(self):
        metadata = self.collect_metadata()
        if not metadata.sir:
            set_invalid_state(self.sir_input, True)
            QMessageBox.warning(
                self,
                "Невозможно сохранить отчет",
                "Заполните поле SIR. Оно используется в имени файла отчета.",
            )
            return

        issues = self.collect_validation_issues()
        if issues and not self.confirm_save_with_issues(issues):
            return

        if not self.confirm_issue_numbers():
            return

        builder = TextReportBuilder(self.output_dir_input.text().strip() or self.get_output_dir())
        filepath = builder.save(metadata, self.collect_sections())
        self.save_session_cache()

        reply = QMessageBox.question(
            self,
            "Отчет сохранен",
            f"Файл успешно сохранен:\n{filepath}\n\nОткрыть папку?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(filepath)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_responsive_layout()

    def closeEvent(self, event):
        self.save_session_cache()
        super().closeEvent(event)

    def _update_responsive_layout(self, *, force: bool = False):
        if not hasattr(self, "content_splitter"):
            return

        self._update_density_mode(force=force)
        compact_mode = self.width() < 1040
        desired_orientation = Qt.Orientation.Vertical if compact_mode else Qt.Orientation.Horizontal
        current_orientation = self.content_splitter.orientation()
        if not force and current_orientation == desired_orientation:
            return

        self.content_splitter.setOrientation(desired_orientation)
        if desired_orientation == Qt.Orientation.Horizontal:
            self.workflow_panel.setMinimumWidth(420)
            self.side_panel.setMinimumWidth(300)
            self.content_splitter.setSizes([max(int(self.width() * 0.68), 620), max(int(self.width() * 0.32), 300)])
            return

        self.workflow_panel.setMinimumWidth(0)
        self.side_panel.setMinimumWidth(0)
        self.content_splitter.setSizes([max(int(self.height() * 0.56), 320), max(int(self.height() * 0.44), 220)])

    def _update_density_mode(self, *, force: bool = False):
        dense_mode = self.width() < 1480
        if not force and self._dense_mode == dense_mode:
            return

        self._dense_mode = dense_mode
        self.setProperty("denseMode", dense_mode)

        for section in self.sections:
            section.set_ui_density(dense_mode)

        if self._base_stylesheet:
            self.setStyleSheet(self._base_stylesheet)
