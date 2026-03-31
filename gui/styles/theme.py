"""
GUI tema — Soft Sage & Deep Blue.

Paleta boja: trijadna (zelena/plava/narandžasta), optimizovana za dugotrajan rad.
Primarna boja: #26629E (Deep Blue, korisničke specifikacije).
Pozadinska osnova: #EFF6F1 (Soft Sage — odmor za oči, bez sivila).
"""
import os

from PyQt6.QtWidgets import QApplication

_ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
_UP_ARROW   = os.path.join(_ASSETS, "arrow_up.svg").replace("\\", "/")
_DOWN_ARROW = os.path.join(_ASSETS, "arrow_down.svg").replace("\\", "/")


# ── Paleta boja ────────────────────────────────────────────────────────────────
COLORS = {
    # Pozadine — "Mliječna Žalfija"
    "bg_main":       "#EFF6F1",   # Osnova cijele aplikacije
    "bg_surface":    "#FFFFFF",   # Kartice, paneli, grupboxovi
    "bg_input":      "#F9FBF9",   # Input polja (blaga mint nijansa)
    "bg_table":      "#FFFFFF",
    "bg_table_alt":  "#E6F0E8",   # Alternativni red u tabeli
    "bg_header":     "#D8E5D8",   # Header tabele i status bar

    # Borderi
    "border":        "#D1D5DB",   # Diskretna siva

    # Tekst
    "text_primary":   "#1A1D21",  # Slate crna, mekša od čisto crne
    "text_secondary": "#4B5563",

    # Akcent — Deep Blue (korisničke specifikacije)
    "accent":         "#26629E",
    "accent_hover":   "#1D4E7F",
    "accent_light":   "#D8E5F0",  # Hover pozadina za dugmad

    # Status — Sunčana narandžasta (trijadni akcenat)
    "status_orange":     "#FF8C00",
    "status_orange_bg":  "#FFF7ED",
    "status_orange_border": "#FFEDD5",

    # Ocjene
    "score_high": "#2E7D32",   # Zelena
    "score_mid":  "#FF8C00",   # Narandžasta
    "score_low":  "#B53A3A",   # Crvena

    # Review status
    "status_pending":   "#8A94A6",
    "status_needs_fix": "#B53A3A",
    "status_reviewed":  "#2E7D32",
    "status_fixed":     "#26629E",

    # Zastavice
    "flag_error":   "#B53A3A",
    "flag_warning": "#FF8C00",
    "flag_ok":      "#2E7D32",
}


