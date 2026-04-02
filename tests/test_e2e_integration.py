"""
End-to-end and integration tests for WebshopAudit.

These tests protect the main audit lifecycle:
- shared audit run (run_audit)
- output file shape and canonical columns
- shortlist/report consistency
- category summary consistency
- CLI/shared orchestration
- GUI adapter integration

They use mocked HTTP fetches and controlled HTML fixtures so tests are
deterministic, fast, and do not depend on the real internet.
"""

import sys
import os
import json
import tempfile
import shutil
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd

from audit.extractor import build_product_audit_row, rows_to_dataframe
from audit.scorer import (
    build_scored_dataframe,
    summarize_by_category,
    summarize_sitewide_scores,
)
from audit.shortlist import select_manual_review_candidates, select_best_products_sample
from audit.exporters import export_dataframe_csv
from audit.pipeline import run_audit


# ---------------------------------------------------------------------------
# HTML fixtures — controlled, realistic product pages
# ---------------------------------------------------------------------------

HTML_GOOD_PRODUCT = """<!DOCTYPE html>
<html>
<head>
    <title>Nike Air Max 90 - Running Shoe</title>
    <meta name="description" content="Classic running shoe with Air Max cushioning.">
    <link rel="canonical" href="https://shop.com/product/nike-air-max-90">
    <meta name="robots" content="index, follow">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Nike Air Max 90",
        "description": "Classic running shoe with Air Max cushioning.",
        "sku": "NK-001",
        "brand": {"@type": "Brand", "name": "Nike"},
        "offers": {
            "@type": "Offer",
            "price": "129.99",
            "priceCurrency": "EUR",
            "availability": "https://schema.org/InStock"
        }
    }
    </script>
</head>
<body>
    <nav><a href="/">Home</a> &gt; <a href="/shoes">Shoes</a> &gt; <a href="/shoes/nike">Nike Air Max 90</a></nav>
    <main>
        <h1>Nike Air Max 90</h1>
        <p class="price">129.99 EUR</p>
        <p>This is a detailed product description with enough words to pass content thresholds. It describes the features, benefits, and specifications of the Nike Air Max 90 running shoe. The shoe features Air Max cushioning technology for superior comfort during long runs. The upper is made from breathable mesh material. The outsole provides excellent traction on various surfaces.</p>
        <ul>
            <li>Air Max cushioning</li>
            <li>Breathable mesh upper</li>
            <li>Rubber outsole</li>
        </ul>
        <table>
            <tr><td>Weight</td><td>300g</td></tr>
            <tr><td>Drop</td><td>10mm</td></tr>
        </table>
        <img src="shoe1.jpg" alt="Nike Air Max 90" width="500" height="500">
        <img src="shoe2.jpg" alt="Side view" width="500" height="500">
        <img src="shoe3.jpg" alt="Sole" width="500" height="500">
        <p>Free shipping on orders over 50 EUR. 30-day return policy.</p>
    </main>
</body>
</html>"""

HTML_MISSING_SCHEMA = """<!DOCTYPE html>
<html>
<head>
    <title>Generic Widget</title>
    <meta name="description" content="A widget.">
    <link rel="canonical" href="https://shop.com/product/widget">
</head>
<body>
    <nav><a href="/">Home</a> &gt; <a href="/shop">Shop</a> &gt; <a href="/shop/widgets">Widget</a></nav>
    <main>
        <h1>Generic Widget</h1>
        <p class="price">29.99 EUR</p>
        <p>Short description.</p>
        <img src="widget.jpg" alt="Widget" width="300" height="300">
    </main>
</body>
</html>"""

HTML_NOINDEX_PAGE = """<!DOCTYPE html>
<html>
<head>
    <title>Hidden Product</title>
    <meta name="robots" content="noindex, nofollow">
    <link rel="canonical" href="https://shop.com/product/hidden">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Hidden Product",
        "sku": "HP-001",
        "offers": {
            "@type": "Offer",
            "price": "49.99",
            "priceCurrency": "EUR"
        }
    }
    </script>
</head>
<body>
    <nav><a href="/">Home</a> &gt; <a href="/shoes">Shoes</a> &gt; <a href="/shoes/hidden">Hidden Product</a></nav>
    <main>
        <h1>Hidden Product</h1>
        <p class="price">49.99 EUR</p>
        <p>This product has enough description text to be considered valid. It contains detailed information about the product features, specifications, and benefits that a buyer would want to know before making a purchase decision. The product is available in multiple colors and sizes.</p>
        <img src="hidden.jpg" alt="Hidden" width="400" height="400">
        <img src="hidden2.jpg" alt="Hidden 2" width="400" height="400">
        <p>Free shipping. Returns accepted within 30 days.</p>
    </main>
</body>
</html>"""

