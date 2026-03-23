"""
Screener Engine — Runs all stocks through technical + fundamental analysis.
Produces a ranked, scored list of candidates.
"""

import logging
import pandas as pd
from datetime import datetime

from ..data_engine.fetcher import fetch_ohlcv, fetch_fundamentals, fetch_batch, fetch_fundamentals_batch
from ..data_engine.symbols import get_nifty50, get_nifty200
from ..indicators.pipeline import apply_all_indicators
from ..fundamentals.analyzer import score_fundamentals, get_fundamental_summary
from .scorer import score_technical
from ..config import (
    TOP_PICKS,
    MIN_COMPOSITE_SCORE,
    DEFAULT_STOP_LOSS_PCT,
    DEFAULT_TARGET_PCT,
    AI_ENABLED,
    AI_MIN_SCORE_THRESHOLD,
)
from ..ai_engine.analyst import generate_trade_brief

logger = logging.getLogger(__name__)


def screen_single(symbol: str) -> dict | None:
    """Run full analysis on a single stock."""
    # Fetch OHLCV
    df = fetch_ohlcv(symbol)
    if df is None:
        return None

    # Apply indicators
    df = apply_all_indicators(df)
    latest = df.iloc[-1].to_dict()

    # Technical score
    tech_result = score_technical(latest)

    # Fetch & score fundamentals
    fund_data = fetch_fundamentals(symbol)
    fund_result = None
    fund_summary = {}
    if fund_data:
        fund_result = score_fundamentals(fund_data)
        fund_summary = get_fundamental_summary(fund_data)

    # Composite score
    tech_score = tech_result["technical_score"]
    fund_score = fund_result["fundamental_score"] if fund_result else 0
    composite = round(tech_score + fund_score, 2)

    # Entry / Stop Loss / Target
    current_price = latest.get("Close", 0)
    atr = latest.get("ATR", current_price * 0.02)
    stop_loss = round(current_price * (1 - DEFAULT_STOP_LOSS_PCT), 2)
    target = round(current_price * (1 + DEFAULT_TARGET_PCT), 2)

    result = {
        "symbol": symbol,
        "name": fund_data.get("name", symbol) if fund_data else symbol,
        "sector": fund_data.get("sector", "Unknown") if fund_data else "Unknown",
        "current_price": round(current_price, 2),
        "stop_loss": stop_loss,
        "target": target,
        "risk_reward": round(DEFAULT_TARGET_PCT / DEFAULT_STOP_LOSS_PCT, 2),
        "technical_score": tech_score,
        "fundamental_score": fund_score,
        "composite_score": composite,
        "is_multibagger": fund_result["is_multibagger_candidate"] if fund_result else False,
        "technical_details": tech_result["rules"],
        "fundamental_details": fund_result["details"] if fund_result else {},
        "fundamental_scores": fund_result["scores"] if fund_result else {},
        "fundamental_summary": fund_summary,
        "rsi": round(latest.get("RSI", 0), 2),
        "macd": round(latest.get("MACD", 0), 4),
        "sma_50": round(latest.get("SMA_50", 0), 2),
        "sma_200": round(latest.get("SMA_200", 0), 2),
        "volume_ratio": round(latest.get("VOL_RATIO", 0), 2),
        "bb_width": round(latest.get("BB_WIDTH", 0), 4),
        "atr": round(atr, 2),
        "pe_ratio": fund_data.get("pe_ratio") if fund_data else None,
        "roe": fund_data.get("roe") if fund_data else None,
        "market_cap": fund_data.get("market_cap") if fund_data else None,
        "revenue_growth": fund_data.get("revenue_growth") if fund_data else None,
        "earnings_growth": fund_data.get("earnings_growth") if fund_data else None,
        "debt_to_equity": fund_data.get("debt_to_equity") if fund_data else None,
        "peg_ratio": fund_data.get("peg_ratio") if fund_data else None,
        "profit_margin": fund_data.get("profit_margin") if fund_data else None,
        "fifty_two_week_high": fund_data.get("fifty_two_week_high") if fund_data else None,
        "fifty_two_week_low": fund_data.get("fifty_two_week_low") if fund_data else None,
        "timestamp": datetime.now().isoformat(),
    }

    # Keep AI optional and cost-controlled; never fail the screener because of LLM issues.
    if AI_ENABLED and composite >= AI_MIN_SCORE_THRESHOLD:
        try:
            result["ai_brief"] = generate_trade_brief(result)
        except Exception as e:
            logger.warning(f"AI brief generation failed for {symbol}: {e}")
            result["ai_brief"] = None

    return result


def run_full_screen(use_nifty200: bool = False) -> list[dict]:
    """
    Run the full screener on Nifty 50 or 200.
    Returns ranked list of stocks sorted by composite score.
    """
    try:
        symbols = get_nifty200() if use_nifty200 else get_nifty50()
    except FileNotFoundError:
        logger.error("Symbol file not found. Using fallback list.")
        symbols = _fallback_symbols()

    logger.info(f"Screening {len(symbols)} stocks...")
    results = []

    for i, symbol in enumerate(symbols, 1):
        logger.info(f"[{i}/{len(symbols)}] Analyzing {symbol}...")
        try:
            result = screen_single(symbol)
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"[{symbol}] Analysis failed: {e}")

    # Sort by composite score descending
    results.sort(key=lambda x: x["composite_score"], reverse=True)

    return results


def get_top_picks(results: list[dict], n: int = TOP_PICKS, min_score: float = MIN_COMPOSITE_SCORE) -> list[dict]:
    """Filter and return top N high-scoring stocks."""
    filtered = [r for r in results if r["composite_score"] >= min_score]
    return filtered[:n]


def get_multibagger_candidates(results: list[dict]) -> list[dict]:
    """Return only stocks flagged as potential multibaggers."""
    return [r for r in results if r.get("is_multibagger")]


def _fallback_symbols() -> list[str]:
    """Hardcoded fallback if CSV files are missing."""
    return [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "HINDUNILVR", "SBIN", "BHARTIARTL", "KOTAKBANK", "ITC",
        "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "BAJFINANCE",
        "TITAN", "SUNPHARMA", "HCLTECH", "WIPRO", "ULTRACEMCO",
        "NESTLEIND", "TATAMOTORS", "POWERGRID", "NTPC", "ONGC",
        "JSWSTEEL", "TATASTEEL", "ADANIENT", "TECHM", "INDUSINDBK",
        "BAJAJFINSV", "HDFCLIFE", "DIVISLAB", "GRASIM", "DRREDDY",
        "CIPLA", "BRITANNIA", "APOLLOHOSP", "EICHERMOT", "COALINDIA",
        "SBILIFE", "BPCL", "HEROMOTOCO", "TATACONSUM", "DABUR",
        "PIDILITIND", "HAVELLS", "GODREJCP", "TORNTPHARM", "MUTHOOTFIN",
    ]
