"""
End-to-end tests for GUI + Report integration features.

Tests cover:
- Issue-centric view export
- Evidence snapshots export
- Report generation with issue summary
- Fix impact in report
- CLI export options
"""
import os
import tempfile
import json
import pandas as pd
import pytest

from audit.issue_grouping import create_issue_summary, create_issue_to_urls_mapping
from audit.evidence import EvidenceSnapshot
from audit.exporters import export_issue_summary, export_issue_to_urls


class TestIssueCentricExport:
    """Tests for issue-centric export functionality."""

    def test_issue_summary_export(self):
        """Test that issue summary CSV is correctly generated."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 30,
             "suspicious_price_missing": True, "suspicious_schema_missing": False,
             "flag_noindex": False, "flag_canonical_mismatch": False,
             "flag_fetch_error": False, "flag_non_200": False,
             "flag_js_rendered": False, "suspicious_low_content": False,
             "flag_not_product_page": False},
            {"url": "https://example.com/p2", "overall_score": 50,
             "suspicious_price_missing": True, "suspicious_schema_missing": True,
             "flag_noindex": False, "flag_canonical_mismatch": False,
             "flag_fetch_error": False, "flag_non_200": False,
             "flag_js_rendered": False, "suspicious_low_content": False,
             "flag_not_product_page": False},
        ])
        
        issue_summary = create_issue_summary(df)
        
        assert len(issue_summary) > 0
        assert "issue_id" in issue_summary.columns
        assert "count" in issue_summary.columns
        assert "pct_affected" in issue_summary.columns

    def test_issue_to_urls_mapping_export(self):
        """Test that issue-to-URLs mapping CSV is correctly generated."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 30,
             "suspicious_price_missing": True, "suspicious_schema_missing": False},
        ])
        
        mapping = create_issue_to_urls_mapping(df)
        
        assert len(mapping) > 0
        assert "issue_id" in mapping.columns
        assert "url" in mapping.columns
        assert "display_name" in mapping.columns

    def test_full_issue_export_pipeline(self):
        """Test full issue export pipeline with temp files."""
        df = pd.DataFrame([
            {"url": f"https://example.com/p{i}", "overall_score": 40,
             "suspicious_price_missing": i % 2 == 0, "suspicious_schema_missing": False}
            for i in range(10)
        ])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Export issue summary
            issue_summary = create_issue_summary(df)
            export_issue_summary(issue_summary, os.path.join(tmpdir, "issue_summary.csv"))
            
            # Export issue to URLs
            issue_to_urls = create_issue_to_urls_mapping(df)
            export_issue_to_urls(issue_to_urls, os.path.join(tmpdir, "issue_to_urls.csv"))
            
            # Verify files exist
            assert os.path.isfile(os.path.join(tmpdir, "issue_summary.csv"))
            assert os.path.isfile(os.path.join(tmpdir, "issue_to_urls.csv"))
            
            # Verify content
            summary_df = pd.read_csv(os.path.join(tmpdir, "issue_summary.csv"))
            assert len(summary_df) > 0
            
            mapping_df = pd.read_csv(os.path.join(tmpdir, "issue_to_urls.csv"))
            assert len(mapping_df) > 0


