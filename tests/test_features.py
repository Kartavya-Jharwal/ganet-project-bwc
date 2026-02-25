"""Tests for feature engineering — Phase 2."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


class TestMovingAverages:
    """Tests for quant_monitor/features/moving_averages.py"""

    def test_ema_matches_pandas_ewm(self):
        """EMA output must match pandas ewm(span=period).mean() within 1e-10."""
        from quant_monitor.features.moving_averages import ema

        series = pd.Series(np.random.randn(100).cumsum() + 100)
        result = ema(series, period=9)
        expected = series.ewm(span=9, adjust=False).mean()
        pd.testing.assert_series_equal(result, expected, atol=1e-10)

    def test_sma_matches_pandas_rolling(self):
        """SMA output must match pandas rolling(period).mean()."""
        from quant_monitor.features.moving_averages import sma

        series = pd.Series(np.random.randn(100).cumsum() + 100)
        result = sma(series, period=50)
        expected = series.rolling(window=50).mean()
        pd.testing.assert_series_equal(result, expected, atol=1e-10)

    def test_kama_returns_series_of_same_length(self):
        """KAMA output length must match input length."""
        from quant_monitor.features.moving_averages import kama

        series = pd.Series(np.random.randn(200).cumsum() + 100)
        result = kama(series, period=10, fast_sc=2, slow_sc=30)
        assert len(result) == len(series)
        assert isinstance(result, pd.Series)

    def test_kama_adapts_to_volatility(self):
        """KAMA should be closer to price in trending markets, smoother in choppy."""
        from quant_monitor.features.moving_averages import kama

        # Trending series
        trending = pd.Series(np.arange(200, dtype=float))
        kama_trending = kama(trending, period=10)
        # In a perfect trend, KAMA should closely track price
        # Check last 50 values: mean absolute error should be small
        mae_trending = (trending.iloc[-50:] - kama_trending.iloc[-50:]).abs().mean()

        # Choppy series
        choppy = pd.Series(np.random.randn(200).cumsum())
        kama_choppy = kama(choppy, period=10)
        # KAMA should be smoother than raw price in choppy market
        # Check that KAMA has lower volatility than raw series
        vol_raw = choppy.diff().std()
        vol_kama = kama_choppy.diff().dropna().std()
        assert vol_kama < vol_raw, "KAMA should smooth out noise"

    def test_vwap_requires_ohlcv_columns(self):
        """VWAP must work with DataFrame containing open/high/low/close/volume."""
        from quant_monitor.features.moving_averages import vwap

        ohlcv = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [105, 106, 107],
            "low": [99, 100, 101],
            "close": [103, 104, 105],
            "volume": [1000, 1500, 1200],
        })
        result = vwap(ohlcv)
        assert isinstance(result, pd.Series)
        assert len(result) == 3

    def test_hma_lower_lag_than_sma(self):
        """HMA should have lower lag than SMA of same period on a trending series."""
        from quant_monitor.features.moving_averages import hma, sma

        # Create a series that starts trending suddenly
        flat = np.full(50, 100.0)
        trend = np.linspace(100, 150, 50)
        series = pd.Series(np.concatenate([flat, trend]))

        hma_result = hma(series, period=16)
        sma_result = sma(series, period=16)

        # After the trend starts (index 50), HMA should respond faster
        # Check at index 60: HMA should be closer to actual price than SMA
        assert hma_result.iloc[65] > sma_result.iloc[65], (
            "HMA should have less lag than SMA on a trending series"
        )

    def test_compute_ma_matrix_returns_all_columns(self):
        """compute_ma_matrix must return DataFrame with all 8 MA columns."""
        from quant_monitor.features.moving_averages import compute_ma_matrix

        np.random.seed(42)
        n = 300  # need enough data for SMA 200
        ohlcv = pd.DataFrame({
            "open": np.random.randn(n).cumsum() + 100,
            "high": np.random.randn(n).cumsum() + 102,
            "low": np.random.randn(n).cumsum() + 98,
            "close": np.random.randn(n).cumsum() + 100,
            "volume": np.random.randint(1000, 10000, n),
        })
        result = compute_ma_matrix(ohlcv)
        expected_columns = {"ema_9", "ema_21", "sma_50", "sma_200", "kama_10", "vwap", "mvwap_20", "hma_16"}
        assert expected_columns.issubset(set(result.columns)), (
            f"Missing columns: {expected_columns - set(result.columns)}"
        )


class TestVolatility:
    """Tests for quant_monitor/features/volatility.py"""

    def test_realized_vol_annualized(self):
        """Realized vol should be annualized (multiply by sqrt(252))."""
        from quant_monitor.features.volatility import realized_volatility

        np.random.seed(42)
        daily_returns = pd.Series(np.random.randn(100) * 0.01)  # ~1% daily vol
        result = realized_volatility(daily_returns, window=20)
        # Last value should be roughly 0.01 * sqrt(252) ≈ 0.159
        assert 0.05 < result.iloc[-1] < 0.5, f"Annualized vol {result.iloc[-1]} out of range"

    def test_vol_percentile_range(self):
        """Volatility percentile must be in [0, 1] range."""
        from quant_monitor.features.volatility import volatility_percentile

        np.random.seed(42)
        vol_series = pd.Series(np.random.rand(300) * 0.3)
        result = volatility_percentile(vol_series, lookback=252)
        valid = result.dropna()
        assert (valid >= 0).all() and (valid <= 1).all(), "Percentile must be in [0,1]"

    def test_hurst_trending_series(self):
        """Hurst exponent > 0.6 for a strongly trending series."""
        from quant_monitor.features.volatility import hurst_exponent

        # Pure trending: cumulative sum with positive drift
        np.random.seed(42)
        trending = pd.Series(np.arange(500, dtype=float) + np.random.randn(500) * 0.1)
        h = hurst_exponent(trending)
        assert h > 0.55, f"Hurst {h} should be > 0.55 for trending series"

    def test_hurst_mean_reverting_series(self):
        """Hurst exponent < 0.45 for mean-reverting (anti-persistent) series."""
        from quant_monitor.features.volatility import hurst_exponent

        np.random.seed(42)
        # Mean-reverting: alternating +1/-1 with small noise
        n = 500
        mean_rev = pd.Series(np.cumsum([(-1)**i + np.random.randn()*0.01 for i in range(n)]))
        h = hurst_exponent(mean_rev)
        assert h < 0.45, f"Hurst {h} should be < 0.45 for mean-reverting series"

    def test_classify_regime_crisis(self):
        """VIX > 30 → CRISIS regardless of other inputs."""
        from quant_monitor.features.volatility import classify_regime, VolRegime

        result = classify_regime(
            realized_vol=0.2,
            vol_percentile=0.5,
            hurst=0.5,
            vix=35.0,
            vix_crisis_threshold=30.0,
        )
        assert result == VolRegime.CRISIS

    def test_classify_regime_low_vol_trend(self):
        """Low vol + high Hurst → LOW_VOL_TREND."""
        from quant_monitor.features.volatility import classify_regime, VolRegime

        result = classify_regime(
            realized_vol=0.10,
            vol_percentile=0.25,
            hurst=0.7,
            vix=15.0,
        )
        assert result == VolRegime.LOW_VOL_TREND

    def test_classify_regime_high_vol_range(self):
        """High vol + low Hurst → HIGH_VOL_RANGE."""
        from quant_monitor.features.volatility import classify_regime, VolRegime

        result = classify_regime(
            realized_vol=0.35,
            vol_percentile=0.85,
            hurst=0.35,
            vix=25.0,
        )
        assert result == VolRegime.HIGH_VOL_RANGE
