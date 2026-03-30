import re
from typing import Optional
from urllib.parse import urlparse, urlunparse, urljoin, parse_qs, urlencode


def normalize_whitespace(value: Optional[str]) -> Optional[str]:
    """Cleans multiple spaces and newline characters."""
    if value is None:
        return None
    return re.sub(r"\s+", " ", value).strip() or None


def safe_get_text(node) -> Optional[str]:
    """Safely reads text from a BeautifulSoup element."""
    if node is None:
        return None
    return normalize_whitespace(node.get_text())


def is_noindex(robots_meta) -> bool:
    """Checks if robots meta contains 'noindex'. Handles None and pandas NaN."""
    if not isinstance(robots_meta, str):
        return False
    return "noindex" in robots_meta.lower()


def safe_len(value: Optional[str]) -> int:
    """Returns string length or 0 if None/empty."""
    if not value:
        return 0
    return len(value)


def score_description_quality(
    description_word_count: int,
    has_feature_list: bool,
    has_spec_table: bool
) -> int:
    """
    Scores description quality for AI agent usability (0-100).
    
    Scoring rules:
    - word_count < 30: 0 points (too short for AI to use)
    - word_count 30-80: 40 points (minimal content)
    - word_count 81-150: 60 points (adequate content)
    - word_count 151-300: 80 points (good content)
    - word_count > 300: 90 points (excellent content)
    - +10 bonus if has_feature_list or has_spec_table (max 100)
    """
    if description_word_count < 30:
        score = 0
    elif description_word_count <= 80:
        score = 40
    elif description_word_count <= 150:
        score = 60
    elif description_word_count <= 300:
        score = 80
    else:
        score = 90
    
    # Add bonus for structured content (feature list or spec table)
    if has_feature_list or has_spec_table:
        score += 10
    
    # Cap at 100
    return min(score, 100)


# Tracking parameters that should be stripped before URL comparison.
_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_source_platform", "utm_creative_format", "utm_marketing_tactic",
    "fbclid", "gclid", "msclkid", "ttclid", "twclid",
    "_ga", "_gl", "mc_cid", "mc_eid",
    "ref", "source", "affiliate",
})


def normalize_url_for_comparison(url: str, base_url: Optional[str] = None) -> str:
    """
    Normalizes a URL for reliable comparison.

    Handles:
    - Relative URLs (resolved against base_url)
    - http vs https (normalized to https)
    - www vs non-www (www removed)
    - Trailing slashes (stripped)
    - Tracking parameters (utm_*, fbclid, gclid, etc. — removed)

    Returns empty string on any failure.
    """
    if not isinstance(url, str) or not url.strip():
        return ""

    url = url.strip()

    # Resolve relative URL against base_url
    if base_url and not url.startswith(("http://", "https://")):
        try:
            url = urljoin(base_url, url)
        except Exception:
            return ""

    try:
        parsed = urlparse(url)

        # Normalize scheme to https
        scheme = "https"

        # Normalize netloc: lowercase + strip www
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Strip tracking parameters
        if parsed.query:
            params = parse_qs(parsed.query, keep_blank_values=True)
            filtered = {
                k: v for k, v in params.items()
                if k.lower() not in _TRACKING_PARAMS
                and not k.lower().startswith("utm_")
            }
            query = urlencode(filtered, doseq=True)
        else:
            query = ""

        # Strip trailing slash (but keep root "/")
        path = parsed.path.rstrip("/") or "/"

        return urlunparse((scheme, netloc, path, "", query, ""))
    except Exception:
        return url.rstrip("/")
