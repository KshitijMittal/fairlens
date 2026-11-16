"""Every sentence the UI renders verbatim. Copy source: UI_UX.md 7.1-7.6 (S6, F4-AC6)."""

LEAD = {
    "fail": {
        "word": "FAIL",
        "headline": "This data would teach a model to treat people unequally.",
        "consequence": "One or more of the five checks failed. Training on this data as it is "
        "would reproduce the disparity the data already contains.",
    },
    "warn": {
        "word": "WARN",
        "headline": "This data is usable, but there is something you should read first.",
        "consequence": "No check failed, and at least one is close enough to the line to be worth "
        "understanding before you train.",
    },
    "inconclusive": {
        "word": "INCONCLUSIVE",
        "headline": "There is not enough here to judge.",
        "consequence": "One or more checks could not be decided honestly. That is a finding about "
        "the data, not a failure of the analysis.",
    },
    "pass": {
        "word": "PASS",
        "headline": "All five checks passed.",
        "consequence": "No group is treated substantially differently in this data by these five "
        "measures. That is not a guarantee of fairness in every sense — the limits are "
        "explained in the method.",
    },
}

CHECK_NAMES = {
    "C1": "Historical disparity",
    "C2": "Model disparity",
    "C3": "Amplification",
    "C4": "Equal opportunity",
    "C5": "Sample adequacy",
}

CHECK_SENTENCES = {
    "C1": {
        "problem": "The decisions already in your data do not treat these groups equally.",
        "pass": "The decisions already in your data treat these groups about equally.",
    },
    "C2": {
        "problem": "A model trained on this data would not treat them equally either.",
        "pass": "A model trained on this data would treat them about equally.",
    },
    "C4": {
        "problem": "People with similar qualifications are not recognised at the same rate.",
        "pass": "People with similar qualifications are recognised at about the same rate.",
    },
    "C5": {
        "problem": "There are not enough rows in each group for these numbers to be worth reading.",
        "pass": "There are enough rows in each group for these numbers to be worth reading.",
    },
}

CHECK_METHODS = {
    "C1": "Ratio of the lower group's selection rate to the higher, 95% bootstrap interval.",
    "C2": "The same ratio on out-of-fold model predictions, 95% bootstrap interval.",
    "C3": "Change in the selection-rate gap between the recorded and model rates.",
    "C4": "Largest difference in true-positive rate between the groups.",
    "C5": "Largest 95% bootstrap half-width among the per-group selection rates.",
}

AMPLIFICATION = {
    "wider": {
        "headline": "The model makes the gap wider.",
        "detail": "Your data already shows a {gap_pts}-point gap between {g_high} and {g_low}. "
        "A model trained on it widens that gap to {model_gap_pts} points. "
        "It learned the pattern and pushed harder than the data did.",
    },
    "same": {
        "headline": "The model keeps the gap where it already is.",
        "detail": "Your data shows a {gap_pts}-point gap between {g_high} and {g_low}. "
        "A model trained on it shows {model_gap_pts} points. It reproduced the pattern without "
        "adding to it — which means removing the disparity means fixing the data, not the model.",
    },
    "narrower": {
        "headline": "The model narrows the gap.",
        "detail": "Your data shows a {gap_pts}-point gap between {g_high} and {g_low}. "
        "A model trained on it shows {model_gap_pts} points. The disparity is smaller than the "
        "one the data already contains — but it has not disappeared.",
    },
}

INCONCLUSIVE_REASONS = {
    "group_too_small": "Group too small",
    "interval_too_wide": "Interval too wide",
    "no_positives": "No positives",
    "no_negatives": "No negatives",
}

LOG_LINES = [
    "Reading your file…",
    "Cleaning the data…",
    "Training a model on your data…",
    "Training fold {fold} of {folds}…",
    "Checking the groups…",
    "Measuring what drove the decisions…",
    "Writing the report…",
]

PRIVACY_LINE = (
    "We processed your file in memory and did not keep it. What is saved is the numbers "
    "on this page — and deleting your account removes them."
)

DISCLAIMER = (
    "These limits are our defaults, based on the common 80% rule. They are not a legal "
    "determination."
)


_DISPLAY_GROUPS = {"female": "women", "male": "men", "group_a": "group a", "group_b": "group b"}


def _display_group(label: str) -> str:
    return _DISPLAY_GROUPS.get(label, label.replace("_", " ").lower())


def affected_sentence(group: str, rate: float, other: str, other_rate: float,
                      gap_pts: int, ci_low_pts: int, ci_high_pts: int, verb: str) -> str:
    return (
        f"For {_display_group(group)}: {round(rate * 100)}% {verb}; "
        f"for {_display_group(other)}: {round(other_rate * 100)}% — a {gap_pts}-point gap "
        f"(95% CI {ci_low_pts}–{ci_high_pts})."
    )


def amplification_detail(form: str, positive_verb: str, g_high: str, g_low: str,
                         gap_pts: int, model_gap_pts: int) -> str:
    body = AMPLIFICATION[form]["detail"]
    return body.format(gap_pts=gap_pts, model_gap_pts=model_gap_pts,
                       g_high=_display_group(g_high), g_low=_display_group(g_low),
                       verb=positive_verb)


def template_narrative(verdict: str, g_high: str, g_low: str, gap_pts: int,
                       positive: str, outcome_column: str) -> str:
    high, low = _display_group(g_high), _display_group(g_low)
    recorded = outcome_column.replace("_", " ")
    if verdict == "pass":
        return (
            f"This dataset was checked for five kinds of disparity and passed all five. "
            f"The {recorded} recorded here are distributed about evenly across "
            f"{high} and {low} — a gap of {gap_pts} percentage points, within the "
            f"tolerance of the common 80% rule. A model trained on this data as it is would "
            f"learn no material group-based pattern. "
            f"This is a template report: it states the measured numbers and nothing else."
        )
    if verdict == "fail":
        return (
            f"This dataset would teach a model to treat {low} unequally. "
            f"The recorded {recorded} values show a {gap_pts}-percentage-point gap between "
            f"{high} and {low} in who was {positive}, and a model trained on this data "
            f"reproduces it. Repair options reweigh, resample or drop-proxy the file; each is "
            f"measured against the same protocol before anything is recommended. "
            f"This is a template report: it states the measured numbers and nothing else."
        )
    if verdict == "warn":
        return (
            f"This dataset is close to even but not there. The {recorded} values recorded here "
            f"show a {gap_pts}-percentage-point gap between {high} and {low} in who was "
            f"{positive}. No check failed outright, which is why the verdict is a warning: read "
            f"the checks, then decide whether to train, repair the data, or collect more rows. "
            f"This is a template report: it states the measured numbers and nothing else."
        )
    return (
        f"There is not enough data here to judge some checks honestly. "
        f"This is a finding about the data, not a failure of the analysis: with the groups as "
        f"small as they are, no defensible verdict is possible. "
        f"This is a template report: it states the measured numbers and nothing else."
    )
