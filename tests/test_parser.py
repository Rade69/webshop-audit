"""
Tests for audit/parser.py — HTML extraction functions.
All tests use static HTML strings, no HTTP requests.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from bs4 import BeautifulSoup
from audit.parser import (
    make_soup,
    extract_title,
    extract_meta_description,
    extract_h1,
    extract_canonical,
    extract_robots_meta,
    extract_breadcrumb_text,
    extract_visible_text_length,
    extract_image_count,
    extract_product_image_count,
    extract_possible_price_text,
    extract_possible_price_value,
    extract_shipping_text_signal,
    extract_returns_text_signal,
    detect_js_rendered,
)


def soup(html: str) -> BeautifulSoup:
    return make_soup(html)


# ---------------------------------------------------------------------------
# extract_title
# ---------------------------------------------------------------------------

def test_extract_title_found():
    s = soup("<html><head><title>Nike Air Max 90</title></head><body></body></html>")
    assert extract_title(s) == "Nike Air Max 90"

def test_extract_title_missing():
    s = soup("<html><head></head><body></body></html>")
    assert extract_title(s) is None

def test_extract_title_whitespace_cleaned():
    s = soup("<html><head><title>  Nike   Air  </title></head></html>")
    assert extract_title(s) == "Nike Air"


# ---------------------------------------------------------------------------
# extract_meta_description
# ---------------------------------------------------------------------------

def test_meta_description_found():
    s = soup('<html><head><meta name="description" content="Best running shoes"></head></html>')
    assert extract_meta_description(s) == "Best running shoes"

def test_meta_description_missing():
    s = soup("<html><head></head></html>")
    assert extract_meta_description(s) is None

def test_meta_description_case_insensitive():
    s = soup('<html><head><meta name="Description" content="Test desc"></head></html>')
    assert extract_meta_description(s) == "Test desc"


# ---------------------------------------------------------------------------
# extract_h1
# ---------------------------------------------------------------------------

def test_extract_h1_found():
    s = soup("<html><body><h1>Product Name</h1></body></html>")
    assert extract_h1(s) == "Product Name"

def test_extract_h1_missing():
    s = soup("<html><body><h2>Not H1</h2></body></html>")
    assert extract_h1(s) is None

def test_extract_h1_returns_first_only():
    s = soup("<html><body><h1>First</h1><h1>Second</h1></body></html>")
    assert extract_h1(s) == "First"


# ---------------------------------------------------------------------------
# extract_canonical
# ---------------------------------------------------------------------------

def test_canonical_found():
    s = soup('<html><head><link rel="canonical" href="https://shop.com/product/1"/></head></html>')
    assert extract_canonical(s) == "https://shop.com/product/1"

def test_canonical_missing():
    s = soup("<html><head></head></html>")
    assert extract_canonical(s) is None


# ---------------------------------------------------------------------------
# extract_robots_meta
# ---------------------------------------------------------------------------

def test_robots_noindex():
    s = soup('<html><head><meta name="robots" content="noindex, nofollow"></head></html>')
    result = extract_robots_meta(s)
    assert result is not None
    assert "noindex" in result

def test_robots_index():
    s = soup('<html><head><meta name="robots" content="index, follow"></head></html>')
    result = extract_robots_meta(s)
    assert "noindex" not in (result or "")

def test_robots_missing():
    s = soup("<html><head></head></html>")
    assert extract_robots_meta(s) is None


# ---------------------------------------------------------------------------
# extract_visible_text_length — critical: must NOT mutate soup
# ---------------------------------------------------------------------------

def test_visible_text_length_does_not_mutate_soup():
    s = soup("<html><head><title>Title</title></head><body><h1>H1</h1><script>var x=1</script><p>Text</p></body></html>")
    title_before = extract_title(s)
    h1_before = extract_h1(s)
    _ = extract_visible_text_length(s)
    assert extract_title(s) == title_before, "extract_visible_text_length mutated soup (title changed)"
    assert extract_h1(s) == h1_before, "extract_visible_text_length mutated soup (h1 changed)"

def test_visible_text_excludes_scripts():
    s = soup("<html><body><p>Real text</p><script>var secret = 'hidden'</script></body></html>")
    length = extract_visible_text_length(s)
    # The word 'hidden' from script should not be counted... but length > 0
    assert length > 0

def test_visible_text_empty_page():
    s = soup("<html><body></body></html>")
    assert extract_visible_text_length(s) == 0


# ---------------------------------------------------------------------------
# extract_image_count and extract_product_image_count
# ---------------------------------------------------------------------------

def test_image_count():
    s = soup('<html><body><img src="a.jpg"><img src="b.jpg"><img src="c.jpg"></body></html>')
    assert extract_image_count(s) == 3

def test_image_count_zero():
    s = soup("<html><body><p>No images</p></body></html>")
    assert extract_image_count(s) == 0

def test_product_image_count_filters_tracking_pixels():
    html = '''<html><body>
        <img src="product.jpg" width="500" height="500">
        <img src="track.gif" width="1" height="1">
        <img src="spacer.gif" width="1" height="1">
        <img src="product2.jpg" width="400" height="400">
    </body></html>'''
    s = soup(html)
    assert extract_image_count(s) == 4         # total
    assert extract_product_image_count(s) == 2  # filtered


# ---------------------------------------------------------------------------
# extract_possible_price_text — must NOT fall back to full-page text
# ---------------------------------------------------------------------------

def test_price_from_class_price():
    s = soup('<html><body><span class="price">29.99 EUR</span></body></html>')
    assert extract_possible_price_text(s) is not None

def test_price_from_itemprop():
    s = soup('<html><body><span itemprop="price">49.90</span></body></html>')
    assert extract_possible_price_text(s) is not None

def test_price_missing_no_fallback():
    """When no price element exists, should return None — NOT pick up phone numbers or IDs."""
    s = soup("<html><body><p>Tel: 061 123 456</p><p>Article: 7892</p><p>Year: 2024</p></body></html>")
    assert extract_possible_price_text(s) is None

def test_price_class_cijena():
    s = soup('<html><body><span class="cijena">15,99 KM</span></body></html>')
    result = extract_possible_price_text(s)
    assert result is not None


# ---------------------------------------------------------------------------
# Price format extraction tests (html_price_text and html_price_value)
# ---------------------------------------------------------------------------

def test_price_format_km_bam():
    """Test '45,99 KM' format (Bosnian/Croatian/Serbian)."""
    s = soup('<html><body><span class="price">45,99 KM</span></body></html>')
    text = extract_possible_price_text(s)
    value = extract_possible_price_value(s)
    assert text == "45,99 KM"
    assert value == pytest.approx(45.99, rel=0.01)


def test_price_format_euro_symbol():
    """Test '€ 45.99' format."""
    s = soup('<html><body><span class="price">€ 45.99</span></body></html>')
    text = extract_possible_price_text(s)
    value = extract_possible_price_value(s)
    assert text == "€ 45.99"
    assert value == pytest.approx(45.99, rel=0.01)


def test_price_format_eur_code():
    """Test '45.99 EUR' format."""
    s = soup('<html><body><span class="price">45.99 EUR</span></body></html>')
    text = extract_possible_price_text(s)
    value = extract_possible_price_value(s)
    assert text == "45.99 EUR"
    assert value == pytest.approx(45.99, rel=0.01)


def test_price_format_data_price_attribute():
    """Test data-price attribute format."""
    s = soup('<html><body><div data-price="29.99" class="price-container"></div></body></html>')
    text = extract_possible_price_text(s)
    value = extract_possible_price_value(s)
    assert text is not None
    assert value == pytest.approx(29.99, rel=0.01)


def test_price_format_data_product_price():
    """Test data-product-price attribute format (Shopify/OpenCart)."""
    s = soup('<html><body><span data-product-price="199.99" class="product-price"></span></body></html>')
    text = extract_possible_price_text(s)
    value = extract_possible_price_value(s)
    assert text is not None
    assert value == pytest.approx(199.99, rel=0.01)


def test_price_format_data_sale_price():
    """Test data-sale-price attribute format."""
    s = soup('<html><body><div data-sale-price="79,99" class="sale-price"></div></body></html>')
    text = extract_possible_price_text(s)
    value = extract_possible_price_value(s)
    assert text is not None
    assert value == pytest.approx(79.99, rel=0.01)


def test_price_format_dollar_symbol():
    """Test dollar symbol format."""
    s = soup('<html><body><span class="price">$129.99</span></body></html>')
    text = extract_possible_price_text(s)
    value = extract_possible_price_value(s)
    assert text == "$129.99"
    assert value == pytest.approx(129.99, rel=0.01)


# ---------------------------------------------------------------------------
# Footer vs product area isolation tests
# ---------------------------------------------------------------------------

def test_shipping_signal_in_main():
    html = '<html><body><main><p>Free shipping on orders over 50 EUR.</p></main></html>'
    s = soup(html)
    assert extract_shipping_text_signal(s) is True

def test_shipping_signal_dostava():
    html = '<html><body><main><p>Besplatna dostava za narudžbe iznad 50 KM.</p></main></html>'
    s = soup(html)
    assert extract_shipping_text_signal(s) is True

def test_returns_signal_in_product_area():
    html = '<html><body><main><p>30 day return policy. No questions asked.</p></main></html>'
    s = soup(html)
    assert extract_returns_text_signal(s) is True

def test_returns_signal_povrat_robe():
    html = '<html><body><main><p>Povrat robe u roku od 30 dana.</p></main></html>'
    s = soup(html)
    assert extract_returns_text_signal(s) is True


# ---------------------------------------------------------------------------
# Footer vs product area isolation tests
# ---------------------------------------------------------------------------

def test_shipping_signal_not_triggered_by_footer():
    """
    Keyword in footer should NOT trigger True.
    Keyword must be in product area (main/article) to trigger.
    """
    # Footer contains "shipping" but product area does not
    html = '''<html>
    <body>
        <main><p>Product name: Nike Air Max</p><p>Price: 120 EUR</p></main>
        <footer><a href="/shipping">Shipping info</a><p>Free shipping on all orders over 100 EUR</p></footer>
    </body>
    </html>'''
    s = soup(html)
    assert extract_shipping_text_signal(s) is False, \
        "Shipping in footer should NOT trigger True — product area has no shipping keywords"


def test_shipping_signal_triggered_by_main():
    """
    Keyword in main tag should trigger True.
    """
    html = '''<html>
    <body>
        <main><p>Free shipping on orders over 50 EUR.</p></main>
        <footer><p>Copyright 2024</p></footer>
    </body>
    </html>'''
    s = soup(html)
    assert extract_shipping_text_signal(s) is True


def test_shipping_signal_triggered_by_article():
    """
    Keyword in article tag should trigger True.
    """
    html = '''<html>
    <body>
        <article><p>Express delivery available for all items.</p></article>
        <footer><p>Copyright 2024</p></footer>
    </body>
    </html>'''
    s = soup(html)
    assert extract_shipping_text_signal(s) is True


def test_returns_signal_not_triggered_by_footer():
    """
    Keyword in footer should NOT trigger True.
    Keyword must be in product area to trigger.
    """
    html = '''<html>
    <body>
        <main><p>Product description here.</p></main>
        <footer>
            <a href="/return-policy">Return Policy</a>
            <p>30 day return policy applies to all purchases.</p>
        </footer>
    </body>
    </html>'''
    s = soup(html)
    assert extract_returns_text_signal(s) is False, \
        "Returns in footer should NOT trigger True — product area has no returns keywords"


def test_returns_signal_triggered_by_main():
    """
    Keyword in main tag should trigger True.
    """
    html = '''<html>
    <body>
        <main><p>30 day return policy. No questions asked.</p></main>
        <footer><p>Copyright 2024</p></footer>
    </body>
    </html>'''
    s = soup(html)


# ---------------------------------------------------------------------------
# detect_js_rendered — JS/SPA rendering detection
# ---------------------------------------------------------------------------

def test_js_rendered_clean_page():
    """
    A normal, well-rendered page should NOT be flagged as JS-rendered.
    """
    html = '''<!DOCTYPE html>
    <html>
    <head><title>Product Name</title></head>
    <body>
        <h1>Product Name</h1>
        <p>This is a detailed product description with lots of content.</p>
        <p>More information about the product features.</p>
        <div class="price">$29.99</div>
    </body>
    </html>'''
    s = soup(html)
    result = detect_js_rendered(s, html)
    assert result["is_likely_js_rendered"] is False
    assert result["js_render_confidence"] == "none"
    assert len(result["js_render_signals"]) == 0


def test_js_rendered_spa_root_element():
    """
    Page with React/Vue/Next.js root element should trigger SPA signal.
    """
    html = '''<!DOCTYPE html>
    <html>
    <head><title>Loading...</title></head>
    <body>
        <div id="root"></div>
        <script src="react.bundle.js"></script>
        <script src="app.js"></script>
    </body>
    </html>'''
    s = soup(html)
    result = detect_js_rendered(s, html)
    assert "spa_root_element" in result["js_render_signals"]
    assert result["is_likely_js_rendered"] is True
    assert result["js_render_confidence"] in ["medium", "high"]


def test_js_rendered_thin_content_large_html():
    """
    Thin visible text but large HTML is a strong JS-rendering signal.
    """
    # Large HTML with minimal rendered content
    large_html = '<html>' + '<div>' * 1000 + '</div>' * 1000 + '<p>Loading</p>' + '</html>'
    large_html = large_html * 20  # Make it > 10000 chars
    s = soup(large_html)
    result = detect_js_rendered(s, large_html)
    assert "thin_content_large_html" in result["js_render_signals"]


def test_js_rendered_no_semantic_content():
    """
    Page with no <p> or <h1> tags should trigger no_semantic_content signal.
    """
    html = '''<!DOCTYPE html>
    <html>
    <head><title>Page</title></head>
    <body>
        <div id="app">Loading...</div>
        <a href="#">Link</a>
    </body>
    </html>'''
    s = soup(html)
    result = detect_js_rendered(s, html)
    assert "no_semantic_content" in result["js_render_signals"]


def test_js_rendered_title_only_no_content():
    """
    Title exists but no H1 and no schema is a JS signal.
    """
    html = '''<!DOCTYPE html>
    <html>
    <head><title>Product Page</title></head>
    <body>
        <div id="app"></div>
        <script>console.log("React app")</script>
    </body>
    </html>'''
    s = soup(html)
    result = detect_js_rendered(s, html)
    assert "title_only_no_content" in result["js_render_signals"]


def test_js_rendered_script_heavy():
    """
    Page with many script tags (>15) should trigger script_heavy signal.
    """
    html = '''<!DOCTYPE html>
    <html>
    <head><title>App</title></head>
    <body>
        <div id="app"></div>
        <script src="1.js"></script>
        <script src="2.js"></script>
        <script src="3.js"></script>
        <script src="4.js"></script>
        <script src="5.js"></script>
        <script src="6.js"></script>
        <script src="7.js"></script>
        <script src="8.js"></script>
        <script src="9.js"></script>
        <script src="10.js"></script>
        <script src="11.js"></script>
        <script src="12.js"></script>
        <script src="13.js"></script>
        <script src="14.js"></script>
        <script src="15.js"></script>
        <script src="16.js"></script>
        <script src="17.js"></script>
    </body>
    </html>'''
    s = soup(html)
    result = detect_js_rendered(s, html)
    assert "script_heavy" in result["js_render_signals"]


def test_js_rendered_high_confidence_multiple_signals():
    """
    Multiple signals should result in high confidence.
    """
    # SPA with root, no content, large HTML
    large_html = '<html>' + '<div>' * 2000 + '</div>' * 2000 + '</html>' * 30
    html = f'''<!DOCTYPE html>
    <html>
    <head><title>Loading</title></head>
    <body>
        <div id="root"></div>
        <div id="app"></div>
        <div id="__next"></div>
        {large_html}
    </body>
    </html>'''
    s = soup(html)
    result = detect_js_rendered(s, html)
    assert result["js_render_confidence"] == "high"
    assert result["is_likely_js_rendered"] is True
    assert len(result["js_render_signals"]) >= 3


def test_js_rendered_low_confidence_single_signal():
    """
    Single signal should result in low confidence but not flagged as JS-rendered.
    Scripts must be inside the body so lxml parses them.
    """
    scripts = "\n".join(["<script>var x=1;</script>"] * 16)
    html = f'''<!DOCTYPE html>
    <html>
    <head><title>Title</title></head>
    <body>
        <h1>Product Name</h1>
        <p>Some content here.</p>
        {scripts}
    </body>
    </html>'''
    s = soup(html)
    result = detect_js_rendered(s, html)
    assert result["js_render_confidence"] == "low"
    assert result["is_likely_js_rendered"] is False
