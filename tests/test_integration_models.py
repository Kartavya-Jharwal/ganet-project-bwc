"""Integration test: data pipeline → feature engineering → model scoring.

This test requires Doppler secrets and network access.
Run with: doppler run -- uv run pytest tests/test_integration_models.py -v
"""

from __future__ import annotations

import pytest
import pandas as pd


@pytest.mark.integration
class TestFullPipeline:
    """End-to-end tests from data pull to model scoring."""

    def test_pipeline_to_technical_score(self):
        """Fetch data → compute MAs → score with technical model."""
        from quant_monitor.data.pipeline import DataPipeline
        from quant_monitor.features.moving_averages import compute_ma_matrix
        from quant_monitor.models.technical import TechnicalModel

        pipeline = DataPipeline()
        # Fetch 1 year of data for SPY
        prices = pipeline.fetch_prices(["SPY"], period="1y")
        # fetch_prices returns a MultiIndex (ticker, date) DataFrame
        assert "SPY" in prices.index.get_level_values(0), "SPY not found in prices index"
        ohlcv = prices.xs("SPY", level=0)
        assert len(ohlcv) > 200, "Need > 200 rows for SMA 200"

        ma_matrix = compute_ma_matrix(ohlcv)
        assert "ema_9" in ma_matrix.columns
        assert "sma_200" in ma_matrix.columns

        model = TechnicalModel()
        score = model.score(ohlcv, ma_matrix)
        assert -1.0 <= score <= 1.0
        print(f"SPY technical score: {score:.4f}")

    def test_pipeline_to_macro_score(self):
        """Fetch FRED data → score with macro model."""
        from quant_monitor.data.pipeline import DataPipeline
        from quant_monitor.models.macro import MacroModel

        pipeline = DataPipeline()
        macro = pipeline.fetch_macro()
        assert "vix" in macro

        model = MacroModel()
        score = model.score(macro)
        assert -1.0 <= score <= 1.0

        regime = model.classify_regime(macro)
        assert regime in ("RISK_ON", "TRANSITION", "CRISIS")
        print(f"Macro score: {score:.4f}, regime: {regime}")

    def test_pipeline_to_volatility_regime(self):
        """Fetch data → compute vol features → classify regime."""
        from quant_monitor.data.pipeline import DataPipeline
        from quant_monitor.features.volatility import (
            realized_volatility,
            volatility_percentile,
            hurst_exponent,
            classify_regime,
        )

        pipeline = DataPipeline()
        prices = pipeline.fetch_prices(["SPY"], period="1y")
        # fetch_prices returns a MultiIndex (ticker, date) DataFrame
        ohlcv = prices.xs("SPY", level=0)
        returns = ohlcv["close"].pct_change().dropna()

        vol = realized_volatility(returns, window=20)
        vol_pct = volatility_percentile(vol.dropna(), lookback=252)
        hurst = hurst_exponent(ohlcv["close"])

        macro = pipeline.fetch_macro()
        vix = macro.get("vix", 20.0)

        regime = classify_regime(
            realized_vol=vol.iloc[-1],
            vol_percentile=vol_pct.iloc[-1],
            hurst=hurst,
            vix=vix,
        )
        print(f"Vol: {vol.iloc[-1]:.4f}, Percentile: {vol_pct.iloc[-1]:.2f}, "
              f"Hurst: {hurst:.3f}, VIX: {vix}, Regime: {regime}")
        assert regime in ("LOW_VOL_TREND", "HIGH_VOL_TREND", "LOW_VOL_RANGE",
                         "HIGH_VOL_RANGE", "CRISIS")
