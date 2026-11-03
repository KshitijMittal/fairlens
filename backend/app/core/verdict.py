"""Verdict states per check and the overall verdict (PRD 8.2-8.5).

Fail > Inconclusive > Warn > Pass. deciding_checks holds every check at the
deciding state, in C1-C5 order, empty on a Pass (BACKEND_SCHEMA 3.3).
"""

ORDER = ["C1", "C2", "C3", "C4", "C5"]

RANK = {"fail": 3, "inconclusive": 2, "warn": 1, "pass": 0}


def overall(states: dict[str, str]) -> str:
    worst = max(RANK[s] for s in states.values())
    return {3: "fail", 2: "inconclusive", 1: "warn", 0: "pass"}[worst]


def deciding(states: dict[str, str]) -> list[str]:
    verdict = overall(states)
    if verdict == "pass":
        return []
    return [code for code in ORDER if states[code] == verdict]
