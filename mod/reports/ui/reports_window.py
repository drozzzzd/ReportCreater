"""Главное окно конструктора отчетов."""
from __future__ import annotations

import json
import os
from datetime import datetime

from PyQt6.QtCore import QEvent, QPoint, QRectF, QSize, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPalette, QPen, QRegion, QTextOption
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizeGrip,
    QSizePolicy,
    QSplitter,
    QSpacerItem,
    QSystemTrayIcon,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from ..core.attachment_counter import (
    attachment_counter_key,
    find_max_attachment_index,
    format_attachment_name,
    iter_attachment_values,
)
from ..core.report_builder import TextReportBuilder
from ..core.report_data import ReportMetadata, ReportSectionData
from ..core.report_parser import TextReportParser
from ..core.report_store import ReportStore
from ..dialogs.settings import SettingsDialog
from ..dialogs.validation_issues import ValidationIssuesDialog
from ..utils.app_assets import apply_windows_dark_frame, load_app_icon
from ..utils.action_icons import make_action_icon
from ..utils.icons import load_mode_icons
from ..utils.paths import get_project_root, get_writable_app_root
from ..utils.widget_helpers import (
    apply_soft_shadow,
    install_clearable_context_menu,
    install_press_feedback,
    set_invalid_state,
)
from ..widgets.smooth_scroll_area import SmoothScrollArea
from .section_widget import ReportSectionWidget


DARK_STYLE_OVERRIDES = """
ReportsWindow,
QDialog,
QFileDialog,
QMessageBox {
    color: #F4F7FB;
}

ReportsWindow {
    background-color: transparent;
}

QDialog,
QFileDialog,
QMessageBox {
    background-color: #171B22;
}

QFrame#windowShell {
    background-color: #171B22;
    border-color: #323B4D;
}

QFrame#appTitleBar {
    background-color: #11161E;
    border-bottom-color: #2A3140;
}

QLabel#appTitleLabel {
    color: #F4F7FB;
}

QToolButton#windowControlButton,
QToolButton#windowCloseButton {
    background-color: transparent;
    border: none;
}

QToolButton#windowControlButton:hover {
    background-color: #252C3A;
}

QToolButton#windowControlButton:pressed {
    background-color: #1C2230;
}

QToolButton#windowCloseButton:hover {
    background-color: #7F1D1D;
}

QToolButton#windowCloseButton:pressed {
    background-color: #991B1B;
}

ReportsWindow QWidget#setupTab,
ReportsWindow QWidget#fillTab,
ReportsWindow QWidget#setupScrollContent,
ReportsWindow QWidget#sectionsPanel,
ReportsWindow QWidget#sectionsHost,
ReportsWindow QWidget#sidePanel,
QDialog QWidget,
QFileDialog QWidget {
    background-color: #171B22;
    color: #F4F7FB;
}

QTabWidget#mainTabs::pane {
    border-top-color: #2A3140;
    background-color: #171B22;
}

QTabWidget#mainTabs QTabBar::tab {
    color: #AEB8C8;
}

QTabWidget#mainTabs QTabBar::tab:hover,
QTabWidget#mainTabs QTabBar::tab:selected {
    color: #FFFFFF;
}

QFrame#heroPanel,
QDialog#settingsDialog,
QDialog#settingsDialog QWidget,
QFrame#metaGroup,
QFrame#previewShell,
QFrame#progressShell,
QFrame#reportSectionCard,
QGroupBox {
    background-color: #202633;
    border-color: #323B4D;
    color: #F4F7FB;
}

QGroupBox::title {
    background-color: #202633;
    color: #F4F7FB;
}

QFrame#reportSectionCard {
    background-color: #171B22;
    border: none;
    border-radius: 0;
}

QLabel,
QLabel#heroTitle,
QLabel#panelTitle,
QLabel#previewWindowTitle,
QLabel#attachmentPreviewLabel,
QLabel#attachmentHintLabel {
    color: #F4F7FB;
}

QLabel#heroSubtitle,
QLabel#summaryLabel,
QLabel#metaSectionLabel,
QLabel#previewHintLabel,
QLabel#previewWindowState {
    color: #B7C2D4;
}

QLineEdit,
QPlainTextEdit,
QComboBox,
QListView,
QTreeView,
QTableView,
QListWidget {
    background-color: #12161D;
    border: 1px solid #394356;
    color: #F7FAFF;
    selection-background-color: #2F6FEA;
    selection-color: #FFFFFF;
}

QComboBox::drop-down {
    border-left: 1px solid #394356;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #202633;
    border: 1px solid #3A4558;
    color: #F4F7FB;
    selection-background-color: #2F6FEA;
    selection-color: #FFFFFF;
}

QLineEdit:hover,
QPlainTextEdit:hover,
QComboBox:hover {
    border-color: #4C5B73;
}

QLineEdit:focus,
QPlainTextEdit:focus,
QComboBox:focus {
    border-color: #6EA2FF;
    background-color: #12161D;
}

QLineEdit[readOnly="true"] {
    background-color: #12161D;
    color: #DDE6F5;
}

QPushButton,
QToolButton#modeButton,
QToolButton#settingsButton,
QToolButton#themeToggleButton {
    background-color: #252C3A;
    border-color: #3A4558;
    color: #F4F7FB;
}

QPushButton:hover,
QToolButton#modeButton:hover,
QToolButton#settingsButton:hover,
QToolButton#themeToggleButton:hover {
    background-color: #2C3546;
    border-color: #4B5A72;
}

QPushButton:pressed,
QToolButton#modeButton:pressed,
QToolButton#settingsButton:pressed,
QToolButton#themeToggleButton:pressed {
    background-color: #1C2230;
    border-color: #526077;
}

QPushButton:focus {
    border-color: #6EA2FF;
}

QPushButton:disabled {
    background-color: #1C2230;
    border-color: #323B4D;
    color: #748199;
}

QPushButton[buttonType="secondary"],
QPushButton#resetCacheBtn {
    background-color: #202633;
    color: #F4F7FB;
    border-color: #3A4558;
}

QPushButton[small="true"] {
    background-color: #202633;
    color: #DDE6F5;
    border: 1px solid #3A4558;
}

QPushButton[small="true"]:hover {
    background-color: #2C3546;
    color: #FFFFFF;
    border-color: #4B5A72;
}

QPushButton[small="true"]:pressed {
    background-color: #1C2230;
    border-color: #526077;
}

QMenu,
QMenu#splitDropdownMenu,
QMenu#reportHistoryMenu {
    background-color: #202633;
    border: 1px solid #3A4558;
    color: #F4F7FB;
}

QMenu::item:selected {
    background-color: #2F6FEA;
    color: #FFFFFF;
}

QFrame#previewWindowBar {
    border-bottom-color: #323B4D;
}

QProgressBar {
    background-color: #12161D;
    border-color: #394356;
    color: #FFFFFF;
}

QScrollBar::handle:vertical {
    background: #526077;
}

QLabel#settingsDialogTitle {
    color: #FFFFFF;
}

QGroupBox#sectionEditorGroup,
QGroupBox#sectionIssueGroup {
    background-color: #202633;
    border: 1px solid #323B4D;
    color: #F4F7FB;
}

QGroupBox#sectionEditorGroup::title,
QGroupBox#sectionIssueGroup::title {
    background-color: #202633;
    color: #DDE6F5;
}

QGroupBox#progressPanel {
    background-color: transparent;
    border: none;
    color: #F4F7FB;
}

QGroupBox#progressPanel::title {
    background-color: transparent;
    color: #F4F7FB;
}

QLineEdit#sectionNumberInput,
QLineEdit#sectionTitleInput,
QPlainTextEdit#previewEditor {
    background-color: #12161D;
    border-color: #394356;
    color: #F7FAFF;
}

QLineEdit#sectionNumberInput:focus,
QLineEdit#sectionTitleInput:focus,
QPlainTextEdit#previewEditor:focus {
    background-color: #12161D;
    border-color: #6EA2FF;
}

QLineEdit[invalid="true"],
QPlainTextEdit[invalid="true"] {
    border: 1px solid #EF4444;
}

QCheckBox {
    color: #F4F7FB;
}

QCheckBox:disabled {
    color: #B7C2D4;
}

QCheckBox::indicator {
    background-color: #12161D;
    border-color: #4C5B73;
}

QCheckBox::indicator:checked {
    background-color: #2F6FEA;
    border-color: #2F6FEA;
}

QWidget#issueTypeCombo,
QWidget#menuSplitRow {
    background-color: transparent;
}

QPushButton#issueTypeSegmentButton {
    background-color: #202633;
    border-color: #3A4558;
    color: #B7C2D4;
}

QPushButton#issueTypeSegmentButton:hover {
    background-color: #2C3546;
    color: #F4F7FB;
}

QPushButton#issueTypeSegmentButton:checked {
    background-color: #2F6FEA;
    border-color: #2F6FEA;
    color: #FFFFFF;
}

QToolButton#modeButton::menu-button {
    border-left-color: #3A4558;
}

QMenu#splitDropdownMenu::separator {
    background-color: #323B4D;
}

QPushButton#menuItemButton,
QPushButton#menuSplitMainButton,
QToolButton#menuSplitArrowButton {
    background-color: transparent;
    border: none;
    color: #F4F7FB;
}

QPushButton#menuItemButton:hover,
QPushButton#menuSplitMainButton:hover,
QToolButton#menuSplitArrowButton:hover {
    background-color: #2C3546;
}

QPushButton#menuSplitMainButton {
    border-right: 1px solid #323B4D;
}

QToolButton#menuSplitArrowButton {
    color: #B7C2D4;
}

QListWidget#reportHistoryList::item:hover,
QListWidget#reportHistoryList::item:selected {
    background-color: #2F6FEA;
    color: #FFFFFF;
}
"""


