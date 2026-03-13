"""End-to-end integration test: full pipeline → fusion → alerts.

Run with: doppler run -- uv run pytest tests/test_integration_e2e.py -v
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestEndToEnd:
    """Full system integration tests."""

    def test_signal_cycle_runs_without_crash(self):
        """The full signal cycle should complete without exceptions."""
        from quant_monitor.main import run_signal_cycle
        # Should not raise — errors are caught internally
        run_signal_cycle()

    def test_fusion_with_real_data(self):
        """Fetch real data → run models → fuse → verify output."""
        from quant_monitor.agent.fusion import SignalFusion
        from quant_monitor.data.pipeline import DataPipeline
        from quant_monitor.models.macro import MacroModel
        from quant_monitor.models.technical import TechnicalModel

        pipeline = DataPipeline()
        prices = pipeline.fetch_prices(["SPY"], period="1y")
        macro = pipeline.fetch_macro()

        tech_model = TechnicalModel()
        macro_model = MacroModel()
        fusion = SignalFusion()

        # Handle the case where the dataframe has multi-index
        spy_prices = prices.loc["SPY"] if "SPY" in getattr(prices.index, "levels", [[]])[0] else prices

        tech_scores = tech_model.score_all({"SPY": spy_prices})
        macro_score = macro_model.score(macro)
        macro_regime = macro_model.classify_regime(macro)

        result = fusion.fuse(
            technical=tech_scores.get("SPY", 0.0),
            fundamental=0.0,  # Not available without fundamentals data
            sentiment=0.0,
            macro=macro_score,
            regime="LOW_VOL_TREND",
        )

        assert -1.0 <= result["fused_score"] <= 1.0
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["action"] in ("BUY", "SELL", "HOLD", "TRIM_UNDERWEIGHT", "TRIM_OVERWEIGHT")
        print(f"SPY fused: {result}")

    def test_alert_formatting(self):
        """Alert formatters produce valid output."""
        from quant_monitor.agent.alerts import AlertDispatcher

        dispatcher = AlertDispatcher()

        trades = [{"ticker": "TSM", "action": "BUY", "current_weight": 0.05, "target_weight": 0.08, "delta": 0.03}]
        msg = dispatcher.format_rebalance_alert(trades)
        assert "TSM" in msg and "BUY" in msg

        kill = {"ticker": "IONQ", "open_price": 30.0, "current_price": 24.0, "drawdown_pct": 0.20}
        msg = dispatcher.format_kill_switch_alert(kill)
        assert "IONQ" in msg and "20" in msg

    def test_risk_manager_integration(self):
        """Risk manager validates against real config limits."""
        from quant_monitor.agent.risk_manager import RiskManager

        rm = RiskManager()
        # Simulate current portfolio weights
        weights = {
            "SPY": 0.09, "TSM": 0.08, "MU": 0.04, "PLTR": 0.05,
            "AMZN": 0.05, "GOOGL": 0.04, "GE": 0.05, "JPM": 0.05,
            "LMT": 0.06, "WMT": 0.08, "XLP": 0.08, "PG": 0.04,
            "JNJ": 0.06, "XLU": 0.04, "IONQ": 0.03,
        }
        violations = rm.check_position_limits(weights, regime="RISK_ON")
        print(f"Violations: {violations}")
        # This should have no individual position breaches (all < 10%)
        pos_breaches = [v for v in violations if "POSITION_BREACH" in v]
        assert len(pos_breaches) == 0