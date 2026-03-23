"""
QuantEdge FastAPI Dashboard — REST API powering the frontend.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from quantedge.screener.engine import screen_single, run_full_screen, get_top_picks, get_multibagger_candidates
from quantedge.backtester.engine import run_backtest
from quantedge.data_engine.fetcher import fetch_ohlcv, fetch_fundamentals
from quantedge.indicators.pipeline import apply_all_indicators
from quantedge.fundamentals.analyzer import score_fundamentals, get_fundamental_summary
from quantedge.ai_engine.analyst import generate_trade_brief
from quantedge.config import TOP_PICKS, AI_ENABLED

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="QuantEdge",
    description="Algorithmic Stock Screener for Indian Markets",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# In-memory cache for latest run
_latest_results: list[dict] = []
_last_run_time: str | None = None


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend page."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>QuantEdge — Frontend not found. Place index.html in dashboard/static/</h1>")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat(), "version": "1.0.0"}


@app.get("/api/screener/run")
async def run_screener(nifty200: bool = False):
    """
    Run the full screener. Returns all scored stocks.
    WARNING: This can take several minutes for 50-200 stocks.
    """
    global _latest_results, _last_run_time
    try:
        results = run_full_screen(use_nifty200=nifty200)
        _latest_results = results
        _last_run_time = datetime.now().isoformat()
        return {
            "total_screened": len(results),
            "timestamp": _last_run_time,
            "results": results,
        }
    except Exception as e:
        logger.error(f"Screener run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/screener/results")
async def get_results():
    """Get results from the latest screener run (cached in memory)."""
    if not _latest_results:
        return {"total_screened": 0, "timestamp": None, "results": [], "message": "No results yet. Run the screener first."}
    return {
        "total_screened": len(_latest_results),
        "timestamp": _last_run_time,
        "results": _latest_results,
    }


@app.get("/api/screener/top")
async def get_top(n: int = Query(default=TOP_PICKS, ge=1, le=50)):
    """Get top N picks from latest run."""
    if not _latest_results:
        return {"picks": [], "message": "No results yet. Run the screener first."}
    top = get_top_picks(_latest_results, n=n, min_score=0)
    return {"picks": top, "count": len(top)}


@app.get("/api/screener/multibaggers")
async def get_multibaggers():
    """Get stocks flagged as potential multibaggers."""
    if not _latest_results:
        return {"candidates": [], "message": "No results yet. Run the screener first."}
    mbs = get_multibagger_candidates(_latest_results)
    return {"candidates": mbs, "count": len(mbs)}


@app.get("/api/stock/{symbol}")
async def analyze_stock(symbol: str):
    """Run full analysis on a single stock."""
    symbol = symbol.upper().strip()
    try:
        result = screen_single(symbol)
        if result is None:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stock analysis failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{symbol}/ai-analysis")
async def get_ai_analysis(symbol: str):
    """Return on-demand AI trade brief for a single stock."""
    if not AI_ENABLED:
        raise HTTPException(status_code=503, detail="AI is disabled. Set GROQ_API_KEY to enable.")

    symbol = symbol.upper().strip()
    try:
        result = screen_single(symbol)
        if result is None:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        brief = result.get("ai_brief") or generate_trade_brief(result)
        return {
            "symbol": symbol,
            "ai_brief": brief,
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI analysis failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{symbol}/chart")
async def get_chart_data(symbol: str, period: str = "6mo"):
    """Get OHLCV + indicator data for charting."""
    symbol = symbol.upper().strip()
    df = fetch_ohlcv(symbol, period=period)
    if df is None:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")

    df = apply_all_indicators(df)
    df = df.tail(120)  # Last 120 days

    records = []
    for date, row in df.iterrows():
        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(row.get("Open", 0), 2),
            "high": round(row.get("High", 0), 2),
            "low": round(row.get("Low", 0), 2),
            "close": round(row.get("Close", 0), 2),
            "volume": int(row.get("Volume", 0)),
            "sma_20": round(row.get("SMA_20", 0), 2) if row.get("SMA_20") else None,
            "sma_50": round(row.get("SMA_50", 0), 2) if row.get("SMA_50") else None,
            "sma_200": round(row.get("SMA_200", 0), 2) if row.get("SMA_200") else None,
            "rsi": round(row.get("RSI", 0), 2) if row.get("RSI") else None,
            "macd": round(row.get("MACD", 0), 4) if row.get("MACD") else None,
            "macd_signal": round(row.get("MACD_SIGNAL", 0), 4) if row.get("MACD_SIGNAL") else None,
            "bb_upper": round(row.get("BB_UPPER", 0), 2) if row.get("BB_UPPER") else None,
            "bb_lower": round(row.get("BB_LOWER", 0), 2) if row.get("BB_LOWER") else None,
        })

    return {"symbol": symbol, "data": records}


@app.get("/api/stock/{symbol}/fundamentals")
async def get_fundamentals(symbol: str):
    """Get fundamental analysis for a single stock."""
    symbol = symbol.upper().strip()
    data = fetch_fundamentals(symbol)
    if not data:
        raise HTTPException(status_code=404, detail=f"No fundamental data for {symbol}")

    scored = score_fundamentals(data)
    summary = get_fundamental_summary(data)
    return {
        "symbol": symbol,
        "raw": data,
        "scored": scored,
        "summary": summary,
    }


@app.get("/api/backtest/{symbol}")
async def backtest_stock(
    symbol: str,
    start: str = "2022-01-01",
    stop_loss: float = 0.05,
    target: float = 0.15,
):
    """Run backtest on a symbol."""
    symbol = symbol.upper().strip()
    try:
        result = run_backtest(symbol, start=start, stop_loss_pct=stop_loss, target_pct=target)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backtest failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
