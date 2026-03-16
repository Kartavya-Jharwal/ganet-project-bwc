"""Tests for MacroModel."""

from __future__ import annotations

from quant_monitor.models.macro import MacroModel

RISK_ON_SNAPSHOT = {
    "vix": 14.0,
    "yield_10y_2y_spread": 1.2,
    "dxy_weekly_change_pct": 0.3,
    "ten_year_yield_weekly_bps": 5.0,
}

RISK_OFF_SNAPSHOT = {
    "vix": 35.0,
    "yield_10y_2y_spread": -0.5,
    "dxy_weekly_change_pct": 3.5,
    "ten_year_yield_weekly_bps": 45.0,
}

NEUTRAL_SNAPSHOT = {
    "vix": 20.0,
    "yield_10y_2y_spread": 0.3,
    "dxy_weekly_change_pct": 1.0,
    "ten_year_yield_weekly_bps": 10.0,
}


class TestMacroModel:
    def setup_method(self):
        self.model = MacroModel()

    # ── score() tests ────────────────────────────────────────────────────────

    def test_score_risk_on_positive(self):
        result = self.model.score(RISK_ON_SNAPSHOT)
        assert isinstance(result, float)
        assert result > 0, f"Expected positive score for risk-on snapshot, got {result}"

    def test_score_risk_off_negative(self):
        result = self.model.score(RISK_OFF_SNAPSHOT)
        assert isinstance(result, float)
        assert result < 0, f"Expected negative score for risk-off snapshot, got {result}"

    def test_score_range(self):
        for snapshot in [RISK_ON_SNAPSHOT, RISK_OFF_SNAPSHOT, NEUTRAL_SNAPSHOT]:
            result = self.model.score(snapshot)
            assert -1.0 <= result <= 1.0, f"Score {result} out of [-1, 1]"

    def test_score_empty_snapshot_uses_defaults(self):
        """Empty dict should not raise — model uses get() with safe defaults."""
        result = self.model.score({})
        assert isinstance(result, float)
        assert -1.0 <= result <= 1.0

    # ── classify_regime() tests ──────────────────────────────────────────────

    def test_classify_regime_risk_on(self):
        regime = self.model.classify_regime(RISK_ON_SNAPSHOT)
        assert regime == "RISK_ON", f"Expected RISK_ON, got {regime}"

    def test_classify_regime_crisis(self):
        regime = self.model.classify_regime(RISK_OFF_SNAPSHOT)
        assert regime == "CRISIS", f"Expected CRISIS, got {regime}"

    def test_classify_regime_transition(self):
        snapshot = {
            "vix": 27.0,  # above 25 threshold → 1 crisis signal
            "yield_10y_2y_spread": 0.5,
            "dxy_weekly_change_pct": 0.5,
            "ten_year_yield_weekly_bps": 10.0,
        }
        regime = self.model.classify_regime(snapshot)
        assert regime in {"TRANSITION", "CRISIS"}

    def test_classify_regime_returns_string(self):
        for snapshot in [RISK_ON_SNAPSHOT, RISK_OFF_SNAPSHOT, NEUTRAL_SNAPSHOT]:
            result = self.model.classify_regime(snapshot)
            assert isinstance(result, str)
            assert result in {"RISK_ON", "TRANSITION", "CRISIS"}

    # ── per_ticker_impact() tests ────────────────────────────────────────────

    def test_per_ticker_impact_tsm_dxy_spike(self):
        """TSM should get a negative impact when DXY spikes."""
        snapshot = {
            "vix": 20.0,
            "dxy_weekly_change_pct": 3.0,  # above 2.0 threshold
            "ten_year_yield_weekly_bps": 5.0,
        }
        impact = self.model.per_ticker_impact(snapshot, "TSM", "Semiconductor")
        assert impact < 0, f"Expected negative DXY impact for TSM, got {impact}"

    def test_per_ticker_impact_rate_sensitive_rising_rates(self):
        """Rate-sensitive growth tickers should get negative impact from rising yields."""
        snapshot = {
            "vix": 18.0,
            "dxy_weekly_change_pct": 0.5,
            "ten_year_yield_weekly_bps": 30.0,  # big positive rate move
        }
        impact = self.model.per_ticker_impact(snapshot, "PLTR", "AI Software")
        assert impact < 0, f"Expected negative rate impact for PLTR, got {impact}"

    def test_per_ticker_impact_range(self):
        for ticker, sector in [("TSM", "Semiconductor"), ("JPM", "Financials"), ("AAPL", "Tech")]:
            for snapshot in [RISK_ON_SNAPSHOT, RISK_OFF_SNAPSHOT]:
                result = self.model.per_ticker_impact(snapshot, ticker, sector)
                assert -1.0 <= result <= 1.0
