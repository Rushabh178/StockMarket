# QuantEdge — Algorithmic Stock Screener for Indian Markets

**Version:** 1.0.0  
**Market:** NSE (National Stock Exchange of India)  
**Strategy:** Swing Trading with Multibagger Detection  
**Data Source:** Yahoo Finance (via yfinance)

---

## Table of Contents

1.  [Project Overview](#1-project-overview)
2.  [Architecture](#2-architecture)
3.  [Directory Structure](#3-directory-structure)
4.  [Installation & Setup](#4-installation--setup)
5.  [How to Run](#5-how-to-run)
6.  [Configuration Reference](#6-configuration-reference)
7.  [Module-by-Module Breakdown](#7-module-by-module-breakdown)
    - 7.1  [config.py](#71-configpy)
    - 7.2  [data_engine](#72-data_engine)
    - 7.3  [indicators](#73-indicators)
    - 7.4  [fundamentals](#74-fundamentals)
    - 7.5  [screener](#75-screener)
    - 7.6  [backtester](#76-backtester)
    - 7.7  [alerts](#77-alerts)
    - 7.8  [dashboard](#78-dashboard)
    - 7.9  [main.py](#79-mainpy)
    - 7.10 [ai_engine](#710-ai_engine)
8.  [Scoring System](#8-scoring-system)
9.  [Multibagger Detection Logic](#9-multibagger-detection-logic)
10. [Technical Rules Reference](#10-technical-rules-reference)
11. [Fundamental Scoring Reference](#11-fundamental-scoring-reference)
12. [API Endpoints Reference](#12-api-endpoints-reference)
13. [Frontend Pages](#13-frontend-pages)
14. [Caching Strategy](#14-caching-strategy)
15. [Backtester Details](#15-backtester-details)
16. [Data Flow](#16-data-flow)
17. [Dependencies](#17-dependencies)
18. [Environment Variables](#18-environment-variables)
19. [Sample Output](#19-sample-output)
20. [Known Limitations](#20-known-limitations)
21. [Troubleshooting](#21-troubleshooting)
22. [AI Analyzer Deep Dive](#22-ai-analyzer-deep-dive)

---

## 1. Project Overview

QuantEdge is a **Python-based algorithmic stock screener** designed for the Indian stock market. It combines **technical analysis** (7 rules, scored 0–10) with **fundamental analysis** (6 metrics, scored 0–10) to produce a **composite score** out of 20 for each stock.

It screens the **Nifty 50** or **Nifty 200** stock universe, identifies **top picks** for swing trading, and flags potential **multibagger candidates** — stocks with strong financials that may deliver outsized returns.

### What it does:

| Capability | Description |
|---|---|
| **Technical Screening** | Evaluates price action, momentum, volatility, and volume using 7 weighted rules |
| **Fundamental Analysis** | Scores revenue growth, profit margin, ROE, debt, PEG ratio, and earnings growth |
| **Multibagger Detection** | Strict filter for stocks meeting all growth + value criteria simultaneously |
| **Backtesting** | Simulates historical trades based on technical score entry signals with stop-loss/target exits |
| **Web Dashboard** | Full browser-based UI with 6 pages (Dashboard, Screener, Multibaggers, Stock Analysis, Backtester, Settings) |
| **CLI Mode** | Terminal output with rich-formatted tables |
| **Telegram Alerts** | Send top picks to Telegram (optional) |
| **AI Analyzer** | Optional LLM trade-brief generation with Groq or Claude (Anthropic), threshold-gated for cost control |
| **SQLite Caching** | Caches OHLCV data (6h) and fundamentals (24h) to avoid redundant API calls |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   LAYER 1: DATA INGESTION               │
│                                                         │
│  symbols.py ─→ fetcher.py ─→ validator.py ─→ cache.py  │
│  (CSV lists)   (yfinance)    (clean OHLCV)   (SQLite)  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 LAYER 2: ANALYSIS ENGINE                 │
│                                                         │
│  indicators/          fundamentals/       screener/     │
│  ├─ moving_avg.py     └─ analyzer.py      ├─ rules.py  │
│  ├─ momentum.py          (0-10 score)     ├─ scorer.py  │
│  ├─ volatility.py                         └─ engine.py  │
│  ├─ volume.py                                           │
│  └─ pipeline.py                                         │
│     (all indicators)                                    │
│                                                         │
│  ai_engine/                                             │
│  └─ analyst.py       (provider-based LLM analysis)      │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              LAYER 3: OUTPUT & DELIVERY                  │
│                                                         │
│  main.py              dashboard/          alerts/       │
│  (CLI entry point)    ├─ api.py           └─ telegram.py│
│                       │  (FastAPI, 11     backtester/   │
│                       │   endpoints)      ├─ engine.py  │
│                       └─ static/          └─ metrics.py │
│                          └─ index.html                  │
│                             (1494-line SPA)             │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Directory Structure

```
quantedge/
├── config.py                          # Central configuration (all settings)
├── main.py                            # CLI entry point & server launcher
├── requirements.txt                   # Python dependencies
├── README.md                          # This file
│
├── data/
│   ├── nifty50.csv                    # 50 Nifty 50 ticker symbols
│   ├── nifty200.csv                   # 200 Nifty 200 ticker symbols
│   └── cache.db                       # SQLite cache (auto-created at runtime)
│
├── output/                            # CSV exports (auto-created)
│
├── data_engine/
│   ├── __init__.py
│   ├── symbols.py                     # Load ticker lists from CSV
│   ├── fetcher.py                     # Fetch OHLCV + fundamentals via yfinance
│   ├── validator.py                   # Clean/validate OHLCV DataFrames
│   └── cache.py                       # SQLite cache for OHLCV & fundamentals
│
├── indicators/
│   ├── __init__.py
│   ├── moving_avg.py                  # SMA (20/50/200), EMA (20/50/200)
│   ├── momentum.py                    # RSI (14), MACD (12/26/9), Stochastic (14)
│   ├── volatility.py                  # Bollinger Bands (20, 2σ), ATR (14)
│   ├── volume.py                      # Volume Average (20), OBV
│   └── pipeline.py                    # apply_all_indicators() — runs everything
│
├── fundamentals/
│   ├── __init__.py
│   └── analyzer.py                    # Score fundamentals 0-10, multibagger filter
│
├── screener/
│   ├── __init__.py
│   ├── rules.py                       # 7 technical rules as pure functions
│   ├── scorer.py                      # Score tech setup using rules registry
│   └── engine.py                      # Full screening pipeline (single + batch)
│
├── backtester/
│   ├── __init__.py
│   ├── engine.py                      # Historical trade simulation
│   └── metrics.py                     # Win rate, Sharpe, drawdown, profit factor
│
├── alerts/
│   ├── __init__.py
│   └── telegram.py                    # Telegram bot alerts (optional)
│
├── ai_engine/
│   ├── __init__.py
│   └── analyst.py                     # AI trade brief / sentiment / score-delta explainer
│
├── dashboard/
│   ├── __init__.py
│   ├── api.py                         # FastAPI REST API (11 endpoints)
│   └── static/
│       └── index.html                 # 1494-line single-page web application
│
└── tests/
    └── __init__.py
```

**Total files:** 27  
**Total Python modules:** 19

---

## 4. Installation & Setup

### Prerequisites

- Python 3.10+ (uses `X | None` union type syntax)
- pip
- Internet connection (for yfinance data fetching)

### Steps

```bash
# 1. Navigate to the project root (parent of quantedge/)
cd e:\StockMarket

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
# Windows (Git Bash / MSYS2):
source venv/Scripts/activate
# Windows (CMD):
venv\Scripts\activate.bat
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r quantedge/requirements.txt
```

### Verify installation

```bash
python -c "from quantedge.config import *; print('Config OK')"
python -c "from quantedge.screener.engine import screen_single; print('All imports OK')"
```

---

## 5. How to Run

All commands assume you are in `e:\StockMarket` with the virtual environment activated.

### Web Dashboard (Recommended)

```bash
python -m quantedge.main --server
```

Opens at **http://localhost:8000**. The FastAPI server serves the frontend and all API endpoints.

### CLI — Full Screener (Nifty 50)

```bash
python -m quantedge.main
```

Screens all 50 stocks and prints a rich-formatted table with top picks.

### CLI — Full Screener (Nifty 200)

```bash
python -m quantedge.main --nifty200
```

Screens all 200 stocks (takes longer due to API rate limiting at 0.5s per request).

### CLI — Single Stock Analysis

```bash
python -m quantedge.main --stock TCS
# or with .NS suffix (handled automatically):
python -m quantedge.main --stock TCS.NS
```

### CLI — Limit Top Picks

```bash
python -m quantedge.main --top 5
```

### All CLI Flags

| Flag | Type | Default | Description |
|---|---|---|---|
| `--server` | flag | off | Start web server on port 8000 |
| `--stock SYMBOL` | string | none | Analyze a single stock |
| `--nifty200` | flag | off | Screen Nifty 200 instead of Nifty 50 |
| `--top N` | int | 10 | Number of top picks to display |

---

## 6. Configuration Reference

All configuration lives in **`config.py`**. Nothing is hardcoded in individual modules.

### Market Settings

| Setting | Value | Description |
|---|---|---|
| `MARKET_SUFFIX` | `.NS` | Appended to symbols for NSE. Change to `.BO` for BSE |
| `DEFAULT_PERIOD` | `1y` | How much historical data to fetch (yfinance period string) |
| `BACKTEST_START` | `2021-01-01` | Default backtest start date |

### Screener Settings

| Setting | Value | Description |
|---|---|---|
| `TOP_PICKS` | `10` | Number of stocks shown in final output |
| `MIN_COMPOSITE_SCORE` | `12` | Minimum composite score to qualify as a "pick" |

### Technical Indicator Parameters

| Indicator | Parameter | Value |
|---|---|---|
| SMA Short | `SMA_SHORT` | 20 days |
| SMA Medium | `SMA_MEDIUM` | 50 days |
| SMA Long | `SMA_LONG` | 200 days |
| RSI | `RSI_PERIOD` | 14 days |
| MACD Fast | `MACD_FAST` | 12 periods |
| MACD Slow | `MACD_SLOW` | 26 periods |
| MACD Signal | `MACD_SIGNAL` | 9 periods |
| Bollinger Bands | `BB_PERIOD` | 20 days |
| Bollinger Bands | `BB_STD` | 2σ (standard deviations) |
| ATR | `ATR_PERIOD` | 14 days |
| Volume Average | `VOLUME_AVG_PERIOD` | 20 days |

### Technical Score Weights (Total: 10.0)

| Component | Weight | Condition |
|---|---|---|
| `trend_sma` | 2.0 | Price above 50/200 SMA |
| `rsi_sweet_spot` | 1.5 | RSI between 40–65 |
| `macd_bullish` | 1.5 | MACD above signal line |
| `volume_spike` | 1.5 | Volume ≥ 1.5× 20-day average |
| `bb_position` | 1.0 | Price in lower half of Bollinger Band |
| `ema_alignment` | 1.5 | EMA 20 > EMA 50 > EMA 200 |

### Fundamental Score Weights (Total: 10.0)

| Component | Weight | Ideal Condition |
|---|---|---|
| `revenue_growth` | 2.0 | YoY revenue growth > 15% |
| `profit_margin` | 1.5 | Net profit margin > 10% |
| `roe` | 2.0 | Return on equity > 15% |
| `low_debt` | 1.5 | Debt-to-equity < 0.5 |
| `peg_ratio` | 1.5 | PEG ratio < 1.5 |
| `earnings_growth` | 1.5 | Earnings growth > 20% |

### Multibagger Thresholds

| Criterion | Threshold | Rationale |
|---|---|---|
| `min_revenue_growth` | 15% YoY | Sustained top-line growth |
| `min_profit_margin` | 10% | Business moat / pricing power |
| `min_roe` | 15% | Efficient capital allocation |
| `max_debt_to_equity` | 0.5 | Low leverage = room to grow |
| `max_peg_ratio` | 1.5 | Growth at a fair price |
| `min_earnings_growth` | 20% YoY | Accelerating bottom line |
| `min_market_cap` | ₹500 Cr | Avoid penny/micro-cap stocks |
| `max_pe_ratio` | 40 | Not excessively overvalued |

### Risk Management

| Setting | Value | Description |
|---|---|---|
| `DEFAULT_STOP_LOSS_PCT` | 5% | Hard stop loss on every position |
| `DEFAULT_TARGET_PCT` | 15% | Profit target for swing trades |
| Risk : Reward | 1 : 3 | Derived from 5% SL / 15% target |

### AI Settings

| Setting | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `groq` | Provider selector: `groq` or `anthropic` |
| `GROQ_API_KEY` | `""` | Enables AI when provider is `groq` and key is present |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model used for chat completion |
| `ANTHROPIC_API_KEY` | `""` | Enables AI when provider is `anthropic` and key is present |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-latest` | Claude model used for messages API |
| `AI_ENABLED` | derived | Computed boolean based on selected provider + key presence |
| `AI_MIN_SCORE_THRESHOLD` | `10` | Calls AI only for stocks at/above this composite score |

### Cache Settings

| Setting | Value | Description |
|---|---|---|
| `CACHE_DB` | `data/cache.db` | SQLite database path |
| `CACHE_EXPIRY_HOURS` | 6 hours | OHLCV data freshness threshold |
| Fundamental cache | 24 hours | Fundamental data freshness (hardcoded in fetcher) |

### API Rate Limiting

| Setting | Value | Description |
|---|---|---|
| `FETCH_DELAY` | 0.5 seconds | Delay between yfinance API calls |

---

## 7. Module-by-Module Breakdown

### 7.1 config.py

**Path:** `quantedge/config.py`  
**Purpose:** Single source of truth for all settings. Every other module imports from here.

**What it defines:**
- Market suffix (`.NS`), default lookback period (`1y`)
- All indicator parameters (SMA/EMA/RSI/MACD/BB/ATR/Volume periods)
- Score weight distributions for both technical and fundamental analysis
- Multibagger threshold criteria (8 conditions)
- Cache database path and expiry durations
- Stop-loss (5%) and target (15%) percentages
- Telegram bot token and chat ID (from environment variables)
- AI provider and model settings (Groq + Anthropic Claude)
- AI runtime controls (`AI_ENABLED`, `AI_MIN_SCORE_THRESHOLD`)
- Output directory path

**Key design choice:** Uses `os.path` for all file paths relative to the package directory, making it portable.

---

### 7.2 data_engine

Contains 4 modules responsible for all data acquisition, validation, and caching.

#### 7.2.1 symbols.py

**Path:** `quantedge/data_engine/symbols.py`  
**Functions:**

| Function | Signature | Returns | Description |
|---|---|---|---|
| `load_symbols` | `(filename: str)` | `list[str]` | Reads a CSV file with a `Symbol` column header from `data/` directory |
| `get_nifty50` | `()` | `list[str]` | Loads `data/nifty50.csv` — 50 symbols |
| `get_nifty200` | `()` | `list[str]` | Loads `data/nifty200.csv` — 200 symbols |

**Data files:**
- `data/nifty50.csv` — 50 rows, each with `.NS` suffix (e.g., `RELIANCE.NS`)
- `data/nifty200.csv` — 200 rows, same format

#### 7.2.2 fetcher.py

**Path:** `quantedge/data_engine/fetcher.py`  
**Functions:**

| Function | Signature | Returns | Description |
|---|---|---|---|
| `fetch_ohlcv` | `(symbol, period="1y", use_cache=True)` | `DataFrame \| None` | Fetches OHLCV data. Cache-first, then yfinance |
| `fetch_fundamentals` | `(symbol, use_cache=True)` | `dict \| None` | Fetches 25+ fundamental metrics from yfinance `.info` |
| `fetch_batch` | `(symbols, period="1y")` | `dict[str, DataFrame]` | Batch OHLCV fetch for multiple symbols |
| `fetch_fundamentals_batch` | `(symbols)` | `dict[str, dict]` | Batch fundamental fetch for multiple symbols |
| `_get_promoter_holding` | `(ticker)` | `float \| None` | Extracts insider/promoter holding % from `major_holders` |

**OHLCV fetch flow:**
1. Strip `.NS` suffix if present (prevents `TCS.NS.NS` duplication)
2. Check SQLite cache with 6-hour expiry
3. If cache miss → call `yf.download(ticker, period, progress=False, auto_adjust=True)`
4. Validate via `validator.py`
5. Store in cache
6. Sleep 0.5s (rate limiting)

**Fundamental data collected (25+ fields):**

| Field | yfinance Key | Description |
|---|---|---|
| `symbol` | — | Ticker symbol |
| `name` | `longName` | Company full name |
| `sector` | `sector` | Business sector |
| `industry` | `industry` | Specific industry |
| `market_cap` | `marketCap` | Market capitalization in absolute value |
| `pe_ratio` | `trailingPE` | Trailing Price/Earnings |
| `forward_pe` | `forwardPE` | Forward Price/Earnings |
| `peg_ratio` | `pegRatio` | Price/Earnings to Growth |
| `price_to_book` | `priceToBook` | Price to Book value |
| `debt_to_equity` | `debtToEquity` | Debt/Equity ratio |
| `roe` | `returnOnEquity` | Return on Equity |
| `roa` | `returnOnAssets` | Return on Assets |
| `profit_margin` | `profitMargins` | Net profit margin |
| `operating_margin` | `operatingMargins` | Operating margin |
| `revenue_growth` | `revenueGrowth` | YoY revenue growth |
| `earnings_growth` | `earningsGrowth` | YoY earnings growth |
| `current_ratio` | `currentRatio` | Current assets / Current liabilities |
| `book_value` | `bookValue` | Book value per share |
| `dividend_yield` | `dividendYield` | Annual dividend yield |
| `free_cash_flow` | `freeCashflow` | Free cash flow |
| `revenue` | `totalRevenue` | Total revenue |
| `net_income` | `netIncomeToCommon` | Net income attributable to common shareholders |
| `total_debt` | `totalDebt` | Total debt |
| `total_cash` | `totalCash` | Total cash on hand |
| `fifty_two_week_high` | `fiftyTwoWeekHigh` | 52-week high |
| `fifty_two_week_low` | `fiftyTwoWeekLow` | 52-week low |
| `current_price` | `currentPrice` | Current market price |
| `target_mean_price` | `targetMeanPrice` | Analyst consensus target |
| `recommendation` | `recommendationKey` | Analyst recommendation (buy/hold/sell) |
| `promoter_holders` | (parsed from `major_holders`) | Promoter/insider holding % |

#### 7.2.3 validator.py

**Path:** `quantedge/data_engine/validator.py`  
**Function:** `validate_ohlcv(df, symbol) → DataFrame | None`

**Validation pipeline (in order):**

| Step | Check | Action |
|---|---|---|
| 1 | Empty DataFrame | Return `None` |
| 2 | Multi-level columns (yfinance quirk) | Flatten to single level using `get_level_values(0)` |
| 3 | Missing required columns (`Open`, `High`, `Low`, `Close`, `Volume`) | Return `None` |
| 4 | NaN in Close column | Drop those rows |
| 5 | Less than 50 rows remaining | Return `None` (insufficient for indicators like 200-SMA) |
| 6 | Suspicious price jumps > 50% in a day | Log warning (possible split/error) but keep data |
| 7 | Small gaps (1–2 days) | Forward-fill |
| 8 | Any remaining NaN rows | Drop them |
| 9 | Index not DatetimeIndex | Convert to datetime |
| 10 | Unsorted dates | Sort ascending |

#### 7.2.4 cache.py

**Path:** `quantedge/data_engine/cache.py`  
**Class:** `DataCache`

**SQLite schema:**

Table `ohlcv_cache`:
```sql
CREATE TABLE ohlcv_cache (
    symbol TEXT,
    date TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    fetched_at TEXT,
    PRIMARY KEY (symbol, date)
);
```

Table `fundamental_cache`:
```sql
CREATE TABLE fundamental_cache (
    symbol TEXT PRIMARY KEY,
    data TEXT,          -- JSON blob
    fetched_at TEXT
);
```

**Methods:**

| Method | Description |
|---|---|
| `__init__(db_path)` | Creates DB directory if needed, initializes tables |
| `get_ohlcv(symbol, expiry_hours=6)` | Returns DataFrame if cached data is newer than expiry window |
| `store_ohlcv(symbol, df)` | Upserts all rows with `INSERT OR REPLACE` |
| `get_fundamentals(symbol, expiry_hours=24)` | Returns dict from JSON blob if fresh |
| `store_fundamentals(symbol, data)` | Stores as JSON string |
| `close()` | Closes SQLite connection |

---

### 7.3 indicators

Contains 5 modules that add technical indicator columns to OHLCV DataFrames. All use the `ta` library.

#### 7.3.1 moving_avg.py

**Path:** `quantedge/indicators/moving_avg.py`

| Function | Adds Columns | Calculation |
|---|---|---|
| `add_sma(df)` | `SMA_20`, `SMA_50`, `SMA_200` | Simple rolling mean of `Close` |
| `add_ema(df)` | `EMA_20`, `EMA_50`, `EMA_200` | Exponential weighted mean (`adjust=False`) |

#### 7.3.2 momentum.py

**Path:** `quantedge/indicators/momentum.py`

| Function | Adds Columns | Library Class |
|---|---|---|
| `add_rsi(df, period=14)` | `RSI` | `ta.momentum.RSIIndicator` |
| `add_macd(df)` | `MACD`, `MACD_SIGNAL`, `MACD_HIST` | `ta.trend.MACD(fast=12, slow=26, signal=9)` |
| `add_stochastic(df, period=14)` | `STOCH_K`, `STOCH_D` | `ta.momentum.StochasticOscillator` |

#### 7.3.3 volatility.py

**Path:** `quantedge/indicators/volatility.py`

| Function | Adds Columns | Library Class |
|---|---|---|
| `add_bollinger_bands(df)` | `BB_UPPER`, `BB_MIDDLE`, `BB_LOWER`, `BB_WIDTH` | `ta.volatility.BollingerBands(window=20, window_dev=2)` |
| `add_atr(df, period=14)` | `ATR` | `ta.volatility.AverageTrueRange` |

Note: `BB_WIDTH` is calculated as `(BB_UPPER - BB_LOWER) / BB_MIDDLE`.

#### 7.3.4 volume.py

**Path:** `quantedge/indicators/volume.py`

| Function | Adds Columns | Calculation |
|---|---|---|
| `add_volume_avg(df, period=20)` | `VOL_AVG`, `VOL_RATIO` | `Volume / rolling(20).mean()` |
| `add_obv(df)` | `OBV` | `ta.volume.OnBalanceVolumeIndicator` |

#### 7.3.5 pipeline.py

**Path:** `quantedge/indicators/pipeline.py`  
**Function:** `apply_all_indicators(df) → DataFrame`

Calls all indicator functions in sequence:
1. `add_sma` → SMA_20, SMA_50, SMA_200
2. `add_ema` → EMA_20, EMA_50, EMA_200
3. `add_rsi` → RSI
4. `add_macd` → MACD, MACD_SIGNAL, MACD_HIST
5. `add_stochastic` → STOCH_K, STOCH_D
6. `add_bollinger_bands` → BB_UPPER, BB_MIDDLE, BB_LOWER, BB_WIDTH
7. `add_atr` → ATR
8. `add_volume_avg` → VOL_AVG, VOL_RATIO
9. `add_obv` → OBV

**Total columns added:** 19 indicator columns on top of the 5 OHLCV columns.

---

### 7.4 fundamentals

#### 7.4.1 analyzer.py

**Path:** `quantedge/fundamentals/analyzer.py`  
**Functions:**

| Function | Signature | Returns | Description |
|---|---|---|---|
| `score_fundamentals` | `(data: dict)` | `dict` | Scores 6 fundamental metrics, returns total + breakdown |
| `_check_multibagger` | `(data: dict, fund_score: float)` | `bool` | Strict pass/fail filter for multibagger candidacy |
| `get_fundamental_summary` | `(data: dict)` | `dict` | Human-readable formatted summary for display |

**Scoring logic for each metric (tiered system):**

Each metric is scored on its own weight using 4 tiers:

| Tier | Condition | Score |
|---|---|---|
| **Full** | Value ≥ 2× threshold | 100% of weight |
| **Good** | Value ≥ 1× threshold | 70% of weight |
| **Partial** | Value > 0 (but below threshold) | 30% of weight |
| **Fail** | Value ≤ 0 or `None` | 0 |

**Example for Revenue Growth (weight 2.0, threshold 15%):**

| Revenue Growth | Tier | Score |
|---|---|---|
| ≥ 30% | Full | 2.0 |
| ≥ 15% | Good | 1.4 |
| > 0% | Partial | 0.6 |
| ≤ 0% or N/A | Fail | 0.0 |

**Special handling:**
- **Debt-to-Equity**: yfinance sometimes returns values in percentage form (e.g., `50` meaning `50%`). If `dte > 5`, it's divided by 100 to normalize. Scoring is **inverted** — lower is better.
- **Debt-to-Equity (no data)**: Gets 50% of weight (neutral), not 0.
- **PEG Ratio**: Must be > 0 to be scored. Negative PEG (declining earnings) gets 0.

**`score_fundamentals()` return structure:**
```python
{
    "fundamental_score": 7.35,          # Total out of 10
    "max_possible": 10.0,
    "scores": {
        "revenue_growth": 2.0,
        "profit_margin": 1.05,
        "roe": 2.0,
        "low_debt": 1.5,
        "peg_ratio": 0.0,
        "earnings_growth": 0.8
    },
    "details": {
        "revenue_growth": "25.3%",
        "profit_margin": "18.1%",
        "roe": "42.6%",
        "debt_to_equity": "0.09",
        "peg_ratio": "N/A",
        "earnings_growth": "12.5%"
    },
    "is_multibagger_candidate": True
}
```

---

### 7.5 screener

Contains 3 modules that combine technical and fundamental analysis.

#### 7.5.1 rules.py

**Path:** `quantedge/screener/rules.py`  
**Pattern:** Each rule is a **pure function** taking a `row` dict (latest DataFrame row) and returning `bool`.

**7 Technical Rules:**

| Rule Name | Function | Weight | Condition | Rationale |
|---|---|---|---|---|
| `above_200_sma` | `above_200_sma(row)` | 2.0 | `Close > SMA_200` | Long-term uptrend confirmation |
| `above_50_sma` | `above_50_sma(row)` | 1.0 | `Close > SMA_50` | Medium-term uptrend |
| `rsi_sweet_spot` | `rsi_sweet_spot(row)` | 1.5 | `40 < RSI < 65` | Momentum without overbought risk |
| `macd_bullish` | `macd_bullish(row)` | 1.5 | `MACD > MACD_SIGNAL` | Bullish crossover territory |
| `volume_spike` | `volume_spike(row)` | 1.5 | `VOL_RATIO > 1.5` | Institutional buying interest |
| `bb_lower_half` | `bb_lower_half(row)` | 1.0 | `Close < (BB_UPPER + BB_LOWER) / 2` | Room to run upward within band |
| `ema_alignment` | `ema_alignment(row)` | 1.5 | `EMA_20 > EMA_50 > EMA_200` | Strong uptrend structure |

**Total max tech score: 10.0** (2.0 + 1.0 + 1.5 + 1.5 + 1.5 + 1.0 + 1.5)

**Additional rule defined but NOT in registry:**
- `near_52_week_high(row)` — Price within 10% of 52-week high. Defined in code but not added to `TECHNICAL_RULES` dict.

**The `TECHNICAL_RULES` registry:**
```python
TECHNICAL_RULES = {
    "above_200_sma": {"fn": above_200_sma, "weight": 2.0, "desc": "Above 200 SMA"},
    "above_50_sma":  {"fn": above_50_sma,  "weight": 1.0, "desc": "Above 50 SMA"},
    "rsi_sweet_spot": {"fn": rsi_sweet_spot, "weight": 1.5, "desc": "RSI 40-65"},
    "macd_bullish":  {"fn": macd_bullish,  "weight": 1.5, "desc": "MACD Bullish"},
    "volume_spike":  {"fn": volume_spike,  "weight": 1.5, "desc": "Volume Spike"},
    "bb_lower_half": {"fn": bb_lower_half, "weight": 1.0, "desc": "BB Lower Half"},
    "ema_alignment": {"fn": ema_alignment, "weight": 1.5, "desc": "EMA Aligned"},
}
```

#### 7.5.2 scorer.py

**Path:** `quantedge/screener/scorer.py`  
**Function:** `score_technical(latest_row: dict) → dict`

Iterates over `TECHNICAL_RULES` registry:
1. Calls each rule's `fn(latest_row)` → `True`/`False`
2. If rule passes → adds `weight` to total
3. Tracks `max_possible` (sum of all weights)
4. Returns score + per-rule breakdown

**Return structure:**
```python
{
    "technical_score": 5.0,
    "max_possible": 10.0,
    "rules": {
        "above_200_sma": {"passed": True, "weight": 2.0, "desc": "Above 200 SMA"},
        "above_50_sma":  {"passed": False, "weight": 1.0, "desc": "Above 50 SMA"},
        ...
    }
}
```

#### 7.5.3 engine.py

**Path:** `quantedge/screener/engine.py`  
**Functions:**

| Function | Signature | Returns | Description |
|---|---|---|---|
| `screen_single` | `(symbol: str)` | `dict \| None` | Full analysis for one stock |
| `run_full_screen` | `(use_nifty200=False)` | `list[dict]` | Screen all stocks, sorted by composite score desc |
| `get_top_picks` | `(results, n=10, min_score=12)` | `list[dict]` | Filter by minimum score, return top N |
| `get_multibagger_candidates` | `(results)` | `list[dict]` | Return only multibagger-flagged stocks |
| `_fallback_symbols` | `()` | `list[str]` | 50 hardcoded tickers if CSV files are missing |

**`screen_single()` pipeline:**
1. `fetch_ohlcv(symbol)` → OHLCV DataFrame
2. `apply_all_indicators(df)` → DataFrame with 19 indicator columns
3. `df.iloc[-1].to_dict()` → Latest row as dict
4. `score_technical(latest)` → Technical score 0–10
5. `fetch_fundamentals(symbol)` → Fundamental data dict
6. `score_fundamentals(fund_data)` → Fundamental score 0–10
7. Compute `composite_score = technical_score + fundamental_score` (0–20)
8. Calculate `stop_loss = price × (1 - 0.05)` and `target = price × (1 + 0.15)`
9. If AI is enabled and score threshold is met, call `generate_trade_brief(result)`
10. Return comprehensive result dict

**`screen_single()` return structure (all 30+ fields):**
```python
{
    "symbol": "TCS.NS",
    "name": "Tata Consultancy Services Limited",
    "sector": "Technology",
    "current_price": 3520.45,
    "stop_loss": 3344.43,
    "target": 4048.52,
    "risk_reward": 3.0,
    "technical_score": 5.0,
    "fundamental_score": 7.35,
    "composite_score": 12.35,
    "is_multibagger": false,
    "technical_details": { ... },    // Per-rule pass/fail + weights
    "fundamental_details": { ... },  // Per-metric formatted values
    "fundamental_scores": { ... },   // Per-metric numeric scores
    "fundamental_summary": { ... },  // Display-formatted summary
    "rsi": 52.3,
    "macd": 15.23,
    "sma_50": 3450.00,
    "sma_200": 3200.00,
    "volume_ratio": 1.2,
    "bb_width": 0.08,
    "atr": 85.50,
    "pe_ratio": 28.5,
    "roe": 0.426,
    "market_cap": 12800000000000,
    "revenue_growth": 0.049,
    "earnings_growth": 0.125,
    "debt_to_equity": 9.444,
    "peg_ratio": null,
    "profit_margin": 0.183,
    "fifty_two_week_high": 3710.0,
    "fifty_two_week_low": 2348.0,
    "ai_brief": "SETUP: ...\nEDGE: ...\nRISK: ...\nVERDICT: WAIT - weak volume confirmation",
    "timestamp": "2026-03-23T14:57:13.450695"
}
```

**AI behavior in screener:**
- AI is never mandatory. Screening always completes even if AI fails.
- AI is called only when `AI_ENABLED == True` and `composite_score >= AI_MIN_SCORE_THRESHOLD`.
- Failures are logged and `ai_brief` is set to `None`.

---

### 7.6 backtester

#### 7.6.1 engine.py

**Path:** `quantedge/backtester/engine.py`  
**Function:** `run_backtest(symbol, start="2022-01-01", stop_loss_pct=0.05, target_pct=0.15, min_tech_score=5.0) → dict`

**Simulation logic:**
1. Fetch 5 years of OHLCV data (ignores cache for fresh data)
2. Apply all technical indicators
3. Filter to rows after `start` date
4. Walk forward day-by-day:
   - **Entry signal**: When technical score ≥ `min_tech_score` and no open position
   - **Position size**: 10% of capital per trade (`capital × 0.1 / price`)
   - **Exit on stop-loss**: Price ≤ entry × (1 - stop_loss_pct)
   - **Exit on target**: Price ≥ entry × (1 + target_pct)
5. Track equity curve (starting capital: ₹1,00,000)
6. Calculate performance metrics

**Return structure:**
```python
{
    "metrics": {
        "symbol": "TCS.NS",
        "period": "2022-01-01 to 2026-03-21",
        "total_trades": 12,
        "win_rate": 66.67,
        "avg_return_pct": 3.45,
        "max_drawdown_pct": 8.5,
        "sharpe_ratio": 1.42,
        "profit_factor": 2.1,
        "total_pnl": 15230.50,
        "best_trade_pct": 14.8,
        "worst_trade_pct": -4.9
    },
    "trades": [ ... ],          // Array of trade objects
    "equity_curve": [ ... ]     // Last 60 data points
}
```

#### 7.6.2 metrics.py

**Path:** `quantedge/backtester/metrics.py`  
**Functions:**

| Function | Signature | Returns | Description |
|---|---|---|---|
| `calc_win_rate` | `(trades)` | `float` | Percentage of trades with positive PnL |
| `calc_avg_return` | `(trades)` | `float` | Mean `pnl_pct` across all trades |
| `calc_max_drawdown` | `(equity_curve)` | `float` | Largest peak-to-trough decline (%) |
| `calc_sharpe_ratio` | `(trades, risk_free_rate=0.06)` | `float` | Annualized Sharpe ratio (6% risk-free, 250 trading days) |
| `calc_profit_factor` | `(trades)` | `float` | Gross profit / Gross loss |
| `generate_metrics` | `(trades, equity_curve)` | `dict` | All metrics in one call |

**Sharpe ratio formula:**
```
daily_rf = risk_free_rate / 250
sharpe = (mean_return - daily_rf) / std_return × √250
```

---

### 7.7 alerts

#### 7.7.1 telegram.py

**Path:** `quantedge/alerts/telegram.py`  
**Functions:**

| Function | Signature | Returns | Description |
|---|---|---|---|
| `send_alert` | `(message: str)` | `bool` | Send raw text to Telegram via bot API |
| `format_screener_alert` | `(results, top_n=5)` | `str` | Format top results as HTML Telegram message |
| `send_screener_results` | `(results)` | `bool` | Format + send in one call |

**Requirements:**
- Set `TELEGRAM_BOT_TOKEN` environment variable
- Set `TELEGRAM_CHAT_ID` environment variable
- Uses `urllib` (no external dependency) to call `https://api.telegram.org/bot.../sendMessage`
- Message format: HTML (`parse_mode: HTML`)

**Alert format:**
```
QuantEdge Daily Screener

1. RELIANCE 🚀 MULTIBAGGER
   Price: 2850.0 | Score: 16.5/20
   Tech: 8.0/10 | Fund: 8.5/10
   SL: 2707.5 | Target: 3277.5
   RSI: 55.2 | P/E: 25.3
```

---

### 7.8 dashboard

#### 7.8.1 api.py

**Path:** `quantedge/dashboard/api.py`  
**Framework:** FastAPI 0.104+  
**Server:** Uvicorn

**Middleware:**
- CORS enabled for all origins (`allow_origins=["*"]`)
- Static file serving from `dashboard/static/`

**In-memory state:**
- `_latest_results: list[dict]` — Cached results from the last full screener run
- `_last_run_time: str | None` — Timestamp of the last run

**11 API Endpoints:**

| # | Method | Path | Description |
|---|---|---|---|
| 1 | `GET` | `/` | Serve frontend `index.html` |
| 2 | `GET` | `/api/health` | Health check — returns `{"status": "ok", "timestamp": "...", "version": "1.0.0"}` |
| 3 | `GET` | `/api/screener/run` | Run full screener (Nifty 50 or 200). Query param: `?nifty200=true`. **Slow — screens all stocks** |
| 4 | `GET` | `/api/screener/results` | Get cached results from the last run |
| 5 | `GET` | `/api/screener/top` | Get top N picks. Query param: `?n=10` (1–50) |
| 6 | `GET` | `/api/screener/multibaggers` | Get multibagger candidates from last run |
| 7 | `GET` | `/api/stock/{symbol}` | Full single-stock analysis (tech + fundamental + composite) |
| 8 | `GET` | `/api/stock/{symbol}/chart` | OHLCV + indicator data for charting (last 120 days). Query param: `?period=6mo` |
| 9 | `GET` | `/api/stock/{symbol}/fundamentals` | Fundamental analysis only (raw + scored + summary) |
| 10 | `GET` | `/api/stock/{symbol}/ai-analysis` | On-demand AI trade brief generation for one symbol |
| 11 | `GET` | `/api/backtest/{symbol}` | Run backtest. Query params: `?start=2022-01-01&stop_loss=0.05&target=0.15` |

**Error handling:**
- 404 for symbols with no data
- 500 for unexpected failures
- All errors returned as `{"detail": "error message"}`

#### 7.8.2 static/index.html

**Path:** `quantedge/dashboard/static/index.html`  
**Size:** 1,494 lines (HTML + CSS + JavaScript in a single file)  
**Type:** Single-Page Application (SPA)  
**Theme:** Dark background with gold accents (#f0c040)

**6 Pages:**

| Page | What it Shows |
|---|---|
| **Dashboard** | 4 stat cards (Total Screened, Avg Score, Multibaggers, Top Score) + Top 10 picks table |
| **Screener** | Full results table with sector filter dropdown, min score slider, sort by column, search |
| **Multibaggers** | Card layout for multibagger candidates with key metrics |
| **Stock Analysis** | Single stock deep-dive: score circles (tech/fund/composite), rule pass/fail chips, fundamental grid |
| **Backtester** | Configuration form (symbol, start date, SL%, target%) + metrics cards + trade log table |
| **Settings** | Display of current thresholds and status (read-only) |

**Frontend Features:**
- Sidebar navigation with active page highlighting
- Search bar in header (analyzes any symbol typed)
- Loading overlay with spinner for long operations
- Toast notifications (success/error)
- CSV export button for screener results
- Score color coding: green (≥14), yellow (≥10), red (<10)
- Responsive layout
- Health check ping on page load

---

### 7.9 main.py

**Path:** `quantedge/main.py`  
**Purpose:** Unified entry point for both CLI and server modes.

**Functions:**

| Function | Description |
|---|---|
| `main()` | Parses CLI arguments and dispatches to appropriate mode |
| `run_server()` | Starts uvicorn on `0.0.0.0:8000` |
| `print_results(results)` | Rich-formatted table output (falls back to plain text if `rich` not installed) |

**CLI table columns:** #, Symbol, Score (color-coded), Tech, Fund, Price (₹), RSI, SL (₹, red), Target (₹, green), Sector, MB? (🚀 or —)

---

### 7.10 ai_engine

#### 7.10.1 analyst.py

**Path:** `quantedge/ai_engine/analyst.py`  
**Purpose:** Provider-agnostic LLM layer for generating analyst-style outputs.

**Design principles:**
1. Provider abstraction (`groq` or `anthropic`) behind one `_chat_completion` function
2. Graceful degradation when key/SDK is missing
3. Prompt-constrained response format for deterministic downstream rendering
4. No hard dependency of core screening on AI success

**Key functions:**

| Function | Signature | Returns | Notes |
|---|---|---|---|
| `_get_provider_and_client` | `() -> tuple[str, Any \| None]` | `(provider, client)` | Resolves runtime provider and initializes SDK client |
| `_chat_completion` | `(prompt, max_tokens=220, temperature=0.2)` | `str` | Unified completion API for both providers |
| `generate_trade_brief` | `(screen_result: dict)` | `str` | 4-line structured brief: SETUP, EDGE, RISK, VERDICT |
| `analyze_news_sentiment` | `(symbol: str, headlines: list[str])` | `dict` | Structured JSON sentiment object (score, label, risk, catalyst, summary) |
| `explain_score_drop` | `(symbol, prev_score, curr_score, prev_data, curr_data)` | `str` | Two-sentence score change explanation |

**Provider switching details:**
- `AI_PROVIDER=groq` uses `groq` SDK and `GROQ_MODEL`
- `AI_PROVIDER=anthropic` uses `anthropic` SDK and `ANTHROPIC_MODEL`
- Unsupported provider values fallback to `groq`

**Error model:**
- Missing key or missing SDK returns no client
- `_chat_completion` raises `RuntimeError` if provider is not configured
- Caller modules (`screener` / `dashboard`) catch and handle to avoid crashing user flows

---

## 8. Scoring System

### How the Composite Score Works

```
Composite Score = Technical Score (0-10) + Fundamental Score (0-10) = 0-20
```

| Score Range | Interpretation |
|---|---|
| 16–20 | Excellent — strong across both technical and fundamental |
| 12–15 | Good — qualifies as a "pick" (above `MIN_COMPOSITE_SCORE`) |
| 8–11 | Average — some positives but mixed signals |
| 0–7 | Weak — avoid |

### Technical Score Breakdown (0–10)

Binary pass/fail for each rule. Weight added if rule passes.

| Weight | Rule | Pass Condition |
|---|---|---|
| 2.0 | Above 200 SMA | `Close > SMA_200` |
| 1.0 | Above 50 SMA | `Close > SMA_50` |
| 1.5 | RSI Sweet Spot | `40 < RSI < 65` |
| 1.5 | MACD Bullish | `MACD > MACD_SIGNAL` |
| 1.5 | Volume Spike | `VOL_RATIO > 1.5` |
| 1.0 | BB Lower Half | `Close < Midline of Bollinger Bands` |
| 1.5 | EMA Alignment | `EMA_20 > EMA_50 > EMA_200` |
| **10.0** | **Total** | |

### Fundamental Score Breakdown (0–10)

Tiered scoring (Full / Good / Partial / Fail) for each metric.

| Weight | Metric | Full (100%) | Good (70%) | Partial (30%) | Fail (0%) |
|---|---|---|---|---|---|
| 2.0 | Revenue Growth | ≥ 30% | ≥ 15% | > 0% | ≤ 0% |
| 1.5 | Profit Margin | ≥ 20% | ≥ 10% | > 0% | ≤ 0% |
| 2.0 | ROE | ≥ 30% | ≥ 15% | > 8% | ≤ 8% |
| 1.5 | Low Debt (D/E) | ≤ 0.25 | ≤ 0.50 | ≤ 1.0 | > 1.0 |
| 1.5 | PEG Ratio | ≤ 0.75 | ≤ 1.50 | ≤ 2.5 | > 2.5 |
| 1.5 | Earnings Growth | ≥ 40% | ≥ 20% | > 0% | ≤ 0% |
| **10.0** | **Total** | | | | |

---

## 9. Multibagger Detection Logic

A stock is flagged as a **multibagger candidate** only if it passes **ALL** of these conditions:

| # | Condition | Check |
|---|---|---|
| 1 | Fundamental Score ≥ 6.0 / 10 | Must be fundamentally strong |
| 2 | Market Cap ≥ ₹500 Cr | Avoids penny stocks and illiquid micro-caps |
| 3 | P/E Ratio ≤ 40 | Not excessively overvalued |
| 4 | Revenue Growth > 0% | Must have positive top-line growth |

**Important:** This is deliberately a strict filter. The multibagger flag is a **necessary but not sufficient** condition for investment. It identifies stocks with the financial profile historically associated with multibagger returns.

**What makes a multibagger (the underlying thesis):**
1. **High Revenue Growth** — Company is growing its top line faster than peers
2. **Expanding Profit Margins** — Pricing power or operational efficiency
3. **High ROE** — Management allocates capital efficiently
4. **Low Debt** — Financial flexibility to invest in growth
5. **Reasonable PEG** — Not paying too much for growth
6. **Strong Earnings Trajectory** — Bottom line following top line
7. **High Promoter Holding** — Management has skin in the game (data collected but not scored)

---

## 10. Technical Rules Reference

### Rule 1: Above 200 SMA (Weight: 2.0)

```python
def above_200_sma(row) -> bool:
    return Close > SMA_200
```

**Rationale:** The 200-day SMA is the most widely watched long-term trend indicator. Stocks above it are in a structural uptrend. This gets the highest weight because trend is the most important factor in swing trading.

### Rule 2: Above 50 SMA (Weight: 1.0)

```python
def above_50_sma(row) -> bool:
    return Close > SMA_50
```

**Rationale:** Medium-term trend confirmation. Lower weight because it's secondary to the 200 SMA.

### Rule 3: RSI Sweet Spot (Weight: 1.5)

```python
def rsi_sweet_spot(row) -> bool:
    return 40 < RSI < 65
```

**Rationale:** RSI 40–65 indicates healthy momentum without being overbought (>70) or oversold (<30). This is the "Goldilocks zone" for swing entries.

### Rule 4: MACD Bullish (Weight: 1.5)

```python
def macd_bullish(row) -> bool:
    return MACD > MACD_SIGNAL
```

**Rationale:** MACD crossing above its signal line is a classic buy signal. Indicates positive momentum acceleration.

### Rule 5: Volume Spike (Weight: 1.5)

```python
def volume_spike(row) -> bool:
    return VOL_RATIO > 1.5
```

**Rationale:** Volume 1.5× above average suggests institutional buying. Smart money moves often precede price moves.

### Rule 6: BB Lower Half (Weight: 1.0)

```python
def bb_lower_half(row) -> bool:
    return Close < (BB_UPPER + BB_LOWER) / 2
```

**Rationale:** Price in the lower half of Bollinger Bands suggests room to move up toward the upper band, providing a better risk/reward entry.

### Rule 7: EMA Alignment (Weight: 1.5)

```python
def ema_alignment(row) -> bool:
    return EMA_20 > EMA_50 > EMA_200
```

**Rationale:** When short-term moving averages are above long-term ones in perfect alignment, the stock is in a strong, multi-timeframe uptrend.

---

## 11. Fundamental Scoring Reference

### Metric 1: Revenue Growth (Weight: 2.0)

| Value | Score |
|---|---|
| ≥ 30% | 2.0 (Full) |
| ≥ 15% | 1.4 (Good) |
| > 0% | 0.6 (Partial) |
| ≤ 0% or N/A | 0.0 |

### Metric 2: Profit Margin (Weight: 1.5)

| Value | Score |
|---|---|
| ≥ 20% | 1.5 (Full) |
| ≥ 10% | 1.05 (Good) |
| > 0% | 0.45 (Partial) |
| ≤ 0% or N/A | 0.0 |

### Metric 3: Return on Equity (Weight: 2.0)

| Value | Score |
|---|---|
| ≥ 30% | 2.0 (Full) |
| ≥ 15% | 1.4 (Good) |
| > 8% | 0.6 (Partial) |
| ≤ 8% or N/A | 0.0 |

### Metric 4: Low Debt — Debt/Equity (Weight: 1.5)

| D/E Value | Score |
|---|---|
| ≤ 0.25 | 1.5 (Full — very low debt) |
| ≤ 0.50 | 1.05 (Good) |
| ≤ 1.0 | 0.45 (Partial) |
| > 1.0 | 0.0 |
| N/A | 0.75 (Neutral — 50% of weight) |

**Note:** `debtToEquity` from yfinance is sometimes in % form (e.g., `50` = 50%). The code normalizes: if `value > 5`, divides by 100.

### Metric 5: PEG Ratio (Weight: 1.5)

| PEG Value | Score |
|---|---|
| ≤ 0.75 | 1.5 (Full — bargain growth) |
| ≤ 1.50 | 1.05 (Good) |
| ≤ 2.5 | 0.45 (Partial) |
| > 2.5 or ≤ 0 | 0.0 |

### Metric 6: Earnings Growth (Weight: 1.5)

| Value | Score |
|---|---|
| ≥ 40% | 1.5 (Full) |
| ≥ 20% | 1.05 (Good) |
| > 0% | 0.45 (Partial) |
| ≤ 0% or N/A | 0.0 |

---

## 12. API Endpoints Reference

Base URL: `http://localhost:8000`

### GET /

Serves the `dashboard/static/index.html` frontend. No JSON response.

### GET /api/health

```json
{
    "status": "ok",
    "timestamp": "2026-03-23T15:00:28.863584",
    "version": "1.0.0"
}
```

### GET /api/screener/run

**Query Parameters:**
- `nifty200` (bool, default: `false`) — Screen Nifty 200 instead of Nifty 50

**Response:**
```json
{
    "total_screened": 50,
    "timestamp": "2026-03-23T15:10:00.000000",
    "results": [ /* array of screen_single() result objects */ ]
}
```

**Warning:** This endpoint is slow. Nifty 50 takes ~1–3 minutes. Nifty 200 takes ~5–15 minutes.

### GET /api/screener/results

Returns the in-memory cached results from the last `/api/screener/run` call. Same response structure. Returns empty if screener hasn't been run yet.

### GET /api/screener/top

**Query Parameters:**
- `n` (int, default: 10, range: 1–50) — Number of top picks

**Response:**
```json
{
    "picks": [ /* top N results sorted by composite score */ ],
    "count": 10
}
```

### GET /api/screener/multibaggers

**Response:**
```json
{
    "candidates": [ /* only stocks where is_multibagger = true */ ],
    "count": 3
}
```

### GET /api/stock/{symbol}

**Path Parameter:**
- `symbol` — Stock ticker (e.g., `TCS`, `RELIANCE`, `INFY.NS`). Auto-uppercased and trimmed.

**Response:** Full `screen_single()` result object (see Section 7.5.3 for complete field list).

### GET /api/stock/{symbol}/chart

**Query Parameters:**
- `period` (string, default: `6mo`) — yfinance period string

**Response:**
```json
{
    "symbol": "TCS.NS",
    "data": [
        {
            "date": "2026-03-21",
            "open": 3510.00,
            "high": 3540.00,
            "low": 3495.00,
            "close": 3520.45,
            "volume": 1250000,
            "sma_20": 3480.00,
            "sma_50": 3450.00,
            "sma_200": 3200.00,
            "rsi": 52.3,
            "macd": 15.23,
            "macd_signal": 12.10,
            "bb_upper": 3600.00,
            "bb_lower": 3380.00
        }
    ]
}
```

Returns last 120 days of data.

### GET /api/stock/{symbol}/fundamentals

**Response:**
```json
{
    "symbol": "TCS",
    "raw": { /* all 25+ fundamental fields from yfinance */ },
    "scored": { /* score_fundamentals() output */ },
    "summary": { /* get_fundamental_summary() output */ }
}
```

### GET /api/stock/{symbol}/ai-analysis

Runs single-stock analysis and returns the AI brief on demand.

**Path Parameter:**
- `symbol` — Stock ticker (e.g., `TCS`, `RELIANCE`, `INFY.NS`)

**Success Response:**
```json
{
    "symbol": "TCS",
    "ai_brief": "SETUP: ...\nEDGE: ...\nRISK: ...\nVERDICT: BUY ZONE - momentum with volume",
    "timestamp": "2026-03-23T16:02:33.124101"
}
```

**Failure Responses:**
- `503` when AI is disabled (provider key not configured)
- `404` when stock data is unavailable
- `500` for unexpected runtime issues

### GET /api/backtest/{symbol}

**Query Parameters:**
- `start` (string, default: `2022-01-01`) — Backtest start date
- `stop_loss` (float, default: `0.05`) — Stop loss percentage (0.05 = 5%)
- `target` (float, default: `0.15`) — Target percentage (0.15 = 15%)

**Response:**
```json
{
    "metrics": {
        "symbol": "TCS.NS",
        "period": "2022-01-01 to 2026-03-21",
        "total_trades": 12,
        "win_rate": 66.67,
        "avg_return_pct": 3.45,
        "max_drawdown_pct": 8.5,
        "sharpe_ratio": 1.42,
        "profit_factor": 2.1,
        "total_pnl": 15230.50,
        "best_trade_pct": 14.8,
        "worst_trade_pct": -4.9
    },
    "trades": [
        {
            "symbol": "TCS.NS",
            "entry_date": "2022-02-15",
            "exit_date": "2022-03-10",
            "entry_price": 3200.00,
            "exit_price": 3680.00,
            "shares": 3,
            "pnl": 1440.00,
            "pnl_pct": 15.0,
            "exit_reason": "target"
        }
    ],
    "equity_curve": [100000, 100500, 101440, ...]
}
```

---

## 13. Frontend Pages

### Page 1: Dashboard

- **4 stat cards** at the top: Total Screened, Avg Score, Multibaggers Found, Top Score
- **Top Picks table** showing symbol, score, price, RSI, sector
- Run Screener button (Nifty 50 or Nifty 200 toggle)

### Page 2: Screener

- Full results table with all screened stocks
- **Filters:** Sector dropdown, minimum score slider
- **Sort** by any column
- **Search** within results
- **Export CSV** button

### Page 3: Multibaggers

- Card-based layout for multibagger candidates
- Each card shows: symbol, name, composite score, key fundamentals (ROE, revenue growth, profit margin, D/E)
- Empty state message if no candidates found

### Page 4: Stock Analysis

- Search/input field to analyze any symbol
- **Score visualization:** Three circular score displays (Technical, Fundamental, Composite)
- **Technical rules:** Chip/badge for each rule (green if passed, red if failed)
- **Fundamental grid:** All fundamental metrics with formatted values
- **Summary section:** Company name, sector, market cap, P/E, etc.

### Page 5: Backtester

- **Config form:** Symbol, start date, stop-loss %, target %
- **Run Backtest** button
- **Metrics cards:** Total trades, win rate, avg return, max drawdown, Sharpe ratio, profit factor, total PnL
- **Trade log table:** Entry/exit dates, prices, PnL, exit reason

### Page 6: Settings

- Displays current configuration thresholds (read-only)
- Technical and fundamental weight tables
- Multibagger criteria
- Server health status with connectivity indicator

---

## 14. Caching Strategy

### Why Cache?

yfinance has rate limits and fetching 50+ stocks takes time. Caching avoids redundant API calls.

### Two Cache Layers

| Layer | Storage | Expiry | Key |
|---|---|---|---|
| OHLCV | SQLite table `ohlcv_cache` | 6 hours | `(symbol, date)` composite PK |
| Fundamentals | SQLite table `fundamental_cache` | 24 hours | `symbol` PK, data as JSON blob |

### Cache Flow

```
Request → Check SQLite (is data fresh?) 
  ├── YES → Return cached data
  └── NO  → Fetch from yfinance → Validate → Store in SQLite → Return
```

### Cache Location

`quantedge/data/cache.db` — Auto-created on first run.

### Clearing Cache

Delete the `cache.db` file to force a complete re-fetch:
```bash
rm quantedge/data/cache.db
```

---

## 15. Backtester Details

### Entry Logic

A trade is entered when:
1. No existing position is open
2. Technical score of the current day ≥ `min_tech_score` (default: 5.0)

### Exit Logic

A trade is exited when either:
- **Stop-loss hit:** Current price ≤ `entry_price × (1 - stop_loss_pct)`
- **Target hit:** Current price ≥ `entry_price × (1 + target_pct)`

### Position Sizing

- **10% of capital** per trade: `shares = int(capital × 0.1 / price)`
- No compounding within the same trade
- Capital is updated after each closed trade

### Starting Capital

₹1,00,000 (1 Lakh)

### Data Range

Fetches 5 years of history (`period="5y"`) and filters to the specified `start` date.

### Metrics Calculated

| Metric | Formula |
|---|---|
| Win Rate | `(winning trades / total trades) × 100%` |
| Average Return | `mean(pnl_pct)` |
| Max Drawdown | `max(peak - trough) / peak × 100%` |
| Sharpe Ratio | `(mean_return - daily_rf) / std_return × √250` with 6% annual risk-free rate |
| Profit Factor | `gross_profit / gross_loss` |
| Total PnL | `sum(all trade pnl)` |

---

## 16. Data Flow

### Single Stock Analysis Flow

```
User requests "Analyze TCS"
        │
        ▼
   symbols: "TCS" or "TCS.NS"
        │
        ▼
   fetcher.py: strip .NS suffix → add .NS → "TCS.NS"
        │
   ┌────┴────┐
   │ Cache?  │
   │ (6hrs)  │
   └────┬────┘
     NO │ YES → return cached DataFrame
        ▼
   yf.download("TCS.NS", period="1y")
        │
        ▼
   validator.py: clean → check columns → drop NaN → check min rows
        │
        ▼
   cache.py: store in SQLite
        │
        ▼
   pipeline.py: add SMA, EMA, RSI, MACD, Stochastic, BB, ATR, OBV, Volume
        │                          (19 columns added)
        ▼
   df.iloc[-1].to_dict()  →  Latest row with all indicators
        │
        ▼
   scorer.py → score_technical()  →  Technical Score 0-10
        │
        ▼
   fetcher.py → fetch_fundamentals()  →  25+ metrics from yfinance
        │
        ▼
   analyzer.py → score_fundamentals()  →  Fundamental Score 0-10
        │
        ▼
   engine.py → composite_score = tech + fund  →  0-20
        │
        ▼
   Return full result dict (30+ fields)
```

### Full Screener Flow

```
Run Full Screen
       │
       ▼
  symbols.py → Load nifty50.csv (50 symbols)
       │
       ▼
  FOR EACH symbol:
       │
       ├→ screen_single(symbol)  →  result dict
       │      (includes 0.5s delay between API calls)
       │
       └→ Append to results list
       
       │
       ▼
  Sort results by composite_score DESC
       │
       ▼
  Return full ranked list
```

---

## 17. Dependencies

**File:** `quantedge/requirements.txt`

| Package | Version | Purpose |
|---|---|---|
| `yfinance` | ≥ 0.2.31 | Yahoo Finance API wrapper for OHLCV + fundamental data |
| `pandas` | ≥ 2.0.0 | DataFrame operations, data manipulation |
| `numpy` | ≥ 1.24.0 | Numerical calculations (Sharpe ratio, metrics) |
| `ta` | ≥ 0.11.0 | Technical analysis indicators (RSI, MACD, BB, ATR, OBV, Stochastic) |
| `rich` | ≥ 13.0.0 | Terminal rich-text formatting (tables, colors) |
| `schedule` | ≥ 1.2.0 | Task scheduling (for future cron-like features) |
| `fastapi` | ≥ 0.104.0 | REST API framework |
| `uvicorn[standard]` | ≥ 0.24.0 | ASGI server for FastAPI |
| `groq` | ≥ 0.11.0 | Groq SDK for LLM inference |
| `anthropic` | ≥ 0.39.0 | Anthropic SDK for Claude models |
| `python-dotenv` | ≥ 1.0.1 | Loads `.env` from project root |

**Standard library modules used:** `sqlite3`, `json`, `os`, `sys`, `csv`, `time`, `logging`, `argparse`, `urllib`, `datetime`, `pathlib`

---

## 18. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `AI_PROVIDER` | No | `groq` | `groq` or `anthropic` |
| `GROQ_API_KEY` | Conditionally | `""` | Required when `AI_PROVIDER=groq` |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model name |
| `ANTHROPIC_API_KEY` | Conditionally | `""` | Required when `AI_PROVIDER=anthropic` |
| `ANTHROPIC_MODEL` | No | `claude-3-5-sonnet-latest` | Claude model name |
| `AI_MIN_SCORE_THRESHOLD` | No | `10` | Minimum composite score to trigger AI during screening |
| `TELEGRAM_BOT_TOKEN` | No | `""` (disabled) | Telegram bot API token for alerts |
| `TELEGRAM_CHAT_ID` | No | `""` (disabled) | Telegram chat/channel ID for alerts |

### Recommended `.env` format

```dotenv
# AI provider
AI_PROVIDER=groq

# Groq
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile

# Anthropic Claude
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-5-sonnet-latest

# AI controls
AI_MIN_SCORE_THRESHOLD=10

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Set shell variables directly (alternative to `.env`):
```bash
# Linux/Mac/Git Bash
export AI_PROVIDER="groq"
export GROQ_API_KEY="your-groq-key"
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"

# Windows CMD
set AI_PROVIDER=anthropic
set ANTHROPIC_API_KEY=your-anthropic-key
set TELEGRAM_BOT_TOKEN=your-bot-token
set TELEGRAM_CHAT_ID=your-chat-id

# Windows PowerShell
$env:AI_PROVIDER="groq"
$env:GROQ_API_KEY="your-groq-key"
$env:TELEGRAM_BOT_TOKEN="your-bot-token"
$env:TELEGRAM_CHAT_ID="your-chat-id"
```

---

## 19. Sample Output

### CLI Output (TCS Single Stock)

```json
{
  "symbol": "TCS.NS",
  "name": "Tata Consultancy Services Limited",
  "sector": "Technology",
  "current_price": 2396.20,
  "stop_loss": 2276.39,
  "target": 2755.63,
  "risk_reward": 3.0,
  "technical_score": 2.5,
  "fundamental_score": 5.15,
  "composite_score": 7.65,
  "is_multibagger": false,
  "technical_details": {
    "above_200_sma": {"passed": false, "weight": 2.0, "desc": "Above 200 SMA"},
    "above_50_sma":  {"passed": false, "weight": 1.0, "desc": "Above 50 SMA"},
    "rsi_sweet_spot": {"passed": false, "weight": 1.5, "desc": "RSI 40-65"},
    "macd_bullish":  {"passed": true,  "weight": 1.5, "desc": "MACD Bullish"},
    "volume_spike":  {"passed": false, "weight": 1.5, "desc": "Volume Spike"},
    "bb_lower_half": {"passed": true,  "weight": 1.0, "desc": "BB Lower Half"},
    "ema_alignment": {"passed": false, "weight": 1.5, "desc": "EMA Aligned"}
  },
  "fundamental_details": {
    "revenue_growth": "4.9%",
    "profit_margin": "18.3%",
    "roe": "42.6%",
    "debt_to_equity": "0.09",
    "peg_ratio": "N/A",
    "earnings_growth": "-13.9%"
  },
  "rsi": 28.9,
  "macd": -120.5762,
  "sma_50": 2813.75,
  "sma_200": 3027.68,
  "pe_ratio": 18.16,
  "roe": 0.42635,
  "market_cap": 8669299736576,
  "timestamp": "2026-03-23T14:57:13.450695"
}
```

**Analysis of this result:**
- TCS scored 2.5/10 technically — below its 50 and 200 SMA, RSI at 28.9 (oversold), EMAs not aligned. Only MACD bullish and BB lower half passed.
- Scored 5.15/10 fundamentally — excellent ROE (42.6%), very low debt (D/E 0.09), good profit margin (18.3%), but weak recent growth.
- Composite 7.65/20 — below the 12-point minimum for a "pick"
- Not flagged as multibagger — negative earnings growth disqualifies it

---

## 20. Known Limitations

| # | Limitation | Impact | Workaround |
|---|---|---|---|
| 1 | **yfinance rate limits** | Screening 200 stocks is slow (~5–15 min) | Cache reduces re-fetch. Use Nifty 50 for faster runs |
| 2 | **yfinance data quality** | Some fields return `None` (e.g., PEG ratio) | Scoring handles `None` gracefully — assigns 0 or neutral |
| 3 | **No real-time data** | yfinance data is delayed (15–20 min for NSE) | Acceptable for swing trading (not intraday) |
| 4 | **Promoter holding** | yfinance's `major_holders` may not have "promoter" label for all stocks | Returns `None` if not found. Metric logged but not scored |
| 5 | **Debt/Equity normalization** | yfinance returns D/E in inconsistent units (ratio vs %) | Code normalizes: divides by 100 if value > 5 |
| 6 | **Backtest limitations** | No slippage, no transaction costs, no partial fills | Results are optimistic. Use as directional indicator only |
| 7 | **Single-threaded screening** | Stocks analyzed sequentially with 0.5s delay | Future: batch parallel fetch or async |
| 8 | **Frontend is SPA** | All JS/CSS in one 1494-line HTML file | Functional but not ideal for large-scale development |
| 9 | **In-memory screener results** | `_latest_results` in API is lost on server restart | Re-run screener after restart. Future: persist to DB |
| 10 | **No authentication** | API endpoints are open | Not designed for public deployment. Add auth if exposing externally |
| 11 | **LLM output variability** | AI brief phrasing can change across runs | Prompt constrains format, but wording remains stochastic |
| 12 | **Provider quotas / rate limits** | AI brief generation may fail intermittently | Retries can be added; screening already falls back safely |

---

## 21. Troubleshooting

### "No module named 'yfinance'" / Import errors

Virtual environment not activated. Run:
```bash
source venv/Scripts/activate   # Git Bash on Windows
```

### "TCS.NS.NS: possibly delisted"

Symbol suffix duplication — should not occur with the current code. If it does, check that `fetcher.py` has the `.NS` stripping logic in both `fetch_ohlcv` and `fetch_fundamentals`.

### "Empty DataFrame — skipping"

The stock may be genuinely delisted, or yfinance temporarily failed. Wait and retry, or check the symbol is valid on Yahoo Finance.

### Screener returns empty results

- Check internet connectivity
- Check that `data/nifty50.csv` exists and has a `Symbol` header
- Run a single stock first: `python -m quantedge.main --stock RELIANCE`

### Server won't start

- Check port 8000 isn't in use: `netstat -ano | findstr 8000` (Windows)
- Check uvicorn is installed: `pip show uvicorn`

### Cache seems stale

Delete the cache file:
```bash
rm quantedge/data/cache.db
```

### Frontend shows "Connection failed"

- Verify server is running
- Check browser console for CORS errors
- Ensure you're accessing `http://localhost:8000` (not `https://`)

### `/api/stock/{symbol}/ai-analysis` returns 503

- Confirm `.env` is in project root (`E:/StockMarket/.env`)
- Confirm `AI_PROVIDER` is set to `groq` or `anthropic`
- Confirm provider key is present for selected provider
- Restart the server after editing `.env`

### AI brief missing in screener results

- Check if stock `composite_score` is below `AI_MIN_SCORE_THRESHOLD`
- Check logs for warnings from `generate_trade_brief`
- Verify SDK dependency is installed (`groq` or `anthropic`)

---

## 22. AI Analyzer Deep Dive

This section documents the exact runtime behavior introduced by the AI integration.

### 22.1 Where AI runs

1. **Automatic mode (during screening)** in `screener/engine.py`
2. **On-demand mode (API call)** in `/api/stock/{symbol}/ai-analysis`
3. **Alert rendering mode** in `alerts/telegram.py` (includes `ai_brief` when available)

### 22.2 Automatic mode lifecycle

For each stock in `screen_single(symbol)`:

1. Compute technical score (0-10)
2. Compute fundamental score (0-10)
3. Compute `composite_score` (0-20)
4. Build result dictionary
5. If `AI_ENABLED` and `composite_score >= AI_MIN_SCORE_THRESHOLD`:
    - call `generate_trade_brief(result)`
    - store output in `result["ai_brief"]`
6. If AI fails:
    - log warning
    - set `result["ai_brief"] = None`
    - continue without interrupting screening

### 22.3 On-demand mode lifecycle

`GET /api/stock/{symbol}/ai-analysis`:

1. Validates AI is enabled
2. Runs `screen_single(symbol)`
3. Reuses `ai_brief` if already generated in that call
4. Otherwise calls `generate_trade_brief(result)`
5. Returns JSON with `symbol`, `ai_brief`, `timestamp`

### 22.4 Prompt contract used for trade brief

The trade brief prompt enforces strict output sections:

- `SETUP:` 1 sentence
- `EDGE:` 1 sentence
- `RISK:` 1 sentence
- `VERDICT:` one of `BUY ZONE`, `WAIT`, `AVOID` + short reason

### 22.5 AI payload minimization

Only decision-relevant fields are sent to the model:

- Symbol and sector
- Composite, technical, and fundamental scores
- Momentum metrics (`rsi`, `volume_ratio`)
- Price context (`current_price`, `stop_loss`, `target`)
- Passed technical rules
- Fundamental details summary

This reduces token usage and keeps prompts focused.

### 22.6 Cost control policy

AI calls are gated by `AI_MIN_SCORE_THRESHOLD`.

Example:
- threshold = 10
- 50-stock universe
- if 12 stocks pass threshold, only 12 AI calls are made

### 22.7 Reliability and fallback policy

- No AI key -> AI disabled
- Missing SDK -> warning + disabled behavior
- Runtime API error -> warning + `ai_brief=None`
- Screening and non-AI API endpoints continue to work normally

### 22.8 Security notes

- Keep API keys only in `.env`
- Do not commit `.env` to version control
- Rotate keys immediately if exposed in logs/chat/screenshots

### 22.9 Quick validation checklist

1. `pip install -r quantedge/requirements.txt`
2. Set `.env` values for provider and key
3. Start server: `python -m quantedge.main --server`
4. Test health: `GET /api/health`
5. Test AI: `GET /api/stock/TCS/ai-analysis`
6. Run screener and inspect whether high-scoring rows include `ai_brief`

---

*QuantEdge V1.0.0 — Built for finding multibagger stocks in the Indian market through quantitative analysis.*
