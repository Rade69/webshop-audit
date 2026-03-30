from dataclasses import dataclass, asdict, field
from typing import Optional

import pandas as pd

from audit import parser, schema_parser
from audit.utils import score_description_quality


@dataclass
class ProductAuditRow:
    # Crawl info
    url: str = ""
    final_url: Optional[str] = None
    status_code: Optional[int] = None
    fetch_error: Optional[str] = None
    content_type: Optional[str] = None
    response_time_ms: Optional[int] = None

    # HTML signals
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    canonical: Optional[str] = None
    robots_meta: Optional[str] = None
    breadcrumb_text: Optional[str] = None
    visible_text_length: int = 0
    image_count: int = 0
    product_image_count: int = 0
    html_price_text: Optional[str] = None
    shipping_signal: bool = False
    returns_signal: bool = False

    # Description quality signals
    description_word_count: int = 0
    has_feature_list: bool = False
    has_spec_table: bool = False
    description_quality_score: int = 0

    # Structured data
    schema_product_present: bool = False
    schema_offer_present: bool = False
    schema_name: Optional[str] = None
    schema_description: Optional[str] = None
    schema_sku: Optional[str] = None
    schema_gtin: Optional[str] = None
    schema_brand: Optional[str] = None
    schema_price: Optional[str] = None
    schema_price_value: Optional[float] = None
    schema_currency: Optional[str] = None
    schema_availability: Optional[str] = None

    # Post-fetch classification
    is_likely_product_page: bool = True
    is_likely_js_rendered: bool = False
    js_render_confidence: str = "none"


def _is_likely_product_page(row: "ProductAuditRow") -> bool:
    """
    Post-fetch heuristic: does this page look like a product page?

    Returns False when the page has no product-specific signals at all:
    no schema Product, no price (schema or HTML), no SKU.

    Conservative by design — ambiguous pages remain True.
    Pages where fetch failed are marked False (no data to judge).
    """
    if row.fetch_error:
        return False
    return bool(
        row.schema_product_present
        or row.schema_price
        or row.html_price_text
        or row.schema_sku
    )


def build_product_audit_row(fetch_result: dict) -> ProductAuditRow:
    """
    Combines fetch result, HTML parsing and schema parsing
    into a single standardized ProductAuditRow.
    A single soup object is created and reused — parser functions do not mutate it.
    """
    html = fetch_result.get("html")

    row = ProductAuditRow(
        url=fetch_result.get("url", ""),
        final_url=fetch_result.get("final_url"),
        status_code=fetch_result.get("status_code"),
        fetch_error=fetch_result.get("error"),
        content_type=fetch_result.get("content_type"),
        response_time_ms=fetch_result.get("response_time_ms"),
    )

    if not html:
        row.is_likely_product_page = _is_likely_product_page(row)
        return row

    # Single soup for all parsing — parser functions must NOT mutate it
    soup = parser.make_soup(html)

    row.title = parser.extract_title(soup)
    row.meta_description = parser.extract_meta_description(soup)
    row.h1 = parser.extract_h1(soup)
    # Pass final_url so relative canonicals are resolved to absolute
    row.canonical = parser.extract_canonical(soup, page_url=row.final_url)
    row.robots_meta = parser.extract_robots_meta(soup)
    row.breadcrumb_text = parser.extract_breadcrumb_text(soup)
    row.image_count = parser.extract_image_count(soup)
    row.product_image_count = parser.extract_product_image_count(soup)
    row.html_price_text = parser.extract_possible_price_text(soup)
    row.shipping_signal = parser.extract_shipping_text_signal(soup)
    row.returns_signal = parser.extract_returns_text_signal(soup)
    row.visible_text_length = parser.extract_visible_text_length(soup)

    # Description quality signals
    desc_signals = parser.extract_description_signals(soup)
    row.description_word_count = desc_signals["description_word_count"]
    row.has_feature_list = desc_signals["has_feature_list"]
    row.has_spec_table = desc_signals["has_spec_table"]
    row.description_quality_score = score_description_quality(
        description_word_count=row.description_word_count,
        has_feature_list=row.has_feature_list,
        has_spec_table=row.has_spec_table,
    )

    # JS rendering detection
    js_signals = parser.detect_js_rendered(soup, html)
    row.is_likely_js_rendered = js_signals["is_likely_js_rendered"]
    row.js_render_confidence = js_signals["js_render_confidence"]

    # Structured data — uses the same soup, no second parse
    blocks = schema_parser.extract_json_ld_blocks(soup)
    objects = schema_parser.flatten_graph_objects(blocks)
    product_obj = schema_parser.find_product_schema(objects)
    offer_obj = schema_parser.find_offer_schema(product_obj, objects)
    schema_fields = schema_parser.extract_schema_fields(product_obj, offer_obj)

    for key, value in schema_fields.items():
        setattr(row, key, value)

    row.is_likely_product_page = _is_likely_product_page(row)
    return row


def rows_to_dataframe(rows: list[ProductAuditRow]) -> pd.DataFrame:
    """Converts a list of ProductAuditRow dataclasses to a pandas DataFrame."""
    return pd.DataFrame([asdict(r) for r in rows])
