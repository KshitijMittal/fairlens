"""Feature influence is computed, sorted, and non-fatal (PRD F3-AC5)."""
from pathlib import Path

import shap

from app.services import engine

SAMPLE = Path(__file__).resolve().parents[1] / "samples" / "loan_approvals.csv"


def test_influence_is_available_on_the_loan_sample(loans_result):
    influence = loans_result["influence"]
    assert influence["available"] is True
    assert influence["rows"] > 0
    assert 0 < len(influence["features"]) <= 15
    values = [row["value"] for row in influence["features"]]
    assert values == sorted(values, reverse=True)


def test_shap_failure_leaves_the_verdict_unchanged(monkeypatch, loans_result):
    def boom(*args, **kwargs):
        raise RuntimeError("shap unavailable")

    monkeypatch.setattr(shap, "LinearExplainer", boom)
    broken = engine.run(SAMPLE.read_bytes(), "loan_approvals.csv",
                        confirmations={"outcome": "decision", "positive": "approved",
                                       "group": "gender"})
    assert broken["influence"]["available"] is False
    assert broken["verdict"] == loans_result["verdict"]
    assert broken["amplification"]["difference"] == loans_result["amplification"]["difference"]
