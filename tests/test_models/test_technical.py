"""Tests for TechnicalModel."""
from __future__ import annotations

import numpy as np
import pandas as pd

from quant_monitor.models.technical import TechnicalModel


def _make_ohlcv(n: int = 250, trend: str = "flat") -> pd.DataFrame:
    """Build synthetic OHLCV data."""
    rng = np.random.default_rng(42)
    if trend == "up":
        close = np.linspace(100, 200, n) + rng.normal(0, 2, n)
    elif trend == "down":
        close = np.linspace(200, 100, n) + rng.normal(0, 2, n)
    else:
        close = np.full(n, 150.0) + rng.normal(0, 2, n)
    volume = rng.integers(1_000_000, 5_000_000, size=n).astype(float)
    df = pd.DataFrame(
        {
            "open": close * 0.998,
            "high": close * 1.005,
            "low": close * 0.995,
            "close": close,
            "volume": volume,
        }
    )
    return df


def _make_ma_matrix(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Compute a minimal MA matrix from synthetic OHLCV."""
    from quant_monitor.features.moving_averages import compute_ma_matrix
    return compute_ma_matrix(ohlcv)


class TestTechnicalModel:
    def setup_method(self):
        self.model = TechnicalModel()

    def test_score_returns_float_in_range(self):
        ohlcv = _make_ohlcv()
        ma = _make_ma_matrix(ohlcv)
        result = self.model.score(ohlcv, ma)
        assert isinstance(result, float)
        assert -1.0 <= result <= 1.0

    def test_uptrend_positive_score(self):
        ohlcv = _make_ohlcv(n=250, trend="up")
        ma = _make_ma_matrix(ohlcv)
        result = self.model.score(ohlcv, ma)
        assert result > 0, f"Expected positive score for uptrend, got {result}"

    def test_downtrend_negative_score(self):
        ohlcv = _make_ohlcv(n=250, trend="down")
        ma = _make_ma_matrix(ohlcv)
        result = self.model.score(ohlcv, ma)
        assert result < 0, f"Expected negative score for downtrend, got {result}"

    def test_score_all_returns_dict(self):
        tickers = {"AAPL": _make_ohlcv(trend="up"), "TSLA": _make_ohlcv(trend="down")}
        results = self.model.score_all(tickers)
        assert isinstance(results, dict)
        assert set(results.keys()) == {"AAPL", "TSLA"}
        for ticker, score in results.items():
            assert isinstance(score, float)
            assert -1.0 <= score <= 1.0

    def test_score_all_handles_bad_data(self):
        """score_all should return 0.0 for tickers with bad data, not raise."""
        bad_df = pd.DataFrame({"close": [np.nan] * 10, "volume": [0.0] * 10})
        results = self.model.score_all({"BAD": bad_df})
        assert "BAD" in results
        assert isinstance(results["BAD"], float)
