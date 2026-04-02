"""
Input tab for the audit tool.

Responsibility: UI for entering audit run configuration - sitemap, domain,
URL list input, and run options. Provides URL summary and validation.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QFileDialog,
    QMessageBox,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QTabWidget,
    QSplitter,
    QScrollArea,
    QFrame,
)
from PyQt6.QtGui import QIntValidator

from config import (
    DEFAULT_MAX_WORKERS,
    DEFAULT_CATALOG_WEIGHT,
    DEFAULT_MACHINE_WEIGHT,
    DEFAULT_COMMERCE_WEIGHT,
    DEFAULT_AGENT_READY_THRESHOLD,
    DEFAULT_DELAY,
    DEFAULT_MAX_URLS,
)

from gui.controllers.audit_run_controller import AuditRunController


class InputTab(QWidget):
    """
    Input tab for configuring and starting audit runs.

    Provides multiple input methods:
    - Sitemap URL or domain discovery
    - URL list from file or manual entry

    Emits start_scan_requested signal with configuration dict when Start Scan is clicked.
    """

    # Signal emitted when user requests to start a scan
    # Dict contains: sitemap_url, domain, urls_file, manual_urls,
    #                max_urls, delay, output_dir, use_async
    start_scan_requested = pyqtSignal(dict)

    def __init__(self, audit_controller: AuditRunController, parent=None):
        """
        Initialize InputTab.

        Args:
            audit_controller: AuditRunController instance for backend communication
            parent: Parent widget
        """
        super().__init__(parent)
        self.audit_controller = audit_controller
        self._settings = QSettings("AuditTool", "WebshopAudit")

        # Collected URLs
        self._collected_urls: list[str] = []

        # UI setup
        self._setup_ui()
        self._load_saved_state()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the UI components — dvostupni layout (lijevo: unos, desno: opcije)."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Jedan scroll area koji obuhvata oba stupca ────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(0)

        # ── Dva stupca unutar scrolla ─────────────────────────────────────────
        columns = QHBoxLayout()
        columns.setSpacing(12)
        columns.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Lijeva kolona ─────────────────────────────────────────────────────
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.input_tabs = QTabWidget()
        sitemap_widget = self._create_sitemap_input()
        self.input_tabs.addTab(sitemap_widget, "Sitemap")  # "Sitemap"
        url_list_widget = self._create_url_list_input()
        self.input_tabs.addTab(url_list_widget, "Lista URL-ova")  # "URL List"
        left_layout.addWidget(self.input_tabs)

        self.url_summary = self._create_url_summary()
        left_layout.addWidget(self.url_summary)

        columns.addWidget(left_col, 55)

        # ── Desna kolona ──────────────────────────────────────────────────────
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        run_options = self._create_run_options()
        right_layout.addWidget(run_options)

        advanced = self._create_advanced_settings()
        advanced.setChecked(True)  # Napredne postavke vidljive po defaultu
        right_layout.addWidget(advanced)

        columns.addWidget(right_col, 45)

        content_layout.addLayout(columns)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        # ── Pinned action bar ─────────────────────────────────────────────────
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        outer.addWidget(separator)

        actions = self._create_actions()
        outer.addWidget(actions)

    def _create_sitemap_input(self) -> QWidget:
        """Create sitemap/domain input widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        group = QGroupBox("Sitemap unos")  # "Sitemap Input"
        form = QFormLayout(group)

        # Sitemap URL
        self.sitemap_url_input = QLineEdit()
        self.sitemap_url_input.setPlaceholderText("https://example.com/sitemap.xml")
        form.addRow("Sitemap URL:", self.sitemap_url_input)

        # Domain
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("https://example.com")
        form.addRow("Domen:", self.domain_input)  # "Domain:"

        # Buttons row
        buttons = QHBoxLayout()
        self.discover_btn = QPushButton("Auto-otkrivanje")  # "Auto-Discover"
        self.discover_btn.setToolTip(
            "Pronađi sitemap iz domena ili robots.txt"
        )  # "Discover sitemap from domain or robots.txt"
        self.load_sitemap_btn = QPushButton("Učitaj sitemap")  # "Load Sitemap"
        self.load_sitemap_btn.setToolTip(
            "Učitaj i parsiraj sitemap URL"
        )  # "Load and parse sitemap URL"
        buttons.addWidget(self.discover_btn)
        buttons.addWidget(self.load_sitemap_btn)
        buttons.addStretch()
        form.addRow("", buttons)

        # Custom URL patterns
        self.custom_patterns_input = QLineEdit()
        self.custom_patterns_input.setPlaceholderText(
            # "e.g. /oglas/, /listing/, /item/   (comma-separated, leave empty for defaults)"
            "npr. /oglas/, /listing/, /item/   (zarezom odvojeni, ostavi prazno za podrazumijevane)"
        )
        self.custom_patterns_input.setToolTip(
            # "Override built-in product URL patterns with your own.\n"
            # "Comma-separated substrings. A URL is kept if it contains any of them.\n"
            # "Example for OLX: /oglas/\n"
            # "Leave empty to use the built-in heuristics."
            "Zamijeni ugrađene URL patterne vlastitima.\n"
            "Zarezom odvojeni podnizovi. URL ostaje ako sadrži bilo koji od njih.\n"
            "Primjer za OLX: /oglas/\n"
            "Ostavi prazno za ugrađenu heuristiku."
        )
        form.addRow("URL patterne:", self.custom_patterns_input)  # "URL patterns:"

        # Status label
        self.sitemap_status_label = QLabel("")
        self.sitemap_status_label.setStyleSheet("color: #666;")
        self.sitemap_status_label.setWordWrap(True)
        form.addRow("Status:", self.sitemap_status_label)

        layout.addWidget(group)
        return widget

    def _create_url_list_input(self) -> QWidget:
        """Create URL list input widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Unos liste URL-ova")  # "URL List Input"
        form = QFormLayout(group)

        # File input row
        file_row = QHBoxLayout()
        self.urls_file_input = QLineEdit()
        self.urls_file_input.setPlaceholderText(
            "Putanja do .txt ili .csv fajla"
        )  # "Path to .txt or .csv file"
        self.browse_btn = QPushButton("Pregledaj...")  # "Browse..."
        file_row.addWidget(self.urls_file_input)
        file_row.addWidget(self.browse_btn)
        form.addRow("Iz fajla:", file_row)  # "From File:"

        # Manual input
        form.addRow("Ili ručni unos:", None)  # "Or Manual Entry:"
        self.manual_urls_edit = QPlainTextEdit()
        self.manual_urls_edit.setPlaceholderText(
            # "Enter URLs (one per line)\ne.g., https://example.com/product/1"
            "Unesi URL-ove (jedan po redu)\nnpr. https://example.com/product/1"
        )
        self.manual_urls_edit.setMinimumHeight(150)
        form.addRow("", self.manual_urls_edit)

        # Append/Replace options
        options_row = QHBoxLayout()
        self.append_checkbox = QCheckBox(
            "Dodaj na postojeće URL-ove"
        )  # "Append to existing URLs"
        options_row.addWidget(self.append_checkbox)
        options_row.addStretch()
        form.addRow("", options_row)

        layout.addWidget(group)
        return widget

    def _create_run_options(self) -> QGroupBox:
        """Create run options group."""
        group = QGroupBox("Opcije pokretanja")  # "Run Options"
        form = QFormLayout(group)

        # Max URLs
        self.max_urls_input = QLineEdit()
        self.max_urls_input.setPlaceholderText(
            "Ostavi prazno za neograničeno"
        )  # "Leave empty for unlimited"
        self.max_urls_input.setValidator(QIntValidator(1, 999999, self))
        form.addRow("Max URL-ova:", self.max_urls_input)  # "Max URLs:"

        # Delay
        delay_layout = QHBoxLayout()
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 30)
        self.delay_spin.setValue(int(DEFAULT_DELAY))
        self.delay_spin.setSuffix(" s")
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addStretch()
        form.addRow("Pauza:", delay_layout)  # "Delay:"

        # Parallel workers
        workers_layout = QHBoxLayout()
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 32)
        self.max_workers_spin.setValue(DEFAULT_MAX_WORKERS)
        self.max_workers_spin.setToolTip(
            # "Number of parallel HTTP threads. Higher = faster but more load on the server."
            "Broj paralelnih HTTP niti. Više = brže, ali veće opterećenje servera."
        )
        workers_layout.addWidget(self.max_workers_spin)
        workers_layout.addStretch()
        form.addRow("Radni procesi:", workers_layout)  # "Workers:"

        # Playwright
        self.use_playwright_cb = QCheckBox(
            "Koristi Playwright (JS stranice)"
        )  # "Use Playwright (JS-rendered pages)"
        self.use_playwright_cb.setToolTip(
            # "Render pages with a headless browser so JavaScript content is visible.\n"
            # "Requires: pip install playwright && playwright install chromium\n"
            # "Forces single-threaded mode (workers setting is ignored)."
            "Renderuj stranice headless browserom kako bi JavaScript sadržaj bio vidljiv.\n"
            "Zahtijeva: pip install playwright && playwright install chromium\n"
            "Forsira sekvencijalni mod (postavka radnih procesa se ignoriše)."
        )
        self.use_playwright_cb.stateChanged.connect(self._on_playwright_toggled)
        form.addRow("", self.use_playwright_cb)

        # Output directory
        output_row = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("outputs/")
        self.output_dir_btn = QPushButton("Pregledaj...")  # "Browse..."
        output_row.addWidget(self.output_dir_input)
        output_row.addWidget(self.output_dir_btn)
        form.addRow("Izlazni dir.:", output_row)  # "Output Dir:"

        # Error label
        self.run_options_error = QLabel("")
        self.run_options_error.setStyleSheet("color: #d32f2f;")
        form.addRow("", self.run_options_error)

        return group

    def _create_advanced_settings(self) -> QGroupBox:
        """Create collapsible Advanced Settings group (scoring weights + resume)."""
        group = QGroupBox("Napredne postavke")  # "Advanced Settings"
        group.setCheckable(True)
        group.setChecked(False)  # collapsed by default
        form = QFormLayout(group)

        # --- Score weights ---
        weights_label = QLabel(
            "Težine ocjena (auto-normalizirano na 100%)"
        )  # "Score weights (auto-normalised to 100%)"
        weights_label.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow(weights_label)

        self.catalog_weight_spin = QDoubleSpinBox()
        self.catalog_weight_spin.setRange(0.01, 1.0)
        self.catalog_weight_spin.setSingleStep(0.05)
        self.catalog_weight_spin.setDecimals(2)
        self.catalog_weight_spin.setValue(DEFAULT_CATALOG_WEIGHT)
        self.catalog_weight_spin.setToolTip(
            "HTML kvalitet: naslov, H1, meta, breadcrumb, tekst cijene"
        )  # "HTML quality: title, H1, meta, breadcrumb, price text"
        form.addRow("Težina kataloga:", self.catalog_weight_spin)  # "Catalog weight:"

        self.machine_weight_spin = QDoubleSpinBox()
        self.machine_weight_spin.setRange(0.01, 1.0)
        self.machine_weight_spin.setSingleStep(0.05)
        self.machine_weight_spin.setDecimals(2)
        self.machine_weight_spin.setValue(DEFAULT_MACHINE_WEIGHT)
        self.machine_weight_spin.setToolTip("Schema.org, SKU, GTIN, canonical, noindex")
        form.addRow("Težina mašine:", self.machine_weight_spin)  # "Machine weight:"

        self.commerce_weight_spin = QDoubleSpinBox()
        self.commerce_weight_spin.setRange(0.01, 1.0)
        self.commerce_weight_spin.setSingleStep(0.05)
        self.commerce_weight_spin.setDecimals(2)
        self.commerce_weight_spin.setValue(DEFAULT_COMMERCE_WEIGHT)
        self.commerce_weight_spin.setToolTip(
            "Cijena, slike, dostava, povrati, kvalitet opisa"
        )  # "Price, images, shipping, returns, description quality"
        form.addRow("Težina commerce:", self.commerce_weight_spin)  # "Commerce weight:"

        self.agent_ready_threshold_spin = QSpinBox()
        self.agent_ready_threshold_spin.setRange(0, 100)
        self.agent_ready_threshold_spin.setValue(DEFAULT_AGENT_READY_THRESHOLD)
        self.agent_ready_threshold_spin.setToolTip(
            # "Minimum overall_score for a product to be flagged agent_ready=True"
            "Minimalni overall_score da bi proizvod bio označen agent_ready=True"
        )
        form.addRow(
            "Prag agent-ready:", self.agent_ready_threshold_spin
        )  # "Agent-ready threshold:"

        # --- Resume from checkpoint ---
        resume_separator = QLabel("Nastavak")  # "Resume"
        resume_separator.setStyleSheet("color: #888; font-size: 11px; margin-top: 6px;")
        form.addRow(resume_separator)

        self.resume_cb = QCheckBox(
            "Nastavi od prethodnog pokretanja"
        )  # "Resume from previous run"
        self.resume_cb.setToolTip(
            # "Skip the fetch phase by reusing pages cached in a previous run's output folder."
            "Preskoči fazu preuzimanja koristeći stranice keširane u prethodnom izlaznom folderu."
        )
        self.resume_cb.stateChanged.connect(self._on_resume_toggled)
        form.addRow("", self.resume_cb)

        resume_row = QHBoxLayout()
        self.resume_dir_input = QLineEdit()
        self.resume_dir_input.setPlaceholderText(
            "Putanja do prethodnog izlaznog direktorija"
        )  # "Path to previous output dir"
        self.resume_dir_input.setEnabled(False)
        self.resume_dir_btn = QPushButton("Pregledaj...")  # "Browse..."
        self.resume_dir_btn.setEnabled(False)
        self.resume_dir_btn.clicked.connect(self._on_resume_dir_browse_clicked)
        resume_row.addWidget(self.resume_dir_input)
        resume_row.addWidget(self.resume_dir_btn)
        form.addRow("Checkpoint dir.:", resume_row)  # "Checkpoint dir:"

        return group

    def _create_url_summary(self) -> QGroupBox:
        """Create URL summary group with preview list."""
        group = QGroupBox("Pregled URL-ova")  # "URL Summary"
        layout = QVBoxLayout(group)

        # Stats row
        stats_layout = QHBoxLayout()
        self.total_urls_label = QLabel("Ukupno: 0")  # "Total: 0"
        self.valid_urls_label = QLabel("Ispravnih: 0")  # "Valid: 0"
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #f57c00;")
        stats_layout.addWidget(self.total_urls_label)
        stats_layout.addWidget(self.valid_urls_label)
        stats_layout.addWidget(self.warning_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Preview list
        preview_label = QLabel("Pregled (prvih 10):")  # "Preview (first 10):"
        layout.addWidget(preview_label)
        self.url_preview_list = QListWidget()
        self.url_preview_list.setMaximumHeight(150)
        layout.addWidget(self.url_preview_list)

        return group

    def _create_actions(self) -> QWidget:
        """Create action buttons widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.start_scan_btn = QPushButton("Pokreni skeniranje")  # "Start Scan"
        self.start_scan_btn.setObjectName("primary")
        self.start_scan_btn.setDefault(True)
        self.start_scan_btn.setEnabled(False)

        self.clear_btn = QPushButton("Obriši listu")  # "Clear List"
        self.export_btn = QPushButton("Izvezi listu URL-ova")  # "Export URL List"

        layout.addWidget(self.clear_btn)
        layout.addWidget(self.export_btn)
        layout.addStretch()
        layout.addWidget(self.start_scan_btn)  # Desna strana action bar-a

        return widget

    def _connect_signals(self):
        """Connect internal signals."""
        # Sitemap buttons
        self.discover_btn.clicked.connect(self._on_discover_clicked)
        self.load_sitemap_btn.clicked.connect(self._on_load_sitemap_clicked)

        # Autodiscover rezultati iz kontrolera
        self.audit_controller.sitemap_discovered.connect(self._on_sitemap_discovered)
        self.audit_controller.sitemap_discover_failed.connect(
            self._on_sitemap_discover_failed
        )

        # File browse
        self.browse_btn.clicked.connect(self._on_browse_clicked)

        # Output dir browse
        self.output_dir_btn.clicked.connect(self._on_output_dir_browse_clicked)

        # Actions
        self.start_scan_btn.clicked.connect(self._on_start_scan_clicked)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.export_btn.clicked.connect(self._on_export_clicked)

        # Input changes - validate and update summary
        self.sitemap_url_input.textChanged.connect(self._on_input_changed)
        self.domain_input.textChanged.connect(self._on_input_changed)
        self.manual_urls_edit.textChanged.connect(self._on_input_changed)

        # Save advanced settings on change
        self.max_workers_spin.valueChanged.connect(self._save_state)
        self.catalog_weight_spin.valueChanged.connect(self._save_state)
        self.machine_weight_spin.valueChanged.connect(self._save_state)
        self.commerce_weight_spin.valueChanged.connect(self._save_state)
        self.agent_ready_threshold_spin.valueChanged.connect(self._save_state)

    def _load_saved_state(self):
        """Load saved state from QSettings."""
        self.sitemap_url_input.setText(self._settings.value("input/sitemap_url", ""))
        self.domain_input.setText(self._settings.value("input/domain", ""))
        self.output_dir_input.setText(
            self._settings.value("input/output_dir", "outputs/")
        )

        max_urls = self._settings.value("input/max_urls", str(DEFAULT_MAX_URLS))
        self.max_urls_input.setText(max_urls if max_urls else str(DEFAULT_MAX_URLS))

        delay = self._settings.value("input/delay", DEFAULT_DELAY)
        self.delay_spin.setValue(int(delay))

        self.max_workers_spin.setValue(
            int(self._settings.value("input/max_workers", DEFAULT_MAX_WORKERS))
        )
        self.catalog_weight_spin.setValue(
            float(self._settings.value("input/catalog_weight", DEFAULT_CATALOG_WEIGHT))
        )
        self.machine_weight_spin.setValue(
            float(self._settings.value("input/machine_weight", DEFAULT_MACHINE_WEIGHT))
        )
        self.commerce_weight_spin.setValue(
            float(
                self._settings.value("input/commerce_weight", DEFAULT_COMMERCE_WEIGHT)
            )
        )
        self.agent_ready_threshold_spin.setValue(
            int(
                self._settings.value(
                    "input/agent_ready_threshold", DEFAULT_AGENT_READY_THRESHOLD
                )
            )
        )

    def _save_state(self):
        """Save current state to QSettings."""
        self._settings.setValue("input/sitemap_url", self.sitemap_url_input.text())
        self._settings.setValue("input/domain", self.domain_input.text())
        self._settings.setValue("input/output_dir", self.output_dir_input.text())
        self._settings.setValue("input/max_urls", self.max_urls_input.text())
        self._settings.setValue("input/delay", self.delay_spin.value())
        self._settings.setValue("input/max_workers", self.max_workers_spin.value())
        self._settings.setValue(
            "input/catalog_weight", self.catalog_weight_spin.value()
        )
        self._settings.setValue(
            "input/machine_weight", self.machine_weight_spin.value()
        )
        self._settings.setValue(
            "input/commerce_weight", self.commerce_weight_spin.value()
        )
        self._settings.setValue(
            "input/agent_ready_threshold", self.agent_ready_threshold_spin.value()
        )

    def _validate_inputs(self) -> tuple[bool, str]:
        """
        Validate all input fields.

        Returns:
            Tuple of (is_valid, error_message)
        """
        sitemap_url = self.sitemap_url_input.text().strip()
        domain = self.domain_input.text().strip()
        manual_urls = self.manual_urls_edit.toPlainText().strip()
        urls_file = self.urls_file_input.text().strip()
        output_dir = self.output_dir_input.text().strip()

        # Check if any input source is provided
        has_sitemap = bool(sitemap_url)
        has_domain = bool(domain)
        has_manual = bool(manual_urls)
        has_file = bool(urls_file)

        if not (has_sitemap or has_domain or has_manual or has_file):
            return (
                False,
                "Unesite barem jedan izvor URL-ova",
            )  # "Please provide at least one input source"

        # Validate URLs start with http/https
        if sitemap_url and not self._is_valid_url(sitemap_url):
            return (
                False,
                "Sitemap URL mora početi sa http:// ili https://",
            )  # "Sitemap URL must start with http:// or https://"

        if domain and not self._is_valid_url(domain):
            return (
                False,
                "Domen mora početi sa http:// ili https://",
            )  # "Domain must start with http:// or https://"

        # Validate output directory
        if not output_dir:
            return (
                False,
                "Izlazni direktorijum je obavezan",
            )  # "Output directory is required"

        return True, ""

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL starts with http:// or https://."""
        return url.startswith("http://") or url.startswith("https://")

    def _validate_and_update(self):
        """Validate inputs and update UI state."""
        is_valid, error = self._validate_inputs()

        # Update start button
        self.start_scan_btn.setEnabled(is_valid and bool(self._collected_urls))

        # Update error label in run options
        if error:
            self.run_options_error.setText(error)
        else:
            self.run_options_error.setText("")

        return is_valid

    def _on_input_changed(self):
        """Handle input changes."""
        self._validate_and_update()
        self._update_url_summary()

    def _on_discover_clicked(self):
        """Handle auto-discover button click."""
        domain = self.domain_input.text().strip()
        if not domain:
            self._set_sitemap_status(
                "Prvo unesite domen", "error"
            )  # "Enter domain first"
            return

        if not self._is_valid_url(domain):
            self._set_sitemap_status(
                "Domen mora početi sa http:// ili https://", "error"
            )  # "Domain must start with http:// or https://"
            return

        self._set_sitemap_status(
            "Tražim sitemap...", "info"
        )  # "Discovering sitemap..."
        self.discover_btn.setEnabled(False)
        self.audit_controller.discover_sitemap(domain)

    def _on_sitemap_discovered(self, url: str):
        """Handle successful sitemap autodiscover."""
        self.discover_btn.setEnabled(True)
        self._set_sitemap_status(f"Pronađeno: {url}", "success")  # "Found: {url}"
        self.sitemap_url_input.setText(url)

    def _on_sitemap_discover_failed(self, message: str):
        """Handle failed sitemap autodiscover."""
        self.discover_btn.setEnabled(True)
        self._set_sitemap_status(message, "error")

    def _set_sitemap_status(self, text: str, level: str = "info"):
        """Update sitemap status label with color coding."""
        colors = {
            "info": "#1976d2",
            "success": "#388e3c",
            "warning": "#D9A441",
            "error": "#d32f2f",
        }
        self.sitemap_status_label.setText(text)
        self.sitemap_status_label.setStyleSheet(
            f"color: {colors.get(level, '#666666')};"
        )

    def _on_load_sitemap_clicked(self):
        """Handle load sitemap button click."""
        sitemap_url = self.sitemap_url_input.text().strip()

        if not sitemap_url:
            self.sitemap_status_label.setText(
                "Prvo unesite sitemap URL"
            )  # "Enter sitemap URL first"
            self.sitemap_status_label.setStyleSheet("color: #C96A5A;")
            return

        if not self._is_valid_url(sitemap_url):
            self.sitemap_status_label.setText(
                "URL mora početi sa http:// ili https://"
            )  # "URL must start with http:// or https://"
            self.sitemap_status_label.setStyleSheet("color: #C96A5A;")
            return

        # Loading state
        self.sitemap_status_label.setText("Učitavam sitemap...")  # "Loading sitemap..."
        self.sitemap_status_label.setStyleSheet("color: #8A94A6;")
        self.load_sitemap_btn.setEnabled(False)

        # Connect signals to handler methods (if not already connected)
        try:
            self.audit_controller.sitemap_loaded.disconnect(self._on_sitemap_loaded)
            self.audit_controller.sitemap_load_failed.disconnect(
                self._on_sitemap_load_failed
            )
        except TypeError:
            pass  # Signals not connected yet

        self.audit_controller.sitemap_loaded.connect(self._on_sitemap_loaded)
        self.audit_controller.sitemap_load_failed.connect(self._on_sitemap_load_failed)

        # Parse custom patterns field (comma-separated, strip whitespace)
        raw_patterns = self.custom_patterns_input.text().strip()
        custom_patterns = (
            [p.strip() for p in raw_patterns.split(",") if p.strip()]
            if raw_patterns
            else None
        )

        # Start loading
        self.audit_controller.load_sitemap(sitemap_url, custom_patterns=custom_patterns)

    def _on_sitemap_loaded(self, urls: list, used_fallback: bool):
        """Handle successful sitemap load."""
        self.load_sitemap_btn.setEnabled(True)

        self._collected_urls = urls
        total = len(urls)

        if used_fallback:
            self._set_sitemap_status(
                f"Upozorenje: nema poklapanja sa URL patternima — prikazujem svih {total} URL-ova. "
                "Dodaj vlastite patterne u polje ispod.",
                "warning",
            )
        else:
            self._set_sitemap_status(f"Učitano {total} URL-ova.", "success")

        self._update_url_summary()
        self._validate_and_update()  # ← aktivira Start Scan dugme

    def _on_sitemap_load_failed(self, error: str):
        """Handle sitemap load failure."""
        self.load_sitemap_btn.setEnabled(True)
        self.sitemap_status_label.setText(error)
        self.sitemap_status_label.setStyleSheet("color: #C96A5A;")

    def _on_browse_clicked(self):
        """Handle browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Odaberi fajl sa listom URL-ova",  # "Select URL List File"
            "",
            "Text Files (*.txt *.csv);;All Files (*)",
        )

        if file_path:
            self.urls_file_input.setText(file_path)
            self._load_urls_from_file(file_path)

    def _load_urls_from_file(self, file_path: str):
        """Load URLs from file with deduplication."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]

            # Deduplicate — keep only URLs not already collected
            new_urls = [u for u in urls if u not in self._collected_urls]

            if self.append_checkbox.isChecked():
                self._collected_urls.extend(new_urls)
            else:
                self._collected_urls = urls

            self._update_url_summary()
            self._validate_and_update()  # aktivira Start Scan dugme
        except Exception as e:
            self.sitemap_status_label.setText(
                f"Greška pri učitavanju fajla: {str(e)}"
            )  # "Error loading file: {e}"
            self.sitemap_status_label.setStyleSheet("color: #d32f2f;")

    def _on_playwright_toggled(self, state: int):
        """Warn that Playwright forces sequential mode."""
        if state:
            self.max_workers_spin.setEnabled(False)
        else:
            self.max_workers_spin.setEnabled(True)

    def _on_resume_toggled(self, state: int):
        """Enable/disable resume path input."""
        enabled = bool(state)
        self.resume_dir_input.setEnabled(enabled)
        self.resume_dir_btn.setEnabled(enabled)

    def _on_resume_dir_browse_clicked(self):
        """Handle resume directory browse click."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Odaberi prethodni izlazni direktorijum",  # "Select Previous Output Directory"
            self.resume_dir_input.text() or "outputs/",
        )
        if dir_path:
            self.resume_dir_input.setText(dir_path)

    def _on_output_dir_browse_clicked(self):
        """Handle output directory browse click."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Odaberi izlazni direktorijum",  # "Select Output Directory"
            self.output_dir_input.text() or "outputs/",
        )

        if dir_path:
            self.output_dir_input.setText(dir_path)
            self._save_state()

    def _on_start_scan_clicked(self):
        """Handle start scan button click."""
        if not self._validate_and_update():
            return

        if not self._collected_urls:
            self.run_options_error.setText(
                "Nema URL-ova za skeniranje"
            )  # "No URLs to scan"
            return

        # Save state
        self._save_state()

        # Build config dict
        config = {
            "sitemap_url": self.sitemap_url_input.text().strip(),
            "domain": self.domain_input.text().strip(),
            "urls_file": self.urls_file_input.text().strip(),
            "manual_urls": self.manual_urls_edit.toPlainText().strip().split("\n"),
            "max_urls": self.max_urls_input.text().strip(),
            "delay": self.delay_spin.value(),
            "output_dir": self.output_dir_input.text().strip(),
            "urls": self._collected_urls,
            # Fetch options
            "max_workers": self.max_workers_spin.value(),
            "use_playwright": self.use_playwright_cb.isChecked(),
            # Scoring
            "catalog_weight": self.catalog_weight_spin.value(),
            "machine_weight": self.machine_weight_spin.value(),
            "commerce_weight": self.commerce_weight_spin.value(),
            "agent_ready_threshold": self.agent_ready_threshold_spin.value(),
            # Checkpoint / resume
            "resume_from": (
                self.resume_dir_input.text().strip()
                if self.resume_cb.isChecked()
                else ""
            ),
        }

        # Emit signal
        self.start_scan_requested.emit(config)

    def _on_clear_clicked(self):
        """Handle clear button click."""
        self._collected_urls = []
        self._update_url_summary()
        self.start_scan_btn.setEnabled(False)
        self.sitemap_status_label.setText("Obrisano")  # "Cleared"
        self.sitemap_status_label.setStyleSheet("color: #666;")

    def _on_export_clicked(self):
        """Handle export button click."""
        if not self._collected_urls:
            self.sitemap_status_label.setText(
                "Nema URL-ova za izvoz"
            )  # "No URLs to export"
            self.sitemap_status_label.setStyleSheet("color: #d32f2f;")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Izvezi listu URL-ova",  # "Export URL List"
            "urls_export.txt",
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(self._collected_urls))
                self.sitemap_status_label.setText(
                    f"Izvezeno {len(self._collected_urls)} URL-ova"
                )  # "Exported {n} URLs"
                self.sitemap_status_label.setStyleSheet("color: #388e3c;")
            except Exception as e:
                self.sitemap_status_label.setText(
                    f"Greška pri izvozu: {str(e)}"
                )  # "Export error: {e}"
                self.sitemap_status_label.setStyleSheet("color: #d32f2f;")

    def _update_url_summary(self):
        """Update URL summary display."""
        # Get URLs from various sources
        urls = list(self._collected_urls) if self._collected_urls else []

        # From manual input
        manual = self.manual_urls_edit.toPlainText().strip()
        manual_invalid_count = 0
        if manual:
            manual_urls = [u.strip() for u in manual.split("\n") if u.strip()]
            manual_invalid_count = len(
                [u for u in manual_urls if not self._is_valid_url(u)]
            )
            # If we have collected URLs from sitemap, don't append manual
            # If no sitemap URLs, append manual URLs
            if not urls:
                urls = manual_urls

        # Total
        total = len(urls)
        self.total_urls_label.setText(f"Ukupno: {total}")  # "Total: {total}"

        # Valid URLs (simple filter)
        valid = len([u for u in urls if self._is_valid_url(u)])
        self.valid_urls_label.setText(f"Ispravnih: {valid}")  # "Valid: {valid}"

        # Update preview list
        self.url_preview_list.clear()
        for url in urls[:10]:
            item = QListWidgetItem(url)
            self.url_preview_list.addItem(item)

        # Warning
        warnings = []
        if valid < total and total > 0:
            warnings.append(f"{total - valid} URL-ova neispravno")
        if manual_invalid_count > 0:
            warnings.append(f"{manual_invalid_count} ručnih URL-ova bez http://")
        if warnings:
            self.warning_label.setText("Upozorenje: " + ", ".join(warnings))
        else:
            self.warning_label.setText("")
