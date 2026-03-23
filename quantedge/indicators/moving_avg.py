"""
Moving Averages — SMA, EMA calculations.
"""

import pandas as pd
from ..config import SMA_SHORT, SMA_MEDIUM, SMA_LONG


def add_sma(df: pd.DataFrame) -> pd.DataFrame:
    """Add Simple Moving Averages (20, 50, 200)."""
    df[f"SMA_{SMA_SHORT}"] = df["Close"].rolling(window=SMA_SHORT).mean()
    df[f"SMA_{SMA_MEDIUM}"] = df["Close"].rolling(window=SMA_MEDIUM).mean()
    df[f"SMA_{SMA_LONG}"] = df["Close"].rolling(window=SMA_LONG).mean()
    return df


def add_ema(df: pd.DataFrame) -> pd.DataFrame:
    """Add Exponential Moving Averages (20, 50, 200)."""
    df[f"EMA_{SMA_SHORT}"] = df["Close"].ewm(span=SMA_SHORT, adjust=False).mean()
    df[f"EMA_{SMA_MEDIUM}"] = df["Close"].ewm(span=SMA_MEDIUM, adjust=False).mean()
    df[f"EMA_{SMA_LONG}"] = df["Close"].ewm(span=SMA_LONG, adjust=False).mean()
    return df
