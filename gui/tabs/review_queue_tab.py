"""
Review Queue tab for manual product review.

Responsibility: Working screen for reviewing flagged products,
managing notes, and setting review status.
"""
import pandas as pd
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, pyqtSlot, QUrl
from PyQt6.QtGui import QColor, QDesktopServices
from PyQt6.QtWidgets import (
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
    QScrollArea,
    QSplitter,
    QHeaderView,
    QAbstractItemView,
    QDialog,
    QTextEdit,
    QDialogButtonBox,
    QMessageBox,
)
from datetime import datetime
from PyQt6.QtCore import pyqtSignal

from gui.controllers.review_controller import ReviewController


class ReviewTableModel(QAbstractTableModel):
    """
    Table model for review queue.

    Displays: URL/Title, Reason, Overall Score, Flags, Status, Has Note.
    """

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._data = data if data is not None else []
        self._columns = ["url", "severity", "reasons", "overall_score", "status", "has_note"]
        self._headers = ["Proizvod", "Prioritet", "Razlozi", "Ocjena", "Status", "Bilješka"]  # "Product", "Severity", "Reasons", "Score", "Status", "Note"

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

        candidate = self._data[row]
        col_name = self._columns[col]

        if role == Qt.ItemDataRole.DisplayRole:
            if col_name == "url":
                url = str(candidate.get("url", "") or "")
                title = str(candidate.get("title", "") or "")
                if title:
                    return title[:40] + "..." if len(title) > 40 else title
                return url[:40] + "..." if len(url) > 40 else url
            elif col_name == "severity":
                severity = candidate.get("severity", "")
                # Map severity to Serbian
                severity_map = {
                    "CRITICAL": "KRITIČNO",
                    "HIGH": "VISOKO",
                    "MEDIUM": "SREDNJE",
                    "LOW": "NISKO"
                }
                return severity_map.get(severity, severity)
            elif col_name == "reasons":
                reasons = candidate.get("reasons", "")
                # Handle NaN/None values
                if pd.isna(reasons) or not reasons:
                    return "-"
                
                # Convert to string if it's not already
                reasons_str = str(reasons)
                if reasons_str:
                    # Show first reason only in table
                    first_reason = reasons_str.split(", ")[0]
                    reason_map = {
                        "fetch-error": "Fetch greška",
                        "non-200": "Status nije 200",
                        "not-product-page": "Nije produktna stranica",
                        "js-rendered-high": "JS render (visok rizik)",
                        "js-rendered-medium": "JS render (srednji rizik)",
                        "js-rendered": "JS render",
                        "noindex": "Noindex",
                        "canonical-mismatch": "Canonical mismatch",
                        "missing-price-critical": "Nema cijene (kritično)",
                        "missing-schema-critical": "Nema sheme (kritično)",
                        "missing-price": "Nema cijene",
                        "missing-schema": "Nema sheme",
                        "low-content": "Malo sadržaja",
                        "low-score": "Nizak score",
                    }
                    return reason_map.get(first_reason, first_reason)
                return "-"
            elif col_name == "overall_score":
                return candidate.get("overall_score", "-")
            elif col_name == "status":
                return candidate.get("status", "pending")
            elif col_name == "has_note":
                return "✓" if candidate.get("note") else "-"

        elif role == Qt.ItemDataRole.BackgroundRole:
            # First priority: severity color
            severity = candidate.get("severity", "")
            if severity == "CRITICAL":
                return QColor("#ffebee")  # Light red
            elif severity == "HIGH":
                return QColor("#fff3cd")  # Light orange
            elif severity == "MEDIUM":
                return QColor("#fff8e1")  # Light yellow
            elif severity == "LOW":
                return QColor("#e3f2fd")  # Light blue
            
            # Fallback: status color
            status = candidate.get("status", "pending")
            if status == "needs_fix":
                return QColor("#ffebee")  # Light red
            elif status == "reviewed":
                return QColor("#e8f5e9")  # Light green
            elif status == "fixed":
                return QColor("#e3f2fd")  # Light blue
            elif status == "pending":
                return QColor("#fafafa")  # Light gray

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col_name in ["severity", "overall_score", "status", "has_note"]:
                return Qt.AlignmentFlag.AlignCenter

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if section < len(self._headers):
                return self._headers[section]
        return None

    def get_candidate(self, row: int) -> dict:
        """Get candidate data at row."""
        if 0 <= row < len(self._data):
            return self._data[row]
        return {}


