"""Backtest performance metrics.

Metrics reported:
- Sharpe Ratio (annualized)
- Calmar Ratio (return / max drawdown)
- Maximum Drawdown
- Hit Rate (% of signals that were profitable)
- Average Holding Period
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualized Sharpe Ratio.

    SR = (mean_return - risk_free_daily) / std_return * sqrt(252)
    """
    if returns.empty or returns.std() == 0:
        return 0.0
    daily_rf = risk_free_rate / 252
    excess = returns - daily_rf
    return float(excess.mean() / excess.std() * np.sqrt(252))


def calmar_ratio(returns: pd.Series) -> float:
    """Calmar Ratio = annualized return / max drawdown."""
    mdd = max_drawdown(returns)
    if mdd == 0:
        return 0.0
    annual_return = (1 + returns).prod() ** (252 / len(returns)) - 1
    return float(annual_return / mdd)


def max_drawdown(returns: pd.Series) -> float:
    """Maximum drawdown from peak to trough.

    Returns positive value (e.g., 0.25 = 25% drawdown).
    """
    if returns.empty:
        return 0.0
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdowns = (running_max - cumulative) / running_max
    return float(drawdowns.max())


def hit_rate(signals: pd.DataFrame) -> float:
    """Percentage of signals that resulted in profitable trades.

    Expects 'pnl' column: positive = profitable.
    """
    if signals.empty or "pnl" not in signals.columns:
        return 0.0
    profitable = (signals["pnl"] > 0).sum()
    return float(profitable / len(signals))


def avg_holding_period(trades: pd.DataFrame) -> float:
    """Average holding period in days.

    Expects 'entry_date' and 'exit_date' columns.
    """
    if trades.empty:
        return 0.0
    if "entry_date" in trades.columns and "exit_date" in trades.columns:
        durations = (
            pd.to_datetime(trades["exit_date"]) - pd.to_datetime(trades["entry_date"])
        ).dt.days
        return float(durations.mean())
    return 0.0


def compute_all_metrics(returns: pd.Series, signals: pd.DataFrame) -> dict:
    """Compute all metrics and return as dict."""
    return {
        "sharpe_ratio": sharpe_ratio(returns),
        "calmar_ratio": calmar_ratio(returns),
        "max_drawdown": max_drawdown(returns),
        "hit_rate": hit_rate(signals),
    }
