"""The analysis engine (F3, PRD 8). Deterministic end to end.

Parse -> clean -> encode -> 5-fold stratified OOF logistic regression ->
C1-C5 + per-group tables + bootstrap intervals -> verdict + AnalysisResult.
"""
import hashlib
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from pandas.api.types import is_numeric_dtype

from app.core import report_text, verdict as verdict_mod
from app.core.settings import (BOOTSTRAP_CONFIDENCE, BOOTSTRAP_RESAMPLES, C5_MAX_RATE_HALF_WIDTH,
                               C5_MIN_GROUP_ROWS, ENGINE_VERSION, FOLDS, MIN_GROUP_ROWS,
                               POSITIVE_RATE_THRESHOLD, RATIO_MAX_HALF_WIDTH, THRESHOLDS,
                               derive_seed)
from app.services import parsing

ALPHA = (1 - BOOTSTRAP_CONFIDENCE) / 2 * 100


def _bootstrap(seed: int, y: np.ndarray, groups: np.ndarray, labels: list[str],
               predictions: np.ndarray | None) -> dict:
    """Per-group selection-rate CIs, plus the parity-ratio CI for labels and predictions."""
    rng = np.random.default_rng(seed)
    n = len(y)
    out: dict = {"rates": {}, "ratio": {}, "matrix": {}}
    for kind, values in (("label", y), ("model", predictions)) if predictions is not None else (("label", y),):
        rates = np.empty((BOOTSTRAP_RESAMPLES, len(labels)))
        for i in range(BOOTSTRAP_RESAMPLES):
            idx = rng.integers(0, n, n)
            for g, label in enumerate(labels):
                mask = groups[idx] == label
                rates[i, g] = values[idx][mask].mean() if mask.any() else np.nan
        # Paired resamples, so a gap between two groups gets its own interval.
        out["matrix"][kind] = rates
        for g, label in enumerate(labels):
            column = rates[:, g]
            column = column[~np.isnan(column)]
            lo, hi = np.percentile(column, [ALPHA, 100 - ALPHA])
            out["rates"][(kind, label)] = (float(lo), float(hi))
        ratio = np.nanmin(rates, axis=1) / np.nanmax(rates, axis=1)
        ratio = ratio[~np.isnan(ratio)]
        lo, hi = np.percentile(ratio, [ALPHA, 100 - ALPHA])
        out["ratio"][kind] = (float(lo), float(hi))
    return out


def _tpr_fpr(y_true: np.ndarray, y_pred: np.ndarray, label_mask: np.ndarray) -> tuple[float | None, float | None]:
    tp = float(((y_true == 1) & (y_pred == 1) & label_mask).sum())
    fn = float(((y_true == 1) & (y_pred == 0) & label_mask).sum())
    fp = float(((y_true == 0) & (y_pred == 1) & label_mask).sum())
    tn = float(((y_true == 0) & (y_pred == 0) & label_mask).sum())
    tpr = tp / (tp + fn) if (tp + fn) > 0 else None
    fpr = fp / (fp + tn) if (fp + tn) > 0 else None
    return tpr, fpr


def _state_from_ratio(ratio: float, half_width: float, group_ns: dict) -> tuple[str, str | None]:
    if any(n < MIN_GROUP_ROWS for n in group_ns.values()):
        return "inconclusive", "group_too_small"
    if half_width > RATIO_MAX_HALF_WIDTH:
        return "inconclusive", "interval_too_wide"
    if ratio >= THRESHOLDS["parity"]["pass_at"]:
        return "pass", None
    if ratio >= THRESHOLDS["parity"]["warn_at"]:
        return "warn", None
    return "fail", None


def _cramers_v(a: pd.Series, b: pd.Series) -> float:
    table = pd.crosstab(a, b).to_numpy(dtype=float)
    n = table.sum()
    if n == 0:
        return 0.0
    observed = table / n
    row = observed.sum(axis=1, keepdims=True)
    col = observed.sum(axis=0, keepdims=True)
    expected = row @ col
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum((observed - expected) ** 2 / expected) * n
    r, k = table.shape
    denom = min(r - 1, k - 1)
    return float(np.sqrt(max(chi2 / n, 0.0) / denom)) if denom > 0 else 0.0


