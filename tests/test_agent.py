"""Tests for agent orchestrator — Phase 7 (risk manager, optimizer, scheduler)."""

from __future__ import annotations

import pandas as pd
import pytest

# ── Risk Manager Tests ──────────────────────────────────────────────────────

class TestRiskManager:
    """Tests for quant_monitor/agent/risk_manager.py"""

    def test_check_position_limits_no_violations(self):
        """No violations when all positions within RISK_ON limits."""
        from quant_monitor.agent.risk_manager import RiskManager

        rm = RiskManager()
        weights = {"SPY": 0.08, "TSM": 0.07, "PLTR": 0.05, "AMZN": 0.06}
        violations = rm.check_position_limits(weights, regime="RISK_ON")
        assert violations == [], f"Expected no violations, got {violations}"

    def test_check_position_limits_breach(self):
        """Position exceeding max_position for the regime should be flagged."""
        from quant_monitor.agent.risk_manager import RiskManager

        rm = RiskManager()
        # RISK_ON max_position = 0.10 (10%)
        weights = {"SPY": 0.12, "TSM": 0.07, "PLTR": 0.05}
        violations = rm.check_position_limits(weights, regime="RISK_ON")
        assert len(violations) > 0, "SPY at 12% should breach RISK_ON 10% limit"
        assert any("SPY" in v for v in violations)

    def test_check_position_limits_crisis_stricter(self):
        """CRISIS regime has tighter limits (5%). 6% position should breach."""
        from quant_monitor.agent.risk_manager import RiskManager

        rm = RiskManager()
        weights = {"SPY": 0.06, "TSM": 0.04}
        violations = rm.check_position_limits(weights, regime="CRISIS")
        assert any("SPY" in v for v in violations), "SPY 6% should breach CRISIS 5% limit"

    def test_check_sector_limits_breach(self):
        """Sector exceeding max_sector should be flagged."""
        from quant_monitor.agent.risk_manager import RiskManager

        rm = RiskManager()
        # Defensive: WMT + XLP + PG + JNJ + XLU — if combined > 25% in RISK_ON
        weights = {
            "WMT": 0.08, "XLP": 0.08, "PG": 0.06, "JNJ": 0.06, "XLU": 0.05,
            "SPY": 0.05, "TSM": 0.05,
        }
        violations = rm.check_position_limits(weights, regime="RISK_ON")
        # Sector "Defensive" total = 33% > 25%
        assert len(violations) > 0, "Defensive sector at 33% should breach 25% limit"

    def test_compute_portfolio_beta(self):
        """Weighted portfolio beta computation."""
        from quant_monitor.agent.risk_manager import RiskManager

        rm = RiskManager()
        weights = {"SPY": 0.50, "IONQ": 0.30, "WMT": 0.20}
        betas = {"SPY": 1.0, "IONQ": 2.0, "WMT": 0.5}
        beta = rm.compute_portfolio_beta(weights, betas)
        # Expected: 0.50*1.0 + 0.30*2.0 + 0.20*0.5 = 0.50 + 0.60 + 0.10 = 1.20
        assert abs(beta - 1.20) < 0.001

    def test_check_kill_switch_triggers(self):
        """Kill switch should fire when a position is down >15% intraday."""
        from quant_monitor.agent.risk_manager import RiskManager

        rm = RiskManager()
        positions = {
            "IONQ": {"qty": 800, "avg_cost": 33.60, "open_price": 30.00},
            "SPY": {"qty": 295, "avg_cost": 684.89, "open_price": 690.00},
        }
        current_prices = {
            "IONQ": 24.00,  # down 20% from open → triggers
            "SPY": 685.00,  # down <1% from open → safe
        }
        kills = rm.check_kill_switch(positions, current_prices)
        assert len(kills) >= 1
        assert any(k["ticker"] == "IONQ" for k in kills)

    def test_check_kill_switch_no_trigger(self):
        """Kill switch should NOT fire for normal drawdowns."""
        from quant_monitor.agent.risk_manager import RiskManager

        rm = RiskManager()
        positions = {
            "SPY": {"qty": 295, "avg_cost": 684.89, "open_price": 690.00},
        }
        current_prices = {"SPY": 680.00}  # down ~1.4%
        kills = rm.check_kill_switch(positions, current_prices)
        assert len(kills) == 0

    def test_validate_trades_blocks_limit_breach(self):
        """validate_trades should reject trades that would breach limits."""
        from quant_monitor.agent.risk_manager import RiskManager

        rm = RiskManager()
        proposed = [
            {"ticker": "IONQ", "action": "BUY", "current_weight": 0.08, "target_weight": 0.12, "delta": 0.04},
        ]
        current_positions = {
            "IONQ": {"weight": 0.08, "sector": "Quantum/Speculative"},
            "SPY": {"weight": 0.09, "sector": "Broad Market"},
        }
        valid = rm.validate_trades(proposed, current_positions, regime="RISK_ON")
        # IONQ target 12% > 10% max → should be rejected
        rejected = [t for t in valid if t.get("rejected_reason")]
        assert len(rejected) >= 1

    def test_validate_trades_passes_clean_trades(self):
        """validate_trades should pass trades within limits."""
        from quant_monitor.agent.risk_manager import RiskManager

        rm = RiskManager()
        proposed = [
            {"ticker": "SPY", "action": "BUY", "current_weight": 0.05, "target_weight": 0.08, "delta": 0.03},
        ]
        current_positions = {
            "SPY": {"weight": 0.05, "sector": "Broad Market"},
        }
        valid = rm.validate_trades(proposed, current_positions, regime="RISK_ON")
        passed = [t for t in valid if not t.get("rejected_reason")]
        assert len(passed) == 1


