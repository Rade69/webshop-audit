"""
Tests for audit/schema_parser.py — JSON-LD structured data parsing.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from bs4 import BeautifulSoup
from audit.schema_parser import (
    extract_json_ld_blocks,
    flatten_graph_objects,
    find_product_schema,
    find_offer_schema,
    extract_schema_fields,
    _parse_price_value,
)


def make_soup_with_schema(json_str: str) -> BeautifulSoup:
    html = f'<html><head><script type="application/ld+json">{json_str}</script></head><body></body></html>'
    return BeautifulSoup(html, "lxml")


# ---------------------------------------------------------------------------
# _parse_price_value
# ---------------------------------------------------------------------------

def test_parse_price_dot_decimal():
    assert _parse_price_value("29.99") == 29.99

def test_parse_price_comma_decimal():
    assert _parse_price_value("29,99") == 29.99

def test_parse_price_thousands_dot():
    assert _parse_price_value("1.234,56") == 1234.56

def test_parse_price_thousands_comma():
    assert _parse_price_value("1,234.56") == 1234.56

def test_parse_price_integer():
    assert _parse_price_value(99) == 99.0

def test_parse_price_none():
    assert _parse_price_value(None) is None

def test_parse_price_invalid():
    assert _parse_price_value("free") is None


# ---------------------------------------------------------------------------
# extract_json_ld_blocks
# ---------------------------------------------------------------------------

def test_extract_single_block():
    s = make_soup_with_schema('{"@type": "Product", "name": "Test"}')
    blocks = extract_json_ld_blocks(s)
    assert len(blocks) == 1
    assert blocks[0]["@type"] == "Product"

def test_extract_multiple_blocks():
    html = '''<html><head>
        <script type="application/ld+json">{"@type": "Product", "name": "A"}</script>
        <script type="application/ld+json">{"@type": "BreadcrumbList"}</script>
    </head></html>'''
    s = BeautifulSoup(html, "lxml")
    blocks = extract_json_ld_blocks(s)
    assert len(blocks) == 2

def test_extract_invalid_json_skipped():
    html = '''<html><head>
        <script type="application/ld+json">NOT JSON</script>
        <script type="application/ld+json">{"@type": "Product"}</script>
    </head></html>'''
    s = BeautifulSoup(html, "lxml")
    blocks = extract_json_ld_blocks(s)
    assert len(blocks) == 1

def test_extract_no_schema():
    s = BeautifulSoup("<html><body><p>No schema</p></body></html>", "lxml")
    assert extract_json_ld_blocks(s) == []


# ---------------------------------------------------------------------------
# flatten_graph_objects
# ---------------------------------------------------------------------------

def test_flatten_graph():
    blocks = [{"@graph": [{"@type": "Product"}, {"@type": "Offer"}]}]
    objects = flatten_graph_objects(blocks)
    assert len(objects) == 2
    assert objects[0]["@type"] == "Product"

def test_flatten_no_graph():
    blocks = [{"@type": "Product"}, {"@type": "WebPage"}]
    objects = flatten_graph_objects(blocks)
    assert len(objects) == 2

def test_flatten_mixed():
    blocks = [
        {"@type": "WebSite"},
        {"@graph": [{"@type": "Product"}, {"@type": "Offer"}]},
    ]
    objects = flatten_graph_objects(blocks)
    assert len(objects) == 3


# ---------------------------------------------------------------------------
# find_product_schema
# ---------------------------------------------------------------------------

def test_find_product_basic():
    objects = [{"@type": "Product", "name": "Shoes"}]
    result = find_product_schema(objects)
    assert result is not None
    assert result["name"] == "Shoes"

def test_find_product_ignores_product_group():
    objects = [
        {"@type": "ProductGroup", "name": "Group"},
        {"@type": "Product", "name": "Variant"},
    ]
    result = find_product_schema(objects)
    assert result["name"] == "Variant"

def test_find_product_not_found():
    objects = [{"@type": "WebPage"}, {"@type": "BreadcrumbList"}]
    assert find_product_schema(objects) is None

def test_find_product_type_as_list():
    objects = [{"@type": ["Product", "Thing"], "name": "Item"}]
    result = find_product_schema(objects)
    assert result is not None


# ---------------------------------------------------------------------------
# find_offer_schema
# ---------------------------------------------------------------------------

def test_find_offer_inside_product():
    product = {"@type": "Product", "offers": {"@type": "Offer", "price": "29.99"}}
    result = find_offer_schema(product, [product])
    assert result["price"] == "29.99"

def test_find_offer_list_in_product():
    product = {
        "@type": "Product",
        "offers": [
            {"@type": "Offer", "price": "29.99"},
            {"@type": "Offer", "price": "39.99"},
        ]
    }
    result = find_offer_schema(product, [product])
    assert result is not None
    assert result["price"] in ("29.99", "39.99")

def test_find_offer_standalone():
    objects = [
        {"@type": "Product", "name": "Shoes"},
        {"@type": "Offer", "price": "55.00"},
    ]
    product = objects[0]
    result = find_offer_schema(product, objects)
    assert result is not None


# ---------------------------------------------------------------------------
# extract_schema_fields — full integration
# ---------------------------------------------------------------------------

def test_full_product_extraction():
    product = {
        "@type": "Product",
        "name": "Nike Air Max 90",
        "description": "Classic running shoe",
        "sku": "NK-AM90-42",
        "brand": {"@type": "Brand", "name": "Nike"},
        "gtin13": "1234567890123",
    }
    offer = {
        "@type": "Offer",
        "price": "129.99",
        "priceCurrency": "EUR",
        "availability": "https://schema.org/InStock",
    }
    fields = extract_schema_fields(product, offer)

    assert fields["schema_product_present"] is True
    assert fields["schema_offer_present"] is True
    assert fields["schema_name"] == "Nike Air Max 90"
    assert fields["schema_sku"] == "NK-AM90-42"
    assert fields["schema_brand"] == "Nike"
    assert fields["schema_gtin"] == "1234567890123"
    assert fields["schema_price"] == "129.99"
    assert fields["schema_price_value"] == 129.99
    assert fields["schema_currency"] == "EUR"
    assert fields["schema_availability"] == "instock"

def test_no_product_no_offer():
    fields = extract_schema_fields(None, None)
    assert fields["schema_product_present"] is False
    assert fields["schema_offer_present"] is False
    assert fields["schema_price"] is None

def test_brand_as_string():
    product = {"@type": "Product", "name": "Item", "brand": "Adidas"}
    fields = extract_schema_fields(product, None)
    assert fields["schema_brand"] == "Adidas"

def test_availability_normalization():
    offer = {"price": "10", "priceCurrency": "EUR", "availability": "https://schema.org/OutOfStock"}
    fields = extract_schema_fields(None, offer)
    assert fields["schema_availability"] == "outofstock"
