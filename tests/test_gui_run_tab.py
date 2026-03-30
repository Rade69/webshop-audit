"""
Tests for gui/tabs/run_tab.py - RunTab structure verification

Note: Full instantiation requires QApplication, so we test structure.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import inspect


class TestRunTabStructure:
    """Test RunTab class structure."""

    def test_class_importable(self):
        """Test RunTab can be imported."""
        from gui.tabs.run_tab import RunTab
        assert RunTab is not None

    def test_accepts_audit_controller_param(self):
        """Test __init__ accepts audit_controller parameter."""
        from gui.tabs.run_tab import RunTab
        
        source = inspect.getsource(RunTab.__init__)
        assert "audit_controller: AuditRunController" in source

    def test_has_status_label(self):
        """Test has status label."""
        from gui.tabs.run_tab import RunTab
        
        source = inspect.getsource(RunTab)
        assert "status_label" in source

    def test_has_phase_label(self):
        """Test has phase label."""
        from gui.tabs.run_tab import RunTab
        
        source = inspect.getsource(RunTab)
        assert "phase_label" in source

    def test_has_progress_bar(self):
        """Test has progress bar."""
        from gui.tabs.run_tab import RunTab
        
        source = inspect.getsource(RunTab)
        assert "progress_bar" in source

    def test_has_statistics_labels(self):
        """Test has statistics labels."""
        from gui.tabs.run_tab import RunTab
        
        source = inspect.getsource(RunTab)
        assert "total_urls_value" in source
        assert "processed_value" in source
        assert "errors_value" in source
        assert "elapsed_value" in source

    def test_has_log_view(self):
        """Test has log view (QPlainTextEdit)."""
        from gui.tabs.run_tab import RunTab
        
        source = inspect.getsource(RunTab)
        assert "log_view" in source

    def test_has_action_buttons(self):
        """Test has action buttons (Stop, Pause, Open Output)."""
        from gui.tabs.run_tab import RunTab
        
        source = inspect.getsource(RunTab)
        assert "stop_btn" in source
        assert "pause_btn" in source
        assert "open_output_btn" in source

    def test_connects_to_controller_signals(self):
        """Test connects to controller signals."""
        from gui.tabs.run_tab import RunTab
        
        source = inspect.getsource(RunTab._connect_signals)
        assert "phase_changed" in source
        assert "progress_updated" in source
        assert "log_message" in source
        assert "stats_updated" in source
        assert "run_completed" in source
        assert "run_failed" in source

    def test_has_elapsed_timer(self):
        """Test uses QTimer for elapsed time."""
        from gui.tabs.run_tab import RunTab
        
        source = inspect.getsource(RunTab)
        assert "QTimer" in source
        assert "_update_elapsed" in source

    def test_has_state_methods(self):
        """Test has state setter methods."""
        from gui.tabs.run_tab import RunTab
        
        source = inspect.getsource(RunTab)
        assert "_set_idle_state" in source
        assert "_set_running_state" in source
        assert "_set_completed_state" in source
        assert "_set_failed_state" in source
        assert "_set_stopped_state" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])