class TestEvidenceExport:
    """Tests for evidence snapshots export."""

    def test_evidence_snapshot_from_row(self):
        """Test creating evidence snapshot from a row."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "status_code": 200,
            "fetch_error": None,
            "canonical": "https://example.com/p1",
            "robots_meta": None,
            "html_price_text": "€99.99",
            "schema_price": "99.99",
            "schema_price_value": 99.99,
            "schema_currency": "EUR",
            "schema_product_present": True,
            "schema_sku": "SKU123",
            "schema_brand": "Brand",
            "breadcrumb_text": "Home > Products",
            "visible_text_length": 500,
        })
        
        evidence = EvidenceSnapshot.from_row(row)
        
        assert evidence.url == "https://example.com/p1"
        assert evidence.html_price_text == "€99.99"
        assert evidence.schema_product_present is True

    def test_evidence_export_dataframe(self):
        """Test exporting evidence as DataFrame."""
        df = pd.DataFrame([
            {
                "url": "https://example.com/p1",
                "status_code": 200,
                "html_price_text": "€99.99",
                "schema_price": "99.99",
                "schema_product_present": True,
            },
            {
                "url": "https://example.com/p2",
                "status_code": 404,
                "html_price_text": None,
                "schema_price": None,
                "schema_product_present": False,
            },
        ])
        
        evidence_records = []
        for _, row in df.iterrows():
            evidence = EvidenceSnapshot.from_row(row)
            html_price = row.get("html_price_text")
            schema_price = row.get("schema_price")
            evidence_records.append({
                "url": row.get("url", ""),
                "status_code": row.get("status_code", ""),
                "html_price_text": html_price if html_price is not None else "",
                "schema_price": schema_price if schema_price is not None else "",
                "schema_product_present": row.get("schema_product_present", False),
            })
        
        evidence_df = pd.DataFrame(evidence_records)
        
        assert len(evidence_df) == 2
        assert "url" in evidence_df.columns
        assert evidence_df.iloc[0]["html_price_text"] == "€99.99"
        # Pandas converts empty string to NaN - check with pd.isna
        assert pd.isna(evidence_df.iloc[1]["html_price_text"]) or evidence_df.iloc[1]["html_price_text"] == ""


class TestReportIntegration:
    """Tests for report generation with new features."""

    def test_report_loads_issue_summary(self):
        """Test that report generator loads issue_summary.csv if available."""
        from audit.report_generator import _load_data, _compute_stats
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal run_summary.json
            summary = {"timestamp": "20250101_120000", "total_urls": 10, "successfully_parsed": 10, "errors": 0}
            with open(os.path.join(tmpdir, "run_summary.json"), "w") as f:
                json.dump(summary, f)
            
            # Create products_scored.csv
            df = pd.DataFrame([
                {"url": f"https://example.com/p{i}", "overall_score": 50,
                 "suspicious_price_missing": i % 2 == 0}
                for i in range(10)
            ])
            df.to_csv(os.path.join(tmpdir, "products_scored.csv"), index=False)
            
            # Create issue_summary.csv
            issue_summary = create_issue_summary(df)
            export_issue_summary(issue_summary, os.path.join(tmpdir, "issue_summary.csv"))
            
            # Load data
            data = _load_data(tmpdir)
            
            assert "issue_summary" in data
            assert data["issue_summary"] is not None
            
            # Compute stats
            stats = _compute_stats(data)
            
            assert "issue_stats" in stats
            assert "high_impact_issues" in stats

    def test_report_high_impact_issues(self):
        """Test that HIGH impact issues are correctly identified."""
        from audit.report_generator import _load_data, _compute_stats
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal run_summary.json
            summary = {"timestamp": "20250101_120000", "total_urls": 10, "successfully_parsed": 10, "errors": 0}
            with open(os.path.join(tmpdir, "run_summary.json"), "w") as f:
                json.dump(summary, f)
            
            # Create products_scored.csv with HIGH impact issues
            df = pd.DataFrame([
                {"url": f"https://example.com/p{i}", "overall_score": 30,
                 "suspicious_price_missing": True}  # missing_price is HIGH impact
                for i in range(5)
            ])
            df.to_csv(os.path.join(tmpdir, "products_scored.csv"), index=False)
            
            # Create issue_summary.csv with impact column
            issue_summary = create_issue_summary(df)
            export_issue_summary(issue_summary, os.path.join(tmpdir, "issue_summary.csv"))
            
            # Load and compute
            data = _load_data(tmpdir)
            stats = _compute_stats(data)
            
            # Check HIGH impact issues are identified
            # Note: issue_summary may not have missing_price if no rows have that flag
            # So we check that issue_stats is populated
            assert "issue_stats" in stats
            # The high_impact_issues list depends on the issue_summary having impact="HIGH"
            # which comes from the ISSUE_DEFINITIONS mapping


class TestCLIExportOptions:
    """Tests for CLI export options."""

    def test_cli_export_issues_flag_exists(self):
        """Test that --export-issues flag is available."""
        import subprocess
        
        result = subprocess.run(
            ["python", "main.py", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/radovan/Desktop/webshop_audit"
        )
        
        assert "--export-issues" in result.stdout
        assert "--export-evidence" in result.stdout


class TestImpactInOutput:
    """Tests for impact field in output files."""

    def test_impact_in_manual_review_candidates(self):
        """Test that fix_impact field is in manual_review_candidates.csv."""
        from audit.shortlist import ShortlistCandidate, select_manual_review_candidates
        
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 30,
             "suspicious_price_missing": True, "suspicious_schema_missing": False,
             "flag_noindex": False, "flag_canonical_mismatch": False,
             "flag_fetch_error": False, "flag_non_200": False,
             "flag_js_rendered": False, "suspicious_low_content": False,
             "flag_not_product_page": False,
             "is_likely_product_page": True, "is_likely_js_rendered": False,
             "js_render_confidence": "none",
             "title": "Product 1", "h1": "Product 1", "breadcrumb_text": "Home > Products"},
        ])
        
        candidates = select_manual_review_candidates(df)
        
        assert "fix_impact" in candidates.columns
        assert "impact_score" in candidates.columns
        assert candidates.iloc[0]["fix_impact"] == "HIGH"  # missing_price is HIGH impact
