"""
Tests for gui/styles/theme.py and gui/widgets/delegates.py

Tests the light analytical theme and custom delegates.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import inspect


class TestThemeColors:
    """Test theme color palette."""

    def test_colors_dict_exists(self):
        """Test COLORS dict exists."""
        from gui.styles.theme import COLORS
        assert COLORS is not None
        assert isinstance(COLORS, dict)

    def test_required_colors_present(self):
        """Test all required colors are present."""
        from gui.styles.theme import COLORS
        
        required = [
            "bg_main", "bg_surface", "bg_input", "bg_table",
            "text_primary", "text_secondary", "accent",
            "score_high", "score_mid", "score_low",
            "status_pending", "status_needs_fix", "status_reviewed", "status_fixed"
        ]
        
        for color in required:
            assert color in COLORS, f"Missing color: {color}"

    def test_light_theme_not_dark(self):
        """Test light theme uses light background."""
        from gui.styles.theme import COLORS
        
        # Light theme should have light background (starts with #EEF or #F)
        assert COLORS["bg_main"].startswith("#EEF") or COLORS["bg_main"].startswith("#F")
        # Text should be dark
        assert COLORS["text_primary"].startswith("#1") or COLORS["text_primary"].startswith("#2")


class TestThemeFunctions:
    """Test theme functions."""

    def test_build_stylesheet_exists(self):
        """Test build_stylesheet function exists."""
        from gui.styles.theme import build_stylesheet
        assert build_stylesheet is not None

    def test_build_stylesheet_returns_string(self):
        """Test build_stylesheet returns string."""
        from gui.styles.theme import build_stylesheet
        result = build_stylesheet()
        assert isinstance(result, str)
        assert len(result) > 1000  # Should have substantial content

    def test_apply_theme_exists(self):
        """Test apply_theme function exists."""
        from gui.styles.theme import apply_theme
        assert apply_theme is not None

    def test_stylesheet_contains_qss(self):
        """Test stylesheet contains QSS."""
        from gui.styles.theme import build_stylesheet
        
        sheet = build_stylesheet()
        assert "QMainWindow" in sheet
        assert "QPushButton" in sheet
        assert "QTableView" in sheet


class TestDelegates:
    """Test custom delegates."""

    def test_score_delegate_importable(self):
        """Test ScoreDelegate can be imported."""
        from gui.widgets.delegates import ScoreDelegate
        assert ScoreDelegate is not None

    def test_status_delegate_importable(self):
        """Test StatusDelegate can be imported."""
        from gui.widgets.delegates import StatusDelegate
        assert StatusDelegate is not None

    def test_flag_delegate_importable(self):
        """Test FlagDelegate can be imported."""
        from gui.widgets.delegates import FlagDelegate
        assert FlagDelegate is not None

    def test_score_delegate_has_badge_colors(self):
        """Test ScoreDelegate has _badge_colors method."""
        from gui.widgets.delegates import ScoreDelegate
        
        source = inspect.getsource(ScoreDelegate)
        assert "def _badge_colors(self, score: int)" in source
        assert "score_high" in source
        assert "score_mid" in source
        assert "score_low" in source

    def test_status_delegate_has_badge_colors(self):
        """Test StatusDelegate has _badge_colors method."""
        from gui.widgets.delegates import StatusDelegate
        
        source = inspect.getsource(StatusDelegate)
        assert "def _badge_colors(self, status: str)" in source
        assert "LABELS" in source

    def test_status_delegate_labels(self):
        """Test StatusDelegate has correct status labels."""
        from gui.widgets.delegates import StatusDelegate
        
        # Check the LABELS dict
        assert hasattr(StatusDelegate, "LABELS")
        labels = StatusDelegate.LABELS
        assert "pending" in labels
        assert "needs_fix" in labels
        assert "reviewed" in labels
        assert "fixed" in labels


class TestDelegatesInTabs:
    """Test delegates are used in tabs."""

    def test_results_tab_uses_score_delegate(self):
        """Test ResultsTab uses ScoreDelegate."""
        from gui.tabs.results_tab import ResultsTab
        
        source = inspect.getsource(ResultsTab)
        assert "ScoreDelegate" in source

    def test_results_tab_uses_flag_delegate(self):
        """Test ResultsTab uses FlagDelegate."""
        from gui.tabs.results_tab import ResultsTab
        
        source = inspect.getsource(ResultsTab)
        assert "FlagDelegate" in source

    def test_review_queue_tab_uses_status_delegate(self):
        """Test ReviewQueueTab uses StatusDelegate."""
        from gui.tabs.review_queue_tab import ReviewQueueTab
        
        source = inspect.getsource(ReviewQueueTab)
        assert "StatusDelegate" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])