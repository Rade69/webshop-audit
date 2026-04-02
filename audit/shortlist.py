import pandas as pd

from audit.explainability import generate_top_explanations, generate_combined_explanation, is_sample_candidate
from audit.evidence import EvidenceSnapshot, build_evidence_for_reasons
from audit.issue_grouping import calculate_fix_impact_score
from config import SHORTLIST_TOP_N, BEST_SAMPLE_TOP_N

# Sample bucket tuning constants
SAMPLE_MAX_ABSOLUTE = 3
SAMPLE_MAX_RATIO_OF_ISSUES = 0.30
SAMPLE_DISABLE_ABOVE_ISSUES = 15


def _is_sample_candidate(candidate: "ShortlistCandidate") -> bool:
    """Return True if this candidate is a sample (good-score) rather than an actual issue."""
    return "sample-good-score" in candidate.reasons


def _compute_sample_limit(issue_count: int) -> int:
    """
    Compute how many sample candidates are allowed given the number of
    real-issue candidates.

    Rules:
    - Never more than SAMPLE_MAX_ABSOLUTE (3) sample candidates.
    - Never more than SAMPLE_MAX_RATIO_OF_ISSUES (30%) of the issue count.
    - If issue_count >= SAMPLE_DISABLE_ABOVE_ISSUES (15), sample bucket is
      disabled entirely (return 0).
    """
    if issue_count == 0:
        return 0
    if issue_count >= SAMPLE_DISABLE_ABOVE_ISSUES:
        return 0
    ratio_limit = max(1, int(issue_count * SAMPLE_MAX_RATIO_OF_ISSUES))
    return min(SAMPLE_MAX_ABSOLUTE, ratio_limit)


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

        # Store row for explanation and evidence generation
        self._row = row

        # Calculate severity and reasons
        self.severity = self._calculate_severity()
        self.reasons = self._calculate_reasons()
        self.severity_score = self._calculate_severity_score()
        self.explanation = self._generate_explanation()
        self.is_sample = is_sample_candidate(self.reasons)
        self.evidence = self._generate_evidence()
        self.fix_impact = self._calculate_fix_impact()

    def _generate_explanation(self) -> str:
        """Generate human-readable explanation for this candidate."""
        return generate_combined_explanation(self.reasons, self._row)

    def _generate_evidence(self) -> dict:
        """Generate evidence snapshot for this candidate."""
        evidence = EvidenceSnapshot.from_row(self._row)
        return build_evidence_for_reasons(evidence, self.reasons)

    def _calculate_fix_impact(self) -> dict:
        """Calculate fix impact score for this candidate's issues."""
        return calculate_fix_impact_score(self.reasons)

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
        if (
            self.suspicious_price_missing
            or self.suspicious_schema_missing
            or self.suspicious_low_content
            or self.flag_js_rendered
        ):
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

        # LOW priority - ALWAYS include at least one reason
        if self.severity == "LOW":
            if self.overall_score < 40:
                reasons.append("low-score")  # Actual problem
            else:
                reasons.append("sample-good-score")  # Benchmark sample

        return reasons

    def _calculate_severity_score(self) -> int:
        """Calculate numeric score for sorting (lower = higher priority)."""
        severity_weights = {"CRITICAL": 0, "HIGH": 10, "MEDIUM": 20, "LOW": 30}

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
            "explanation": self.explanation,
            "is_sample": self.is_sample,
            "evidence_summary": self._get_evidence_summary(),
            "fix_impact": self.fix_impact["primary_impact"],
            "impact_score": self.fix_impact["impact_score"],
            "is_likely_product_page": self.is_likely_product_page,
            "is_likely_js_rendered": self.is_likely_js_rendered,
            "severity_score": self.severity_score,
        }

    def _get_evidence_summary(self) -> str:
        """Get a short evidence summary string for CSV export."""
        parts = []
        
        # Price evidence
        if self._row.get("html_price_text"):
            parts.append(f"HTML cijena: {self._row.get('html_price_text')}")
        else:
            parts.append("HTML cijena: nije pronađena")
        
        if self._row.get("schema_price"):
            parts.append(f"Schema cijena: {self._row.get('schema_price')}")
        else:
            parts.append("Schema cijena: nije pronađena")
        
        # Schema evidence
        if self._row.get("schema_product_present"):
            parts.append("Product schema: ✓")
        else:
            parts.append("Product schema: ✗")
        
        # Indexability
        if self._row.get("robots_meta"):
            parts.append(f"Robots: {self._row.get('robots_meta')}")
        
        if self._row.get("canonical"):
            parts.append(f"Canonical: {self._row.get('canonical')[:50]}..." if len(str(self._row.get("canonical", ""))) > 50 else f"Canonical: {self._row.get('canonical')}")
        
        return " | ".join(parts)


