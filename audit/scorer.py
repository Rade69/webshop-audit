from typing import Optional

import pandas as pd

from audit.utils import is_noindex, normalize_url_for_comparison
from config import (
    MIN_VISIBLE_TEXT_LENGTH,
    MIN_IMAGE_COUNT,
    DEFAULT_CATALOG_WEIGHT,
    DEFAULT_MACHINE_WEIGHT,
    DEFAULT_COMMERCE_WEIGHT,
    DEFAULT_AGENT_READY_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Individual score functions (each returns 0–100)
#
# Design principle: each score dimension measures ONE thing cleanly.
# AGENT-FRIENDLY CONTEXT: These scores measure how well an AI agent can
# identify, read, understand, and recommend a product.
#
# catalog_score  = Does the catalog have enough data for the agent to identify
#                  and describe the product? (title, H1, meta, breadcrumb, price)
# machine_score = Can the agent programmatically read structured product data?
#                  (schema.org Product/Offer, SKU, brand, GTIN, canonical)
# commerce_score = Does the buyer (and agent) have clear info to make a decision?
#                  (price visible, images, shipping, returns, description quality)
# ---------------------------------------------------------------------------

def score_catalog_completeness(row: dict) -> int:
    """
    Mjeri da li katalog ima dovoljno podataka da agent može identificirati
    i opisati proizvod.
    
    Ovo uključuje osnovne HTML elemente koje bilo koji CMS proizvodi,
    bez obzira na to ima li stranica JSON-LD schema ili ne.
    A shop without JSON-LD should not be penalized here for missing schema fields.
    """
    points = 0
    max_points = 0

    def check(value, weight: int):
        nonlocal points, max_points
        max_points += weight
        if value:
            points += weight

    check(row.get("title"), 20)
    check(row.get("h1"), 20)
    check(row.get("meta_description"), 15)
    check(row.get("breadcrumb_text"), 10)
    check(row.get("html_price_text"), 20)

    # Visible text: at least MIN_VISIBLE_TEXT_LENGTH characters
    max_points += 15
    if (row.get("visible_text_length") or 0) >= MIN_VISIBLE_TEXT_LENGTH:
        points += 15

    if not max_points:
        return 0
    return round((points / max_points) * 100)


def score_machine_readability(row: dict) -> int:
    """
    Mjeri da li agent može programski pročitati proizvod podatke.
    
    Ovo uključuje Schema.org structured data (Product/Offer), tehničke
    SEO signale (canonical), i identifikatore (SKU, GTIN, brand).
    Schema polja žive isključivo ovdje — ne u catalog_score.
    """
    points = 0
    max_points = 0

    def check(value, weight: int):
        nonlocal points, max_points
        max_points += weight
        if value:
            points += weight

    check(row.get("schema_product_present"), 15)
    check(row.get("schema_offer_present"), 10)
    check(row.get("schema_price"), 12)
    check(row.get("schema_currency"), 8)
    check(row.get("schema_availability"), 10)
    check(row.get("schema_sku"), 10)
    check(row.get("schema_brand"), 8)
    check(row.get("schema_gtin"), 7)
    check(row.get("canonical"), 10)

    # Not noindex — positive signal
    max_points += 10
    if not is_noindex(row.get("robots_meta")):
        points += 10

    if not max_points:
        return 0
    return round((points / max_points) * 100)


def score_commerce_clarity(row: dict) -> int:
    """
    Mjeri da li kupac i agent imaju jasne informacije za donošenje odluke.
    
    Ovo uključuje: cijena vidljiva, dovoljno slika proizvoda, signal za
    dostavu/povrat, i kvalitet opisa (koji agent koristi za preporuku).
    
    Koristi product_image_count umjesto image_count da izbjegne lažne pozitive.
    Shipping/returns su sada ciljani na product area, ne cijelu stranicu.
    
    Total weight: 100
    - Price: 30
    - Shipping: 15
    - Returns: 15
    - Images: 20
    - Description quality: 15
    """
    points = 0
    max_points = 0

    def check(value, weight: int):
        nonlocal points, max_points
        max_points += weight
        if value:
            points += weight

    # Price: schema price takes priority, html_price_text as secondary
    has_price = bool(row.get("schema_price") or row.get("html_price_text"))
    check(has_price, 30)

    check(row.get("shipping_signal"), 15)
    check(row.get("returns_signal"), 15)

    # product_image_count filters tracking pixels, more honest than image_count
    max_points += 20
    if (row.get("product_image_count") or 0) >= MIN_IMAGE_COUNT:
        points += 20

    # Description quality score (0-100, contributes proportionally)
    desc_quality = row.get("description_quality_score") or 0
    max_points += 15
    points += round((desc_quality / 100) * 15)

    if not max_points:
        return 0
    return round((points / max_points) * 100)


# ---------------------------------------------------------------------------
# Flag detectors
# ---------------------------------------------------------------------------

def detect_indexability_blockers(row: dict) -> list[str]:
    flags = []
    if is_noindex(row.get("robots_meta")):
        flags.append("noindex")
    if row.get("status_code") and row["status_code"] != 200:
        flags.append(f"status_{row['status_code']}")
    if row.get("fetch_error"):
        flags.append("fetch_error")
    canonical = row.get("canonical")
    final_url = row.get("final_url")
    if isinstance(canonical, str) and isinstance(final_url, str):
        # Normalize both URLs before comparing:
        # handles http/https, www/non-www, trailing slashes, tracking params
        canon_norm = normalize_url_for_comparison(canonical)
        final_norm = normalize_url_for_comparison(final_url)
        if canon_norm and final_norm and canon_norm != final_norm:
            flags.append("canonical_mismatch")
    return flags


def detect_missing_fields(row: dict) -> list[str]:
    """Human-readable list of missing fields — used for CSV review column, not scoring."""
    missing = []
    checks = {
        "title": row.get("title"),
        "h1": row.get("h1"),
        "meta_description": row.get("meta_description"),
        "canonical": row.get("canonical"),
        "html_price": row.get("html_price_text"),
        "schema_product": row.get("schema_product_present"),
        "schema_offer": row.get("schema_offer_present"),
        "schema_price": row.get("schema_price"),
        "schema_currency": row.get("schema_currency"),
        "schema_availability": row.get("schema_availability"),
        "schema_sku": row.get("schema_sku"),
        "schema_brand": row.get("schema_brand"),
    }
    for field_name, value in checks.items():
        if not value:
            missing.append(field_name)
    return missing


# ---------------------------------------------------------------------------
# DataFrame-level scoring
# ---------------------------------------------------------------------------

def build_scored_dataframe(
    df: pd.DataFrame,
    catalog_weight: float = DEFAULT_CATALOG_WEIGHT,
    machine_weight: float = DEFAULT_MACHINE_WEIGHT,
    commerce_weight: float = DEFAULT_COMMERCE_WEIGHT,
    agent_ready_threshold: int = DEFAULT_AGENT_READY_THRESHOLD,
) -> pd.DataFrame:
    """
    Adds scoring columns and flag columns to the raw DataFrame.
    Returns the enriched DataFrame.

    Args:
        df: Raw product DataFrame.
        catalog_weight: Weight for catalog_score in overall_score (auto-normalised).
        machine_weight: Weight for machine_score in overall_score (auto-normalised).
        commerce_weight: Weight for commerce_score in overall_score (auto-normalised).
        agent_ready_threshold: Minimum overall_score for agent_ready=True.
    """
    df = df.copy()
    rows_as_dicts = df.to_dict(orient="records")

    df["catalog_score"] = [score_catalog_completeness(r) for r in rows_as_dicts]
    df["machine_score"] = [score_machine_readability(r) for r in rows_as_dicts]
    df["commerce_score"] = [score_commerce_clarity(r) for r in rows_as_dicts]

    # Normalise weights so they always sum to 1, even if the caller passes
    # raw percentage integers (e.g. 30, 35, 35) or mismatched floats.
    total_weight = catalog_weight + machine_weight + commerce_weight
    if total_weight <= 0:
        total_weight = 1.0
    w_cat = catalog_weight / total_weight
    w_mac = machine_weight / total_weight
    w_com = commerce_weight / total_weight

    df["overall_score"] = (
        df["catalog_score"] * w_cat
        + df["machine_score"] * w_mac
        + df["commerce_score"] * w_com
    ).round().astype(int)

    # Human-readable summary columns
    df["missing_fields"] = [
        ", ".join(detect_missing_fields(r)) for r in rows_as_dicts
    ]
    df["indexability_flags"] = [
        ", ".join(detect_indexability_blockers(r)) for r in rows_as_dicts
    ]

    # Separate filterable flag columns (easier to use in Excel than comma-separated string)
    df["flag_noindex"] = df["robots_meta"].apply(
        lambda x: is_noindex(x)
    )
    
    # Handle NaN values in indexability_flags before using .str accessor
    if "indexability_flags" in df.columns:
        flags_series = df["indexability_flags"].fillna("")
        df["flag_canonical_mismatch"] = flags_series.str.contains(
            "canonical_mismatch", na=False
        )
        df["flag_fetch_error"] = flags_series.str.contains(
            "fetch_error", na=False
        )
        df["flag_non_200"] = flags_series.str.contains(
            r"status_\d+", na=False, regex=True
        )
    else:
        df["flag_canonical_mismatch"] = False
        df["flag_fetch_error"] = False
        df["flag_non_200"] = False
    
    df["flag_js_rendered"] = df["is_likely_js_rendered"].astype(bool)

    # Convenience diagnostic flags
    df["suspicious_price_missing"] = ~(
        df["schema_price"].notna() | df["html_price_text"].notna()
    )
    df["suspicious_schema_missing"] = ~df["schema_product_present"].astype(bool)
    df["suspicious_low_content"] = df["visible_text_length"] < MIN_VISIBLE_TEXT_LENGTH
    df["flag_not_product_page"] = ~df["is_likely_product_page"].astype(bool)

    # Agent-ready: binary signal za "je li ovaj proizvod spreman za AI preporuku?"
    df["agent_ready"] = (
        (df["overall_score"] >= agent_ready_threshold)
        & (~df["flag_js_rendered"])
        & (~df["suspicious_price_missing"])
        & (~df["suspicious_schema_missing"])
    )

    return df


# ---------------------------------------------------------------------------
# Bonus: sitewide and category summaries
# ---------------------------------------------------------------------------

def summarize_sitewide_scores(df: pd.DataFrame) -> dict:
    """Returns sitewide averages and score distribution."""
    if df.empty:
        return {}

    score_cols = ["catalog_score", "machine_score", "commerce_score", "overall_score"]
    summary = {}
    for col in score_cols:
        if col in df.columns:
            summary[f"avg_{col}"] = round(df[col].mean(), 1)

    if "overall_score" in df.columns:
        summary["pct_above_70"] = round((df["overall_score"] >= 70).mean() * 100, 1)
        summary["pct_below_40"] = round((df["overall_score"] < 40).mean() * 100, 1)

    return summary


def summarize_by_category(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    If breadcrumb_text exists, infers category using hierarchical approach.
    Returns aggregated scores per category or None if data is insufficient.
    
    Hierarchy:
    1. breadcrumb_text - reverse iteration, skip generic/brand/product names
    2. URL pattern - extract from URL path with regex patterns
    3. title/H1 signal - use meaningful words, skip marketing noise
    4. fallback to "Unknown" (not "Generic")
    """
    if "breadcrumb_text" not in df.columns or df["breadcrumb_text"].isna().all():
        return None

    # Extended generic categories to skip - these don't carry useful information
    GENERIC_CATEGORIES = {
        # Generic shop terms
        "proizvodi", "products", "artikli", "artikal", "item", "items",
        "shop", "katalog", "catalog", "store", "trgovina", "prodavnica",
        "home", "početna", "pocetna", "start", "main", "glavna",
        "all", "svi", "sve", "all products", "svi proizvodi",
        "new", "novo", "novosti", "new arrivals", "najnovije",
        "sale", "popust", "akcija", "discount", "snizenje",
        "best", "najbolje", "top", "featured", "istaknuto",
        "collection", "kolekcija", "collections", "kolekcije",
        "category", "kategorija", "categories", "kategorije",
        "generic", "general", "opšte", "opste", "common",
    }
    
    # Extended brand indicators to skip
    BRAND_INDICATORS = {
        "nike", "adidas", "puma", "reebok", "under armour", "ua",
        "zara", "h&m", "mango", "uniqlo", "levis", "levi's",
        "calvin klein", "ck", "gucci", "prada", "versace", "armani",
        "tommy hilfiger", "ralph lauren", "lacoste", "boss", "hugo boss",
        "converse", "vans", "new balance", "asics", "skechers",
        "sport vision", "intersport", "decathlon", "sports direct",
    }
    
    # Extended category keywords to look for (positive signals)
    CATEGORY_KEYWORDS = {
        # Clothing
        "tekstil", "odeća", "odeca", "odjeća", "odjeca", "clothing", "apparel",
        "majice", "t-shirt", "tshirt", "bluze", "blouse", "košulje", "kosulje", "shirts",
        "haljine", "dresses", "suknje", "skirts", "pantalone", "trousers", "pants",
        "jakne", "jackets", "kaputi", "coats", "prsluci", "vests", "waistcoats",
        "duksevi", "hoodies", "dukserice", "sweatshirts", "sweaters", "puloveri",
        "trenirke", "tracksuits", "trenerke", "sportswear", "sport suit",
        "donji dio", "bottoms", "gornji dio", "tops", "donje rublje", "underwear",
        "kupaći", "swimwear", "kupaci", "beachwear", "plažna odjeća", "beach clothing",
        
        # Footwear
        "obuća", "obuca", "footwear", "shoes", "patike", "sneakers", "tenisice",
        "cipele", "shoes", "cizme", "čizme", "boots", "sandale", "sandals",
        "čarape", "carape", "socks", "stopala", "foot",
        
        # Accessories
        "torbe", "bags", "torbice", "handbags", "ruksaci", "backpacks",
        "nakiti", "jewelry", "nakit", "bijuterija", "satovi", "watches",
        "naočare", "naocare", "glasses", "sunglasses", "sunčane naočare",
        "kape", "caps", "šeširi", "hats", "marame", "scarves",
        "remenje", "belts", "kaiševi", "belts",
        
        # Sports
        "sportska oprema", "sports equipment", "sport", "fitness",
        "biciklističke", "cycling", "bicikl", "bicycle",
        "trčanje", "running", "trkačke", "running shoes",
        "teretana", "gym", "fitness", "workout",
        
        # Electronics
        "elektronika", "electronics", "telefon", "phone", "mobitel",
        "laptop", "tablet", "računar", "racunar", "computer",
        "audio", "zvuk", "sound", "slušalice", "headphones",
        
        # Home & Furniture
        "nameštaj", "namestaj", "furniture", "djak", "sofa", "krevet", "bed",
        "kućni tekstil", "home textile", "posteljina", "bedding",
        "kuhinja", "kitchen", "trpezarija", "dining",
        
        # Other
        "igračke", "toys", "knjige", "books", "hrana", "food", "piće", "drink",
        "kozmetika", "cosmetics", "parfemi", "perfumes", "lična njega", "personal care",
    }
    
    # Extended product name patterns to skip (too specific)
    # These are product/collection/model names, NOT categories
    PRODUCT_PATTERNS = {
        # Under Armour collection names
        "unstoppable", "icon", "foundation", "baseline", "essential", "core",
        "sportstyle", "vanish", "hero", "phantom", "stripe", "precision",
        "coldgear", "heatgear", "rush", "recovery", "iso-chill",
        
        # Nike collection names  
        "air", "max", "zoom", "fly", " Pegasus", "revolution", "quest",
        "flex", "react", "invigor", " Odyssey", "Element", " dry",
        
        # Puma collection names
        "stack", "crossback", "vida", "softer", "faster", "cell",
        
        # Generic product patterns
        "seamless", "bra", "logo", "ss", "fleece", "update", "classic",
        "pro", "basic", "prime", "premium", "elite", "ultra",
        "boost", "cloud", "limited", "edition", "special", "exclusive",
        "signature", "original", "authentic", "genuine", "official",
        "graphic", "print", "stripe", "colorblock", "panel",
        
        # Common model suffixes
        "mid", "low", "high", "retro", "fw", "ss", "ls", "gt",
    }
    
    # Words that are ALWAYS categories (even if they match product patterns)
    # These take precedence over PRODUCT_PATTERNS
    # Note: "pro" removed - too ambiguous as standalone word
    CATEGORY_OVERRIDES = {
        "bra", "bra i top", "bras",    # Lingerie category, not product
    }
    
    def is_generic(text: str) -> bool:
        """Check if text contains any generic category word."""
        if not text:
            return False
        text_lower = text.lower()
        # Check for exact match or contains generic word
        for gen in GENERIC_CATEGORIES:
            if gen == text_lower or f" {gen} " in f" {text_lower} ":
                return True
        return False
    
    def is_brand(text: str) -> bool:
        """Check if text contains any brand indicator."""
        if not text:
            return False
        text_lower = text.lower()
        for brand in BRAND_INDICATORS:
            if brand in text_lower:
                return True
        return False
    
    def contains_category_keyword(text: str) -> Optional[str]:
        """Check if text contains any category keyword, return the keyword."""
        if not text:
            return None
        text_lower = text.lower()
        for kw in CATEGORY_KEYWORDS:
            if kw in text_lower:
                return kw
        return None
    
    def extract_category(row: dict) -> str:
        import re
        """Extract category using hierarchical approach.
        
        Hierarchy:
        1. breadcrumb_text - reverse iteration, skip generic/brand/product names
           - Prefer mid-level category over final product name segment
           - Skip segments that are ALL CAPS (likely product names)
           - Use category overrides to prevent skipping true categories
        2. URL pattern - extract from URL path with regex patterns
        3. title/H1 signal - use meaningful words, skip marketing noise
        4. fallback to 'Unknown'
        """
        
        # 1. Try breadcrumb_text - look for category keywords
        breadcrumb = row.get("breadcrumb_text", "")
        if breadcrumb and not pd.isna(breadcrumb):
            parts = [p.strip() for p in str(breadcrumb).split(">") if p.strip()]
            
            # Search from END to START (most specific to least specific)
            for part in reversed(parts):
                part_lower = part.lower()
                
                # Skip if empty
                if not part or len(part) < 2:
                    continue
                    
                # Skip generic
                if is_generic(part):
                    continue
                    
                # Skip if it's a brand
                if is_brand(part):
                    continue
                
                # Skip if it looks like a product name
                # BUT first check if it's a category override (e.g., "Bra" is a category, not product)
                is_override_category = any(
                    override in part_lower for override in CATEGORY_OVERRIDES
                )
                if not is_override_category and any(pat in part_lower for pat in PRODUCT_PATTERNS):
                    continue
                
                # NEW: Skip if the segment is ALL CAPS (likely a product name, not category)
                # Exception: common acronyms that could be categories
                if part.isupper() and len(part) > 3 and part not in ('USA', 'EU', 'UK', 'UN'):
                    continue
                
                # Check for category keywords
                category_kw = contains_category_keyword(part)
                if category_kw:
                    # Return the original part (with proper casing)
                    return part
                
                # If it looks like a reasonable category word
                # Not too short, not too long, no digits, not all uppercase
                # Note: use >= 3 not > 3 to allow 3-char category words like "Bra"
                if (3 <= len(part) < 25 and 
                    not any(c.isdigit() for c in part) and
                    not part.isupper() and
                    not part_lower.endswith(('s', 'es'))):  # Avoid plurals as generic
                    return part
        
        # 2. Try URL pattern with improved regex
        url = row.get("url", "")
        if url and not pd.isna(url):
            url_str = str(url).lower()
            
            # Extract path from URL
            path_match = re.search(r'https?://[^/]+(/[^?#]*)', url_str)
            if path_match:
                path = path_match.group(1)
                
                # Common category patterns in URLs with regex
                url_patterns = [
                    # Clothing patterns
                    (r'/(majic[aey]|t-shirt|tshirt|bluz[aey])/', 'Majice'),
                    (r'/(dukseric[aey]|hoodie|sweatshirt|pulover)/', 'Dukserice'),
                    (r'/(patik[aey]|tenisic[aey]|sneaker|obuca)/', 'Patike'),
                    (r'/(jakn[aey]|jacket|kaput)/', 'Jakne'),
                    (r'/(haljin[aey]|dress)/', 'Haljine'),
                    (r'/(košulj[aey]|kosulj[aey]|shirt)/', 'Košulje'),
                    (r'/(pantalon[aey]|trousers|pants)/', 'Pantalone'),
                    (r'/(torba|torbica|bag|ruksak)/', 'Torbe'),
                    
                    # Footwear
                    (r'/(cizam[aey]|čizam[aey]|boot)/', 'Čizme'),
                    (r'/(cipel[aey]|shoe)/', 'Cipele'),
                    (r'/(sandala|sandale|sandal)/', 'Sandale'),
                    
                    # Accessories
                    (r'/(nakit|jewelry|bijuterija)/', 'Nakit'),
                    (r'/(sat|watch)/', 'Satovi'),
                    (r'/(naočar[aey]|naocar[aey]|glasses)/', 'Naočare'),
                    
                    # Sports
                    (r'/(biciklistick[aey]|cycling|bicycle)/', 'Biciklističke'),
                    (r'/(sportska|sport|fitness)/', 'Sportska oprema'),
                    
                    # Generic category patterns (fallback)
                    (r'/(tekstil|odeca|odeća|clothing)/', 'Tekstil'),
                    (r'/(elektronika|electronics)/', 'Elektronika'),
                    (r'/(namestaj|nameštaj|furniture)/', 'Nameštaj'),
                ]
                
                for pattern, category in url_patterns:
                    if re.search(pattern, path):
                        return category
        
        # 3. Try title/H1 signal with improved filtering
        title = row.get("title", "") or row.get("h1", "")
        if title and not pd.isna(title):
            title_str = str(title)
            
            # Skip words that are too common or marketing
            skip_words = {
                "proizvod", "proizvodi", "product", "products", 
                "artikal", "artikli", "item", "items",
                "kupite", "kupi", "buy", "purchase", "shop",
                "online", "prodavnica", "store", "trgovina",
                "novo", "new", "akcija", "sale", "popust", "discount",
                "besplatna", "free", "brza", "fast", "express",
                "kvalitet", "quality", "premium", "luxury", "luksuz",
            }
            
            # Also skip brand names
            skip_words.update(BRAND_INDICATORS)
            
            words = re.findall(r'\b[\w-]+\b', title_str)
            for word in words[:5]:  # Check first 5 words
                cleaned = word.strip("-|,.:;()").lower()
                
                # Skip if too short, skip word, or generic
                if len(cleaned) < 4 or cleaned in skip_words or is_generic(cleaned):
                    continue
                    
                # Check if it's a category keyword
                category_kw = contains_category_keyword(cleaned)
                if category_kw:
                    return category_kw.title()
                
                # If it looks like a reasonable category
                if (4 <= len(cleaned) <= 20 and 
                    not any(c.isdigit() for c in cleaned) and
                    not cleaned.isnumeric()):
                    return cleaned.title()
        
        # 4. Fallback to "Unknown" (not "Generic")
        return "Unknown"

    df = df.copy()
    df["_category"] = df.apply(extract_category, axis=1)

    group = df.groupby("_category").agg(
        product_count=("url", "count"),
        avg_overall_score=("overall_score", "mean"),
        avg_catalog_score=("catalog_score", "mean"),
        avg_machine_score=("machine_score", "mean"),
        avg_commerce_score=("commerce_score", "mean"),
        pct_no_schema=("suspicious_schema_missing", "mean"),
        pct_no_price=("suspicious_price_missing", "mean"),
    ).reset_index().rename(columns={"_category": "category"})

    group["avg_overall_score"] = group["avg_overall_score"].round(1)
    group["avg_catalog_score"] = group["avg_catalog_score"].round(1)
    group["avg_machine_score"] = group["avg_machine_score"].round(1)
    group["avg_commerce_score"] = group["avg_commerce_score"].round(1)
    group["pct_no_schema"] = (group["pct_no_schema"] * 100).round(1)
    group["pct_no_price"] = (group["pct_no_price"] * 100).round(1)

    return group.sort_values("avg_overall_score")
