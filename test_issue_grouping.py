"""
Tests for issue-centric grouping module.

Tests cover:
- Issue grouping by type
- Count consistency
- URL → issue mapping
- Summary statistics
- Integration with scored output
"""
import pandas as pd
import pytest

from audit.issue_grouping import (
    group_by_issue,
    get_all_issue_groups,
    create_issue_summary,
    create_issue_to_urls_mapping,
    get_url_issues,
    get_issue_display_name,
    get_issue_priority,
    get_issue_filter_presets,
    ISSUE_DEFINITIONS,
)


class TestIssueDefinitions:
    """Tests for ISSUE_DEFINITIONS constant."""

    def test_has_required_issues(self):
        """Test that all required issue types are defined."""
        issue_ids = [i["issue_id"] for i in ISSUE_DEFINITIONS]
        
        required = [
            "fetch_error",
            "non_200",
            "not_product_page",
            "noindex",
            "canonical_mismatch",
            "missing_price",
            "missing_schema",
            "js_rendered",
            "low_content",
        ]
        
        for req in required:
            assert req in issue_ids

    def test_all_have_required_fields(self):
        """Test that all issue definitions have required fields."""
        required_fields = ["issue_id", "display_name", "flag_column", "description", "priority"]
        
        for issue_def in ISSUE_DEFINITIONS:
            for field in required_fields:
                assert field in issue_def


class TestGroupByIssue:
    """Tests for group_by_issue function."""

    def test_group_missing_price(self):
        """Test grouping by missing price issue."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 50, "suspicious_price_missing": True},
            {"url": "https://example.com/p2", "overall_score": 75, "suspicious_price_missing": False},
            {"url": "https://example.com/p3", "overall_score": 30, "suspicious_price_missing": True},
        ])
        
        group = group_by_issue(df, "missing_price")
        
        assert group is not None
        assert group.issue_id == "missing_price"
        assert group.count == 2
        assert group.url_count == 2
        assert len(group.urls) == 2  # Both URLs

    def test_group_no_matches(self):
        """Test grouping when no URLs match the issue."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 75, "suspicious_price_missing": False},
            {"url": "https://example.com/p2", "overall_score": 80, "suspicious_price_missing": False},
        ])
        
        group = group_by_issue(df, "missing_price")
        
        assert group is None

    def test_group_with_int_flag(self):
        """Test grouping with int (0/1) flag column."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 50, "flag_noindex": 1},
            {"url": "https://example.com/p2", "overall_score": 75, "flag_noindex": 0},
        ])
        
        group = group_by_issue(df, "noindex")
        
        assert group is not None
        assert group.count == 1

    def test_group_unknown_issue(self):
        """Test grouping with unknown issue_id."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 50},
        ])
        
        group = group_by_issue(df, "unknown_issue")
        
        assert group is None

    def test_group_avg_score(self):
        """Test that average score is calculated correctly."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 40, "suspicious_price_missing": True},
            {"url": "https://example.com/p2", "overall_score": 60, "suspicious_price_missing": True},
        ])
        
        group = group_by_issue(df, "missing_price")
        
        assert group.avg_score == 50.0

    def test_group_urls_sorted_by_score(self):
        """Test that URLs are sorted by score (worst first)."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 80, "suspicious_price_missing": True},
            {"url": "https://example.com/p2", "overall_score": 30, "suspicious_price_missing": True},
            {"url": "https://example.com/p3", "overall_score": 50, "suspicious_price_missing": True},
        ])
        
        group = group_by_issue(df, "missing_price")
        
        # First URL should be the worst score
        assert "p2" in group.urls[0]


class TestGetAllIssueGroups:
    """Tests for get_all_issue_groups function."""

    def test_returns_sorted_groups(self):
        """Test that groups are sorted by priority and count."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 50, 
             "suspicious_price_missing": True, "flag_noindex": False,
             "suspicious_schema_missing": False},
            {"url": "https://example.com/p2", "overall_score": 30,
             "suspicious_price_missing": True, "flag_noindex": True,
             "suspicious_schema_missing": True},
        ])
        
        groups = get_all_issue_groups(df)
        
        # Should have multiple groups
        assert len(groups) >= 2
        
        # Should be sorted by priority (lower = higher priority)
        for i in range(len(groups) - 1):
            assert groups[i].priority <= groups[i+1].priority


class TestCreateIssueSummary:
    """Tests for create_issue_summary function."""

    def test_summary_dataframe_columns(self):
        """Test that summary DataFrame has required columns."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 50, 
             "suspicious_price_missing": True, "flag_noindex": False},
        ])
        
        summary = create_issue_summary(df)
        
        required_cols = ["issue_id", "display_name", "count", "avg_score", "pct_affected"]
        for col in required_cols:
            assert col in summary.columns

    def test_summary_count_matches(self):
        """Test that summary count matches actual count."""
        df = pd.DataFrame([
            {"url": f"https://example.com/p{i}", "overall_score": 50, 
             "suspicious_price_missing": True, "flag_noindex": False}
            for i in range(10)
        ])
        
        summary = create_issue_summary(df)
        
        missing_price_row = summary[summary["issue_id"] == "missing_price"]
        assert len(missing_price_row) == 1
        assert missing_price_row.iloc[0]["count"] == 10


