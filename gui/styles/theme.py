"""
Theme stylesheet for the GUI application.

Responsibility: Central QSS stylesheet with light analytical theme colors.
Focus: Informative clarity, data readability, professional workspace.
"""
from PyQt6.QtWidgets import QApplication


# Color palette - Light Analytical Theme
COLORS = {
    # Main backgrounds
    "bg_main": "#EEF2F7",
    "bg_surface": "#FFFFFF",
    "bg_subtle": "#F7F9FC",
    "bg_input": "#FFFFFF",
    "bg_table": "#FFFFFF",
    "bg_table_alt": "#FAFBFD",
    "bg_header": "#E3EAF3",

    # Borders
    "border": "#C9D3E0",
    "border_soft": "#D9E1EC",

    # Text
    "text_primary": "#1F2937",
    "text_secondary": "#5B6B7F",
    "text_muted": "#7B8794",
    "text_disabled": "#A0AEC0",

    # Accent
    "accent": "#4A7CCF",
    "accent_hover": "#3E6FBE",
    "accent_soft": "#E8F0FB",

    # Scores
    "score_high": "#5FA777",
    "score_mid": "#D9A441",
    "score_low": "#C96A5A",

    # Review status
    "status_pending": "#8A94A6",
    "status_needs_fix": "#C96A5A",
    "status_reviewed": "#5FA777",
    "status_fixed": "#4A90C2",

    # Flags
    "flag_error": "#C96A5A",
    "flag_warning": "#D9A441",
    "flag_ok": "#5FA777",
}


