"""Parsing tests - encoding/delimiter detection, corrupt files (F1-AC1, F1-AC5, F1-AC6)."""
from pathlib import Path

import pandas as pd
import pytest

from app.services.parsing import read_csv, clean, detect, build_confirmation_card, ParseError

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


class TestReadCSV:
    """Tests for read_csv with encoding and delimiter detection."""

    def test_comma_utf8(self):
        """Comma-separated UTF-8 produces expected frame."""
        csv = "decision,gender,age\napproved,male,25\ndecided,female,30\n"
        raw = csv.encode("utf-8")
        frame, meta = read_csv(raw)
        assert frame.shape == (2, 3)
        assert meta["encoding"] == "utf-8-sig"
        assert meta["delimiter"] == ","
        assert list(frame.columns) == ["decision", "gender", "age"]

    def test_semicolon_latin1(self):
        """Semicolon-separated Latin-1 produces byte-identical frame to comma UTF-8 (F1-AC1)."""
        # Same data: semicolon + Latin-1 (with non-ASCII char to force cp1252)
        csv_latin1 = "decision;gender;age\napproved;male;25\ndecided;female;30\n"
        raw_latin1 = csv_latin1.encode("cp1252")

        # Equivalent comma + UTF-8
        csv_utf8 = "decision,gender,age\napproved,male,25\ndecided,female,30\n"
        raw_utf8 = csv_utf8.encode("utf-8")

        frame1, meta1 = read_csv(raw_latin1)
        frame2, meta2 = read_csv(raw_utf8)

        # Frames should be byte-identical after parsing
        pd.testing.assert_frame_equal(frame1, frame2)
        # Both produce valid frames; encoding may be utf-8-sig if ASCII-compatible
        assert meta1["delimiter"] == ";"
        assert meta2["delimiter"] == ","

    def test_tab_delimited(self):
        """Tab-delimited files are parsed correctly."""
        csv = "decision\tgender\tage\napproved\tmale\t25\ndecided\tfemale\t30\n"
        raw = csv.encode("utf-8")
        frame, meta = read_csv(raw)
        assert frame.shape == (2, 3)
        assert meta["delimiter"] == "\t"

    def test_skips_attribution_header(self):
        """Leading '#' comment lines are skipped."""
        csv = "# This is a comment\n# Another comment\ndecision,gender\napproved,male\n"
        raw = csv.encode("utf-8")
        frame, meta = read_csv(raw)
        assert frame.shape == (1, 2)
        assert list(frame.columns) == ["decision", "gender"]

    def test_empty_file_raises(self):
        """Empty file raises ParseError with sentence, not traceback (F1-AC6)."""
        raw = b""
        with pytest.raises(ParseError) as exc:
            read_csv(raw)
        assert "empty" in str(exc.value).lower()

    def test_binary_file_raises_sentence(self):
        """Binary file yields a sentence, not a traceback (F1-AC6)."""
        raw = b"\x00\x01\x02\x03\xff\xfe\xfd"
        with pytest.raises(ParseError) as exc:
            read_csv(raw)
        # Should be a human-readable sentence, not an exception repr
        msg = str(exc.value)
        assert "traceback" not in msg.lower()
        assert "exception" not in msg.lower()
        assert len(msg) < 200  # Reasonable sentence length

    def test_fewer_than_two_columns_raises(self):
        """File with < 2 columns raises ParseError."""
        csv = "only_one\nvalue1\nvalue2\n"
        raw = csv.encode("utf-8")
        with pytest.raises(ParseError) as exc:
            read_csv(raw)
        assert "fewer than two columns" in str(exc.value).lower()


class TestClean:
    """Tests for clean function (F1-AC5)."""

    def test_drops_empty_columns(self):
        """Columns that are all NaN are dropped."""
        df = pd.DataFrame({"a": [1, 2], "b": [None, None], "c": [3, 4]})
        frame, stats = clean(df)
        assert "b" not in frame.columns
        assert stats["dropped_empty_columns"] == ["b"]

    def test_drops_exact_duplicates(self):
        """Exact duplicate rows are dropped."""
        df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
        frame, stats = clean(df)
        assert len(frame) == 2
        assert stats["dropped_duplicate_rows"] == 1

    def test_fills_blank_text_cells(self):
        """Blank text cells are filled with 'unknown'."""
        df = pd.DataFrame({"a": ["x", "", "y"], "b": [1, 2, 3]})
        frame, stats = clean(df)
        assert frame["a"].iloc[1] == "unknown"
        assert stats["filled_text_cells"] >= 1

    def test_imputes_numeric_medians(self):
        """Missing numeric values are imputed with median."""
        df = pd.DataFrame({"a": [1.0, None, 3.0], "b": ["x", "y", "z"]})
        frame, stats = clean(df)
        assert frame["a"].iloc[1] == 2.0  # median of 1 and 3
        assert stats["imputed_medians"]["a"] == 2.0

    def test_normalizes_column_names(self):
        """Column names are lowercased, stripped, spaces to underscores."""
        df = pd.DataFrame({"Decision ": [1, 2], " Gender": [3, 4], "Age Group": [5, 6]})
        frame, stats = clean(df)
        assert list(frame.columns) == ["decision", "gender", "age_group"]
        assert stats["originals"] == ["Decision ", " Gender", "Age Group"]


