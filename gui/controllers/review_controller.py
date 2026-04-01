"""
Kontroler za Review Queue tab.

Responsibility: Upravljanje listom proizvoda za ručnu reviziju.
Učitava CSV, upravlja statusom, čuva/čita note iz JSON.
"""
import os
import json
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal as Signal
from typing import Optional

from gui.viewmodels.review_state import ReviewState


class ReviewController(QObject):
    """
    Kontroler za Review Queue tab.

    Odgovornost:
    - Učitavanje kandidata iz CSV
    - Upravljanje statusom i notama
    - Persistence u review_notes.json
    """

    # Signali
    queue_updated = Signal()
    selection_changed = Signal(dict)
    all_reviewed = Signal()

    def __init__(self):
        super().__init__()
        self._output_dir: Optional[str] = None
        self._state = ReviewState()
        self._candidates: list = []
        self._review_data: dict = {}  # {url: {status, note, added_at, added_by}}

    @property
    def state(self) -> ReviewState:
        """Vraća stanje."""
        return self._state

    @property
    def candidates(self) -> list:
        """Vraća listu kandidata."""
        return self._candidates

    def load_queue(self, output_dir: str):
        """
        Učitava review queue iz output direktorijuma.

        Args:
            output_dir: Putanja do output direktorijuma.
        """
        self._output_dir = output_dir
        self._state.output_dir = output_dir
        self._state.status = "loaded"

        # Load manual_review_candidates.csv
        csv_path = os.path.join(output_dir, "manual_review_candidates.csv")
        candidates = []

        if os.path.exists(csv_path):
            import pandas as pd
            df = pd.read_csv(csv_path)
            # Add manually added marker
            for _, row in df.iterrows():
                candidate = row.to_dict()
                candidate["added_by"] = "auto"
                candidates.append(candidate)

        # Load review notes
        self._load_review_notes(output_dir)

        self._candidates = candidates
        self._update_counts()
        self.queue_updated.emit()

    def _load_review_notes(self, output_dir: str):
        """Load review notes from JSON."""
        notes_path = os.path.join(output_dir, "review_notes.json")
        if os.path.exists(notes_path):
            with open(notes_path, 'r', encoding='utf-8') as f:
                self._review_data = json.load(f)
        else:
            self._review_data = {}

    def _save_review_notes(self):
        """Save review notes to JSON."""
        if not self._output_dir:
            return
        notes_path = os.path.join(self._output_dir, "review_notes.json")
        with open(notes_path, 'w', encoding='utf-8') as f:
            json.dump(self._review_data, f, indent=2, ensure_ascii=False)

    def _update_counts(self):
        """Update state counts."""
        self._state.total_count = len(self._candidates)
        self._state.pending_count = 0
        self._state.needs_fix_count = 0
        self._state.reviewed_count = 0
        self._state.fixed_count = 0
        self._state.manually_added_count = 0

        for candidate in self._candidates:
            url = candidate.get("url", "")
            status = self._review_data.get(url, {}).get("status", "pending")
            added_by = candidate.get("added_by", "auto")

            if status == "pending":
                self._state.pending_count += 1
            elif status == "needs_fix":
                self._state.needs_fix_count += 1
            elif status == "reviewed":
                self._state.reviewed_count += 1
            elif status == "fixed":
                self._state.fixed_count += 1

            if added_by == "manual":
                self._state.manually_added_count += 1

        # Check if all reviewed
        if self._state.pending_count == 0 and self._state.total_count > 0:
            self.all_reviewed.emit()

    def add_to_queue(self, url: str):
        """
        Dodaje URL u review queue ručno.

        Args:
            url: URL proizvoda.
        """
        # Check if already in queue
        if any(c.get("url") == url for c in self._candidates):
            return

        candidate = {
            "url": url,
            "added_by": "manual",
            "reason": "Manually Added"
        }
        self._candidates.append(candidate)

        # Initialize review data
        self._review_data[url] = {
            "status": "pending",
            "note": "",
            "added_at": datetime.now().isoformat(),
            "added_by": "manual"
        }

        self._update_counts()
        self._save_review_notes()
        self.queue_updated.emit()

    def remove_from_queue(self, url: str):
        """
        Uklanja proizvod iz review queue.

        Args:
            url: URL proizvoda.
        """
        self._candidates = [c for c in self._candidates if c.get("url") != url]
        if url in self._review_data:
            del self._review_data[url]

        self._update_counts()
        self._save_review_notes()
        self.queue_updated.emit()

    def get_candidates(self) -> list:
        """Vraća listu kandidata sa statusom."""
        result = []
        for candidate in self._candidates:
            url = candidate.get("url", "")
            review_info = self._review_data.get(url, {})
            candidate_copy = candidate.copy()
            candidate_copy["status"] = review_info.get("status", "pending")
            candidate_copy["note"] = review_info.get("note", "")
            candidate_copy["note_timestamp"] = review_info.get("note_timestamp", "")
            result.append(candidate_copy)
        return result

    def select_product(self, url: str):
        """Bira proizvod za pregled."""
        candidate = next((c for c in self._candidates if c.get("url") == url), {})
        review_info = self._review_data.get(url, {})
        candidate["status"] = review_info.get("status", "pending")
        candidate["note"] = review_info.get("note", "")
        self._state.selected_product = candidate
        self.selection_changed.emit(candidate)

    def get_selected_product(self) -> Optional[dict]:
        """Vraća selektovani proizvod."""
        return self._state.selected_product

    def set_status(self, url: str, status: str):
        """
        Postavlja status za proizvod.

        Args:
            url: URL proizvoda
            status: Status ("pending", "reviewed", "needs_fix", "fixed")
        """
        if url not in self._review_data:
            self._review_data[url] = {"note": "", "added_at": datetime.now().isoformat()}

        self._review_data[url]["status"] = status

        self._update_counts()
        self._save_review_notes()
        self.queue_updated.emit()

    def set_note(self, url: str, note: str):
        """
        Postavlja notu za proizvod.

        Args:
            url: URL proizvoda
            note: Nota tekst
        """
        if url not in self._review_data:
            self._review_data[url] = {"status": "pending", "added_at": datetime.now().isoformat()}

        self._review_data[url]["note"] = note
        self._review_data[url]["note_timestamp"] = datetime.now().isoformat()

        self._save_review_notes()

    def get_note(self, url: str) -> str:
        """Vraća notu za URL."""
        return self._review_data.get(url, {}).get("note", "")

    def get_status(self, url: str) -> str:
        """Vraća status za URL."""
        return self._review_data.get(url, {}).get("status", "pending")

    def get_review_data(self, url: str) -> dict:
        """Vraća kompletne review podatke za URL."""
        return self._review_data.get(url, {})

    def get_reason(self, candidate: dict) -> str:
        """Get human-readable reason for queue entry."""
        reasons = []
        
        # Use new severity and reasons columns if available
        severity = candidate.get("severity", "")
        reason_str = candidate.get("reasons", "")
        
        if severity:
            reasons.append(f"Severity: {severity}")
        
        if reason_str:
            # Convert machine-readable reasons to human-readable
            reason_map = {
                "fetch-error": "Fetch Error",
                "non-200": "Non-200 Status",
                "not-product-page": "Not Product Page",
                "js-rendered-high": "JS Rendered (High Risk)",
                "js-rendered-medium": "JS Rendered (Medium Risk)",
                "js-rendered": "JS Rendered",
                "noindex": "Noindex",
                "canonical-mismatch": "Canonical Mismatch",
                "missing-price-critical": "Missing Price (Critical)",
                "missing-schema-critical": "Missing Schema (Critical)",
                "missing-price": "Missing Price",
                "missing-schema": "Missing Schema",
                "low-content": "Low Content",
                "low-score": "Low Score",
            }
            
            for reason in reason_str.split(", "):
                if reason in reason_map:
                    reasons.append(reason_map[reason])
                elif reason:
                    reasons.append(reason)
        
        # Fallback to old flags if new columns not available
        if not reasons:
            if candidate.get("flag_noindex"):
                reasons.append("Noindex")
            if candidate.get("flag_canonical_mismatch"):
                reasons.append("Canonical Mismatch")
            if candidate.get("flag_js_rendered"):
                reasons.append("JS Rendered")
            if candidate.get("suspicious_schema_missing"):
                reasons.append("Missing Schema")
            if candidate.get("suspicious_price_missing"):
                reasons.append("Missing Price")
            if candidate.get("suspicious_low_content"):
                reasons.append("Low Content")
        
        if candidate.get("added_by") == "manual":
            reasons.append("Manually Added")

        return ", ".join(reasons) if reasons else "Review Candidate"