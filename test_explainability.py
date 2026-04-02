"""
Tests for explainability module.

Tests cover:
- Single explanation generation
- Multiple explanation generation
- Priority ordering
- Sample candidate detection
- Combined explanation
- Integration with ShortlistCandidate
"""
import pandas as pd
import pytest

from audit.explainability import (
    generate_explanation,
    generate_top_explanations,
    generate_combined_explanation,
    is_sample_candidate,
    get_primary_issue_reason,
    EXPLANATION_PRIORITY,
)
from audit.shortlist import ShortlistCandidate


class TestGenerateExplanation:
    """Tests for generate_explanation function."""

    def test_missing_price_explanation(self):
        row = {
            "url": "https://example.com/p1",
            "html_price_text": None,
            "schema_price": None,
        }
        explanation = generate_explanation("missing-price", row)
        assert "cijenu" in explanation.lower()
        assert "HTML" in explanation

    def test_missing_schema_explanation(self):
        row = {
            "url": "https://example.com/p1",
            "schema_product_present": False,
        }
        explanation = generate_explanation("missing-schema", row)
        assert "json-ld" in explanation.lower() or "structured data" in explanation.lower()
        assert "ai agenti" in explanation.lower()

    def test_canonical_mismatch_explanation(self):
        row = {
            "url": "https://example.com/p1",
            "canonical": "https://example.com/p1-duplicate",
        }
        explanation = generate_explanation("canonical-mismatch", row)
        assert "Canonical" in explanation
        assert "drugu stranicu" in explanation

    def test_noindex_explanation(self):
        row = {"robots_meta": "noindex"}
        explanation = generate_explanation("noindex", row)
        assert "noindex" in explanation.lower()
        assert "tražilice" in explanation

    def test_fetch_error_explanation(self):
        row = {"fetch_error": "Connection timeout"}
        explanation = generate_explanation("fetch-error", row)
        assert "preuzeti" in explanation.lower()
        assert "Connection timeout" in explanation

    def test_non_200_explanation(self):
        row = {"status_code": 404}
        explanation = generate_explanation("non-200", row)
        assert "404" in explanation
        assert "status kod" in explanation

    def test_low_content_explanation(self):
        row = {"visible_text_length": 50}
        explanation = generate_explanation("low-content", row)
        assert "50" in explanation
        assert "teksta" in explanation.lower()

    def test_js_rendered_explanation(self):
        row = {"is_likely_js_rendered": True}
        explanation = generate_explanation("js-rendered", row)
        assert "JavaScript" in explanation

    def test_sample_good_score_explanation(self):
        row = {"overall_score": 85}
        explanation = generate_explanation("sample-good-score", row)
        assert "85" in explanation
        assert "uzorak" in explanation.lower()

    def test_unknown_reason_fallback(self):
        row = {}
        explanation = generate_explanation("unknown-reason", row)
        assert "unknown reason" in explanation.lower()


class TestGenerateTopExplanations:
    """Tests for generate_top_explanations function."""

    def test_single_explanation(self):
        reasons = ["missing-price"]
        row = {}
        explanations = generate_top_explanations(reasons, row)
        assert len(explanations) == 1

    def test_multiple_explanations(self):
        reasons = ["missing-price", "missing-schema", "low-content"]
        row = {"visible_text_length": 50}
        explanations = generate_top_explanations(reasons, row)
        assert len(explanations) == 3

    def test_respects_max_explanations(self):
        reasons = ["missing-price", "missing-schema", "low-content", "noindex"]
        row = {}
        explanations = generate_top_explanations(reasons, row, max_explanations=2)
        assert len(explanations) == 2

    def test_priority_ordering(self):
        # Critical reasons should come first
        reasons = ["low-content", "fetch-error", "missing-price"]
        row = {}
        explanations = generate_top_explanations(reasons, row, max_explanations=2)
        # fetch-error should be first
        assert "preuzeti" in explanations[0].lower()

    def test_empty_reasons(self):
        explanations = generate_top_explanations([], {})
        assert len(explanations) == 0


