from typing import Optional

import pandas as pd

from audit.utils import is_noindex, normalize_url_for_comparison
from config import MIN_VISIBLE_TEXT_LENGTH, MIN_IMAGE_COUNT


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

def build_scored_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds scoring columns and flag columns to the raw DataFrame.
    Returns the enriched DataFrame.
    """
    df = df.copy()
    rows_as_dicts = df.to_dict(orient="records")

    df["catalog_score"] = [score_catalog_completeness(r) for r in rows_as_dicts]
    df["machine_score"] = [score_machine_readability(r) for r in rows_as_dicts]
    df["commerce_score"] = [score_commerce_clarity(r) for r in rows_as_dicts]

    # Overall score: weighted average
    # AGENT-FRIENDLY: commerce_clarity je jednako važan kao machine_readability
    # catalog (HTML quality) 30% | machine (schema+tech) 35% | commerce (clarity) 35%
    df["overall_score"] = (
        df["catalog_score"] * 0.30
        + df["machine_score"] * 0.35
        + df["commerce_score"] * 0.35
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
    df["flag_canonical_mismatch"] = df["indexability_flags"].str.contains(
        "canonical_mismatch", na=False
    )
    df["flag_fetch_error"] = df["indexability_flags"].str.contains(
        "fetch_error", na=False
    )
    df["flag_non_200"] = df["indexability_flags"].str.contains(
        r"status_\d+", na=False, regex=True
    )
    df["flag_js_rendered"] = df["is_likely_js_rendered"].astype(bool)

    # Convenience diagnostic flags
    df["suspicious_price_missing"] = ~(
        df["schema_price"].notna() | df["html_price_text"].notna()
    )
    df["suspicious_schema_missing"] = ~df["schema_product_present"].astype(bool)
    df["suspicious_low_content"] = df["visible_text_length"] < MIN_VISIBLE_TEXT_LENGTH
    df["flag_not_product_page"] = ~df["is_likely_product_page"].astype(bool)

    # Agent-ready: binary signal za "je li ovaj proizvod spreman za AI preporuku?"
    # requires: overall_score >= 65, not JS-rendered, has price, has schema
    df["agent_ready"] = (
        (df["overall_score"] >= 65)
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
    If breadcrumb_text exists, infers category from the second breadcrumb segment.
    Returns aggregated scores per category or None if data is insufficient.
    """
    if "breadcrumb_text" not in df.columns or df["breadcrumb_text"].isna().all():
        return None

    def infer_category(breadcrumb: Optional[str]) -> str:
        if not breadcrumb:
            return "Unknown"
        parts = [p.strip() for p in breadcrumb.split(">") if p.strip()]
        # Home > Category > Subcategory > Product — we want index 1 (Category)
        if len(parts) >= 2:
            return parts[1]
        if parts:
            return parts[0]
        return "Unknown"

    df = df.copy()
    df["_category"] = df["breadcrumb_text"].apply(infer_category)

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
