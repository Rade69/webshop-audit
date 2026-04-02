"""
Issue-centric grouping module — grupisanje URL-ova po tipovima problema.

Ovaj modul pruža pregled problema po vrstama umjesto po URL-ovima.
Koristi postojeće flag/score podatke — ne duplicira extraction logiku.

Design principles:
- Koristiti postojeće flag kolone iz scorer-a
- Jedan source-of-truth za issue definicije
- Fokus na praktičan workflow (popravi sve stranice bez cijene)
- Bez generičkog BI dashboard-a
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import pandas as pd


# Issue definicije — canonical mapping
# Svaki issue ima:
# - issue_id: mašinski identifikator
# - display_name: ljudsko ime
# - flag_column: kolona koja označava problem
# - description: kratak opis
# - priority: prioritet (1 = najviši)
# - impact: očekivani impact popravke (HIGH/MEDIUM/LOW)

ISSUE_DEFINITIONS = [
    {
        "issue_id": "fetch_error",
        "display_name": "Fetch greška",
        "flag_column": "flag_fetch_error",
        "description": "Stranice koje se ne mogu preuzeti (timeout, connection error)",
        "priority": 1,
        "impact": "HIGH",  # Kritično - stranica nije dostupna
    },
    {
        "issue_id": "non_200",
        "display_name": "Nije 200 OK",
        "flag_column": "flag_non_200",
        "description": "Stranice vraćaju 4xx/5xx status kod",
        "priority": 1,
        "impact": "HIGH",  # Kritično - stranica ne radi
    },
    {
        "issue_id": "not_product_page",
        "display_name": "Nije produktna stranica",
        "flag_column": "flag_not_product_page",
        "description": "Stranica ne liči na produktnu (kategorija, blog, itd.)",
        "priority": 1,
        "impact": "MEDIUM",  # Zavisi od konteksta - možda namjerno
    },
    {
        "issue_id": "noindex",
        "display_name": "Noindex",
        "flag_column": "flag_noindex",
        "description": "Stranice sa noindex meta tagom — nisu indeksirane",
        "priority": 2,
        "impact": "HIGH",  # Visok impact - stranica nije u Google-u
    },
    {
        "issue_id": "canonical_mismatch",
        "display_name": "Canonical mismatch",
        "flag_column": "flag_canonical_mismatch",
        "description": "Canonical URL pokazuje na drugu stranicu",
        "priority": 2,
        "impact": "HIGH",  # Visok impact - SEO signal ide na drugu stranicu
    },
    {
        "issue_id": "missing_price",
        "display_name": "Nema cijene",
        "flag_column": "suspicious_price_missing",
        "description": "Stranice bez vidljive cijene (HTML ili schema)",
        "priority": 2,
        "impact": "HIGH",  # Kritično za ecommerce - kupci ne vide cijenu
    },
    {
        "issue_id": "missing_schema",
        "display_name": "Nema Product schema",
        "flag_column": "suspicious_schema_missing",
        "description": "Stranice bez Product structured data",
        "priority": 2,
        "impact": "HIGH",  # Visok impact - AI agenti i Google teže razumiju
    },
    {
        "issue_id": "js_rendered",
        "display_name": "JS render",
        "flag_column": "flag_js_rendered",
        "description": "Stranice koje koriste JavaScript renderiranje",
        "priority": 3,
        "impact": "MEDIUM",  # Srednji impact - neki crawleri ne vide sadržaj
    },
    {
        "issue_id": "low_content",
        "display_name": "Malo sadržaja",
        "flag_column": "suspicious_low_content",
        "description": "Stranice sa malo vidljivog teksta (<200 znakova)",
        "priority": 3,
        "impact": "MEDIUM",  # Srednji impact - manje korisno za AI/kupce
    },
]


# Impact ordering za sortiranje
IMPACT_ORDER = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}


@dataclass
class IssueGroup:
    """
    Grupa URL-ova za specifičan issue.
    
    Sadrži:
    - issue_id, display_name, description, priority
    - count: broj pogođenih stranica
    - avg_score: prosječan overall_score pogođenih
    - urls: lista URL-ova (max 10 za preview)
    - url_count: ukupan broj URL-ova (može biti > len(urls))
    """
    issue_id: str
    display_name: str
    description: str
    priority: int
    count: int
    avg_score: float
    urls: List[str]
    url_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertuje u dictionary za export."""
        return asdict(self)