class TestGenerateCombinedExplanation:
    """Tests for generate_combined_explanation function."""

    def test_single_reason(self):
        reasons = ["missing-price"]
        row = {}
        explanation = generate_combined_explanation(reasons, row)
        assert "cijenu" in explanation.lower()

    def test_multiple_reasons_combined(self):
        reasons = ["missing-price", "missing-schema"]
        row = {}
        explanation = generate_combined_explanation(reasons, row)
        # Should contain both explanations separated
        assert "cijenu" in explanation.lower() or "schema" in explanation.lower()

    def test_empty_reasons(self):
        explanation = generate_combined_explanation([], {})
        assert "nema" in explanation.lower()
        assert "problema" in explanation.lower()


class TestIsSampleCandidate:
    """Tests for is_sample_candidate function."""

    def test_sample_good_score_is_sample(self):
        assert is_sample_candidate(["sample-good-score"]) is True

    def test_real_issue_not_sample(self):
        assert is_sample_candidate(["missing-price"]) is False
        assert is_sample_candidate(["noindex"]) is False

    def test_mixed_reasons_is_sample(self):
        # If sample-good-score is present, it's a sample
        assert is_sample_candidate(["sample-good-score", "low-score"]) is True

    def test_empty_reasons_not_sample(self):
        assert is_sample_candidate([]) is False


class TestGetPrimaryIssueReason:
    """Tests for get_primary_issue_reason function."""

    def test_single_reason(self):
        assert get_primary_issue_reason(["missing-price"]) == "missing-price"

    def test_multiple_reasons_returns_highest_priority(self):
        # fetch-error has higher priority than missing-price
        reason = get_primary_issue_reason(["missing-price", "fetch-error"])
        assert reason == "fetch-error"

    def test_excludes_sample_good_score(self):
        reason = get_primary_issue_reason(["sample-good-score", "missing-price"])
        assert reason == "missing-price"

    def test_only_sample_returns_none(self):
        assert get_primary_issue_reason(["sample-good-score"]) is None

    def test_empty_returns_none(self):
        assert get_primary_issue_reason([]) is None


