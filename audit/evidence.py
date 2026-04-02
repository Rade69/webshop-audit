"""
Evidence snapshots module — dokazni paket za audit nalaze.

Ovaj modul pruža strukturirani skup dokaza zašto je alat donio određeni zaključak.
Koristi postojeće extracted podatke — ne duplicira extraction logiku.

Design principles:
- Koristiti postojeće extracted podatke iz ProductAuditRow
- Ne duplicirati extraction logiku
- Fokus na 5-10 najkorisnijih dokaznih signala
- Ljudski čitljiv format
- Ne dumpovati cijeli HTML
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List


@dataclass
class EvidenceSnapshot:
    """
    Evidence snapshot za jednu stranicu.
    
    Sadrži ključne dokazne signale koji objašnjavaju nalaze alata.
    """
    # URL identification
    url: str = ""
    final_url: Optional[str] = None
    
    # HTTP response
    status_code: Optional[int] = None
    fetch_error: Optional[str] = None
    
    # Indexability evidence
    canonical: Optional[str] = None
    robots_meta: Optional[str] = None
    
    # Price evidence
    html_price_text: Optional[str] = None
    schema_price: Optional[str] = None
    schema_price_value: Optional[float] = None
    schema_currency: Optional[str] = None
    
    # Product identification evidence
    schema_product_present: bool = False
    schema_offer_present: bool = False
    schema_sku: Optional[str] = None
    schema_brand: Optional[str] = None
    
    # Content evidence
    breadcrumb_text: Optional[str] = None
    title: Optional[str] = None
    h1: Optional[str] = None
    visible_text_length: int = 0
    
    # Classification
    is_likely_product_page: bool = True
    is_likely_js_rendered: bool = False
    
    @classmethod
    def from_row(cls, row: Any) -> "EvidenceSnapshot":
        """
        Kreira EvidenceSnapshot iz ProductAuditRow ili pandas Series.
        
        Args:
            row: ProductAuditRow dataclass ili pandas Series sa extracted podacima
        
        Returns:
            EvidenceSnapshot instance
        """
        def get_val(key, default=None):
            """Helper to get value from either dict-like or attribute-like object."""
            if hasattr(row, "get"):
                return row.get(key, default)
            return getattr(row, key, default)
        
        return cls(
            url=get_val("url", "") or "",
            final_url=get_val("final_url"),
            status_code=get_val("status_code"),
            fetch_error=get_val("fetch_error"),
            canonical=get_val("canonical"),
            robots_meta=get_val("robots_meta"),
            html_price_text=get_val("html_price_text"),
            schema_price=get_val("schema_price"),
            schema_price_value=get_val("schema_price_value"),
            schema_currency=get_val("schema_currency"),
            schema_product_present=bool(get_val("schema_product_present", False)),
            schema_offer_present=bool(get_val("schema_offer_present", False)),
            schema_sku=get_val("schema_sku"),
            schema_brand=get_val("schema_brand"),
            breadcrumb_text=get_val("breadcrumb_text"),
            title=get_val("title"),
            h1=get_val("h1"),
            visible_text_length=int(get_val("visible_text_length", 0)),
            is_likely_product_page=bool(get_val("is_likely_product_page", True)),
            is_likely_js_rendered=bool(get_val("is_likely_js_rendered", False)),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertuje u dictionary za export."""
        return asdict(self)
    
    def get_evidence_for_finding(self, finding_type: str) -> Dict[str, Any]:
        """
        Vraća relevantne evidence za specifičan nalaz.
        
        Args:
            finding_type: Tip nalaza (npr. "missing-price", "noindex", "canonical-mismatch")
        
        Returns:
            Dictionary sa relevantnim evidence poljima za taj nalaz
        """
        evidence_map = {
            "missing-price": {
                "html_price_text": self.html_price_text,
                "schema_price": self.schema_price,
                "schema_price_value": self.schema_price_value,
                "schema_currency": self.schema_currency,
            },
            "missing-schema": {
                "schema_product_present": self.schema_product_present,
                "schema_offer_present": self.schema_offer_present,
                "schema_sku": self.schema_sku,
                "schema_brand": self.schema_brand,
            },
            "noindex": {
                "robots_meta": self.robots_meta,
            },
            "canonical-mismatch": {
                "canonical": self.canonical,
                "url": self.url,
                "final_url": self.final_url,
            },
            "low-content": {
                "visible_text_length": self.visible_text_length,
                "title": self.title,
                "h1": self.h1,
            },
            "fetch-error": {
                "fetch_error": self.fetch_error,
                "status_code": self.status_code,
            },
            "not-product-page": {
                "is_likely_product_page": self.is_likely_product_page,
                "schema_product_present": self.schema_product_present,
                "html_price_text": self.html_price_text,
                "schema_sku": self.schema_sku,
            },
            "js-rendered": {
                "is_likely_js_rendered": self.is_likely_js_rendered,
            },
        }
        
        return evidence_map.get(finding_type, {})
    
    def get_summary(self) -> List[str]:
        """
        Vraća kratki sažetak evidence u ljudski čitljivom formatu.
        
        Returns:
            List of strings sa ključnim evidence stavkama
        """
        summary = []
        
        # HTTP status
        if self.fetch_error:
            summary.append(f"Greška pri preuzimanju: {self.fetch_error}")
        elif self.status_code:
            if self.status_code == 200:
                summary.append("Status: 200 OK")
            else:
                summary.append(f"Status: {self.status_code}")
        
        # Indexability
        if self.robots_meta and "noindex" in self.robots_meta.lower():
            summary.append(f"Robots: noindex ({self.robots_meta})")
        
        if self.canonical:
            if self.final_url and self.canonical != self.final_url:
                summary.append(f"Canonical različit: {self.canonical}")
            else:
                summary.append(f"Canonical: {self.canonical}")
        
        # Price evidence
        if self.html_price_text:
            summary.append(f"HTML cijena: {self.html_price_text}")
        else:
            summary.append("HTML cijena: nije pronađena")
        
        if self.schema_price:
            summary.append(f"Schema cijena: {self.schema_price} {self.schema_currency or ''}")
        else:
            summary.append("Schema cijena: nije pronađena")
        
        # Schema evidence
        if self.schema_product_present:
            summary.append("Product schema: prisutna")
            if self.schema_sku:
                summary.append(f"SKU: {self.schema_sku}")
            if self.schema_brand:
                summary.append(f"Brand: {self.schema_brand}")
        else:
            summary.append("Product schema: nije prisutna")
        
        # Content evidence
        summary.append(f"Tekst: {self.visible_text_length} znakova")
        
        if self.breadcrumb_text:
            summary.append(f"Breadcrumb: {self.breadcrumb_text}")
        
        # Classification
        if not self.is_likely_product_page:
            summary.append("Klasifikacija: nije produktna stranica")
        
        if self.is_likely_js_rendered:
            summary.append("JS render: detektovan")
        
        return summary


