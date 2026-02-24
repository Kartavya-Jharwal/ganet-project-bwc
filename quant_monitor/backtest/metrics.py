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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualized Sharpe Ratio."""
    # TODO Phase 8
    raise NotImplementedError


def calmar_ratio(returns: pd.Series) -> float:
    """Calmar Ratio = annualized return / max drawdown."""
    # TODO Phase 8
    raise NotImplementedError


def max_drawdown(returns: pd.Series) -> float:
    """Maximum drawdown from peak to trough."""
    # TODO Phase 8
    raise NotImplementedError


def hit_rate(signals: pd.DataFrame) -> float:
    """Percentage of signals that resulted in profitable trades."""
    # TODO Phase 8
    raise NotImplementedError


def avg_holding_period(trades: pd.DataFrame) -> float:
    """Average holding period in days."""
    # TODO Phase 8
    raise NotImplementedError


def compute_all_metrics(returns: pd.Series, signals: pd.DataFrame) -> dict:
    """Compute all metrics and return as dict."""
    # TODO Phase 8
    raise NotImplementedError