class TestShortlistCandidateExplanation:
    """Integration tests for ShortlistCandidate with explanations."""

    def test_candidate_has_explanation(self):
        row = pd.Series({
            "url": "https://example.com/p1",
            "overall_score": 35,
            "suspicious_price_missing": True,
            "suspicious_schema_missing": False,
            "flag_noindex": False,
            "flag_canonical_mismatch": False,
            "flag_fetch_error": False,
            "flag_non_200": False,
            "flag_js_rendered": False,
            "suspicious_low_content": False,
            "flag_not_product_page": False,
            "is_likely_product_page": True,
            "is_likely_js_rendered": False,
            "js_render_confidence": "none",
        })
        candidate = ShortlistCandidate(row)
        assert hasattr(candidate, "explanation")
        assert candidate.explanation != ""

    def test_candidate_with_fetch_error(self):
        row = pd.Series({
            "url": "https://example.com/p1",
            "overall_score": 0,
            "fetch_error": "Connection refused",
            "flag_fetch_error": True,
            "flag_non_200": False,
            "flag_not_product_page": False,
            "flag_noindex": False,
            "flag_canonical_mismatch": False,
            "flag_js_rendered": False,
            "suspicious_price_missing": False,
            "suspicious_schema_missing": False,
            "suspicious_low_content": False,
            "is_likely_product_page": True,
            "is_likely_js_rendered": False,
            "js_render_confidence": "none",
        })
        candidate = ShortlistCandidate(row)
        assert "preuzeti" in candidate.explanation.lower()

    def test_candidate_with_noindex(self):
        row = pd.Series({
            "url": "https://example.com/p1",
            "overall_score": 40,
            "robots_meta": "noindex",
            "flag_noindex": True,
            "flag_canonical_mismatch": False,
            "flag_fetch_error": False,
            "flag_non_200": False,
            "flag_js_rendered": False,
            "suspicious_price_missing": False,
            "suspicious_schema_missing": False,
            "suspicious_low_content": False,
            "flag_not_product_page": False,
            "is_likely_product_page": True,
            "is_likely_js_rendered": False,
            "js_render_confidence": "none",
        })
        candidate = ShortlistCandidate(row)
        assert "noindex" in candidate.explanation.lower()

    def test_candidate_with_missing_price_and_schema(self):
        row = pd.Series({
            "url": "https://example.com/p1",
            "overall_score": 30,
            "suspicious_price_missing": True,
            "suspicious_schema_missing": True,
            "flag_noindex": False,
            "flag_canonical_mismatch": False,
            "flag_fetch_error": False,
            "flag_non_200": False,
            "flag_js_rendered": False,
            "suspicious_low_content": False,
            "flag_not_product_page": False,
            "is_likely_product_page": True,
            "is_likely_js_rendered": False,
            "js_render_confidence": "none",
        })
        candidate = ShortlistCandidate(row)
        assert candidate.severity == "HIGH"
        assert "cijenu" in candidate.explanation.lower() or "schema" in candidate.explanation.lower()

    def test_sample_candidate_has_explanation(self):
        row = pd.Series({
            "url": "https://example.com/p1",
            "overall_score": 85,
            "suspicious_price_missing": False,
            "suspicious_schema_missing": False,
            "flag_noindex": False,
            "flag_canonical_mismatch": False,
            "flag_fetch_error": False,
            "flag_non_200": False,
            "flag_js_rendered": False,
            "suspicious_low_content": False,
            "flag_not_product_page": False,
            "is_likely_product_page": True,
            "is_likely_js_rendered": False,
            "js_render_confidence": "none",
        })
        candidate = ShortlistCandidate(row)
        assert candidate.is_sample is True
        assert "uzorak" in candidate.explanation.lower() or "dobre" in candidate.explanation.lower()

    def test_to_dict_includes_explanation(self):
        row = pd.Series({
            "url": "https://example.com/p1",
            "overall_score": 50,
            "suspicious_price_missing": True,
            "suspicious_schema_missing": False,
            "flag_noindex": False,
            "flag_canonical_mismatch": False,
            "flag_fetch_error": False,
            "flag_non_200": False,
            "flag_js_rendered": False,
            "suspicious_low_content": False,
            "flag_not_product_page": False,
            "is_likely_product_page": True,
            "is_likely_js_rendered": False,
            "js_render_confidence": "none",
        })
        candidate = ShortlistCandidate(row)
        result = candidate.to_dict()
        assert "explanation" in result
        assert result["explanation"] != ""

    def test_to_dict_includes_is_sample(self):
        row = pd.Series({
            "url": "https://example.com/p1",
            "overall_score": 85,
            "suspicious_price_missing": False,
            "suspicious_schema_missing": False,
            "flag_noindex": False,
            "flag_canonical_mismatch": False,
            "flag_fetch_error": False,
            "flag_non_200": False,
            "flag_js_rendered": False,
            "suspicious_low_content": False,
            "flag_not_product_page": False,
            "is_likely_product_page": True,
            "is_likely_js_rendered": False,
            "js_render_confidence": "none",
        })
        candidate = ShortlistCandidate(row)
        result = candidate.to_dict()
        assert "is_sample" in result
        assert result["is_sample"] is True


class TestExplanationPriority:
    """Tests for explanation priority ordering."""

    def test_critical_before_high(self):
        fetch_idx = EXPLANATION_PRIORITY.index("fetch-error")
        noindex_idx = EXPLANATION_PRIORITY.index("noindex")
        assert fetch_idx < noindex_idx

    def test_high_before_medium(self):
        noindex_idx = EXPLANATION_PRIORITY.index("noindex")
        missing_price_idx = EXPLANATION_PRIORITY.index("missing-price")
        assert noindex_idx < missing_price_idx

    def test_medium_before_low(self):
        missing_price_idx = EXPLANATION_PRIORITY.index("missing-price")
        low_score_idx = EXPLANATION_PRIORITY.index("low-score")
        assert missing_price_idx < low_score_idx

    def test_sample_last(self):
        low_score_idx = EXPLANATION_PRIORITY.index("low-score")
        sample_idx = EXPLANATION_PRIORITY.index("sample-good-score")
        assert low_score_idx < sample_idx
