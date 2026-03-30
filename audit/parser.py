import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from audit.utils import normalize_whitespace, safe_get_text

# Keywords for shipping/returns detection (multilingual basics)
SHIPPING_KEYWORDS = [
    # English
    "shipping", "delivery", "ship", "deliver", "free shipping", 
    "express shipping", "overnight", "standard shipping",
    
    # Bosnian/Croatian/Serbian
    "dostava", "isporuka", "besplatna dostava", "brza dostava",
    "ekspres dostava", "dostava na kućnu adresu",
    
    # German
    "versand", "lieferung", "kostenloser versand", "expressversand",
    
    # French
    "livraison", "expédition", "livraison gratuite", "livraison express",
    
    # Spanish
    "envío", "entrega", "envío gratuito", "entrega rápida",
    
    # Italian
    "spedizione", "consegna", "spedizione gratuita", "consegna rapida",
]

RETURNS_KEYWORDS = [
    # English
    "return policy", "refund policy", "returns", "refund", 
    "money back", "30 day return", "easy return", "free return",
    
    # Bosnian/Croatian/Serbian
    "povrat robe", "povrat novca", "zamjena robe", "reklamacija",
    "30 dana povrat", "garancija povrata",
    
    # German
    "rückgabe", "rückgaberecht", "widerruf", "garantie",
    
    # French
    "politique de retour", "retour", "remboursement", "garantie",
    
    # Spanish
    "política de devolución", "devolución", "reembolso", "garantía",
    
    # Italian
    "politica di reso", "reso", "rimborso", "garanzia",
]

# Price validation regex — validates price strings with currency
# Accepts: digits, optional decimal separator, optional currency symbol/code
# Handles both "45.99 EUR" and "€ 45.99" formats
# Max length: 30 characters
PRICE_VALIDATION_RE = re.compile(
    r"^(?:[\$\€\£]?\s*)?[\d.,]+(?:\s*[\$\€\£])?(?:\s*(?:KM|BAM|EUR|USD|GBP|HRK|RSD|CHF|PLN|CZK|HUF|RON|CAD|AUD|JPY))?$",
    re.IGNORECASE
)

# Price extraction regex — extracts price value for parsing to float
PRICE_EXTRACTION_RE = re.compile(
    r"""
    (?:[\$\€\£\¥\₽\₹\元]?\s*)?         # Optional currency symbols
    (?:                              # Price amount
        \d{1,3}(?:[.,]\d{3})*        # Thousands with separator: 1,234 or 1.234
        |
        \d{1,6}                      # Simple number: 1234
    )
    (?:                              # Decimal part
        [.,]                         # Decimal separator
        \d{1,2}                      # 1-2 decimal digits
    )?
    (?:\s*(?:KM|BAM|EUR|USD|GBP|HRK|RSD|CAD|AUD|JPY|CHF|PLN|CZK|HUF|RON))?
    $                               # Must match to end
    """,
    re.IGNORECASE | re.VERBOSE
)

# Selectors targeting HTML elements that explicitly carry price data.
# Order matters — more specific first.
PRICE_SELECTORS = [
    # Schema.org microdata (highest priority)
    {"itemprop": "price"},
    # meta tag with price (common in structured themes)
    {"itemprop": "price", "content": True},
    # Data attributes
    {"data-price": True},
    {"data-product-price": True},
    {"data-sale-price": True},
    # WooCommerce standard
    {"class": re.compile(r"woocommerce-Price-amount", re.I)},
    # WooCommerce .amount class
    {"class": re.compile(r"\bamount\b", re.I)},
    # Price type classes
    {"class": re.compile(r"\bproduct-price\b", re.I)},
    {"class": re.compile(r"\bsale-price\b", re.I)},
    {"class": re.compile(r"\bregular-price\b", re.I)},
    # Generic price class (catch-all)
    {"class": re.compile(r"\bprice\b", re.I)},
    # Multi-platform price classes
    {"class": re.compile(r"ProductPrice", re.I)},
    {"class": re.compile(r"product_price", re.I)},
    # Localized price classes
    {"class": re.compile(r"\bcijena\b", re.I)},
    {"class": re.compile(r"\bpreis\b", re.I)},
    {"class": re.compile(r"\bprix\b", re.I)},
    {"class": re.compile(r"\bprecio\b", re.I)},
    {"class": re.compile(r"\bprezzo\b", re.I)},
    # ID selectors
    {"id": re.compile(r"price", re.I)},
    {"id": re.compile(r"cijena", re.I)},
]

