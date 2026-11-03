"""F11-AC1/2/5: each bundled sample produces its documented verdict through the
real pipeline, and the served files are the same ones the tests read."""

from pathlib import Path

from app.services import engine


def test_loans_fails_with_c1_and_c2(loans_result):
    assert loans_result["verdict"] == "fail"
    states = {c["code"]: c["state"] for c in loans_result["checks"]}
    assert states["C1"] == "fail"
    assert states["C2"] == "fail"


def test_loans_parity_in_0_6s(loans_result):
    value = next(c for c in loans_result["checks"] if c["code"] == "C1")["value"]
    assert 0.60 <= value < 0.70


def test_hiring_warns(loans_result, hiring_result):
    assert hiring_result["verdict"] == "warn"


def test_hiring_parity_in_warn_band(hiring_result):
    value = next(c for c in hiring_result["checks"] if c["code"] == "C1")["value"]
    assert 0.80 <= value < 0.90


def test_served_files_are_the_fixtures():
    root = Path(__file__).resolve().parents[1]
    for slug, filename in (("loan_approvals", "loan_approvals.csv"),
                           ("hiring_shortlist", "hiring_shortlist.csv"),
                           ("scholarship", "scholarship.csv")):
        import sys

        from app import main

        assert main.SAMPLE_FILES[slug] == filename
        served = main.SAMPLES_DIR / filename
        assert served.read_bytes() == (root / "samples" / filename).read_bytes()
