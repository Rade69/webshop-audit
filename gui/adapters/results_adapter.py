"""
Adapter layer for results data.

This module provides an adapter interface that decouples the GUI from
the underlying data structure, allowing for easier maintenance and
future changes to the data model.
"""

from typing import Dict, Any, List, Optional, Union
import pandas as pd


class ResultsAdapter:
    """
    Adapter for results data that provides a stable interface
    for the GUI regardless of underlying data structure changes.
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize adapter with data.
        
        Args:
            data: DataFrame containing audit results
        """
        self._data = data
        self._column_mapping = self._create_column_mapping()
    
    def _create_column_mapping(self) -> Dict[str, str]:
        """
        Create mapping from GUI field names to actual column names.
        
        This centralizes all column name references and makes it easy
        to adapt to changes in the data model.
        """
        return {
            # Basic page info
            'url': 'url',
            'title': 'title',
            'h1': 'h1',
            'canonical': 'canonical',
            'robots_meta': 'robots_meta',
            
            # Scores
            'catalog_score': 'catalog_score',
            'machine_score': 'machine_score',
            'commerce_score': 'commerce_score',
            'overall_score': 'overall_score',
            
            # Schema fields
            'schema_product_present': 'schema_product_present',
            'schema_offer_present': 'schema_offer_present',
            'schema_price': 'schema_price',
            'schema_currency': 'schema_currency',
            'schema_availability': 'schema_availability',
            'schema_sku': 'schema_sku',
            'schema_gtin': 'schema_gtin',
            'schema_brand': 'schema_brand',
            
            # HTML signals
            'html_price_text': 'html_price_text',
            'shipping_signal': 'shipping_signal',
            'returns_signal': 'returns_signal',
            'image_count': 'image_count',
            'visible_text_length': 'visible_text_length',
            
            # Flags and status
            'flag_js_rendered': 'flag_js_rendered',
            'flag_noindex': 'flag_noindex',
            'flag_canonical_mismatch': 'flag_canonical_mismatch',
            'suspicious_price_missing': 'suspicious_price_missing',
            'suspicious_schema_missing': 'suspicious_schema_missing',
            'review_status': 'review_status',
            'candidate': 'candidate',
            'is_likely_product_page': 'is_likely_product_page',
            
            # Additional fields
            'breadcrumb_text': 'breadcrumb_text',
            'indexability_flags': 'indexability_flags',
            'is_likely_js_rendered': 'is_likely_js_rendered',
        }
    
    def get_column(self, field_name: str) -> str:
        """
        Get actual column name for a GUI field.
        
        Args:
            field_name: GUI field name
            
        Returns:
            Actual column name in the DataFrame
        """
        return self._column_mapping.get(field_name, field_name)
    
    def get_value(self, row: Dict[str, Any], field_name: str, default: Any = None) -> Any:
        """
        Get value from a row for a specific field.
        
        Args:
            row: Row data as dictionary
            field_name: GUI field name
            default: Default value if field not found
            
        Returns:
            Field value or default
        """
        col_name = self.get_column(field_name)
        return row.get(col_name, default)
    
    def get_formatted_value(self, row: Dict[str, Any], field_name: str) -> str:
        """
        Get formatted value for display in GUI.
        
        Args:
            row: Row data as dictionary
            field_name: GUI field name
            
        Returns:
            Formatted string for display
        """
        value = self.get_value(row, field_name)
        
        # Handle None/NaN
        if value is None:
            return "-"
        
        # Handle pandas NaN
        try:
            import math
            if isinstance(value, float) and math.isnan(value):
                return "-"
        except Exception:
            pass
        
        # Handle boolean values
        if isinstance(value, bool):
            return "Da" if value else "Ne"
        
        # Handle numeric values
        if isinstance(value, (int, float)):
            return str(value)
        
        # Handle strings
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.lower() in ['nan', 'none', 'null', '']:
                return "-"
            return stripped
        
        # Default string conversion
        return str(value)
    
    def get_flags_list(self, row: Dict[str, Any]) -> List[str]:
        """
        Get list of flags for a row.
        
        Args:
            row: Row data as dictionary
            
        Returns:
            List of flag strings
        """
        flags = []
        
        # JavaScript rendering flag
        if self.get_value(row, 'flag_js_rendered', False):
            flags.append("JS")
        
        # Noindex flag
        if self.get_value(row, 'flag_noindex', False):
            flags.append("noindex")
        
        # Canonical mismatch flag
        if self.get_value(row, 'flag_canonical_mismatch', False):
            flags.append("no-canonical")
        
        # Missing price flag
        if self.get_value(row, 'suspicious_price_missing', False):
            flags.append("no-price")
        
        # Missing schema flag
        if self.get_value(row, 'suspicious_schema_missing', False):
            flags.append("no-schema")
        
        return flags
    
    def get_detailed_flags_list(self, row: Dict[str, Any]) -> List[str]:
        """
        Get detailed flags list for display in details panel.
        
        Args:
            row: Row data as dictionary
            
        Returns:
            List of detailed flag descriptions
        """
        flags = []
        
        # JavaScript rendering
        if self.get_value(row, 'is_likely_js_rendered', False):
            flags.append("JS renderovano")
        
        # Noindex from indexability flags
        idx_flags = self.get_formatted_value(row, 'indexability_flags')
        if "noindex" in idx_flags.lower():
            flags.append("Noindex")
        
        # Canonical issues
        if "canonical" in idx_flags.lower():
            flags.append("Canonical mismatch")
        
        # Missing schema
        if not self.get_value(row, 'schema_product_present', False):
            flags.append("Nema sheme")
        
        # Missing price in schema
        schema_price = self.get_formatted_value(row, 'schema_price')
        if schema_price == "-":
            flags.append("Nema cijene u schema")
        
        return flags
    
    def get_row_background_color(self, row: Dict[str, Any]) -> Optional[str]:
        """
        Get background color for a row based on issues.
        
        Args:
            row: Row data as dictionary
            
        Returns:
            Color string or None
        """
        has_critical = (
            self.get_value(row, 'flag_noindex', False) or
            (self.get_value(row, 'suspicious_price_missing', False) and 
             self.get_value(row, 'suspicious_schema_missing', False))
        )
        
        has_warning = (
            self.get_value(row, 'flag_js_rendered', False) or
            self.get_value(row, 'flag_canonical_mismatch', False)
        )
        
        if has_critical:
            return "#ffebee"  # Light red
        elif has_warning:
            return "#fff8e1"  # Light yellow
        
        return None
    
    def get_categories(self) -> List[str]:
        """
        Get unique categories from breadcrumb_text.
        
        Returns:
            List of unique category strings
        """
        if 'breadcrumb_text' in self._data.columns:
            categories = self._data['breadcrumb_text'].dropna().unique()
            return sorted([str(cat) for cat in categories if str(cat).strip()])
        return []
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Convert data to list of dictionaries for table model.
        
        Returns:
            List of row dictionaries
        """
        return self._data.to_dict('records')
    
    def filter_data(self, 
                   min_score: int = 0,
                   max_score: int = 100,
                   missing_schema: bool = False,
                   missing_price: bool = False,
                   noindex: bool = False,
                   canonical_mismatch: bool = False,
                   shortlist_only: bool = False,
                   show_non_product: bool = True,
                   search_text: str = "",
                   category: str = "") -> pd.DataFrame:
        """
        Filter data based on criteria.
        
        Args:
            min_score: Minimum overall score
            max_score: Maximum overall score
            missing_schema: Filter for missing schema
            missing_price: Filter for missing price
            noindex: Filter for noindex pages
            canonical_mismatch: Filter for canonical mismatch
            shortlist_only: Filter for shortlist only
            show_non_product: Show non-product pages
            search_text: Search text
            category: Category filter
            
        Returns:
            Filtered DataFrame
        """
        df = self._data.copy()
        
        # Score filter
        df = df[(df['overall_score'] >= min_score) & (df['overall_score'] <= max_score)]
        
        # Missing schema filter
        if missing_schema:
            df = df[~df['schema_product_present']]
        
        # Missing price filter
        if missing_price:
            df = df[~(df['html_price_text'].notna() | df['schema_price'].notna())]
        
        # Noindex filter
        if noindex:
            df = df[df['flag_noindex']]
        
        # Canonical issues filter
        if canonical_mismatch:
            df = df[df['flag_canonical_mismatch']]
        
        # Shortlist only filter
        if shortlist_only:
            df = df[df['candidate']]
        
        # Non-product filter
        if not show_non_product:
            df = df[df['is_likely_product_page']]
        
        # Category filter
        if category:
            df = df[df['breadcrumb_text'].str.contains(category, na=False)]
        
        # Search filter
        if search_text:
            search_lower = search_text.lower()
            mask = (
                df['url'].str.lower().str.contains(search_lower, na=False) |
                df['title'].str.lower().str.contains(search_lower, na=False) |
                df['schema_sku'].str.lower().str.contains(search_lower, na=False) |
                df['schema_gtin'].str.lower().str.contains(search_lower, na=False)
            )
            df = df[mask]
        
        return df