# ── Portfolio Optimizer Tests ───────────────────────────────────────────────

class TestPortfolioOptimizer:
    """Tests for quant_monitor/agent/optimizer.py"""

    def test_compute_target_weights_returns_dict(self):
        """compute_target_weights must return {ticker: float}."""
        from quant_monitor.agent.optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        prices = pd.Series({"SPY": 690.0, "TSM": 180.0, "PLTR": 100.0})
        views = {"SPY": 0.05, "TSM": 0.08, "PLTR": -0.02}
        confidences = {"SPY": 0.8, "TSM": 0.7, "PLTR": 0.6}
        weights = opt.compute_target_weights(prices, views, confidences)
        assert isinstance(weights, dict)
        for ticker, w in weights.items():
            assert 0.0 <= w <= 1.0, f"{ticker} weight {w} out of [0, 1]"
        # Weights should approximately sum to 1.0
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_compute_target_weights_bullish_views(self):
        """Bullish view should result in higher weight than bearish view."""
        from quant_monitor.agent.optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        prices = pd.Series({"SPY": 690.0, "TSM": 180.0})
        # Bullish on TSM, bearish on SPY
        views = {"SPY": -0.05, "TSM": 0.15}
        confidences = {"SPY": 0.8, "TSM": 0.9}
        weights = opt.compute_target_weights(prices, views, confidences)
        assert weights.get("TSM", 0) > weights.get("SPY", 0), "TSM weight should be higher"

    def test_compute_rebalance_trades_no_drift(self):
        """If weights within drift threshold, no trades should be generated."""
        from quant_monitor.agent.optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        current = {"SPY": 0.50, "TSM": 0.50}
        target = {"SPY": 0.51, "TSM": 0.49}  # 1% drift
        trades = opt.compute_rebalance_trades(current, target, drift_threshold=0.02)
        assert len(trades) == 0

    def test_compute_rebalance_trades_with_drift(self):
        """If drift > threshold, trade is generated."""
        from quant_monitor.agent.optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        current = {"SPY": 0.50, "TSM": 0.50}
        target = {"SPY": 0.55, "TSM": 0.45}  # 5% drift
        trades = opt.compute_rebalance_trades(current, target, drift_threshold=0.02)
        assert len(trades) == 2
        # Sort should put largest delta first
        assert abs(trades[0]["delta"]) >= abs(trades[1]["delta"])

    def test_rebalance_trade_actions_correct(self):
        """BUY/SELL actions correctly assigned based on delta."""
        from quant_monitor.agent.optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        current = {"SPY": 0.50, "TSM": 0.50}
        target = {"SPY": 0.60, "TSM": 0.40}
        trades = opt.compute_rebalance_trades(current, target, drift_threshold=0.02)

        spy_trade = next(t for t in trades if t["ticker"] == "SPY")
        tsm_trade = next(t for t in trades if t["ticker"] == "TSM")

        assert spy_trade["action"] == "BUY"
        assert spy_trade["delta"] > 0

        assert tsm_trade["action"] == "SELL"
        assert tsm_trade["delta"] < 0
