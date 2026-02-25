"""Moving average computations — EMA, SMA, KAMA, VWAP, HMA, MVWAP.

All functions take a pandas Series/DataFrame and return computed MA values.
Config-driven periods loaded from config.toml [moving_averages].
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd

# TYPE_CHECKING import no longer needed for runtime

logger = logging.getLogger(__name__)


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    # Phase 2 implementation – standard EMA using pandas
    # adjust=False yields the recursive EMA formula used in finance
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    # Phase 2 implementation — rolling mean
    return series.rolling(window=period).mean()


def kama(series: pd.Series, period: int = 10, fast_sc: int = 2, slow_sc: int = 30) -> pd.Series:
    """Kaufman Adaptive Moving Average — adjusts speed based on volatility."""
    import pandas as pd  # local import to avoid TYPE_CHECKING only

    # Efficiency ratio calculation
    direction = (series - series.shift(period)).abs()
    volatility = series.diff().abs().rolling(period).sum()
    er = direction / volatility

    fast_alpha = 2 / (fast_sc + 1)
    slow_alpha = 2 / (slow_sc + 1)
    sc = (er * (fast_alpha - slow_alpha) + slow_alpha) ** 2

    # prepare output series
    kama_vals = pd.Series(index=series.index, dtype=float)
    # initialize at first non-NaN point
    if len(series) >= period:
        kama_vals.iloc[period - 1] = series.iloc[period - 1]
    else:
        # if series shorter than period just return nan series
        return kama_vals

    # iterative computation
    for i in range(period, len(series)):
        prev = kama_vals.iloc[i - 1]
        kama_vals.iloc[i] = prev + sc.iloc[i] * (series.iloc[i] - prev)

    return kama_vals


def vwap(ohlcv: pd.DataFrame) -> pd.Series:
    """Session-anchored Volume-Weighted Average Price."""
    # ensure required columns exist
    required = {"high", "low", "close", "volume"}
    if not required.issubset(set(ohlcv.columns)):
        missing = required - set(ohlcv.columns)
        raise ValueError(f"VWAP requires columns {missing}")

    typical_price = (ohlcv["high"] + ohlcv["low"] + ohlcv["close"]) / 3
    tp_vol = typical_price * ohlcv["volume"]
    cum_tp_vol = tp_vol.cumsum()
    cum_vol = ohlcv["volume"].cumsum()
    return (cum_tp_vol / cum_vol).rename("vwap")


def mvwap(ohlcv: pd.DataFrame, period: int = 20) -> pd.Series:
    """Moving VWAP — N-day rolling VWAP. Institutional price reference."""
    # reuse typical price
    typical_price = (ohlcv["high"] + ohlcv["low"] + ohlcv["close"]) / 3
    tp_vol = (typical_price * ohlcv["volume"]).rolling(window=period).sum()
    vol_sum = ohlcv["volume"].rolling(window=period).sum()
    return (tp_vol / vol_sum).rename("mvwap")


def hma(series: pd.Series, period: int = 16) -> pd.Series:
    """Hull Moving Average — low-lag responsive trend signal."""
    import numpy as np

    def weighted_ma(s: pd.Series, w: int) -> pd.Series:
        weights = np.arange(1, w + 1, dtype=float)
        return s.rolling(window=w).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )

    half_period = period // 2
    sqrt_period = int(np.sqrt(period))

    wma_half = weighted_ma(series, half_period)
    wma_full = weighted_ma(series, period)
    diff = 2 * wma_half - wma_full
    return weighted_ma(diff, sqrt_period).rename("hma")


def compute_ma_matrix(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Compute full MA matrix for a single ticker. Returns DataFrame with all MAs as columns."""
    import pandas as pd
    from quant_monitor.config import cfg

    # assume ohlcv columns are lowercase and include open/high/low/close/volume
    result = pd.DataFrame(index=ohlcv.index)

    # EMA periods
    fast = cfg.moving_averages.get("ema_fast")
    medium = cfg.moving_averages.get("ema_medium")
    if fast:
        result[f"ema_{fast}"] = ema(ohlcv["close"], period=fast)
    if medium:
        result[f"ema_{medium}"] = ema(ohlcv["close"], period=medium)

    # SMA periods
    sma_med = cfg.moving_averages.get("sma_medium")
    sma_long = cfg.moving_averages.get("sma_long")
    if sma_med:
        result[f"sma_{sma_med}"] = sma(ohlcv["close"], period=sma_med)
    if sma_long:
        result[f"sma_{sma_long}"] = sma(ohlcv["close"], period=sma_long)

    # KAMA
    kama_period = cfg.moving_averages.get("kama_period")
    if kama_period:
        result[f"kama_{kama_period}"] = kama(ohlcv["close"], period=kama_period)

    # VWAP
    result["vwap"] = vwap(ohlcv)

    # MVWAP
    mvwap_period = cfg.moving_averages.get("mvwap_period")
    if mvwap_period:
        result[f"mvwap_{mvwap_period}"] = mvwap(ohlcv, period=mvwap_period)

    # HMA
    hma_period = cfg.moving_averages.get("hma_period")
    if hma_period:
        result[f"hma_{hma_period}"] = hma(ohlcv["close"], period=hma_period)

    return result
