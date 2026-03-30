"""
Tests for gui/viewmodels/review_state.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from gui.viewmodels.review_state import ReviewState


def test_review_state_default_values():
    """Test default values."""
    state = ReviewState()
    
    assert state.status == "idle"
    assert state.output_dir == ""
    assert state.total_count == 0
    assert state.pending_count == 0
    assert state.needs_fix_count == 0
    assert state.reviewed_count == 0
    assert state.fixed_count == 0
    assert state.manually_added_count == 0
    assert state.selected_product is None
    assert state.notes == {}


def test_review_state_reset():
    """Test reset method."""
    state = ReviewState()
    state.status = "loaded"
    state.output_dir = "outputs/test"
    state.total_count = 10
    state.pending_count = 5
    state.needs_fix_count = 3
    state.notes = {"http://example.com": "test note"}
    
    state.reset()
    
    assert state.status == "idle"
    assert state.output_dir == ""
    assert state.total_count == 0
    assert state.pending_count == 0
    assert state.notes == {}


def test_review_state_is_loaded():
    """Test is_loaded method."""
    state = ReviewState()
    assert state.is_loaded() is False
    
    state.status = "loaded"
    assert state.is_loaded() is True


def test_review_state_is_empty():
    """Test is_empty method."""
    state = ReviewState()
    assert state.is_empty() is True
    
    state.total_count = 10
    assert state.is_empty() is False


def test_review_state_is_all_reviewed():
    """Test is_all_reviewed method."""
    state = ReviewState()
    assert state.is_all_reviewed() is False  # Empty, not all reviewed
    
    state.total_count = 10
    state.pending_count = 5
    assert state.is_all_reviewed() is False
    
    state.pending_count = 0
    assert state.is_all_reviewed() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])