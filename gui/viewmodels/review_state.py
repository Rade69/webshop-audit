"""
ViewModel for Review Queue tab state.

Responsibility: Storing and accessing data about review queue.
This is a plain data class without logic - just data structure.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReviewState:
    """
    State of review queue.

    Attributes:
        status: State of queue ("idle", "loaded", "empty")
        output_dir: Path to output directory
        total_count: Total number of candidates
        pending_count: Number of pending reviews
        needs_fix_count: Number needing fixes
        reviewed_count: Number reviewed
        fixed_count: Number fixed
        manually_added_count: Number manually added
        selected_product: Currently selected product data
        notes: Dictionary of notes per URL
    """
    status: str = "idle"
    output_dir: str = ""
    total_count: int = 0
    pending_count: int = 0
    needs_fix_count: int = 0
    reviewed_count: int = 0
    fixed_count: int = 0
    manually_added_count: int = 0
    selected_product: Optional[dict] = None
    notes: dict = field(default_factory=dict)

    def reset(self):
        """Reset state to initial values."""
        self.status = "idle"
        self.output_dir = ""
        self.total_count = 0
        self.pending_count = 0
        self.needs_fix_count = 0
        self.reviewed_count = 0
        self.fixed_count = 0
        self.manually_added_count = 0
        self.selected_product = None
        self.notes = {}

    def is_loaded(self) -> bool:
        """Check if queue is loaded."""
        return self.status == "loaded"

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self.total_count == 0

    def is_all_reviewed(self) -> bool:
        """Check if all candidates are reviewed (status != pending)."""
        return self.pending_count == 0 and self.total_count > 0