"""
Tests for gui/controllers/audit_run_controller.py

Note: These tests verify the controller logic without requiring Qt application.
AuditWorker tests require QApplication, so they're skipped in CI.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestAuditRunController:
    """Test AuditRunController class."""

    def test_controller_init(self):
        """Test controller initialization."""
        # Import without creating Qt objects
        from gui.controllers.audit_run_controller import AuditRunController
        
        # We can't instantiate without QApplication, so just test import
        assert AuditRunController is not None

    def test_signal_definitions(self):
        """Test that signals are properly defined."""
        # This verifies the signal names without instantiating
        import inspect
        from gui.controllers import audit_run_controller
        
        # Get the AuditRunController class source
        source = inspect.getsource(audit_run_controller.AuditRunController)
        
        # Check for signal definitions
        assert "run_started = Signal()" in source
        assert "run_completed = Signal(str)" in source
        assert "run_failed = Signal(str)" in source
        assert "phase_changed = Signal(str)" in source
        assert "progress_updated = Signal(int, int)" in source
        assert "log_message = Signal(str, str)" in source
        assert "stats_updated = Signal(dict)" in source


class TestAuditWorker:
    """Test AuditWorker class."""

    def test_worker_signal_definitions(self):
        """Test that worker signals are properly defined."""
        import inspect
        from gui.controllers import audit_run_controller
        
        source = inspect.getsource(audit_run_controller.AuditWorker)
        
        # Check for signal definitions
        assert "phase_changed = Signal(str)" in source
        assert "progress_updated = Signal(int, int)" in source
        assert "url_fetched = Signal(str, bool)" in source
        assert "url_error = Signal(str, str)" in source
        assert "log_message = Signal(str, str)" in source
        assert "stats_updated = Signal(dict)" in source
        assert "run_completed = Signal(str)" in source
        assert "run_failed = Signal(str)" in source

    def test_worker_request_stop(self):
        """Test worker has request_stop method."""
        import inspect
        from gui.controllers import audit_run_controller
        
        source = inspect.getsource(audit_run_controller.AuditWorker)
        assert "def request_stop(self)" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])