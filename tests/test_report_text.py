"""The copy is the product (UI_UX 7): report_text.py must match the spec verbatim (S6)."""

from app.core import report_text

# Verbatim from UI_UX.md 7.1
DOC_LEAD = {
    "fail": (
        "FAIL",
        "This data would teach a model to treat people unequally.",
        "One or more of the five checks failed. Training on this data as it is would reproduce "
        "the disparity the data already contains.",
    ),
    "warn": (
        "WARN",
        "This data is usable, but there is something you should read first.",
        "No check failed, and at least one is close enough to the line to be worth understanding "
        "before you train.",
    ),
    "inconclusive": (
        "INCONCLUSIVE",
        "There is not enough here to judge.",
        "One or more checks could not be decided honestly. That is a finding about the data, not "
        "a failure of the analysis.",
    ),
    "pass": (
        "PASS",
        "All five checks passed.",
        "No group is treated substantially differently in this data by these five measures. That "
        "is not a guarantee of fairness in every sense — the limits are explained in the method.",
    ),
}

# Verbatim from UI_UX.md 7.2: (problem form, pass form) per check
DOC_CHECK_SENTENCES = {
    "C1": (
        "The decisions already in your data do not treat these groups equally.",
        "The decisions already in your data treat these groups about equally.",
    ),
    "C2": (
        "A model trained on this data would not treat them equally either.",
        "A model trained on this data would treat them about equally.",
    ),
    "C4": (
        "People with similar qualifications are not recognised at the same rate.",
        "People with similar qualifications are recognised at about the same rate.",
    ),
    "C5": (
        "There are not enough rows in each group for these numbers to be worth reading.",
        "There are enough rows in each group for these numbers to be worth reading.",
    ),
}

# Verbatim from UI_UX.md 7.3
DOC_AMPLIFICATION = {
    "wider": "The model makes the gap wider.",
    "same": "The model keeps the gap where it already is.",
    "narrower": "The model narrows the gap.",
}

# Verbatim from UI_UX.md 7.5 and 7.6
DOC_PRIVACY_LINE = (
    "We processed your file in memory and did not keep it. What is saved is the numbers on this "
    "page — and deleting your account removes them."
)
DOC_DISCLAIMER = (
    "These limits are our defaults, based on the common 80% rule. They are not a legal "
    "determination."
)


def test_lead_blocks_verbatim():
    for state, (word, headline, consequence) in DOC_LEAD.items():
        assert report_text.LEAD[state]["word"] == word
        assert report_text.LEAD[state]["headline"] == headline
        assert report_text.LEAD[state]["consequence"] == consequence


def test_check_sentences_both_forms_verbatim():
    for code, (problem, passing) in DOC_CHECK_SENTENCES.items():
        assert report_text.CHECK_SENTENCES[code]["problem"] == problem
        assert report_text.CHECK_SENTENCES[code]["pass"] == passing


def test_amplification_headlines_verbatim():
    for form, headline in DOC_AMPLIFICATION.items():
        assert report_text.AMPLIFICATION[form]["headline"] == headline


def test_privacy_and_disclaimer_verbatim():
    assert report_text.PRIVACY_LINE == DOC_PRIVACY_LINE
    assert report_text.DISCLAIMER == DOC_DISCLAIMER


def test_all_five_checks_have_names():
    assert set(report_text.CHECK_NAMES) == {"C1", "C2", "C3", "C4", "C5"}
