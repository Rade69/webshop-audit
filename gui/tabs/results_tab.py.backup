"""
Results tab for displaying audit results.

Responsibility: Working screen for viewing, filtering, and analyzing
audit results. Shows table with scores, details panel, and actions.
"""
import csv
import os

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSlot, QSortFilterProxyModel, QUrl, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QDesktopServices
from PyQt6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QScrollArea,
    QFrame,
    QSplitter,
    QAbstractItemView,
    QHeaderView,
)
from PyQt6.QtCore import pyqtSignal

from gui.controllers.results_controller import ResultsController


class ResultsTableModel(QAbstractTableModel):
    """
    Table model for audit results.

    Displays: URL/Title, Catalog Score, Machine Score, Commerce Score,
    Overall Score, Flags, Review Status.
    """

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._data = data if data is not None else []
        self._columns = [
            "title",
            "catalog_score",
            "machine_score",
            "commerce_score",
            "overall_score",
            "flags",
            "review_status"
        ]
        self._headers = [
            "Naslov",     # "Title"
            "Katalog",    # "Catalog"
            "Mašina",     # "Machine"
            "Commerce",   # "Commerce"
            "Ukupno",     # "Overall"
            "Oznake",     # "Flags"
            "Revizija"    # "Review"
        ]

    def update_data(self, data):
        """Update table data."""
        self.beginResetModel()
        self._data = data if data is not None else []
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self._data):
            return None

        product = self._data[row]
        col_name = self._columns[col]

        if role == Qt.ItemDataRole.DisplayRole:
            if col_name == "title":
                title = str(product.get("title", "") or product.get("url", "") or "")
                return title[:50] + "..." if len(title) > 50 else title
            elif col_name in ["catalog_score", "machine_score", "commerce_score", "overall_score"]:
                return product.get(col_name, "-")
            elif col_name == "flags":
                flags = []
                if product.get("flag_js_rendered"):
                    flags.append("JS")
                if product.get("flag_noindex"):
                    flags.append("noindex")
                if product.get("flag_canonical_mismatch"):
                    flags.append("no-canonical")
                if product.get("suspicious_price_missing"):
                    flags.append("no-price")
                if product.get("suspicious_schema_missing"):
                    flags.append("no-schema")
                return ", ".join(flags) if flags else "-"
            elif col_name == "review_status":
                return product.get("review_status", "-")

        elif role == Qt.ItemDataRole.BackgroundRole:
            # Color coding based on issues
            has_critical = product.get("flag_noindex") or (
                product.get("suspicious_price_missing") and product.get("suspicious_schema_missing")
            )
            has_warning = product.get("flag_js_rendered") or product.get("flag_canonical_mismatch")

            if has_critical:
                return QColor("#ffebee")  # Light red
            elif has_warning:
                return QColor("#fff8e1")  # Light yellow

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col_name in ["catalog_score", "machine_score", "commerce_score", "overall_score"]:
                return Qt.AlignmentFlag.AlignCenter

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if section < len(self._headers):
                return self._headers[section]
        return None

    def get_product(self, row: int) -> dict:
        """Get product data at row."""
        if 0 <= row < len(self._data):
            return self._data[row]
        return {}