class HeroIllustration(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("heroIllustration")
        self.setFixedSize(QSize(104, 82))

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        outline = QRectF(14, 4, 56, 56)
        outline_pen = QPen(QColor("#9DBAF7"), 2)
        outline_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(outline_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(outline, 14, 14)

        card = QRectF(26, 22, 58, 50)
        painter.setPen(QPen(QColor("#DDE3EA"), 1))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRoundedRect(card, 8, 8)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#2F6FEA")))
        painter.drawRoundedRect(QRectF(36, 32, 42, 5), 2, 2)

        painter.setBrush(QBrush(QColor("#D5DAE1")))
        painter.drawRoundedRect(QRectF(36, 43, 32, 4), 2, 2)
        painter.drawRoundedRect(QRectF(36, 52, 40, 4), 2, 2)
        painter.drawRoundedRect(QRectF(36, 61, 34, 4), 2, 2)

        painter.setBrush(QBrush(QColor("#2F6FEA")))
        painter.setPen(QPen(QColor("#2F6FEA"), 1))
        painter.drawEllipse(QRectF(74, 54, 26, 26))
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.drawLine(80, 67, 94, 67)
        painter.drawLine(87, 60, 87, 74)


class ReportsWindow(QWidget):
    SESSION_CACHE_VERSION = 1
    WINDOW_CORNER_RADIUS = 16

    def __init__(self, config: dict, config_path: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("ReportsWindow")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
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
        self._window_control_buttons: set[QWidget] = set()
        self._title_drag_widgets: set[QWidget] = set()
        self._drag_start_position: QPoint | None = None
        self._session_cache_path = self.get_session_cache_path()
        self._report_store = ReportStore(self.get_report_store_path())
        self._user_settings = self._load_user_settings()
        self._current_theme = self._user_settings["theme"]

        self.setWindowTitle("Конструктор отчетов")
        self.resize(1180, 760)
        self.setMinimumSize(860, 560)

        self._load_styles()
        self._apply_theme(self._current_theme)
        self._build_ui()
        self._connect_live_updates()
        self.add_section()
        self.restore_session_cache()
        self.apply_saved_preferences()
        self._session_cache_enabled = True
        self.refresh_live_state()

    # ---- Стили ----

    def _load_styles(self):
        style_path = os.path.join(get_project_root(), "styles", "reports_window.qss")
        if not os.path.exists(style_path):
            return
        with open(style_path, "r", encoding="utf-8") as file:
            self._base_stylesheet = file.read()
        self.setStyleSheet(self._compose_stylesheet())

    def _compose_stylesheet(self) -> str:
        if self._current_theme == "dark":
            return f"{self._base_stylesheet}\n{DARK_STYLE_OVERRIDES}"
        return self._base_stylesheet

    def _apply_theme(self, theme: str) -> None:
        self._current_theme = "dark" if theme == "dark" else "light"
        self.setProperty("theme", self._current_theme)
        self.setStyleSheet(self._compose_stylesheet())
        self._apply_theme_palette()
        self._sync_native_frame(self)

        if hasattr(self, "theme_toggle_btn"):
            self.theme_toggle_btn.setText("")
            self.theme_toggle_btn.setIcon(
                make_action_icon("sun" if self._current_theme == "dark" else "moon", self._current_theme)
            )
            self.theme_toggle_btn.setToolTip("Переключить на светлую тему" if self._current_theme == "dark" else "Переключить на темную тему")
        if hasattr(self, "settings_btn"):
            self.settings_btn.setIcon(make_action_icon("settings", self._current_theme))
        if hasattr(self, "window_minimize_btn"):
            self._refresh_window_controls()
        self._refresh_action_icons()

    def _apply_theme_palette(self) -> None:
        app = QApplication.instance()
        if app is None:
            return

        palette = QPalette()
        if self._current_theme == "dark":
            palette.setColor(QPalette.ColorRole.Window, QColor("#171B22"))
            palette.setColor(QPalette.ColorRole.WindowText, QColor("#F4F7FB"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#12161D"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#202633"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#F7FAFF"))
            palette.setColor(QPalette.ColorRole.Button, QColor("#252C3A"))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor("#F4F7FB"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#2F6FEA"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#8692A6"))
        else:
            palette = app.style().standardPalette()
        app.setPalette(palette)

    def _sync_native_frame(self, widget: QWidget) -> None:
        if not widget.isVisible():
            return
        dark = self._current_theme == "dark"
        apply_windows_dark_frame(widget, dark)
        QTimer.singleShot(0, lambda target=widget, is_dark=dark: apply_windows_dark_frame(target, is_dark))
        QTimer.singleShot(80, lambda target=widget, is_dark=dark: apply_windows_dark_frame(target, is_dark))

    def _refresh_action_icons(self) -> None:
        themed_buttons = {
            "add_btn": "add",
            "remove_last_btn": "remove",
            "save_btn": "save",
            "open_report_btn": "open",
            "open_file_btn": "file-open",
            "reset_cache_btn": "reset",
            "settings_btn": "settings",
        }
        for attr_name, icon_name in themed_buttons.items():
            button = getattr(self, attr_name, None)
            if button is not None:
                button.setIcon(make_action_icon(icon_name, self._current_theme))

    def _toggle_window_maximized(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self._refresh_window_controls()

    def _refresh_window_controls(self) -> None:
        if not hasattr(self, "window_minimize_btn"):
            return
        self.window_minimize_btn.setIcon(make_action_icon("window-minimize", self._current_theme))
        self.window_maximize_btn.setIcon(
            make_action_icon("window-restore" if self.isMaximized() else "window-maximize", self._current_theme)
        )
        self.window_close_btn.setIcon(make_action_icon("window-close", self._current_theme))
        self.window_maximize_btn.setToolTip("Восстановить" if self.isMaximized() else "Развернуть")

    def _config_section(self, key: str) -> dict:
        section = self.config.setdefault(key, {})
        if not isinstance(section, dict):
            section = {}
            self.config[key] = section
        return section

    def _load_user_settings(self) -> dict:
        ui_config = self._config_section("ui")
        preferences = self._config_section("preferences")
        theme_value = ui_config.get("default_theme", ui_config.get("theme", "light"))
        return {
            "theme": "dark" if str(theme_value).lower() == "dark" else "light",
            "default_performer": str(preferences.get("default_performer", "")).strip(),
            "default_output_dir": str(preferences.get("default_output_dir", "")).strip(),
            "remember_defaults": bool(preferences.get("remember_defaults", False)),
        }

    def _save_config(self) -> None:
        if not self.config_path:
            return
        try:
            with open(self.config_path, "w", encoding="utf-8") as file:
                json.dump(self.config, file, ensure_ascii=False, indent=4)
        except OSError:
            return

    def toggle_theme(self) -> None:
        self.set_theme("light" if self._current_theme == "dark" else "dark")

    def set_theme(self, theme: str) -> None:
        self._user_settings["theme"] = "dark" if theme == "dark" else "light"
        self._config_section("ui")["theme"] = self._user_settings["theme"]
        self._config_section("ui")["default_theme"] = self._user_settings["theme"]
        self._save_config()
        self._apply_theme(self._user_settings["theme"])

    # ---- Построение UI ----

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.window_shell = QFrame()
        self.window_shell.setObjectName("windowShell")
        self.window_shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        root.addWidget(self.window_shell, 1)
        self.size_grip = QSizeGrip(self.window_shell)
        self.size_grip.setObjectName("windowSizeGrip")
        self.size_grip.resize(18, 18)

        shell_layout = QVBoxLayout(self.window_shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        self._build_window_titlebar(shell_layout)

        self.main_tabs = QTabWidget()
        self.main_tabs.setObjectName("mainTabs")
        shell_layout.addWidget(self.main_tabs, 1)

        self._build_setup_tab()
        self._build_fill_tab()
        self._build_tab_corner_actions()
        self.main_tabs.currentChanged.connect(self._sync_tab_corner_actions)
        self._update_responsive_layout(force=True)

    def _build_window_titlebar(self, parent_layout: QVBoxLayout) -> None:
        self.title_bar = QFrame()
        self.title_bar.setObjectName("appTitleBar")
        self.title_bar.setFixedHeight(38)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(12, 0, 6, 0)
        title_layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setObjectName("appTitleIcon")
        app_icon = load_app_icon()
        if not app_icon.isNull():
            icon_label.setPixmap(app_icon.pixmap(16, 16))
        icon_label.setFixedSize(18, 18)

        self.title_label = QLabel(self.windowTitle())
        self.title_label.setObjectName("appTitleLabel")

        title_layout.addWidget(icon_label)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch(1)

        self.window_minimize_btn = self._create_window_button("window-minimize", "Свернуть")
        self.window_maximize_btn = self._create_window_button("window-maximize", "Развернуть")
        self.window_close_btn = self._create_window_button("window-close", "Закрыть")
        self.window_close_btn.setObjectName("windowCloseButton")

        self.window_minimize_btn.clicked.connect(self.showMinimized)
        self.window_maximize_btn.clicked.connect(self._toggle_window_maximized)
        self.window_close_btn.clicked.connect(self.close)

        title_layout.addWidget(self.window_minimize_btn)
        title_layout.addWidget(self.window_maximize_btn)
        title_layout.addWidget(self.window_close_btn)
        parent_layout.addWidget(self.title_bar)
        self._title_drag_widgets = {self.title_bar, icon_label, self.title_label}
        for widget in self._title_drag_widgets:
            widget.installEventFilter(self)
        self._refresh_window_controls()

    def _create_window_button(self, icon_name: str, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setObjectName("windowControlButton")
        button.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        button.setAutoRaise(False)
        button.setFixedSize(38, 30)
        button.setIconSize(QSize(16, 16))
        button.setToolTip(tooltip)
        button.setIcon(make_action_icon(icon_name, self._current_theme))
        self._window_control_buttons.add(button)
        return button

    def _polish_visible_controls(self) -> None:
        widgets = [
            getattr(self, "save_btn", None),
            getattr(self, "open_report_btn", None),
            getattr(self, "open_file_btn", None),
            getattr(self, "reset_cache_btn", None),
            getattr(self, "add_btn", None),
            getattr(self, "remove_last_btn", None),
            getattr(self, "theme_toggle_btn", None),
            getattr(self, "settings_btn", None),
            getattr(self, "window_minimize_btn", None),
            getattr(self, "window_maximize_btn", None),
            getattr(self, "window_close_btn", None),
        ]
        for widget in widgets:
            if widget is None:
                continue
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
        if hasattr(self, "window_shell"):
            self.window_shell.update()

    def _update_window_mask(self) -> None:
        if self.isMaximized() or self.isFullScreen():
            self.clearMask()
            return
        path = QPainterPath()
        path.addRoundedRect(
            QRectF(self.rect()),
            self.WINDOW_CORNER_RADIUS,
            self.WINDOW_CORNER_RADIUS,
        )
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def _build_tab_corner_actions(self):
        self.tab_actions = QFrame()
        self.tab_actions.setObjectName("tabCornerActions")
        actions_layout = QHBoxLayout(self.tab_actions)
        actions_layout.setContentsMargins(0, 0, 14, 0)
        actions_layout.setSpacing(8)

        self.add_btn = QPushButton("+  Раздел")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.setIcon(make_action_icon("add", self._current_theme))
        self.add_btn.clicked.connect(self.add_section)

        self.remove_last_btn = QPushButton("- Последний")
        self.remove_last_btn.setProperty("buttonType", "secondary")
        self.remove_last_btn.setIcon(make_action_icon("remove", self._current_theme))
        self.remove_last_btn.clicked.connect(self.remove_last_section)

        self.theme_toggle_btn = QToolButton()
        self.theme_toggle_btn.setObjectName("themeToggleButton")
        self.theme_toggle_btn.setAutoRaise(False)
        self.theme_toggle_btn.setFixedSize(34, 30)
        self.theme_toggle_btn.setIconSize(QSize(18, 18))
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)

        self.settings_btn = QToolButton()
        self.settings_btn.setObjectName("settingsButton")
        self.settings_btn.setAutoRaise(False)
        self.settings_btn.setFixedSize(34, 30)
        self.settings_btn.setText("")
        self.settings_btn.setIcon(make_action_icon("settings", self._current_theme))
        self.settings_btn.setIconSize(QSize(18, 18))
        self.settings_btn.setToolTip("Настройки")
        self.settings_btn.clicked.connect(self.open_settings_dialog)

        for button in (self.add_btn, self.remove_last_btn):
            button.setMinimumHeight(30)
            button.setIconSize(QSize(15, 15))
            install_press_feedback(button)
        for button in (self.theme_toggle_btn, self.settings_btn):
            install_press_feedback(button)
        self.add_btn.setFixedWidth(104)
        self.remove_last_btn.setFixedWidth(112)

        actions_layout.addWidget(self.add_btn)
        actions_layout.addWidget(self.remove_last_btn)
        actions_layout.addWidget(self.theme_toggle_btn)
        actions_layout.addWidget(self.settings_btn)
        self.main_tabs.setCornerWidget(self.tab_actions, Qt.Corner.TopRightCorner)
        self._apply_theme(self._current_theme)
        self._sync_tab_corner_actions()

    def _sync_tab_corner_actions(self):
        if not hasattr(self, "tab_actions"):
            return
        fill_tab_active = self.main_tabs.currentWidget() is self.fill_tab
        self.add_btn.setVisible(fill_tab_active)
        self.remove_last_btn.setVisible(fill_tab_active)

    def _build_setup_tab(self):
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
        workflow_content_layout.setContentsMargins(20, 16, 20, 20)
        workflow_content_layout.setSpacing(14)

        self.main_tabs.addTab(self.setup_tab, "Конструктор отчетов")

        self._build_hero_panel(workflow_content_layout)
        self._build_meta_group(workflow_content_layout)

    def _build_hero_panel(self, parent_layout: QVBoxLayout):
        toolbar = QFrame()
        toolbar.setObjectName("constructorToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        self.toolbar_layout = toolbar_layout
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(14)

        self.save_btn = QPushButton("Сохранить отчет")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setIcon(make_action_icon("save", self._current_theme))
        self.save_btn.clicked.connect(self.save_report)

        self.open_report_btn = QPushButton("Открыть отчет")
        self.open_report_btn.setProperty("buttonType", "secondary")
        self.open_report_btn.setIcon(make_action_icon("open", self._current_theme))
        self.open_report_btn.clicked.connect(self.show_report_history)

        self.open_file_btn = QPushButton("Из файлов")
        self.open_file_btn.setProperty("buttonType", "secondary")
        self.open_file_btn.setIcon(make_action_icon("file-open", self._current_theme))
        self.open_file_btn.clicked.connect(self.select_report_file)

        self.reset_cache_btn = QPushButton("Сброс черновика")
        self.reset_cache_btn.setObjectName("resetCacheBtn")
        self.reset_cache_btn.setIcon(make_action_icon("reset", self._current_theme))
        self.reset_cache_btn.clicked.connect(lambda: self.reset_autosave_draft())

        self.sections_label = QLabel("Разделов: 0")
        self.sections_label.setObjectName("summaryLabel")
        self.sections_label.setProperty("summaryBadge", "true")

        for button in (self.save_btn, self.open_report_btn, self.open_file_btn):
            button.setMinimumHeight(34)
            button.setIconSize(QSize(15, 15))
            install_press_feedback(button)
        self.reset_cache_btn.setMinimumHeight(34)
        self.reset_cache_btn.setIconSize(QSize(15, 15))
        install_press_feedback(self.reset_cache_btn)
        self.save_btn.setFixedWidth(178)
        self.open_report_btn.setFixedWidth(154)
        self.open_file_btn.setFixedWidth(126)
        self.reset_cache_btn.setFixedWidth(170)
        self.sections_label.setFixedWidth(88)

        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.save_btn)
        toolbar_layout.addWidget(self.open_report_btn)
        toolbar_layout.addWidget(self.open_file_btn)
        self.toolbar_gap = QSpacerItem(28, 1, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        toolbar_layout.addItem(self.toolbar_gap)
        toolbar_layout.addWidget(self.sections_label)
        toolbar_layout.addWidget(self.reset_cache_btn)
        parent_layout.addWidget(toolbar)

        # Hero-панель
        self.hero_panel = QFrame()
        self.hero_panel.setObjectName("heroPanel")
        self.hero_panel.setMinimumHeight(170)
        apply_soft_shadow(self.hero_panel, blur_radius=26, y_offset=10, color=QColor(30, 42, 64, 22))
        hero_layout = QVBoxLayout(self.hero_panel)
        hero_layout.setContentsMargins(16, 16, 16, 16)
        hero_layout.setSpacing(6)

        hero_layout.addStretch(1)
        hero_layout.addWidget(HeroIllustration(), 0, Qt.AlignmentFlag.AlignHCenter)

        hero_title = QLabel("Конструктор отчетов")
        hero_title.setObjectName("heroTitle")
        hero_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(hero_title)

        hero_subtitle = QLabel(
            "Собирайте шаги, проверяйте результат вживую и сохраняйте готовый TXT без лишней ручной правки."
        )
        hero_subtitle.setObjectName("heroSubtitle")
        hero_subtitle.setWordWrap(True)
        hero_subtitle.setMaximumWidth(620)
        hero_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(hero_subtitle)
        hero_layout.addStretch(1)
        parent_layout.addWidget(self.hero_panel)

    def _build_meta_group(self, parent_layout: QVBoxLayout):
        self.meta_group = QFrame()
        self.meta_group.setObjectName("metaGroup")
        apply_soft_shadow(self.meta_group, blur_radius=20, y_offset=7)
        outer_layout = QVBoxLayout(self.meta_group)
        outer_layout.setContentsMargins(16, 14, 16, 16)
        outer_layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        accent = QFrame()
        accent.setObjectName("panelTitleAccent")
        accent.setFixedSize(4, 22)
        header_layout.addWidget(accent)

        title = QLabel("Параметры отчета")
        title.setObjectName("panelTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()
        outer_layout.addLayout(header_layout)

        meta_layout = QFormLayout()
        meta_layout.setSpacing(4)
        meta_layout.setHorizontalSpacing(8)
        meta_layout.setVerticalSpacing(8)
        meta_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addLayout(meta_layout)

        # Поля
        self.build_input = self._make_meta_input("Введите build")
        self.database_input = self._make_meta_input("Введите BD")
        self.sir_input = self._make_meta_input("Введите SIR")
        self.performer_input = self._make_meta_input("Введите исполнителя")

        self.sql_check = QCheckBox("Добавить строку SQL")
        self.sql_check.setChecked(True)
        self.sql_input = self._make_meta_input("Введите SQL")

        self.doc_check = QCheckBox("Добавить строку DOC")
        self.doc_check.setChecked(True)
        self.doc_input = self._make_meta_input("Введите DOC")

        self.tax_reference_check = QCheckBox("Добавить Tax Referens")
        self.tax_reference_check.setChecked(True)
        self.tax_reference_input = self._make_meta_input("Введите Tax Referens")

        # Папка сохранения
        self.output_dir_row_widget = QWidget()
        path_row = QHBoxLayout(self.output_dir_row_widget)
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.setSpacing(6)
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setReadOnly(True)
        self.output_dir_input.setText(self.get_output_dir())
        self.output_dir_input.setFixedHeight(28)
        browse_btn = QPushButton("...")
        browse_btn.setObjectName("browseBtn")
        browse_btn.setFixedWidth(34)
        browse_btn.setFixedHeight(28)
        install_press_feedback(browse_btn)
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

        self.meta_layout = meta_layout
        meta_layout.addRow(report_fields_label)
        meta_layout.addRow("Build:", self.build_input)
        meta_layout.addRow("BD:", self.database_input)
        meta_layout.addRow(self.sql_check, self.sql_input)
        meta_layout.addRow(self.doc_check, self.doc_input)
        meta_layout.addRow(self.tax_reference_check, self.tax_reference_input)
        meta_layout.addRow("Папка сохранения:", self.output_dir_row_widget)
        meta_layout.addRow(service_fields_label)
        meta_layout.addRow("SIR:", self.sir_input)
        meta_layout.addRow("Исполнитель:", self.performer_input)
        meta_layout.addRow("Следующее вложение:", self.next_attachment_label)
        parent_layout.addWidget(self.meta_group)

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

    @staticmethod
    def _make_meta_input(placeholder: str) -> QLineEdit:
        widget = QLineEdit()
        widget.setPlaceholderText(placeholder)
        widget.setFixedHeight(28)
        return widget

    def _build_fill_tab(self):
        self.fill_tab = QWidget()
        self.fill_tab.setObjectName("fillTab")
        fill_layout = QVBoxLayout(self.fill_tab)
        fill_layout.setContentsMargins(0, 0, 0, 0)
        fill_layout.setSpacing(0)

        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_splitter.setObjectName("mainContentSplitter")
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.setHandleWidth(12)
        fill_layout.addWidget(self.content_splitter, 1)

        self.sections_panel = QWidget()
        self.sections_panel.setObjectName("sectionsPanel")
        self.sections_panel.setMinimumWidth(420)
        sections_panel_layout = QVBoxLayout(self.sections_panel)
        sections_panel_layout.setContentsMargins(0, 0, 0, 0)
        sections_panel_layout.setSpacing(6)
        self.workflow_panel = self.sections_panel

        self.side_panel = QWidget()
        self.side_panel.setObjectName("sidePanel")
        self.side_panel.setMinimumWidth(300)
        side_layout = QVBoxLayout(self.side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(8)

        self._build_sections_scroll(sections_panel_layout)
        self._build_preview_panel(side_layout)
        self._build_progress_panel(side_layout)

        self.content_splitter.addWidget(self.sections_panel)
        self.content_splitter.addWidget(self.side_panel)
        self.content_splitter.setStretchFactor(0, 3)
        self.content_splitter.setStretchFactor(1, 2)
        self.content_splitter.setSizes([910, 390])
        self.main_tabs.addTab(self.fill_tab, "Заполнение ошибок и предпросмотр")

    def _build_sections_scroll(self, parent_layout: QVBoxLayout):
        self.sections_host = QWidget()
        self.sections_host.setObjectName("sectionsHost")
        self.sections_layout = QVBoxLayout(self.sections_host)
        self.sections_layout.setContentsMargins(0, 0, 0, 0)
        self.sections_layout.setSpacing(8)
        self.sections_layout.addStretch(0)

        self.sections_scroll_area = SmoothScrollArea()
        self.sections_scroll_area.setObjectName("sectionsScrollArea")
        self.sections_scroll_area.setWidgetResizable(True)
        self.sections_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.sections_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sections_scroll_area.setWidget(self.sections_host)
        parent_layout.addWidget(self.sections_scroll_area, 1)

    def _build_preview_panel(self, parent_layout: QVBoxLayout):
        self.preview_shell = QFrame()
        self.preview_shell.setObjectName("previewShell")
        self.preview_shell.setMinimumWidth(320)
        apply_soft_shadow(self.preview_shell, blur_radius=22, y_offset=8)
        preview_shell_layout = QVBoxLayout(self.preview_shell)
        preview_shell_layout.setContentsMargins(10, 10, 10, 10)
        preview_shell_layout.setSpacing(8)

        preview_bar = QFrame()
        preview_bar.setObjectName("previewWindowBar")
        preview_bar_layout = QHBoxLayout(preview_bar)
        preview_bar_layout.setContentsMargins(10, 8, 10, 8)
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
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_layout.setSpacing(6)

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
        parent_layout.addWidget(self.preview_shell, 1)

    def _build_progress_panel(self, parent_layout: QVBoxLayout):
        progress_group = QGroupBox("Заполненность отчета")
        progress_group.setObjectName("progressPanel")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setContentsMargins(10, 8, 10, 8)
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
        self.progress_shell.setMinimumHeight(104)
        apply_soft_shadow(self.progress_shell, blur_radius=18, y_offset=6, color=QColor(30, 42, 64, 24))
        progress_shell_layout = QVBoxLayout(self.progress_shell)
        progress_shell_layout.setContentsMargins(8, 8, 8, 8)
        progress_shell_layout.setSpacing(6)
        progress_shell_layout.addWidget(progress_group)
        parent_layout.addWidget(self.progress_shell, 0)

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
        self._hero_collapsed = False
        self.hero_panel.setVisible(True)
        self.scroll_area.updateGeometry()
        self.refresh_live_state()

    def set_meta_collapsed(self, collapsed: bool):
        self._meta_collapsed = False
        self.meta_group.setVisible(True)
        self.scroll_area.updateGeometry()
        self.refresh_live_state()

    # ---- Пути ----

    def get_output_dir(self) -> str:
        general_config = self.config.get("general", {})
        base_dir = general_config.get("reports_dir", "reports")
        if not os.path.isabs(base_dir):
            base_dir = os.path.join(get_writable_app_root(), base_dir)
        return os.path.join(base_dir, "text_reports")

    def get_session_cache_path(self) -> str:
        general_config = self.config.get("general", {})
        cache_path = general_config.get("session_cache_path")
        if cache_path:
            if not os.path.isabs(cache_path):
                cache_path = os.path.join(get_writable_app_root(), cache_path)
            return cache_path

        base_dir = general_config.get("reports_dir", "reports")
        if not os.path.isabs(base_dir):
            base_dir = os.path.join(get_writable_app_root(), base_dir)
        return os.path.join(base_dir, ".report_builder_session_cache.json")

    def get_report_store_path(self) -> str:
        general_config = self.config.get("general", {})
        store_path = general_config.get("report_store_path")
        if store_path:
            if not os.path.isabs(store_path):
                store_path = os.path.join(get_writable_app_root(), store_path)
            return store_path

        base_dir = general_config.get("reports_dir", "reports")
        if not os.path.isabs(base_dir):
            base_dir = os.path.join(get_writable_app_root(), base_dir)
        return os.path.join(base_dir, ".report_history.sqlite3")

    def effective_output_dir(self) -> str:
        remembered_path = self._user_settings.get("default_output_dir", "")
        if self._user_settings.get("remember_defaults") and remembered_path:
            return remembered_path
        return self.output_dir_input.text().strip() or self.get_output_dir()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self._user_settings, self)
        dialog.setStyleSheet(self._compose_stylesheet())
        self._sync_native_frame(dialog)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._user_settings = dialog.values()
        self._config_section("ui")["theme"] = self._user_settings["theme"]
        self._config_section("ui")["default_theme"] = self._user_settings["theme"]
        preferences = self._config_section("preferences")
        preferences["default_performer"] = self._user_settings["default_performer"]
        preferences["default_output_dir"] = self._user_settings["default_output_dir"]
        preferences["remember_defaults"] = self._user_settings["remember_defaults"]
        self._save_config()
        self._apply_theme(self._user_settings["theme"])
        self.apply_saved_preferences()
        self.refresh_live_state()

    def apply_saved_preferences(self):
        remember = bool(self._user_settings.get("remember_defaults", False))
        performer = str(self._user_settings.get("default_performer", "")).strip()
        output_dir = str(self._user_settings.get("default_output_dir", "")).strip()

        if remember and performer:
            self.performer_input.setText(performer)
        if remember and output_dir:
            self.output_dir_input.setText(output_dir)

        self._set_form_field_visible(self.performer_input, not (remember and bool(performer)))
        self._set_form_field_visible(self.output_dir_row_widget, not (remember and bool(output_dir)))

    def _set_form_field_visible(self, field_widget: QWidget, visible: bool):
        field_widget.setVisible(visible)
        if hasattr(self, "meta_layout"):
            label = self.meta_layout.labelForField(field_widget)
            if label is not None:
                label.setVisible(visible)

    def _prepare_dialog(self, dialog: QFileDialog) -> QFileDialog:
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setStyleSheet(self._compose_stylesheet())
        self._sync_native_frame(dialog)
        return dialog

    def select_output_dir(self):
        dialog = self._prepare_dialog(QFileDialog(self, "Выберите папку для сохранения отчетов"))
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.selectedFiles()
            if selected:
                self.output_dir_input.setText(selected[0])

    def select_report_file(self):
        folder = self.effective_output_dir()
        os.makedirs(folder, exist_ok=True)
        dialog = self._prepare_dialog(QFileDialog(self, "Выбрать отчет из файлов", folder))
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilters(["Текстовые отчеты (*.txt)", "Все файлы (*)"])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.selectedFiles()
            if selected:
                self.load_report_from_file(selected[0])

    def show_report_history(self):
        records = self._report_store.list_recent(limit=100)
        if not records:
            QMessageBox.information(
                self,
                "История пуста",
                "Внутренняя история отчетов пока пустая. Используйте кнопку \"Из файлов\", чтобы открыть TXT вручную.",
            )
            return

        menu = QMenu(self)
        menu.setObjectName("reportHistoryMenu")
        menu.setStyleSheet(self._compose_stylesheet())
        list_widget = QListWidget(menu)
        list_widget.setObjectName("reportHistoryList")
        list_widget.setUniformItemSizes(True)
        list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        list_widget.setFixedWidth(420)
        row_height = 44
        list_widget.setFixedHeight(min(len(records), 7) * row_height + 6)

        for record in records:
            item = QListWidgetItem(f"{record['title']}\n{record['saved_at']}")
            item.setData(Qt.ItemDataRole.UserRole, int(record["id"]))
            list_widget.addItem(item)

        action = QWidgetAction(menu)
        action.setDefaultWidget(list_widget)
        menu.addAction(action)

        def load_selected(item: QListWidgetItem):
            menu.close()
            report_id = int(item.data(Qt.ItemDataRole.UserRole))
            self.load_report_from_store(report_id)

        list_widget.itemClicked.connect(load_selected)
        menu.exec(self.open_report_btn.mapToGlobal(self.open_report_btn.rect().bottomLeft()))

    def load_report_from_store(self, report_id: int):
        record = self._report_store.get(report_id)
        if record is None:
            QMessageBox.warning(self, "Отчет не найден", "Запись во внутренней истории больше недоступна.")
            return
        metadata, sections = self._report_store.decode_record(record)
        self.apply_loaded_report(metadata, sections)

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

            self._resize_sections_to(max(1, len(sections)))

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

    # ---- Управление секциями ----

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
        self.sections_layout.insertWidget(self.sections_layout.count() - 1, section, 1)
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
            self.sections_layout.removeWidget(section)
            section.deleteLater()
            self.renumber_sections()
            self.refresh_live_state()

    def _resize_sections_to(self, desired_count: int):
        """Гарантирует ровно desired_count секций (но не меньше 1)."""
        while len(self.sections) < desired_count:
            self.add_section()
        while len(self.sections) > desired_count and len(self.sections) > 1:
            section = self.sections.pop()
            self.sections_layout.removeWidget(section)
            section.deleteLater()
        self.renumber_sections()

    def renumber_sections(self):
        for index, section in enumerate(self.sections, start=1):
            section.set_section_number(index)
        self.sections_label.setText(f"Разделов: {len(self.sections)}")

    # ---- Сбор данных ----

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

    def collect_sections(self) -> list[ReportSectionData]:
        return [section.get_section_data() for section in self.sections]

    # ---- Сессия (autosave кеш) ----

    def build_session_cache_payload(self) -> dict:
        metadata = self.collect_metadata()
        return {
            "version": self.SESSION_CACHE_VERSION,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
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
                {"sir": sir, "performer": performer, "index": index}
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
        finally:
            self._session_cache_enabled = was_enabled

        self.apply_saved_preferences()
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
            self._resize_sections_to(max(1, len(sections)))

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
                key = attachment_counter_key(str(item.get("sir", "")), str(item.get("performer", "")))
                self._attachment_counters[key] = max(self._attachment_counters.get(key, 0), index)

        self._sync_attachment_counters_from_content()

    # ---- Attachment-счётчик ----

    def _section_text_blocks(self):
        for section in self.collect_sections():
            yield from (section.precondition, section.scenario, section.issue_text)

    def _sync_attachment_counters_from_content(self):
        metadata = self.collect_metadata()
        if not metadata.sir or not metadata.performer:
            return

        existing = find_max_attachment_index(metadata.sir, metadata.performer, self._section_text_blocks())
        if existing > 0:
            key = attachment_counter_key(metadata.sir, metadata.performer)
            self._attachment_counters[key] = max(self._attachment_counters.get(key, 0), existing)

    def build_attachment_text(self) -> str:
        sir = self.sir_input.text().strip()
        performer = self.performer_input.text().strip()
        if not sir or not performer:
            return format_attachment_name(sir, performer, 0)

        key = attachment_counter_key(sir, performer)
        existing = find_max_attachment_index(sir, performer, self._section_text_blocks())
        index = max(self._attachment_counters.get(key, 0), existing) + 1
        self._attachment_counters[key] = index
        return format_attachment_name(sir, performer, index)

    def preview_attachment_text(self) -> str:
        sir = self.sir_input.text().strip()
        performer = self.performer_input.text().strip()
        if not sir or not performer:
            return format_attachment_name(sir, performer, 0)

        key = attachment_counter_key(sir, performer)
        existing = find_max_attachment_index(sir, performer, self._section_text_blocks())
        index = max(self._attachment_counters.get(key, 0), existing) + 1
        return format_attachment_name(sir, performer, index)

    def build_tax_reference_menu_prefix(self) -> str:
        return self.tax_reference_input.text().strip()

    def refresh_attachment_hints(self):
        attachment_text = self.preview_attachment_text()
        self.next_attachment_label.setText(attachment_text)
        for section in self.sections:
            section.set_attachment_hint(attachment_text)

    # ---- Валидация ----

    @staticmethod
    def _attachment_issues(section_number: str, block_name: str, text: str) -> list[str]:
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
        builder = TextReportBuilder(self.effective_output_dir())
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

    # ---- Сохранение отчёта ----

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

        sections = self.collect_sections()
        builder = TextReportBuilder(self.effective_output_dir())
        filepath = builder.save(metadata, sections)
        self._report_store.save(
            metadata=metadata,
            sections=sections,
            filepath=filepath,
            content=builder.build_content(metadata, sections),
        )
        self.save_session_cache()

        QMessageBox.question(
            self,
            "Отчет сохранен",
            f"Отчет сохранен во внутренней истории и TXT-файле:\n{filepath}",
            QMessageBox.StandardButton.Ok,
        )

    # ---- Адаптивность ----

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._update_window_mask()
            self._refresh_window_controls()
        elif event.type() == QEvent.Type.WindowTitleChange and hasattr(self, "title_label"):
            self.title_label.setText(self.windowTitle())

    def showEvent(self, event):
        super().showEvent(event)
        self._update_window_mask()
        self._polish_visible_controls()
        QTimer.singleShot(0, self._polish_visible_controls)
        QTimer.singleShot(120, self._polish_visible_controls)

    def eventFilter(self, watched, event):
        if watched in self._title_drag_widgets:
            if event.type() == QEvent.Type.MouseButtonDblClick and event.button() == Qt.MouseButton.LeftButton:
                self._toggle_window_maximized()
                return True
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                return True
            if event.type() == QEvent.Type.MouseMove and self._drag_start_position is not None:
                if self.isMaximized():
                    self.showNormal()
                    self._drag_start_position = QPoint(self.width() // 2, 18)
                self.move(event.globalPosition().toPoint() - self._drag_start_position)
                return True
            if event.type() == QEvent.Type.MouseButtonRelease:
                self._drag_start_position = None
                return True
        return super().eventFilter(watched, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_window_mask()
        self._update_responsive_layout()
        if hasattr(self, "size_grip"):
            grip_size = self.size_grip.size()
            self.size_grip.move(
                self.window_shell.width() - grip_size.width() - 4,
                self.window_shell.height() - grip_size.height() - 4,
            )
            self.size_grip.setVisible(not self.isMaximized() and not self.isFullScreen())

    def closeEvent(self, event):
        self.save_session_cache()
        tray_icon = getattr(self, "_tray_icon", None)
        close_to_tray = bool(getattr(self, "_close_to_tray", False))
        force_quit = bool(getattr(self, "_force_quit", False))
        if close_to_tray and not force_quit and tray_icon is not None and tray_icon.isVisible():
            event.ignore()
            self.hide()
            if not getattr(self, "_tray_hint_shown", False):
                tray_icon.showMessage(
                    "Конструктор отчетов",
                    "Программа продолжает работать в трее.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2200,
                )
                self._tray_hint_shown = True
            return
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

        if hasattr(self, "toolbar_layout"):
            if dense_mode:
                toolbar_widths = {
                    self.add_btn: 104,
                    self.remove_last_btn: 112,
                    self.save_btn: 164,
                    self.open_report_btn: 144,
                    self.open_file_btn: 116,
                    self.reset_cache_btn: 158,
                }
                self.sections_label.setFixedWidth(84)
                self.toolbar_layout.setSpacing(6)
                self.toolbar_gap.changeSize(8, 1, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
            else:
                toolbar_widths = {
                    self.add_btn: 112,
                    self.remove_last_btn: 120,
                    self.save_btn: 178,
                    self.open_report_btn: 154,
                    self.open_file_btn: 126,
                    self.reset_cache_btn: 170,
                }
                self.sections_label.setFixedWidth(88)
                self.toolbar_layout.setSpacing(8)
                self.toolbar_gap.changeSize(12, 1, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

            for button, width in toolbar_widths.items():
                button.setFixedWidth(width)
            self.toolbar_layout.invalidate()

        if self._base_stylesheet:
            self.setStyleSheet(self._compose_stylesheet())
