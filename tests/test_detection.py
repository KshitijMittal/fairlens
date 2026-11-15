"""Detection tests — bundled samples prefill correctly (F2-AC1, F2-AC3, F2-AC4)."""
import pandas as pd
from pathlib import Path

from app.services.parsing import read_csv, clean, detect, build_confirmation_card


def _samples_dir() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "samples"
        if (candidate / "scholarship.csv").exists():
            return candidate
    return here.parents[1] / "samples"


SAMPLES = {
    "scholarship": "scholarship.csv",
    "loan_approvals": "loan_approvals.csv",
    "hiring_shortlist": "hiring_shortlist.csv",
}


class TestDetection:
    """Tests that bundled samples prefill correctly (F2-AC1)."""

    def test_scholarship_prefill(self):
        """Scholarship sample detects correct outcome, positive, group."""
        path = _samples_dir() / SAMPLES["scholarship"]
        raw = path.read_bytes()
        frame, _ = read_csv(raw)
        frame, _ = clean(frame)
        detection = detect(frame)

        # Scholarship should detect 'awarded' as outcome, 'region' as group
        assert detection["outcome"] in ("awarded", "decision", "outcome")
        assert detection["group"] in ("gender", "sex", "ethnicity", "race", "region")
        assert detection["positive"] in ("yes", "true", "1", "approved", "awarded")

    def test_loan_approvals_prefill(self):
        """Loan approvals sample detects correct columns."""
        path = _samples_dir() / SAMPLES["loan_approvals"]
        raw = path.read_bytes()
        frame, _ = read_csv(raw)
        frame, _ = clean(frame)
        detection = detect(frame)

        assert detection["outcome"] in ("approved", "decision", "outcome")
        assert detection["group"] in ("gender", "sex", "ethnicity", "race", "region")
        assert detection["positive"] in ("yes", "true", "1", "approved")

    def test_hiring_shortlist_prefill(self):
        """Hiring shortlist sample detects correct columns."""
        path = _samples_dir() / SAMPLES["hiring_shortlist"]
        raw = path.read_bytes()
        frame, _ = read_csv(raw)
        frame, _ = clean(frame)
        detection = detect(frame)

        assert detection["outcome"] in ("shortlisted", "decision", "outcome")
        assert detection["group"] in ("gender", "sex", "ethnicity", "race")
        assert detection["positive"] in ("yes", "true", "1", "shortlisted")

    def test_majority_class_default_positive(self):
        """Majority class is default positive for all samples (F2-AC3)."""
        for slug, filename in SAMPLES.items():
            path = _samples_dir() / filename
            raw = path.read_bytes()
            frame, _ = read_csv(raw)
            frame, _ = clean(frame)
            detection = detect(frame)

            # Verify the positive value is actually the majority
            counts = frame[detection["outcome"]].astype(str).str.lower().value_counts()
            majority = str(counts.idxmax())
            assert detection["positive"] == majority, f"{slug}: positive should be majority class"

    def test_single_value_demographic_blocked(self):
        """Single-value demographic blocks with explanation (F2-AC4)."""
        # Create a frame with single-value demographic
        df = pd.DataFrame({
            "decision": ["approved", "denied", "approved", "denied"],
            "gender": ["male", "male", "male", "male"],  # Single value
        })
        frame, _ = clean(df)
        detection = detect(frame)
        card = build_confirmation_card(frame, detection)

        warnings = card["warnings"]
        single_value_warnings = [w for w in warnings if w["code"] == "single_value_demographic"]
        assert len(single_value_warnings) == 1
        assert "only one value" in single_value_warnings[0]["message"].lower()
        assert "fairness analysis requires at least two groups" in single_value_warnings[0]["message"].lower()

    def test_card_structure_complete(self):
        """Confirmation card has all required fields."""
        path = _samples_dir() / SAMPLES["scholarship"]
        raw = path.read_bytes()
        frame, _ = read_csv(raw)
        frame, _ = clean(frame)
        detection = detect(frame)
        card = build_confirmation_card(frame, detection)

        # Required top-level keys
        assert "outcome" in card
        assert "groups" in card
        assert "age_banding" in card
        assert "factor_columns" in card
        assert "warnings" in card

        # Outcome subkeys
        assert "column" in card["outcome"]
        assert "positive_value" in card["outcome"]
        assert "positive_count" in card["outcome"]
        assert "total_rows" in card["outcome"]

        # Groups subkeys
        assert "column" in card["groups"]
        assert "values" in card["groups"]
        assert isinstance(card["groups"]["values"], list)
        assert len(card["groups"]["values"]) >= 2

        # Age banding
        assert "available" in card["age_banding"]
        assert "bands" in card["age_banding"]

        # Factor columns is a list
        assert isinstance(card["factor_columns"], list)

        # Warnings is a list
        assert isinstance(card["warnings"], list)