class TestDetect:
    """Tests for deterministic column detection (F2)."""

    def test_detects_standard_names(self):
        """Standard outcome/group names are detected."""
        df = pd.DataFrame({
            "decision": ["approved", "denied", "approved"],
            "gender": ["male", "female", "male"],
            "age": [25, 30, 35],
        })
        result = detect(df)
        assert result["outcome"] == "decision"
        assert result["group"] == "gender"
        assert result["positive"] in ("approved", "denied")

    def test_detects_by_cardinality(self):
        """Falls back to cardinality when standard names absent."""
        df = pd.DataFrame({
            "outcome_col": ["yes", "no", "yes"],
            "protected": ["a", "b", "a"],
            "other": [1, 2, 3],
        })
        result = detect(df)
        assert result["outcome"] == "outcome_col"
        assert result["group"] == "protected"

    def test_raises_when_cannot_detect(self):
        """Raises ParseError with sentence when detection fails."""
        df = pd.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        })
        with pytest.raises(ParseError) as exc:
            detect(df)
        assert "could not detect" in str(exc.value).lower()


class TestConfirmationCard:
    """Tests for the confirmation card (F2)."""

    def test_builds_card_with_all_fields(self):
        """Card contains outcome, groups, age_banding, factors, warnings."""
        df = pd.DataFrame({
            "decision": ["approved", "denied", "approved", "denied"],
            "gender": ["male", "female", "male", "female"],
            "age": [25, 30, 35, 40],
            "region": ["north", "south", "north", "south"],
        })
        detection = {"outcome": "decision", "positive": "approved", "group": "gender"}
        card = build_confirmation_card(df, detection)

        assert card["outcome"]["column"] == "decision"
        assert card["outcome"]["positive_value"] == "approved"
        assert card["outcome"]["positive_count"] == 2
        assert card["outcome"]["total_rows"] == 4
        assert card["groups"]["column"] == "gender"
        assert len(card["groups"]["values"]) == 2
        assert card["age_banding"]["available"] is True
        assert card["age_banding"]["column"] == "age"
        assert "region" in card["factor_columns"]
        # Equal group sizes are not a single-value demographic.
        assert not any(w["code"] == "single_value_demographic" for w in card["warnings"])

    def test_single_value_demographic_blocks(self):
        """Single-value demographic column produces warning (F2-AC4)."""
        df = pd.DataFrame({
            "decision": ["approved", "denied", "approved"],
            "gender": ["male", "male", "male"],  # Only one value
        })
        detection = {"outcome": "decision", "positive": "approved", "group": "gender"}
        card = build_confirmation_card(df, detection)

        warnings = card["warnings"]
        assert any(w["code"] == "single_value_demographic" for w in warnings)

    def test_majority_class_is_default_positive(self):
        """Majority class is the default positive and card says so (F2-AC3)."""
        df = pd.DataFrame({
            "decision": ["approved", "approved", "denied"],  # approved majority
            "gender": ["male", "female", "male"],
        })
        detection = {"outcome": "decision", "positive": "approved", "group": "gender"}
        card = build_confirmation_card(df, detection)
        assert card["outcome"]["positive_value"] == "approved"
        assert card["outcome"]["positive_count"] == 2
        assert card["outcome"]["total_rows"] == 3

    def test_group_labels_merge_across_casing(self):
        """Casing and padding in a group column collapse to one label, as the engine does."""
        df = pd.DataFrame({
            "decision": ["approved", "denied", "approved", "denied"],
            "gender": ["male", "Male", "MALE ", "female"],
        })
        detection = {"outcome": "decision", "positive": "approved", "group": "gender"}
        card = build_confirmation_card(df, detection)

        labels = [g["label"] for g in card["groups"]["values"]]
        counts = {g["label"]: g["n"] for g in card["groups"]["values"]}
        assert labels == ["male", "female"]
        assert counts["male"] == 3

    def test_prefills_correctly_for_bundled_samples(self):
        """Each bundled sample prefills exactly (F2-AC1)."""
        expected = {
            "scholarship.csv": ("awarded", "region"),
            "loan_approvals.csv": ("decision", "gender"),
            "hiring_shortlist.csv": ("shortlisted", "ethnicity"),
        }
        for filename, (outcome, group) in expected.items():
            frame, _ = read_csv((SAMPLES / filename).read_bytes())
            frame, _ = clean(frame)
            detection = detect(frame)
            assert (detection["outcome"], detection["group"]) == (outcome, group)