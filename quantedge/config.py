"""
QuantEdge Configuration — All settings in one place.
"""

import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - runtime safety only
    load_dotenv = None

if load_dotenv:
    # Load environment values from repository root .env when available.
    ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
    load_dotenv(os.path.join(ROOT_DIR, ".env"))

# ─── Market Settings ──────────────────────────────────────────────
MARKET_SUFFIX = ".NS"  # .NS for NSE, .BO for BSE
DEFAULT_PERIOD = "1y"  # Data lookback period
BACKTEST_START = "2021-01-01"

# ─── Screener Settings ────────────────────────────────────────────
TOP_PICKS = 10  # Number of stocks to show in final output
MIN_COMPOSITE_SCORE = 12  # Minimum composite score (tech + fundamental) out of 20

# ─── Technical Indicator Parameters ──────────────────────────────
SMA_SHORT = 20
SMA_MEDIUM = 50
SMA_LONG = 200
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2
ATR_PERIOD = 14
VOLUME_AVG_PERIOD = 20

# ─── Technical Score Weights (total = 10) ─────────────────────────
TECH_WEIGHTS = {
    "trend_sma": 2.0,       # Price above 50/200 SMA
    "rsi_sweet_spot": 1.5,  # RSI between 40-65 (momentum without overbought)
    "macd_bullish": 1.5,    # MACD above signal
    "volume_spike": 1.5,    # Volume > 1.5x average
    "bb_position": 1.0,     # Price in lower half of BB (room to run)
    "ema_alignment": 1.5,   # EMA 20 > 50 > 200 (strong uptrend)
}

# ─── Fundamental Score Weights (total = 10) ───────────────────────
FUND_WEIGHTS = {
    "revenue_growth": 2.0,    # YoY revenue growth > 15%
    "profit_margin": 1.5,     # Net profit margin > 10%
    "roe": 2.0,               # Return on equity > 15%
    "low_debt": 1.5,          # Debt-to-equity < 0.5
    "peg_ratio": 1.5,         # PEG ratio < 1.5 (undervalued growth)
    "earnings_growth": 1.5,   # Earnings growth > 20%
}

# ─── Multibagger Specific Thresholds ─────────────────────────────
MULTIBAGGER = {
    "min_revenue_growth": 0.15,    # 15% YoY
    "min_profit_margin": 0.10,     # 10%
    "min_roe": 0.15,               # 15%
    "max_debt_to_equity": 0.5,     # Low leverage
    "max_peg_ratio": 1.5,          # Undervalued growth
    "min_earnings_growth": 0.20,   # 20% YoY
    "min_market_cap": 500_000_000, # 500 Cr minimum (avoid penny stocks)
    "max_pe_ratio": 40,            # Not excessively overvalued
}

# ─── API / Rate Limiting ─────────────────────────────────────────
FETCH_DELAY = 0.5  # Seconds between API requests (avoid rate limiting)

# ─── Cache Settings ───────────────────────────────────────────────
CACHE_DB = os.path.join(os.path.dirname(__file__), "data", "cache.db")
CACHE_EXPIRY_HOURS = 6  # Re-fetch data after this many hours

# ─── Output Settings ─────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# ─── Telegram (fill in when ready) ───────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# ─── AI (Provider + Models) ───────────────────────────────────────
AI_PROVIDER = os.environ.get("AI_PROVIDER", "groq").strip().lower()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

if AI_PROVIDER == "anthropic":
    AI_ENABLED = bool(ANTHROPIC_API_KEY)
else:
    AI_ENABLED = bool(GROQ_API_KEY)

AI_MIN_SCORE_THRESHOLD = float(os.environ.get("AI_MIN_SCORE_THRESHOLD", 10))

# ─── Stop Loss / Risk Management ─────────────────────────────────
DEFAULT_STOP_LOSS_PCT = 0.05  # 5% hard stop loss — non-negotiable
DEFAULT_TARGET_PCT = 0.15     # 15% target for swing trades
