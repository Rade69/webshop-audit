"""
Tests for evidence snapshots module.

Tests cover:
- EvidenceSnapshot creation from row
- Evidence for specific findings
- Evidence summary generation
- Evidence formatting for display
- Integration with ShortlistCandidate
"""
import pandas as pd
import pytest

from audit.evidence import (
    EvidenceSnapshot,
    build_evidence_for_reasons,
    format_evidence_for_display,
)
from audit.shortlist import ShortlistCandidate


class TestEvidenceSnapshotCreation:
    """Tests for EvidenceSnapshot.from_row."""

    def test_create_from_product_audit_row(self):
        """Test creating evidence from a complete row."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "final_url": "https://example.com/p1",
            "status_code": 200,
            "fetch_error": None,
            "canonical": "https://example.com/p1",
            "robots_meta": None,
            "html_price_text": "€99.99",
            "schema_price": "99.99",
            "schema_price_value": 99.99,
            "schema_currency": "EUR",
            "schema_product_present": True,
            "schema_offer_present": True,
            "schema_sku": "SKU123",
            "schema_brand": "Example Brand",
            "breadcrumb_text": "Home > Products > Shoes",
            "title": "Example Product",
            "h1": "Example Product",
            "visible_text_length": 500,
            "is_likely_product_page": True,
            "is_likely_js_rendered": False,
        })
        
        evidence = EvidenceSnapshot.from_row(row)
        
        assert evidence.url == "https://example.com/p1"
        assert evidence.status_code == 200
        assert evidence.html_price_text == "€99.99"
        assert evidence.schema_price == "99.99"
        assert evidence.schema_currency == "EUR"
        assert evidence.schema_product_present is True
        assert evidence.schema_sku == "SKU123"
        assert evidence.breadcrumb_text == "Home > Products > Shoes"

    def test_create_from_row_with_missing_data(self):
        """Test creating evidence from a row with missing data."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "final_url": None,
            "status_code": None,
            "fetch_error": "Connection timeout",
            "canonical": None,
            "robots_meta": None,
            "html_price_text": None,
            "schema_price": None,
            "schema_price_value": None,
            "schema_currency": None,
            "schema_product_present": False,
            "schema_offer_present": False,
            "schema_sku": None,
            "schema_brand": None,
            "breadcrumb_text": None,
            "title": None,
            "h1": None,
            "visible_text_length": 0,
            "is_likely_product_page": False,
            "is_likely_js_rendered": False,
        })
        
        evidence = EvidenceSnapshot.from_row(row)
        
        assert evidence.fetch_error == "Connection timeout"
        assert evidence.html_price_text is None
        assert evidence.schema_product_present is False
        assert evidence.is_likely_product_page is False

    def test_create_from_dataclass(self):
        """Test creating evidence from a dataclass-like object."""
        class FakeRow:
            url = "https://example.com/p1"
            final_url = "https://example.com/p1"
            status_code = 200
            fetch_error = None
            canonical = "https://example.com/p1"
            robots_meta = "noindex"
            html_price_text = "€50"
            schema_price = "50"
            schema_price_value = 50.0
            schema_currency = "EUR"
            schema_product_present = True
            schema_offer_present = False
            schema_sku = None
            schema_brand = None
            breadcrumb_text = None
            title = "Product"
            h1 = "Product"
            visible_text_length = 100
            is_likely_product_page = True
            is_likely_js_rendered = True
        
        evidence = EvidenceSnapshot.from_row(FakeRow())
        
        assert evidence.url == "https://example.com/p1"
        assert evidence.robots_meta == "noindex"
        assert evidence.is_likely_js_rendered is True


