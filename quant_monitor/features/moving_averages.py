"""Moving average computations — EMA, SMA, KAMA, VWAP, HMA, MVWAP.

All functions take a pandas Series/DataFrame and return computed MA values.
Config-driven periods loaded from config.toml [moving_averages].
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    # TODO Phase 2
    raise NotImplementedError


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    # TODO Phase 2
    raise NotImplementedError


def kama(series: pd.Series, period: int = 10, fast_sc: int = 2, slow_sc: int = 30) -> pd.Series:
    """Kaufman Adaptive Moving Average — adjusts speed based on volatility."""
    # TODO Phase 2
    raise NotImplementedError


def vwap(ohlcv: pd.DataFrame) -> pd.Series:
    """Session-anchored Volume-Weighted Average Price."""
    # TODO Phase 2
    raise NotImplementedError


def mvwap(ohlcv: pd.DataFrame, period: int = 20) -> pd.Series:
    """Moving VWAP — N-day rolling VWAP. Institutional price reference."""
    # TODO Phase 2
    raise NotImplementedError


def hma(series: pd.Series, period: int = 16) -> pd.Series:
    """Hull Moving Average — low-lag responsive trend signal."""
    # TODO Phase 2
    raise NotImplementedError


def compute_ma_matrix(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Compute full MA matrix for a single ticker. Returns DataFrame with all MAs as columns."""
    # TODO Phase 2: Use config periods, compute all MAs, return combined df
    raise NotImplementedError
