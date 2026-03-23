"""
Fundamental Analyzer — Score stocks on financial health and growth metrics.
This is the key module for finding multibagger candidates.

Multibagger characteristics:
  1. High revenue growth (>15% YoY)
  2. Expanding profit margins
  3. High ROE (>15%) — efficient capital use
  4. Low debt — room to grow without risk
  5. Reasonable valuation (PEG < 1.5) — growth at a fair price
  6. Strong earnings trajectory
  7. High promoter holding — skin in the game
"""

import logging
from ..config import MULTIBAGGER, FUND_WEIGHTS

logger = logging.getLogger(__name__)


def score_fundamentals(data: dict) -> dict:
    """
    Score a stock's fundamentals on a 0-10 scale.
    Returns a dict with individual scores and total.
    """
    scores = {}
    details = {}

    # 1. Revenue Growth (weight: 2.0)
    rev_growth = data.get("revenue_growth")
    if rev_growth is not None:
        if rev_growth >= MULTIBAGGER["min_revenue_growth"] * 2:
            scores["revenue_growth"] = FUND_WEIGHTS["revenue_growth"]  # 30%+ = full score
        elif rev_growth >= MULTIBAGGER["min_revenue_growth"]:
            scores["revenue_growth"] = FUND_WEIGHTS["revenue_growth"] * 0.7
        elif rev_growth > 0:
            scores["revenue_growth"] = FUND_WEIGHTS["revenue_growth"] * 0.3
        else:
            scores["revenue_growth"] = 0
        details["revenue_growth"] = f"{rev_growth:.1%}"
    else:
        scores["revenue_growth"] = 0
        details["revenue_growth"] = "N/A"

    # 2. Profit Margin (weight: 1.5)
    margin = data.get("profit_margin")
    if margin is not None:
        if margin >= MULTIBAGGER["min_profit_margin"] * 2:
            scores["profit_margin"] = FUND_WEIGHTS["profit_margin"]
        elif margin >= MULTIBAGGER["min_profit_margin"]:
            scores["profit_margin"] = FUND_WEIGHTS["profit_margin"] * 0.7
        elif margin > 0:
            scores["profit_margin"] = FUND_WEIGHTS["profit_margin"] * 0.3
        else:
            scores["profit_margin"] = 0
        details["profit_margin"] = f"{margin:.1%}"
    else:
        scores["profit_margin"] = 0
        details["profit_margin"] = "N/A"

    # 3. Return on Equity (weight: 2.0) — The king metric for multibaggers
    roe = data.get("roe")
    if roe is not None:
        if roe >= MULTIBAGGER["min_roe"] * 2:
            scores["roe"] = FUND_WEIGHTS["roe"]
        elif roe >= MULTIBAGGER["min_roe"]:
            scores["roe"] = FUND_WEIGHTS["roe"] * 0.7
        elif roe > 0.08:
            scores["roe"] = FUND_WEIGHTS["roe"] * 0.3
        else:
            scores["roe"] = 0
        details["roe"] = f"{roe:.1%}"
    else:
        scores["roe"] = 0
        details["roe"] = "N/A"

    # 4. Low Debt (weight: 1.5) — Debt-to-equity ratio
    dte = data.get("debt_to_equity")
    if dte is not None:
        # debt_to_equity from yfinance is often in percentage (e.g., 50 = 50%)
        dte_normalized = dte / 100 if dte > 5 else dte
        if dte_normalized <= MULTIBAGGER["max_debt_to_equity"] * 0.5:
            scores["low_debt"] = FUND_WEIGHTS["low_debt"]  # Very low debt
        elif dte_normalized <= MULTIBAGGER["max_debt_to_equity"]:
            scores["low_debt"] = FUND_WEIGHTS["low_debt"] * 0.7
        elif dte_normalized <= 1.0:
            scores["low_debt"] = FUND_WEIGHTS["low_debt"] * 0.3
        else:
            scores["low_debt"] = 0
        details["debt_to_equity"] = f"{dte_normalized:.2f}"
    else:
        scores["low_debt"] = FUND_WEIGHTS["low_debt"] * 0.5  # No data = neutral
        details["debt_to_equity"] = "N/A"

    # 5. PEG Ratio (weight: 1.5) — Growth at reasonable price
    peg = data.get("peg_ratio")
    if peg is not None and peg > 0:
        if peg <= MULTIBAGGER["max_peg_ratio"] * 0.5:
            scores["peg_ratio"] = FUND_WEIGHTS["peg_ratio"]  # PEG < 0.75 = bargain
        elif peg <= MULTIBAGGER["max_peg_ratio"]:
            scores["peg_ratio"] = FUND_WEIGHTS["peg_ratio"] * 0.7
        elif peg <= 2.5:
            scores["peg_ratio"] = FUND_WEIGHTS["peg_ratio"] * 0.3
        else:
            scores["peg_ratio"] = 0
        details["peg_ratio"] = f"{peg:.2f}"
    else:
        scores["peg_ratio"] = 0
        details["peg_ratio"] = "N/A"

    # 6. Earnings Growth (weight: 1.5)
    eg = data.get("earnings_growth")
    if eg is not None:
        if eg >= MULTIBAGGER["min_earnings_growth"] * 2:
            scores["earnings_growth"] = FUND_WEIGHTS["earnings_growth"]
        elif eg >= MULTIBAGGER["min_earnings_growth"]:
            scores["earnings_growth"] = FUND_WEIGHTS["earnings_growth"] * 0.7
        elif eg > 0:
            scores["earnings_growth"] = FUND_WEIGHTS["earnings_growth"] * 0.3
        else:
            scores["earnings_growth"] = 0
        details["earnings_growth"] = f"{eg:.1%}"
    else:
        scores["earnings_growth"] = 0
        details["earnings_growth"] = "N/A"

    total = round(sum(scores.values()), 2)

    return {
        "fundamental_score": total,
        "max_possible": sum(FUND_WEIGHTS.values()),
        "scores": scores,
        "details": details,
        "is_multibagger_candidate": _check_multibagger(data, total),
    }


