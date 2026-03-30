import json
import os

import pandas as pd


def _prepare_df_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares a DataFrame for CSV export:
    - Converts bool columns to int (1/0) for Excel compatibility.
    """
    df = df.copy()
    bool_cols = df.select_dtypes(include="bool").columns
    if len(bool_cols):
        df[bool_cols] = df[bool_cols].astype(int)
    return df


def export_dataframe_csv(df: pd.DataFrame, path: str) -> None:
    """Saves a DataFrame to CSV. Bool columns are exported as 1/0."""
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    _prepare_df_for_export(df).to_csv(path, index=False, encoding="utf-8-sig")


def export_json_summary(summary: dict, path: str) -> None:
    """Saves a dict as a formatted JSON file."""
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)


def export_errors(errors: list[dict], path: str) -> None:
    """Saves a list of error dicts to errors.csv."""
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    if not errors:
        pd.DataFrame(columns=["url", "error", "status_code"]).to_csv(
            path, index=False, encoding="utf-8-sig"
        )
        return
    pd.DataFrame(errors).to_csv(path, index=False, encoding="utf-8-sig")