class NoteDialog(QDialog):
    """
    Dialog for adding/editing notes.
    """

    def __init__(self, current_note: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dodaj/Uredi bilješku")  # "Add/Edit Note"
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout(self)

        self.note_edit = QTextEdit()
        self.note_edit.setPlainText(current_note)
        self.note_edit.setPlaceholderText("Unesi bilješku...")  # "Enter note..."
        layout.addWidget(self.note_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_note(self) -> str:
        """Get note text."""
        return self.note_edit.toPlainText()


class ReviewQueueTab(QWidget):
    """
    Review Queue tab for manual product review.

    Shows queue summary, table of candidates with status badges,
    details panel with notes, and action buttons.
    """

    def __init__(self, review_controller: ReviewController, parent=None):
        """
        Initialize ReviewQueueTab.

        Args:
            review_controller: ReviewController instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.review_controller = review_controller
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

        # Pregled reda — u GroupBox-u
        summary_group = QGroupBox("Pregled reda")  # "Queue Summary"
        summary_group_layout = QVBoxLayout(summary_group)
        summary_group_layout.setContentsMargins(8, 8, 8, 8)
        summary_group_layout.setSpacing(0)
        summary = self._create_summary()
        summary_group_layout.addWidget(summary)
        layout.addWidget(summary_group)

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

    def _create_summary(self) -> QWidget:
        """Create queue summary widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("<b>Pregled reda:</b>"))  # "<b>Queue Summary:</b>"

        self.total_label = QLabel("Ukupno: 0")  # "Total: 0"
        layout.addWidget(self.total_label)

        self.pending_label = QLabel("Na čekanju: 0")  # "Pending: 0"
        self.pending_label.setStyleSheet(
            "background: #F3F4F6; color: #4B5563; padding: 3px 10px; border-radius: 10px;"
        )
        layout.addWidget(self.pending_label)

        self.needs_fix_label = QLabel("Treba popravku: 0")  # "Needs Fix: 0"
        self.needs_fix_label.setStyleSheet(
            "background: #FEE2E2; color: #B53A3A; padding: 3px 10px; border-radius: 10px;"
        )
        layout.addWidget(self.needs_fix_label)

        self.reviewed_label = QLabel("Pregledano: 0")  # "Reviewed: 0"
        self.reviewed_label.setStyleSheet(
            "background: #DCFCE7; color: #2E7D32; padding: 3px 10px; border-radius: 10px;"
        )
        layout.addWidget(self.reviewed_label)

        self.fixed_label = QLabel("Popravljeno: 0")  # "Fixed: 0"
        self.fixed_label.setStyleSheet(
            "background: #D8E5F0; color: #26629E; padding: 3px 10px; border-radius: 10px;"
        )
        layout.addWidget(self.fixed_label)

        self.manual_label = QLabel("Ručno: 0")  # "Manual: 0"
        layout.addWidget(self.manual_label)

        layout.addStretch()

        self.all_reviewed_label = QLabel("")
        self.all_reviewed_label.setStyleSheet("color: #2E7D32; font-weight: bold;")
        layout.addWidget(self.all_reviewed_label)

        return widget

    def _create_table_view(self) -> QWidget:
        """Create table view widget."""
        from gui.widgets.delegates import StatusDelegate

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table_view = QTableView()
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.clicked.connect(self._on_row_clicked)

        self.table_model = ReviewTableModel()
        self.table_view.setModel(self.table_model)

        # Set delegate for status column (index 4)
        self.status_delegate = StatusDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(4, self.status_delegate)

        # Additional table styling
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setDefaultSectionSize(32)
        self.table_view.verticalHeader().setVisible(False)

        layout.addWidget(self.table_view)

        return container

    def _create_details_panel(self) -> QWidget:
        """Create details panel widget."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(350)

        container = QWidget()
        layout = QVBoxLayout(container)

        # Product info section
        info_group = QGroupBox("Informacije o proizvodu")  # "Product Info"
        info_layout = QFormLayout(info_group)
        self.detail_url = QLabel("-")
        self.detail_url.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.detail_title = QLabel("-")
        self.detail_score = QLabel("-")
        info_layout.addRow("URL:", self.detail_url)
        info_layout.addRow("Naslov:", self.detail_title)  # "Title:"
        info_layout.addRow("Ocjena:", self.detail_score)  # "Score:"
        layout.addWidget(info_group)

        # Reason section
        reason_group = QGroupBox("Razlog")  # "Reason"
        reason_layout = QFormLayout(reason_group)
        self.detail_reason = QLabel("-")
        self.detail_flags = QLabel("-")
        reason_layout.addRow("Razlozi:", self.detail_reason)  # "Reasons:"
        reason_layout.addRow("Oznake:", self.detail_flags)  # "Flags:"
        layout.addWidget(reason_group)

        # Note section
        note_group = QGroupBox("Bilješka")  # "Note"
        note_layout = QFormLayout(note_group)
        self.detail_note = QLabel("-")
        self.detail_note.setWordWrap(True)
        self.detail_note_timestamp = QLabel("")
        self.detail_note_timestamp.setStyleSheet("color: #666; font-size: 10px;")
        note_layout.addRow("Trenutna:", self.detail_note)  # "Current:"
        note_layout.addRow("Ažurirano:", self.detail_note_timestamp)  # "Updated:"
        layout.addWidget(note_group)

        # Actions within panel
        note_actions = QHBoxLayout()
        self.edit_note_btn = QPushButton("Uredi bilješku")  # "Edit Note"
        self.edit_note_btn.clicked.connect(self._on_edit_note)
        note_actions.addWidget(self.edit_note_btn)

        self.status_combo = QComboBox()
        # Values are internal keys — display text is Serbian, data stays English
        self.status_combo.addItem("Na čekanju", "pending")    # "pending"
        self.status_combo.addItem("Pregledano", "reviewed")   # "reviewed"
        self.status_combo.addItem("Treba popravku", "needs_fix")  # "needs_fix"
        self.status_combo.addItem("Popravljeno", "fixed")     # "fixed"
        self.status_combo.currentIndexChanged.connect(self._on_status_changed)
        note_actions.addWidget(QLabel("Status:"))
        note_actions.addWidget(self.status_combo)
        note_actions.addStretch()
        layout.addLayout(note_actions)

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

        self.mark_reviewed_btn = QPushButton("Označi kao pregledano")  # "Mark Reviewed"
        self.mark_reviewed_btn.setEnabled(False)
        self.mark_reviewed_btn.clicked.connect(lambda: self._on_change_status("reviewed"))

        self.mark_needs_fix_btn = QPushButton("Označi za popravku")  # "Mark Needs Fix"
        self.mark_needs_fix_btn.setEnabled(False)
        self.mark_needs_fix_btn.clicked.connect(lambda: self._on_change_status("needs_fix"))

        self.mark_fixed_btn = QPushButton("Označi kao popravljeno")  # "Mark Fixed"
        self.mark_fixed_btn.setEnabled(False)
        self.mark_fixed_btn.clicked.connect(lambda: self._on_change_status("fixed"))

        self.remove_btn = QPushButton("Ukloni iz reda")  # "Remove from Queue"
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self._on_remove)

        self.next_btn = QPushButton("Sljedeći kandidat")  # "Next Candidate"
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self._on_next)

        layout.addWidget(self.open_page_btn)
        layout.addWidget(self.mark_reviewed_btn)
        layout.addWidget(self.mark_needs_fix_btn)
        layout.addWidget(self.mark_fixed_btn)
        layout.addWidget(self.remove_btn)
        layout.addStretch()
        layout.addWidget(self.next_btn)

        return widget

    def _connect_signals(self):
        """Connect signals."""
        self.review_controller.queue_updated.connect(self._on_queue_updated)
        self.review_controller.selection_changed.connect(self._on_selection_changed)
        self.review_controller.all_reviewed.connect(self._on_all_reviewed)

    def _set_empty_state(self):
        """Set empty state."""
        self.table_model.update_data([])
        self._clear_details()
        self._set_buttons_enabled(False)
        self._update_summary()

    def _set_buttons_enabled(self, enabled: bool):
        """Enable/disable action buttons."""
        self.open_page_btn.setEnabled(enabled)
        self.mark_reviewed_btn.setEnabled(enabled)
        self.mark_needs_fix_btn.setEnabled(enabled)
        self.mark_fixed_btn.setEnabled(enabled)
        self.remove_btn.setEnabled(enabled)
        self.next_btn.setEnabled(enabled)

    def _clear_details(self):
        """Clear details panel."""
        self.detail_url.setText("-")
        self.detail_title.setText("-")
        self.detail_score.setText("-")
        self.detail_reason.setText("-")
        self.detail_flags.setText("-")
        self.detail_note.setText("Još nema bilješke.")  # "No note yet."
        self.detail_note_timestamp.setText("")
        self.status_combo.setCurrentIndex(0)

    def _update_summary(self):
        """Update queue summary."""
        state = self.review_controller.state
        self.total_label.setText(f"Ukupno: {state.total_count}")  # "Total: ..."
        self.pending_label.setText(f"Na čekanju: {state.pending_count}")  # "Pending: ..."
        self.needs_fix_label.setText(f"Treba popravku: {state.needs_fix_count}")  # "Needs Fix: ..."
        self.reviewed_label.setText(f"Pregledano: {state.reviewed_count}")  # "Reviewed: ..."
        self.fixed_label.setText(f"Popravljeno: {state.fixed_count}")  # "Fixed: ..."
        self.manual_label.setText(f"Ručno: {state.manually_added_count}")  # "Manual: ..."

    @pyqtSlot()
    def _on_queue_updated(self):
        """Handle queue updated signal."""
        candidates = self.review_controller.get_candidates()
        self.table_model.update_data(candidates)
        self._update_summary()

    @pyqtSlot(dict)
    def _on_selection_changed(self, candidate: dict):
        """Handle selection changed."""
        self._show_details(candidate)

    @pyqtSlot()
    def _on_all_reviewed(self):
        """Handle all reviewed signal."""
        self.all_reviewed_label.setText("✓ Svi kandidati su pregledani!")  # "✓ All candidates reviewed!"
        self.next_btn.setEnabled(False)

    def _on_row_clicked(self, index: QModelIndex):
        """Handle row click."""
        row = index.row()
        candidate = self.table_model.get_candidate(row)
        self._current_url = candidate.get("url", "")
        self._show_details(candidate)
        self._set_buttons_enabled(True)

    def _show_details(self, candidate: dict):
        """Show candidate details in panel."""
        url = candidate.get("url", "")

        # Product info
        self.detail_url.setText(f'<a href="{url}">{url}</a>')
        self.detail_title.setText(str(candidate.get("title", "-")))
        self.detail_score.setText(str(candidate.get("overall_score", "-")))

        # Severity and reasons
        severity = candidate.get("severity", "")
        reasons = candidate.get("reasons", "")
        
        # Map severity to Serbian
        severity_map = {
            "CRITICAL": "KRITIČNO",
            "HIGH": "VISOKO",
            "MEDIUM": "SREDNJE",
            "LOW": "NISKO"
        }
        severity_display = severity_map.get(severity, severity)
        
        # Map reasons to Serbian
        reason_map = {
            "fetch-error": "Fetch greška",
            "non-200": "Status nije 200",
            "not-product-page": "Nije produktna stranica",
            "js-rendered-high": "JS render (visok rizik)",
            "js-rendered-medium": "JS render (srednji rizik)",
            "js-rendered": "JS render",
            "noindex": "Noindex",
            "canonical-mismatch": "Canonical mismatch",
            "missing-price-critical": "Nema cijene (kritično)",
            "missing-schema-critical": "Nema sheme (kritično)",
            "missing-price": "Nema cijene",
            "missing-schema": "Nema sheme",
            "low-content": "Malo sadržaja",
            "low-score": "Nizak score",
        }
        
        reason_list = []
        if severity_display:
            reason_list.append(f"Prioritet: {severity_display}")
        
        # Handle NaN/None values
        if not pd.isna(reasons) and reasons:
            reasons_str = str(reasons)
            for reason in reasons_str.split(", "):
                if reason in reason_map:
                    reason_list.append(reason_map[reason])
                elif reason:
                    reason_list.append(reason)
        
        # Fallback to old method if no new data
        if not reason_list:
            reason = self.review_controller.get_reason(candidate)
            self.detail_reason.setText(reason)
            self.detail_flags.setText("Nema")
        else:
            self.detail_reason.setText("\n".join(reason_list))
            self.detail_flags.setText("")

        # Note
        note = self.review_controller.get_note(url)
        self.detail_note.setText(note if note else "Još nema bilješke.")  # "No note yet."

        # Get timestamp from controller
        review_data = self.review_controller.get_review_data(url)
        timestamp = review_data.get("note_timestamp", "")
        if timestamp:
            self.detail_note_timestamp.setText(timestamp[:19].replace("T", " "))
        else:
            self.detail_note_timestamp.setText("")

        # Status
        status = self.review_controller.get_status(url)
        index = self.status_combo.findData(status)  # find by English key
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

    def _on_open_page(self):
        """Open selected page in browser."""
        if self._current_url:
            QDesktopServices.openUrl(QUrl(self._current_url))

    def _on_status_changed(self, _):
        """Handle status combo change."""
        if self._current_url:
            status = self.status_combo.currentData()  # English key, e.g. "pending"
            self.review_controller.set_status(self._current_url, status)

    def _on_change_status(self, status: str):
        """Change status via button."""
        if self._current_url:
            self.review_controller.set_status(self._current_url, status)
            index = self.status_combo.findData(status)  # find by English key
            if index >= 0:
                self.status_combo.setCurrentIndex(index)

    def _on_edit_note(self):
        """Open note editor dialog."""
        if not self._current_url:
            return

        current_note = self.review_controller.get_note(self._current_url)
        dialog = NoteDialog(current_note, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            note = dialog.get_note()
            self.review_controller.set_note(self._current_url, note)
            self.detail_note.setText(note if note else "Još nema bilješke.")  # "No note yet."

    def _on_remove(self):
        """Remove from queue."""
        if not self._current_url:
            return

        reply = QMessageBox.question(
            self,
            "Ukloni iz reda",  # "Remove from Queue"
            "Jeste li sigurni da želite ukloniti ovaj proizvod iz reda?",  # "Are you sure you want to remove this product from the queue?"
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.review_controller.remove_from_queue(self._current_url)
            self._current_url = ""
            self._clear_details()
            self._set_buttons_enabled(False)

    def _on_next(self):
        """Select next pending candidate."""
        candidates = self.review_controller.get_candidates()
        for candidate in candidates:
            if candidate.get("status") == "pending":
                self._current_url = candidate.get("url", "")
                self._show_details(candidate)

                # Select in table
                for i in range(self.table_model.rowCount()):
                    if self.table_model.get_candidate(i).get("url") == self._current_url:
                        self.table_view.selectRow(i)
                        break
                break