def build_evidence_for_reasons(evidence: EvidenceSnapshot, reasons: List[str]) -> Dict[str, Any]:
    """
    Gradi evidence paket za listu reason code-ova.
    
    Args:
        evidence: EvidenceSnapshot instance
        reasons: Lista reason code-ova
    
    Returns:
        Dictionary sa svim relevantnim evidence za navedene reason-e
    """
    result = {
        "url": evidence.url,
        "findings": {},
    }
    
    for reason in reasons:
        finding_evidence = evidence.get_evidence_for_finding(reason)
        if finding_evidence:
            result["findings"][reason] = finding_evidence
    
    # Dodaj i generalni summary
    result["summary"] = evidence.get_summary()
    
    return result


def format_evidence_for_display(evidence: EvidenceSnapshot, max_width: int = 60) -> str:
    """
    Formatira evidence za tekstualni display (npr. u terminalu ili reportu).
    
    Args:
        evidence: EvidenceSnapshot instance
        max_width: Maksimalna širina linije
    
    Returns:
        Formatirani string za display
    """
    lines = []
    lines.append("=" * max_width)
    lines.append("EVIDENCE SNAPSHOT")
    lines.append("=" * max_width)
    
    # URL
    lines.append(f"URL: {evidence.url[:max_width-6]}..." if len(evidence.url) > max_width-6 else f"URL: {evidence.url}")
    
    # Status
    if evidence.fetch_error:
        lines.append(f"❌ Fetch error: {evidence.fetch_error}")
    else:
        lines.append(f"✓ Status: {evidence.status_code or 'N/A'}")
    
    # Indexability
    if evidence.robots_meta:
        lines.append(f"Robots: {evidence.robots_meta}")
    
    if evidence.canonical:
        lines.append(f"Canonical: {evidence.canonical[:max_width-12]}..." if len(evidence.canonical) > max_width-12 else f"Canonical: {evidence.canonical}")
    
    # Price
    lines.append(f"HTML cijena: {evidence.html_price_text or 'nije pronađena'}")
    lines.append(f"Schema cijena: {evidence.schema_price or 'nije pronađena'} {evidence.schema_currency or ''}")
    
    # Schema
    lines.append(f"Product schema: {'✓' if evidence.schema_product_present else '✗'}")
    if evidence.schema_sku:
        lines.append(f"SKU: {evidence.schema_sku}")
    if evidence.schema_brand:
        lines.append(f"Brand: {evidence.schema_brand}")
    
    # Content
    lines.append(f"Tekst: {evidence.visible_text_length} znakova")
    
    if evidence.breadcrumb_text:
        breadcrumb_display = evidence.breadcrumb_text[:max_width-12] + "..." if len(evidence.breadcrumb_text) > max_width-12 else evidence.breadcrumb_text
        lines.append(f"Breadcrumb: {breadcrumb_display}")
    
    # Classification
    if not evidence.is_likely_product_page:
        lines.append("⚠ Nije produktna stranica")
    
    if evidence.is_likely_js_rendered:
        lines.append("⚠ JS render detektovan")
    
    lines.append("=" * max_width)
    
    return "\n".join(lines)
