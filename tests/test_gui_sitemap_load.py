"""
Tests for gui/controllers/audit_run_controller.py - SitemapLoadWorker

Tests the SitemapLoadWorker and load_sitemap functionality.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import inspect


class TestSitemapLoadWorker:
    """Test SitemapLoadWorker class."""

    def test_worker_importable(self):
        """Test SitemapLoadWorker can be imported."""
        from gui.controllers.audit_run_controller import SitemapLoadWorker
        assert SitemapLoadWorker is not None

    def test_worker_signals(self):
        """Test worker has required signals."""
        from gui.controllers.audit_run_controller import SitemapLoadWorker
        
        source = inspect.getsource(SitemapLoadWorker)
        assert "sitemap_loaded = Signal(list, bool)" in source
        assert "sitemap_load_failed = Signal(str)" in source


class TestAuditRunControllerLoadSitemap:
    """Test AuditRunController load_sitemap method."""

    def test_load_sitemap_method_exists(self):
        """Test load_sitemap method exists."""
        from gui.controllers.audit_run_controller import AuditRunController
        
        source = inspect.getsource(AuditRunController)
        assert "def load_sitemap(self, sitemap_url" in source

    def test_load_sitemap_signals(self):
        """Test controller has sitemap_loaded and sitemap_load_failed signals."""
        from gui.controllers.audit_run_controller import AuditRunController
        
        source = inspect.getsource(AuditRunController)
        assert "sitemap_loaded = Signal(list, bool)" in source
        assert "sitemap_load_failed = Signal(str)" in source

    def test_on_sitemap_loaded_handler(self):
        """Test _on_sitemap_loaded handler exists."""
        from gui.controllers.audit_run_controller import AuditRunController
        
        source = inspect.getsource(AuditRunController)
        assert "def _on_sitemap_loaded(self, urls: list, used_fallback: bool)" in source

    def test_on_sitemap_load_failed_handler(self):
        """Test _on_sitemap_load_failed handler exists."""
        from gui.controllers.audit_run_controller import AuditRunController
        
        source = inspect.getsource(AuditRunController)
        assert "def _on_sitemap_load_failed(self, message: str)" in source


class TestInputTabLoadSitemap:
    """Test InputTab load sitemap integration."""

    def test_on_load_sitemap_clicked_exists(self):
        """Test _on_load_sitemap_clicked method exists."""
        from gui.tabs.input_tab import InputTab
        
        source = inspect.getsource(InputTab)
        assert "def _on_load_sitemap_clicked(self)" in source

    def test_on_sitemap_loaded_handler_exists(self):
        """Test _on_sitemap_loaded handler exists."""
        from gui.tabs.input_tab import InputTab
        
        source = inspect.getsource(InputTab)
        assert "def _on_sitemap_loaded(self, urls: list, used_fallback: bool)" in source

    def test_on_sitemap_load_failed_handler_exists(self):
        """Test _on_sitemap_load_failed handler exists."""
        from gui.tabs.input_tab import InputTab
        
        source = inspect.getsource(InputTab)
        assert "def _on_sitemap_load_failed(self, error: str)" in source

    def test_update_url_summary_uses_collected_urls(self):
        """Test _update_url_summary uses _collected_urls."""
        from gui.tabs.input_tab import InputTab
        
        source = inspect.getsource(InputTab._update_url_summary)
        assert "_collected_urls" in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
