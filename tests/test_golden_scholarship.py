"""F11-AC3: the scholarship sample passes all five checks, no Inconclusive,
and every group contains both positives and negatives (PRD 8.5 blocks a Pass
if any check is Inconclusive)."""


def test_scholarship_is_pass(scholarship_result):
    assert scholarship_result["verdict"] == "pass"


def test_all_five_checks_green(scholarship_result):
    states = {c["code"]: c["state"] for c in scholarship_result["checks"]}
    assert states == {"C1": "pass", "C2": "pass", "C3": "pass", "C4": "pass", "C5": "pass"}


def test_no_inconclusive(scholarship_result):
    assert all(c["state"] != "inconclusive" for c in scholarship_result["checks"])
    assert all(c["reason"] is None for c in scholarship_result["checks"])


def test_every_group_has_both_outcomes(scholarship_result):
    for row in scholarship_result["groups"]["historical"]:
        assert row["positives"] > 0
        assert row["positives"] < row["n"]


def test_deciding_checks_empty_on_pass(scholarship_result):
    assert scholarship_result["deciding_checks"] == []
