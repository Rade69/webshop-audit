"""
Tests for run-to-run comparison module.

Tests cover:
- URL matching and normalization
- Score delta calculation
- Issue detection (resolved vs new)
- Severity change detection
- Summary statistics
"""
import os
import tempfile
import json

import pandas as pd
import pytest

from audit.run_diff import (
    compare_runs,
    URLDiff,
    RunDiffSummary,
    _extract_flags,
    _extract_issues,
    _severity_from_score_and_flags,
    _severity_change_direction,
    url_diffs_to_dataframe,
    summary_to_dict,
)
from audit.exporters import export_run_diff_summary, export_run_diff_urls


def _create_test_run(output_dir: str, rows: list[dict], timestamp: str = "20250101_120000"):
    """Helper to create a minimal test run output."""
    os.makedirs(output_dir, exist_ok=True)
    
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(output_dir, "products_scored.csv"), index=False, encoding="utf-8-sig")
    
    summary = {
        "timestamp": timestamp,
        "total_urls": len(df),
        "successfully_parsed": len(df),
        "errors": 0,
        "manual_review_candidates": 0,
    }
    with open(os.path.join(output_dir, "run_summary.json"), "w") as f:
        json.dump(summary, f)


class TestFlagExtraction:
    """Tests for _extract_flags helper."""
    
    def test_extract_boolean_flags(self):
        row = pd.Series({
            "flag_noindex": True,
            "flag_canonical_mismatch": False,
            "flag_fetch_error": True,
            "flag_non_200": False,
        })
        flags = _extract_flags(row)
        assert "flag_noindex" in flags
        assert "flag_fetch_error" in flags
        assert "flag_canonical_mismatch" not in flags
    
    def test_extract_indexability_flags_string(self):
        row = pd.Series({
            "indexability_flags": "noindex, canonical_mismatch",
            "flag_noindex": False,
        })
        flags = _extract_flags(row)
        assert "noindex" in flags
        assert "canonical_mismatch" in flags
    
    def test_extract_no_flags(self):
        row = pd.Series({
            "flag_noindex": False,
            "flag_fetch_error": False,
            "indexability_flags": "",
        })
        flags = _extract_flags(row)
        assert len(flags) == 0


class TestIssueExtraction:
    """Tests for _extract_issues helper."""
    
    def test_extract_issues_from_flags(self):
        flags = ["flag_noindex", "suspicious_price_missing", "flag_fetch_error"]
        issues = _extract_issues(flags)
        assert "noindex" in issues
        assert "price_missing" in issues
        assert "fetch_error" in issues
    
    def test_extract_issues_from_string_flags(self):
        flags = ["noindex", "canonical_mismatch", "status_404"]
        issues = _extract_issues(flags)
        assert "noindex" in issues
        assert "canonical_mismatch" in issues
        assert "non_200" in issues


class TestSeverityInference:
    """Tests for _severity_from_score_and_flags."""
    
    def test_critical_from_fetch_error(self):
        assert _severity_from_score_and_flags(50, ["flag_fetch_error"]) == "CRITICAL"
    
    def test_critical_from_non_200(self):
        assert _severity_from_score_and_flags(50, ["flag_non_200"]) == "CRITICAL"
    
    def test_high_from_noindex(self):
        assert _severity_from_score_and_flags(50, ["flag_noindex"]) == "HIGH"
    
    def test_high_from_missing_both_price_and_schema(self):
        flags = ["suspicious_price_missing", "suspicious_schema_missing"]
        assert _severity_from_score_and_flags(50, flags) == "HIGH"
    
    def test_medium_from_price_missing_only(self):
        assert _severity_from_score_and_flags(50, ["suspicious_price_missing"]) == "MEDIUM"
    
    def test_medium_from_js_rendered(self):
        assert _severity_from_score_and_flags(50, ["flag_js_rendered"]) == "MEDIUM"
    
    def test_low_from_low_score(self):
        assert _severity_from_score_and_flags(35, []) == "LOW"
    
    def test_none_from_good_score_no_flags(self):
        assert _severity_from_score_and_flags(75, []) == "NONE"


