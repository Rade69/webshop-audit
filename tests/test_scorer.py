"""
Tests for audit/scorer.py — scoring and flag detection.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pandas as pd
from audit.scorer import (
    score_catalog_completeness,
    score_machine_readability,
    score_commerce_clarity,
    detect_indexability_blockers,
    detect_missing_fields,
    build_scored_dataframe,
)


def full_row() -> dict:
    """A complete, ideal product row."""
    return {
        "url": "https://shop.com/product/1",
        "final_url": "https://shop.com/product/1",
        "status_code": 200,
        "fetch_error": None,
        "title": "Nike Air Max 90",
        "meta_description": "Best running shoe",
        "h1": "Nike Air Max 90",
        "canonical": "https://shop.com/product/1",
        "robots_meta": "index, follow",
        "breadcrumb_text": "Home > Shoes > Nike Air Max 90",
        "visible_text_length": 500,
        "image_count": 5,
        "product_image_count": 4,
        "html_price_text": "129.99 EUR",
        "shipping_signal": True,
        "returns_signal": True,
        "description_word_count": 200,
        "has_feature_list": True,
        "has_spec_table": False,
        "description_quality_score": 90,
        "schema_product_present": True,
        "schema_offer_present": True,
        "schema_name": "Nike Air Max 90",
        "schema_description": "Classic running shoe",
        "schema_sku": "NK-001",
        "schema_gtin": "1234567890123",
        "schema_brand": "Nike",
        "schema_price": "129.99",
        "schema_price_value": 129.99,
        "schema_currency": "EUR",
        "schema_availability": "InStock",
        "is_likely_product_page": True,
        "is_likely_js_rendered": False,
        "js_render_confidence": "none",
    }


def empty_row() -> dict:
    """A completely empty/failed product row."""
    return {
        "url": "https://shop.com/product/2",
        "final_url": None,
        "status_code": None,
        "fetch_error": "Timeout",
        "title": None,
        "meta_description": None,
        "h1": None,
        "canonical": None,
        "robots_meta": None,
        "breadcrumb_text": None,
        "visible_text_length": 0,
        "image_count": 0,
        "product_image_count": 0,
        "html_price_text": None,
        "shipping_signal": False,
        "returns_signal": False,
        "description_word_count": 0,
        "has_feature_list": False,
        "has_spec_table": False,
        "description_quality_score": 0,
        "schema_product_present": False,
        "schema_offer_present": False,
        "schema_name": None,
        "schema_description": None,
        "schema_sku": None,
        "schema_gtin": None,
        "schema_brand": None,
        "schema_price": None,
        "schema_price_value": None,
        "schema_currency": None,
        "schema_availability": None,
        "is_likely_product_page": False,
        "is_likely_js_rendered": False,
        "js_render_confidence": "none",
    }


# ---------------------------------------------------------------------------
# score_catalog_completeness
# ---------------------------------------------------------------------------

def test_catalog_score_full_row():
    score = score_catalog_completeness(full_row())
    assert score == 100

def test_catalog_score_empty_row():
    score = score_catalog_completeness(empty_row())
    assert score == 0

def test_catalog_score_no_schema_not_zero():
    """A shop without JSON-LD but good HTML content should not score zero."""
    row = full_row()
    row["schema_name"] = None
    row["schema_description"] = None
    row["schema_sku"] = None
    row["schema_brand"] = None
    row["schema_gtin"] = None
    row["schema_product_present"] = False
    row["schema_offer_present"] = False
    # catalog_score should still be > 0 because it only measures HTML fields
    score = score_catalog_completeness(row)
    assert score > 0, f"Expected score > 0 for page with good HTML but no schema, got {score}"

def test_catalog_score_range():
    for row in [full_row(), empty_row()]:
        score = score_catalog_completeness(row)
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# score_machine_readability
# ---------------------------------------------------------------------------

def test_machine_score_full_row():
    score = score_machine_readability(full_row())
    assert score == 100

def test_machine_score_empty_row():
    score = score_machine_readability(empty_row())
    # Not noindex gives points even on empty row
    assert score >= 0

def test_machine_score_noindex_penalized():
    row = full_row()
    score_normal = score_machine_readability(row)
    row["robots_meta"] = "noindex, nofollow"
    score_noindex = score_machine_readability(row)
    assert score_noindex < score_normal

def test_machine_score_range():
    for row in [full_row(), empty_row()]:
        score = score_machine_readability(row)
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# score_commerce_clarity
# ---------------------------------------------------------------------------

def test_commerce_score_full_row():
    """Full row with all signals should score close to 100."""
    score = score_commerce_clarity(full_row())
    assert score >= 95  # Near-perfect score

def test_commerce_score_empty_row():
    score = score_commerce_clarity(empty_row())
    assert score == 0

def test_commerce_score_html_price_counts():
    row = empty_row()
    row["html_price_text"] = "29.99"
    row["product_image_count"] = 3
    score = score_commerce_clarity(row)
    assert score > 0

def test_commerce_score_range():
    for row in [full_row(), empty_row()]:
        score = score_commerce_clarity(row)
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# No double penalty test
# ---------------------------------------------------------------------------

def test_no_double_penalty_for_missing_schema():
    """
    A page with no JSON-LD but good HTML content should score reasonably
    in catalog_score. The absence of schema should only penalize machine_score.
    """
    html_only_row = full_row()
    html_only_row.update({
        "schema_product_present": False,
        "schema_offer_present": False,
        "schema_name": None,
        "schema_description": None,
        "schema_sku": None,
        "schema_gtin": None,
        "schema_brand": None,
        "schema_price": None,
        "schema_price_value": None,
        "schema_currency": None,
        "schema_availability": None,
    })
    catalog = score_catalog_completeness(html_only_row)
    machine = score_machine_readability(html_only_row)

    # catalog_score should be high (HTML is complete)
    assert catalog >= 70, f"Expected catalog_score >= 70 for good HTML page, got {catalog}"
    # machine_score should be low (no schema)
    assert machine < 30, f"Expected machine_score < 30 for page without schema, got {machine}"


# ---------------------------------------------------------------------------
# detect_indexability_blockers
# ---------------------------------------------------------------------------

def test_no_flags_on_clean_page():
    assert detect_indexability_blockers(full_row()) == []

def test_noindex_flag():
    row = full_row()
    row["robots_meta"] = "noindex"
    flags = detect_indexability_blockers(row)
    assert "noindex" in flags

def test_fetch_error_flag():
    row = empty_row()
    flags = detect_indexability_blockers(row)
    assert "fetch_error" in flags

def test_non_200_flag():
    row = full_row()
    row["status_code"] = 404
    row["fetch_error"] = "HTTP 404"
    flags = detect_indexability_blockers(row)
    assert any("status_" in f for f in flags)

def test_canonical_mismatch_flag():
    row = full_row()
    row["canonical"] = "https://shop.com/product/different"
    flags = detect_indexability_blockers(row)
    assert "canonical_mismatch" in flags


# ---------------------------------------------------------------------------
# build_scored_dataframe
# ---------------------------------------------------------------------------

def test_build_scored_dataframe_columns():
    df = pd.DataFrame([full_row(), empty_row()])
    scored = build_scored_dataframe(df)
    expected_cols = [
        "catalog_score", "machine_score", "commerce_score", "overall_score",
        "missing_fields", "indexability_flags",
        "flag_noindex", "flag_canonical_mismatch", "flag_fetch_error", "flag_non_200",
        "suspicious_price_missing", "suspicious_schema_missing", "suspicious_low_content",
        "flag_not_product_page",
    ]
    for col in expected_cols:
        assert col in scored.columns, f"Missing column: {col}"

def test_build_scored_dataframe_scores_in_range():
    df = pd.DataFrame([full_row(), empty_row()])
    scored = build_scored_dataframe(df)
    for col in ["catalog_score", "machine_score", "commerce_score", "overall_score"]:
        assert scored[col].between(0, 100).all(), f"{col} out of 0-100 range"

def test_build_scored_full_row_scores_high():
    """Full row should score high on all dimensions."""
    df = pd.DataFrame([full_row()])
    scored = build_scored_dataframe(df)
    assert scored["overall_score"].iloc[0] >= 95  # Near-perfect overall score


# ---------------------------------------------------------------------------
# agent_ready flag
# ---------------------------------------------------------------------------

def test_agent_ready_full_row():
    """Full row should be agent-ready (high scores, no flags)."""
    df = pd.DataFrame([full_row()])
    scored = build_scored_dataframe(df)
    assert scored["agent_ready"].iloc[0] == True


def test_agent_ready_empty_row():
    """Empty row should NOT be agent-ready."""
    df = pd.DataFrame([empty_row()])
    scored = build_scored_dataframe(df)
    assert scored["agent_ready"].iloc[0] == False


def test_agent_ready_js_rendered():
    """JS-rendered products should NOT be agent-ready even with high scores."""
    row = full_row()
    row["is_likely_js_rendered"] = True
    row["js_render_confidence"] = "high"
    df = pd.DataFrame([row])
    scored = build_scored_dataframe(df)
    assert scored["agent_ready"].iloc[0] == False


def test_agent_ready_missing_price():
    """Products without price should NOT be agent-ready."""
    row = full_row()
    row["schema_price"] = None
    row["html_price_text"] = None
    df = pd.DataFrame([row])
    scored = build_scored_dataframe(df)
    assert scored["agent_ready"].iloc[0] == False


def test_agent_ready_missing_schema():
    """Products without schema should NOT be agent-ready."""
    row = full_row()
    row["schema_product_present"] = False
    df = pd.DataFrame([row])
    scored = build_scored_dataframe(df)
    assert scored["agent_ready"].iloc[0] == False
