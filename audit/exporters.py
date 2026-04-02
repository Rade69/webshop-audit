import json
import os

import pandas as pd


def _ensure_dir(path: str) -> None:
    """Create parent directory for *path* if it does not already exist."""
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


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
    _ensure_dir(path)
    _prepare_df_for_export(df).to_csv(path, index=False, encoding="utf-8-sig")


def export_json_summary(summary: dict, path: str) -> None:
    """Saves a dict as a formatted JSON file."""
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)


def export_errors(errors: list[dict], path: str) -> None:
    """Saves a list of error dicts to errors.csv."""
    _ensure_dir(path)
    if not errors:
        pd.DataFrame(columns=["url", "error", "status_code"]).to_csv(
            path, index=False, encoding="utf-8-sig"
        )
        return
    pd.DataFrame(errors).to_csv(path, index=False, encoding="utf-8-sig")


def export_run_diff_summary(summary: dict, path: str) -> None:
    """Saves run diff summary dict as a formatted JSON file."""
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)


def export_run_diff_urls(df: pd.DataFrame, path: str) -> None:
    """Saves run diff URL DataFrame to CSV."""
    _ensure_dir(path)
    # No bool conversion needed - diff DF is already prepared
    df.to_csv(path, index=False, encoding="utf-8-sig")


def export_run_diff_categories(df: pd.DataFrame, path: str) -> None:
    """Saves run diff category DataFrame to CSV."""
    _ensure_dir(path)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def export_issue_summary(df: pd.DataFrame, path: str) -> None:
    """Saves issue summary DataFrame to CSV."""
    _ensure_dir(path)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def export_issue_to_urls(df: pd.DataFrame, path: str) -> None:
    """Saves issue-to-URLs mapping DataFrame to CSV."""
    _ensure_dir(path)
    df.to_csv(path, index=False, encoding="utf-8-sig")
