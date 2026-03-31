import re
import requests
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import urljoin, urlparse

from config import DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, PRODUCT_URL_PATTERNS, PRODUCT_URL_EXCLUSIONS


SITEMAP_CANDIDATES = [
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap/sitemap.xml",
    "/sitemaps/sitemap.xml",
]


def discover_sitemap_urls(base_url: str) -> list[str]:
    """Builds a list of candidate sitemap URLs from a domain."""
    parsed = urlparse(base_url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    candidates = [urljoin(root, path) for path in SITEMAP_CANDIDATES]

    # Also try robots.txt — it often lists the sitemap explicitly
    try:
        resp = requests.get(
            urljoin(root, "/robots.txt"),
            timeout=10,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        if resp.status_code == 200:
            for line in resp.text.splitlines():
                if line.strip().lower().startswith("sitemap:"):
                    sitemap_url = line.split(":", 1)[1].strip()
                    if sitemap_url not in candidates:
                        candidates.insert(0, sitemap_url)
    except Exception:
        pass

    return candidates


def fetch_sitemap(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    """Downloads sitemap XML content. Returns raw text or None on failure."""
    try:
        resp = requests.get(
            url, timeout=timeout, headers={"User-Agent": DEFAULT_USER_AGENT}
        )
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


def parse_sitemap(xml_text: str) -> dict:
    """
    Parses sitemap XML.
    Returns {'urls': [...], 'child_sitemaps': [...]}.
    Handles both <urlset> and <sitemapindex>.
    Namespace is stripped from tags for robustness.
    """
    urls: list[str] = []
    child_sitemaps: list[str] = []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {"urls": urls, "child_sitemaps": child_sitemaps}

    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag

    if tag == "sitemapindex":
        for el in root.iter():
            el_tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
            if el_tag == "loc" and el.text:
                child_sitemaps.append(el.text.strip())
    else:
        for el in root.iter():
            el_tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
            if el_tag == "loc" and el.text:
                urls.append(el.text.strip())

    return {"urls": urls, "child_sitemaps": child_sitemaps}


def collect_urls_from_sitemap(
    start_sitemap_url: str,
    max_urls: Optional[int] = None,
    _visited: Optional[set] = None,
) -> list[str]:
    """
    Recursively walks sitemap/sitemapindex and collects all URLs.
    Deduplicates URLs. max_urls limit is applied only AFTER all child
    sitemaps are fully traversed — this ensures that category sitemaps
    listed before product sitemaps cannot crowd out product URLs.
    """
    if _visited is None:
        _visited = set()

    if start_sitemap_url in _visited:
        return []
    _visited.add(start_sitemap_url)

    collected: list[str] = []
    seen_urls: set[str] = set()

    xml_text = fetch_sitemap(start_sitemap_url)
    if not xml_text:
        return collected

    result = parse_sitemap(xml_text)

    for url in result["urls"]:
        if url not in seen_urls:
            seen_urls.add(url)
            collected.append(url)

    # Recurse into children WITHOUT passing max_urls — collect everything first.
    # The limit is applied at the very end so no child sitemap is skipped early.
    for child_url in result["child_sitemaps"]:
        child_results = collect_urls_from_sitemap(child_url, None, _visited)
        for url in child_results:
            if url not in seen_urls:
                seen_urls.add(url)
                collected.append(url)

    if max_urls:
        collected = collected[:max_urls]

    return collected


def filter_product_like_urls(urls: list[str]) -> tuple[list[str], bool]:
    """
    Heuristically keeps URLs that look like product pages.

    Returns:
        (filtered_urls, used_fallback)

    used_fallback=True means no patterns matched and ALL urls were returned.
    Caller should warn the user when fallback is used.
    """
    # Numeric product-ID pattern common in Balkan/EU shops:
    # e.g. /majica/53211619-brooklyn-essentials  →  /{word}/{6+digits}-{slug}
    _numeric_id_re = re.compile(r'/\d{5,}-[a-z]')

    def is_product_like(url: str) -> bool:
        lower = url.lower()
        for excl in PRODUCT_URL_EXCLUSIONS:
            if excl in lower:
                return False
        for pattern in PRODUCT_URL_PATTERNS:
            if pattern in lower:
                return True
        # Detect numeric product IDs (checked last, after exclusions pass)
        if _numeric_id_re.search(lower):
            return True
        return False

    filtered = [u for u in urls if is_product_like(u)]

    if not filtered:
        # Fallback: return all URLs, but signal that heuristics found nothing
        return urls, True

    return filtered, False
