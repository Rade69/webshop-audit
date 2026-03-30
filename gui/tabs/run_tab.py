"""
Run tab for displaying audit progress.

Responsibility: Real-time display of scan progress, statistics, logs,
and run controls during audit execution.
"""
from PyQt6.QtCore import QUrl, QTimer, pyqtSlot
from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QPlainTextEdit,
)
from PyQt6.QtGui import QDesktopServices

from gui.controllers.audit_run_controller import AuditRunController


class RunTab(QWidget):
    """
    Run tab for displaying audit progress.

    Shows real-time status, progress bar, statistics, and live log.
    Connects to AuditRunController signals for updates.
    """

    def __init__(self, audit_controller: AuditRunController, parent=None):
        """
        Initialize RunTab.

        Args:
            audit_controller: AuditRunController instance for signal connections
            parent: Parent widget
        """
        super().__init__(parent)
        self.audit_controller = audit_controller
        self._output_dir: str = ""
        self._start_time: float = 0.0

        # UI setup
        self._setup_ui()
        self._connect_signals()
        self._set_idle_state()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Status header
        status_group = self._create_status_header()
        layout.addWidget(status_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Statistics group
        stats_group = self._create_stats_group()
        layout.addWidget(stats_group)

        # Live log panel
        log_group = self._create_log_group()
        layout.addWidget(log_group, 1)  # Stretch factor 1

        # Action buttons
        actions = self._create_actions()
        layout.addWidget(actions)

    def _create_status_header(self) -> QGroupBox:
        """Create status header group."""
        group = QGroupBox("Run Status")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(8, 6, 8, 6)

        # Status label
        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("status_idle")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Phase label
        self.phase_label = QLabel("-")
        self.phase_label.setStyleSheet("color: #5B6B7F;")
        layout.addWidget(self.phase_label)

        return group

    def _create_stats_group(self) -> QGroupBox:
        """Create statistics group."""
        group = QGroupBox("Statistics")
        layout = QHBoxLayout(group)

        # Left column
        left_form = QFormLayout()
        self.total_urls_value = QLabel("-")
        self.processed_value = QLabel("-")
        self.errors_value = QLabel("-")
        left_form.addRow("Total URLs:", self.total_urls_value)
        left_form.addRow("Processed:", self.processed_value)
        left_form.addRow("Errors:", self.errors_value)
        layout.addLayout(left_form)

        # Right column
        right_form = QFormLayout()
        self.non_product_value = QLabel("-")
        self.candidates_value = QLabel("-")
        self.elapsed_value = QLabel("-")
        right_form.addRow("Non-product:", self.non_product_value)
        right_form.addRow("Candidates:", self.candidates_value)
        right_form.addRow("Elapsed:", self.elapsed_value)
        layout.addLayout(right_form)

        layout.addStretch()

        return group

    def _create_log_group(self) -> QGroupBox:
        """Create live log panel group."""
        group = QGroupBox("Live Log")
        layout = QVBoxLayout(group)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("Run will start when you click Start Scan.")
        layout.addWidget(self.log_view)

        return group

    def _create_actions(self) -> QWidget:
        """Create action buttons widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop_clicked)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setToolTip("Not supported in v1")

        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.setEnabled(False)
        self.open_output_btn.clicked.connect(self._on_open_output_clicked)

        layout.addWidget(self.stop_btn)
        layout.addWidget(self.pause_btn)
        layout.addStretch()
        layout.addWidget(self.open_output_btn)

        return widget

    def _connect_signals(self):
        """Connect to controller signals."""
        self.audit_controller.phase_changed.connect(self._on_phase_changed)
        self.audit_controller.progress_updated.connect(self._on_progress_updated)
        self.audit_controller.log_message.connect(self._on_log_message)
        self.audit_controller.stats_updated.connect(self._on_stats_updated)
        self.audit_controller.run_completed.connect(self._on_run_completed)
        self.audit_controller.run_failed.connect(self._on_run_failed)
        self.audit_controller.run_started.connect(self._on_run_started)

    def _set_idle_state(self):
        """Set UI to idle state."""
        self.status_label.setText("Idle")
        self.status_label.setStyleSheet("font-weight: bold; color: #666;")
        self.phase_label.setText("-")

        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setValue(0)

        self.total_urls_value.setText("-")
        self.processed_value.setText("-")
        self.errors_value.setText("-")
        self.non_product_value.setText("-")
        self.candidates_value.setText("-")
        self.elapsed_value.setText("-")

        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.open_output_btn.setEnabled(False)

    def _set_running_state(self):
        """Set UI to running state."""
        self.status_label.setText("Running")
        self.status_label.setStyleSheet("font-weight: bold; color: #1976d2;")

        self.stop_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)  # Not supported
        self.open_output_btn.setEnabled(False)

    def _set_completed_state(self):
        """Set UI to completed state."""
        self.status_label.setText("Completed")
        self.status_label.setStyleSheet("font-weight: bold; color: #388e3c;")

        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.open_output_btn.setEnabled(bool(self._output_dir))

    def _set_failed_state(self, error: str):
        """Set UI to failed state."""
        self.status_label.setText("Failed")
        self.status_label.setStyleSheet("font-weight: bold; color: #d32f2f;")

        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.open_output_btn.setEnabled(bool(self._output_dir))

        self._append_log(f"[ERROR] {error}", "error")

    def _set_stopped_state(self):
        """Set UI to stopped state."""
        self.status_label.setText("Stopped")
        self.status_label.setStyleSheet("font-weight: bold; color: #f57c00;")

        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.open_output_btn.setEnabled(bool(self._output_dir))

    def _append_log(self, message: str, level: str = "info"):
        """Append message to log with color formatting."""
        # Color mapping
        colors = {
            "info": "#212121",
            "warning": "#f57c00",
            "error": "#d32f2f"
        }

        # Create text format
        format = QTextCharFormat()
        format.setForeground(QColor(colors.get(level, "#212121")))

        # Append text
        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(message + "\n", format)

        # Auto-scroll to bottom
        self.log_view.setTextCursor(cursor)
        self.log_view.ensureCursorVisible()

        # Trim old lines (keep max 1000)
        doc = self.log_view.document()
        if doc.blockCount() > 1000:
            cursor = QTextCursor(doc.findBlockByLineNumber(0))
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # Remove the trailing newline

    def _phase_display_name(self, phase: str) -> str:
        """Convert phase code to display name."""
        phase_map = {
            "url_collection": "URL Collection",
            "fetch": "Fetch",
            "parse": "Parse HTML",
            "score": "Score",
            "shortlist": "Shortlist",
            "export": "Export",
            "done": "Done"
        }
        return phase_map.get(phase, phase)

    # Signal handlers

    @pyqtSlot()
    def _on_run_started(self):
        """Handle run started signal."""
        self._start_time = QTimer.currentMSecsSinceStart()
        self.log_view.clear()
        self._set_running_state()
        self._append_log("[INFO] Starting scan...", "info")

        # Start elapsed time timer
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.timeout.connect(self._update_elapsed)
        self._elapsed_timer.start(1000)

    @pyqtSlot(str)
    def _on_phase_changed(self, phase: str):
        """Handle phase changed signal."""
        display_name = self._phase_display_name(phase)
        self.phase_label.setText(display_name)

        # Set indeterminate during URL collection
        if phase == "url_collection":
            self.progress_bar.setRange(0, 0)

    @pyqtSlot(int, int)
    def _on_progress_updated(self, processed: int, total: int):
        """Handle progress updated signal."""
        if total > 0:
            # Set determinate if not already
            if self.progress_bar.minimum() == 0 and self.progress_bar.maximum() == 0:
                self.progress_bar.setRange(0, total)

            self.progress_bar.setValue(processed)
            self.processed_value.setText(str(processed))

            if total > 0:
                percentage = int((processed / total) * 100)
                self.progress_bar.setFormat(f"{percentage}% ({processed}/{total})")

    @pyqtSlot(str, str)
    def _on_log_message(self, level: str, message: str):
        """Handle log message signal."""
        prefix = {
            "info": "[INFO]",
            "warning": "[WARN]",
            "error": "[ERROR]"
        }.get(level, "[INFO]")

        self._append_log(f"{prefix} {message}", level)

    @pyqtSlot(dict)
    def _on_stats_updated(self, stats: dict):
        """Handle stats updated signal."""
        self.total_urls_value.setText(str(stats.get("total", "-")))
        self.processed_value.setText(str(stats.get("processed", "-")))
        self.errors_value.setText(str(stats.get("errors", "-")))
        self.non_product_value.setText(str(stats.get("non_product", "-")))
        self.candidates_value.setText(str(stats.get("candidates", "-")))

    @pyqtSlot(str)
    def _on_run_completed(self, output_dir: str):
        """Handle run completed signal."""
        self._output_dir = output_dir

        # Stop elapsed timer
        if hasattr(self, '_elapsed_timer'):
            self._elapsed_timer.stop()

        # Check if stopped early
        # (This would come from stats_updated, handled separately)

        self._set_completed_state()
        self._append_log(f"[INFO] Scan completed. Results saved to: {output_dir}", "info")

    @pyqtSlot(str)
    def _on_run_failed(self, error: str):
        """Handle run failed signal."""
        # Stop elapsed timer
        if hasattr(self, '_elapsed_timer'):
            self._elapsed_timer.stop()

        self._set_failed_state(error)

    def _update_elapsed(self):
        """Update elapsed time display."""
        if self._start_time > 0:
            elapsed_ms = QTimer.currentMSecsSinceStart() - self._start_time
            elapsed_sec = elapsed_ms // 1000
            minutes = elapsed_sec // 60
            seconds = elapsed_sec % 60
            self.elapsed_value.setText(f"{minutes:02d}:{seconds:02d}")

    def _on_stop_clicked(self):
        """Handle stop button click."""
        self._append_log("[INFO] Stopping scan...", "info")
        self.audit_controller.stop_run()
        # UI will update via run_completed signal

    def _on_open_output_clicked(self):
        """Handle open output folder button click."""
        if self._output_dir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._output_dir))