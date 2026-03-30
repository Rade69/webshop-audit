"""
Tests for audit/sitemap.py — sitemap parsing and URL filtering.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from audit.sitemap import parse_sitemap, filter_product_like_urls


URLSET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://shop.com/product/shoe-1</loc></url>
    <url><loc>https://shop.com/product/shoe-2</loc></url>
    <url><loc>https://shop.com/category/shoes</loc></url>
</urlset>"""

SITEMAPINDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <sitemap><loc>https://shop.com/sitemap-products.xml</loc></sitemap>
    <sitemap><loc>https://shop.com/sitemap-pages.xml</loc></sitemap>
</sitemapindex>"""

MALFORMED_XML = "This is not XML at all <<<"


# ---------------------------------------------------------------------------
# parse_sitemap
# ---------------------------------------------------------------------------

def test_parse_urlset():
    result = parse_sitemap(URLSET_XML)
    assert len(result["urls"]) == 3
    assert len(result["child_sitemaps"]) == 0
    assert "https://shop.com/product/shoe-1" in result["urls"]

def test_parse_sitemapindex():
    result = parse_sitemap(SITEMAPINDEX_XML)
    assert len(result["child_sitemaps"]) == 2
    assert len(result["urls"]) == 0
    assert "https://shop.com/sitemap-products.xml" in result["child_sitemaps"]

def test_parse_malformed_xml():
    result = parse_sitemap(MALFORMED_XML)
    assert result["urls"] == []
    assert result["child_sitemaps"] == []

def test_parse_empty_string():
    result = parse_sitemap("")
    assert result["urls"] == []


# ---------------------------------------------------------------------------
# filter_product_like_urls
# ---------------------------------------------------------------------------

def test_filter_keeps_product_urls():
    urls = [
        "https://shop.com/product/shoe-1",
        "https://shop.com/product/shoe-2",
        "https://shop.com/category/shoes",
        "https://shop.com/blog/how-to-choose",
    ]
    filtered, fallback = filter_product_like_urls(urls)
    assert not fallback
    assert all("/product/" in u for u in filtered)
    assert len(filtered) == 2

def test_filter_excludes_category():
    urls = ["https://shop.com/category/shoes", "https://shop.com/product/item"]
    filtered, fallback = filter_product_like_urls(urls)
    assert not any("/category/" in u for u in filtered)

def test_filter_excludes_cart():
    urls = ["https://shop.com/cart", "https://shop.com/product/item"]
    filtered, fallback = filter_product_like_urls(urls)
    assert "https://shop.com/cart" not in filtered

def test_filter_fallback_when_nothing_matches():
    """When no product patterns match, return ALL urls and signal fallback=True."""
    urls = [
        "https://shop.com/custom-path/abc",
        "https://shop.com/custom-path/xyz",
    ]
    filtered, fallback = filter_product_like_urls(urls)
    assert fallback is True
    assert len(filtered) == len(urls)

def test_filter_returns_tuple():
    urls = ["https://shop.com/product/item"]
    result = filter_product_like_urls(urls)
    assert isinstance(result, tuple)
    assert len(result) == 2

def test_filter_empty_input():
    filtered, fallback = filter_product_like_urls([])
    assert filtered == []