HTML_CANONICAL_MISMATCH = """<!DOCTYPE html>
<html>
<head>
    <title>Redirected Product</title>
    <link rel="canonical" href="https://shop.com/product/other-product">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Redirected Product",
        "offers": {"@type": "Offer", "price": "19.99", "priceCurrency": "EUR"}
    }
    </script>
</head>
<body>
    <nav><a href="/">Home</a> &gt; <a href="/electronics">Electronics</a> &gt; <a href="/electronics/redirected">Redirected Product</a></nav>
    <main>
        <h1>Redirected Product</h1>
        <p class="price">19.99 EUR</p>
        <p>Enough text to be a valid product page. This description contains sufficient content for the audit system to recognize it as a product page with meaningful content for buyers and search engines.</p>
        <img src="redirect.jpg" alt="Redirect" width="400" height="400">
        <img src="redirect2.jpg" alt="Redirect 2" width="400" height="400">
    </main>
</body>
</html>"""

HTML_FETCH_ERROR = """<!DOCTYPE html>
<html><head><title>Error</title></head><body><h1>500 Server Error</h1></body></html>"""

HTML_LOW_CONTENT = """<!DOCTYPE html>
<html>
<head><title>Barely Anything</title></head>
<body><main><p>Too short.</p></main></body>
</html>"""


# ---------------------------------------------------------------------------
# Mock fetch helper
# ---------------------------------------------------------------------------


def _make_fetch_result(
    url: str, html: str | None = None, error: str | None = None, status_code: int = 200
) -> dict:
    return {
        "url": url,
        "final_url": url,
        "status_code": status_code,
        "html": html,
        "content_type": "text/html; charset=utf-8" if html else None,
        "error": error,
        "response_time_ms": 100,
    }


def _mock_fetch_pages(
    urls,
    delay_seconds=0,
    max_workers=1,
    use_playwright=False,
    progress_callback=None,
    stop_event=None,
):
    """Mock fetcher that returns controlled HTML for known URLs."""
    html_map = {
        "https://shop.com/product/good": HTML_GOOD_PRODUCT,
        "https://shop.com/product/no-schema": HTML_MISSING_SCHEMA,
        "https://shop.com/product/noindex": HTML_NOINDEX_PAGE,
        "https://shop.com/product/canonical-mismatch": HTML_CANONICAL_MISMATCH,
        "https://shop.com/product/error": None,
        "https://shop.com/product/low-content": HTML_LOW_CONTENT,
    }
    results = []
    for url in urls:
        html = html_map.get(url)
        if url == "https://shop.com/product/error":
            results.append(
                _make_fetch_result(url, error="Connection timeout", status_code=None)
            )
        elif html:
            results.append(_make_fetch_result(url, html=html))
        else:
            results.append(_make_fetch_result(url, html=HTML_LOW_CONTENT))
        if progress_callback:
            progress_callback(len(results), len(urls))
    return results


# ---------------------------------------------------------------------------
# 1. Shared audit run integration
# ---------------------------------------------------------------------------