class TestEvidenceForFinding:
    """Tests for get_evidence_for_finding method."""

    def test_missing_price_evidence(self):
        """Test evidence returned for missing-price finding."""
        import pandas as pd
        row = pd.Series({
            "url": "https://example.com/p1",
            "html_price_text": None,
            "schema_price": None,
            "schema_price_value": None,
            "schema_currency": None,
        })
        evidence = EvidenceSnapshot.from_row(row)
        
        price_evidence = evidence.get_evidence_for_finding("missing-price")
        
        assert "html_price_text" in price_evidence
        assert "schema_price" in price_evidence
        # pandas uses NaN for None in Series, so check with pd.isna
        assert pd.isna(price_evidence["html_price_text"])
        assert pd.isna(price_evidence["schema_price"])

    def test_missing_schema_evidence(self):
        """Test evidence returned for missing-schema finding."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "schema_product_present": False,
            "schema_offer_present": False,
            "schema_sku": None,
            "schema_brand": None,
        })
        evidence = EvidenceSnapshot.from_row(row)
        
        schema_evidence = evidence.get_evidence_for_finding("missing-schema")
        
        assert "schema_product_present" in schema_evidence
        assert "schema_sku" in schema_evidence
        assert schema_evidence["schema_product_present"] is False

    def test_noindex_evidence(self):
        """Test evidence returned for noindex finding."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "robots_meta": "noindex, nofollow",
        })
        evidence = EvidenceSnapshot.from_row(row)
        
        noindex_evidence = evidence.get_evidence_for_finding("noindex")
        
        assert "robots_meta" in noindex_evidence
        assert noindex_evidence["robots_meta"] == "noindex, nofollow"

    def test_canonical_mismatch_evidence(self):
        """Test evidence returned for canonical-mismatch finding."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "final_url": "https://example.com/p1",
            "canonical": "https://example.com/p1?sort=price",
        })
        evidence = EvidenceSnapshot.from_row(row)
        
        canonical_evidence = evidence.get_evidence_for_finding("canonical-mismatch")
        
        assert "canonical" in canonical_evidence
        assert "url" in canonical_evidence
        assert canonical_evidence["canonical"] == "https://example.com/p1?sort=price"

    def test_fetch_error_evidence(self):
        """Test evidence returned for fetch-error finding."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "fetch_error": "Connection refused",
            "status_code": None,
        })
        evidence = EvidenceSnapshot.from_row(row)
        
        error_evidence = evidence.get_evidence_for_finding("fetch-error")
        
        assert "fetch_error" in error_evidence
        assert error_evidence["fetch_error"] == "Connection refused"

    def test_unknown_finding_returns_empty(self):
        """Test that unknown finding type returns empty dict."""
        evidence = EvidenceSnapshot()
        
        result = evidence.get_evidence_for_finding("unknown-finding")
        
        assert result == {}


class TestEvidenceSummary:
    """Tests for get_summary method."""

    def test_summary_with_complete_data(self):
        """Test summary generation with complete data."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "final_url": "https://example.com/p1",
            "status_code": 200,
            "fetch_error": None,
            "robots_meta": None,
            "canonical": "https://example.com/p1",
            "html_price_text": "€99.99",
            "schema_price": "99.99",
            "schema_currency": "EUR",
            "schema_product_present": True,
            "schema_sku": "SKU123",
            "schema_brand": "Brand",
            "visible_text_length": 500,
            "breadcrumb_text": "Home > Products",
            "is_likely_product_page": True,
            "is_likely_js_rendered": False,
        })
        evidence = EvidenceSnapshot.from_row(row)
        
        summary = evidence.get_summary()
        
        assert any("200 OK" in s for s in summary)
        assert any("HTML cijena" in s for s in summary)
        assert any("Schema cijena" in s for s in summary)
        assert any("Product schema: prisutna" in s for s in summary)
        assert any("SKU" in s for s in summary)

    def test_summary_with_noindex(self):
        """Test summary includes noindex when present."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "status_code": 200,
            "robots_meta": "noindex, nofollow",
            "html_price_text": None,
            "schema_price": None,
            "schema_currency": None,
            "schema_product_present": False,
            "visible_text_length": 100,
            "breadcrumb_text": None,
            "is_likely_product_page": True,
            "is_likely_js_rendered": False,
        })
        evidence = EvidenceSnapshot.from_row(row)
        
        summary = evidence.get_summary()
        
        assert any("noindex" in s for s in summary)

    def test_summary_with_fetch_error(self):
        """Test summary includes fetch error when present."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "status_code": None,
            "fetch_error": "Timeout",
            "html_price_text": None,
            "schema_price": None,
            "schema_currency": None,
            "schema_product_present": False,
            "visible_text_length": 0,
            "breadcrumb_text": None,
            "is_likely_product_page": False,
            "is_likely_js_rendered": False,
        })
        evidence = EvidenceSnapshot.from_row(row)
        
        summary = evidence.get_summary()
        
        assert any("Greška pri preuzimanju" in s for s in summary)
        assert any("Timeout" in s for s in summary)


class TestBuildEvidenceForReasons:
    """Tests for build_evidence_for_reasons function."""

    def test_build_evidence_for_multiple_reasons(self):
        """Test building evidence for multiple reason codes."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "html_price_text": None,
            "schema_price": None,
            "schema_currency": None,
            "schema_product_present": False,
            "robots_meta": "noindex",
            "status_code": 200,
            "fetch_error": None,
        })
        evidence = EvidenceSnapshot.from_row(row)
        
        reasons = ["missing-price", "missing-schema", "noindex"]
        result = build_evidence_for_reasons(evidence, reasons)
        
        assert result["url"] == "https://example.com/p1"
        assert "missing-price" in result["findings"]
        assert "missing-schema" in result["findings"]
        assert "noindex" in result["findings"]
        assert "summary" in result

    def test_build_evidence_with_empty_reasons(self):
        """Test building evidence with empty reason list."""
        evidence = EvidenceSnapshot()
        
        result = build_evidence_for_reasons(evidence, [])
        
        assert result["url"] == ""
        assert result["findings"] == {}
        assert "summary" in result