def build_stylesheet() -> str:
    """
    Build and return the complete QSS stylesheet.

    Returns:
        str: Complete QSS stylesheet string.
    """
    c = COLORS

    return f"""
/* ====== Global ====== */
QMainWindow, QWidget {{
    background: {c['bg_main']};
    color: {c['text_primary']};
    font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}

/* ====== Tab Widget ====== */
QTabWidget::pane {{
    background: {c['bg_surface']};
    border: 1px solid {c['border']};
}}

QTabBar::tab {{
    background: {c['bg_main']};
    color: {c['text_secondary']};
    padding: 10px 20px;
    border: none;
    border-bottom: 3px solid transparent;
}}

QTabBar::tab:selected {{
    color: {c['text_primary']};
    border-bottom: 3px solid {c['accent']};
    background: {c['bg_surface']};
}}

QTabBar::tab:hover:!selected {{
    background: {c['accent_soft']};
}}

/* ====== Group Box ====== */
QGroupBox {{
    border: 1px solid {c['border']};
    border-radius: 6px;
    margin-top: 10px;
    padding: 12px;
    font-weight: 600;
    color: {c['text_secondary']};
}}

QGroupBox::title {{
    color: {c['text_primary']};
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}

/* ====== Inputs ====== */
QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border_soft']};
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 28px;
}}

QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {{
    border: 1px solid {c['accent']};
}}

QLineEdit:disabled, QPlainTextEdit:disabled {{
    color: {c['text_disabled']};
    background: {c['bg_main']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

/* ====== Buttons ====== */
QPushButton {{
    background: {c['bg_surface']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 5px 14px;
    min-height: 28px;
}}

QPushButton:hover {{
    border: 1px solid {c['accent']};
    background: {c['accent_soft']};
}}

QPushButton:pressed {{
    background: #d4e0f0;
}}

QPushButton:disabled {{
    color: {c['text_disabled']};
    border-color: {c['border_soft']};
    background: {c['bg_main']};
}}

QPushButton#primary {{
    background: {c['accent']};
    color: #ffffff;
    border: none;
    font-weight: 600;
}}

QPushButton#primary:hover {{
    background: {c['accent_hover']};
}}

QPushButton#primary:disabled {{
    background: #a0b8d8;
    color: #ffffff;
}}

QPushButton#danger {{
    background: {c['flag_error']};
    color: #ffffff;
    border: none;
}}

QPushButton#danger:hover {{
    background: #b55a4a;
}}

/* ====== Table ====== */
QTableView {{
    background: {c['bg_table']};
    alternate-background-color: {c['bg_table_alt']};
    color: {c['text_primary']};
    gridline-color: {c['border_soft']};
    border: 1px solid {c['border_soft']};
    selection-background-color: {c['accent_soft']};
}}

QTableView::item {{
    padding: 4px 8px;
}}

QTableView::item:selected {{
    background: {c['accent_soft']};
}}

QHeaderView::section {{
    background: {c['bg_header']};
    color: {c['text_secondary']};
    font-weight: 600;
    font-size: 12px;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid {c['border_soft']};
    border-bottom: 1px solid {c['border']};
}}

/* ====== Scrollbar ====== */
QScrollBar:vertical {{
    background: {c['bg_main']};
    width: 8px;
}}

QScrollBar::handle:vertical {{
    background: {c['border']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {c['accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {c['bg_main']};
    height: 8px;
}}

QScrollBar::handle:horizontal {{
    background: {c['border']};
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ====== Progress Bar ====== */
QProgressBar {{
    background: {c['bg_subtle']};
    border: 1px solid {c['border_soft']};
    border-radius: 4px;
    min-height: 16px;
    text-align: center;
    color: {c['text_primary']};
    font-size: 11px;
}}

QProgressBar::chunk {{
    background: {c['accent']};
    border-radius: 4px;
}}

/* ====== Log Panel ====== */
QPlainTextEdit#log_panel {{
    background: {c['bg_subtle']};
    font-family: "Consolas", "JetBrains Mono", "Courier New", monospace;
    font-size: 12px;
    color: {c['text_primary']};
    border: 1px solid {c['border_soft']};
}}

/* ====== Status Labels ====== */
QLabel#status_idle {{
    color: {c['text_secondary']};
    font-weight: 600;
}}

QLabel#status_running {{
    color: {c['accent']};
    font-weight: 600;
}}

QLabel#status_done {{
    color: {c['score_high']};
    font-weight: 600;
}}

QLabel#status_error {{
    color: {c['score_low']};
    font-weight: 600;
}}

QLabel#status_stopped {{
    color: {c['score_mid']};
    font-weight: 600;
}}

/* ====== Status Bar ====== */
QStatusBar {{
    background: {c['bg_header']};
    color: {c['text_secondary']};
    border-top: 1px solid {c['border']};
}}

/* ====== Tooltip ====== */
QToolTip {{
    background: {c['text_primary']};
    color: #ffffff;
    border: none;
    padding: 4px 8px;
    border-radius: 3px;
    font-size: 12px;
}}

/* ====== Checkbox ====== */
QCheckBox {{
    color: {c['text_primary']};
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {c['border_soft']};
    border-radius: 3px;
    background: {c['bg_input']};
}}

QCheckBox::indicator:checked {{
    background: {c['accent']};
    border-color: {c['accent']};
}}

/* ====== List Widget ====== */
QListWidget {{
    background: {c['bg_surface']};
    color: {c['text_primary']};
    border: 1px solid {c['border_soft']};
}}

/* ====== Splitter ====== */
QSplitter::handle {{
    background: {c['border_soft']};
}}

/* ====== Menu ====== */
QMenuBar {{
    background: {c['bg_header']};
    color: {c['text_primary']};
    border-bottom: 1px solid {c['border_soft']};
}}

QMenuBar::item:selected {{
    background: {c['bg_surface']};
}}

QMenu {{
    background: {c['bg_surface']};
    color: {c['text_primary']};
    border: 1px solid {c['border_soft']};
}}

QMenu::item:selected {{
    background: {c['accent']};
}}
"""


def apply_theme(app: QApplication) -> None:
    """
    Apply the light analytical theme stylesheet to the entire application.

    Args:
        app: QApplication instance to apply the theme to.
    """
    app.setStyle("Fusion")
    app.setStyleSheet(build_stylesheet())