class TestSharedAuditRun:
    """Test the full run_audit() pipeline with mocked fetches."""

    def test_full_pipeline_with_mocked_fetch(self, tmp_path):
        """Run the full audit pipeline with controlled HTML fixtures."""
        urls = [
            "https://shop.com/product/good",
            "https://shop.com/product/no-schema",
            "https://shop.com/product/noindex",
            "https://shop.com/product/canonical-mismatch",
            "https://shop.com/product/error",
            "https://shop.com/product/low-content",
        ]

        config = {
            "urls": urls,
            "output_dir": str(tmp_path),
            "delay": 0,
            "max_workers": 1,
            "use_playwright": False,
        }

        with patch("audit.fetcher.fetch_pages", side_effect=_mock_fetch_pages):
            result = run_audit(config=config)

        assert result["processed"] > 0
        assert result["errors"] >= 1  # at least the error URL
        assert result["candidates"] > 0

    def test_progress_and_log_callbacks(self, tmp_path):
        """Verify callbacks are invoked during pipeline run."""
        urls = ["https://shop.com/product/good"]
        config = {"urls": urls, "output_dir": str(tmp_path), "delay": 0}

        progress_calls = []
        log_calls = []

        def progress_cb(done, total, phase):
            progress_calls.append((done, total, phase))

        def log_cb(level, message):
            log_calls.append((level, message))

        with patch("audit.fetcher.fetch_pages", side_effect=_mock_fetch_pages):
            run_audit(config=config, progress_callback=progress_cb, log_callback=log_cb)

        assert len(progress_calls) > 0
        assert len(log_calls) > 0
        assert any("score" in str(c[2]) for c in progress_calls)

    def test_stop_event_early_termination(self, tmp_path):
        """Verify stop_event is passed through to fetcher."""
        urls = [f"https://shop.com/product/good" for _ in range(5)]
        config = {"urls": urls, "output_dir": str(tmp_path), "delay": 0}

        stop_event = __import__("threading").Event()
        stop_event.set()

        call_args = {}

        def capturing_fetch(
            urls_list,
            delay_seconds=0,
            max_workers=1,
            use_playwright=False,
            progress_callback=None,
            stop_event=None,
        ):
            call_args["stop_event"] = stop_event
            return _mock_fetch_pages(
                urls_list,
                delay_seconds,
                max_workers,
                use_playwright,
                progress_callback,
                stop_event,
            )

        with patch("audit.fetcher.fetch_pages", side_effect=capturing_fetch):
            run_audit(config=config, stop_event=stop_event)

        assert call_args.get("stop_event") is stop_event


# ---------------------------------------------------------------------------
# 2. Output file shape integration
# ---------------------------------------------------------------------------


