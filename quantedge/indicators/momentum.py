"""
Momentum Indicators — RSI, MACD, Stochastic.
"""

import pandas as pd
import ta
from ..config import RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL


def add_rsi(df: pd.DataFrame, period: int = RSI_PERIOD) -> pd.DataFrame:
    """Add Relative Strength Index."""
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=period).rsi()
    return df


def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    """Add MACD, MACD Signal, and MACD Histogram."""
    macd = ta.trend.MACD(
        df["Close"],
        window_slow=MACD_SLOW,
        window_fast=MACD_FAST,
        window_sign=MACD_SIGNAL,
    )
    df["MACD"] = macd.macd()
    df["MACD_SIGNAL"] = macd.macd_signal()
    df["MACD_HIST"] = macd.macd_diff()
    return df


def add_stochastic(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Add Stochastic Oscillator (%K and %D)."""
    stoch = ta.momentum.StochasticOscillator(
        high=df["High"], low=df["Low"], close=df["Close"], window=period
    )
    df["STOCH_K"] = stoch.stoch()
    df["STOCH_D"] = stoch.stoch_signal()
    return df
