"""Parse, clean and detect (F1-lite, F2-lite for M0). No AI in this step.

Returns a cleaned frame plus the metadata the payload needs. Never retains
rows beyond the caller's request lifetime.
"""
import io

import pandas as pd
from pandas.api.types import is_numeric_dtype

OUTCOME_NAMES = ("decision", "approved", "outcome", "awarded", "shortlisted", "target", "label", "y")
GROUP_NAMES = ("gender", "sex", "ethnicity", "race", "region", "group", "protected")


class ParseError(Exception):
    """Human-readable parse failure (F1-AC6)."""


def read_csv(raw: bytes) -> tuple[pd.DataFrame, list[str]]:
    """Read a CSV, skipping the leading '#' attribution header (F11)."""
    lines = raw.decode("utf-8-sig").splitlines()
    while lines and lines[0].lstrip().startswith("#"):
        lines.pop(0)
    if not lines:
        raise ParseError("The file is empty.")
    for sep in (",", ";", "\t"):
        try:
            frame = pd.read_csv(io.StringIO("\n".join(lines)), sep=sep, engine="python")
        except Exception as exc:
            last = f"Could not read the file as a table: {exc}"
            continue
        if frame.shape[1] >= 2:
            return frame
        last = "The file has fewer than two columns."
    raise ParseError(last or "Could not read the file as a table.")


def clean(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Normalise, drop empty columns and exact duplicates, fill blanks (F1-AC5)."""
    originals = list(frame.columns)
    renames = {c: str(c).strip().lower().replace(" ", "_") for c in frame.columns}
    frame = frame.rename(columns=renames)

    empty_columns = [c for c in frame.columns if frame[c].isna().all()]
    frame = frame.drop(columns=empty_columns)
    before = len(frame)
    frame = frame.drop_duplicates().reset_index(drop=True)
    dropped_rows = before - len(frame)

    text_columns = [c for c in frame.columns if not is_numeric_dtype(frame[c])]
    for c in text_columns:
        frame[c] = frame[c].astype(str).str.strip()
        blanks = frame[c].isin(("", "nan", "None"))
        filled = int(blanks.sum())
        if filled:
            frame.loc[blanks, c] = "unknown"

    numeric_columns = [c for c in frame.columns if c not in text_columns]
    imputed = {}
    for c in numeric_columns:
        frame[c] = pd.to_numeric(frame[c], errors="coerce")
        missing = int(frame[c].isna().sum())
        if missing:
            median = float(frame[c].median())
            frame[c] = frame[c].fillna(median)
            imputed[c] = median

    stats = {
        "originals": originals,
        "dropped_empty_columns": empty_columns,
        "dropped_duplicate_rows": dropped_rows,
        "filled_text_cells": sum(int((frame[c] == "unknown").sum()) for c in text_columns),
        "imputed_medians": imputed,
    }
    return frame, stats


def detect(frame: pd.DataFrame) -> dict:
    """Deterministic candidates for the outcome, positive value and group column (F2)."""
    outcome_col, group_col = None, None
    for c in frame.columns:
        if c in OUTCOME_NAMES:
            outcome_col = c
            break
    if outcome_col is None:
        for c in frame.columns:
            n = frame[c].nunique(dropna=True)
            if 2 <= n <= 10 and not is_numeric_dtype(frame[c]):
                outcome_col = c
                break
    for c in frame.columns:
        if c == outcome_col:
            continue
        if c in GROUP_NAMES:
            group_col = c
            break
    if group_col is None:
        for c in frame.columns:
            if c == outcome_col:
                continue
            n = frame[c].nunique(dropna=True)
            if 2 <= n <= 10 and not is_numeric_dtype(frame[c]):
                group_col = c
                break

    if outcome_col is None or group_col is None:
        raise ParseError("Could not detect an outcome column and a group column in this file.")

    counts = frame[outcome_col].str.lower().value_counts()
    positive = str(counts.idxmax())
    return {"outcome": outcome_col, "positive": positive, "group": group_col}