# Selectors for product content areas (shipping/returns search scope)
PRODUCT_AREA_SELECTORS = [
    "main",
    "article",
    "[class*='product-detail']",
    "[class*='product-info']",
    "[class*='product-description']",
    "[class*='product-content']",
    "#product",
    "#content",
    ".product",
    ".product-page",
    ".product-details",
]


def _parse_price_value(raw: str) -> Optional[float]:
    """
    Parses a price string to float.
    Handles various formats: "45,99 KM", "€ 45.99", "45.99 EUR", "45.99".
    Returns None if parsing fails.
    """
    if not raw:
        return None
    
    s = str(raw).strip()
    
    # Remove currency symbols
    s = re.sub(r'[€$£¥₽₹元]', '', s)
    s = s.strip()
    
    if not s:
        return None
    
    # Determine decimal separator
    # European format: "45,99" or "1.234,56"
    # US format: "45.99" or "1,234.56"
    
    # Handle European format (comma as decimal separator)
    # Count commas and dots
    comma_count = s.count(',')
    dot_count = s.count('.')
    
    if comma_count == 1 and dot_count == 0:
        # Simple European: "45,99"
        s = s.replace(',', '.')
    elif comma_count == 1 and dot_count == 1:
        # Multiple separators - determine which is decimal
        comma_pos = s.rfind(',')
        dot_pos = s.rfind('.')
        if comma_pos > dot_pos:
            # European: "1.234,56" - dots are thousands
            s = s.replace('.', '')
            s = s.replace(',', '.')
        else:
            # US: "1,234.56" - commas are thousands
            s = s.replace(',', '')
    elif comma_count > 1 and dot_count == 0:
        # European with thousands: "1,234,567"
        s = s.replace(',', '')
    elif dot_count > 1 and comma_count == 0:
        # Numbers like "1.234.567" (European thousands only)
        s = s.replace('.', '')
    elif comma_count == 0 and dot_count == 1:
        # Simple US format: "45.99"
        pass
    elif comma_count > 0 and dot_count == 0:
        # Could be "1,234,567" (European thousands) or "45,99" (European decimal)
        # If the last comma is followed by exactly 2 digits, it's likely decimal
        last_comma_pos = s.rfind(',')
        after_comma = s[last_comma_pos + 1:]
        if len(after_comma) == 2 and after_comma.isdigit():
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')
    
    # Remove any remaining non-numeric except dot
    s = re.sub(r'[^\d.]', '', s)
    
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _is_valid_price_text(text: str) -> bool:
    """
    Validates that text looks like a price string.
    Returns True if:
    - Contains digits and currency symbol/code, OR
    - Contains digits with decimal separator (looks like a price number)
    
    Rejects strings longer than 30 characters.
    """
    if not text or len(text) > 30:
        return False
    
    stripped = text.strip()
    
    # Must contain digits
    if not any(c.isdigit() for c in stripped):
        return False
    
    # Check for currency symbol or code
    currency_pattern = re.compile(
        r'(?:KM|BAM|EUR|USD|GBP|€|\$|£|HRK|RSD|CHF|PLN|CZK|HUF|RON|CAD|AUD|JPY)',
        re.IGNORECASE
    )
    has_currency = bool(currency_pattern.search(stripped))
    
    # Check for decimal separator (indicates it's likely a price number)
    has_decimal = ('.' in stripped or ',' in stripped)
    
    # Must have either currency OR decimal separator
    if not has_currency and not has_decimal:
        return False
    
    # Validate format
    return bool(PRICE_VALIDATION_RE.match(stripped))


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def extract_title(soup: BeautifulSoup) -> Optional[str]:
    tag = soup.find("title")
    return normalize_whitespace(tag.get_text()) if tag else None


def extract_meta_description(soup: BeautifulSoup) -> Optional[str]:
    tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    if tag and tag.get("content"):
        return normalize_whitespace(tag["content"])
    return None


def extract_h1(soup: BeautifulSoup) -> Optional[str]:
    tag = soup.find("h1")
    return safe_get_text(tag)


