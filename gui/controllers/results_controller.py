"""
Kontroler za Results tab.

Responsibility: Upravljanje prikazom rezultata audit run-a.
Učitava CSV fajlove, upravlja filterima i sortira podatke.
"""
import os
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal as Signal
from typing import Optional

from gui.viewmodels.results_state import ResultsState


class ResultsController(QObject):
    """
    Kontroler za Results tab.

    Odgovornost:
    - Učitavanje rezultata iz CSV fajlova
    - Upravljanje filterima i sortiranjem
    - Prosljeđivanje signala za mark for review
    """

    # Signali
    results_loaded = Signal()
    filter_changed = Signal()
    selection_changed = Signal(dict)
    mark_for_review_requested = Signal(str)  # URL

    def __init__(self):
        super().__init__()
        self._output_dir: Optional[str] = None
        self._state = ResultsState()
        self._df: Optional[pd.DataFrame] = None

    @property
    def state(self) -> ResultsState:
        """Vraća trenutno stanje."""
        return self._state

    @property
    def dataframe(self) -> Optional[pd.DataFrame]:
        """Vraća pandas DataFrame sa rezultatima."""
        return self._df

    def get_output_dir(self) -> Optional[str]:
        """Vraća putanju do output direktorija trenutnih rezultata."""
        return self._output_dir

    def load_results(self, output_dir: str):
        """
        Učitava rezultate iz output direktorijuma.

        Args:
            output_dir: Putanja do output direktorijuma.
        """
        self._output_dir = output_dir
        self._state.output_dir = output_dir
        self._state.status = "loaded"

        # Load products_scored.csv
        csv_path = os.path.join(output_dir, "products_scored.csv")
        if os.path.exists(csv_path):
            self._df = pd.read_csv(csv_path)
            self._state.total_count = len(self._df)
            self._state.filtered_count = len(self._df)

            # Extract categories from breadcrumb column
            if "breadcrumb_text" in self._df.columns:
                categories = set()
                for val in self._df["breadcrumb_text"].dropna():
                    if isinstance(val, str):
                        parts = val.split(" > ")
                        categories.update(parts)
                self._state.categories = sorted(list(categories))

            self.results_loaded.emit()
        else:
            self._df = pd.DataFrame()
            self._state.total_count = 0
            self._state.filtered_count = 0

    def get_filtered_data(self) -> pd.DataFrame:
        """
        Vraća filtrirani DataFrame.

        Returns:
            pd.DataFrame: Filtrirani podaci.
        """
        if self._df is None or self._df.empty:
            return pd.DataFrame()

        df = self._df.copy()

        # Apply filters
        if self._state.filter_category:
            if "breadcrumb_text" in df.columns:
                # Handle NaN values in breadcrumb_text
                breadcrumb_series = df["breadcrumb_text"].fillna("")
                df = df[breadcrumb_series.str.contains(self._state.filter_category, na=False)]

        if self._state.filter_min_score > 0:
            if "overall_score" in df.columns:
                df = df[df["overall_score"] >= self._state.filter_min_score]

        if self._state.filter_max_score < 100:
            if "overall_score" in df.columns:
                df = df[df["overall_score"] <= self._state.filter_max_score]

        if self._state.filter_missing_schema:
            if "schema_product_present" in df.columns:
                df = df[df["schema_product_present"] != True]

        if self._state.filter_missing_price:
            if "html_price_text" in df.columns:
                df = df[df["html_price_text"].isna()]
            if "schema_price" in df.columns:
                df = df[df["schema_price"].isna()]

        if self._state.filter_noindex:
            if "flag_noindex" in df.columns:
                df = df[df["flag_noindex"] == True]

        if self._state.filter_canonical_issues:
            if "flag_canonical_mismatch" in df.columns:
                df = df[df["flag_canonical_mismatch"] == True]

        if self._state.filter_shortlist_only:
            if "candidate" in df.columns:
                df = df[df["candidate"] == True]

        if not self._state.filter_show_non_product:
            if "is_likely_product_page" in df.columns:
                df = df[df["is_likely_product_page"] != False]

        # Search filter
        if self._state.search_text:
            search = self._state.search_text.lower()
            cols_to_search = ["url", "title", "schema_sku", "schema_gtin"]
            mask = pd.Series([False] * len(df), index=df.index)
            for col in cols_to_search:
                if col in df.columns:
                    # Handle NaN values before string operations
                    col_series = df[col].fillna("").astype(str)
                    mask = mask | col_series.str.lower().str.contains(search, na=False)
            df = df[mask]

        self._state.filtered_count = len(df)
        return df

    def set_filter(self, filter_type: str):
        """
        Postavlja filter za prikaz rezultata.

        Args:
            filter_type: Tip filtera
        """
        self._state.current_filter = filter_type
        self.filter_changed.emit()

    def update_filter_state(self, **kwargs):
        """
        Ažurira stanje filtera.

        Args:
            **kwargs: Ključ-vrijednost parovi za ažuriranje.
        """
        for key, value in kwargs.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
        self.filter_changed.emit()

    def select_product(self, product_data: dict):
        """
        Bira proizvod za prikaz detalja.

        Args:
            product_data: Podaci o proizvodu.
        """
        self._state.selected_product = product_data
        self.selection_changed.emit(product_data)

    def get_selected_product(self) -> Optional[dict]:
        """
        Vraća selektovani proizvod.

        Returns:
            Optional[dict]: Podaci o selektovanom proizvodu.
        """
        return self._state.selected_product

    def mark_for_review(self, url: str):
        """
        Signalizira zahtjev za dodavanje u review queue.

        Args:
            url: URL proizvoda.
        """
        # Get full product data from dataframe
        if self._df is not None:
            product_row = self._df[self._df["url"] == url]
            if not product_row.empty:
                product_data = product_row.iloc[0].to_dict()
                self.mark_for_review_requested.emit(url)

    def get_categories(self) -> list[str]:
        """
        Vraća listu dostupnih kategorija.

        Returns:
            list[str]: Lista kategorija.
        """
        return self._state.categories