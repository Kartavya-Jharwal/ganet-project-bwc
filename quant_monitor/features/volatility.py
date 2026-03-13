"""Volatility features — realized vol, Hurst exponent, regime classifier.

Regimes: LOW_VOL_TREND | HIGH_VOL_TREND | LOW_VOL_RANGE | HIGH_VOL_RANGE | CRISIS

Key insight: Hurst exponent separates "volatile but trending" (ride it)
from "volatile and choppy" (reduce size).
"""

from __future__ import annotations

import logging
from enum import StrEnum

import pandas as pd

# pandas imported at runtime; TYPE_CHECKING may still be used elsewhere

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
    # rolling std dev of returns multiplied by sqrt(252) for annualization
    return returns.rolling(window=window).std() * (252**0.5)


def volatility_percentile(vol_series: pd.Series, lookback: int = 252) -> pd.Series:
    """Percentile rank of current vol vs trailing lookback period."""

    def pct_rank(window: pd.Series) -> float:
        # percentile of last value within window (excluding itself)
        if len(window) <= 1:
            return 0.5
        last = window.iloc[-1]
        # count values strictly less than last
        rank = (window.iloc[:-1] < last).sum()
        return rank / (len(window) - 1)

    return vol_series.rolling(window=lookback, min_periods=2).apply(pct_rank, raw=False)


def hurst_exponent(series: pd.Series, max_lag: int = 100) -> float:
    """Compute Hurst exponent using R/S analysis.

    H > 0.6 → trending (persistent)
    H ≈ 0.5 → random walk
    H < 0.4 → mean-reverting (anti-persistent)
    """
    import numpy as np

    ts = series.dropna().values
    n = len(ts)
    if n < 20:
        return 0.5  # not enough data, assume random walk

    max_k = min(max_lag, n // 2)
    lags = range(2, max_k + 1)

    rs_values = []
    for lag in lags:
        n_chunks = n // lag
        if n_chunks < 1:
            continue
        chunk_rs = []
        for i in range(n_chunks):
            chunk = ts[i * lag : (i + 1) * lag]
            mean = np.mean(chunk)
            dev = chunk - mean
            cum_dev = np.cumsum(dev)
            R = np.max(cum_dev) - np.min(cum_dev)
            S = np.std(chunk, ddof=1)
            if S > 0:
                chunk_rs.append(R / S)
        if chunk_rs:
            rs_values.append(np.mean(chunk_rs))
    if not rs_values:
        return 0.5
    # fit line to log(lag) vs log(R/S)
    logs = np.log(rs_values)
    log_lags = np.log(list(lags)[: len(rs_values)])
    # linear regression slope
    slope = np.polyfit(log_lags, logs, 1)[0]
    return slope


def classify_regime(
    realized_vol: float,
    vol_percentile: float,
    hurst: float,
    vix: float,
    vix_crisis_threshold: float = 30.0,
) -> VolRegime:
    """Classify current volatility regime from multiple inputs."""
    # Rule 1: VIX above crisis threshold → CRISIS
    if vix >= vix_crisis_threshold:
        return VolRegime.CRISIS

    # Rule 2: High/Low vol by percentile
    is_high_vol = vol_percentile > 0.5

    # Rule 3: Trending/Range by Hurst
    is_trending = hurst > 0.5

    if is_high_vol and is_trending:
        return VolRegime.HIGH_VOL_TREND
    elif is_high_vol and not is_trending:
        return VolRegime.HIGH_VOL_RANGE
    elif not is_high_vol and is_trending:
        return VolRegime.LOW_VOL_TREND
    else:
        return VolRegime.LOW_VOL_RANGE