def _check_multibagger(data: dict, fund_score: float) -> bool:
    """
    Strict multibagger filter — must pass ALL of these:
    - Fundamental score >= 6/10
    - Market cap above minimum (avoid penny stocks)
    - PE ratio below ceiling
    - Positive revenue and earnings growth
    """
    if fund_score < 6.0:
        return False

    market_cap = data.get("market_cap", 0)
    if market_cap and market_cap < MULTIBAGGER["min_market_cap"]:
        return False

    pe = data.get("pe_ratio")
    if pe is not None and pe > MULTIBAGGER["max_pe_ratio"]:
        return False

    rev_growth = data.get("revenue_growth")
    if rev_growth is not None and rev_growth <= 0:
        return False

    return True


def get_fundamental_summary(data: dict) -> dict:
    """Return a clean summary dict for display purposes."""
    return {
        "Name": data.get("name", "N/A"),
        "Sector": data.get("sector", "N/A"),
        "Market Cap (Cr)": _format_cr(data.get("market_cap")),
        "P/E": _safe_round(data.get("pe_ratio")),
        "PEG": _safe_round(data.get("peg_ratio")),
        "ROE": _format_pct(data.get("roe")),
        "Profit Margin": _format_pct(data.get("profit_margin")),
        "Revenue Growth": _format_pct(data.get("revenue_growth")),
        "Earnings Growth": _format_pct(data.get("earnings_growth")),
        "Debt/Equity": _safe_round(data.get("debt_to_equity")),
        "Promoter Hold": _format_pct(data.get("promoter_holders")),
    }


def _format_cr(val) -> str:
    if val is None:
        return "N/A"
    return f"₹{val / 1e7:,.0f}"


def _format_pct(val) -> str:
    if val is None:
        return "N/A"
    return f"{val:.1%}"


def _safe_round(val, digits=2) -> str:
    if val is None:
        return "N/A"
    return f"{val:.{digits}f}"
