"""
Display adapters for converting domain data to view-friendly formats.

Responsibility: Transform canonical domain data into display-ready formats
for GUI tabs. This layer should contain ONLY display logic, not business logic.
"""

from typing import Any, Dict, List, Optional
import pandas as pd


class ResultsDisplayAdapter:
    """
    Adapter for preparing audit results for display in ResultsTab.
    
    Converts canonical DataFrame rows to display-friendly dictionaries.
    """
    
    @staticmethod
    def prepare_table_row(product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a single product row for display in results table.
        
        Args:
            product: Raw product data from DataFrame
            
        Returns:
            Display-ready dictionary with view-friendly values
        """
        display_row = product.copy()
        
        # Title display
        title = str(product.get("title", "") or product.get("url", "") or "")
        display_row["display_title"] = title[:50] + "..." if len(title) > 50 else title
        
        # Score display (already numeric, just ensure formatting)
        for score_col in ["catalog_score", "machine_score", "commerce_score", "overall_score"]:
            if score_col in display_row:
                val = display_row[score_col]
                if pd.isna(val):
                    display_row[score_col] = "-"
        
        # Flags display
        flags = []
        if product.get("flag_js_rendered"):
            flags.append("JS")
        if product.get("flag_noindex"):
            flags.append("noindex")
        if product.get("flag_canonical_mismatch"):
            flags.append("no-canonical")
        if product.get("suspicious_price_missing"):
            flags.append("no-price")
        if product.get("suspicious_schema_missing"):
            flags.append("no-schema")
        display_row["display_flags"] = ", ".join(flags) if flags else "-"
        
        # Review status (from controller state, not domain)
        display_row["review_status"] = product.get("review_status", "-")
        
        # Background color hint (for table model)
        has_critical = product.get("flag_noindex") or (
            product.get("suspicious_price_missing") and product.get("suspicious_schema_missing")
        )
        has_warning = product.get("flag_js_rendered") or product.get("flag_canonical_mismatch")
        
        display_row["_bg_color_hint"] = "critical" if has_critical else "warning" if has_warning else "normal"
        
        return display_row
    
    @staticmethod
    def prepare_detail_view(product: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare product data for detail panel display.
        
        Args:
            product: Raw product data from DataFrame
            
        Returns:
            Dictionary with display-ready string values for detail panel
        """
        def _format_yn(val) -> str:
            """Format boolean/truthy value to Da/Ne."""
            if val is None:
                return "Ne"
            try:
                import math
                if isinstance(val, float) and math.isnan(val):
                    return "Ne"
            except Exception:
                pass
            return "Da" if val else "Ne"
        
        def _format_val(key, default="-") -> str:
            """Format value with NaN/None handling."""
            v = product.get(key)
            if v is None:
                return default
            try:
                import math
                if isinstance(v, float) and math.isnan(v):
                    return default
            except Exception:
                pass
            s = str(v).strip()
            return s if s and s.lower() != "nan" else default
        
        details = {}
        
        # Page info
        details["url"] = product.get("url", "-")
        details["title"] = _format_val("title")
        details["h1"] = _format_val("h1")
        details["canonical"] = _format_val("canonical")
        details["robots"] = _format_val("robots_meta")
        
        # Schema
        details["schema_product"] = _format_yn(product.get("schema_product_present"))
        details["schema_offer"] = _format_yn(product.get("schema_offer_present"))
        details["price_schema"] = _format_val("schema_price", "nije pronađeno")
        details["currency"] = _format_val("schema_currency")
        details["availability"] = _format_val("schema_availability")
        details["sku"] = _format_val("schema_sku")
        details["gtin"] = _format_val("schema_gtin")
        details["brand"] = _format_val("schema_brand")
        
        # Signals
        details["price_html"] = _format_val("html_price_text", "nije pronađeno")
        details["shipping"] = _format_yn(product.get("shipping_signal"))
        details["returns"] = _format_yn(product.get("returns_signal"))
        details["images"] = _format_val("image_count", "0")
        details["text_length"] = _format_val("visible_text_length", "0")
        
        # Flags summary
        flags = []
        if product.get("is_likely_js_rendered"):
            flags.append("JS renderovano")
        
        idx_flags = _format_val("indexability_flags", "")
        if "noindex" in idx_flags.lower():
            flags.append("Noindex")
        if "canonical" in idx_flags.lower():
            flags.append("Canonical mismatch")
        if not product.get("schema_product_present"):
            flags.append("Nema sheme")
        if not product.get("schema_price") and _format_val("schema_price", "") == "-":
            flags.append("Nema cijene u schema")
        
        details["flags_summary"] = ", ".join(flags) if flags else "Nema"
        
        return details


class ReviewDisplayAdapter:
    """
    Adapter for preparing review candidates for display in ReviewQueueTab.
    
    Converts canonical candidate data to display-friendly formats.
    """
    
    # Static mappings for display
    SEVERITY_MAP = {
        "CRITICAL": "KRITIČNO",
        "HIGH": "VISOKO",
        "MEDIUM": "SREDNJE",
        "LOW": "NISKO"
    }
    
    REASON_MAP = {
        "fetch-error": "Fetch greška",
        "non-200": "Status nije 200",
        "not-product-page": "Nije produktna stranica",
        "js-rendered-high": "JS render (visok rizik)",
        "js-rendered-medium": "JS render (srednji rizik)",
        "js-rendered": "JS render",
        "noindex": "Noindex",
        "canonical-mismatch": "Canonical mismatch",
        "missing-price-critical": "Nema cijene (kritično)",
        "missing-schema-critical": "Nema sheme (kritično)",
        "missing-price": "Nema cijene",
        "missing-schema": "Nema sheme",
        "low-content": "Malo sadržaja",
        "low-score": "Nizak score",
        "sample-good-score": "Uzorak (dobar score)",
    }
    
    @staticmethod
    def prepare_table_row(candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a single candidate row for display in review table.
        
        Args:
            candidate: Raw candidate data
            
        Returns:
            Display-ready dictionary with view-friendly values
        """
        display_row = candidate.copy()
        
        # URL/Title display
        url = str(candidate.get("url", "") or "")
        title = str(candidate.get("title", "") or "")
        if title:
            display_row["display_url_title"] = title[:40] + "..." if len(title) > 40 else title
        else:
            display_row["display_url_title"] = url[:40] + "..." if len(url) > 40 else url
        
        # Severity display
        severity = candidate.get("severity", "")
        display_row["display_severity"] = ReviewDisplayAdapter.SEVERITY_MAP.get(severity, severity)
        
        # Reasons display
        reasons = candidate.get("reasons", "")
        display_row["display_reasons"] = ReviewDisplayAdapter._format_reasons(reasons)
        
        # Score display
        score = candidate.get("overall_score", "-")
        if pd.isna(score):
            display_row["overall_score"] = "-"
        
        # Status and note (from controller, not domain)
        display_row["status"] = candidate.get("status", "pending")
        display_row["has_note"] = "✓" if candidate.get("note") else "-"
        
        # Background color hint (for table model)
        severity = candidate.get("severity", "")
        if severity == "CRITICAL":
            display_row["_bg_color_hint"] = "critical"
        elif severity == "HIGH":
            display_row["_bg_color_hint"] = "high"
        elif severity == "MEDIUM":
            display_row["_bg_color_hint"] = "medium"
        elif severity == "LOW":
            display_row["_bg_color_hint"] = "low"
        else:
            # Fallback to status
            status = candidate.get("status", "pending")
            if status == "needs_fix":
                display_row["_bg_color_hint"] = "needs_fix"
            elif status == "reviewed":
                display_row["_bg_color_hint"] = "reviewed"
            elif status == "fixed":
                display_row["_bg_color_hint"] = "fixed"
            else:
                display_row["_bg_color_hint"] = "pending"
        
        return display_row
    
    @staticmethod
    def prepare_detail_view(candidate: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare candidate data for detail panel display.
        
        Args:
            candidate: Raw candidate data
            
        Returns:
            Dictionary with display-ready string values for detail panel
        """
        details = {}
        
        # Product info
        details["url"] = candidate.get("url", "-")
        details["title"] = str(candidate.get("title", "-"))
        details["score"] = str(candidate.get("overall_score", "-"))
        
        # Severity and reasons
        severity = candidate.get("severity", "")
        reasons = candidate.get("reasons", "")
        
        # Format severity
        severity_display = ReviewDisplayAdapter.SEVERITY_MAP.get(severity, severity)
        
        # Format reasons
        reason_list = []
        if severity_display:
            reason_list.append(f"Prioritet: {severity_display}")
        
        # Handle NaN/None values
        if not pd.isna(reasons) and reasons:
            reasons_str = str(reasons)
            for reason in reasons_str.split(", "):
                if reason in ReviewDisplayAdapter.REASON_MAP:
                    reason_list.append(ReviewDisplayAdapter.REASON_MAP[reason])
                elif reason:
                    reason_list.append(reason)
        
        # Fallback to old flags if new columns not available
        if not reason_list:
            if candidate.get("flag_noindex"):
                reason_list.append("Noindex")
            if candidate.get("flag_canonical_mismatch"):
                reason_list.append("Canonical Mismatch")
            if candidate.get("flag_js_rendered"):
                reason_list.append("JS Rendered")
            if candidate.get("suspicious_schema_missing"):
                reason_list.append("Missing Schema")
            if candidate.get("suspicious_price_missing"):
                reason_list.append("Missing Price")
            if candidate.get("suspicious_low_content"):
                reason_list.append("Low Content")
        
        if candidate.get("added_by") == "manual":
            reason_list.append("Ručno dodato")
        
        details["reasons_summary"] = "\n".join(reason_list) if reason_list else "Kandidat za pregled"
        details["flags"] = ""  # Not used in new format
        
        # Note info (from controller)
        details["note"] = candidate.get("note", "Još nema bilješke.")
        details["note_timestamp"] = candidate.get("note_timestamp", "")
        
        return details
    
    @staticmethod
    def _format_reasons(reasons: Any) -> str:
        """Format reasons for table display (first reason only)."""
        if pd.isna(reasons) or not reasons:
            return "-"
        
        reasons_str = str(reasons)
        if not reasons_str:
            return "-"
        
        # Show first reason only in table
        first_reason = reasons_str.split(", ")[0]
        return ReviewDisplayAdapter.REASON_MAP.get(first_reason, first_reason)