class TestFormatEvidenceForDisplay:
    """Tests for format_evidence_for_display function."""

    def test_format_for_display(self):
        """Test formatting evidence for text display."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "status_code": 200,
            "fetch_error": None,
            "robots_meta": None,
            "canonical": "https://example.com/p1",
            "html_price_text": "€99.99",
            "schema_price": None,
            "schema_currency": None,
            "schema_product_present": True,
            "schema_sku": "SKU123",
            "visible_text_length": 500,
            "breadcrumb_text": "Home > Products",
            "is_likely_product_page": True,
            "is_likely_js_rendered": False,
        })
        evidence = EvidenceSnapshot.from_row(row)
        
        display = format_evidence_for_display(evidence)
        
        assert "EVIDENCE SNAPSHOT" in display
        assert "https://example.com/p1" in display
        assert "200" in display
        assert "€99.99" in display
        assert "SKU123" in display

    def test_format_with_error(self):
        """Test formatting evidence when there's an error."""
        row = pd.Series({
            "url": "https://example.com/p1",
            "status_code": None,
            "fetch_error": "Connection refused",
            "html_price_text": None,
            "schema_price": None,
            "schema_currency": None,
            "schema_product_present": False,
            "visible_text_length": 0,
            "breadcrumb_text": None,
            "is_likely_product_page": False,
            "is_likely_js_rendered": False,
        })
        evidence = EvidenceSnapshot.from_row(row)
        
        display = format_evidence_for_display(evidence)
        
        assert "Fetch error" in display
        assert "Connection refused" in display


class TestShortlistCandidateEvidence:
    """Integration tests for ShortlistCandidate with evidence."""

    def test_candidate_has_evidence(self):
        """Test that ShortlistCandidate has evidence field."""
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
            "html_price_text": None,
            "schema_price": None,
            "schema_currency": None,
            "schema_product_present": False,
            "robots_meta": None,
            "canonical": None,
            "status_code": 200,
            "fetch_error": None,
            "final_url": "https://example.com/p1",
        })
        candidate = ShortlistCandidate(row)
        
        assert hasattr(candidate, "evidence")
        assert "url" in candidate.evidence
        assert "findings" in candidate.evidence

    def test_candidate_evidence_matches_reasons(self):
        """Test that evidence matches the candidate's reasons."""
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
            "html_price_text": None,
            "schema_price": None,
            "schema_currency": None,
            "schema_product_present": False,
            "robots_meta": None,
            "canonical": None,
            "status_code": 200,
            "fetch_error": None,
            "final_url": "https://example.com/p1",
        })
        candidate = ShortlistCandidate(row)
        
        # Check that evidence findings match reasons
        for reason in candidate.reasons:
            if reason in ["missing-price", "missing-schema"]:
                assert reason in candidate.evidence["findings"]

    def test_to_dict_includes_evidence_summary(self):
        """Test that to_dict includes evidence_summary field."""
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
            "html_price_text": None,
            "schema_price": None,
            "schema_currency": None,
            "schema_product_present": True,
            "robots_meta": None,
            "canonical": "https://example.com/p1",
            "status_code": 200,
            "fetch_error": None,
            "final_url": "https://example.com/p1",
        })
        candidate = ShortlistCandidate(row)
        result = candidate.to_dict()
        
        assert "evidence_summary" in result
        assert "HTML cijena:" in result["evidence_summary"]
        assert "Product schema:" in result["evidence_summary"]
