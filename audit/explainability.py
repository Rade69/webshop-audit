"""
Explainability module — human-readable explanations for audit findings.

This module provides deterministic, short explanations for why a page
has issues. Explanations are based on actual data signals, not LLM-generated.

Design principles:
- Explanations must be deterministic
- Must use real data from the row
- Must not invent causes
- Must be short (1-2 sentences)
- Single source-of-truth for explanation mapping
"""
from typing import Optional


# Explanation templates organized by reason code
# Each template can have optional data placeholders like {field_name}
EXPLANATION_TEMPLATES = {
    # Critical issues
    "fetch-error": "Stranica se ne može preuzeti — HTTP zahtjev nije uspio ({fetch_error}).",
    "non-200": "Stranica vraća status kod {status_code} umjesto 200 OK.",
    "not-product-page": "Stranica ne liči na produktnu — vjerovatno kategorija, blog ili druga sadržajna stranica.",
    
    # High priority issues
    "noindex": "Stranica ima noindex u robots meta tagu — tražilice je neće indeksirati.",
    "canonical-mismatch": "Canonical URL ({canonical}) pokazuje na drugu stranicu — ova stranica možda nije glavna verzija.",
    
    # Missing data (critical when on product pages)
    "missing-price-critical": "Stranica nema vidljivu cijenu ni u HTML-u ni u structured data — izgleda kao nekupovna.",
    "missing-schema-critical": "Stranica nema Product schema — AI agenti ne mogu programski pročitati podatke o proizvodu.",
    
    # Missing data (medium priority)
    "missing-price": "HTML nema jasan signal cijene — kupci možda ne vide cijenu odmah.",
    "missing-schema": "Nema JSON-LD structured data — AI agenti i tražilice teže razumiju proizvod.",
    
    # Content issues
    "low-content": "Stranica ima malo vidljivog teksta ({visible_text_length} znakova) — premalo za kvalitetnu preporuku.",
    
    # JS rendering
    "js-rendered-high": "Stranica se renderira putem JavaScripta (visok rizik) — sadržaj možda nije dostupan crawlerima.",
    "js-rendered-medium": "Stranica koristi JavaScript renderiranje (srednji rizik) — provjeriti da li je sadržaj dostupan bez JS.",
    "js-rendered": "Stranica koristi JavaScript — sadržaj možda nije dostupan svim crawlerima.",
    
    # Low priority
    "low-score": "Ukupna ocjena stranice je niska ({overall_score}/100) — nedostaje više elemenata kvalitete.",
    "sample-good-score": "Stranica ima dobru ocjenu ({overall_score}/100) — uključena kao uzorak za poređenje.",
}


# Priority order for selecting top explanations (lower = higher priority)
EXPLANATION_PRIORITY = [
    # Critical
    "fetch-error",
    "non-200",
    "not-product-page",
    # High
    "noindex",
    "canonical-mismatch",
    "missing-price-critical",
    "missing-schema-critical",
    # Medium
    "missing-price",
    "missing-schema",
    "low-content",
    "js-rendered-high",
    "js-rendered-medium",
    "js-rendered",
    # Low
    "low-score",
    "sample-good-score",
]


def _get_row_value(row: dict, key: str, default: str = "") -> str:
    """Safely get a value from row, handling None/NaN."""
    val = row.get(key, default)
    if val is None:
        return default
    return str(val)


def generate_explanation(reason_code: str, row: dict) -> str:
    """
    Generate a human-readable explanation for a single reason code.
    
    Args:
        reason_code: The reason code (e.g., "missing-price", "noindex")
        row: The data row with actual values
    
    Returns:
        Human-readable explanation string
    """
    template = EXPLANATION_TEMPLATES.get(reason_code)
    if not template:
        # Fallback: return the reason code itself
        return reason_code.replace("-", " ").capitalize()
    
    # Fill in template placeholders with actual data
    explanation = template
    
    # Common placeholders
    placeholders = {
        "fetch_error": _get_row_value(row, "fetch_error", "nepoznata greška"),
        "status_code": _get_row_value(row, "status_code", "nepoznat"),
        "canonical": _get_row_value(row, "canonical", "nepoznat URL"),
        "visible_text_length": _get_row_value(row, "visible_text_length", "0"),
        "overall_score": _get_row_value(row, "overall_score", "0"),
    }
    
    for key, value in placeholders.items():
        explanation = explanation.replace(f"{{{key}}}", value)
    
    return explanation


def generate_top_explanations(reasons: list[str], row: dict, max_explanations: int = 3) -> list[str]:
    """
    Generate top explanations for a list of reason codes.
    
    Args:
        reasons: List of reason codes
        row: The data row with actual values
        max_explanations: Maximum number of explanations to return
    
    Returns:
        List of human-readable explanations, sorted by priority
    """
    if not reasons:
        return []
    
    # Sort reasons by priority
    def get_priority(reason: str) -> int:
        try:
            return EXPLANATION_PRIORITY.index(reason)
        except ValueError:
            return len(EXPLANATION_PRIORITY)  # Unknown reasons go last
    
    sorted_reasons = sorted(reasons, key=get_priority)
    
    # Generate explanations for top reasons
    explanations = []
    for reason in sorted_reasons[:max_explanations]:
        explanation = generate_explanation(reason, row)
        explanations.append(explanation)
    
    return explanations


def generate_combined_explanation(reasons: list[str], row: dict) -> str:
    """
    Generate a single combined explanation for multiple issues.
    
    This creates a concise summary that mentions the most important issues
    without being too verbose.
    
    Args:
        reasons: List of reason codes
        row: The data row with actual values
    
    Returns:
        Single combined explanation string
    """
    if not reasons:
        return "Stranica nema detektovanih problema."
    
    # Get top 2 explanations
    top_explanations = generate_top_explanations(reasons, row, max_explanations=2)
    
    if len(top_explanations) == 1:
        return top_explanations[0]
    
    # Combine top 2 with semicolon
    return f"{top_explanations[0]} {top_explanations[1]}"


def is_sample_candidate(reasons: list[str]) -> bool:
    """
    Check if a candidate is a sample (good score) rather than a real issue.
    
    Args:
        reasons: List of reason codes
    
    Returns:
        True if this is a sample candidate
    """
    return "sample-good-score" in reasons


def get_primary_issue_reason(reasons: list[str]) -> Optional[str]:
    """
    Get the primary (most important) issue reason.
    
    Args:
        reasons: List of reason codes
    
    Returns:
        Primary reason code or None if no real issues
    """
    if not reasons:
        return None
    
    # Filter out sample-good-score
    issue_reasons = [r for r in reasons if r != "sample-good-score"]
    
    if not issue_reasons:
        return None
    
    # Return highest priority reason
    def get_priority(reason: str) -> int:
        try:
            return EXPLANATION_PRIORITY.index(reason)
        except ValueError:
            return len(EXPLANATION_PRIORITY)
    
    return min(issue_reasons, key=get_priority)
