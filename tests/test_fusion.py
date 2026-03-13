"""Tests for signal fusion engine - Phase 6."""

from __future__ import annotations

import pytest

from quant_monitor.agent.fusion import SignalFusion


class TestSignalFusion:
    """Tests for quant_monitor/agent/fusion.py."""

    def test_fuse_returns_dict_with_required_keys(self):
        fusion = SignalFusion()

        result = fusion.fuse(0.7, 0.5, 0.4, 0.2, "LOW_VOL_TREND")

        assert set(result) == {"fused_score", "confidence", "action", "dominant_model"}

    @pytest.mark.parametrize(
        ("technical", "fundamental", "sentiment", "macro", "regime"),
        [
            (1.0, 1.0, 1.0, 1.0, "LOW_VOL_TREND"),
            (-1.0, -1.0, -1.0, -1.0, "CRISIS"),
            (0.9, -0.9, 0.3, -0.2, "HIGH_VOL_RANGE"),
        ],
    )
    def test_fuse_score_in_range(self, technical, fundamental, sentiment, macro, regime):
        fusion = SignalFusion()

        result = fusion.fuse(technical, fundamental, sentiment, macro, regime)

        assert -1.0 <= result["fused_score"] <= 1.0

    def test_crisis_regime_macro_dominates(self):
        fusion = SignalFusion()

        result = fusion.fuse(0.1, 0.1, 0.1, -0.9, "CRISIS")

        assert result["dominant_model"] == "macro"
        assert result["fused_score"] < 0

    def test_low_confidence_forces_hold(self):
        fusion = SignalFusion()

        result = fusion.fuse(1.0, -1.0, 1.0, -1.0, "LOW_VOL_TREND")

        assert result["confidence"] < 0.65
        assert result["action"] == "HOLD"

    def test_fuse_buy_action_when_score_and_confidence_clear_thresholds(self):
        fusion = SignalFusion()

        result = fusion.fuse(0.9, 0.8, 0.85, 0.7, "LOW_VOL_TREND")

        assert result["confidence"] >= 0.65
        assert result["action"] in {"BUY", "TRIM_UNDERWEIGHT"}

    def test_fuse_all_returns_dict_of_dicts(self):
        fusion = SignalFusion()

        results = fusion.fuse_all(
            technical_scores={"SPY": 0.6, "TSM": 0.7},
            fundamental_scores={"SPY": 0.4, "TSM": 0.5},
            sentiment_scores={"SPY": 0.3, "TSM": 0.1},
            macro_score=0.2,
            regime="LOW_VOL_TREND",
        )

        assert set(results) == {"SPY", "TSM"}
        assert all(isinstance(value, dict) for value in results.values())

    def test_fuse_all_handles_missing_tickers(self):
        fusion = SignalFusion()

        results = fusion.fuse_all(
            technical_scores={"SPY": 0.6},
            fundamental_scores={"TSM": 0.5},
            sentiment_scores={"SPY": 0.3, "IONQ": -0.2},
            macro_score=-0.1,
            regime="HIGH_VOL_RANGE",
        )

        assert set(results) == {"SPY", "TSM", "IONQ"}
        assert results["TSM"]["dominant_model"] in {
            "technical",
            "fundamental",
            "sentiment",
            "macro",
        }