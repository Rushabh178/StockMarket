"""
Volume Indicators — Volume average, OBV, Volume spike detection.
"""

import pandas as pd
import ta
from ..config import VOLUME_AVG_PERIOD


def add_volume_avg(df: pd.DataFrame, period: int = VOLUME_AVG_PERIOD) -> pd.DataFrame:
    """Add rolling average volume and volume ratio."""
    df["VOL_AVG"] = df["Volume"].rolling(window=period).mean()
    df["VOL_RATIO"] = df["Volume"] / df["VOL_AVG"]
    return df


def add_obv(df: pd.DataFrame) -> pd.DataFrame:
    """Add On-Balance Volume."""
    df["OBV"] = ta.volume.OnBalanceVolumeIndicator(
        close=df["Close"], volume=df["Volume"]
    ).on_balance_volume()
    return df
