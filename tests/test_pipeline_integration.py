"""
Integration tests for audit pipeline - basic API verification

These tests verify key modules can be imported and have expected functions.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
import tempfile


class TestModuleImports:
    """Test all key modules can be imported."""

    def test_parser_imports(self):
        """Test parser module imports."""
        from audit.parser import make_soup, extract_title, extract_h1, extract_canonical
        assert make_soup is not None

    def test_schema_parser_imports(self):
        """Test schema_parser module imports."""
        from audit.schema_parser import extract_json_ld_blocks, find_product_schema
        assert extract_json_ld_blocks is not None

    def test_extractor_imports(self):
        """Test extractor module imports."""
        from audit.extractor import ProductAuditRow, build_product_audit_row
        assert ProductAuditRow is not None

    def test_scorer_imports(self):
        """Test scorer module imports."""
        from audit.scorer import (
            score_catalog_completeness,
            score_machine_readability,
            score_commerce_clarity,
            build_scored_dataframe
        )
        assert score_catalog_completeness is not None

    def test_shortlist_imports(self):
        """Test shortlist module imports."""
        from audit.shortlist import select_manual_review_candidates, select_best_products_sample
        assert select_manual_review_candidates is not None

    def test_exporters_imports(self):
        """Test exporters module imports."""
        from audit.exporters import export_dataframe_csv, export_json_summary
        assert export_dataframe_csv is not None

    def test_pipeline_imports(self):
        """Test pipeline module imports."""
        from audit.pipeline import run_audit
        assert run_audit is not None


class TestDataFrameIntegration:
    """Test dataframes work correctly."""

    def test_dataframe_to_dataframe(self):
        """Test pandas operations work."""
        df = pd.DataFrame({
            "a": [1, 2, 3],
            "b": ["x", "y", "z"]
        })
        assert len(df) == 3
        assert "a" in df.columns


class TestCSVExport:
    """Test CSV export functionality."""

    def test_export_empty_dataframe(self):
        """Test export handles empty dataframe."""
        from audit.exporters import export_dataframe_csv
        
        df = pd.DataFrame({"col": []})
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            path = f.name
        
        try:
            export_dataframe_csv(df, path)
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_export_roundtrip(self):
        """Test export and read back."""
        from audit.exporters import export_dataframe_csv
        
        df = pd.DataFrame({
            "url": ["https://a.com", "https://b.com"],
            "score": [80, 90]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            path = f.name
        
        try:
            export_dataframe_csv(df, path)
            
            # Read back
            result = pd.read_csv(path)
            assert len(result) == 2
            assert "url" in result.columns
        finally:
            os.unlink(path)


class TestConfig:
    """Test configuration."""

    def test_config_importable(self):
        """Test config module can be imported."""
        import config
        assert config is not None

    def test_default_delay_exists(self):
        """Test default delay exists."""
        from config import DEFAULT_DELAY
        assert isinstance(DEFAULT_DELAY, (int, float))

    def test_default_output_exists(self):
        """Test default output dir exists."""
        from config import DEFAULT_OUTPUT_DIR
        assert isinstance(DEFAULT_OUTPUT_DIR, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])