class TestOutputFileShape:
    """Test that audit run produces expected output files with correct shapes."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.tmp_path = tmp_path
        urls = [
            "https://shop.com/product/good",
            "https://shop.com/product/no-schema",
            "https://shop.com/product/noindex",
            "https://shop.com/product/canonical-mismatch",
            "https://shop.com/product/error",
            "https://shop.com/product/low-content",
        ]
        config = {"urls": urls, "output_dir": str(tmp_path), "delay": 0}
        with patch("audit.fetcher.fetch_pages", side_effect=_mock_fetch_pages):
            self.result = run_audit(config=config)

    def _read_csv(self, name):
        path = self.tmp_path / name
        assert path.exists(), f"{name} not found in output dir"
        return pd.read_csv(path)

    def test_products_raw_exists_and_has_urls(self):
        df = self._read_csv("products_raw.csv")
        assert not df.empty
        assert "url" in df.columns
        assert "title" in df.columns

    def test_products_scored_has_canonical_columns(self):
        df = self._read_csv("products_scored.csv")
        assert not df.empty
        required = [
            "url",
            "overall_score",
            "catalog_score",
            "machine_score",
            "commerce_score",
            "agent_ready",
            "missing_fields",
            "indexability_flags",
            "flag_noindex",
            "flag_canonical_mismatch",
            "suspicious_price_missing",
            "suspicious_schema_missing",
            "is_likely_product_page",
        ]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_manual_review_candidates_has_severity(self):
        df = self._read_csv("manual_review_candidates.csv")
        assert "severity" in df.columns
        assert "reasons" in df.columns
        assert "url" in df.columns

    def test_best_products_sample_exists(self):
        df = self._read_csv("best_products_sample.csv")
        assert "url" in df.columns

    def test_category_summary_exists(self):
        # category_summary.csv is only created when there are breadcrumbs
        path = self.tmp_path / "category_summary.csv"
        if path.exists():
            df = pd.read_csv(path)
            assert "category" in df.columns
            assert "product_count" in df.columns

    def test_errors_csv_exists(self):
        df = self._read_csv("errors.csv")
        assert "url" in df.columns
        assert "error" in df.columns

    def test_run_summary_json(self):
        path = self.tmp_path / "run_summary.json"
        assert path.exists()
        summary = json.loads(path.read_text())
        assert "total_urls" in summary
        assert "errors" in summary
        assert "manual_review_candidates" in summary
        assert "elapsed_seconds" in summary

    def test_output_files_are_semantically_consistent(self):
        """URLs in shortlist must exist in scored data."""
        scored = self._read_csv("products_scored.csv")
        shortlist = self._read_csv("manual_review_candidates.csv")
        if not shortlist.empty:
            shortlist_urls = set(shortlist["url"])
            scored_urls = set(scored["url"])
            assert shortlist_urls.issubset(scored_urls), (
                "Shortlist URLs not in scored data"
            )


# ---------------------------------------------------------------------------
# 3. Shortlist/report consistency
# ---------------------------------------------------------------------------


class TestShortlistReportConsistency:
    """Test that shortlist output is consistent with report expectations."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.tmp_path = tmp_path
        urls = [
            "https://shop.com/product/good",
            "https://shop.com/product/no-schema",
            "https://shop.com/product/noindex",
            "https://shop.com/product/canonical-mismatch",
            "https://shop.com/product/error",
            "https://shop.com/product/low-content",
        ]
        config = {"urls": urls, "output_dir": str(tmp_path), "delay": 0}
        with patch("audit.fetcher.fetch_pages", side_effect=_mock_fetch_pages):
            run_audit(config=config)
        self.shortlist_df = pd.read_csv(tmp_path / "manual_review_candidates.csv")
        self.scored_df = pd.read_csv(tmp_path / "products_scored.csv")

    def test_severity_ordering_in_shortlist(self):
        """CRITICAL should appear before HIGH before MEDIUM before LOW."""
        if self.shortlist_df.empty:
            return
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        severities = self.shortlist_df["severity"].map(severity_order)
        assert list(severities) == sorted(severities), "Severity not ordered correctly"

    def test_sample_candidates_are_marked(self):
        """Sample candidates must have sample-good-score in reasons."""
        if self.shortlist_df.empty:
            return
        sample_rows = self.shortlist_df[
            self.shortlist_df["reasons"].str.contains("sample-good-score", na=False)
        ]
        for _, row in sample_rows.iterrows():
            assert row["severity"] == "LOW"

    def test_issue_candidates_before_samples(self):
        """Non-sample candidates must appear before sample candidates."""
        if self.shortlist_df.empty:
            return
        reasons_list = self.shortlist_df["reasons"].tolist()
        first_sample_idx = None
        for i, r in enumerate(reasons_list):
            if "sample-good-score" in str(r):
                first_sample_idx = i
                break
        if first_sample_idx is not None:
            for i in range(first_sample_idx):
                assert "sample-good-score" not in str(reasons_list[i])

    def test_shortlist_urls_in_scored_data(self):
        """All shortlist URLs must exist in scored data."""
        shortlist_urls = set(self.shortlist_df["url"])
        scored_urls = set(self.scored_df["url"])
        assert shortlist_urls.issubset(scored_urls)

    def test_noindex_candidate_has_high_severity(self):
        """The noindex page should appear with HIGH severity."""
        noindex_rows = self.shortlist_df[
            self.shortlist_df["reasons"].str.contains("noindex", na=False)
        ]
        if not noindex_rows.empty:
            assert (noindex_rows["severity"] == "HIGH").all()


# ---------------------------------------------------------------------------
# 4. Category summary consistency
# ---------------------------------------------------------------------------


