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
    QTabWidget,
    QSplitter,
)
from PyQt6.QtGui import QIntValidator

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
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Create tab widget for input methods
        self.input_tabs = QTabWidget()

        # Sitemap input tab
        sitemap_widget = self._create_sitemap_input()
        self.input_tabs.addTab(sitemap_widget, "Sitemap")

        # URL list input tab
        url_list_widget = self._create_url_list_input()
        self.input_tabs.addTab(url_list_widget, "URL List")

        layout.addWidget(self.input_tabs)

        # Run options group
        run_options = self._create_run_options()
        layout.addWidget(run_options)

        # URL Summary group
        self.url_summary = self._create_url_summary()
        layout.addWidget(self.url_summary)

        # Action buttons
        actions = self._create_actions()
        layout.addWidget(actions)

        layout.addStretch()

    def _create_sitemap_input(self) -> QWidget:
        """Create sitemap/domain input widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Sitemap Input")
        form = QFormLayout(group)

        # Sitemap URL
        self.sitemap_url_input = QLineEdit()
        self.sitemap_url_input.setPlaceholderText("https://example.com/sitemap.xml")
        form.addRow("Sitemap URL:", self.sitemap_url_input)

        # Domain
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("https://example.com")
        form.addRow("Domain:", self.domain_input)

        # Buttons row
        buttons = QHBoxLayout()
        self.discover_btn = QPushButton("Auto-Discover")
        self.discover_btn.setToolTip("Discover sitemap from domain or robots.txt")
        self.load_sitemap_btn = QPushButton("Load Sitemap")
        self.load_sitemap_btn.setToolTip("Load and parse sitemap URL")
        buttons.addWidget(self.discover_btn)
        buttons.addWidget(self.load_sitemap_btn)
        buttons.addStretch()
        form.addRow("", buttons)

        # Status label
        self.sitemap_status_label = QLabel("")
        self.sitemap_status_label.setStyleSheet("color: #666;")
        form.addRow("Status:", self.sitemap_status_label)

        layout.addWidget(group)
        return widget

    def _create_url_list_input(self) -> QWidget:
        """Create URL list input widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("URL List Input")
        form = QFormLayout(group)

        # File input row
        file_row = QHBoxLayout()
        self.urls_file_input = QLineEdit()
        self.urls_file_input.setPlaceholderText("Path to .txt or .csv file")
        self.browse_btn = QPushButton("Browse...")
        file_row.addWidget(self.urls_file_input)
        file_row.addWidget(self.browse_btn)
        form.addRow("From File:", file_row)

        # Manual input
        form.addRow("Or Manual Entry:", None)
        self.manual_urls_edit = QPlainTextEdit()
        self.manual_urls_edit.setPlaceholderText("Enter URLs (one per line)\ne.g., https://example.com/product/1")
        self.manual_urls_edit.setMinimumHeight(150)
        form.addRow("", self.manual_urls_edit)

        # Append/Replace options
        options_row = QHBoxLayout()
        self.append_checkbox = QCheckBox("Append to existing URLs")
        options_row.addWidget(self.append_checkbox)
        options_row.addStretch()
        form.addRow("", options_row)

        layout.addWidget(group)
        return widget

    def _create_run_options(self) -> QGroupBox:
        """Create run options group."""
        group = QGroupBox("Run Options")
        form = QFormLayout(group)

        # Max URLs
        self.max_urls_input = QLineEdit()
        self.max_urls_input.setPlaceholderText("Leave empty for unlimited")
        self.max_urls_input.setValidator(QIntValidator(1, 999999, self))
        form.addRow("Max URLs:", self.max_urls_input)

        # Delay
        delay_layout = QHBoxLayout()
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 30)
        self.delay_spin.setValue(1)
        self.delay_spin.setSuffix(" s")
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addStretch()
        form.addRow("Delay:", delay_layout)

        # Output directory
        output_row = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("outputs/")
        self.output_dir_btn = QPushButton("Browse...")
        output_row.addWidget(self.output_dir_input)
        output_row.addWidget(self.output_dir_btn)
        form.addRow("Output Dir:", output_row)

        # Error label
        self.run_options_error = QLabel("")
        self.run_options_error.setStyleSheet("color: #d32f2f;")
        form.addRow("", self.run_options_error)

        return group

    def _create_url_summary(self) -> QGroupBox:
        """Create URL summary group with preview list."""
        group = QGroupBox("URL Summary")
        layout = QVBoxLayout(group)

        # Stats row
        stats_layout = QHBoxLayout()
        self.total_urls_label = QLabel("Total: 0")
        self.valid_urls_label = QLabel("Valid: 0")
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #f57c00;")
        stats_layout.addWidget(self.total_urls_label)
        stats_layout.addWidget(self.valid_urls_label)
        stats_layout.addWidget(self.warning_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Preview list
        preview_label = QLabel("Preview (first 10):")
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

        self.start_scan_btn = QPushButton("Start Scan")
        self.start_scan_btn.setDefault(True)
        self.start_scan_btn.setEnabled(False)

        self.clear_btn = QPushButton("Clear List")
        self.export_btn = QPushButton("Export URL List")

        layout.addWidget(self.start_scan_btn)
        layout.addWidget(self.clear_btn)
        layout.addWidget(self.export_btn)
        layout.addStretch()

        return widget

    def _connect_signals(self):
        """Connect internal signals."""
        # Sitemap buttons
        self.discover_btn.clicked.connect(self._on_discover_clicked)
        self.load_sitemap_btn.clicked.connect(self._on_load_sitemap_clicked)

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

    def _load_saved_state(self):
        """Load saved state from QSettings."""
        self.sitemap_url_input.setText(self._settings.value("input/sitemap_url", ""))
        self.domain_input.setText(self._settings.value("input/domain", ""))
        self.output_dir_input.setText(self._settings.value("input/output_dir", "outputs/"))
        
        max_urls = self._settings.value("input/max_urls", "")
        self.max_urls_input.setText(max_urls if max_urls else "")
        
        delay = self._settings.value("input/delay", 1)
        self.delay_spin.setValue(int(delay))

    def _save_state(self):
        """Save current state to QSettings."""
        self._settings.setValue("input/sitemap_url", self.sitemap_url_input.text())
        self._settings.setValue("input/domain", self.domain_input.text())
        self._settings.setValue("input/output_dir", self.output_dir_input.text())
        self._settings.setValue("input/max_urls", self.max_urls_input.text())
        self._settings.setValue("input/delay", self.delay_spin.value())

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
            return False, "Please provide at least one input source"

        # Validate URLs start with http/https
        if sitemap_url and not self._is_valid_url(sitemap_url):
            return False, "Sitemap URL must start with http:// or https://"

        if domain and not self._is_valid_url(domain):
            return False, "Domain must start with http:// or https://"

        # Validate output directory
        if not output_dir:
            return False, "Output directory is required"

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
            self.sitemap_status_label.setText("Enter domain first")
            self.sitemap_status_label.setStyleSheet("color: #d32f2f;")
            return

        if not self._is_valid_url(domain):
            self.sitemap_status_label.setText("Domain must start with http:// or https://")
            self.sitemap_status_label.setStyleSheet("color: #d32f2f;")
            return

        self.sitemap_status_label.setText("Discovering sitemap...")
        self.sitemap_status_label.setStyleSheet("color: #1976d2;")

        # TODO: Call backend sitemap discover through controller
        # For now, just update status
        self.sitemap_status_label.setText("Auto-discover not implemented yet")
        self.sitemap_status_label.setStyleSheet("color: #666;")

    def _on_load_sitemap_clicked(self):
        """Handle load sitemap button click."""
        sitemap_url = self.sitemap_url_input.text().strip()
        
        if not sitemap_url:
            self.sitemap_status_label.setText("Enter sitemap URL first")
            self.sitemap_status_label.setStyleSheet("color: #d32f2f;")
            return

        if not self._is_valid_url(sitemap_url):
            self.sitemap_status_label.setText("URL must start with http:// or https://")
            self.sitemap_status_label.setStyleSheet("color: #d32f2f;")
            return

        self.sitemap_status_label.setText("Loading sitemap...")
        self.sitemap_status_label.setStyleSheet("color: #1976d2;")

        # TODO: Call backend sitemap load through controller
        # For now, just update status
        self.sitemap_status_label.setText("Load sitemap not implemented yet")
        self.sitemap_status_label.setStyleSheet("color: #666;")

    def _on_browse_clicked(self):
        """Handle browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select URL List File",
            "",
            "Text Files (*.txt *.csv);;All Files (*)"
        )

        if file_path:
            self.urls_file_input.setText(file_path)
            self._load_urls_from_file(file_path)

    def _load_urls_from_file(self, file_path: str):
        """Load URLs from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]

            if self.append_checkbox.isChecked():
                self._collected_urls.extend(urls)
            else:
                self._collected_urls = urls

            self._update_url_summary()
        except Exception as e:
            self.sitemap_status_label.setText(f"Error loading file: {str(e)}")
            self.sitemap_status_label.setStyleSheet("color: #d32f2f;")

    def _on_output_dir_browse_clicked(self):
        """Handle output directory browse click."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir_input.text() or "outputs/"
        )

        if dir_path:
            self.output_dir_input.setText(dir_path)
            self._save_state()

    def _on_start_scan_clicked(self):
        """Handle start scan button click."""
        if not self._validate_and_update():
            return

        if not self._collected_urls:
            self.run_options_error.setText("No URLs to scan")
            return

        # Save state
        self._save_state()

        # Build config dict
        config = {
            "sitemap_url": self.sitemap_url_input.text().strip(),
            "domain": self.domain_input.text().strip(),
            "urls_file": self.urls_file_input.text().strip(),
            "manual_urls": self.manual_urls_edit.toPlainText().strip().split('\n'),
            "max_urls": self.max_urls_input.text().strip(),
            "delay": self.delay_spin.value(),
            "output_dir": self.output_dir_input.text().strip(),
            "urls": self._collected_urls,
        }

        # Emit signal
        self.start_scan_requested.emit(config)

    def _on_clear_clicked(self):
        """Handle clear button click."""
        self._collected_urls = []
        self._update_url_summary()
        self.start_scan_btn.setEnabled(False)
        self.sitemap_status_label.setText("Cleared")
        self.sitemap_status_label.setStyleSheet("color: #666;")

    def _on_export_clicked(self):
        """Handle export button click."""
        if not self._collected_urls:
            self.sitemap_status_label.setText("No URLs to export")
            self.sitemap_status_label.setStyleSheet("color: #d32f2f;")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export URL List",
            "urls_export.txt",
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self._collected_urls))
                self.sitemap_status_label.setText(f"Exported {len(self._collected_urls)} URLs")
                self.sitemap_status_label.setStyleSheet("color: #388e3c;")
            except Exception as e:
                self.sitemap_status_label.setText(f"Export error: {str(e)}")
                self.sitemap_status_label.setStyleSheet("color: #d32f2f;")

    def _update_url_summary(self):
        """Update URL summary display."""
        # Get URLs from various sources
        urls = []

        # From manual input
        manual = self.manual_urls_edit.toPlainText().strip()
        if manual:
            urls.extend([u.strip() for u in manual.split('\n') if u.strip()])

        # From file (if already loaded)
        # Note: This is simplified - in real implementation, we'd track file URLs separately

        # Total
        total = len(urls)
        self.total_urls_label.setText(f"Total: {total}")

        # Valid URLs (simple filter)
        valid = len([u for u in urls if self._is_valid_url(u)])
        self.valid_urls_label.setText(f"Valid: {valid}")

        # Update preview list
        self.url_preview_list.clear()
        for url in urls[:10]:
            item = QListWidgetItem(url)
            self.url_preview_list.addItem(item)

        # Warning
        if valid < total and total > 0:
            self.warning_label.setText(f"Warning: {total - valid} URLs invalid")
        else:
            self.warning_label.setText("")
