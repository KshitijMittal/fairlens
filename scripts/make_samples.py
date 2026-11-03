"""Generate the three bundled samples (F11). Deterministic: fixed seeds.

- loan_approvals.csv  UCI German Credit, curated so the female/male parity
  ratio lands in the 0.6s (documented verdict: Fail via C1+C2).
- hiring_shortlist.csv synthetic, moderate disparity (documented: Warn).
- scholarship.csv      synthetic, fair by construction (documented: Pass).

Writes an attribution header (lines starting with '#') that the parser skips.
Run: python scripts/make_samples.py
"""
import io
import urllib.request

import numpy as np
import pandas as pd

SEED = 20261101
GERMAN_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data"

GERMAN_COLS = [
    "chk_acct", "months_loan_duration", "credit_history", "purpose", "credit_amount_eur",
    "savings", "employment_years", "installment_rate", "personal_status", "other_debtors",
    "residence_since", "property", "age", "other_plans", "housing", "existing_credits",
    "job", "dependents", "telephone", "foreign_worker", "target",
]

PURPOSE = {"A40": "car_new", "A41": "car_used", "A42": "furniture", "A43": "tv", "A44": "appliances",
           "A45": "repairs", "A46": "education", "A47": "vacation", "A48": "retraining",
           "A49": "business", "A410": "other"}
EMPLOY = {"A71": "unemployed", "A72": "under_1y", "A73": "1_to_4y", "A74": "4_to_7y", "A75": "over_7y"}
HOUSING = {"A151": "rent", "A152": "own", "A153": "free"}
SAVINGS = {"A61": "little", "A62": "moderate", "A63": "quite_rich", "A64": "rich", "A65": "unknown"}


def parity_ratio(frame: pd.DataFrame, group: str, outcome: str, positive: str) -> float:
    rates = frame.groupby(group)[outcome].apply(lambda s: (s == positive).mean())
    return float(rates.min() / rates.max())


def write_with_header(path: str, header_lines: list[str], frame: pd.DataFrame) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        for line in header_lines:
            f.write(f"# {line}\n")
        frame.to_csv(f, index=False)


def make_loan_approvals() -> tuple[pd.DataFrame, float]:
    raw = urllib.request.urlopen(GERMAN_URL, timeout=60).read().decode("utf-8")
    frame = pd.read_csv(io.StringIO(raw), sep=" ", header=None, names=GERMAN_COLS)

    frame["gender"] = frame["personal_status"].map(
        lambda v: "female" if v == "A92" else "male"
    )
    frame["decision"] = np.where(frame["target"] == 1, "approved", "denied")
    frame["purpose"] = frame["purpose"].map(PURPOSE)
    frame["employment_years"] = frame["employment_years"].map(EMPLOY)
    frame["housing"] = frame["housing"].map(HOUSING)
    frame["savings"] = frame["savings"].map(SAVINGS)
    frame = frame.rename(columns={"months_loan_duration": "duration_months", "age": "age_years"})
    keep = ["gender", "age_years", "duration_months", "credit_amount_eur", "purpose",
            "credit_history", "savings", "employment_years", "housing", "decision"]
    frame = frame[keep]

    rng = np.random.default_rng(SEED)
    female = frame[frame["gender"] == "female"]
    female_good = female[female["decision"] == "approved"]
    female_bad = female[female["decision"] == "denied"]
    kept_good = female_good.iloc[rng.choice(len(female_good), size=110, replace=False)]
    curated = pd.concat([female_bad, kept_good])
    rate_f = float((curated["decision"] == "approved").mean())

    male = frame[frame["gender"] == "male"]
    male_good = male[male["decision"] == "approved"]
    male_bad = male[male["decision"] == "denied"]
    target_rate_m = rate_f / 0.695
    keep_n = min(round(target_rate_m * len(male_bad) / (1 - target_rate_m)), len(male_good))
    kept_male_good = male_good.iloc[rng.choice(len(male_good), size=keep_n, replace=False)]
    curated = pd.concat([curated, kept_male_good, male_bad]).sort_index()

    cur = curated.reset_index(drop=True)
    # The six duplicate indexes are drawn first, then copied after the
    # perturbations so all six survive as exact duplicates.
    dup_idx = rng.choice(len(cur), size=6, replace=False)
    blank_housing = rng.choice(len(cur), size=12, replace=False)
    cur.loc[blank_housing, "housing"] = ""
    blank_employ = rng.choice(len(cur), size=8, replace=False)
    cur.loc[blank_employ, "employment_years"] = ""
    casing = rng.choice(["lower", "title", "upper"], size=len(cur))
    cur["gender"] = [g.upper() if c == "upper" else g.title() if c == "title" else g
                     for g, c in zip(cur["gender"], casing)]
    cur["purpose"] = [p.replace("_", " ") if c == "title" else p
                      for p, c in zip(cur["purpose"], casing)]
    cur = pd.concat([cur, cur.iloc[dup_idx]], ignore_index=True)
    cur = cur.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    normalised = cur.assign(gender=cur["gender"].str.strip().str.lower())
    return cur, parity_ratio(normalised, "gender", "decision", "approved")


