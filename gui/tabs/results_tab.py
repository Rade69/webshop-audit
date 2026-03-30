"""
Results tab for displaying audit results.

Responsibility: Working screen for viewing, filtering, and analyzing
audit results. Shows table with scores, details panel, and actions.
"""
import csv

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSlot, QSortFilterProxyModel, QUrl
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
            "Title",
            "Catalog",
            "Machine",
            "Commerce",
            "Overall",
            "Flags",
            "Review"
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
                title = product.get("title", product.get("url", ""))
                return title[:50] + "..." if len(title) > 50 else title
            elif col_name in ["catalog_score", "machine_score", "commerce_score", "overall_score"]:
                return product.get(col_name, "-")
            elif col_name == "flags":
                flags = []
                if product.get("flag_js_rendered"):
                    flags.append("JS")
                if product.get("flag_noindex"):
                    flags.append("noindex")
                if product.get("flag_canonical_missing"):
                    flags.append("no-canonical")
                if product.get("missing_price"):
                    flags.append("no-price")
                if product.get("missing_schema"):
                    flags.append("no-schema")
                return ", ".join(flags) if flags else "-"
            elif col_name == "review_status":
                return product.get("review_status", "-")

        elif role == Qt.ItemDataRole.BackgroundRole:
            # Color coding based on issues
            has_critical = product.get("flag_noindex") or (
                product.get("missing_price") and product.get("missing_schema")
            )
            has_warning = product.get("flag_js_rendered") or product.get("flag_canonical_missing")

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
        self._filter_canonical_issues = False
        self._filter_shortlist_only = False
        self._show_non_product = True
        self._search_text = ""
        self._category = ""

    def set_filters(self, min_score=0, max_score=100, missing_schema=False,
                    missing_price=False, noindex=False, canonical_issues=False,
                    shortlist_only=False, show_non_product=True, search_text="",
                    category=""):
        """Set filter parameters."""
        self._min_score = min_score
        self._max_score = max_score
        self._filter_missing_schema = missing_schema
        self._filter_missing_price = missing_price
        self._filter_noindex = noindex
        self._filter_canonical_issues = canonical_issues
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
        if self._filter_missing_schema and product.get("schema_product"):
            return False

        # Missing price filter
        if self._filter_missing_price:
            has_price = product.get("price_html") or product.get("price_schema")
            if has_price:
                return False

        # Noindex filter
        if self._filter_noindex and not product.get("flag_noindex"):
            return False

        # Canonical issues filter
        if self._filter_canonical_issues and not product.get("flag_canonical_missing"):
            return False

        # Shortlist only filter
        if self._filter_shortlist_only and not product.get("candidate"):
            return False

        # Non-product filter
        if not self._show_non_product and not product.get("is_product_page", True):
            return False

        # Category filter
        if self._category:
            breadcrumb = product.get("breadcrumb", "")
            if self._category not in breadcrumb:
                return False

        # Search filter
        if self._search_text:
            search_fields = [
                str(product.get("url", "")),
                str(product.get("title", "")),
                str(product.get("sku", "")),
                str(product.get("gtin", ""))
            ]
            if not any(self._search_text in f.lower() for f in search_fields):
                return False

        return True


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
        layout.setSpacing(10)

        # Filter bar
        filter_bar = self._create_filter_bar()
        layout.addWidget(filter_bar)

        # Main content: table + details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Table view
        table_container = self._create_table_view()
        splitter.addWidget(table_container)

        # Details panel
        details_panel = self._create_details_panel()
        splitter.addWidget(details_panel)

        splitter.setSizes([600, 300])
        layout.addWidget(splitter)

        # Action buttons
        actions = self._create_actions()
        layout.addWidget(actions)

    def _create_filter_bar(self) -> QWidget:
        """Create filter bar widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Category dropdown
        layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("All", "")
        self.category_combo.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self.category_combo)

        # Score range
        layout.addWidget(QLabel("Score:"))
        self.min_score_spin = QSpinBox()
        self.min_score_spin.setRange(0, 100)
        self.min_score_spin.setValue(0)
        self.min_score_spin.setPrefix("Min: ")
        self.min_score_spin.valueChanged.connect(self._on_filter_changed)
        layout.addWidget(self.min_score_spin)

        self.max_score_spin = QSpinBox()
        self.max_score_spin.setRange(0, 100)
        self.max_score_spin.setValue(100)
        self.max_score_spin.setPrefix("Max: ")
        self.max_score_spin.valueChanged.connect(self._on_filter_changed)
        layout.addWidget(self.max_score_spin)

        # Checkboxes
        self.missing_schema_cb = QCheckBox("Missing Schema")
        self.missing_schema_cb.stateChanged.connect(self._on_filter_changed)
        layout.addWidget(self.missing_schema_cb)

        self.missing_price_cb = QCheckBox("Missing Price")
        self.missing_price_cb.stateChanged.connect(self._on_filter_changed)
        layout.addWidget(self.missing_price_cb)

        self.noindex_cb = QCheckBox("Noindex")
        self.noindex_cb.stateChanged.connect(self._on_filter_changed)
        layout.addWidget(self.noindex_cb)

        self.canonical_cb = QCheckBox("Canonical Issues")
        self.canonical_cb.stateChanged.connect(self._on_filter_changed)
        layout.addWidget(self.canonical_cb)

        self.shortlist_cb = QCheckBox("Shortlist Only")
        self.shortlist_cb.stateChanged.connect(self._on_filter_changed)
        layout.addWidget(self.shortlist_cb)

        self.show_non_product_cb = QCheckBox("Show Non-Product")
        self.show_non_product_cb.setChecked(True)
        self.show_non_product_cb.stateChanged.connect(self._on_filter_changed)
        layout.addWidget(self.show_non_product_cb)

        layout.addStretch()

        # Search
        layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("URL, title, SKU, GTIN...")
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.setMinimumWidth(200)
        layout.addWidget(self.search_input)

        # Reset button
        self.reset_filters_btn = QPushButton("Reset")
        self.reset_filters_btn.clicked.connect(self._on_reset_filters)
        layout.addWidget(self.reset_filters_btn)

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
        self.count_label = QLabel("0 products")
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
        page_group = QGroupBox("Page Info")
        page_layout = QFormLayout(page_group)
        self.detail_url = QLabel("-")
        self.detail_url.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.detail_title = QLabel("-")
        self.detail_h1 = QLabel("-")
        self.detail_canonical = QLabel("-")
        self.detail_robots = QLabel("-")
        page_layout.addRow("URL:", self.detail_url)
        page_layout.addRow("Title:", self.detail_title)
        page_layout.addRow("H1:", self.detail_h1)
        page_layout.addRow("Canonical:", self.detail_canonical)
        page_layout.addRow("Robots:", self.detail_robots)
        layout.addWidget(page_group)

        # Schema section
        schema_group = QGroupBox("Schema")
        schema_layout = QFormLayout(schema_group)
        self.detail_schema_product = QLabel("-")
        self.detail_schema_offer = QLabel("-")
        self.detail_price_schema = QLabel("-")
        self.detail_currency = QLabel("-")
        self.detail_availability = QLabel("-")
        self.detail_sku = QLabel("-")
        self.detail_gtin = QLabel("-")
        self.detail_brand = QLabel("-")
        schema_layout.addRow("Product:", self.detail_schema_product)
        schema_layout.addRow("Offer:", self.detail_schema_offer)
        schema_layout.addRow("Price:", self.detail_price_schema)
        schema_layout.addRow("Currency:", self.detail_currency)
        schema_layout.addRow("Availability:", self.detail_availability)
        schema_layout.addRow("SKU:", self.detail_sku)
        schema_layout.addRow("GTIN:", self.detail_gtin)
        schema_layout.addRow("Brand:", self.detail_brand)
        layout.addWidget(schema_group)

        # Signals section
        signals_group = QGroupBox("Signals")
        signals_layout = QFormLayout(signals_group)
        self.detail_price_html = QLabel("-")
        self.detail_shipping = QLabel("-")
        self.detail_returns = QLabel("-")
        self.detail_images = QLabel("-")
        self.detail_text_length = QLabel("-")
        signals_layout.addRow("HTML Price:", self.detail_price_html)
        signals_layout.addRow("Shipping:", self.detail_shipping)
        signals_layout.addRow("Returns:", self.detail_returns)
        signals_layout.addRow("Images:", self.detail_images)
        signals_layout.addRow("Text Length:", self.detail_text_length)
        layout.addWidget(signals_group)

        # Flags section
        flags_group = QGroupBox("Flags")
        flags_layout = QFormLayout(flags_group)
        self.detail_flags = QLabel("-")
        flags_layout.addRow("Issues:", self.detail_flags)
        layout.addWidget(flags_group)

        layout.addStretch()

        scroll.setWidget(container)
        return scroll

    def _create_actions(self) -> QWidget:
        """Create action buttons widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.open_page_btn = QPushButton("Open Page")
        self.open_page_btn.setEnabled(False)
        self.open_page_btn.clicked.connect(self._on_open_page)

        self.mark_review_btn = QPushButton("Mark for Manual Review")
        self.mark_review_btn.setEnabled(False)
        self.mark_review_btn.clicked.connect(self._on_mark_review)

        self.export_btn = QPushButton("Export Selected")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._on_export)

        layout.addWidget(self.open_page_btn)
        layout.addWidget(self.mark_review_btn)
        layout.addWidget(self.export_btn)
        layout.addStretch()

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
        self.count_label.setText(f"{count} products")

    def _on_results_loaded(self):
        """Handle results loaded signal."""
        df = self.results_controller.get_filtered_data()
        self.table_model.update_data(df.to_dict('records'))
        self._update_count(len(df))

        # Enable export as soon as data is loaded (selection not required)
        self.export_btn.setEnabled(True)

        # Update category dropdown
        categories = self.results_controller.get_categories()
        self.category_combo.clear()
        self.category_combo.addItem("All", "")
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
            canonical_issues=self.canonical_cb.isChecked(),
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

        # Schema
        self.detail_schema_product.setText("Yes" if product.get("schema_product") else "No")
        self.detail_schema_offer.setText("Yes" if product.get("schema_offer") else "No")
        self.detail_price_schema.setText(str(product.get("price_schema", "not found")))
        self.detail_currency.setText(str(product.get("currency", "-")))
        self.detail_availability.setText(str(product.get("availability", "-")))
        self.detail_sku.setText(str(product.get("sku", "-")))
        self.detail_gtin.setText(str(product.get("gtin", "-")))
        self.detail_brand.setText(str(product.get("brand", "-")))

        # Signals
        self.detail_price_html.setText(str(product.get("price_html", "not found")))
        self.detail_shipping.setText("Yes" if product.get("has_shipping") else "No")
        self.detail_returns.setText("Yes" if product.get("has_returns") else "No")
        self.detail_images.setText(str(product.get("image_count", 0)))
        self.detail_text_length.setText(str(product.get("text_length", 0)))

        # Flags
        flags = []
        if product.get("flag_js_rendered"):
            flags.append("JS Rendered")
        if product.get("flag_noindex"):
            flags.append("Noindex")
        if product.get("flag_canonical_missing"):
            flags.append("No Canonical")
        if product.get("missing_price"):
            flags.append("Missing Price")
        if product.get("missing_schema"):
            flags.append("Missing Schema")
        self.detail_flags.setText(", ".join(flags) if flags else "None")

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
            QMessageBox.information(self, "Export", "No rows to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Filtered Results",
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
                self, "Export", f"Exported {len(rows)} rows to:\n{file_path}"
            )
        except OSError as e:
            QMessageBox.critical(self, "Export Error", str(e))