class TestCreateIssueToUrlsMapping:
    """Tests for create_issue_to_urls_mapping function."""

    def test_mapping_has_required_columns(self):
        """Test that mapping DataFrame has required columns."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 50, 
             "suspicious_price_missing": True},
        ])
        
        mapping = create_issue_to_urls_mapping(df)
        
        required_cols = ["issue_id", "display_name", "url", "overall_score"]
        for col in required_cols:
            assert col in mapping.columns

    def test_mapping_one_row_per_issue_url(self):
        """Test that there's one row per issue-URL pair."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 50, 
             "suspicious_price_missing": True, "flag_noindex": True},
        ])
        
        mapping = create_issue_to_urls_mapping(df)
        
        # Should have 2 rows (missing_price + noindex)
        assert len(mapping) == 2

    def test_mapping_min_count_filter(self):
        """Test that min_count parameter filters issues."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 50, 
             "suspicious_price_missing": True},
        ])
        
        mapping = create_issue_to_urls_mapping(df, min_count=5)
        
        # Should be empty (only 1 URL, min_count is 5)
        assert len(mapping) == 0


class TestGetUrlIssues:
    """Tests for get_url_issues function."""

    def test_get_issues_for_url(self):
        """Test getting all issues for a specific URL."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 30,
             "suspicious_price_missing": True, "flag_noindex": True,
             "suspicious_schema_missing": False, "flag_fetch_error": False,
             "flag_non_200": False, "flag_not_product_page": False,
             "flag_canonical_mismatch": False, "flag_js_rendered": False,
             "suspicious_low_content": False},
            {"url": "https://example.com/p2", "overall_score": 75,
             "suspicious_price_missing": False, "flag_noindex": False,
             "suspicious_schema_missing": False, "flag_fetch_error": False,
             "flag_non_200": False, "flag_not_product_page": False,
             "flag_canonical_mismatch": False, "flag_js_rendered": False,
             "suspicious_low_content": False},
        ])
        
        issues = get_url_issues(df, "https://example.com/p1")
        
        assert "missing_price" in issues
        assert "noindex" in issues

    def test_get_issues_for_unknown_url(self):
        """Test getting issues for unknown URL."""
        df = pd.DataFrame([
            {"url": "https://example.com/p1", "overall_score": 50},
        ])
        
        issues = get_url_issues(df, "https://example.com/unknown")
        
        assert issues == []


class TestGetIssueDisplayInfo:
    """Tests for get_issue_display_name and get_issue_priority."""

    def test_get_display_name(self):
        """Test getting display name for issue_id."""
        name = get_issue_display_name("missing_price")
        assert name == "Nema cijene"

    def test_get_display_name_unknown(self):
        """Test getting display name for unknown issue_id."""
        name = get_issue_display_name("unknown_issue")
        assert name == "unknown_issue"

    def test_get_priority(self):
        """Test getting priority for issue_id."""
        priority = get_issue_priority("fetch_error")
        assert priority == 1  # Highest priority

    def test_get_priority_medium(self):
        """Test getting priority for medium priority issue."""
        priority = get_issue_priority("js_rendered")
        assert priority == 3

    def test_get_priority_unknown(self):
        """Test getting priority for unknown issue_id."""
        priority = get_issue_priority("unknown_issue")
        assert priority == 99


class TestGetIssueFilterPresets:
    """Tests for get_issue_filter_presets function."""

    def test_presets_is_dict(self):
        """Test that presets returns a dictionary."""
        presets = get_issue_filter_presets()
        assert isinstance(presets, dict)

    def test_presets_has_flag_columns(self):
        """Test that presets maps to flag columns."""
        presets = get_issue_filter_presets()
        
        # Check a few known mappings
        assert "Nema cijene" in presets
        assert presets["Nema cijene"] == "suspicious_price_missing"
        
        assert "Noindex" in presets
        assert presets["Noindex"] == "flag_noindex"


