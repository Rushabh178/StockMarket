"""
Volatility Indicators — Bollinger Bands, ATR.
"""

import pandas as pd
import ta
from ..config import BB_PERIOD, BB_STD, ATR_PERIOD


def add_bollinger_bands(df: pd.DataFrame) -> pd.DataFrame:
    """Add Bollinger Bands (upper, middle, lower)."""
    bb = ta.volatility.BollingerBands(
        df["Close"], window=BB_PERIOD, window_dev=BB_STD
    )
    df["BB_UPPER"] = bb.bollinger_hband()
    df["BB_MIDDLE"] = bb.bollinger_mavg()
    df["BB_LOWER"] = bb.bollinger_lband()
    df["BB_WIDTH"] = (df["BB_UPPER"] - df["BB_LOWER"]) / df["BB_MIDDLE"]
    return df


def add_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.DataFrame:
    """Add Average True Range."""
    df["ATR"] = ta.volatility.AverageTrueRange(
        high=df["High"], low=df["Low"], close=df["Close"], window=period
    ).average_true_range()
    return df