def group_by_issue(df: pd.DataFrame, issue_id: str) -> Optional[IssueGroup]:
    """
    Grupiše URL-ove za specifičan issue.
    
    Args:
        df: Scored DataFrame sa flag kolonama
        issue_id: ID issue-a iz ISSUE_DEFINITIONS
    
    Returns:
        IssueGroup ili None ako nema pogođenih URL-ova
    """
    # Pronađi definiciju
    issue_def = next((i for i in ISSUE_DEFINITIONS if i["issue_id"] == issue_id), None)
    if not issue_def:
        return None
    
    flag_col = issue_def["flag_column"]
    if flag_col not in df.columns:
        return None
    
    # Filtriraj pogođene URL-ove
    # Handle both boolean and int (0/1) columns
    if df[flag_col].dtype == bool:
        mask = df[flag_col]
    else:
        mask = df[flag_col].astype(bool)
    
    affected = df[mask].copy()
    
    if affected.empty:
        return None
    
    # Izračunaj statistike
    count = len(affected)
    avg_score = round(affected["overall_score"].mean(), 1) if "overall_score" in affected.columns else 0.0
    
    # Uzmi top 10 URL-ova (sortirano po overall_score ascending — najgori prvi)
    if "overall_score" in affected.columns:
        affected = affected.sort_values("overall_score", ascending=True)
    
    urls = affected["url"].head(10).tolist()
    
    return IssueGroup(
        issue_id=issue_id,
        display_name=issue_def["display_name"],
        description=issue_def["description"],
        priority=issue_def["priority"],
        count=count,
        avg_score=avg_score,
        urls=urls,
        url_count=count,
    )


def get_all_issue_groups(df: pd.DataFrame) -> List[IssueGroup]:
    """
    Grupiše sve issue-e i vraća sortirano po prioritetu i count-u.
    
    Args:
        df: Scored DataFrame sa flag kolonama
    
    Returns:
        Lista IssueGroup objekata sortirana po prioritetu (1 = prvi)
    """
    groups = []
    
    for issue_def in ISSUE_DEFINITIONS:
        group = group_by_issue(df, issue_def["issue_id"])
        if group:
            groups.append(group)
    
    # Sortiraj po prioritetu (1 = najviši), pa po count-u (descending)
    groups.sort(key=lambda g: (g.priority, -g.count))
    
    return groups


