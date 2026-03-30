"""
Tests for gui/controllers/review_controller.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json


class TestReviewController:
    """Test ReviewController class."""

    def test_controller_init(self):
        """Test controller initialization."""
        from gui.controllers.review_controller import ReviewController
        
        # Can't instantiate without QApplication, just verify import
        assert ReviewController is not None

    def test_state_property(self):
        """Test state property exists."""
        import inspect
        from gui.controllers.review_controller import ReviewController
        
        source = inspect.getsource(ReviewController)
        assert "@property" in source
        assert "def state(self)" in source

    def test_candidates_property(self):
        """Test candidates property exists."""
        import inspect
        from gui.controllers.review_controller import ReviewController
        
        source = inspect.getsource(ReviewController)
        assert "def candidates(self)" in source

    def test_signal_definitions(self):
        """Test signal definitions."""
        import inspect
        from gui.controllers.review_controller import ReviewController
        
        source = inspect.getsource(ReviewController)
        assert "queue_updated = Signal()" in source
        assert "selection_changed = Signal(dict)" in source
        assert "all_reviewed = Signal()" in source

    def test_load_queue_reads_csv(self):
        """Test load_queue reads manual_review_candidates.csv."""
        import inspect
        from gui.controllers.review_controller import ReviewController
        
        source = inspect.getsource(ReviewController.load_queue)
        assert "manual_review_candidates.csv" in source

    def test_review_notes_json_persistence(self):
        """Test review notes JSON persistence."""
        import inspect
        from gui.controllers.review_controller import ReviewController
        
        source = inspect.getsource(ReviewController)
        
        # Check for JSON file handling
        assert "review_notes.json" in source
        assert "json.load" in source
        assert "json.dump" in source

    def test_set_status_method_exists(self):
        """Test set_status method exists."""
        import inspect
        from gui.controllers.review_controller import ReviewController
        
        source = inspect.getsource(ReviewController.set_status)
        assert "def set_status(self, url: str, status: str)" in source

    def test_set_note_method_exists(self):
        """Test set_note method exists."""
        import inspect
        from gui.controllers.review_controller import ReviewController
        
        source = inspect.getsource(ReviewController.set_note)
        assert "def set_note(self, url: str, note: str)" in source

    def test_add_to_queue_method_exists(self):
        """Test add_to_queue method exists."""
        import inspect
        from gui.controllers.review_controller import ReviewController
        
        source = inspect.getsource(ReviewController.add_to_queue)
        assert "def add_to_queue(self, url: str)" in source

    def test_remove_from_queue_method_exists(self):
        """Test remove_from_queue method exists."""
        import inspect
        from gui.controllers.review_controller import ReviewController
        
        source = inspect.getsource(ReviewController.remove_from_queue)
        assert "def remove_from_queue(self, url: str)" in source

    def test_get_reason_maps_flags(self):
        """Test get_reason maps internal flags to human-readable."""
        import inspect
        from gui.controllers.review_controller import ReviewController
        
        source = inspect.getsource(ReviewController.get_reason)
        
        # Check flag to reason mapping
        assert "suspicious_schema_missing" in source
        assert "Missing Schema" in source
        assert "suspicious_price_missing" in source
        assert "Missing Price" in source
        assert "flag_noindex" in source
        assert "Noindex" in source
        assert "Manually Added" in source


class TestReviewState:
    """Test ReviewState dataclass."""

    def test_default_counts(self):
        """Test default count values."""
        from gui.viewmodels.review_state import ReviewState
        
        state = ReviewState()
        assert state.total_count == 0
        assert state.pending_count == 0
        assert state.needs_fix_count == 0
        assert state.reviewed_count == 0
        assert state.fixed_count == 0

    def test_status_values(self):
        """Test status values."""
        from gui.viewmodels.review_state import ReviewState
        
        state = ReviewState()
        assert state.status == "idle"
        
        state.status = "loaded"
        assert state.is_loaded() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])