def run(raw: bytes, dataset_name: str, confirmations: dict | None = None) -> dict:
    started = time.perf_counter()
    confirmations = confirmations or {}

    frame, clean_stats = parsing.clean(parsing.read_csv(raw))
    detected = parsing.detect(frame)
    outcome_col = confirmations.get("outcome", detected["outcome"])
    positive_raw = confirmations.get("positive", detected["positive"])
    group_col = confirmations.get("group", detected["group"])

    frame[outcome_col] = frame[outcome_col].astype(str).str.strip().str.lower()
    positive = positive_raw.strip().lower()
    y = (frame[outcome_col] == positive).astype(int).to_numpy()
    groups = frame[group_col].astype(str).str.strip().str.lower().to_numpy()
    labels = sorted(set(groups))

    group_counts = {label: int((groups == label).sum()) for label in labels}
    positive_counts = {label: int(((groups == label) & (y == 1)).sum()) for label in labels}

    seed = derive_seed(raw, {"outcome": outcome_col, "positive": positive, "group": group_col})
    positive_count = int(y.sum())

    features = [c for c in frame.columns if c != outcome_col]
    categorical = [c for c in features if not is_numeric_dtype(frame[c])]
    numeric = [c for c in features if c not in categorical]
    x = frame[features].copy()
    for c in categorical:
        x[c] = x[c].astype(object)

    skf = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=seed)
    oof = np.zeros(len(y), dtype=float)
    for train_idx, test_idx in skf.split(x, y):
        pre = ColumnTransformer(
            [("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), categorical),
             ("num", StandardScaler(), numeric)],
            remainder="drop",
        )
        model = Pipeline([("pre", pre),
                          ("clf", LogisticRegression(max_iter=1000))])
        model.fit(x.iloc[train_idx], y[train_idx])
        oof[test_idx] = model.predict_proba(x.iloc[test_idx])[:, 1]

    oof_labels = (oof >= POSITIVE_RATE_THRESHOLD).astype(int)
    oof_accuracy = float((oof_labels == y).mean())
    predicted_positive = oof_labels == 1
    oof_recall = float(predicted_positive[y == 1].mean()) if (y == 1).any() else None
    oof_precision = float((y[predicted_positive] == 1).mean()) if predicted_positive.any() else None

    boot = _bootstrap(seed, y, groups, labels, oof_labels)

    def group_table(kind: str, values: np.ndarray) -> list[dict]:
        rows = []
        for label in labels:
            mask = groups == label
            n = int(mask.sum())
            positives = int(values[mask].sum())
            rate = float(values[mask].mean())
            lo, hi = boot["rates"].get((kind, label), (None, None))
            if kind == "label":
                tpr = fpr = accuracy = None
            else:
                tpr, fpr = _tpr_fpr(y, values, mask)
                accuracy = float((values[mask] == y[mask]).mean())
            rows.append({
                "label": label, "n": n, "positives": positives,
                "selection_rate": round(rate, 3),
                "interval": [round(lo, 3), round(hi, 3)] if lo is not None else None,
                "tpr": round(tpr, 3) if tpr is not None else None,
                "fpr": round(fpr, 3) if fpr is not None else None,
                "accuracy": round(accuracy, 3) if accuracy is not None else None,
            })
        return rows

    historical = group_table("label", y)
    model = group_table("model", oof_labels)

    rates_h = {label: float(y[groups == label].mean()) for label in labels}
    rates_m = {label: float(oof_labels[groups == label].mean()) for label in labels}
    ratio_h = min(rates_h.values()) / max(rates_h.values())
    ratio_m = min(rates_m.values()) / max(rates_m.values())
    dpd_h = max(rates_h.values()) - min(rates_h.values())
    dpd_m = max(rates_m.values()) - min(rates_m.values())
    amplification = dpd_m - dpd_h

    tprs = [r["tpr"] for r in model if r["tpr"] is not None]
    tpr_gap = max(tprs) - min(tprs) if len(tprs) == len(labels) else None

    hw_h = (boot["ratio"]["label"][1] - boot["ratio"]["label"][0]) / 2
    hw_m = (boot["ratio"]["model"][1] - boot["ratio"]["model"][0]) / 2
    rate_hws = {r["label"]: (r["interval"][1] - r["interval"][0]) / 2 for r in historical}

    c1_state, c1_reason = _state_from_ratio(ratio_h, hw_h, group_counts)
    c2_state, c2_reason = _state_from_ratio(ratio_m, hw_m, group_counts)

    if amplification < THRESHOLDS["amplification"]["warn_at"]:
        c3_state, c3_form = "pass", ("narrower" if amplification <= -THRESHOLDS["amplification"]["warn_at"] else "same")
    elif amplification < THRESHOLDS["amplification"]["fail_at"]:
        c3_state, c3_form = "warn", "wider"
    else:
        c3_state, c3_form = "fail", "wider"

    if tpr_gap is None:
        c4_state, c4_reason = "inconclusive", (
            "no_positives" if any(positive_counts[l] == 0 for l in labels) else "no_negatives")
    elif tpr_gap <= THRESHOLDS["equal_opportunity"]["pass_at"]:
        c4_state, c4_reason = "pass", None
    elif tpr_gap <= THRESHOLDS["equal_opportunity"]["fail_at"]:
        c4_state, c4_reason = "warn", None
    else:
        c4_state, c4_reason = "fail", None

    if any(group_counts[l] < MIN_GROUP_ROWS for l in labels):
        c5_state, c5_reason = "inconclusive", "group_too_small"
    elif all(group_counts[l] >= C5_MIN_GROUP_ROWS and rate_hws[l] <= C5_MAX_RATE_HALF_WIDTH
             for l in labels):
        c5_state, c5_reason = "pass", None
    elif all(rate_hws[l] <= RATIO_MAX_HALF_WIDTH for l in labels):
        c5_state, c5_reason = "warn", None
    else:
        c5_state, c5_reason = "inconclusive", "interval_too_wide"

    states = {"C1": c1_state, "C2": c2_state, "C3": c3_state, "C4": c4_state, "C5": c5_state}
    reasons = {"C1": c1_reason, "C2": c2_reason, "C3": None, "C4": c4_reason, "C5": c5_reason}
    overall = verdict_mod.overall(states)
    deciding = verdict_mod.deciding(states)

    g_high = max(rates_h, key=rates_h.get)
    g_low = min(rates_h, key=rates_h.get)
    gap_pts = round((rates_h[g_high] - rates_h[g_low]) * 100)
    model_gap_pts = round(abs(rates_m[g_high] - rates_m[g_low]) * 100)

    # Nobody is "affected" on a Pass, and the interval on a gap must be the gap's.
    verb = positive if positive not in ("yes", "no", "true", "false", "1", "0") else outcome_col.replace("_", " ")
    affected = []
    if overall != "pass":
        index = {label: i for i, label in enumerate(labels)}
        for row in historical:
            if row["label"] == g_high:
                continue
            paired = (boot["matrix"]["label"][:, index[g_high]]
                      - boot["matrix"]["label"][:, index[row["label"]]])
            paired = paired[~np.isnan(paired)]
            ci_low, ci_high = np.percentile(paired, [ALPHA, 100 - ALPHA])
            affected.append({
                "group": row["label"],
                "sentence": report_text.affected_sentence(
                    row["label"], row["selection_rate"], g_high, rates_h[g_high],
                    round((rates_h[g_high] - rates_h[row["label"]]) * 100),
                    round(float(ci_low) * 100), round(float(ci_high) * 100), verb),
            })

    ratio_interval_h = [round(v, 3) for v in boot["ratio"]["label"]]
    ratio_interval_m = [round(v, 3) for v in boot["ratio"]["model"]]

    checks = [
        {"code": "C1", "name": report_text.CHECK_NAMES["C1"], "core": True, "state": c1_state,
         "value": round(ratio_h, 3), "interval": ratio_interval_h,
         "threshold": {**THRESHOLDS["parity"], "direction": "above"},
         "sentence": (report_text.INCONCLUSIVE_REASONS[c1_reason] if c1_reason else
                      report_text.CHECK_SENTENCES["C1"]["pass" if c1_state == "pass" else "problem"]),
         "reason": c1_reason},
        {"code": "C2", "name": report_text.CHECK_NAMES["C2"], "core": True, "state": c2_state,
         "value": round(ratio_m, 3), "interval": ratio_interval_m,
         "threshold": {**THRESHOLDS["parity"], "direction": "above"},
         "sentence": (report_text.INCONCLUSIVE_REASONS[c2_reason] if c2_reason else
                      report_text.CHECK_SENTENCES["C2"]["pass" if c2_state == "pass" else "problem"]),
         "reason": c2_reason},
        {"code": "C3", "name": report_text.CHECK_NAMES["C3"], "core": False, "state": c3_state,
         "value": round(amplification, 3), "interval": None,
         "threshold": {**THRESHOLDS["amplification"], "direction": "below"},
         "sentence": report_text.AMPLIFICATION[c3_form]["headline"],
         "reason": None},
        {"code": "C4", "name": report_text.CHECK_NAMES["C4"], "core": False, "state": c4_state,
         "value": round(tpr_gap, 3) if tpr_gap is not None else None, "interval": None,
         "threshold": {**THRESHOLDS["equal_opportunity"], "direction": "below"},
         "sentence": (report_text.INCONCLUSIVE_REASONS[c4_reason] if c4_reason else
                      report_text.CHECK_SENTENCES["C4"]["pass" if c4_state == "pass" else "problem"]),
         "reason": c4_reason},
        {"code": "C5", "name": report_text.CHECK_NAMES["C5"], "core": True, "state": c5_state,
         "value": round(max(rate_hws.values()), 3), "interval": None,
         "threshold": {**THRESHOLDS["sample_adequacy"], "direction": "below",
                       "measured": "max per-group selection-rate CI half-width"},
         "sentence": (report_text.INCONCLUSIVE_REASONS[c5_reason] if c5_reason else
                      report_text.CHECK_SENTENCES["C5"]["pass" if c5_state == "pass" else "problem"]),
         "reason": c5_reason},
    ]

    proxies = []
    for c in features:
        if c == group_col:
            continue
        if c in categorical:
            value = _cramers_v(frame[c].astype(str), pd.Series(groups))
            if value >= 0.1:
                proxies.append({"column": c, "measure": "cramers_v", "value": round(value, 3)})
        else:
            other = frame[c]
            a = other.to_numpy(dtype=float)
            g01 = (groups == labels[0]).astype(float)
            if a.std() == 0 or g01.std() == 0:
                continue
            corr = float(abs(np.corrcoef(a, g01)[0, 1]))
            if corr >= 0.1:
                proxies.append({"column": c, "measure": "point_biserial", "value": round(corr, 3)})
    proxies.sort(key=lambda p: -p["value"])
    proxies = proxies[:3]

    result = {
        "id": None,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "engine_version": ENGINE_VERSION,
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "dataset": {
            "name": dataset_name,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "rows": int(len(frame)),
            "columns": int(frame.shape[1]),
            "column_names": list(frame.columns),
            "is_sample": True,
            "sample": None,
        },
        "confirmation": {
            "outcome": {"column": outcome_col, "positive_value": positive,
                        "positive_count": positive_count},
            "groups": {"column": group_col,
                       "values": [{"label": l, "n": group_counts[l]} for l in labels]},
            "age_banding": {"applied": False, "bands": None},
            "factor_columns": len(features) - 1,
        },
        "verdict": overall,
        "deciding_checks": deciding,
        "lead": {"state": overall, **{k: report_text.LEAD[overall][k] for k in ("headline", "consequence")}},
        "checks": checks,
        "groups": {"historical": historical, "model": model},
        "affected": affected,
        "amplification": {
            "sentence": report_text.AMPLIFICATION[c3_form]["headline"],
            "detail": report_text.amplification_detail(
                c3_form, "approved", g_high, g_low, gap_pts, model_gap_pts),
            "historical_gap": round(dpd_h, 3),
            "model_gap": round(dpd_m, 3),
            "difference": round(amplification, 3),
        },
        "model_card": {
            "algorithm": "logistic_regression",
            "hyperparameters": {"max_iter": 1000, "solver": "lbfgs", "class_weight": None},
            "folds": FOLDS,
            "oof_accuracy": round(oof_accuracy, 3),
            "oof_precision": round(oof_precision, 3) if oof_precision is not None else None,
            "oof_recall": round(oof_recall, 3) if oof_recall is not None else None,
            "positive_label": positive,
            "sensitive_as_feature": True,
            "engine_version": ENGINE_VERSION,
        },
        "encoding": {
            "categorical": [{"column": c, "mapping": "one-hot (drop first)"} for c in categorical],
            "numeric": [{"column": c, "imputed_median": clean_stats["imputed_medians"].get(c)}
                        for c in numeric],
            "dropped": [{"column": c, "reason": "empty column"}
                        for c in clean_stats["dropped_empty_columns"]],
            "grouped_rare": [],
        },
        "proxies": proxies,
        "sampling": None,
        "thresholds": THRESHOLDS,
        "narrative": {
            "kind": "template",
            "body": report_text.template_narrative(
                overall, g_high, g_low, gap_pts, verb, outcome_col),
            "provider": None,
        },
    }
    return result
