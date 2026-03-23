"""
Backtest Metrics — Win rate, Sharpe ratio, max drawdown, etc.
"""

import pandas as pd
import numpy as np


def calc_win_rate(trades: list[dict]) -> float:
    """Percentage of profitable trades."""
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t["pnl"] > 0)
    return round(wins / len(trades) * 100, 2)


def calc_avg_return(trades: list[dict]) -> float:
    """Average return per trade (%)."""
    if not trades:
        return 0.0
    returns = [t["pnl_pct"] for t in trades]
    return round(np.mean(returns), 2)


def calc_max_drawdown(equity_curve: list[float]) -> float:
    """Maximum peak-to-trough decline (%)."""
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)


def calc_sharpe_ratio(trades: list[dict], risk_free_rate: float = 0.06) -> float:
    """Annualized Sharpe ratio (assuming ~250 trading days)."""
    if len(trades) < 2:
        return 0.0
    returns = [t["pnl_pct"] / 100 for t in trades]
    avg_ret = np.mean(returns)
    std_ret = np.std(returns)
    if std_ret == 0:
        return 0.0
    daily_rf = risk_free_rate / 250
    sharpe = (avg_ret - daily_rf) / std_ret * np.sqrt(250)
    return round(sharpe, 2)


def calc_profit_factor(trades: list[dict]) -> float:
    """Gross profit / Gross loss."""
    gross_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return round(gross_profit / gross_loss, 2)


def generate_metrics(trades: list[dict], equity_curve: list[float]) -> dict:
    """Generate all backtest metrics."""
    return {
        "total_trades": len(trades),
        "win_rate": calc_win_rate(trades),
        "avg_return_pct": calc_avg_return(trades),
        "max_drawdown_pct": calc_max_drawdown(equity_curve),
        "sharpe_ratio": calc_sharpe_ratio(trades),
        "profit_factor": calc_profit_factor(trades),
        "total_pnl": round(sum(t["pnl"] for t in trades), 2),
        "best_trade_pct": round(max((t["pnl_pct"] for t in trades), default=0), 2),
        "worst_trade_pct": round(min((t["pnl_pct"] for t in trades), default=0), 2),
    }
