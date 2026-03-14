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
from scipy.stats import norm

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
        "sortino_ratio": sortino_ratio(returns),
        "kappa_ratio": kappa_ratio(returns),
        "cornish_fisher_var": cornish_fisher_var(returns),
        "conditional_var": conditional_var(returns),
        "tail_ratio": tail_ratio(returns),
        "drawdown_duration": drawdown_duration(returns),
        "calmar_ratio": calmar_ratio(returns),
        "max_drawdown": max_drawdown(returns),
        "hit_rate": hit_rate(signals),
    }


def sortino_ratio(
    returns: pd.Series, risk_free_rate: float = 0.0, target_return: float = 0.0
) -> float:
    """Sortino ratio = (mean_return - risk_free_daily) / downside_deviation * sqrt(252)."""
    if returns.empty or returns.std() == 0:
        return 0.0
    daily_rf = risk_free_rate / 252
    excess = returns - daily_rf
    downside_returns = returns[returns < target_return]
    if downside_returns.empty:
        return float("inf")
    downside_dev = np.sqrt((downside_returns**2).mean())
    if downside_dev == 0:
        return 0.0
    return float(excess.mean() / downside_dev * np.sqrt(252))


def kappa_ratio(returns: pd.Series, threshold: float = 0.0, n: float = 3) -> float:
    """Kappa ratio = (mean_return - threshold) / (LPM_n)^(1/n)."""
    if returns.empty:
        return 0.0
    excess = returns - threshold
    lpm = np.mean(np.maximum(threshold - returns, 0) ** n)
    if lpm == 0:
        return float("inf")
    return float(excess.mean() / (lpm ** (1 / n)) * (252 ** (1 - 1 / n)))  # Scaled approximation


def cornish_fisher_var(returns: pd.Series, alpha: float = 0.05) -> float:
    """Cornish-Fisher Value at Risk (Adjusted for skewness and kurtosis)."""
    if len(returns) < 4:
        return 0.0
    z_c = norm.ppf(alpha)
    s = returns.skew()
    k = returns.kurtosis()
    z_cf = (
        z_c
        + (1 / 6) * (z_c**2 - 1) * s
        + (1 / 24) * (z_c**3 - 3 * z_c) * k
        - (1 / 36) * (2 * z_c**3 - 5 * z_c) * (s**2)
    )
    return float(-(returns.mean() + z_cf * returns.std()))


def conditional_var(returns: pd.Series, alpha: float = 0.05) -> float:
    """Conditional VaR (Expected Shortfall). average of returns below alpha VaR."""
    if returns.empty:
        return 0.0
    empirical_var = returns.quantile(alpha)
    worst_cases = returns[returns <= empirical_var]
    if worst_cases.empty:
        return 0.0
    return float(-worst_cases.mean())


def tail_ratio(returns: pd.Series) -> float:
    """Tail Ratio = abs(95th percentile / 5th percentile)."""
    if returns.empty:
        return 0.0
    p95 = returns.quantile(0.95)
    p05 = returns.quantile(0.05)
    if p05 == 0:
        return 0.0
    return float(abs(p95 / p05))


def drawdown_duration(returns: pd.Series) -> int:
    """Maximum contiguous days underwater."""
    if returns.empty:
        return 0
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdowns = running_max - cumulative

    underwater = drawdowns > 0
    # Find longest stretch of True
    return int(
        (
            underwater
            * (underwater.groupby((underwater != underwater.shift()).cumsum()).cumcount() + 1)
        ).max()
    )