def select_manual_review_candidates(
    df: pd.DataFrame,
    max_candidates: int = SHORTLIST_TOP_N,
    severity_limits: dict | None = None,
) -> pd.DataFrame:
    """
    Returns a subset of products that need manual review with severity-based selection.

    Selection logic:
    1. Always include CRITICAL severity candidates
    2. Include HIGH severity candidates up to limit
    3. Include MEDIUM severity candidates up to limit
    4. Sample (LOW with good score) candidates are limited dynamically:
       - Never more than SAMPLE_MAX_ABSOLUTE (3)
       - Never more than SAMPLE_MAX_RATIO_OF_ISSUES (30%) of real issues
       - Disabled entirely if real issues >= SAMPLE_DISABLE_ABOVE_ISSUES (15)
    5. Sort by severity score (priority) and overall score

    Args:
        df: Scored DataFrame
        max_candidates: Maximum number of candidates to return
        severity_limits: Optional dict with limits per severity level
            Example: {"CRITICAL": None, "HIGH": 15, "MEDIUM": 20, "LOW": 5}
            Note: LOW limit is overridden by sample bucket tuning.
    """
    if df.empty:
        return pd.DataFrame()

    # Default severity limits if not provided
    if severity_limits is None:
        severity_limits = {"CRITICAL": None, "HIGH": 20, "MEDIUM": 15, "LOW": 5}

    # Process all rows into candidates
    candidates: list[ShortlistCandidate] = []
    for _, row in df.iterrows():
        candidate = ShortlistCandidate(row)
        candidates.append(candidate)

    # Sort by severity score (priority)
    candidates.sort(key=lambda x: x.severity_score)

    # First pass: count how many real-issue candidates we have
    # (everything that is NOT a sample-good-score candidate)
    issue_candidates = [c for c in candidates if not _is_sample_candidate(c)]
    sample_candidates = [c for c in candidates if _is_sample_candidate(c)]

    # Compute dynamic sample limit based on real issue count
    sample_limit = _compute_sample_limit(len(issue_candidates))

    # Select issue candidates first (respecting their severity limits)
    selected: list[ShortlistCandidate] = []
    severity_counts: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for candidate in issue_candidates:
        severity = candidate.severity
        limit = severity_limits.get(severity)

        if limit is None or severity_counts[severity] < limit:
            selected.append(candidate)
            severity_counts[severity] += 1

        if len(selected) >= max_candidates:
            break

    # Then add sample candidates up to the dynamic limit
    if sample_limit > 0 and len(selected) < max_candidates:
        samples_added = 0
        for candidate in sample_candidates:
            if samples_added >= sample_limit:
                break
            if len(selected) >= max_candidates:
                break
            selected.append(candidate)
            samples_added += 1

    # Convert to DataFrame
    if not selected:
        return pd.DataFrame()

    result_dicts = [c.to_dict() for c in selected]
    result_df = pd.DataFrame(result_dicts)

    # Add original columns for context
    original_cols = [
        "title",
        "h1",
        "breadcrumb_text",
        "schema_product_present",
        "schema_price",
        "html_price_text",
        "visible_text_length",
        "catalog_score",
        "machine_score",
        "commerce_score",
    ]

    for col in original_cols:
        if col in df.columns:
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
    # Handle NaN values in indexability_flags
    if "indexability_flags" in df.columns:
        flags_series = df["indexability_flags"].fillna("")
        no_flags = df[flags_series.str.len() == 0]
    else:
        no_flags = df.copy()

    if "agent_ready" in df.columns:
        # Prefer agent-ready products, then others with no flags
        best = pd.concat(
            [
                agent_ready if len(agent_ready) < top_n else agent_ready.head(top_n),
                no_flags[~no_flags.index.isin(agent_ready.index)]
                if len(agent_ready) < top_n
                else pd.DataFrame(),
            ]
        ).sort_values("overall_score", ascending=False)
    else:
        best = no_flags.sort_values("overall_score", ascending=False)

    return best.head(top_n)
