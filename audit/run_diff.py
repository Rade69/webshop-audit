"""
Run-to-run comparison module.

Compares two audit run outputs and produces:
- run_diff_summary.json: aggregate diff metrics
- run_diff_urls.csv: URL-level changes
- run_diff_categories.csv: category-level changes (if available)

Matching logic:
- Primary key: normalized URL
- Handles new/removed URLs between runs
"""
import json
import os
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from audit.utils import normalize_url_for_comparison


@dataclass
class URLDiff:
    """Represents the diff for a single URL."""
    url: str
    status: str  # "unchanged", "improved", "degraded", "new", "removed"
    score_delta: float = 0.0  # new_score - old_score
    old_score: Optional[float] = None
    new_score: Optional[float] = None
    old_severity: Optional[str] = None
    new_severity: Optional[str] = None
    severity_change: str = "none"  # "none", "improved", "degraded"
    resolved_issues: list = field(default_factory=list)
    new_issues: list = field(default_factory=list)
    old_flags: list = field(default_factory=list)
    new_flags: list = field(default_factory=list)


@dataclass
class RunDiffSummary:
    """Aggregate summary of run comparison."""
    # Run metadata
    old_timestamp: str = ""
    new_timestamp: str = ""
    old_total_urls: int = 0
    new_total_urls: int = 0
    
    # Score changes
    avg_overall_delta: float = 0.0
    avg_catalog_delta: float = 0.0
    avg_machine_delta: float = 0.0
    avg_commerce_delta: float = 0.0
    
    # URL status counts
    unchanged_count: int = 0
    improved_count: int = 0
    degraded_count: int = 0
    new_url_count: int = 0
    removed_url_count: int = 0
    
    # Issue counts
    old_critical_high_count: int = 0
    new_critical_high_count: int = 0
    critical_high_delta: int = 0
    
    old_no_price_count: int = 0
    new_no_price_count: int = 0
    no_price_delta: int = 0
    
    old_no_schema_count: int = 0
    new_no_schema_count: int = 0
    no_schema_delta: int = 0
    
    # Resolved vs new issues
    resolved_issues_count: int = 0
    new_issues_count: int = 0
    
    # Category changes (if available)
    category_changes: dict = field(default_factory=dict)


def _load_scored_csv(output_dir: str) -> Optional[pd.DataFrame]:
    """Loads products_scored.csv from an output directory."""
    path = os.path.join(output_dir, "products_scored.csv")
    if not os.path.isfile(path):
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def _load_run_summary(output_dir: str) -> dict:
    """Loads run_summary.json from an output directory."""
    path = os.path.join(output_dir, "run_summary.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _normalize_url(url: str) -> str:
    """Normalizes URL for matching between runs."""
    return normalize_url_for_comparison(url)


def _extract_flags(row: pd.Series) -> list[str]:
    """Extracts active flags from a scored row."""
    flags = []

    # Boolean flag columns
    flag_cols = [
        "flag_noindex",
        "flag_canonical_mismatch",
        "flag_fetch_error",
        "flag_non_200",
        "flag_js_rendered",
        "suspicious_price_missing",
        "suspicious_schema_missing",
        "suspicious_low_content",
        "flag_not_product_page",
    ]

    for col in flag_cols:
        if col in row.index:
            val = row.get(col, False)
            # Handle pandas/numpy bool types and integers
            if val is True or val == 1 or (isinstance(val, (bool, int)) and val):
                flags.append(col)

    # Parse indexability_flags string if present
    if "indexability_flags" in row.index:
        val = row.get("indexability_flags", "")
        if isinstance(val, str) and val.strip():
            for flag in val.split(","):
                flag = flag.strip()
                if flag and flag not in flags:
                    flags.append(flag)

    return flags


def _extract_issues(flags: list[str]) -> list[str]:
    """Extracts issue codes from flags (subset that are actual problems)."""
    issues = []
    for flag in flags:
        # Map flags to issue codes
        if flag == "flag_noindex" or flag == "noindex":
            issues.append("noindex")
        elif flag == "flag_canonical_mismatch" or flag == "canonical_mismatch":
            issues.append("canonical_mismatch")
        elif flag == "flag_fetch_error" or flag == "fetch_error":
            issues.append("fetch_error")
        elif flag == "flag_non_200" or flag.startswith("status_"):
            issues.append("non_200")
        elif flag == "flag_js_rendered":
            issues.append("js_rendered")
        elif flag == "suspicious_price_missing":
            issues.append("price_missing")
        elif flag == "suspicious_schema_missing":
            issues.append("schema_missing")
        elif flag == "suspicious_low_content":
            issues.append("low_content")
        elif flag == "flag_not_product_page":
            issues.append("not_product_page")
    return issues


def _severity_from_score_and_flags(score: float, flags: list[str]) -> str:
    """
    Infers severity from score and flags.
    Matches the logic in audit/shortlist.py ShortlistCandidate.
    """
    # CRITICAL: serious flags
    if any(f in flags for f in [
        "flag_fetch_error", "fetch_error",
        "flag_non_200", "non_200",
        "flag_not_product_page", "not_product_page"
    ]):
        return "CRITICAL"
    
    # HIGH: indexability blockers
    if any(f in flags for f in [
        "flag_noindex", "noindex",
        "flag_canonical_mismatch", "canonical_mismatch"
    ]):
        return "HIGH"
    
    # Check for critical missing data
    has_price_missing = any(f in flags for f in ["suspicious_price_missing", "price_missing"])
    has_schema_missing = any(f in flags for f in ["suspicious_schema_missing", "schema_missing"])
    
    if has_price_missing and has_schema_missing:
        return "HIGH"
    
    # MEDIUM: missing important data or JS rendering
    if (
        has_price_missing
        or has_schema_missing
        or any(f in flags for f in ["suspicious_low_content", "low_content", "flag_js_rendered", "js_rendered"])
    ):
        return "MEDIUM"
    
    # LOW: only low score
    if score < 40:
        return "LOW"
    
    return "NONE"


def _severity_change_direction(old_sev: str, new_sev: str) -> str:
    """Determines if severity improved, degraded, or unchanged."""
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "NONE": 4}
    
    old_rank = severity_order.get(old_sev, 4)
    new_rank = severity_order.get(new_sev, 4)
    
    if new_rank > old_rank:
        return "improved"
    elif new_rank < old_rank:
        return "degraded"
    return "none"


