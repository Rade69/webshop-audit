"""
ViewModel for Results tab state.

Responsibility: Storing and accessing data about audit results.
This is a plain data class without logic - just data structure.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResultsState:
    """
    State of audit results.

    Attributes:
        status: State of results ("idle", "loaded", "filtered")
        output_dir: Path to output directory
        total_count: Total number of products
        filtered_count: Number of products after filtering
        categories: Available breadcrumb categories
        current_filter: Current filter type
        selected_product: Currently selected product data
    """
    status: str = "idle"
    output_dir: str = ""
    total_count: int = 0
    filtered_count: int = 0
    categories: list[str] = field(default_factory=list)
    current_filter: str = "all"
    selected_product: Optional[dict] = None

    # Filter state
    filter_category: str = ""
    filter_min_score: int = 0
    filter_max_score: int = 100
    filter_missing_schema: bool = False
    filter_missing_price: bool = False
    filter_noindex: bool = False
    filter_canonical_issues: bool = False
    filter_shortlist_only: bool = False
    filter_show_non_product: bool = True
    search_text: str = ""

    def reset(self):
        """Reset state to initial values."""
        self.status = "idle"
        self.output_dir = ""
        self.total_count = 0
        self.filtered_count = 0
        self.categories = []
        self.current_filter = "all"
        self.selected_product = None
        self.filter_category = ""
        self.filter_min_score = 0
        self.filter_max_score = 100
        self.filter_missing_schema = False
        self.filter_missing_price = False
        self.filter_noindex = False
        self.filter_canonical_issues = False
        self.filter_shortlist_only = False
        self.filter_show_non_product = True
        self.search_text = ""

    def is_loaded(self) -> bool:
        """Check if results are loaded."""
        return self.status in ("loaded", "filtered")

    def is_idle(self) -> bool:
        """Check if state is idle."""
        return self.status == "idle"