def create_issue_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Kreira issue summary DataFrame za CSV export.

    Args:
        df: Scored DataFrame

    Returns:
        DataFrame sa kolonama:
        - issue_id, display_name, description, priority, impact
        - count, avg_score, pct_affected
    """
    groups = get_all_issue_groups(df)
    total_urls = len(df)

    records = []
    for g in groups:
        pct_affected = round(g.count / total_urls * 100, 1) if total_urls > 0 else 0.0
        # Get impact from ISSUE_DEFINITIONS
        issue_def = next((i for i in ISSUE_DEFINITIONS if i["issue_id"] == g.issue_id), None)
        impact = issue_def["impact"] if issue_def else "MEDIUM"
        
        records.append({
            "issue_id": g.issue_id,
            "display_name": g.display_name,
            "description": g.description,
            "priority": g.priority,
            "impact": impact,
            "count": g.count,
            "avg_score": g.avg_score,
            "pct_affected": pct_affected,
            "top_urls": "; ".join(g.urls[:5]),  # Prvih 5 za preview
        })

    return pd.DataFrame(records)


def create_issue_to_urls_mapping(df: pd.DataFrame, min_count: int = 1) -> pd.DataFrame:
    """
    Kreira mapping issue → URL-ovi za CSV export.
    
    Args:
        df: Scored DataFrame
        min_count: Minimalan broj URL-ova da se issue uključi
    
    Returns:
        DataFrame sa kolonama:
        - issue_id, display_name, url, overall_score
    """
    groups = get_all_issue_groups(df)
    
    records = []
    for g in groups:
        if g.count < min_count:
            continue
        
        # Uzmi sve URL-ove za ovaj issue
        issue_def = next((i for i in ISSUE_DEFINITIONS if i["issue_id"] == g.issue_id), None)
        if not issue_def:
            continue
        
        flag_col = issue_def["flag_column"]
        if flag_col not in df.columns:
            continue
        
        # Filtriraj
        if df[flag_col].dtype == bool:
            mask = df[flag_col]
        else:
            mask = df[flag_col].astype(bool)
        
        affected = df[mask][["url", "overall_score"]].copy()
        
        for _, row in affected.iterrows():
            records.append({
                "issue_id": g.issue_id,
                "display_name": g.display_name,
                "url": row["url"],
                "overall_score": row["overall_score"],
            })
    
    return pd.DataFrame(records)


def get_url_issues(df: pd.DataFrame, url: str) -> List[str]:
    """
    Vraća listu issue-a za specifičan URL.
    
    Args:
        df: Scored DataFrame
        url: URL za provjeru
    
    Returns:
        Lista issue_id-eva koji se odnose na ovaj URL
    """
    row = df[df["url"] == url]
    if row.empty:
        return []
    
    row = row.iloc[0]
    issues = []
    
    for issue_def in ISSUE_DEFINITIONS:
        flag_col = issue_def["flag_column"]
        if flag_col in row.index:
            val = row[flag_col]
            # Handle various truthy values including pandas NaN
            if val is True or val == 1:
                issues.append(issue_def["issue_id"])
            elif isinstance(val, (bool, int)) and val:
                issues.append(issue_def["issue_id"])
            elif isinstance(val, float) and val == 1.0:
                issues.append(issue_def["issue_id"])
    
    return issues


def get_issue_display_name(issue_id: str) -> str:
    """
    Vraća display name za issue_id.
    
    Args:
        issue_id: ID issue-a
    
    Returns:
        Display name ili issue_id ako nije pronađen
    """
    issue_def = next((i for i in ISSUE_DEFINITIONS if i["issue_id"] == issue_id), None)
    return issue_def["display_name"] if issue_def else issue_id


def get_issue_priority(issue_id: str) -> int:
    """
    Vraća prioritet za issue_id.
    
    Args:
        issue_id: ID issue-a
    
    Returns:
        Prioritet (1 = najviši) ili 99 ako nije pronađen
    """
    issue_def = next((i for i in ISSUE_DEFINITIONS if i["issue_id"] == issue_id), None)
    return issue_def["priority"] if issue_def else 99


def get_issue_filter_presets() -> Dict[str, str]:
    """
    Vraća filter preset-e za GUI.

    Returns:
        Dictionary {preset_name: flag_column}
    """
    return {
        issue_def["display_name"]: issue_def["flag_column"]
        for issue_def in ISSUE_DEFINITIONS
    }


def get_issue_impact(issue_id: str) -> str:
    """
    Vraća impact nivo za issue_id.

    Args:
        issue_id: ID issue-a

    Returns:
        Impact nivo (HIGH/MEDIUM/LOW) ili "LOW" ako nije pronađen
    """
    issue_def = next((i for i in ISSUE_DEFINITIONS if i["issue_id"] == issue_id), None)
    return issue_def["impact"] if issue_def else "LOW"


def get_impact_order(impact: str) -> int:
    """
    Vraća redni broj za impact (za sortiranje).

    Args:
        impact: Impact nivo (HIGH/MEDIUM/LOW)

    Returns:
        Redni broj (1 = HIGH, 2 = MEDIUM, 3 = LOW)
    """
    return IMPACT_ORDER.get(impact, 3)


def calculate_fix_impact_score(issues: List[str]) -> Dict[str, Any]:
    """
    Računa ukupni impact score za listu issue-a.

    Args:
        issues: Lista issue_id-eva (može biti sa hyphen ili underscore)

    Returns:
        Dictionary sa:
        - primary_impact: najviši impact među issue-ima
        - impact_score: numerički score (1-3)
        - high_count: broj HIGH impact issue-a
        - medium_count: broj MEDIUM impact issue-a
        - low_count: broj LOW impact issue-a
    """
    # Mapping od reason codes (hyphen) na issue_ids (underscore)
    REASON_TO_ISSUE = {
        "fetch-error": "fetch_error",
        "non-200": "non_200",
        "not-product-page": "not_product_page",
        "noindex": "noindex",
        "canonical-mismatch": "canonical_mismatch",
        "missing-price": "missing_price",
        "missing-price-critical": "missing_price",
        "missing-schema": "missing_schema",
        "missing-schema-critical": "missing_schema",
        "js-rendered": "js_rendered",
        "js-rendered-high": "js_rendered",
        "js-rendered-medium": "js_rendered",
        "low-content": "low_content",
        "low-score": "low_content",  # Treat low-score as low-content for impact
        "sample-good-score": "low_content",  # Sample = low impact
    }
    
    high_count = 0
    medium_count = 0
    low_count = 0
    
    for issue_id in issues:
        # Convert reason code to issue_id if needed
        normalized_issue = REASON_TO_ISSUE.get(issue_id, issue_id.replace("-", "_"))
        impact = get_issue_impact(normalized_issue)
        if impact == "HIGH":
            high_count += 1
        elif impact == "MEDIUM":
            medium_count += 1
        else:
            low_count += 1
    
    # Primary impact je najviši među issue-ima
    if high_count > 0:
        primary_impact = "HIGH"
        impact_score = 1
    elif medium_count > 0:
        primary_impact = "MEDIUM"
        impact_score = 2
    else:
        primary_impact = "LOW"
        impact_score = 3
    
    return {
        "primary_impact": primary_impact,
        "impact_score": impact_score,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
    }
