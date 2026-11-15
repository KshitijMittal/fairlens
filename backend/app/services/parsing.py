"""Parse, clean and detect (F1-lite, F2-lite for M0). No AI in this step.

Returns a cleaned frame plus the metadata the payload needs. Never retains
rows beyond the caller's request lifetime.
"""
import io
import logging
from typing import BinaryIO

import pandas as pd
from pandas.api.types import is_numeric_dtype

OUTCOME_NAMES = ("decision", "approved", "outcome", "awarded", "shortlisted", "target", "label", "y")
GROUP_NAMES = ("gender", "sex", "ethnicity", "race", "region", "group", "protected")


logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Human-readable parse failure (F1-AC6)."""


def read_csv(raw: bytes) -> tuple[pd.DataFrame, dict]:
    """
    Read a CSV with encoding and delimiter detection.

    Tries utf-8-sig then cp1252. Sniffs delimiter from first 8 KB.
    Returns (frame, metadata) where metadata contains encoding, delimiter, etc.
    """
    # Try encodings in order
    encodings = ["utf-8-sig", "cp1252"]
    delimiters = [",", ";", "\t"]

    last_error = None

    for encoding in encodings:
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
            continue

        # Skip leading '#' attribution header lines
        lines = text.splitlines()
        while lines and lines[0].lstrip().startswith("#"):
            lines.pop(0)
        if not lines:
            raise ParseError("The file is empty.")

        # Sniff delimiter from first 8 KB
        sample = "\n".join(lines[:100])  # first ~100 lines or 8KB
        delimiter = _sniff_delimiter(sample, delimiters)

        for sep in [delimiter] + [d for d in delimiters if d != delimiter]:
            try:
                frame = pd.read_csv(io.StringIO("\n".join(lines)), sep=sep, engine="python")
            except Exception as exc:
                last_error = exc
                continue

            if frame.shape[1] >= 2:
                meta = {
                    "encoding": encoding,
                    "delimiter": sep,
                    "sniffed_delimiter": delimiter,
                }
                return frame, meta

            last_error = "The file has fewer than two columns."

    raise ParseError(last_error or "Could not read the file as a table.")


def _sniff_delimiter(sample: str, delimiters: list[str]) -> str:
    """Sniff the most likely delimiter from a text sample."""
    best_delim = ","
    best_score = -1

    for delim in delimiters:
        # Count occurrences per line
        lines = sample.splitlines()
        if not lines:
            continue
        counts = [line.count(delim) for line in lines]
        # Consistent delimiter: similar count across lines, at least 1
        if min(counts) >= 1 and max(counts) - min(counts) <= 2:
            score = sum(counts)
            if score > best_score:
                best_score = score
                best_delim = delim

    return best_delim


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


def build_confirmation_card(frame: pd.DataFrame, detection: dict) -> dict:
    """Build the confirmation card from frame and detection results (F2)."""
    outcome_col = detection["outcome"]
    positive_val = detection["positive"]
    group_col = detection["group"]

    # Outcome column info
    outcome_values = frame[outcome_col].astype(str).str.lower().value_counts()
    positive_count = int(outcome_values.get(positive_val, 0))
    total_rows = len(frame)

    # Group column info
    groups = frame[group_col].astype(str).value_counts()
    group_values = [
        {"label": str(label), "n": int(count)}
        for label, count in groups.items()
    ]

    # Factor columns (other categoricals with 2-10 unique values)
    factor_columns = []
    for c in frame.columns:
        if c in (outcome_col, group_col):
            continue
        if not is_numeric_dtype(frame[c]):
            n = frame[c].nunique(dropna=True)
            if 2 <= n <= 10:
                factor_columns.append(c)

    # Age banding is offered when an age column is present.
    age_col = next(
        (c for c in ("age", "age_years") if c in frame.columns and is_numeric_dtype(frame[c])),
        None,
    )
    age_bands = []
    if age_col:
        min_age = int(frame[age_col].min())
        max_age = int(frame[age_col].max())
        start = (min_age // 10) * 10
        for band_start in range(start, max_age + 10, 10):
            band_end = band_start + 9
            mask = (frame[age_col] >= band_start) & (frame[age_col] <= band_end)
            n = int(mask.sum())
            if n > 0:
                pos = int((frame.loc[mask, outcome_col].astype(str).str.lower() == positive_val).sum())
                age_bands.append({"band": f"{band_start}-{band_end}", "n": n, "positives": pos})

    # Warnings
    warnings = []
    # Single-value demographic check (value_counts is indexed by label)
    if len(groups) == 1:
        warnings.append({
            "code": "single_value_demographic",
            "message": f"The demographic column '{group_col}' has only one value. Fairness analysis requires at least two groups."
        })
    # Minority group too small
    for label, count in groups.items():
        if count < 30:
            warnings.append({
                "code": "group_too_small",
                "message": f"Group '{label}' has only {count} rows. Results may be unreliable."
            })
            break

    return {
        "outcome": {
            "column": outcome_col,
            "positive_value": positive_val,
            "positive_count": positive_count,
            "total_rows": total_rows,
        },
        "groups": {
            "column": group_col,
            "values": group_values,
        },
        "age_banding": {
            "available": age_col is not None,
            "column": age_col,
            "bands": age_bands,
        },
        "factor_columns": factor_columns,
        "warnings": warnings,
    }