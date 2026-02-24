"""Volatility features — realized vol, Hurst exponent, regime classifier.

Regimes: LOW_VOL_TREND | HIGH_VOL_TREND | LOW_VOL_RANGE | HIGH_VOL_RANGE | CRISIS

Key insight: Hurst exponent separates "volatile but trending" (ride it)
from "volatile and choppy" (reduce size).
"""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class VolRegime(StrEnum):
    """Volatility regime classifications."""

    LOW_VOL_TREND = "LOW_VOL_TREND"
    HIGH_VOL_TREND = "HIGH_VOL_TREND"
    LOW_VOL_RANGE = "LOW_VOL_RANGE"
    HIGH_VOL_RANGE = "HIGH_VOL_RANGE"
    CRISIS = "CRISIS"


def realized_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
    """Annualized rolling realized volatility."""
    # TODO Phase 2
    raise NotImplementedError


def volatility_percentile(vol_series: pd.Series, lookback: int = 252) -> pd.Series:
    """Percentile rank of current vol vs trailing lookback period."""
    # TODO Phase 2
    raise NotImplementedError


def hurst_exponent(series: pd.Series, max_lag: int = 100) -> float:
    """Compute Hurst exponent using R/S analysis.

    H > 0.6 → trending (persistent)
    H ≈ 0.5 → random walk
    H < 0.4 → mean-reverting (anti-persistent)
    """
    # TODO Phase 2 — this is one of the genuinely hard parts
    raise NotImplementedError


def classify_regime(
    realized_vol: float,
    vol_percentile: float,
    hurst: float,
    vix: float,
    vix_crisis_threshold: float = 30.0,
) -> VolRegime:
    """Classify current volatility regime from multiple inputs."""
    # TODO Phase 2
    raise NotImplementedError