def make_hiring_shortlist() -> tuple[pd.DataFrame, float]:
    rng = np.random.default_rng(SEED + 1)
    n = 700
    group = np.array(["group_a"] * n + ["group_b"] * n)
    skill = rng.normal(0, 1, 2 * n)
    interview = np.clip(60 + 12 * skill + rng.normal(0, 5, 2 * n), 0, 100)
    school = rng.random(2 * n) < np.where(group == "group_a", 0.45, 0.15)
    school = np.where(school, "yes", "no")
    edu = rng.choice(["high_school", "bachelor", "master"], 2 * n, p=[0.4, 0.4, 0.2])
    years = np.clip(rng.normal(6, 3, 2 * n), 0, 25).round(1)
    logit = 2.2 * skill + 0.5 * (school == "yes") - 0.43 * (group == "group_b") + 0.55 + rng.normal(0, 0.7, 2 * n)
    shortlisted = np.where(rng.random(2 * n) < 1 / (1 + np.exp(-logit)), "yes", "no")
    frame = pd.DataFrame({
        "ethnicity": group, "age_years": np.clip(rng.normal(35, 8, 2 * n), 21, 65).round(0),
        "education": edu, "years_experience": years, "interview_score": interview.round(1),
        "prestigious_school": school, "shortlisted": shortlisted,
    })
    return frame, parity_ratio(frame, "ethnicity", "shortlisted", "yes")


def make_scholarship() -> tuple[pd.DataFrame, float]:
    rng = np.random.default_rng(SEED + 2)
    n = 720
    region = np.array(["north"] * n + ["south"] * n)
    bands = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    age = rng.choice(bands, 2 * n)
    gpa = np.clip(rng.normal(3.0, 0.5, 2 * n), 0, 4).round(2)
    entrance = np.clip(rng.normal(70, 10, 2 * n), 0, 100).round(1)
    extra = np.clip(rng.normal(4, 2, 2 * n), 0, 10).round(0)
    logit = 1.4 * (gpa - 3.0) / 0.5 + 1.0 * (entrance - 70) / 10 + 0.3 * (extra - 4) / 2 + 0.30
    awarded = np.where(rng.random(2 * n) < 1 / (1 + np.exp(-logit)), "yes", "no")
    frame = pd.DataFrame({
        "region": region, "age_band": age, "gpa": gpa, "entrance_score": entrance,
        "extracurriculars": extra, "awarded": awarded,
    })
    return frame, parity_ratio(frame, "region", "awarded", "yes")


def main() -> None:
    loans, loans_ratio = make_loan_approvals()
    hiring, hiring_ratio = make_hiring_shortlist()
    scholarship, scholarship_ratio = make_scholarship()

    write_with_header(
        "samples/loan_approvals.csv",
        ["Source: UCI Machine Learning Repository - Statlog (German Credit) Data Set.",
         "URL: https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data",
         "Licence: CC BY 4.0 (citation: Hans Hofmann, 1994).",
         "Derivation: 1,000 source rows subsampled to 908 (219 women: all denials +",
         "110 of 201 approvals; 689 men: all denials + 498 of 499 approvals) so the",
         "documented female/male parity ratio lands in the 0.6s; then 6 exact duplicate",
         "rows; 12 blank housing and 8 blank employment_years cells; mixed letter casing",
         "in gender and purpose. No identifiers existed in the source.",
         "Documented historical parity ratio (female/male, approved): "
         f"{loans_ratio:.3f}."],
        loans,
    )
    write_with_header(
        "samples/hiring_shortlist.csv",
        ["Source: synthetic, generated by scripts/make_samples.py (seed 20261102).",
         "Licence: CC0 (generated for this repository).",
         "Construction: interview score tracks skill; prestigious_school correlates with",
         "ethnicity (45% vs 15%); shortlisting adds a fixed group_b offset so the",
         "documented parity ratio lands in the warn band. 0 duplicates/blanks.",
         "Documented historical parity ratio (group_b/group_a, shortlisted): "
         f"{hiring_ratio:.3f}."],
        hiring,
    )
    write_with_header(
        "samples/scholarship.csv",
        ["Source: synthetic, generated by scripts/make_samples.py (seed 20261103).",
         "Licence: CC0 (generated for this repository).",
         "Construction: awards depend on gpa, entrance score and extracurriculars only;",
         "region and age band are independent, so both outcomes appear in every group",
         "and the documented parity ratio is near 1.",
         "Documented historical parity ratio (south/north, awarded): "
         f"{scholarship_ratio:.3f}."],
        scholarship,
    )

    for name, ratio in (("loan_approvals", loans_ratio), ("hiring_shortlist", hiring_ratio),
                        ("scholarship", scholarship_ratio)):
        frame = {"loan_approvals": loans, "hiring_shortlist": hiring, "scholarship": scholarship}[name]
        print(f"{name}: rows={len(frame)} parity_ratio={ratio:.3f}")


if __name__ == "__main__":
    main()