class TestIssueGroupDataclass:
    """Tests for IssueGroup dataclass."""

    def test_to_dict(self):
        """Test converting IssueGroup to dictionary."""
        from audit.issue_grouping import IssueGroup
        
        group = IssueGroup(
            issue_id="missing_price",
            display_name="Nema cijene",
            description="Test description",
            priority=2,
            count=10,
            avg_score=45.5,
            urls=["https://example.com/p1", "https://example.com/p2"],
            url_count=10,
        )
        
        result = group.to_dict()
        
        assert result["issue_id"] == "missing_price"
        assert result["count"] == 10
        assert result["avg_score"] == 45.5
        assert len(result["urls"]) == 2


class TestFixImpact:
    """Tests for fix impact feature."""

    def test_get_issue_impact_high(self):
        """Test getting HIGH impact for critical issues."""
        from audit.issue_grouping import get_issue_impact
        
        assert get_issue_impact("missing_price") == "HIGH"
        assert get_issue_impact("missing_schema") == "HIGH"
        assert get_issue_impact("fetch_error") == "HIGH"
        assert get_issue_impact("noindex") == "HIGH"
        assert get_issue_impact("canonical_mismatch") == "HIGH"

    def test_get_issue_impact_medium(self):
        """Test getting MEDIUM impact for less critical issues."""
        from audit.issue_grouping import get_issue_impact
        
        assert get_issue_impact("js_rendered") == "MEDIUM"
        assert get_issue_impact("low_content") == "MEDIUM"
        assert get_issue_impact("not_product_page") == "MEDIUM"

    def test_get_issue_impact_unknown(self):
        """Test getting impact for unknown issue."""
        from audit.issue_grouping import get_issue_impact
        
        assert get_issue_impact("unknown_issue") == "LOW"

    def test_get_impact_order(self):
        """Test impact ordering for sorting."""
        from audit.issue_grouping import get_impact_order
        
        assert get_impact_order("HIGH") == 1
        assert get_impact_order("MEDIUM") == 2
        assert get_impact_order("LOW") == 3
        assert get_impact_order("UNKNOWN") == 3

    def test_calculate_fix_impact_score_single_high(self):
        """Test impact score calculation with single HIGH issue."""
        from audit.issue_grouping import calculate_fix_impact_score
        
        result = calculate_fix_impact_score(["missing_price"])
        
        assert result["primary_impact"] == "HIGH"
        assert result["impact_score"] == 1
        assert result["high_count"] == 1
        assert result["medium_count"] == 0
        assert result["low_count"] == 0

    def test_calculate_fix_impact_score_mixed(self):
        """Test impact score calculation with mixed issues."""
        from audit.issue_grouping import calculate_fix_impact_score
        
        result = calculate_fix_impact_score([
            "missing_price",  # HIGH
            "js_rendered",    # MEDIUM
            "low_content",    # MEDIUM
        ])
        
        assert result["primary_impact"] == "HIGH"
        assert result["impact_score"] == 1
        assert result["high_count"] == 1
        assert result["medium_count"] == 2
        assert result["low_count"] == 0

    def test_calculate_fix_impact_score_only_medium(self):
        """Test impact score calculation with only MEDIUM issues."""
        from audit.issue_grouping import calculate_fix_impact_score
        
        result = calculate_fix_impact_score(["js_rendered", "low_content"])
        
        assert result["primary_impact"] == "MEDIUM"
        assert result["impact_score"] == 2
        assert result["high_count"] == 0
        assert result["medium_count"] == 2
        assert result["low_count"] == 0

    def test_calculate_fix_impact_score_empty(self):
        """Test impact score calculation with empty issues list."""
        from audit.issue_grouping import calculate_fix_impact_score
        
        result = calculate_fix_impact_score([])
        
        assert result["primary_impact"] == "LOW"
        assert result["impact_score"] == 3
        assert result["high_count"] == 0
        assert result["medium_count"] == 0
        assert result["low_count"] == 0

    def test_shortlist_candidate_has_fix_impact(self):
        """Test that ShortlistCandidate has fix_impact field."""
        from audit.shortlist import ShortlistCandidate
        
        row = pd.Series({
            "url": "https://example.com/p1",
            "overall_score": 30,
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
        
        assert hasattr(candidate, "fix_impact")
        assert "primary_impact" in candidate.fix_impact
        assert "impact_score" in candidate.fix_impact

    def test_shortlist_candidate_to_dict_has_impact(self):
        """Test that ShortlistCandidate.to_dict includes impact fields."""
        from audit.shortlist import ShortlistCandidate
        
        row = pd.Series({
            "url": "https://example.com/p1",
            "overall_score": 30,
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
        
        assert "fix_impact" in result
        assert "impact_score" in result
        assert result["fix_impact"] == "HIGH"  # missing_price is HIGH impact