class TestCategorySummaryConsistency:
    """Test category summary output is meaningful and stable."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.tmp_path = tmp_path
        urls = [
            "https://shop.com/product/good",
            "https://shop.com/product/no-schema",
            "https://shop.com/product/noindex",
            "https://shop.com/product/canonical-mismatch",
            "https://shop.com/product/low-content",
        ]
        config = {"urls": urls, "output_dir": str(tmp_path), "delay": 0}
        with patch("audit.fetcher.fetch_pages", side_effect=_mock_fetch_pages):
            run_audit(config=config)
        cat_path = tmp_path / "category_summary.csv"
        self.cat_df = pd.read_csv(cat_path) if cat_path.exists() else None

    def test_category_summary_not_all_unknown(self):
        """Category summary should extract meaningful categories from breadcrumbs."""
        if self.cat_df is None or self.cat_df.empty:
            return
        unknown_count = (self.cat_df["category"] == "Unknown").sum()
        total = len(self.cat_df)
        assert unknown_count < total, "All categories are Unknown"

    def test_category_summary_has_required_columns(self):
        if self.cat_df is None or self.cat_df.empty:
            return
        required = [
            "category",
            "product_count",
            "avg_overall_score",
            "avg_catalog_score",
            "avg_machine_score",
            "avg_commerce_score",
        ]
        for col in required:
            assert col in self.cat_df.columns, f"Missing column: {col}"

    def test_category_product_counts_add_up(self):
        """Sum of category product counts should not exceed total scored products."""
        if self.cat_df is None or self.cat_df.empty:
            return
        scored_df = pd.read_csv(self.tmp_path / "products_scored.csv")
        total_in_categories = self.cat_df["product_count"].sum()
        assert total_in_categories <= len(scored_df)

    def test_category_scores_are_in_valid_range(self):
        """Average scores in category summary should be 0-100."""
        if self.cat_df is None or self.cat_df.empty:
            return
        for col in [
            "avg_overall_score",
            "avg_catalog_score",
            "avg_machine_score",
            "avg_commerce_score",
        ]:
            if col in self.cat_df.columns:
                assert (self.cat_df[col] >= 0).all(), f"{col} has negative values"
                assert (self.cat_df[col] <= 100).all(), f"{col} has values above 100"


# ---------------------------------------------------------------------------
# 5. CLI/shared orchestration integration
# ---------------------------------------------------------------------------


class TestCliSharedOrchestration:
    """Test that CLI entry point uses shared run_audit() correctly."""

    def test_run_audit_returns_expected_keys(self, tmp_path):
        """run_audit() must return a dict with expected keys."""
        urls = ["https://shop.com/product/good"]
        config = {"urls": urls, "output_dir": str(tmp_path), "delay": 0}

        with patch("audit.fetcher.fetch_pages", side_effect=_mock_fetch_pages):
            result = run_audit(config=config)

        required_keys = [
            "output_dir",
            "total_urls",
            "processed",
            "errors",
            "candidates",
        ]
        for key in required_keys:
            assert key in result, f"Missing key in result: {key}"

    def test_run_audit_with_domain_config(self, tmp_path):
        """run_audit() should work with domain-based config (GUI pattern)."""
        config = {
            "domain": "shop.com",
            "output_dir": str(tmp_path),
            "delay": 0,
            "max_urls": 5,
        }

        with patch(
            "audit.pipeline.discover_sitemap_urls",
            return_value=["https://shop.com/sitemap.xml"],
        ):
            with patch("audit.pipeline.fetch_sitemap", return_value=None):
                with pytest.raises(RuntimeError, match="Could not find sitemap"):
                    run_audit(config=config)

    def test_run_audit_with_preloaded_urls(self, tmp_path):
        """run_audit() should accept pre-loaded URLs from GUI."""
        urls = [
            "https://shop.com/product/good",
            "https://shop.com/product/no-schema",
        ]
        config = {
            "urls": urls,
            "output_dir": str(tmp_path),
            "delay": 0,
        }

        with patch("audit.fetcher.fetch_pages", side_effect=_mock_fetch_pages):
            result = run_audit(config=config)

        assert result["total_urls"] == 2
        assert result["processed"] >= 1

    def test_run_audit_empty_urls_raises(self, tmp_path):
        """run_audit() should raise when empty URL list is provided."""
        config = {"urls": [], "output_dir": str(tmp_path)}
        with pytest.raises(ValueError):
            run_audit(config=config)

    def test_run_audit_no_source_raises(self, tmp_path):
        """run_audit() should raise when no input source is provided."""
        config = {"output_dir": str(tmp_path)}
        with pytest.raises(ValueError):
            run_audit(config=config)


# ---------------------------------------------------------------------------
# 6. GUI adapter integration
# ---------------------------------------------------------------------------


class TestResultsAdapterIntegration:
    """Test ResultsAdapter with real pipeline output."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.tmp_path = tmp_path
        urls = [
            "https://shop.com/product/good",
            "https://shop.com/product/no-schema",
            "https://shop.com/product/noindex",
            "https://shop.com/product/canonical-mismatch",
            "https://shop.com/product/error",
        ]
        config = {"urls": urls, "output_dir": str(tmp_path), "delay": 0}
        with patch("audit.fetcher.fetch_pages", side_effect=_mock_fetch_pages):
            run_audit(config=config)
        self.scored_path = str(tmp_path / "products_scored.csv")
        self.shortlist_path = str(tmp_path / "manual_review_candidates.csv")

    def test_results_adapter_loads_scored_data(self):
        """ResultsAdapter should be able to load and filter scored data."""
        from gui.adapters.results_adapter import ResultsAdapter

        df = pd.read_csv(self.scored_path)
        adapter = ResultsAdapter(data=df)
        assert len(adapter._data) > 0

    def test_results_adapter_filter_by_severity(self):
        """ResultsAdapter should filter by noindex flag."""
        from gui.adapters.results_adapter import ResultsAdapter

        df = pd.read_csv(self.scored_path)
        # CSV export converts bool to 0/1; adapter expects bool
        for col in [
            "flag_noindex",
            "flag_canonical_mismatch",
            "flag_js_rendered",
            "suspicious_price_missing",
            "suspicious_schema_missing",
            "is_likely_product_page",
        ]:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        adapter = ResultsAdapter(data=df)

        filtered = adapter.filter_data(noindex=True)
        assert isinstance(filtered, pd.DataFrame)

    def test_results_adapter_get_column_mapping(self):
        """ResultsAdapter should map canonical column names correctly."""
        from gui.adapters.results_adapter import ResultsAdapter

        df = pd.read_csv(self.scored_path)
        adapter = ResultsAdapter(data=df)

        urls = adapter.get_column("url")
        assert len(urls) > 0

    def test_results_adapter_score_formatting(self):
        """ResultsAdapter should format score values correctly."""
        from gui.adapters.results_adapter import ResultsAdapter

        df = pd.read_csv(self.scored_path)
        adapter = ResultsAdapter(data=df)

        for col in [
            "overall_score",
            "catalog_score",
            "machine_score",
            "commerce_score",
        ]:
            values = adapter.get_column(col)
            for v in values:
                if v is not None and str(v) not in ("nan", "NaN", "-"):
                    assert isinstance(v, (int, float, str))