def extract_canonical(soup: BeautifulSoup, page_url: Optional[str] = None) -> Optional[str]:
    """
    Extracts canonical URL.
    If page_url is provided, resolves relative canonicals to absolute URLs.
    """
    tag = soup.find("link", rel=lambda v: v and "canonical" in v)
    if not tag or not tag.get("href"):
        return None
    href = tag["href"].strip()
    if not href:
        return None
    # Resolve relative canonical (e.g. "/product/1" → "https://shop.com/product/1")
    if page_url and not href.startswith(("http://", "https://")):
        href = urljoin(page_url, href)
    return href


def extract_robots_meta(soup: BeautifulSoup) -> Optional[str]:
    tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    if tag and tag.get("content"):
        return tag["content"].strip().lower()
    return None


def extract_breadcrumb_text(soup: BeautifulSoup) -> Optional[str]:
    """Tries several common breadcrumb patterns."""
    bc = soup.find(attrs={"itemtype": re.compile(r"BreadcrumbList", re.I)})
    if bc:
        return normalize_whitespace(bc.get_text(separator=" > "))

    for cls in ["breadcrumb", "breadcrumbs", "kruh-mrvice", "bread-crumb", "migalhas"]:
        bc = soup.find(class_=re.compile(cls, re.I))
        if bc:
            return normalize_whitespace(bc.get_text(separator=" > "))

    bc = soup.find(attrs={"aria-label": re.compile(r"breadcrumb", re.I)})
    if bc:
        return normalize_whitespace(bc.get_text(separator=" > "))

    return None


def extract_visible_text_length(soup: BeautifulSoup) -> int:
    """
    Estimates visible text length WITHOUT mutating soup.
    Iterates NavigableStrings and skips those inside non-visible tags.
    """
    SKIP_TAGS = {"script", "style", "noscript", "meta", "link", "head"}
    texts = []
    for string in soup.find_all(string=True):
        parent = getattr(string, "parent", None)
        if parent is None:
            continue
        if any(p.name in SKIP_TAGS for p in string.parents):
            continue
        texts.append(str(string))
    text = " ".join(texts)
    return len(normalize_whitespace(text) or "")


def extract_image_count(soup: BeautifulSoup) -> int:
    """Total number of <img> tags on the page."""
    return len(soup.find_all("img"))


def extract_product_image_count(soup: BeautifulSoup) -> int:
    """
    Counts images that are likely product images.
    Excludes obvious tracking pixels, icons, and decorative images.
    """
    count = 0
    for img in soup.find_all("img"):
        # Skip tracking pixels
        try:
            width = img.get("width", "")
            height = img.get("height", "")
            if width and height:
                if int(width) <= 1 or int(height) <= 1:
                    continue
        except (ValueError, TypeError):
            pass
        
        # Skip common icon/logo images
        src = img.get("src", "").lower()
        alt = img.get("alt", "").lower()
        class_ = img.get("class", [])
        
        # Skip if it's likely an icon/logo
        if any(keyword in src for keyword in ["icon", "logo", "spacer", "pixel", "track"]):
            continue
        if any(keyword in alt for keyword in ["icon", "logo", "spacer"]):
            continue
        if any("icon" in str(c).lower() for c in class_):
            continue
            
        count += 1
    return count


def extract_possible_price_text(soup: BeautifulSoup) -> Optional[str]:
    """
    Extracts price text ONLY from explicit price HTML elements.
    Does NOT fall back to full-page text search — that produces too many false positives.
    Validates extracted text contains currency symbol/code or decimal separator before returning.
    Returns None if no valid price element is found.
    """
    for attrs in PRICE_SELECTORS:
        el = soup.find(attrs=attrs)
        if el:
            # Get text content or data attribute value
            text = None
            if el.name == "meta" and el.get("content"):
                text = el.get("content")
            elif attrs.get("data-price") is not None:
                text = el.get("data-price")
            elif attrs.get("data-product-price") is not None:
                text = el.get("data-product-price")
            elif attrs.get("data-sale-price") is not None:
                text = el.get("data-sale-price")
            else:
                text = normalize_whitespace(el.get_text())
            
            if text and _is_valid_price_text(text):
                return text.strip()
    return None


def extract_possible_price_value(soup: BeautifulSoup) -> Optional[float]:
    """
    Extracts price value as float from explicit price HTML elements.
    Returns None if no valid price element is found or value cannot be parsed.
    """
    price_text = extract_possible_price_text(soup)
    if price_text:
        return _parse_price_value(price_text)
    return None


