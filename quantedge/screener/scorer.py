"""
Scorer — Compute technical score for a stock based on rules.
"""

from .rules import TECHNICAL_RULES


def score_technical(latest_row: dict) -> dict:
    """
    Score a stock's technical setup on a 0-10 scale.
    """
    results = {}
    total = 0.0
    max_possible = 0.0

    for name, rule in TECHNICAL_RULES.items():
        passed = rule["fn"](latest_row)
        weight = rule["weight"]
        max_possible += weight
        if passed:
            total += weight
        results[name] = {
            "passed": passed,
            "weight": weight,
            "desc": rule["desc"],
        }

    return {
        "technical_score": round(total, 2),
        "max_possible": max_possible,
        "rules": results,
    }