def compare_runs(
    old_output_dir: str,
    new_output_dir: str,
) -> tuple[RunDiffSummary, list[URLDiff]]:
    """
    Compares two audit run outputs.
    
    Args:
        old_output_dir: Path to the older run's output directory
        new_output_dir: Path to the newer run's output directory
    
    Returns:
        Tuple of (RunDiffSummary, list of URLDiff objects)
    """
    # Load data
    old_df = _load_scored_csv(old_output_dir)
    new_df = _load_scored_csv(new_output_dir)
    
    old_summary = _load_run_summary(old_output_dir)
    new_summary = _load_run_summary(new_output_dir)
    
    # Handle missing data
    if old_df is None and new_df is None:
        raise ValueError("Neither run has products_scored.csv")
    
    if old_df is None:
        # Treat as "new run only" - all URLs are new
        old_df = pd.DataFrame(columns=["url", "overall_score"])
    if new_df is None:
        # Treat as "old run only" - all URLs are removed
        new_df = pd.DataFrame(columns=["url", "overall_score"])
    
    # Create URL-indexed DataFrames with normalized URLs
    old_df = old_df.copy()
    new_df = new_df.copy()
    
    old_df["_norm_url"] = old_df["url"].apply(_normalize_url)
    new_df["_norm_url"] = new_df["url"].apply(_normalize_url)
    
    old_df = old_df.set_index("_norm_url")
    new_df = new_df.set_index("_norm_url")
    
    # Find URL sets
    old_urls = set(old_df.index)
    new_urls = set(new_df.index)
    
    common_urls = old_urls & new_urls
    new_only_urls = new_urls - old_urls
    old_only_urls = old_urls - new_urls
    
    # Initialize summary
    summary = RunDiffSummary(
        old_timestamp=old_summary.get("timestamp", ""),
        new_timestamp=new_summary.get("timestamp", ""),
        old_total_urls=old_summary.get("total_urls", len(old_df)),
        new_total_urls=new_summary.get("total_urls", len(new_df)),
    )
    
    url_diffs: list[URLDiff] = []
    
    # Process common URLs
    for norm_url in common_urls:
        old_row = old_df.loc[norm_url]
        new_row = new_df.loc[norm_url]
        
        old_score = float(old_row.get("overall_score", 0))
        new_score = float(new_row.get("overall_score", 0))
        score_delta = new_score - old_score
        
        old_flags = _extract_flags(old_row)
        new_flags = _extract_flags(new_row)
        
        old_issues = _extract_issues(old_flags)
        new_issues = _extract_issues(new_flags)
        
        resolved = [i for i in old_issues if i not in new_issues]
        new = [i for i in new_issues if i not in old_issues]
        
        old_sev = _severity_from_score_and_flags(old_score, old_flags)
        new_sev = _severity_from_score_and_flags(new_score, new_flags)
        
        sev_change = _severity_change_direction(old_sev, new_sev)
        
        # Determine status
        if score_delta > 0 and sev_change != "degraded":
            status = "improved"
        elif score_delta < 0 and sev_change != "improved":
            status = "degraded"
        elif sev_change == "improved":
            status = "improved"
        elif sev_change == "degraded":
            status = "degraded"
        else:
            status = "unchanged"
        
        diff = URLDiff(
            url=str(old_row.get("url", norm_url)),
            status=status,
            score_delta=round(score_delta, 1),
            old_score=round(old_score, 1),
            new_score=round(new_score, 1),
            old_severity=old_sev if old_sev != "NONE" else None,
            new_severity=new_sev if new_sev != "NONE" else None,
            severity_change=sev_change,
            resolved_issues=resolved,
            new_issues=new,
            old_flags=old_flags,
            new_flags=new_flags,
        )
        url_diffs.append(diff)
    
    # Process new URLs
    for norm_url in new_only_urls:
        new_row = new_df.loc[norm_url]
        new_score = float(new_row.get("overall_score", 0))
        new_flags = _extract_flags(new_row)
        new_sev = _severity_from_score_and_flags(new_score, new_flags)
        new_issues = _extract_issues(new_flags)
        
        diff = URLDiff(
            url=str(new_row.get("url", norm_url)),
            status="new",
            score_delta=0.0,
            new_score=round(new_score, 1),
            new_severity=new_sev if new_sev != "NONE" else None,
            new_issues=new_issues,
            new_flags=new_flags,
        )
        url_diffs.append(diff)
    
    # Process removed URLs
    for norm_url in old_only_urls:
        old_row = old_df.loc[norm_url]
        old_score = float(old_row.get("overall_score", 0))
        old_flags = _extract_flags(old_row)
        old_sev = _severity_from_score_and_flags(old_score, old_flags)
        old_issues = _extract_issues(old_flags)
        
        diff = URLDiff(
            url=str(old_row.get("url", norm_url)),
            status="removed",
            score_delta=0.0,
            old_score=round(old_score, 1),
            old_severity=old_sev if old_sev != "NONE" else None,
            resolved_issues=old_issues,
            old_flags=old_flags,
        )
        url_diffs.append(diff)
    
    # Compute aggregate statistics
    summary.unchanged_count = sum(1 for d in url_diffs if d.status == "unchanged")
    summary.improved_count = sum(1 for d in url_diffs if d.status == "improved")
    summary.degraded_count = sum(1 for d in url_diffs if d.status == "degraded")
    summary.new_url_count = len(new_only_urls)
    summary.removed_url_count = len(old_only_urls)
    
    # Score deltas
    if not old_df.empty and "overall_score" in old_df.columns:
        summary.avg_overall_delta = round(
            new_df["overall_score"].mean() - old_df["overall_score"].mean(),
            1
        ) if not new_df.empty else 0.0
    
    for score_col, delta_attr in [
        ("catalog_score", "avg_catalog_delta"),
        ("machine_score", "avg_machine_delta"),
        ("commerce_score", "avg_commerce_delta"),
    ]:
        if score_col in old_df.columns and score_col in new_df.columns:
            delta = new_df[score_col].mean() - old_df[score_col].mean()
            setattr(summary, delta_attr, round(delta, 1))
    
    # Critical/high counts
    def count_critical_high(df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        # Use severity from shortlist if available, otherwise infer
        if "severity" in df.columns:
            return int((df["severity"].isin(["CRITICAL", "HIGH"])).sum())
        # Fallback: infer from flags
        count = 0
        for _, row in df.iterrows():
            flags = _extract_flags(row)
            score = float(row.get("overall_score", 0))
            sev = _severity_from_score_and_flags(score, flags)
            if sev in ["CRITICAL", "HIGH"]:
                count += 1
        return count
    
    summary.old_critical_high_count = count_critical_high(old_df)
    summary.new_critical_high_count = count_critical_high(new_df)
    summary.critical_high_delta = summary.new_critical_high_count - summary.old_critical_high_count
    
    # Price/schema counts
    def count_no_price(df: pd.DataFrame) -> int:
        if df.empty or "suspicious_price_missing" not in df.columns:
            return 0
        return int(df["suspicious_price_missing"].sum())
    
    def count_no_schema(df: pd.DataFrame) -> int:
        if df.empty or "suspicious_schema_missing" not in df.columns:
            return 0
        return int(df["suspicious_schema_missing"].sum())
    
    summary.old_no_price_count = count_no_price(old_df)
    summary.new_no_price_count = count_no_price(new_df)
    summary.no_price_delta = summary.new_no_price_count - summary.old_no_price_count
    
    summary.old_no_schema_count = count_no_schema(old_df)
    summary.new_no_schema_count = count_no_schema(new_df)
    summary.no_schema_delta = summary.new_no_schema_count - summary.old_no_schema_count
    
    # Resolved vs new issues
    summary.resolved_issues_count = sum(len(d.resolved_issues) for d in url_diffs)
    summary.new_issues_count = sum(len(d.new_issues) for d in url_diffs)
    
    # Category changes
    summary.category_changes = _compare_categories(old_output_dir, new_output_dir)
    
    return summary, url_diffs


def _compare_categories(old_output_dir: str, new_output_dir: str) -> dict:
    """Compares category_summary.csv between runs."""
    old_cat = _load_category_summary(old_output_dir)
    new_cat = _load_category_summary(new_output_dir)
    
    if old_cat is None or new_cat is None:
        return {}
    
    changes = {}
    
    # Merge on category name
    merged = old_cat.merge(
        new_cat,
        on="category",
        how="outer",
        suffixes=("_old", "_new"),
        indicator=True,
    )
    
    score_col_new = "avg_overall_score_new" if "avg_overall_score_new" in merged.columns else None
    score_col_old = "avg_overall_score_old" if "avg_overall_score_old" in merged.columns else None
    
    if score_col_new is None or score_col_old is None:
        return {}
    
    for _, row in merged.iterrows():
        cat = row["category"]
        status = row["_merge"]
        
        old_score = row.get(score_col_old)
        new_score = row.get(score_col_new)
        
        if isinstance(old_score, (int, float)) and isinstance(new_score, (int, float)):
            delta = round(new_score - old_score, 1)
        else:
            delta = None
        
        if status == "both":
            if delta and delta != 0:
                changes[cat] = {
                    "status": "changed",
                    "old_score": old_score,
                    "new_score": new_score,
                    "delta": delta,
                }
        elif status == "left_only":
            changes[cat] = {
                "status": "removed",
                "old_score": old_score,
            }
        elif status == "right_only":
            changes[cat] = {
                "status": "new",
                "new_score": new_score,
            }
    
    return changes


def _load_category_summary(output_dir: str) -> Optional[pd.DataFrame]:
    """Loads category_summary.csv from an output directory."""
    path = os.path.join(output_dir, "category_summary.csv")
    if not os.path.isfile(path):
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def url_diffs_to_dataframe(url_diffs: list[URLDiff]) -> pd.DataFrame:
    """Converts list of URLDiff objects to DataFrame for CSV export."""
    records = []
    for d in url_diffs:
        records.append({
            "url": d.url,
            "status": d.status,
            "score_delta": d.score_delta,
            "old_score": d.old_score if d.old_score is not None else "",
            "new_score": d.new_score if d.new_score is not None else "",
            "old_severity": d.old_severity if d.old_severity else "",
            "new_severity": d.new_severity if d.new_severity else "",
            "severity_change": d.severity_change,
            "resolved_issues": "; ".join(d.resolved_issues) if d.resolved_issues else "",
            "new_issues": "; ".join(d.new_issues) if d.new_issues else "",
            "old_flags": "; ".join(d.old_flags) if d.old_flags else "",
            "new_flags": "; ".join(d.new_flags) if d.new_flags else "",
        })
    
    df = pd.DataFrame(records)
    
    # Sort by status priority
    status_order = {"degraded": 0, "new": 1, "improved": 2, "removed": 3, "unchanged": 4}
    if not df.empty:
        df["_sort_key"] = df["status"].map(status_order).fillna(5)
        df = df.sort_values(["_sort_key", "url"]).drop(columns=["_sort_key"])
    
    return df


def summary_to_dict(summary: RunDiffSummary) -> dict:
    """Converts RunDiffSummary to dictionary for JSON export."""
    return {
        "old_timestamp": summary.old_timestamp,
        "new_timestamp": summary.new_timestamp,
        "old_total_urls": summary.old_total_urls,
        "new_total_urls": summary.new_total_urls,
        "score_changes": {
            "avg_overall_delta": summary.avg_overall_delta,
            "avg_catalog_delta": summary.avg_catalog_delta,
            "avg_machine_delta": summary.avg_machine_delta,
            "avg_commerce_delta": summary.avg_commerce_delta,
        },
        "url_status_counts": {
            "unchanged": summary.unchanged_count,
            "improved": summary.improved_count,
            "degraded": summary.degraded_count,
            "new_urls": summary.new_url_count,
            "removed_urls": summary.removed_url_count,
        },
        "issue_counts": {
            "old_critical_high": summary.old_critical_high_count,
            "new_critical_high": summary.new_critical_high_count,
            "critical_high_delta": summary.critical_high_delta,
            "old_no_price": summary.old_no_price_count,
            "new_no_price": summary.new_no_price_count,
            "no_price_delta": summary.no_price_delta,
            "old_no_schema": summary.old_no_schema_count,
            "new_no_schema": summary.new_no_schema_count,
            "no_schema_delta": summary.no_schema_delta,
        },
        "issues_resolved_vs_new": {
            "resolved_count": summary.resolved_issues_count,
            "new_count": summary.new_issues_count,
        },
        "category_changes": summary.category_changes,
    }