def build_stylesheet() -> str:
    """Gradi i vraća kompletan QSS stylesheet."""
    c = COLORS

    return f"""
/* ══ Globalno ══════════════════════════════════════════════════════════════ */
QMainWindow, QWidget {{
    background: {c['bg_main']};
    color: {c['text_primary']};
    font-family: "Inter", "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}

/* ══ Tab widget ═════════════════════════════════════════════════════════════*/
QTabWidget::pane {{
    background: {c['bg_surface']};
    border: 1px solid {c['border']};
    border-top: none;
}}

QTabBar {{
    background: {c['bg_main']};
}}

/* Glavni tab bar — veliki ispunjeni tabovi */
QTabBar::tab {{
    background: {c['bg_main']};
    color: {c['text_secondary']};
    padding: 9px 22px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background: {c['bg_surface']};
    color: {c['accent']};
    font-weight: bold;
    border-bottom: 3px solid {c['accent']};
}}

QTabBar::tab:hover:!selected {{
    background: {c['accent_light']};
    color: {c['accent']};
}}

/* Sub-tabovi unutar grupova — podcrtan stil, manji padding */
QGroupBox QTabBar::tab, QWidget QTabWidget QTabBar::tab {{
    padding: 6px 16px;
    font-weight: normal;
}}

QGroupBox QTabBar::tab:selected, QWidget QTabWidget QTabBar::tab:selected {{
    background: {c['bg_surface']};
    color: {c['accent']};
    border-bottom: 2px solid {c['accent']};
    font-weight: 600;
}}

/* ══ GroupBox ════════════════════════════════════════════════════════════════*/
QGroupBox {{
    background: {c['bg_surface']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    margin-top: 15px;
    padding: 15px;
    font-weight: bold;
    color: {c['text_secondary']};
}}

QGroupBox::title {{
    color: {c['text_primary']};
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
}}

/* ══ Input polja ═════════════════════════════════════════════════════════════*/
QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {c['bg_input']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 5px 8px;
    min-height: 28px;
}}

QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {c['accent']};
    background: #FFFFFF;
}}

QLineEdit:disabled, QPlainTextEdit:disabled, QSpinBox:disabled {{
    color: #A0AEC0;
    background: {c['bg_main']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid {c['border']};
    border-bottom: 1px solid {c['border']};
    border-top-right-radius: 4px;
    background: {c['bg_header']};
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border-left: 1px solid {c['border']};
    border-top: 1px solid {c['border']};
    border-bottom-right-radius: 4px;
    background: {c['bg_header']};
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {c['accent_light']};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url("{_UP_ARROW}");
    width: 10px;
    height: 6px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url("{_DOWN_ARROW}");
    width: 10px;
    height: 6px;
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background: {c['bg_surface']};
    border: 1px solid {c['border']};
    selection-background-color: {c['accent_light']};
}}

/* ══ Dugmad ══════════════════════════════════════════════════════════════════*/
QPushButton {{
    background: {c['bg_surface']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 30px;
    font-weight: 500;
}}

QPushButton:hover {{
    background: {c['accent_light']};
    border: 1px solid {c['accent']};
}}

QPushButton:pressed {{
    background: #c5d8ee;
}}

QPushButton:disabled {{
    color: #A0AEC0;
    border-color: #E5E7EB;
    background: {c['bg_main']};
}}

QPushButton#primary {{
    background: {c['accent']};
    color: #FFFFFF;
    border: none;
    font-weight: bold;
}}

QPushButton#primary:hover {{
    background: {c['accent_hover']};
}}

QPushButton#primary:disabled {{
    background: #7AAACF;
    color: #FFFFFF;
}}

/* ══ Status info box (sitemap/greška labela) ══════════════════════════════*/
QLabel#status_info_box {{
    background: {c['status_orange_bg']};
    color: {c['status_orange']};
    border: 1px solid {c['status_orange_border']};
    padding: 8px;
    border-radius: 6px;
    font-weight: 600;
}}

/* ══ Tabela ══════════════════════════════════════════════════════════════════*/
QTableView {{
    background: {c['bg_table']};
    alternate-background-color: {c['bg_table_alt']};
    color: {c['text_primary']};
    gridline-color: {c['border']};
    border: 1px solid {c['border']};
    selection-background-color: {c['accent_light']};
}}

QTableView::item {{
    padding: 4px 8px;
}}

QTableView::item:selected {{
    background: {c['accent_light']};
    color: {c['text_primary']};
}}

QHeaderView::section {{
    background: {c['bg_header']};
    color: {c['text_secondary']};
    font-weight: bold;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid {c['border']};
    border-bottom: 1px solid {c['border']};
}}

/* ══ Progress bar ═══════════════════════════════════════════════════════════*/
QProgressBar {{
    background: {c['bg_input']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    min-height: 16px;
    text-align: center;
    color: {c['text_primary']};
    font-size: 11px;
}}

QProgressBar::chunk {{
    background: {c['status_orange']};
    border-radius: 3px;
}}

/* ══ Scrollbar ═══════════════════════════════════════════════════════════════*/
QScrollBar:vertical {{
    background: {c['bg_main']};
    width: 8px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: {c['border']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {c['accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

QScrollBar:horizontal {{
    background: {c['bg_main']};
    height: 8px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: {c['border']};
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}

/* ══ Log panel ═══════════════════════════════════════════════════════════════*/
QPlainTextEdit#log_panel {{
    background: #F5FAF6;
    font-family: "JetBrains Mono", "Consolas", "Courier New", monospace;
    font-size: 12px;
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
}}

/* ══ Status labele ═══════════════════════════════════════════════════════════*/
QLabel#status_idle    {{ color: {c['text_secondary']}; font-weight: 600; }}
QLabel#status_running {{ color: {c['accent']};          font-weight: 600; }}
QLabel#status_done    {{ color: {c['score_high']};       font-weight: 600; }}
QLabel#status_error   {{ color: {c['score_low']};        font-weight: 600; }}
QLabel#status_stopped {{ color: {c['status_orange']};    font-weight: 600; }}

/* ══ Status bar ══════════════════════════════════════════════════════════════*/
QStatusBar {{
    background: {c['bg_header']};
    color: {c['text_secondary']};
    border-top: 1px solid {c['border']};
    font-size: 12px;
}}

/* ══ Tooltip ═════════════════════════════════════════════════════════════════*/
QToolTip {{
    background: {c['text_primary']};
    color: #FFFFFF;
    border: none;
    padding: 5px 9px;
    border-radius: 4px;
    font-size: 12px;
}}

/* ══ Checkbox ════════════════════════════════════════════════════════════════*/
QCheckBox {{ color: {c['text_primary']}; spacing: 6px; }}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {c['border']};
    border-radius: 3px;
    background: {c['bg_input']};
}}

QCheckBox::indicator:checked {{
    background: {c['accent']};
    border-color: {c['accent']};
}}

/* ══ List widget ═════════════════════════════════════════════════════════════*/
QListWidget {{
    background: {c['bg_surface']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background: {c['accent_light']};
}}

/* ══ Splitter ════════════════════════════════════════════════════════════════*/
QSplitter::handle {{
    background: {c['border']};
}}

/* ══ Scroll area ═════════════════════════════════════════════════════════════*/
QScrollArea {{
    border: none;
    background: transparent;
}}

/* ══ Action bar (pinned dugmad pri dnu tabova) ═══════════════════════════════*/
QWidget#action_bar {{
    background: {c['bg_surface']};
    border-top: 1px solid {c['border']};
    padding: 6px 0px;
}}
"""


def apply_theme(app: QApplication) -> None:
    """
    Primjenjuje Soft Sage & Deep Blue temu na cijelu aplikaciju.

    Args:
        app: QApplication instanca.
    """
    app.setStyle("Fusion")
    app.setStyleSheet(build_stylesheet())