def _get_product_content_area(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Returns the most likely product-specific content area as a BeautifulSoup element.
    Search order (returns first match):
    1. Tag with itemtype containing "Product"
    2. Element with class containing: product-description, product-detail,
       product-info, product-summary, woocommerce-product-details__short-description,
       product__description
    3. main tag
    4. article tag
    5. Fallback: body tag (backward compatibility)
    """
    # 1. Try itemtype containing "Product"
    product_elem = soup.find(attrs={"itemtype": re.compile(r"Product", re.I)})
    if product_elem:
        return product_elem

    # 2. Try specific product class patterns
    product_class_patterns = [
        re.compile(r"product-description", re.I),
        re.compile(r"product-detail", re.I),
        re.compile(r"product-info", re.I),
        re.compile(r"product-summary", re.I),
        re.compile(r"woocommerce-product-details__short-description", re.I),
        re.compile(r"product__description", re.I),
    ]
    for pattern in product_class_patterns:
        elem = soup.find(class_=pattern)
        if elem:
            return elem

    # 3. Try main tag
    main_tag = soup.find("main")
    if main_tag:
        return main_tag

    # 4. Try article tag
    article_tag = soup.find("article")
    if article_tag:
        return article_tag

    # 5. Fallback: body tag
    body_tag = soup.find("body")
    if body_tag:
        return body_tag

    # Last resort: return original soup
    return soup


def _get_product_area_text(soup: BeautifulSoup) -> str:
    """
    Returns text from the most likely product content area.
    Falls back to body if no product area container is found.
    Does not mutate soup.
    """
    area = _get_product_content_area(soup)
    return area.get_text(" ", strip=True).lower()


def extract_shipping_text_signal(soup: BeautifulSoup) -> bool:
    """
    Returns True if shipping keywords are found in the PRODUCT CONTENT AREA.
    Uses targeted area search, not full-page scan, to avoid footer false positives.
    """
    text = _get_product_area_text(soup)
    return any(kw in text for kw in SHIPPING_KEYWORDS)


def extract_returns_text_signal(soup: BeautifulSoup) -> bool:
    """
    Returns True if returns keywords are found in the PRODUCT CONTENT AREA.
    Uses multi-word phrases to reduce false positives ('return to top', 'return home').
    """
    text = _get_product_area_text(soup)
    return any(kw in text for kw in RETURNS_KEYWORDS)


# Language detection keywords (most common words per language)
_LANGUAGE_KEYWORDS = {
    "hr": {"i", "je", "su", "na", "za", "od", "u", "se", "s", "da", "to", "sa", "biti", "ili", "kao", "ali", "nije", "može", "ima", "samo"},
    "sr": {"и", "је", "су", "на", "за", "од", "у", "се", "са", "да", "то", "са", "бити", "или", "као", "али", "није", "може", "има", "само"},
    "en": {"the", "is", "are", "and", "or", "for", "to", "in", "on", "with", "a", "an", "of", "it", "this", "that", "by", "as", "be", "has"},
    "de": {"der", "die", "und", "ist", "in", "zu", "den", "das", "mit", "von", "für", "auf", "nicht", "sich", "sie", "auch", "es", "an", "werden"},
}


def _detect_language(text: str) -> str:
    """
    Detects language based on most common words.
    Returns 'hr', 'sr', 'en', 'de' or 'unknown'.
    """
    if not text:
        return "unknown"
    
    words = set(text.lower().split())
    
    scores = {}
    for lang, lang_words in _LANGUAGE_KEYWORDS.items():
        scores[lang] = len(words & lang_words)
    
    best_lang = max(scores, key=scores.get)
    if scores[best_lang] >= 2:
        return best_lang
    return "unknown"


def extract_description_signals(soup: BeautifulSoup) -> dict:
    """
    Extracts description quality signals from the product content area.
    
    Returns dict with:
    - description_length: int (character count)
    - description_word_count: int
    - has_feature_list: bool (ul/ol exists in product content area)
    - has_spec_table: bool (table exists in product content area)
    - description_language_signal: str ('hr'|'sr'|'en'|'de'|'unknown')
    """
    # Get product content area
    area = _get_product_content_area(soup)
    
    # Get description text (look for common description selectors first)
    description_text = None
    
    # Try Schema.org description
    desc_elem = area.find(attrs={"itemprop": re.compile(r"description", re.I)})
    if desc_elem:
        description_text = safe_get_text(desc_elem)
    
    # Try common class patterns for description
    if not description_text:
        for cls_pattern in ["description", "product-description", "short-description", 
                           "product-desc", "desc", "summary"]:
            desc_elem = area.find(class_=re.compile(cls_pattern, re.I))
            if desc_elem:
                description_text = safe_get_text(desc_elem)
                if description_text:
                    break
    
    # Fallback to first paragraph in product area
    if not description_text:
        p_elem = area.find("p")
        if p_elem:
            description_text = safe_get_text(p_elem)
    
    # If still nothing, use the entire area text (minus navigation/header)
    if not description_text:
        # Remove nav, header, footer from text
        area_copy = BeautifulSoup(str(area), "lxml")
        for tag in area_copy.find_all(["nav", "header", "footer", "aside"]):
            tag.decompose()
        description_text = normalize_whitespace(area_copy.get_text())
    
    # Calculate metrics
    description_length = len(description_text) if description_text else 0
    description_word_count = len(description_text.split()) if description_text else 0
    
    # Check for feature lists (ul/ol with more than 2 items)
    has_feature_list = False
    for list_tag in area.find_all(["ul", "ol"]):
        items = list_tag.find_all("li")
        if len(items) >= 3:
            has_feature_list = True
            break
    
    # Check for spec tables
    has_spec_table = False
    for table in area.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) >= 2:
            has_spec_table = True
            break
    
    # Detect language
    lang_signal = _detect_language(description_text or "")
    
    return {
        "description_length": description_length,
        "description_word_count": description_word_count,
        "has_feature_list": has_feature_list,
        "has_spec_table": has_spec_table,
        "description_language_signal": lang_signal,
    }


# SPA/JS-rendered detection patterns
_SPA_ROOT_SELECTORS = [
    {"id": "root"},
    {"id": "app"},
    {"id": "__next"},
    {"data-reactroot": True},
]


def detect_js_rendered(soup: BeautifulSoup, html: str) -> dict:
    """
    Detects if a page is likely rendered by JavaScript (SPA, React, Vue, Next.js, etc.)
    based on common signals.
    
    Returns dict with:
    - is_likely_js_rendered: bool
    - js_render_confidence: str ("high"|"medium"|"low"|"none")
    - js_render_signals: list[str]
    """
    signals = []
    
    # Signal 1: Thin content but large HTML (JS hasn't rendered yet)
    html_length = len(html) if html else 0
    visible_text = extract_visible_text_length(soup)
    if html_length > 10000 and visible_text < 200:
        signals.append("thin_content_large_html")
    
    # Signal 2: SPA root elements (React/Vue/Next.js common patterns)
    for selector in _SPA_ROOT_SELECTORS:
        if soup.find(attrs=selector):
            signals.append("spa_root_element")
            break
    
    # Signal 3: Script-heavy page
    script_count = len(soup.find_all("script"))
    if script_count > 15:
        signals.append("script_heavy")
    
    # Signal 4: No semantic content (no <p> or <h1> in body)
    body = soup.find("body")
    if body:
        p_count = len(body.find_all("p"))
        h1_count = len(body.find_all("h1"))
        if p_count == 0 and h1_count == 0:
            signals.append("no_semantic_content")
    
    # Signal 5: Title exists but no H1 and no schema (page loaded but JS didn't populate)
    title = extract_title(soup)
    h1 = extract_h1(soup)
    schema_blocks = soup.find_all("script", type="application/ld+json")
    if title and not h1 and len(schema_blocks) == 0:
        signals.append("title_only_no_content")
    
    # Determine confidence level based on number of signals
    signal_count = len(signals)
    if signal_count == 0:
        confidence = "none"
        is_js_rendered = False
    elif signal_count == 1:
        confidence = "low"
        is_js_rendered = False
    elif signal_count == 2:
        confidence = "medium"
        is_js_rendered = True
    else:  # 3+
        confidence = "high"
        is_js_rendered = True
    
    return {
        "is_likely_js_rendered": is_js_rendered,
        "js_render_confidence": confidence,
        "js_render_signals": signals,
    }
