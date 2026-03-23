"""
Backtest Engine — Simulate trades on historical data.
"""

import pandas as pd
import logging
from datetime import datetime

from ..data_engine.fetcher import fetch_ohlcv
from ..indicators.pipeline import apply_all_indicators
from ..screener.scorer import score_technical
from ..config import DEFAULT_STOP_LOSS_PCT, DEFAULT_TARGET_PCT
from .metrics import generate_metrics

logger = logging.getLogger(__name__)


def run_backtest(
    symbol: str,
    start: str = "2022-01-01",
    stop_loss_pct: float = DEFAULT_STOP_LOSS_PCT,
    target_pct: float = DEFAULT_TARGET_PCT,
    min_tech_score: float = 5.0,
) -> dict:
    """
    Backtest a symbol using the screener rules.
    Simulates entry when technical score exceeds threshold,
    exit on stop loss or target hit.
    """
    df = fetch_ohlcv(symbol, period="5y", use_cache=False)
    if df is None:
        return {"error": f"No data for {symbol}"}

    df = apply_all_indicators(df)

    # Filter to start date
    df = df[df.index >= start]
    if len(df) < 20:
        return {"error": f"Not enough data for {symbol} from {start}"}

    trades = []
    equity_curve = [100000.0]  # Start with 1L
    capital = 100000.0
    position = None

    for i in range(1, len(df)):
        row = df.iloc[i].to_dict()
        price = row["Close"]

        if position is None:
            # Check entry signal
            result = score_technical(row)
            if result["technical_score"] >= min_tech_score:
                position = {
                    "entry_date": df.index[i].strftime("%Y-%m-%d"),
                    "entry_price": price,
                    "stop_loss": price * (1 - stop_loss_pct),
                    "target": price * (1 + target_pct),
                    "shares": int(capital * 0.1 / price),  # 10% position size
                }
        else:
            # Check exit conditions
            exit_reason = None
            if price <= position["stop_loss"]:
                exit_reason = "stop_loss"
            elif price >= position["target"]:
                exit_reason = "target"

            if exit_reason:
                shares = position["shares"]
                pnl = (price - position["entry_price"]) * shares
                pnl_pct = (price - position["entry_price"]) / position["entry_price"] * 100

                trades.append({
                    "symbol": symbol,
                    "entry_date": position["entry_date"],
                    "exit_date": df.index[i].strftime("%Y-%m-%d"),
                    "entry_price": round(position["entry_price"], 2),
                    "exit_price": round(price, 2),
                    "shares": shares,
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl_pct, 2),
                    "exit_reason": exit_reason,
                })
                capital += pnl
                position = None

        equity_curve.append(capital)

    metrics = generate_metrics(trades, equity_curve)
    metrics["symbol"] = symbol
    metrics["period"] = f"{start} to {df.index[-1].strftime('%Y-%m-%d')}"

    return {
        "metrics": metrics,
        "trades": trades,
        "equity_curve": equity_curve[-60:],  # Last 60 points for chart
    }
