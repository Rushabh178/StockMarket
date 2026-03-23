"""
Technical Screening Rules — Each rule is a pure function: row → bool.
"""

from ..config import SMA_SHORT, SMA_MEDIUM, SMA_LONG


def above_200_sma(row) -> bool:
    """Price trading above 200-day SMA (long-term uptrend)."""
    sma = row.get(f"SMA_{SMA_LONG}")
    close = row.get("Close")
    if sma is None or close is None:
        return False
    return close > sma


def above_50_sma(row) -> bool:
    """Price trading above 50-day SMA (medium-term uptrend)."""
    sma = row.get(f"SMA_{SMA_MEDIUM}")
    close = row.get("Close")
    if sma is None or close is None:
        return False
    return close > sma


def rsi_sweet_spot(row) -> bool:
    """RSI in 40-65 range — momentum without being overbought."""
    rsi = row.get("RSI")
    if rsi is None:
        return False
    return 40 < rsi < 65


def macd_bullish(row) -> bool:
    """MACD line above signal line (bullish crossover territory)."""
    macd = row.get("MACD")
    signal = row.get("MACD_SIGNAL")
    if macd is None or signal is None:
        return False
    return macd > signal


def volume_spike(row) -> bool:
    """Volume is at least 1.5x the 20-day average (institutional interest)."""
    ratio = row.get("VOL_RATIO")
    if ratio is None:
        return False
    return ratio > 1.5


def bb_lower_half(row) -> bool:
    """Price in lower half of Bollinger Band (room to run up)."""
    close = row.get("Close")
    upper = row.get("BB_UPPER")
    lower = row.get("BB_LOWER")
    if close is None or upper is None or lower is None:
        return False
    mid = (upper + lower) / 2
    return close < mid


def ema_alignment(row) -> bool:
    """EMA 20 > EMA 50 > EMA 200 — strong uptrend structure."""
    e20 = row.get(f"EMA_{SMA_SHORT}")
    e50 = row.get(f"EMA_{SMA_MEDIUM}")
    e200 = row.get(f"EMA_{SMA_LONG}")
    if e20 is None or e50 is None or e200 is None:
        return False
    return e20 > e50 > e200


def near_52_week_high(row) -> bool:
    """Price within 10% of 52-week high (stocks making new highs tend to go higher)."""
    close = row.get("Close")
    high = row.get("52W_HIGH")
    if close is None or high is None or high == 0:
        return False
    return close >= high * 0.90


# ─── All Rules Registry ──────────────────────────────────────────
TECHNICAL_RULES = {
    "above_200_sma": {"fn": above_200_sma, "weight": 2.0, "desc": "Above 200 SMA"},
    "above_50_sma": {"fn": above_50_sma, "weight": 1.0, "desc": "Above 50 SMA"},
    "rsi_sweet_spot": {"fn": rsi_sweet_spot, "weight": 1.5, "desc": "RSI 40-65"},
    "macd_bullish": {"fn": macd_bullish, "weight": 1.5, "desc": "MACD Bullish"},
    "volume_spike": {"fn": volume_spike, "weight": 1.5, "desc": "Volume Spike"},
    "bb_lower_half": {"fn": bb_lower_half, "weight": 1.0, "desc": "BB Lower Half"},
    "ema_alignment": {"fn": ema_alignment, "weight": 1.5, "desc": "EMA Aligned"},
}
