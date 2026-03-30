"""
Integration tests for audit/extractor.py
Tests the full extraction pipeline: HTML string → ProductAuditRow
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from audit.extractor import build_product_audit_row, rows_to_dataframe, ProductAuditRow


FULL_PRODUCT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Nike Air Max 90 | Shop</title>
    <meta name="description" content="Classic Nike running shoe">
    <link rel="canonical" href="https://shop.com/product/nike-air-max-90">
    <meta name="robots" content="index, follow">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Nike Air Max 90",
        "description": "Classic running shoe",
        "sku": "NK-AM90-42",
        "brand": {"@type": "Brand", "name": "Nike"},
        "gtin13": "1234567890123",
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
    <nav class="breadcrumb">Home > Shoes > Nike Air Max 90</nav>
    <main>
        <h1>Nike Air Max 90</h1>
        <span class="price">129.99 EUR</span>
        <img src="shoe1.jpg" width="500" height="500">
        <img src="shoe2.jpg" width="500" height="500">
        <img src="shoe3.jpg" width="500" height="500">
        <img src="track.gif" width="1" height="1">
        <p>This is a long product description with plenty of visible text content.
        The Nike Air Max 90 is a classic running shoe with excellent cushioning.
        Available in multiple colors. Free shipping on orders over 50 EUR.
        30 day return policy, no questions asked.</p>
    </main>
</body>
</html>
"""

MINIMAL_HTML = """
<html>
<head><title>Product</title></head>
<body><h1>Simple Product</h1><p>Short description.</p></body>
</html>
"""

NOINDEX_HTML = """
<html>
<head>
    <title>Hidden Product</title>
    <meta name="robots" content="noindex, nofollow">
</head>
<body><h1>Hidden</h1></body>
</html>
"""


def make_fetch_result(html: str, url: str = "https://shop.com/product/1") -> dict:
    return {
        "url": url,
        "final_url": url,
        "status_code": 200,
        "html": html,
        "content_type": "text/html; charset=utf-8",
        "error": None,
        "response_time_ms": 150,
    }


def failed_fetch_result(url: str = "https://shop.com/product/2") -> dict:
    return {
        "url": url,
        "final_url": url,
        "status_code": None,
        "html": None,
        "content_type": None,
        "error": "Timeout",
        "response_time_ms": None,
    }


# ---------------------------------------------------------------------------
# Basic extraction
# ---------------------------------------------------------------------------

def test_extract_full_product():
    result = build_product_audit_row(make_fetch_result(FULL_PRODUCT_HTML))
    assert isinstance(result, ProductAuditRow)
    assert result.title == "Nike Air Max 90 | Shop"
    assert result.h1 == "Nike Air Max 90"
    assert result.meta_description == "Classic Nike running shoe"
    assert result.canonical == "https://shop.com/product/nike-air-max-90"
    assert result.robots_meta == "index, follow"

def test_extract_schema_data():
    result = build_product_audit_row(make_fetch_result(FULL_PRODUCT_HTML))
    assert result.schema_product_present is True
    assert result.schema_offer_present is True
    assert result.schema_name == "Nike Air Max 90"
    assert result.schema_sku == "NK-AM90-42"
    assert result.schema_brand == "Nike"
    assert result.schema_gtin == "1234567890123"
    assert result.schema_price == "129.99"
    assert result.schema_price_value == 129.99
    assert result.schema_currency == "EUR"
    assert result.schema_availability is not None

def test_extract_price_from_html():
    result = build_product_audit_row(make_fetch_result(FULL_PRODUCT_HTML))
    assert result.html_price_text is not None

def test_extract_image_counts():
    result = build_product_audit_row(make_fetch_result(FULL_PRODUCT_HTML))
    assert result.image_count == 4           # 3 product + 1 tracking pixel
    assert result.product_image_count == 3   # tracking pixel filtered out

def test_extract_visible_text_not_zero():
    result = build_product_audit_row(make_fetch_result(FULL_PRODUCT_HTML))
    assert result.visible_text_length > 100


# ---------------------------------------------------------------------------
# Soup must not be mutated
# ---------------------------------------------------------------------------

def test_soup_not_mutated_single_parse():
    """
    All fields should be populated correctly from a single soup.
    If soup were mutated mid-extraction, some fields would be None.
    """
    result = build_product_audit_row(make_fetch_result(FULL_PRODUCT_HTML))
    # All these should be populated — if any is None, soup was mutated before it was read
    assert result.title is not None, "title is None — soup may have been mutated"
    assert result.h1 is not None, "h1 is None — soup may have been mutated"
    assert result.schema_name is not None, "schema_name is None — soup may have been mutated"
    assert result.canonical is not None, "canonical is None — soup may have been mutated"


# ---------------------------------------------------------------------------
# Failed fetch handling
# ---------------------------------------------------------------------------

def test_failed_fetch_returns_row_with_error():
    result = build_product_audit_row(failed_fetch_result())
    assert isinstance(result, ProductAuditRow)
    assert result.fetch_error == "Timeout"
    assert result.title is None
    assert result.schema_product_present is False

def test_failed_fetch_does_not_raise():
    """A fetch failure must never raise an exception."""
    try:
        result = build_product_audit_row(failed_fetch_result())
    except Exception as e:
        pytest.fail(f"build_product_audit_row raised on failed fetch: {e}")


# ---------------------------------------------------------------------------
# Minimal page
# ---------------------------------------------------------------------------

def test_minimal_page():
    result = build_product_audit_row(make_fetch_result(MINIMAL_HTML))
    assert result.title == "Product"
    assert result.h1 == "Simple Product"
    assert result.schema_product_present is False
    assert result.schema_price is None


# ---------------------------------------------------------------------------
# Noindex detection
# ---------------------------------------------------------------------------

def test_noindex_detected():
    result = build_product_audit_row(make_fetch_result(NOINDEX_HTML))
    assert result.robots_meta is not None
    assert "noindex" in result.robots_meta


# ---------------------------------------------------------------------------
# rows_to_dataframe
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# is_likely_product_page
# ---------------------------------------------------------------------------

def test_is_likely_product_page_full_product():
    """Full product with schema + price → is_likely_product_page True."""
    result = build_product_audit_row(make_fetch_result(FULL_PRODUCT_HTML))
    assert result.is_likely_product_page is True

def test_is_likely_product_page_minimal_no_signals():
    """Page with only title/h1, no price/schema/sku → not a product page."""
    result = build_product_audit_row(make_fetch_result(MINIMAL_HTML))
    assert result.is_likely_product_page is False

def test_is_likely_product_page_failed_fetch():
    """Failed fetch → not a product page (no data to judge)."""
    result = build_product_audit_row(failed_fetch_result())
    assert result.is_likely_product_page is False

def test_is_likely_product_page_html_price_only():
    """HTML price alone (no schema) → treated as product page."""
    html = """
    <html><head><title>Product</title></head>
    <body><h1>Widget</h1><span class="price">19.99 EUR</span></body>
    </html>
    """
    result = build_product_audit_row(make_fetch_result(html))
    assert result.is_likely_product_page is True


def test_rows_to_dataframe():
    rows = [
        build_product_audit_row(make_fetch_result(FULL_PRODUCT_HTML, "https://shop.com/1")),
        build_product_audit_row(make_fetch_result(MINIMAL_HTML, "https://shop.com/2")),
        build_product_audit_row(failed_fetch_result("https://shop.com/3")),
    ]
    df = rows_to_dataframe(rows)
    assert len(df) == 3
    assert "url" in df.columns
    assert "schema_product_present" in df.columns
    assert "schema_price_value" in df.columns
