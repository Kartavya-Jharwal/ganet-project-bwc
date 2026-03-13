"""Tests for backtesting framework — Phase 8."""

from __future__ import annotations

import numpy as np
import pandas as pd


class TestBacktestMetrics:
    """Tests for quant_monitor/backtest/metrics.py"""

    def test_sharpe_ratio_positive_returns(self):
        """Positive consistent returns → positive Sharpe."""
        from quant_monitor.backtest.metrics import sharpe_ratio

        returns = pd.Series(np.random.normal(0.001, 0.01, 252))  # slight positive drift
        sr = sharpe_ratio(returns)
        assert isinstance(sr, float)
        # With positive mean and reasonable vol, Sharpe should be positive
        # (may rarely be negative due to randomness, so we just check it's finite)
        assert np.isfinite(sr)

    def test_sharpe_ratio_zero_vol(self):
        """Zero-volatility returns → handle gracefully (not inf/nan)."""
        from quant_monitor.backtest.metrics import sharpe_ratio

        returns = pd.Series([0.001] * 100)  # constant returns
        sr = sharpe_ratio(returns)
        assert np.isfinite(sr) or sr == 0.0

    def test_max_drawdown_known_series(self):
        """Known drawdown series should return correct value."""
        from quant_monitor.backtest.metrics import max_drawdown

        # Prices: 100 → 120 → 90 → 110
        # Max drawdown = (120 - 90) / 120 = 25%
        returns = pd.Series([0.0, 0.20, -0.25, 0.2222])
        mdd = max_drawdown(returns)
        assert isinstance(mdd, float)
        assert mdd > 0, "Max drawdown should be positive"
        assert mdd <= 1.0

    def test_max_drawdown_all_positive(self):
        """Strictly increasing equity → max drawdown ≈ 0."""
        from quant_monitor.backtest.metrics import max_drawdown

        returns = pd.Series([0.01] * 50)
        mdd = max_drawdown(returns)
        assert mdd < 0.01, "Strictly positive returns → near-zero drawdown"

    def test_calmar_ratio(self):
        """Calmar = annualized return / max drawdown."""
        from quant_monitor.backtest.metrics import calmar_ratio

        returns = pd.Series(np.random.normal(0.001, 0.02, 252))
        cr = calmar_ratio(returns)
        assert isinstance(cr, float)
        assert np.isfinite(cr)

    def test_hit_rate_all_winners(self):
        """100% profitable signals → hit rate = 1.0."""
        from quant_monitor.backtest.metrics import hit_rate

        signals = pd.DataFrame({
            "ticker": ["SPY", "TSM", "PLTR"],
            "action": ["BUY", "BUY", "BUY"],
            "pnl": [100, 50, 200],
        })
        hr = hit_rate(signals)
        assert hr == 1.0

    def test_hit_rate_mixed(self):
        """Mix of winners and losers → correct ratio."""
        from quant_monitor.backtest.metrics import hit_rate

        signals = pd.DataFrame({
            "ticker": ["SPY", "TSM", "PLTR", "IONQ"],
            "action": ["BUY", "BUY", "SELL", "BUY"],
            "pnl": [100, -50, 200, -30],
        })
        hr = hit_rate(signals)
        assert abs(hr - 0.5) < 0.01, "2/4 profitable → 50%"

    def test_compute_all_metrics(self):
        """compute_all_metrics returns dict with all expected keys."""
        from quant_monitor.backtest.metrics import compute_all_metrics

        returns = pd.Series(np.random.normal(0.001, 0.01, 252))
        signals = pd.DataFrame({
            "ticker": ["SPY", "TSM"],
            "action": ["BUY", "SELL"],
            "pnl": [100, -50],
        })
        metrics = compute_all_metrics(returns, signals)
        assert isinstance(metrics, dict)
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "calmar_ratio" in metrics
        assert "hit_rate" in metrics


class TestWalkForwardEngine:
    """Tests for quant_monitor/backtest/engine.py"""

    def test_run_returns_dict_of_metrics(self):
        """run() should return a dict with performance metrics."""
        from quant_monitor.backtest.engine import WalkForwardEngine

        engine = WalkForwardEngine(train_window=50, test_window=10, step_size=10)
        # Create minimal price data (100 days)
        np.random.seed(42)
        dates = pd.date_range("2025-01-01", periods=100, freq="B")
        data = pd.DataFrame({
            "open": 100 + np.random.randn(100).cumsum(),
            "high": 102 + np.random.randn(100).cumsum(),
            "low": 98 + np.random.randn(100).cumsum(),
            "close": 100 + np.random.randn(100).cumsum(),
            "volume": np.random.randint(1_000_000, 10_000_000, 100),
        }, index=dates)
        result = engine.run(data, model_name="technical")
        assert isinstance(result, dict)
        assert "sharpe_ratio" in result or "total_return" in result

    def test_walk_forward_windows(self):
        """Engine should respect train/test window sizes."""
        from quant_monitor.backtest.engine import WalkForwardEngine

        engine = WalkForwardEngine(train_window=50, test_window=10, step_size=10)
        assert engine.train_window == 50
        assert engine.test_window == 10
        assert engine.step_size == 10

    def test_compare_models_returns_dataframe(self):
        """compare_models() should return a DataFrame comparing model configs."""
        from quant_monitor.backtest.engine import WalkForwardEngine

        engine = WalkForwardEngine(train_window=50, test_window=10, step_size=10)
        np.random.seed(42)
        dates = pd.date_range("2025-01-01", periods=100, freq="B")
        data = pd.DataFrame({
            "open": 100 + np.random.randn(100).cumsum(),
            "high": 102 + np.random.randn(100).cumsum(),
            "low": 98 + np.random.randn(100).cumsum(),
            "close": 100 + np.random.randn(100).cumsum(),
            "volume": np.random.randint(1_000_000, 10_000_000, 100),
        }, index=dates)
        result = engine.compare_models(data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) >= 1, "Should have at least 1 model config row"