class TestReviewAdapterIntegration:
    """Test ReviewAdapter with real pipeline output."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.tmp_path = tmp_path
        urls = [
            "https://shop.com/product/good",
            "https://shop.com/product/no-schema",
            "https://shop.com/product/noindex",
            "https://shop.com/product/canonical-mismatch",
            "https://shop.com/product/error",
        ]
        config = {"urls": urls, "output_dir": str(tmp_path), "delay": 0}
        with patch("audit.fetcher.fetch_pages", side_effect=_mock_fetch_pages):
            run_audit(config=config)
        self.shortlist_path = str(tmp_path / "manual_review_candidates.csv")

    def test_review_adapter_loads_shortlist(self):
        """ReviewAdapter should load shortlist CSV correctly."""
        from gui.adapters.review_adapter import ReviewAdapter

        df = pd.read_csv(self.shortlist_path)
        candidates = df.to_dict(orient="records")
        adapter = ReviewAdapter(candidates=candidates)
        assert len(adapter._candidates) > 0
        assert "severity" in adapter._candidates[0]
        assert "reasons" in adapter._candidates[0]

    def test_review_adapter_severity_formatting(self):
        """ReviewAdapter should format severity levels correctly."""
        from gui.adapters.review_adapter import ReviewAdapter

        candidates = [
            {"severity": s, "reasons": "test"}
            for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        ]
        adapter = ReviewAdapter(candidates=candidates)

        for i, candidate in enumerate(candidates):
            formatted = adapter.get_formatted_severity(candidate)
            assert formatted is not None
            assert len(formatted) > 0

    def test_review_adapter_reason_formatting(self):
        """ReviewAdapter should format reason codes correctly."""
        from gui.adapters.review_adapter import ReviewAdapter

        candidates = [{"severity": "CRITICAL", "reasons": "fetch-error, non-200"}]
        adapter = ReviewAdapter(candidates=candidates)

        formatted = adapter.get_formatted_reasons(candidates[0])
        assert len(formatted) > 0

    def test_review_adapter_color_mapping(self):
        """ReviewAdapter should map severity to colors."""
        from gui.adapters.review_adapter import ReviewAdapter

        candidates = [
            {"severity": s, "reasons": "test"}
            for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        ]
        adapter = ReviewAdapter(candidates=candidates)

        for candidate in candidates:
            color = adapter.get_row_color(candidate)
            assert color is not None


# ---------------------------------------------------------------------------
# 7. Data contract consistency across layers
# ---------------------------------------------------------------------------


class TestDataContractConsistency:
    """Test that data contract is maintained across all layers."""

    def test_extractor_to_scorer_contract(self):
        """Columns produced by extractor must be consumable by scorer."""
        rows = []
        for url, html in [
            ("https://shop.com/product/good", HTML_GOOD_PRODUCT),
            ("https://shop.com/product/no-schema", HTML_MISSING_SCHEMA),
        ]:
            fetch = _make_fetch_result(url, html=html)
            rows.append(build_product_audit_row(fetch))

        df_raw = rows_to_dataframe(rows)
        df_scored = build_scored_dataframe(df_raw)

        # Scored DataFrame must have all raw columns plus score columns
        for col in df_raw.columns:
            assert col in df_scored.columns, f"Raw column {col} lost in scoring"

        # Must have score columns
        for col in [
            "overall_score",
            "catalog_score",
            "machine_score",
            "commerce_score",
            "agent_ready",
        ]:
            assert col in df_scored.columns, f"Score column missing: {col}"

    def test_scorer_to_shortlist_contract(self):
        """Columns produced by scorer must be consumable by shortlist."""
        rows = []
        for url, html in [
            ("https://shop.com/product/good", HTML_GOOD_PRODUCT),
            ("https://shop.com/product/noindex", HTML_NOINDEX_PAGE),
            ("https://shop.com/product/error", None),
        ]:
            fetch = _make_fetch_result(
                url,
                html=html,
                error="Connection timeout" if url.endswith("error") else None,
            )
            rows.append(build_product_audit_row(fetch))

        df_raw = rows_to_dataframe(rows)
        df_scored = build_scored_dataframe(df_raw)
        shortlist = select_manual_review_candidates(df_scored)

        assert not shortlist.empty
        assert "severity" in shortlist.columns
        assert "reasons" in shortlist.columns
        assert "url" in shortlist.columns

    def test_scorer_to_category_summary_contract(self):
        """Columns produced by scorer must support category summary."""
        rows = []
        for url, html in [
            ("https://shop.com/product/good", HTML_GOOD_PRODUCT),
            ("https://shop.com/product/no-schema", HTML_MISSING_SCHEMA),
        ]:
            fetch = _make_fetch_result(url, html=html)
            rows.append(build_product_audit_row(fetch))

        df_raw = rows_to_dataframe(rows)
        df_scored = build_scored_dataframe(df_raw)
        cat_summary = summarize_by_category(df_scored)

        # summarize_by_category returns None if no breadcrumb_text column
        # or all breadcrumbs are NA. With our HTML fixtures, breadcrumbs exist.
        if cat_summary is not None:
            assert not cat_summary.empty
            assert "category" in cat_summary.columns
            assert "product_count" in cat_summary.columns

    def test_sitewide_summary_returns_valid_dict(self):
        """Sitewide summary must return expected keys with valid values."""
        rows = []
        for url, html in [
            ("https://shop.com/product/good", HTML_GOOD_PRODUCT),
            ("https://shop.com/product/no-schema", HTML_MISSING_SCHEMA),
        ]:
            fetch = _make_fetch_result(url, html=html)
            rows.append(build_product_audit_row(fetch))

        df_raw = rows_to_dataframe(rows)
        df_scored = build_scored_dataframe(df_raw)
        summary = summarize_sitewide_scores(df_scored)

        assert "avg_overall_score" in summary
        assert "avg_catalog_score" in summary
        assert "avg_machine_score" in summary
        assert "avg_commerce_score" in summary
        assert 0 <= summary["avg_overall_score"] <= 100

    def test_best_sample_contains_high_scoring_products(self):
        """Best products sample should contain high-scoring, agent-ready products."""
        rows = []
        for url, html in [
            ("https://shop.com/product/good", HTML_GOOD_PRODUCT),
            ("https://shop.com/product/no-schema", HTML_MISSING_SCHEMA),
        ]:
            fetch = _make_fetch_result(url, html=html)
            rows.append(build_product_audit_row(fetch))

        df_raw = rows_to_dataframe(rows)
        df_scored = build_scored_dataframe(df_raw)
        sample = select_best_products_sample(df_scored)

        if not sample.empty:
            assert "overall_score" in sample.columns
            # Sample should contain relatively high-scoring products
            assert sample["overall_score"].mean() >= 30
