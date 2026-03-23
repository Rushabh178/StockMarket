"""
Apply all indicators to a DataFrame in one call.
"""

import pandas as pd

from .moving_avg import add_sma, add_ema
from .momentum import add_rsi, add_macd, add_stochastic
from .volatility import add_bollinger_bands, add_atr
from .volume import add_volume_avg, add_obv


def apply_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all technical indicators to an OHLCV DataFrame."""
    df = add_sma(df)
    df = add_ema(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_stochastic(df)
    df = add_bollinger_bands(df)
    df = add_atr(df)
    df = add_volume_avg(df)
    df = add_obv(df)
    return df
