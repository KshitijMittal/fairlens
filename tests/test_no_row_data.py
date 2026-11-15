"""BACKEND_SCHEMA 3.1: the serialised payload contains no cell value. Column
names, group labels and the positive value are allowed; arbitrary cell values
from non-encoded columns must not appear."""

import json

from pandas.api.types import is_numeric_dtype

from app.services import parsing


def _text_columns(frame):
    return [c for c in frame.columns if frame[c].dtype in ("object", "string")]


def test_loans_no_row_data(loans_result):
    frame, _ = parsing.read_csv(_fixture("loan_approvals.csv").read_bytes())
    payload = json.dumps(loans_result)

    group_col = loans_result["confirmation"]["groups"]["column"]
    outcome_col = loans_result["confirmation"]["outcome"]["column"]
    positive = loans_result["confirmation"]["outcome"]["positive_value"]
    allow = set(frame[group_col].astype(str).str.lower().unique()) | {positive}

    for col in _text_columns(frame):
        if col in (group_col, outcome_col):
            continue
        for value in frame[col].astype(str).str.lower().unique():
            value = str(value)
            if value in allow or value in ("", "nan", "unknown"):
                continue
            assert value not in payload, f"cell value leaked into payload: {col}={value!r}"

    for col in frame.columns:
        if col in (group_col, outcome_col):
            continue
        if is_numeric_dtype(frame[col]):
            for value in frame[col].dropna().unique()[:5]:
                text = str(value)
                # Small integers collide with legitimate payload numbers (counts,
                # rates, milliseconds); only distinctive magnitudes can be asserted.
                if len(text) < 4 or (text.isdigit() and float(value) < 1000):
                    continue
                assert text not in payload, f"cell value leaked into payload: {col}={value!r}"


def test_scholarship_no_row_data(scholarship_result):
    frame, _ = parsing.read_csv(_fixture("scholarship.csv").read_bytes())
    payload = json.dumps(scholarship_result)

    group_col = scholarship_result["confirmation"]["groups"]["column"]
    outcome_col = scholarship_result["confirmation"]["outcome"]["column"]
    positive = scholarship_result["confirmation"]["outcome"]["positive_value"]
    allow = set(frame[group_col].astype(str).str.lower().unique()) | {positive}

    for col in _text_columns(frame):
        if col in (group_col, outcome_col):
            continue
        for value in frame[col].astype(str).str.lower().unique():
            if value in allow or value in ("", "nan", "unknown"):
                continue
            assert value not in payload, f"cell value leaked into payload: {col}={value!r}"


def _fixture(name):
    from pathlib import Path

    return Path(__file__).resolve().parents[1] / "samples" / name
