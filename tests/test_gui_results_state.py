"""
Tests for gui/viewmodels/results_state.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from gui.viewmodels.results_state import ResultsState


def test_results_state_default_values():
    """Test default values."""
    state = ResultsState()
    
    assert state.status == "idle"
    assert state.output_dir == ""
    assert state.total_count == 0
    assert state.filtered_count == 0
    assert state.categories == []
    assert state.current_filter == "all"
    assert state.selected_product is None


def test_results_state_filter_defaults():
    """Test default filter values."""
    state = ResultsState()
    
    assert state.filter_category == ""
    assert state.filter_min_score == 0
    assert state.filter_max_score == 100
    assert state.filter_missing_schema is False
    assert state.filter_missing_price is False
    assert state.filter_noindex is False
    assert state.filter_canonical_issues is False
    assert state.filter_shortlist_only is False
    assert state.filter_show_non_product is True
    assert state.search_text == ""


def test_results_state_reset():
    """Test reset method."""
    state = ResultsState()
    state.status = "loaded"
    state.output_dir = "outputs/test"
    state.total_count = 100
    state.filter_category = "Shoes"
    state.filter_min_score = 50
    state.search_text = "nike"
    
    state.reset()
    
    assert state.status == "idle"
    assert state.output_dir == ""
    assert state.total_count == 0
    assert state.filter_category == ""
    assert state.filter_min_score == 0
    assert state.search_text == ""


def test_results_state_is_loaded():
    """Test is_loaded method."""
    state = ResultsState()
    assert state.is_loaded() is False
    
    state.status = "loaded"
    assert state.is_loaded() is True
    
    state.status = "filtered"
    assert state.is_loaded() is True


def test_results_state_is_idle():
    """Test is_idle method."""
    state = ResultsState()
    assert state.is_idle() is True
    
    state.status = "loaded"
    assert state.is_idle() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
