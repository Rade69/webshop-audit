"""
Tests for audit/utils.py — URL normalization and helper functions.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from audit.utils import normalize_url_for_comparison, is_noindex, normalize_whitespace, score_description_quality


# ---------------------------------------------------------------------------
# normalize_url_for_comparison
# ---------------------------------------------------------------------------

def test_identity_already_normalized():
    url = "https://shop.com/product/nike-air-max"
    assert normalize_url_for_comparison(url) == url

def test_http_normalized_to_https():
    result = normalize_url_for_comparison("http://shop.com/product/1")
    assert result.startswith("https://")

def test_www_stripped():
    result = normalize_url_for_comparison("https://www.shop.com/product/1")
    assert "www." not in result
    assert "shop.com" in result

def test_trailing_slash_stripped():
    a = normalize_url_for_comparison("https://shop.com/product/1/")
    b = normalize_url_for_comparison("https://shop.com/product/1")
    assert a == b

def test_root_trailing_slash_kept():
    result = normalize_url_for_comparison("https://shop.com/")
    # Root path stays as /
    assert result.endswith("/")

def test_utm_params_stripped():
    url = "https://shop.com/product/1?utm_source=google&utm_medium=cpc"
    result = normalize_url_for_comparison(url)
    assert "utm_source" not in result
    assert "utm_medium" not in result
    assert "shop.com/product/1" in result

def test_fbclid_stripped():
    url = "https://shop.com/product/1?fbclid=abc123"
    result = normalize_url_for_comparison(url)
    assert "fbclid" not in result

def test_gclid_stripped():
    url = "https://shop.com/product/1?gclid=xyz"
    result = normalize_url_for_comparison(url)
    assert "gclid" not in result

def test_non_tracking_params_kept():
    url = "https://shop.com/products?color=red&size=42"
    result = normalize_url_for_comparison(url)
    assert "color=red" in result
    assert "size=42" in result

def test_http_vs_https_equal():
    a = normalize_url_for_comparison("http://shop.com/product/1")
    b = normalize_url_for_comparison("https://shop.com/product/1")
    assert a == b

def test_www_vs_non_www_equal():
    a = normalize_url_for_comparison("https://www.shop.com/product/1")
    b = normalize_url_for_comparison("https://shop.com/product/1")
    assert a == b

def test_trailing_slash_equal():
    a = normalize_url_for_comparison("https://shop.com/product/1/")
    b = normalize_url_for_comparison("https://shop.com/product/1")
    assert a == b

def test_relative_url_resolved_with_base():
    result = normalize_url_for_comparison("/product/1", base_url="https://shop.com")
    assert result == "https://shop.com/product/1"

def test_empty_string_returns_empty():
    assert normalize_url_for_comparison("") == ""

def test_none_like_non_string_returns_empty():
    assert normalize_url_for_comparison(None) == ""

def test_whitespace_only_returns_empty():
    assert normalize_url_for_comparison("   ") == ""

def test_netloc_lowercased():
    result = normalize_url_for_comparison("https://SHOP.COM/product/1")
    assert "shop.com" in result
    assert "SHOP.COM" not in result

def test_canonical_mismatch_detected():
    """Two truly different URLs should not normalize to the same value."""
    a = normalize_url_for_comparison("https://shop.com/product/1")
    b = normalize_url_for_comparison("https://shop.com/product/2")
    assert a != b

def test_canonical_match_after_normalization():
    """http+www+trailing-slash should match clean https version."""
    canonical = "http://www.shop.com/product/1/"
    final_url = "https://shop.com/product/1"
    assert normalize_url_for_comparison(canonical) == normalize_url_for_comparison(final_url)


# ---------------------------------------------------------------------------
# is_noindex
# ---------------------------------------------------------------------------

def test_is_noindex_true():
    assert is_noindex("noindex, nofollow") is True

def test_is_noindex_false():
    assert is_noindex("index, follow") is False

def test_is_noindex_none():
    assert is_noindex(None) is False

def test_is_noindex_nan():
    import math
    assert is_noindex(float("nan")) is False

def test_is_noindex_pandas_nan():
    import pandas as pd
    assert is_noindex(pd.NA) is False
    assert is_noindex(float("nan")) is False


# ---------------------------------------------------------------------------
# score_description_quality
# ---------------------------------------------------------------------------

def test_description_score_too_short():
    """word_count < 30 should return 0."""
    assert score_description_quality(description_word_count=0, has_feature_list=False, has_spec_table=False) == 0
    assert score_description_quality(description_word_count=10, has_feature_list=False, has_spec_table=False) == 0
    assert score_description_quality(description_word_count=29, has_feature_list=False, has_spec_table=False) == 0

def test_description_score_minimal():
    """word_count 30-80 should return 40."""
    assert score_description_quality(description_word_count=30, has_feature_list=False, has_spec_table=False) == 40
    assert score_description_quality(description_word_count=50, has_feature_list=False, has_spec_table=False) == 40
    assert score_description_quality(description_word_count=80, has_feature_list=False, has_spec_table=False) == 40

def test_description_score_adequate():
    """word_count 81-150 should return 60."""
    assert score_description_quality(description_word_count=81, has_feature_list=False, has_spec_table=False) == 60
    assert score_description_quality(description_word_count=100, has_feature_list=False, has_spec_table=False) == 60
    assert score_description_quality(description_word_count=150, has_feature_list=False, has_spec_table=False) == 60

def test_description_score_good():
    """word_count 151-300 should return 80."""
    assert score_description_quality(description_word_count=151, has_feature_list=False, has_spec_table=False) == 80
    assert score_description_quality(description_word_count=200, has_feature_list=False, has_spec_table=False) == 80
    assert score_description_quality(description_word_count=300, has_feature_list=False, has_spec_table=False) == 80

def test_description_score_excellent():
    """word_count > 300 should return 90."""
    assert score_description_quality(description_word_count=301, has_feature_list=False, has_spec_table=False) == 90
    assert score_description_quality(description_word_count=500, has_feature_list=False, has_spec_table=False) == 90
    assert score_description_quality(description_word_count=1000, has_feature_list=False, has_spec_table=False) == 90

def test_description_score_bonus_feature_list():
    """+10 bonus if has_feature_list is True."""
    # No bonus
    score = score_description_quality(description_word_count=50, has_feature_list=False, has_spec_table=False)
    assert score == 40
    # With bonus
    score = score_description_quality(description_word_count=50, has_feature_list=True, has_spec_table=False)
    assert score == 50

def test_description_score_bonus_spec_table():
    """+10 bonus if has_spec_table is True."""
    # No bonus
    score = score_description_quality(description_word_count=100, has_feature_list=False, has_spec_table=False)
    assert score == 60
    # With bonus
    score = score_description_quality(description_word_count=100, has_feature_list=False, has_spec_table=True)
    assert score == 70

def test_description_score_bonus_capped_at_100():
    """Score should never exceed 100."""
    # Excellent content + both bonuses = 90 + 10 = 100
    score = score_description_quality(description_word_count=500, has_feature_list=True, has_spec_table=True)
    assert score == 100

def test_description_score_bonus_both_flags():
    """Only +10 bonus even if both flags are True."""
    score = score_description_quality(description_word_count=50, has_feature_list=True, has_spec_table=True)
    assert score == 50  # 40 + 10 (not 40 + 20)
