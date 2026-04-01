import pandas as pd

from config import SHORTLIST_TOP_N, BEST_SAMPLE_TOP_N, MIN_VISIBLE_TEXT_LENGTH


class ShortlistCandidate:
    """Represents a candidate for manual review with severity and reasons."""
    
    def __init__(self, row: pd.Series):
        self.url = row.get("url", "")
        self.overall_score = row.get("overall_score", 0)
        self.is_likely_product_page = row.get("is_likely_product_page", False)
        self.is_likely_js_rendered = row.get("is_likely_js_rendered", False)
        self.js_render_confidence = row.get("js_render_confidence", "none")
        
        # Flags
        self.flag_noindex = row.get("flag_noindex", False)
        self.flag_canonical_mismatch = row.get("flag_canonical_mismatch", False)
        self.flag_fetch_error = row.get("flag_fetch_error", False)
        self.flag_non_200 = row.get("flag_non_200", False)
        self.flag_js_rendered = row.get("flag_js_rendered", False)
        
        # Suspicious flags
        self.suspicious_price_missing = row.get("suspicious_price_missing", False)
        self.suspicious_schema_missing = row.get("suspicious_schema_missing", False)
        self.suspicious_low_content = row.get("suspicious_low_content", False)
        self.flag_not_product_page = row.get("flag_not_product_page", False)
        
        # Calculate severity and reasons
        self.severity = self._calculate_severity()
        self.reasons = self._calculate_reasons()
        self.severity_score = self._calculate_severity_score()
    
    def _calculate_severity(self) -> str:
        """Calculate severity level: CRITICAL, HIGH, MEDIUM, LOW."""
        # CRITICAL: page cannot be processed or is definitely not a product page
        if self.flag_fetch_error or self.flag_non_200 or self.flag_not_product_page:
            return "CRITICAL"
        
        # HIGH: serious issues that block indexing or critical data missing
        if self.flag_noindex or self.flag_canonical_mismatch:
            return "HIGH"
        
        # Check for critical missing data on likely product pages
        if self.is_likely_product_page:
            if self.suspicious_price_missing and self.suspicious_schema_missing:
                return "HIGH"
        
        # MEDIUM: missing important data or JS rendering issues
        if (self.suspicious_price_missing or self.suspicious_schema_missing or 
            self.suspicious_low_content or self.flag_js_rendered):
            return "MEDIUM"
        
        # LOW: only low score or minor issues
        return "LOW"
    
    def _calculate_reasons(self) -> list[str]:
        """Calculate machine-readable reason codes."""
        reasons = []
        
        # Critical reasons
        if self.flag_fetch_error:
            reasons.append("fetch-error")
        if self.flag_non_200:
            reasons.append("non-200")
        if self.flag_not_product_page:
            reasons.append("not-product-page")
        
        # High priority reasons
        if self.flag_noindex:
            reasons.append("noindex")
        if self.flag_canonical_mismatch:
            reasons.append("canonical-mismatch")
        
        # Check for critical missing data on product pages
        if self.is_likely_product_page:
            if self.suspicious_price_missing and self.suspicious_schema_missing:
                reasons.append("missing-price-critical")
                reasons.append("missing-schema-critical")
        
        # Medium priority reasons
        if self.suspicious_price_missing and "missing-price-critical" not in reasons:
            reasons.append("missing-price")
        if self.suspicious_schema_missing and "missing-schema-critical" not in reasons:
            reasons.append("missing-schema")
        if self.suspicious_low_content:
            reasons.append("low-content")
        
        # JS rendering reasons with confidence level
        if self.flag_js_rendered:
            if self.js_render_confidence in ["high", "medium"]:
                reasons.append(f"js-rendered-{self.js_render_confidence}")
            else:
                reasons.append("js-rendered")
        
        # Low priority - only if no other reasons
        if not reasons and self.overall_score < 40:
            reasons.append("low-score")
        
        return reasons
    
    def _calculate_severity_score(self) -> int:
        """Calculate numeric score for sorting (lower = higher priority)."""
        severity_weights = {
            "CRITICAL": 0,
            "HIGH": 10,
            "MEDIUM": 20,
            "LOW": 30
        }
        
        base_score = severity_weights.get(self.severity, 30)
        
        # Adjust by overall score for same severity level
        # Lower overall score = higher priority within same severity
        score_adjustment = max(0, 100 - self.overall_score) / 100
        
        return base_score + score_adjustment
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DataFrame."""
        return {
            "url": self.url,
            "overall_score": self.overall_score,
            "severity": self.severity,
            "reasons": ", ".join(self.reasons) if self.reasons else "",
            "reason_count": len(self.reasons),
            "is_likely_product_page": self.is_likely_product_page,
            "is_likely_js_rendered": self.is_likely_js_rendered,
            "severity_score": self.severity_score,
        }


def select_manual_review_candidates(
    df: pd.DataFrame, 
    max_candidates: int = SHORTLIST_TOP_N,
    severity_limits: dict = None
) -> pd.DataFrame:
    """
    Returns a subset of products that need manual review with severity-based selection.
    
    New selection logic:
    1. Always include CRITICAL severity candidates
    2. Include HIGH severity candidates up to limit
    3. Include MEDIUM severity candidates up to limit
    4. Optionally include some LOW severity for sample
    5. Sort by severity score (priority) and overall score
    
    Args:
        df: Scored DataFrame
        max_candidates: Maximum number of candidates to return
        severity_limits: Optional dict with limits per severity level
            Example: {"CRITICAL": None, "HIGH": 15, "MEDIUM": 20, "LOW": 5}
    """
    if df.empty:
        return pd.DataFrame()
    
    # Default severity limits if not provided
    if severity_limits is None:
        severity_limits = {
            "CRITICAL": None,  # No limit for critical
            "HIGH": 20,
            "MEDIUM": 15,
            "LOW": 5
        }
    
    # Filter to likely product pages for non-critical issues
    if "is_likely_product_page" in df.columns:
        product_df = df[df["is_likely_product_page"].astype(bool)].copy()
    else:
        product_df = df.copy()
    
    # Process all rows into candidates
    candidates = []
    for _, row in df.iterrows():
        candidate = ShortlistCandidate(row)
        candidates.append(candidate)
    
    # Sort by severity score (priority)
    candidates.sort(key=lambda x: x.severity_score)
    
    # Select candidates by severity with limits
    selected = []
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    
    for candidate in candidates:
        severity = candidate.severity
        limit = severity_limits.get(severity)
        
        # Check if we should include this candidate
        if limit is None or severity_counts[severity] < limit:
            selected.append(candidate)
            severity_counts[severity] += 1
        
        # Stop if we reached max candidates
        if len(selected) >= max_candidates:
            break
    
    # Convert to DataFrame
    if not selected:
        return pd.DataFrame()
    
    result_dicts = [c.to_dict() for c in selected]
    result_df = pd.DataFrame(result_dicts)
    
    # Add original columns for context
    original_cols = ["title", "h1", "breadcrumb_text", "schema_product_present", 
                     "schema_price", "html_price_text", "visible_text_length",
                     "catalog_score", "machine_score", "commerce_score"]
    
    for col in original_cols:
        if col in df.columns:
            # Create mapping from url to column value
            url_to_value = df.set_index("url")[col].to_dict()
            result_df[col] = result_df["url"].map(url_to_value)
    
    return result_df


def select_best_products_sample(
    df: pd.DataFrame, top_n: int = BEST_SAMPLE_TOP_N
) -> pd.DataFrame:
    """
    Returns a sample of highest-scoring products for comparison.
    
    Prioritizes agent_ready products first (products that are ready for
    AI recommendation), then fills with the best-scoring non-indexability-
    flagged products.
    """
    if df.empty:
        return df

    # Start with agent-ready products (no JS, has price, has schema, score >= 65)
    if "agent_ready" in df.columns:
        agent_ready = df[df["agent_ready"]].copy()
        if len(agent_ready) >= top_n:
            return agent_ready.sort_values("overall_score", ascending=False).head(top_n)
    
    # Combine: agent-ready + non-flagged products
    no_flags = df[df["indexability_flags"].str.len() == 0]
    
    if "agent_ready" in df.columns:
        # Prefer agent-ready products, then others with no flags
        best = pd.concat([
            agent_ready if len(agent_ready) < top_n else agent_ready.head(top_n),
            no_flags[~no_flags.index.isin(agent_ready.index)] if len(agent_ready) < top_n else pd.DataFrame()
        ]).sort_values("overall_score", ascending=False)
    else:
        best = no_flags.sort_values("overall_score", ascending=False)
    
    return best.head(top_n)