class TestSeverityChangeDirection:
    """Tests for _severity_change_direction."""
    
    def test_improved(self):
        assert _severity_change_direction("HIGH", "MEDIUM") == "improved"
        assert _severity_change_direction("MEDIUM", "NONE") == "improved"
    
    def test_degraded(self):
        assert _severity_change_direction("MEDIUM", "HIGH") == "degraded"
        assert _severity_change_direction("NONE", "CRITICAL") == "degraded"
    
    def test_unchanged(self):
        assert _severity_change_direction("HIGH", "HIGH") == "none"
        assert _severity_change_direction("NONE", "NONE") == "none"


class TestCompareRuns:
    """Tests for main compare_runs function."""
    
    def test_compare_identical_runs(self):
        """Two identical runs should show all unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = os.path.join(tmpdir, "old")
            new_dir = os.path.join(tmpdir, "new")
            
            rows = [
                {"url": "https://example.com/p1", "overall_score": 75, "flag_noindex": False},
                {"url": "https://example.com/p2", "overall_score": 50, "flag_noindex": False},
            ]
            _create_test_run(old_dir, rows, "20250101_120000")
            _create_test_run(new_dir, rows, "20250102_120000")
            
            summary, diffs = compare_runs(old_dir, new_dir)
            
            assert summary.unchanged_count == 2
            assert summary.improved_count == 0
            assert summary.degraded_count == 0
            assert summary.avg_overall_delta == 0.0
    
    def test_compare_improved_score(self):
        """Score increase should show as improved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = os.path.join(tmpdir, "old")
            new_dir = os.path.join(tmpdir, "new")
            
            old_rows = [
                {"url": "https://example.com/p1", "overall_score": 50, "flag_noindex": False},
            ]
            new_rows = [
                {"url": "https://example.com/p1", "overall_score": 75, "flag_noindex": False},
            ]
            _create_test_run(old_dir, old_rows)
            _create_test_run(new_dir, new_rows)
            
            summary, diffs = compare_runs(old_dir, new_dir)
            
            assert summary.avg_overall_delta == 25.0
            assert summary.improved_count == 1
            assert diffs[0].score_delta == 25.0
    
    def test_compare_degraded_score(self):
        """Score decrease should show as degraded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = os.path.join(tmpdir, "old")
            new_dir = os.path.join(tmpdir, "new")
            
            old_rows = [
                {"url": "https://example.com/p1", "overall_score": 75, "flag_noindex": False},
            ]
            new_rows = [
                {"url": "https://example.com/p1", "overall_score": 50, "flag_noindex": False},
            ]
            _create_test_run(old_dir, old_rows)
            _create_test_run(new_dir, new_rows)
            
            summary, diffs = compare_runs(old_dir, new_dir)
            
            assert summary.avg_overall_delta == -25.0
            assert summary.degraded_count == 1
            assert diffs[0].score_delta == -25.0
    
    def test_compare_new_url(self):
        """New URL in new run should be marked as 'new'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = os.path.join(tmpdir, "old")
            new_dir = os.path.join(tmpdir, "new")
            
            old_rows = [
                {"url": "https://example.com/p1", "overall_score": 75},
            ]
            new_rows = [
                {"url": "https://example.com/p1", "overall_score": 75},
                {"url": "https://example.com/p2", "overall_score": 60},
            ]
            _create_test_run(old_dir, old_rows)
            _create_test_run(new_dir, new_rows)
            
            summary, diffs = compare_runs(old_dir, new_dir)
            
            assert summary.new_url_count == 1
            new_diff = [d for d in diffs if d.status == "new"][0]
            assert "p2" in new_diff.url
    
    def test_compare_removed_url(self):
        """URL missing in new run should be marked as 'removed'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = os.path.join(tmpdir, "old")
            new_dir = os.path.join(tmpdir, "new")
            
            old_rows = [
                {"url": "https://example.com/p1", "overall_score": 75},
                {"url": "https://example.com/p2", "overall_score": 60},
            ]
            new_rows = [
                {"url": "https://example.com/p1", "overall_score": 75},
            ]
            _create_test_run(old_dir, old_rows)
            _create_test_run(new_dir, new_rows)
            
            summary, diffs = compare_runs(old_dir, new_dir)
            
            assert summary.removed_url_count == 1
            removed_diff = [d for d in diffs if d.status == "removed"][0]
            assert "p2" in removed_diff.url
    
    def test_compare_resolved_issue(self):
        """Resolved noindex should appear in resolved_issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = os.path.join(tmpdir, "old")
            new_dir = os.path.join(tmpdir, "new")
            
            old_rows = [
                {
                    "url": "https://example.com/p1",
                    "overall_score": 40,
                    "flag_noindex": True,
                    "indexability_flags": "noindex",
                },
            ]
            new_rows = [
                {
                    "url": "https://example.com/p1",
                    "overall_score": 75,
                    "flag_noindex": False,
                    "indexability_flags": "",
                },
            ]
            _create_test_run(old_dir, old_rows)
            _create_test_run(new_dir, new_rows)
            
            summary, diffs = compare_runs(old_dir, new_dir)
            
            # noindex is counted both from flag_noindex and indexability_flags string
            assert summary.resolved_issues_count >= 1
            diff = diffs[0]
            assert "noindex" in diff.resolved_issues
            assert diff.severity_change == "improved"
    
    def test_compare_new_issue(self):
        """New noindex should appear in new_issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = os.path.join(tmpdir, "old")
            new_dir = os.path.join(tmpdir, "new")
            
            old_rows = [
                {
                    "url": "https://example.com/p1",
                    "overall_score": 75,
                    "flag_noindex": False,
                    "indexability_flags": "",
                },
            ]
            new_rows = [
                {
                    "url": "https://example.com/p1",
                    "overall_score": 40,
                    "flag_noindex": True,
                    "indexability_flags": "noindex",
                },
            ]
            _create_test_run(old_dir, old_rows)
            _create_test_run(new_dir, new_rows)
            
            summary, diffs = compare_runs(old_dir, new_dir)
            
            # noindex is counted both from flag_noindex and indexability_flags string
            assert summary.new_issues_count >= 1
            diff = diffs[0]
            assert "noindex" in diff.new_issues
            assert diff.severity_change == "degraded"
    
    def test_compare_critical_high_counts(self):
        """Critical/high counts should reflect severity changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = os.path.join(tmpdir, "old")
            new_dir = os.path.join(tmpdir, "new")
            
            # Old: 1 critical (fetch error)
            old_rows = [
                {"url": "https://example.com/p1", "overall_score": 0, "flag_fetch_error": True},
                {"url": "https://example.com/p2", "overall_score": 75, "flag_noindex": False},
            ]
            # New: 0 critical (fixed fetch error)
            new_rows = [
                {"url": "https://example.com/p1", "overall_score": 75, "flag_fetch_error": False},
                {"url": "https://example.com/p2", "overall_score": 75, "flag_noindex": False},
            ]
            _create_test_run(old_dir, old_rows)
            _create_test_run(new_dir, new_rows)
            
            summary, diffs = compare_runs(old_dir, new_dir)
            
            assert summary.old_critical_high_count == 1
            assert summary.new_critical_high_count == 0
            assert summary.critical_high_delta == -1
    
    def test_compare_price_schema_counts(self):
        """Price and schema missing counts should be tracked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = os.path.join(tmpdir, "old")
            new_dir = os.path.join(tmpdir, "new")
            
            # Old: 1 without price
            old_rows = [
                {
                    "url": "https://example.com/p1",
                    "overall_score": 50,
                    "suspicious_price_missing": True,
                    "html_price_text": None,
                    "schema_price": None,
                },
            ]
            # New: price added
            new_rows = [
                {
                    "url": "https://example.com/p1",
                    "overall_score": 75,
                    "suspicious_price_missing": False,
                    "html_price_text": "€99.99",
                    "schema_price": "99.99",
                },
            ]
            _create_test_run(old_dir, old_rows)
            _create_test_run(new_dir, new_rows)
            
            summary, diffs = compare_runs(old_dir, new_dir)
            
            assert summary.old_no_price_count == 1
            assert summary.new_no_price_count == 0
            assert summary.no_price_delta == -1


class TestURLDiffsToDataFrame:
    """Tests for url_diffs_to_dataframe."""
    
    def test_convert_diffs_to_dataframe(self):
        diffs = [
            URLDiff(
                url="https://example.com/p1",
                status="improved",
                score_delta=25.0,
                old_score=50.0,
                new_score=75.0,
                resolved_issues=["noindex"],
            ),
            URLDiff(
                url="https://example.com/p2",
                status="degraded",
                score_delta=-10.0,
                old_score=80.0,
                new_score=70.0,
                new_issues=["price_missing"],
            ),
        ]
        
        df = url_diffs_to_dataframe(diffs)
        
        assert len(df) == 2
        assert list(df.columns) == [
            "url", "status", "score_delta", "old_score", "new_score",
            "old_severity", "new_severity", "severity_change",
            "resolved_issues", "new_issues", "old_flags", "new_flags",
        ]
        
        improved = df[df["status"] == "improved"].iloc[0]
        assert improved["score_delta"] == 25.0
        assert "noindex" in improved["resolved_issues"]


class TestSummaryToDict:
    """Tests for summary_to_dict."""
    
    def test_convert_summary_to_dict(self):
        summary = RunDiffSummary(
            old_timestamp="20250101_120000",
            new_timestamp="20250102_120000",
            avg_overall_delta=5.5,
            improved_count=10,
            degraded_count=5,
            old_critical_high_count=20,
            new_critical_high_count=15,
        )
        
        result = summary_to_dict(summary)
        
        assert result["old_timestamp"] == "20250101_120000"
        assert result["new_timestamp"] == "20250102_120000"
        assert result["score_changes"]["avg_overall_delta"] == 5.5
        assert result["url_status_counts"]["improved"] == 10
        assert result["issue_counts"]["old_critical_high"] == 20
        assert result["issue_counts"]["new_critical_high"] == 15


class TestDiffExports:
    """Tests for diff export functions."""
    
    def test_export_run_diff_summary(self):
        summary = {
            "old_timestamp": "20250101_120000",
            "avg_overall_delta": 5.5,
            "url_status_counts": {"improved": 10},
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "diff_summary.json")
            export_run_diff_summary(summary, path)
            
            assert os.path.isfile(path)
            with open(path) as f:
                loaded = json.load(f)
            assert loaded["avg_overall_delta"] == 5.5
    
    def test_export_run_diff_urls(self):
        df = pd.DataFrame({
            "url": ["https://example.com/p1"],
            "status": ["improved"],
            "score_delta": [25.0],
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "diff_urls.csv")
            export_run_diff_urls(df, path)
            
            assert os.path.isfile(path)
            loaded = pd.read_csv(path)
            assert len(loaded) == 1
            assert loaded.iloc[0]["status"] == "improved"


class TestURLNormalization:
    """Tests for URL normalization in diff matching."""
    
    def test_url_with_tracking_params(self):
        """URLs differing only by tracking params should match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_dir = os.path.join(tmpdir, "old")
            new_dir = os.path.join(tmpdir, "new")
            
            old_rows = [
                {"url": "https://example.com/p1?utm_source=google", "overall_score": 50},
            ]
            new_rows = [
                {"url": "https://example.com/p1?utm_campaign=sale", "overall_score": 75},
            ]
            _create_test_run(old_dir, old_rows)
            _create_test_run(new_dir, new_rows)
            
            summary, diffs = compare_runs(old_dir, new_dir)
            
            # Should be treated as same URL
            assert summary.unchanged_count + summary.improved_count + summary.degraded_count == 1
            assert summary.new_url_count == 0
            assert summary.removed_url_count == 0