class ResultsFilterModel(QSortFilterProxyModel):
    """
    Sort and filter proxy model for results table.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._min_score = 0
        self._max_score = 100
        self._filter_missing_schema = False
        self._filter_missing_price = False
        self._filter_noindex = False
        self._filter_canonical_mismatch = False
        self._filter_shortlist_only = False
        self._show_non_product = True
        self._search_text = ""
        self._category = ""

    def set_filters(self, min_score=0, max_score=100, missing_schema=False,
                    missing_price=False, noindex=False, canonical_mismatch=False,
                    shortlist_only=False, show_non_product=True, search_text="",
                    category=""):
        """Set filter parameters."""
        self._min_score = min_score
        self._max_score = max_score
        self._filter_missing_schema = missing_schema
        self._filter_missing_price = missing_price
        self._filter_noindex = noindex
        self._filter_canonical_mismatch = canonical_mismatch
        self._filter_shortlist_only = shortlist_only
        self._show_non_product = show_non_product
        self._search_text = search_text.lower()
        self._category = category
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        source_model = self.sourceModel()
        if not source_model:
            return True

        product = source_model.get_product(source_row)

        # Score filter
        overall = product.get("overall_score", 0)
        if overall < self._min_score or overall > self._max_score:
            return False

        # Missing schema filter
        if self._filter_missing_schema and product.get("schema_product_present"):
            return False

        # Missing price filter
        if self._filter_missing_price:
            has_price = product.get("html_price_text") or product.get("schema_price")
            if has_price:
                return False

        # Noindex filter
        if self._filter_noindex and not product.get("flag_noindex"):
            return False

        # Canonical issues filter
        if self._filter_canonical_mismatch and not product.get("flag_canonical_mismatch"):
            return False

        # Shortlist only filter
        if self._filter_shortlist_only and not product.get("candidate"):
            return False

        # Non-product filter
        if not self._show_non_product and not product.get("is_likely_product_page", True):
            return False

        # Category filter
        if self._category:
            breadcrumb = product.get("breadcrumb_text", "")
            if self._category not in breadcrumb:
                return False

        # Search filter
        if self._search_text:
            search_fields = [
                str(product.get("url", "")),
                str(product.get("title", "")),
                str(product.get("schema_sku", "")),
                str(product.get("schema_gtin", ""))
            ]
            if not any(self._search_text in f.lower() for f in search_fields):
                return False

        return True


class _ReportWorker(QThread):
    """Pozadinski thread za generisanje Word izvještaja — ne blokira GUI."""
    finished = pyqtSignal(str)   # report_path
    failed   = pyqtSignal(str)   # error message

    def __init__(self, output_dir: str):
        super().__init__()
        self.output_dir = output_dir

    def run(self):
        try:
            from audit.report_generator import generate_report
            path = generate_report(self.output_dir)
            self.finished.emit(path)
        except Exception as e:
            self.failed.emit(str(e))


class ResultsTab(QWidget):
    """
    Results tab for displaying audit results.

    Shows table with scores, details panel, filters, and actions.
    """

    # Signal for requesting review
    mark_for_review_requested = pyqtSignal(str)  # URL

    def __init__(self, results_controller: ResultsController, parent=None):
        """
        Initialize ResultsTab.

        Args:
            results_controller: ResultsController instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.results_controller = results_controller
        self._current_url = ""

        # UI setup
        self._setup_ui()
        self._connect_signals()
        self._set_empty_state()

    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Filter bar — u GroupBox-u
        filter_group = QGroupBox("Filteri")  # "Filters"
        filter_group_layout = QVBoxLayout(filter_group)
        filter_group_layout.setContentsMargins(8, 8, 8, 8)
        filter_group_layout.setSpacing(0)
        filter_bar = self._create_filter_bar()
        filter_group_layout.addWidget(filter_bar)
        layout.addWidget(filter_group)

        # Splitter: tabela + detalji panel
        splitter = QSplitter(Qt.Orientation.Horizontal)

        table_container = self._create_table_view()
        splitter.addWidget(table_container)

        details_panel = self._create_details_panel()
        splitter.addWidget(details_panel)

        splitter.setSizes([650, 400])
        layout.addWidget(splitter, 1)  # stretch — popuni ostatak prostora

        # Action buttons
        actions = self._create_actions()
        layout.addWidget(actions)

    def _create_filter_bar(self) -> QWidget:
        """Create filter bar widget — dva reda."""
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # ── Red 1: kategorija, ocjena, checkboxovi ────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        row1.addWidget(QLabel("Kategorija:"))  # "Category:"
        self.category_combo = QComboBox()
        self.category_combo.addItem("Sve", "")  # "All"
        self.category_combo.currentTextChanged.connect(self._on_filter_changed)
        self.category_combo.setFixedWidth(130)
        row1.addWidget(self.category_combo)

        row1.addWidget(QLabel("Ocjena:"))  # "Score:"
        self.min_score_spin = QSpinBox()
        self.min_score_spin.setRange(0, 100)
        self.min_score_spin.setValue(0)
        self.min_score_spin.setPrefix("Min: ")
        self.min_score_spin.setFixedWidth(80)
        self.min_score_spin.valueChanged.connect(self._on_filter_changed)
        row1.addWidget(self.min_score_spin)

        self.max_score_spin = QSpinBox()
        self.max_score_spin.setRange(0, 100)
        self.max_score_spin.setValue(100)
        self.max_score_spin.setPrefix("Max: ")
        self.max_score_spin.setFixedWidth(80)
        self.max_score_spin.valueChanged.connect(self._on_filter_changed)
        row1.addWidget(self.max_score_spin)

        row1.addStretch()

        row1.addWidget(QLabel("Pretraga:"))  # "Search:"
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("URL, naslov, SKU, GTIN...")
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.setMinimumWidth(220)
        row1.addWidget(self.search_input)

        self.reset_filters_btn = QPushButton("Resetuj")  # "Reset"
        self.reset_filters_btn.clicked.connect(self._on_reset_filters)
        row1.addWidget(self.reset_filters_btn)

        main_layout.addLayout(row1)

        # ── Red 2: checkbox filteri ───────────────────────────────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        self.missing_schema_cb = QCheckBox("Nema sheme")  # "Missing Schema"
        self.missing_schema_cb.stateChanged.connect(self._on_filter_changed)
        row2.addWidget(self.missing_schema_cb)

        self.missing_price_cb = QCheckBox("Nema cijene")  # "Missing Price"
        self.missing_price_cb.stateChanged.connect(self._on_filter_changed)
        row2.addWidget(self.missing_price_cb)

        self.noindex_cb = QCheckBox("Noindex")
        self.noindex_cb.stateChanged.connect(self._on_filter_changed)
        row2.addWidget(self.noindex_cb)

        self.canonical_cb = QCheckBox("Problem canonical")  # "Canonical Issues"
        self.canonical_cb.stateChanged.connect(self._on_filter_changed)
        row2.addWidget(self.canonical_cb)

        self.shortlist_cb = QCheckBox("Samo kratka lista")  # "Shortlist Only"
        self.shortlist_cb.stateChanged.connect(self._on_filter_changed)
        row2.addWidget(self.shortlist_cb)

        self.show_non_product_cb = QCheckBox("Prikaži ne-proizvode")  # "Show Non-Product"
        self.show_non_product_cb.setChecked(True)
        self.show_non_product_cb.stateChanged.connect(self._on_filter_changed)
        row2.addWidget(self.show_non_product_cb)

        row2.addStretch()
        main_layout.addLayout(row2)

        return widget

    def _create_table_view(self) -> QWidget:
        """Create table view widget."""
        from gui.widgets.delegates import ScoreDelegate, FlagDelegate

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Table view
        self.table_view = QTableView()
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.clicked.connect(self._on_row_clicked)

        # Model
        self.table_model = ResultsTableModel()
        self.filter_model = ResultsFilterModel()
        self.filter_model.setSourceModel(self.table_model)
        self.table_view.setModel(self.filter_model)

        # Set delegates for score columns (1-4: catalog, machine, commerce, overall)
        self.score_delegate = ScoreDelegate(self.table_view)
        for col in range(1, 5):
            self.table_view.setItemDelegateForColumn(col, self.score_delegate)

        # Set delegate for flags column (5: flags)
        self.flag_delegate = FlagDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(5, self.flag_delegate)

        # Additional table styling
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setDefaultSectionSize(32)
        self.table_view.verticalHeader().setVisible(False)

        layout.addWidget(self.table_view)

        # Count label
        self.count_label = QLabel("0 proizvoda")  # "0 products"
        layout.addWidget(self.count_label)

        return container

    def _create_details_panel(self) -> QWidget:
        """Create details panel widget."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(350)

        container = QWidget()
        layout = QVBoxLayout(container)

        # Page info section
        page_group = QGroupBox("Informacije o stranici")  # "Page Info"
        page_layout = QFormLayout(page_group)
        self.detail_url = QLabel("-")
        self.detail_url.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.detail_title = QLabel("-")
        self.detail_h1 = QLabel("-")
        self.detail_canonical = QLabel("-")
        self.detail_robots = QLabel("-")
        page_layout.addRow("URL:", self.detail_url)
        page_layout.addRow("Naslov:", self.detail_title)  # "Title:"
        page_layout.addRow("H1:", self.detail_h1)
        page_layout.addRow("Canonical:", self.detail_canonical)
        page_layout.addRow("Robots:", self.detail_robots)
        layout.addWidget(page_group)

        # Schema section
        schema_group = QGroupBox("Shema")  # "Schema"
        schema_layout = QFormLayout(schema_group)
        self.detail_schema_product = QLabel("-")
        self.detail_schema_offer = QLabel("-")
        self.detail_price_schema = QLabel("-")
        self.detail_currency = QLabel("-")
        self.detail_availability = QLabel("-")
        self.detail_sku = QLabel("-")
        self.detail_gtin = QLabel("-")
        self.detail_brand = QLabel("-")
        schema_layout.addRow("Proizvod:", self.detail_schema_product)  # "Product:"
        schema_layout.addRow("Ponuda:", self.detail_schema_offer)  # "Offer:"
        schema_layout.addRow("Cijena:", self.detail_price_schema)  # "Price:"
        schema_layout.addRow("Valuta:", self.detail_currency)  # "Currency:"
        schema_layout.addRow("Dostupnost:", self.detail_availability)  # "Availability:"
        schema_layout.addRow("SKU:", self.detail_sku)
        schema_layout.addRow("GTIN:", self.detail_gtin)
        schema_layout.addRow("Brend:", self.detail_brand)  # "Brand:"
        layout.addWidget(schema_group)

        # Signals section
        signals_group = QGroupBox("Signali")  # "Signals"
        signals_layout = QFormLayout(signals_group)
        self.detail_price_html = QLabel("-")
        self.detail_shipping = QLabel("-")
        self.detail_returns = QLabel("-")
        self.detail_images = QLabel("-")
        self.detail_text_length = QLabel("-")
        signals_layout.addRow("HTML cijena:", self.detail_price_html)  # "HTML Price:"
        signals_layout.addRow("Dostava:", self.detail_shipping)  # "Shipping:"
        signals_layout.addRow("Povrati:", self.detail_returns)  # "Returns:"
        signals_layout.addRow("Slike:", self.detail_images)  # "Images:"
        signals_layout.addRow("Dužina teksta:", self.detail_text_length)  # "Text Length:"
        layout.addWidget(signals_group)

        # Flags section
        flags_group = QGroupBox("Oznake")  # "Flags"
        flags_layout = QFormLayout(flags_group)
        self.detail_flags = QLabel("-")
        flags_layout.addRow("Problemi:", self.detail_flags)  # "Issues:"
        layout.addWidget(flags_group)

        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _create_actions(self) -> QWidget:
        """Create action buttons widget."""
        widget = QWidget()
        widget.setObjectName("action_bar")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.open_page_btn = QPushButton("Otvori stranicu")  # "Open Page"
        self.open_page_btn.setEnabled(False)
        self.open_page_btn.clicked.connect(self._on_open_page)

        self.mark_review_btn = QPushButton("Označi za ručnu reviziju")  # "Mark for Manual Review"
        self.mark_review_btn.setEnabled(False)
        self.mark_review_btn.clicked.connect(self._on_mark_review)

        self.export_btn = QPushButton("Izvezi odabrano")  # "Export Selected"
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._on_export)

        self.report_btn = QPushButton("Generiši izvještaj")  # "Generate Report"
        self.report_btn.setObjectName("primary")
        self.report_btn.setEnabled(False)
        self.report_btn.setToolTip("Generiše Word (.docx) izvještaj iz trenutnih rezultata")
        self.report_btn.clicked.connect(self._on_generate_report)

        layout.addWidget(self.open_page_btn)
        layout.addWidget(self.mark_review_btn)
        layout.addWidget(self.export_btn)
        layout.addStretch()
        layout.addWidget(self.report_btn)

        return widget

    def _connect_signals(self):
        """Connect signals."""
        self.results_controller.results_loaded.connect(self._on_results_loaded)
        self.results_controller.filter_changed.connect(self._on_filter_refresh)
        self.results_controller.selection_changed.connect(self._on_selection_changed)

    def _set_empty_state(self):
        """Set empty state."""
        self.table_model.update_data([])
        self._update_count(0)
        self._clear_details()
        self._set_buttons_enabled(False)

    def _set_buttons_enabled(self, enabled: bool):
        """Enable/disable action buttons."""
        self.open_page_btn.setEnabled(enabled)
        self.mark_review_btn.setEnabled(enabled)
        self.export_btn.setEnabled(enabled)

    def _clear_details(self):
        """Clear details panel."""
        self.detail_url.setText("-")
        self.detail_title.setText("-")
        self.detail_h1.setText("-")
        self.detail_canonical.setText("-")
        self.detail_robots.setText("-")
        self.detail_schema_product.setText("-")
        self.detail_schema_offer.setText("-")
        self.detail_price_schema.setText("-")
        self.detail_currency.setText("-")
        self.detail_availability.setText("-")
        self.detail_sku.setText("-")
        self.detail_gtin.setText("-")
        self.detail_brand.setText("-")
        self.detail_price_html.setText("-")
        self.detail_shipping.setText("-")
        self.detail_returns.setText("-")
        self.detail_images.setText("-")
        self.detail_text_length.setText("-")
        self.detail_flags.setText("-")

    def _update_count(self, count: int):
        """Update product count label."""
        self.count_label.setText(f"{count} proizvoda")  # "{count} products"

    def _on_results_loaded(self):
        """Handle results loaded signal."""
        df = self.results_controller.get_filtered_data()
        self.table_model.update_data(df.to_dict('records'))
        self._update_count(len(df))

        # Enable export and report as soon as data is loaded
        self.export_btn.setEnabled(True)
        self.report_btn.setEnabled(True)

        # Update category dropdown
        categories = self.results_controller.get_categories()
        self.category_combo.clear()
        self.category_combo.addItem("Sve", "")  # "All"
        for cat in categories:
            self.category_combo.addItem(cat, cat)

    def _on_filter_changed(self):
        """Handle filter changes."""
        self.filter_model.set_filters(
            min_score=self.min_score_spin.value(),
            max_score=self.max_score_spin.value(),
            missing_schema=self.missing_schema_cb.isChecked(),
            missing_price=self.missing_price_cb.isChecked(),
            noindex=self.noindex_cb.isChecked(),
            canonical_mismatch=self.canonical_cb.isChecked(),
            shortlist_only=self.shortlist_cb.isChecked(),
            show_non_product=self.show_non_product_cb.isChecked(),
            search_text=self.search_input.text(),
            category=self.category_combo.currentData()
        )

    def _on_search_changed(self, text: str):
        """Handle search text changes."""
        self._on_filter_changed()

    def _on_filter_refresh(self):
        """Handle filter refresh from controller."""
        df = self.results_controller.get_filtered_data()
        self.table_model.update_data(df.to_dict('records'))
        self._update_count(len(df))

    def _on_reset_filters(self):
        """Reset all filters."""
        self.category_combo.setCurrentIndex(0)
        self.min_score_spin.setValue(0)
        self.max_score_spin.setValue(100)
        self.missing_schema_cb.setChecked(False)
        self.missing_price_cb.setChecked(False)
        self.noindex_cb.setChecked(False)
        self.canonical_cb.setChecked(False)
        self.shortlist_cb.setChecked(False)
        self.show_non_product_cb.setChecked(True)
        self.search_input.clear()
        self._on_filter_changed()

    @pyqtSlot(QModelIndex)
    def _on_row_clicked(self, index: QModelIndex):
        """Handle row click."""
        source_row = self.filter_model.mapToSource(index).row()
        product = self.table_model.get_product(source_row)
        self._current_url = product.get("url", "")
        self._show_details(product)
        self._set_buttons_enabled(True)

    def _on_selection_changed(self, product_data: dict):
        """Handle selection changed from controller."""
        self._show_details(product_data)

    def _show_details(self, product: dict):
        """Show product details in panel."""
        # Page info
        self.detail_url.setText(f'<a href="{product.get("url", "")}">{product.get("url", "-")}</a>')
        self.detail_title.setText(str(product.get("title", "-")))
        self.detail_h1.setText(str(product.get("h1", "-")))
        self.detail_canonical.setText(str(product.get("canonical", "-")))
        self.detail_robots.setText(str(product.get("robots_meta", "-")))

        def _yn(val) -> str:
            """Pretvara truthy vrijednost u Da/Ne, ignorira pandas NaN/None."""
            if val is None:
                return "Ne"
            try:
                import math
                if isinstance(val, float) and math.isnan(val):
                    return "Ne"
            except Exception:
                pass
            return "Da" if val else "Ne"

        def _val(key, default="-") -> str:
            v = product.get(key)
            if v is None:
                return default
            try:
                import math
                if isinstance(v, float) and math.isnan(v):
                    return default
            except Exception:
                pass
            s = str(v).strip()
            return s if s and s.lower() != "nan" else default

        # Schema — ispravna imena kolona iz extractor.py
        self.detail_schema_product.setText(_yn(product.get("schema_product_present")))
        self.detail_schema_offer.setText(_yn(product.get("schema_offer_present")))
        self.detail_price_schema.setText(_val("schema_price", "nije pronađeno"))
        self.detail_currency.setText(_val("schema_currency"))
        self.detail_availability.setText(_val("schema_availability"))
        self.detail_sku.setText(_val("schema_sku"))
        self.detail_gtin.setText(_val("schema_gtin"))
        self.detail_brand.setText(_val("schema_brand"))

        # Signals — ispravna imena kolona
        self.detail_price_html.setText(_val("html_price_text", "nije pronađeno"))
        self.detail_shipping.setText(_yn(product.get("shipping_signal")))
        self.detail_returns.setText(_yn(product.get("returns_signal")))
        self.detail_images.setText(_val("image_count", "0"))
        self.detail_text_length.setText(_val("visible_text_length", "0"))

        # Flags — iz indexability_flags kolone i boolean signala
        flags = []
        if product.get("is_likely_js_rendered"):
            flags.append("JS renderovano")
        idx_flags = _val("indexability_flags", "")
        if "noindex" in idx_flags.lower():
            flags.append("Noindex")
        if "canonical" in idx_flags.lower():
            flags.append("Canonical mismatch")
        if not product.get("schema_product_present"):
            flags.append("Nema sheme")
        if not product.get("schema_price") and _val("schema_price", "") == "-":
            flags.append("Nema cijene u schema")
        self.detail_flags.setText(", ".join(flags) if flags else "Nema")

    def _on_open_page(self):
        """Open selected page in browser."""
        if self._current_url:
            QDesktopServices.openUrl(QUrl(self._current_url))

    def _on_mark_review(self):
        """Mark product for manual review."""
        if self._current_url:
            self.mark_for_review_requested.emit(self._current_url)

    def _on_export(self):
        """Export currently visible (filtered) rows to CSV."""
        row_count = self.filter_model.rowCount()
        if not row_count:
            QMessageBox.information(self, "Izvoz", "Nema redova za izvoz.")  # "Export", "No rows to export."
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Izvezi filtrirane rezultate",  # "Export Filtered Results"
            "results_filtered.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        # Collect all rows visible after both controller-level and UI-level filtering
        rows = []
        for proxy_row in range(row_count):
            source_row = self.filter_model.mapToSource(
                self.filter_model.index(proxy_row, 0)
            ).row()
            rows.append(self.table_model.get_product(source_row))

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                if rows:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
            QMessageBox.information(
                self, "Izvoz", f"Izvezeno {len(rows)} redova u:\n{file_path}"  # "Export", "Exported {n} rows to:\n{path}"
            )
        except OSError as e:
            QMessageBox.critical(self, "Greška pri izvozu", str(e))  # "Export Error"

    def _on_generate_report(self):
        """Pokreće generisanje Word izvještaja u pozadinskom threadu."""
        output_dir = self.results_controller.get_output_dir()
        if not output_dir:
            QMessageBox.warning(self, "Izvještaj", "Nema učitanih rezultata.")
            return

        self.report_btn.setEnabled(False)
        self.report_btn.setText("Generišem...")

        self._report_worker = _ReportWorker(output_dir)
        self._report_worker.finished.connect(self._on_report_finished)
        self._report_worker.failed.connect(self._on_report_failed)
        self._report_worker.start()

    def _on_report_finished(self, report_path: str):
        self.report_btn.setEnabled(True)
        self.report_btn.setText("Generiši izvještaj")
        QMessageBox.information(
            self,
            "Izvještaj generisan",
            f"Word izvještaj sačuvan:\n{report_path}",
        )
        # Otvori folder koji sadrži izvještaj
        folder = os.path.dirname(os.path.abspath(report_path))
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _on_report_failed(self, error: str):
        self.report_btn.setEnabled(True)
        self.report_btn.setText("Generiši izvještaj")
        QMessageBox.critical(self, "Greška pri generisanju", error)