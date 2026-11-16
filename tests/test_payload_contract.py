"""Contract checks for fields the report page and the technical view both read."""
import hashlib
import re

from app.services import engine


def test_sha256_is_the_hash_of_the_uploaded_bytes():
    raw = b"group,amount,label\n" + b"".join(
        f"{'a' if i % 3 else 'b'},{10 + i},{'yes' if i % 2 else 'no'}\n".encode()
        for i in range(30)
    )
    result = engine.run(raw, "tiny.csv")
    assert result["dataset"]["sha256"] == hashlib.sha256(raw).hexdigest()


def test_precision_and_recall_are_different_metrics(loans_result):
    card = loans_result["model_card"]
    assert 0 < card["oof_precision"] <= 1
    assert 0 < card["oof_recall"] <= 1
    assert card["oof_precision"] != card["oof_recall"]


def test_affected_sentence_states_the_gap_and_the_gaps_interval(loans_result):
    sentence = loans_result["affected"][0]["sentence"]
    match = re.search(r"For (\w+): (\d+)% (\w+); for (\w+): (\d+)% .+ a (\d+)-point gap \(95% CI (\d+).(\d+)\)", sentence)
    assert match, sentence
    gap, low, high = int(match.group(6)), int(match.group(7)), int(match.group(8))
    assert gap == abs(int(match.group(2)) - int(match.group(5)))
    assert low < gap < high
    assert " were " not in sentence


def test_model_gap_is_never_negative(loans_result, hiring_result, scholarship_result):
    for result in (loans_result, hiring_result, scholarship_result):
        detail = result["amplification"]["detail"]
        match = re.search(r"(?:shows|widens that gap to) (-?\d+) points", detail)
        assert match, detail
        assert int(match.group(1)) >= 0


def test_pass_has_no_affected_groups(scholarship_result):
    assert scholarship_result["verdict"] == "pass"
    assert scholarship_result["affected"] == []


def test_every_check_carries_its_method_and_the_report_its_copy(loans_result):
    for check in loans_result["checks"]:
        assert check["method"].endswith(".")
    assert loans_result["privacy_line"].startswith("We processed your file in memory")
    assert loans_result["disclaimer"].startswith("These limits are our defaults")
    assert loans_result["influence"]["method"] == "mean absolute SHAP"


def test_imputed_medians_and_dropped_columns_are_reported():
    rows = ["group,amount,blank,label"]
    for i in range(30):
        rows.append(f"{'a' if i % 3 else 'b'},{'' if i == 7 else 10 + i},,{'yes' if i % 2 else 'no'}")
    result = engine.run(("\n".join(rows) + "\n").encode(), "tiny.csv")
    medians = {row["column"]: row["imputed_median"] for row in result["encoding"]["numeric"]}
    assert medians == {"amount": 25.0}
    assert result["encoding"]["dropped"] == [{"column": "blank", "reason": "empty column"}]
