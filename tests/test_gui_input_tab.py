"""
Tests for gui/tabs/input_tab.py - InputTab structure verification

Note: Full instantiation requires QApplication, so we test structure.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import inspect


class TestInputTabStructure:
    """Test InputTab class structure."""

    def test_class_importable(self):
        """Test InputTab can be imported."""
        from gui.tabs.input_tab import InputTab
        assert InputTab is not None

    def test_has_start_scan_requested_signal(self):
        """Test start_scan_requested signal is defined."""
        from gui.tabs.input_tab import InputTab
        
        # Check signal in source
        source = inspect.getsource(InputTab)
        assert "start_scan_requested = pyqtSignal(dict)" in source

    def test_accepts_audit_controller_param(self):
        """Test __init__ accepts audit_controller parameter."""
        from gui.tabs.input_tab import InputTab
        
        source = inspect.getsource(InputTab.__init__)
        assert "audit_controller: AuditRunController" in source

    def test_has_sitemap_url_input(self):
        """Test has sitemap URL input field."""
        from gui.tabs.input_tab import InputTab
        
        source = inspect.getsource(InputTab)
        assert "sitemap_url_input" in source

    def test_has_domain_input(self):
        """Test has domain input field."""
        from gui.tabs.input_tab import InputTab
        
        source = inspect.getsource(InputTab)
        assert "domain_input" in source

    def test_has_manual_urls_edit(self):
        """Test has manual URLs edit field."""
        from gui.tabs.input_tab import InputTab
        
        source = inspect.getsource(InputTab)
        assert "manual_urls_edit" in source

    def test_has_run_options(self):
        """Test has run options (max_urls, delay, output_dir)."""
        from gui.tabs.input_tab import InputTab
        
        source = inspect.getsource(InputTab)
        assert "max_urls_input" in source
        assert "delay_spin" in source
        assert "output_dir_input" in source

    def test_has_url_summary(self):
        """Test has URL summary with counts and preview."""
        from gui.tabs.input_tab import InputTab
        
        source = inspect.getsource(InputTab)
        assert "total_urls_label" in source
        assert "valid_urls_label" in source
        assert "url_preview_list" in source

    def test_has_action_buttons(self):
        """Test has action buttons."""
        from gui.tabs.input_tab import InputTab
        
        source = inspect.getsource(InputTab)
        assert "start_scan_btn" in source
        assert "clear_btn" in source
        assert "export_btn" in source

    def test_has_qsettings_persistence(self):
        """Test uses QSettings for state persistence."""
        from gui.tabs.input_tab import InputTab
        
        source = inspect.getsource(InputTab)
        assert "QSettings" in source
        assert "_settings" in source
        assert "_load_saved_state" in source
        assert "_save_state" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])