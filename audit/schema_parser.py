import json
import re
from typing import Optional, List, Dict

from bs4 import BeautifulSoup

from audit.utils import normalize_whitespace


def extract_json_ld_blocks(soup: BeautifulSoup) -> list[dict]:
    """Extracts and parses all JSON-LD script blocks from the page."""
    blocks = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                blocks.append(data)
            elif isinstance(data, list):
                blocks.extend([b for b in data if isinstance(b, dict)])
        except (json.JSONDecodeError, TypeError):
            continue
    return blocks


def flatten_graph_objects(json_ld_blocks: list[dict]) -> list[dict]:
    """
    Unpacks @graph arrays and returns a flat list of individual schema objects.
    """
    objects = []
    for block in json_ld_blocks:
        if "@graph" in block and isinstance(block["@graph"], list):
            for item in block["@graph"]:
                if isinstance(item, dict):
                    objects.append(item)
        else:
            objects.append(block)
    return objects


def _get_type(obj: dict) -> str:
    """Returns the @type value as a lowercase string."""
    raw = obj.get("@type", "")
    if isinstance(raw, list):
        raw = " ".join(raw)
    return raw.lower()


def find_product_schema(objects: list[dict]) -> Optional[dict]:
    """
    Finds the first schema object of type Product.
    Avoids ProductGroup and ProductCollection (variant containers, not individual products).
    """
    for obj in objects:
        t = _get_type(obj)
        if "product" in t and "productgroup" not in t and "productcollection" not in t:
            return obj
    return None


def find_offer_schema(
    product_obj: Optional[dict], objects: list[dict]
) -> Optional[dict]:
    """
    Finds Offer data — first inside a Product's 'offers' field,
    then as a standalone Offer object.
    """
    if product_obj:
        offers = product_obj.get("offers")
        if isinstance(offers, dict):
            return offers
        if isinstance(offers, list) and offers:
            return offers[0]

    for obj in objects:
        if "offer" in _get_type(obj):
            return obj

    return None


def _safe_str(value) -> Optional[str]:
    """Converts various schema value types to string."""
    if value is None:
        return None
    if isinstance(value, dict):
        return normalize_whitespace(value.get("name") or value.get("@id") or str(value))
    if isinstance(value, list):
        return normalize_whitespace(", ".join(str(v) for v in value if v))
    return normalize_whitespace(str(value))


def _parse_price_value(raw) -> Optional[float]:
    """
    Tries to parse a schema price value to a float.
    Handles dot and comma decimal separators, including European thousands format.
    Returns None if parsing fails.
    """
    if raw is None:
        return None
    try:
        s = str(raw).strip().replace(" ", "")
        if "." in s and "," in s:
            # Both present — whichever comes last is the decimal separator
            last_dot = s.rfind(".")
            last_comma = s.rfind(",")
            if last_comma > last_dot:
                # European: "1.234,56" — dot=thousands, comma=decimal
                s = s.replace(".", "").replace(",", ".")
            else:
                # US/UK: "1,234.56" — comma=thousands, dot=decimal
                s = s.replace(",", "")
        elif "," in s and "." not in s:
            # Simple European: "29,99" → "29.99"
            s = s.replace(",", ".")
        return float(s)
    except (ValueError, TypeError):
        return None


def extract_schema_fields(
    product_obj: Optional[dict],
    offer_obj: Optional[dict],
) -> dict:
    """
    Returns standardized schema fields from Product and Offer objects.
    """
    fields: dict = {
        "schema_product_present": product_obj is not None,
        "schema_offer_present": offer_obj is not None,
        "schema_name": None,
        "schema_description": None,
        "schema_sku": None,
        "schema_gtin": None,
        "schema_brand": None,
        "schema_price": None,
        "schema_price_value": None,
        "schema_currency": None,
        "schema_availability": None,
    }

    if product_obj:
        fields["schema_name"] = _safe_str(product_obj.get("name"))
        fields["schema_description"] = _safe_str(product_obj.get("description"))
        fields["schema_sku"] = _safe_str(product_obj.get("sku"))
        
        # Brand extraction with multiple formats
        brand = product_obj.get("brand")
        if isinstance(brand, dict):
            fields["schema_brand"] = _safe_str(brand.get("name") or brand.get("@id"))
        else:
            fields["schema_brand"] = _safe_str(brand)

        # GTIN variants — try in order of specificity
        for gtin_key in ("gtin14", "gtin13", "gtin12", "gtin8", "gtin", "isbn", "mpn", "ean"):
            val = product_obj.get(gtin_key)
            if val:
                fields["schema_gtin"] = _safe_str(val)
                break

    if offer_obj:
        price_raw = offer_obj.get("price")
        fields["schema_price"] = _safe_str(price_raw)
        fields["schema_price_value"] = _parse_price_value(price_raw)
        fields["schema_currency"] = _safe_str(offer_obj.get("priceCurrency"))

        availability_raw = _safe_str(offer_obj.get("availability")) or ""
        # Normalize availability: strip schema.org URL prefix
        if "schema.org/" in availability_raw:
            fields["schema_availability"] = availability_raw.split("/")[-1].lower()
        else:
            fields["schema_availability"] = availability_raw.lower() or None

    return fields
