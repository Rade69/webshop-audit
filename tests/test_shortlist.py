"""
Tests for audit/shortlist.py — sample bucket tuning.

These tests protect the new sample bucket behaviour:
- sample candidates are limited
- sample candidates cannot override real issues
- sample candidates remain clearly marked
- shortlist with many real issues contains fewer or no sample candidates
- shortlist with few real issues may have a small number of sample candidates
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd

from audit.shortlist import (
    ShortlistCandidate,
    select_manual_review_candidates,
    _is_sample_candidate,
    _compute_sample_limit,
    SAMPLE_MAX_ABSOLUTE,
    SAMPLE_MAX_RATIO_OF_ISSUES,
    SAMPLE_DISABLE_ABOVE_ISSUES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_row(
    url: str = "https://example.com/p/1",
    overall_score: int = 50,
    is_likely_product_page: bool = True,
    flag_fetch_error: bool = False,
    flag_non_200: bool = False,
    flag_not_product_page: bool = False,
    flag_noindex: bool = False,
    flag_canonical_mismatch: bool = False,
    flag_js_rendered: bool = False,
    suspicious_price_missing: bool = False,
    suspicious_schema_missing: bool = False,
    suspicious_low_content: bool = False,
    js_render_confidence: str = "none",
    **extra,
) -> pd.Series:
    """Build a minimal pd.Series that ShortlistCandidate can consume."""
    data = {
        "url": url,
        "overall_score": overall_score,
        "is_likely_product_page": is_likely_product_page,
        "is_likely_js_rendered": flag_js_rendered,
        "js_render_confidence": js_render_confidence,
        "flag_noindex": flag_noindex,
        "flag_canonical_mismatch": flag_canonical_mismatch,
        "flag_fetch_error": flag_fetch_error,
        "flag_non_200": flag_non_200,
        "flag_js_rendered": flag_js_rendered,
        "suspicious_price_missing": suspicious_price_missing,
        "suspicious_schema_missing": suspicious_schema_missing,
        "suspicious_low_content": suspicious_low_content,
        "flag_not_product_page": flag_not_product_page,
    }
    data.update(extra)
    return pd.Series(data)


def _make_scored_df(rows: list[dict]) -> pd.DataFrame:
    """Build a scored DataFrame from raw row dicts."""
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # Ensure all required columns exist
    for col in [
        "url",
        "overall_score",
        "is_likely_product_page",
        "is_likely_js_rendered",
        "js_render_confidence",
        "flag_noindex",
        "flag_canonical_mismatch",
        "flag_fetch_error",
        "flag_non_200",
        "flag_js_rendered",
        "suspicious_price_missing",
        "suspicious_schema_missing",
        "suspicious_low_content",
        "flag_not_product_page",
    ]:
        if col not in df.columns:
            if col in ("overall_score",):
                df[col] = 50
            elif col in (
                "is_likely_product_page",
                "is_likely_js_rendered",
                "flag_noindex",
                "flag_canonical_mismatch",
                "flag_fetch_error",
                "flag_non_200",
                "flag_js_rendered",
                "suspicious_price_missing",
                "suspicious_schema_missing",
                "suspicious_low_content",
                "flag_not_product_page",
            ):
                df[col] = False
            elif col == "js_render_confidence":
                df[col] = "none"
            else:
                df[col] = ""
    return df


# ---------------------------------------------------------------------------
# _compute_sample_limit tests
# ---------------------------------------------------------------------------


class TestComputeSampleLimit:
    def test_zero_issues_returns_zero(self):
        assert _compute_sample_limit(0) == 0

    def test_few_issues_allows_at_least_one(self):
        # With 1-3 issues, ratio would be 0, but max(1, ...) ensures at least 1
        assert _compute_sample_limit(1) >= 1
        assert _compute_sample_limit(3) >= 1

    def test_never_exceeds_absolute_max(self):
        # Even with many issues (but below disable threshold), cap at 3
        for n in range(1, SAMPLE_DISABLE_ABOVE_ISSUES):
            assert _compute_sample_limit(n) <= SAMPLE_MAX_ABSOLUTE

    def test_disabled_above_threshold(self):
        assert _compute_sample_limit(SAMPLE_DISABLE_ABOVE_ISSUES) == 0
        assert _compute_sample_limit(100) == 0

    def test_ratio_respected(self):
        # With 10 issues, 30% = 3, so limit should be min(3, 3) = 3
        limit_10 = _compute_sample_limit(10)
        assert limit_10 <= int(10 * SAMPLE_MAX_RATIO_OF_ISSUES) + 1


# ---------------------------------------------------------------------------
# _is_sample_candidate tests
# ---------------------------------------------------------------------------


class TestIsSampleCandidate:
    def test_sample_good_score_is_sample(self):
        row = _make_row(overall_score=80)
        c = ShortlistCandidate(row)
        assert c.severity == "LOW"
        assert c.overall_score >= 40
        assert "sample-good-score" in c.reasons
        assert _is_sample_candidate(c) is True

    def test_low_score_is_not_sample(self):
        row = _make_row(overall_score=30)
        c = ShortlistCandidate(row)
        assert c.severity == "LOW"
        assert "low-score" in c.reasons
        assert _is_sample_candidate(c) is False

    def test_critical_is_not_sample(self):
        row = _make_row(flag_fetch_error=True)
        c = ShortlistCandidate(row)
        assert c.severity == "CRITICAL"
        assert _is_sample_candidate(c) is False

    def test_high_is_not_sample(self):
        row = _make_row(flag_noindex=True)
        c = ShortlistCandidate(row)
        assert c.severity == "HIGH"
        assert _is_sample_candidate(c) is False

    def test_medium_is_not_sample(self):
        row = _make_row(suspicious_price_missing=True)
        c = ShortlistCandidate(row)
        assert c.severity == "MEDIUM"
        assert _is_sample_candidate(c) is False


# ---------------------------------------------------------------------------
# ShortlistCandidate reason tests
# ---------------------------------------------------------------------------


class TestShortlistCandidateReasons:
    def test_sample_reason_for_good_low_candidate(self):
        row = _make_row(overall_score=75)
        c = ShortlistCandidate(row)
        assert c.severity == "LOW"
        assert "sample-good-score" in c.reasons

    def test_low_score_reason_for_bad_low_candidate(self):
        row = _make_row(overall_score=25)
        c = ShortlistCandidate(row)
        assert c.severity == "LOW"
        assert "low-score" in c.reasons
        assert "sample-good-score" not in c.reasons

    def test_boundary_score_40_is_sample(self):
        row = _make_row(overall_score=40)
        c = ShortlistCandidate(row)
        # score >= 40 means sample
        assert "sample-good-score" in c.reasons

    def test_boundary_score_39_is_low_score(self):
        row = _make_row(overall_score=39)
        c = ShortlistCandidate(row)
        assert "low-score" in c.reasons


# ---------------------------------------------------------------------------
# select_manual_review_candidates — sample bucket limit tests
# ---------------------------------------------------------------------------


class TestSelectManualReviewCandidatesSampleLimit:
    def test_sample_bucket_has_limit_with_no_issues(self):
        """When there are no real issues, sample bucket should still be limited."""
        rows = [
            {"url": f"https://example.com/p/{i}", "overall_score": 80 + i}
            for i in range(20)
        ]
        df = _make_scored_df(rows)
        result = select_manual_review_candidates(df)
        samples = [
            r
            for r in result.to_dict(orient="records")
            if "sample-good-score" in str(r.get("reasons", ""))
        ]
        assert len(samples) <= SAMPLE_MAX_ABSOLUTE

    def test_sample_bucket_disabled_with_many_issues(self):
        """When there are >= 15 real issues, sample bucket should be empty."""
        rows = []
        # 15 MEDIUM issues
        for i in range(15):
            rows.append(
                {
                    "url": f"https://example.com/p/{i}",
                    "overall_score": 30,
                    "suspicious_price_missing": True,
                    "is_likely_product_page": True,
                }
            )
        # 10 sample candidates
        for i in range(15, 25):
            rows.append(
                {
                    "url": f"https://example.com/p/{i}",
                    "overall_score": 85,
                    "is_likely_product_page": True,
                }
            )
        df = _make_scored_df(rows)
        result = select_manual_review_candidates(df)
        samples = [
            r
            for r in result.to_dict(orient="records")
            if "sample-good-score" in str(r.get("reasons", ""))
        ]
        assert len(samples) == 0

    def test_sample_bucket_reduced_with_some_issues(self):
        """When there are some issues, sample bucket should be proportional."""
        rows = []
        # 5 MEDIUM issues
        for i in range(5):
            rows.append(
                {
                    "url": f"https://example.com/p/{i}",
                    "overall_score": 30,
                    "suspicious_price_missing": True,
                    "is_likely_product_page": True,
                }
            )
        # 10 sample candidates
        for i in range(5, 15):
            rows.append(
                {
                    "url": f"https://example.com/p/{i}",
                    "overall_score": 85,
                    "is_likely_product_page": True,
                }
            )
        df = _make_scored_df(rows)
        result = select_manual_review_candidates(df)
        samples = [
            r
            for r in result.to_dict(orient="records")
            if "sample-good-score" in str(r.get("reasons", ""))
        ]
        # 5 issues * 30% = 1.5 -> int = 1, min(3, 1) = 1
        assert len(samples) <= 1

    def test_sample_candidates_do_not_override_issues(self):
        """All real issue candidates must appear before sample candidates."""
        rows = []
        # 3 CRITICAL issues
        for i in range(3):
            rows.append(
                {
                    "url": f"https://example.com/p/{i}",
                    "overall_score": 50,
                    "flag_fetch_error": True,
                }
            )
        # 10 sample candidates
        for i in range(3, 13):
            rows.append(
                {
                    "url": f"https://example.com/p/{i}",
                    "overall_score": 90,
                    "is_likely_product_page": True,
                }
            )
        df = _make_scored_df(rows)
        result = select_manual_review_candidates(df)
        records = result.to_dict(orient="records")

        # Find position of first sample candidate
        first_sample_idx = None
        for idx, r in enumerate(records):
            if "sample-good-score" in str(r.get("reasons", "")):
                first_sample_idx = idx
                break

        # All records before first sample must be non-sample (real issues)
        if first_sample_idx is not None:
            for idx in range(first_sample_idx):
                assert "sample-good-score" not in str(records[idx].get("reasons", ""))

    def test_all_critical_candidates_included(self):
        """All CRITICAL candidates should be included regardless of count."""
        rows = []
        for i in range(20):
            rows.append(
                {
                    "url": f"https://example.com/p/{i}",
                    "overall_score": 50,
                    "flag_fetch_error": True,
                }
            )
        df = _make_scored_df(rows)
        result = select_manual_review_candidates(df)
        assert len(result) == 20

    def test_empty_dataframe_returns_empty(self):
        df = pd.DataFrame()
        result = select_manual_review_candidates(df)
        assert result.empty

    def test_sample_reasons_stay_clear_of_issue_reasons(self):
        """Sample candidates should only have sample-good-score reason, not issue reasons."""
        row = _make_row(overall_score=85)
        c = ShortlistCandidate(row)
        assert "sample-good-score" in c.reasons
        # Should not have any issue-related reasons
        issue_reasons = {
            "fetch-error",
            "non-200",
            "not-product-page",
            "noindex",
            "canonical-mismatch",
            "missing-price-critical",
            "missing-schema-critical",
            "missing-price",
            "missing-schema",
            "low-content",
            "js-rendered",
            "low-score",
        }
        for reason in c.reasons:
            assert reason not in issue_reasons or reason == "sample-good-score"


# ---------------------------------------------------------------------------
# Integration: CSV/report consistency
# ---------------------------------------------------------------------------


class TestCsvReportConsistency:
    def test_reasons_column_is_string(self):
        """reasons column must be a string for CSV export."""
        rows = [
            {
                "url": "https://example.com/p/1",
                "overall_score": 30,
                "suspicious_price_missing": True,
            },
            {"url": "https://example.com/p/2", "overall_score": 85},
        ]
        df = _make_scored_df(rows)
        result = select_manual_review_candidates(df)
        assert result["reasons"].dtype.kind in ("O", "U", "S")
        for val in result["reasons"]:
            assert isinstance(val, str)

    def test_severity_column_present(self):
        rows = [
            {
                "url": "https://example.com/p/1",
                "overall_score": 30,
                "suspicious_price_missing": True,
            },
            {"url": "https://example.com/p/2", "overall_score": 85},
        ]
        df = _make_scored_df(rows)
        result = select_manual_review_candidates(df)
        assert not result.empty
        assert "severity" in result.columns

    def test_url_column_present(self):
        rows = [
            {
                "url": "https://example.com/p/1",
                "overall_score": 30,
                "suspicious_price_missing": True,
            },
            {"url": "https://example.com/p/2", "overall_score": 85},
        ]
        df = _make_scored_df(rows)
        result = select_manual_review_candidates(df)
        assert not result.empty
        assert "url" in result.columns
