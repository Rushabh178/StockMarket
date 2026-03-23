"""
Fetcher — Fetch OHLCV and fundamental data via yfinance.
"""

import yfinance as yf
import pandas as pd
import time
import logging

from ..config import MARKET_SUFFIX, DEFAULT_PERIOD, FETCH_DELAY, CACHE_DB, CACHE_EXPIRY_HOURS
from .validator import validate_ohlcv
from .cache import DataCache

logger = logging.getLogger(__name__)


def fetch_ohlcv(symbol: str, period: str = DEFAULT_PERIOD, use_cache: bool = True) -> pd.DataFrame | None:
    """
    Fetch OHLCV data for a single symbol.
    Checks cache first, then hits yfinance if stale.
    """
    # Strip suffix if already present to avoid duplication (e.g. TCS.NS.NS)
    clean = symbol.replace(MARKET_SUFFIX, "") if symbol.endswith(MARKET_SUFFIX) else symbol
    ticker = f"{clean}{MARKET_SUFFIX}"
    cache = DataCache(CACHE_DB) if use_cache else None

    # Try cache first
    if cache:
        cached = cache.get_ohlcv(symbol, CACHE_EXPIRY_HOURS)
        if cached is not None and len(cached) >= 50:
            logger.debug(f"[{symbol}] Using cached data ({len(cached)} rows)")
            cache.close()
            return cached

    # Fetch from yfinance
    try:
        logger.info(f"[{symbol}] Fetching from yfinance...")
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        df = validate_ohlcv(df, symbol)

        if df is not None and cache:
            cache.store_ohlcv(symbol, df)

        if cache:
            cache.close()

        time.sleep(FETCH_DELAY)  # Rate limiting
        return df

    except Exception as e:
        logger.error(f"[{symbol}] Fetch failed: {e}")
        if cache:
            cache.close()
        return None


def fetch_fundamentals(symbol: str, use_cache: bool = True) -> dict | None:
    """
    Fetch fundamental data for a stock via yfinance.
    Returns a dict with key financial metrics.
    """
    # Strip suffix if already present to avoid duplication
    clean = symbol.replace(MARKET_SUFFIX, "") if symbol.endswith(MARKET_SUFFIX) else symbol
    ticker_str = f"{clean}{MARKET_SUFFIX}"
    cache = DataCache(CACHE_DB) if use_cache else None

    # Try cache first
    if cache:
        cached = cache.get_fundamentals(symbol, expiry_hours=24)
        if cached:
            logger.debug(f"[{symbol}] Using cached fundamentals")
            cache.close()
            return cached

    try:
        logger.info(f"[{symbol}] Fetching fundamentals...")
        ticker = yf.Ticker(ticker_str)
        info = ticker.info or {}

        fundamentals = {
            "symbol": symbol,
            "name": info.get("longName", symbol),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            "debt_to_equity": info.get("debtToEquity"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "current_ratio": info.get("currentRatio"),
            "book_value": info.get("bookValue"),
            "dividend_yield": info.get("dividendYield"),
            "free_cash_flow": info.get("freeCashflow"),
            "revenue": info.get("totalRevenue"),
            "net_income": info.get("netIncomeToCommon"),
            "total_debt": info.get("totalDebt"),
            "total_cash": info.get("totalCash"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "current_price": info.get("currentPrice"),
            "target_mean_price": info.get("targetMeanPrice"),
            "recommendation": info.get("recommendationKey"),
            "promoter_holders": _get_promoter_holding(ticker),
        }

        if cache:
            cache.store_fundamentals(symbol, fundamentals)
            cache.close()

        time.sleep(FETCH_DELAY)
        return fundamentals

    except Exception as e:
        logger.error(f"[{symbol}] Fundamental fetch failed: {e}")
        if cache:
            cache.close()
        return None


def _get_promoter_holding(ticker) -> float | None:
    """Extract promoter holding percentage from major holders."""
    try:
        holders = ticker.major_holders
        if holders is not None and not holders.empty:
            # Look for insider/promoter holding row
            for _, row in holders.iterrows():
                desc = str(row.iloc[1]).lower() if len(row) > 1 else ""
                if "insider" in desc or "promoter" in desc:
                    val = str(row.iloc[0]).replace("%", "")
                    return float(val) / 100
    except Exception:
        pass
    return None


def fetch_batch(symbols: list[str], period: str = DEFAULT_PERIOD) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV data for a list of symbols."""
    results = {}
    total = len(symbols)
    for i, symbol in enumerate(symbols, 1):
        logger.info(f"[{i}/{total}] Fetching {symbol}...")
        df = fetch_ohlcv(symbol, period)
        if df is not None:
            results[symbol] = df
        else:
            logger.warning(f"[{symbol}] Skipped — no valid data")
    return results


def fetch_fundamentals_batch(symbols: list[str]) -> dict[str, dict]:
    """Fetch fundamental data for a list of symbols."""
    results = {}
    total = len(symbols)
    for i, symbol in enumerate(symbols, 1):
        logger.info(f"[{i}/{total}] Fetching fundamentals for {symbol}...")
        data = fetch_fundamentals(symbol)
        if data:
            results[symbol] = data
    return results
