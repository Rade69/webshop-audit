"""
Adapter layer for review queue data.

This module provides an adapter interface that decouples the GUI from
the underlying data structure for the review queue, allowing for easier
maintenance and localization.
"""

from typing import Dict, Any, List, Optional
import pandas as pd


# Constants for severity and reasons mapping
SEVERITY_MAP = {
    "CRITICAL": "KRITIČNO",
    "HIGH": "VISOKO",
    "MEDIUM": "SREDNJE",
    "LOW": "NISKO"
}

SEVERITY_MAP_REVERSE = {
    "KRITIČNO": "CRITICAL",
    "VISOKO": "HIGH",
    "SREDNJE": "MEDIUM",
    "NISKO": "LOW"
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


class ReviewAdapter:
    """
    Adapter for review queue data that provides a stable interface
    for the GUI regardless of underlying data structure changes.
    """

    def __init__(self, candidates: List[Dict[str, Any]]):
        """
        Initialize adapter with candidates data.

        Args:
            candidates: List of candidate dictionaries
        """
        self._candidates = candidates

    def get_formatted_severity(self, candidate: Dict[str, Any]) -> str:
        """
        Get formatted severity for display.

        Args:
            candidate: Candidate dictionary

        Returns:
            Formatted severity string (in Serbian)
        """
        severity = candidate.get("severity", "")
        return SEVERITY_MAP.get(severity, severity)

    def get_formatted_reasons(self, candidate: Dict[str, Any]) -> str:
        """
        Get formatted reasons for display in table.

        Args:
            candidate: Candidate dictionary

        Returns:
            First formatted reason for table display
        """
        reasons = candidate.get("reasons", "")

        # Handle NaN/None values
        if pd.isna(reasons) or not reasons:
            return "-"

        reasons_str = str(reasons)
        if not reasons_str:
            return "-"

        # Show first reason only in table
        first_reason = reasons_str.split(", ")[0]
        return REASON_MAP.get(first_reason, first_reason)

    def get_all_formatted_reasons(self, candidate: Dict[str, Any]) -> List[str]:
        """
        Get all formatted reasons for details panel.

        Args:
            candidate: Candidate dictionary

        Returns:
            List of formatted reason strings
        """
        reasons = candidate.get("reasons", "")
        reason_list = []

        # Handle NaN/None values
        if not pd.isna(reasons) and reasons:
            reasons_str = str(reasons)
            for reason in reasons_str.split(", "):
                formatted = REASON_MAP.get(reason, reason)
                reason_list.append(formatted)

        return reason_list

    def get_row_color(self, candidate: Dict[str, Any]) -> Optional[str]:
        """
        Get background color for a row based on severity/status.

        Args:
            candidate: Candidate dictionary

        Returns:
            Color hex string or None
        """
        # First priority: severity color
        severity = candidate.get("severity", "")
        if severity == "CRITICAL":
            return "#ffebee"  # Light red
        elif severity == "HIGH":
            return "#fff3cd"  # Light orange
        elif severity == "MEDIUM":
            return "#fff8e1"  # Light yellow
        elif severity == "LOW":
            return "#e3f2fd"  # Light blue

        # Fallback: status color
        status = candidate.get("status", "pending")
        if status == "needs_fix":
            return "#ffebee"  # Light red
        elif status == "reviewed":
            return "#e8f5e9"  # Light green
        elif status == "fixed":
            return "#e3f2fd"  # Light blue
        elif status == "pending":
            return "#fafafa"  # Light gray

        return None

    def get_display_title(self, candidate: Dict[str, Any], max_length: int = 40) -> str:
        """
        Get display title for table cell.

        Args:
            candidate: Candidate dictionary
            max_length: Maximum length for display

        Returns:
            Truncated title or URL
        """
        url = str(candidate.get("url", "") or "")
        title = str(candidate.get("title", "") or "")
        if title:
            return title[:max_length] + "..." if len(title) > max_length else title
        return url[:max_length] + "..." if len(url) > max_length else url

    def get_display_reason_for_details(self, candidate: Dict[str, Any]) -> str:
        """
        Get formatted reason for details panel with priority info.

        Args:
            candidate: Candidate dictionary

        Returns:
            Formatted reason string with priority
        """
        reason_list = []

        # Add priority
        severity = self.get_formatted_severity(candidate)
        if severity:
            reason_list.append(f"Prioritet: {severity}")

        # Add all reasons
        reasons = self.get_all_formatted_reasons(candidate)
        reason_list.extend(reasons)

        if not reason_list:
            return "-"

        return "\n".join(reason_list)

    def get_explanation(self, candidate: Dict[str, Any]) -> str:
        """
        Get human-readable explanation for details panel.

        Args:
            candidate: Candidate dictionary

        Returns:
            Formatted explanation string
        """
        explanation = candidate.get("explanation", "")
        
        # Handle NaN/None/empty values
        if pd.isna(explanation) or not explanation:
            return "-"
        
        return str(explanation)

    def get_evidence_summary(self, candidate: Dict[str, Any]) -> str:
        """
        Get evidence summary for details panel.

        Args:
            candidate: Candidate dictionary

        Returns:
            Formatted evidence summary string
        """
        evidence_summary = candidate.get("evidence_summary", "")
        
        # Handle NaN/None/empty values
        if pd.isna(evidence_summary) or not evidence_summary:
            return "-"
        
        # Split by " | " and format as bullet points
        parts = evidence_summary.split(" | ")
        return "\n".join(f"• {part}" for part in parts)

    def get_full_evidence(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get full evidence snapshot for details panel.

        Args:
            candidate: Candidate dictionary

        Returns:
            Dictionary with full evidence data
        """
        return candidate.get("evidence", {})

    def is_sample_candidate(self, candidate: Dict[str, Any]) -> bool:
        """
        Check if candidate is a sample (good score) rather than a real issue.

        Args:
            candidate: Candidate dictionary

        Returns:
            True if this is a sample candidate
        """
        is_sample = candidate.get("is_sample", False)
        return bool(is_sample)

    def get_fix_impact(self, candidate: Dict[str, Any]) -> str:
        """
        Get fix impact level for candidate.

        Args:
            candidate: Candidate dictionary

        Returns:
            Formatted impact string (HIGH/MEDIUM/LOW)
        """
        impact = candidate.get("fix_impact", "")
        
        # Handle NaN/None/empty values
        if pd.isna(impact) or not impact:
            return "-"
        
        # Map to Serbian
        impact_map = {
            "HIGH": "VISOK",
            "MEDIUM": "SREDNJI",
            "LOW": "NIZAK",
        }
        return impact_map.get(impact, impact)

    def get_impact_color(self, candidate: Dict[str, Any]) -> Optional[str]:
        """
        Get color for impact level.

        Args:
            candidate: Candidate dictionary

        Returns:
            Color hex string or None
        """
        impact = candidate.get("fix_impact", "")
        
        colors = {
            "HIGH": "#ffebee",  # Light red
            "MEDIUM": "#fff3cd",  # Light orange
            "LOW": "#e8f5e9",  # Light green
        }
        return colors.get(impact)

    @staticmethod
    def get_severity_color(severity: str) -> Optional[str]:
        """
        Get color for a severity level.

        Args:
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)

        Returns:
            Color hex string or None
        """
        colors = {
            "CRITICAL": "#ffebee",
            "HIGH": "#fff3cd",
            "MEDIUM": "#fff8e1",
            "LOW": "#e3f2fd",
        }
        return colors.get(severity)

    @staticmethod
    def get_status_color(status: str) -> Optional[str]:
        """
        Get color for a status.

        Args:
            status: Status (pending, reviewed, needs_fix, fixed)

        Returns:
            Color hex string or None
        """
        colors = {
            "pending": "#fafafa",
            "reviewed": "#e8f5e9",
            "needs_fix": "#ffebee",
            "fixed": "#e3f2fd",
        }
        return colors.get(status)