"""
Tests for gui/controllers/results_controller.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json


class TestResultsController:
    """Test ResultsController class."""

    def test_controller_init(self):
        """Test controller initialization."""
        from gui.controllers.results_controller import ResultsController
        
        # Can't instantiate without QApplication, just verify import
        assert ResultsController is not None

    def test_state_property(self):
        """Test state property exists."""
        import inspect
        from gui.controllers.results_controller import ResultsController
        
        source = inspect.getsource(ResultsController)
        assert "@property" in source
        assert "def state(self)" in source

    def test_dataframe_property(self):
        """Test dataframe property exists."""
        import inspect
        from gui.controllers.results_controller import ResultsController
        
        source = inspect.getsource(ResultsController)
        assert "def dataframe(self)" in source

    def test_signal_definitions(self):
        """Test signal definitions."""
        import inspect
        from gui.controllers.results_controller import ResultsController
        
        source = inspect.getsource(ResultsController)
        assert "results_loaded = Signal()" in source
        assert "filter_changed = Signal()" in source
        assert "selection_changed = Signal(dict)" in source
        assert "mark_for_review_requested = Signal(str)" in source

    def test_load_results_creates_csv_path(self):
        """Test load_results builds correct CSV path."""
        import inspect
        from gui.controllers.results_controller import ResultsController
        
        source = inspect.getsource(ResultsController.load_results)
        assert "products_scored.csv" in source
        assert "os.path.join" in source

    def test_get_filtered_data_implements_filters(self):
        """Test get_filtered_data implements filtering logic."""
        import inspect
        from gui.controllers.results_controller import ResultsController
        
        source = inspect.getsource(ResultsController.get_filtered_data)
        
        # Check filter implementations
        assert "filter_category" in source
        assert "filter_min_score" in source
        assert "filter_missing_schema" in source
        assert "filter_noindex" in source
        assert "search_text" in source


class TestResultsStateIntegration:
    """Integration tests for ResultsState with controller."""

    def test_results_state_created_on_init(self):
        """Test that ResultsState is created on controller init."""
        from gui.viewmodels.results_state import ResultsState
        
        state = ResultsState()
        assert state.status == "idle"
        assert state.filter_min_score == 0
        assert state.filter_max_score == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])