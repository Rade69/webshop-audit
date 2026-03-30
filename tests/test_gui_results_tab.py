"""
Tests for gui/tabs/results_tab.py - ResultsTab structure verification

Note: Full instantiation requires QApplication, so we test structure.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import inspect


class TestResultsTabStructure:
    """Test ResultsTab class structure."""

    def test_class_importable(self):
        """Test ResultsTab can be imported."""
        from gui.tabs.results_tab import ResultsTab
        assert ResultsTab is not None

    def test_has_mark_for_review_signal(self):
        """Test mark_for_review_requested signal is defined."""
        from gui.tabs.results_tab import ResultsTab
        
        source = inspect.getsource(ResultsTab)
        assert "mark_for_review_requested = pyqtSignal(str)" in source

    def test_accepts_results_controller_param(self):
        """Test __init__ accepts results_controller parameter."""
        from gui.tabs.results_tab import ResultsTab
        
        source = inspect.getsource(ResultsTab.__init__)
        assert "results_controller: ResultsController" in source

    def test_has_filter_bar_components(self):
        """Test has filter bar components."""
        from gui.tabs.results_tab import ResultsTab
        
        source = inspect.getsource(ResultsTab)
        assert "category_combo" in source
        assert "min_score_spin" in source
        assert "max_score_spin" in source
        assert "search_input" in source

    def test_has_table_view(self):
        """Test has QTableView for results."""
        from gui.tabs.results_tab import ResultsTab
        
        source = inspect.getsource(ResultsTab)
        assert "table_view" in source
        assert "QTableView" in source
        assert "ResultsTableModel" in source
        assert "ResultsFilterModel" in source

    def test_has_details_panel(self):
        """Test has details panel components."""
        from gui.tabs.results_tab import ResultsTab
        
        source = inspect.getsource(ResultsTab)
        assert "detail_url" in source
        assert "detail_title" in source
        assert "detail_schema_product" in source
        assert "detail_price_schema" in source
        assert "detail_flags" in source
        # Note: ResultsTab shows signals, not note (note is in ReviewQueueTab)

    def test_has_action_buttons(self):
        """Test has action buttons."""
        from gui.tabs.results_tab import ResultsTab
        
        source = inspect.getsource(ResultsTab)
        assert "open_page_btn" in source
        assert "mark_review_btn" in source
        assert "export_btn" in source

    def test_connects_to_controller_signals(self):
        """Test connects to controller signals."""
        from gui.tabs.results_tab import ResultsTab
        
        source = inspect.getsource(ResultsTab._connect_signals)
        assert "results_loaded" in source
        assert "filter_changed" in source
        assert "selection_changed" in source

    def test_has_empty_state(self):
        """Test has empty state method."""
        from gui.tabs.results_tab import ResultsTab
        
        source = inspect.getsource(ResultsTab)
        assert "_set_empty_state" in source

    def test_table_model_columns(self):
        """Test table model has correct columns."""
        from gui.tabs.results_tab import ResultsTableModel
        
        source = inspect.getsource(ResultsTableModel)
        assert "catalog_score" in source
        assert "machine_score" in source
        assert "commerce_score" in source
        assert "overall_score" in source
        assert "flags" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])