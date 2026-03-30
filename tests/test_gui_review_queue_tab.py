"""
Tests for gui/tabs/review_queue_tab.py - ReviewQueueTab structure verification

Note: Full instantiation requires QApplication, so we test structure.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import inspect


class TestReviewQueueTabStructure:
    """Test ReviewQueueTab class structure."""

    def test_class_importable(self):
        """Test ReviewQueueTab can be imported."""
        from gui.tabs.review_queue_tab import ReviewQueueTab
        assert ReviewQueueTab is not None

    def test_accepts_review_controller_param(self):
        """Test __init__ accepts review_controller parameter."""
        from gui.tabs.review_queue_tab import ReviewQueueTab
        
        source = inspect.getsource(ReviewQueueTab.__init__)
        assert "review_controller: ReviewController" in source

    def test_has_summary_labels(self):
        """Test has queue summary labels."""
        from gui.tabs.review_queue_tab import ReviewQueueTab
        
        source = inspect.getsource(ReviewQueueTab)
        assert "total_label" in source
        assert "pending_label" in source
        assert "needs_fix_label" in source
        assert "reviewed_label" in source
        assert "fixed_label" in source

    def test_has_table_view(self):
        """Test has QTableView for review queue."""
        from gui.tabs.review_queue_tab import ReviewQueueTab
        
        source = inspect.getsource(ReviewQueueTab)
        assert "table_view" in source
        assert "QTableView" in source
        assert "ReviewTableModel" in source

    def test_has_details_panel(self):
        """Test has details panel components."""
        from gui.tabs.review_queue_tab import ReviewQueueTab
        
        source = inspect.getsource(ReviewQueueTab)
        assert "detail_url" in source
        assert "detail_title" in source
        assert "detail_score" in source
        assert "detail_reason" in source
        assert "detail_note" in source
        assert "status_combo" in source

    def test_has_action_buttons(self):
        """Test has action buttons."""
        from gui.tabs.review_queue_tab import ReviewQueueTab
        
        source = inspect.getsource(ReviewQueueTab)
        assert "open_page_btn" in source
        assert "mark_reviewed_btn" in source
        assert "mark_needs_fix_btn" in source
        assert "mark_fixed_btn" in source
        assert "remove_btn" in source
        assert "next_btn" in source

    def test_connects_to_controller_signals(self):
        """Test connects to controller signals."""
        from gui.tabs.review_queue_tab import ReviewQueueTab
        
        source = inspect.getsource(ReviewQueueTab._connect_signals)
        assert "queue_updated" in source
        assert "selection_changed" in source
        assert "all_reviewed" in source

    def test_has_empty_state(self):
        """Test has empty state method."""
        from gui.tabs.review_queue_tab import ReviewQueueTab
        
        source = inspect.getsource(ReviewQueueTab)
        assert "_set_empty_state" in source

    def test_has_note_dialog(self):
        """Test has NoteDialog class."""
        from gui.tabs.review_queue_tab import NoteDialog
        
        source = inspect.getsource(NoteDialog)
        assert "QDialog" in source
        assert "get_note" in source

    def test_review_status_values(self):
        """Test status combo has correct values."""
        from gui.tabs.review_queue_tab import ReviewQueueTab
        
        source = inspect.getsource(ReviewQueueTab._create_details_panel)
        assert "pending" in source
        assert "reviewed" in source
        assert "needs_fix" in source
        assert "fixed" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])