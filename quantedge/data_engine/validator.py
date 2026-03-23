"""
Validator — Clean and validate OHLCV DataFrames.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def validate_ohlcv(df: pd.DataFrame, symbol: str) -> pd.DataFrame | None:
    """
    Validate and clean an OHLCV DataFrame.
    Returns cleaned DataFrame or None if data is unusable.
    """
    if df is None or df.empty:
        logger.warning(f"[{symbol}] Empty DataFrame — skipping")
        return None

    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    # Handle multi-level columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.warning(f"[{symbol}] Missing columns: {missing}")
        return None

    # Drop rows where Close is NaN
    df = df.dropna(subset=["Close"])

    # Need at least 50 trading days for meaningful indicators
    if len(df) < 50:
        logger.warning(f"[{symbol}] Only {len(df)} rows — need at least 50")
        return None

    # Check for suspicious price jumps (>50% in a day could be a split/error)
    pct_change = df["Close"].pct_change().abs()
    suspicious = pct_change > 0.50
    if suspicious.any():
        count = suspicious.sum()
        logger.info(f"[{symbol}] {count} suspicious price jumps detected (>50%)")

    # Forward-fill small gaps (1-2 days max)
    df = df.ffill(limit=2)

    # Drop any remaining NaN rows
    df = df.dropna(subset=required_cols)

    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # Sort by date ascending
    df = df.sort_index()

    return df
