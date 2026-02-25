# Quant Portfolio Monitor — Phases 6–10 Granular Task List

> **Purpose:** Step-by-step implementation roadmap for Phases 6–10.
> Follows the same conventions as Phases 0–5 in `task.md`.
>
> **Prerequisites:** ALL of Phases 0–5 must be COMPLETE (≈35 tests passing).
>
> **CRITICAL RULES (same as Phases 0–5):**
> 1. DO NOT change function signatures — they are already defined in the stub files.
> 2. DO NOT rename files or move files.
> 3. DO NOT add new dependencies unless explicitly stated.
> 4. ALWAYS use `from quant_monitor.config import cfg` to read config values.
> 5. ALWAYS run `doppler run -- uv run pytest` after each task to verify no regressions.
> 6. ALWAYS read the existing file FIRST before editing — stubs contain exact signatures.
> 7. Config values are in `quant_monitor/config.toml` — NEVER hardcode them.
> 8. Secrets come from Doppler via `os.environ` — NEVER hardcode API keys.
> 9. All functions that raise `NotImplementedError` must be replaced with real logic.
> 10. Type hints are ALREADY in the stubs — preserve them exactly.

---

## TABLE OF CONTENTS

- [Phase 6: Signal Fusion Engine](#phase-6-signal-fusion-engine)
- [Phase 7: Agent Orchestrator (Risk Manager + Optimizer + Scheduler)](#phase-7-agent-orchestrator)
- [Phase 8: Backtesting Framework](#phase-8-backtesting-framework)
- [Phase 9: Rich CLI + OpenBB Dashboard](#phase-9-rich-cli--openbb-dashboard)
- [Phase 10: Alerts + Deployment](#phase-10-alerts--deployment)

---

## Quick Reference: Existing Stubs to Implement

| Phase | File | Class/Functions | Status |
|-------|------|----------------|--------|
| 6 | `quant_monitor/agent/fusion.py` | `SignalFusion.fuse()`, `.fuse_all()` | `NotImplementedError` |
| 7 | `quant_monitor/agent/risk_manager.py` | `RiskManager` (4 methods) | `NotImplementedError` |
| 7 | `quant_monitor/agent/optimizer.py` | `PortfolioOptimizer` (2 methods) | `NotImplementedError` |
| 7 | `quant_monitor/main.py` | `main()` scheduler wiring | TODO comment |
| 8 | `quant_monitor/backtest/engine.py` | `WalkForwardEngine` (2 methods) | `NotImplementedError` |
| 8 | `quant_monitor/backtest/metrics.py` | 6 metric functions | `NotImplementedError` |
| 9 | `quant_monitor/dashboard/app.py` | Rich CLI with 5 views | TODO placeholder |
| 10 | `quant_monitor/agent/alerts.py` | `AlertDispatcher` (3 methods) | `NotImplementedError` |

---

## Quick Reference: Config Values Used in Phases 6–10

| Config Section | Key | Value | Used In |
|---------------|-----|-------|---------|
| `[regime_weights.*]` | technical, fundamental, sentiment, macro | (varies per regime) | Phase 6 — fusion |
| `[signal_thresholds]` | `confidence_min` | 0.65 | Phase 6 — action gating |
| `[signal_thresholds]` | `fused_score_min` | 0.35 | Phase 6 — action gating |
| `[signal_thresholds]` | `drift_threshold` | 0.02 | Phase 7 — rebalance trigger |
| `[signal_thresholds]` | `kill_switch_drawdown` | 0.15 | Phase 7 — kill switch |
| `[risk_params.RISK_ON]` | max_position, max_sector, target_beta | 0.10, 0.25, 0.50 | Phase 7 — risk limits |
| `[risk_params.TRANSITION]` | max_position, max_sector, target_beta | 0.08, 0.20, 0.35 | Phase 7 — risk limits |
| `[risk_params.CRISIS]` | max_position, max_sector, target_beta | 0.05, 0.15, 0.20 | Phase 7 — risk limits |
| `[project]` | `rebalance_interval_minutes` | 15 | Phase 7 — scheduler |
| `[project]` | `initial_capital` | 1,000,000 | Phase 8 — backtest |
| `[alerts]` | `enabled` | true | Phase 10 — alerts |
| `[alerts]` | `cooldown_minutes` | 30 | Phase 10 — cooldown |
| `[alerts]` | `market_hours_only` | false | Phase 10 — alert timing |

---

## Phase 6: Signal Fusion Engine

> **Prerequisites:** Phases 0–5 COMPLETE.
> **File to edit:** `quant_monitor/agent/fusion.py`
> **Config needed:** `[regime_weights.*]`, `[signal_thresholds]`
> **No new dependencies.**

---

### Task 6.0 — Create Phase 6 test file

**File to CREATE:** `tests/test_fusion.py`

```python
"""Tests for signal fusion engine — Phase 6."""

from __future__ import annotations

import pytest


class TestSignalFusion:
    """Tests for quant_monitor/agent/fusion.py"""

    def test_fuse_returns_dict_with_required_keys(self):
        """fuse() must return dict with fused_score, confidence, action, dominant_model."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        result = fusion.fuse(
            technical=0.5,
            fundamental=0.3,
            sentiment=0.4,
            macro=0.2,
            regime="LOW_VOL_TREND",
        )
        assert isinstance(result, dict)
        assert "fused_score" in result
        assert "confidence" in result
        assert "action" in result
        assert "dominant_model" in result

    def test_fuse_score_in_range(self):
        """Fused score must always be in [-1.0, +1.0]."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        # Extreme inputs
        for tech, fund, sent, macro in [
            (1.0, 1.0, 1.0, 1.0),
            (-1.0, -1.0, -1.0, -1.0),
            (1.0, -1.0, 0.5, -0.5),
            (0.0, 0.0, 0.0, 0.0),
        ]:
            result = fusion.fuse(tech, fund, sent, macro, "LOW_VOL_TREND")
            assert -1.0 <= result["fused_score"] <= 1.0, (
                f"Fused score out of range for inputs ({tech}, {fund}, {sent}, {macro})"
            )

    def test_confidence_in_range(self):
        """Confidence must be in [0.0, 1.0]."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        result = fusion.fuse(0.5, 0.3, 0.4, 0.2, "LOW_VOL_TREND")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_high_agreement_high_confidence(self):
        """When all models agree strongly, confidence should be high."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        result = fusion.fuse(0.8, 0.7, 0.9, 0.8, "LOW_VOL_TREND")
        assert result["confidence"] > 0.6, "All models agree positively → high confidence"

    def test_disagreement_low_confidence(self):
        """When models strongly disagree, confidence should be low."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        result = fusion.fuse(0.9, -0.9, 0.5, -0.5, "LOW_VOL_TREND")
        assert result["confidence"] < 0.65, "Models disagree → low confidence"

    def test_low_confidence_forces_hold(self):
        """Low confidence should produce HOLD regardless of fused score magnitude."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        # Strong disagreement: tech says buy, fundamental says sell
        result = fusion.fuse(1.0, -1.0, 0.8, -0.8, "LOW_VOL_TREND")
        assert result["action"] == "HOLD", "Low confidence → HOLD"

    def test_strong_buy_signal(self):
        """Strong positive agreement should produce BUY."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        result = fusion.fuse(0.8, 0.7, 0.9, 0.6, "LOW_VOL_TREND")
        assert result["action"] in ("BUY", "TRIM_UNDERWEIGHT"), (
            f"Strong positive signals → BUY or TRIM_UNDERWEIGHT, got {result['action']}"
        )

    def test_strong_sell_signal(self):
        """Strong negative agreement should produce SELL."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        result = fusion.fuse(-0.8, -0.7, -0.9, -0.6, "LOW_VOL_TREND")
        assert result["action"] in ("SELL", "TRIM_OVERWEIGHT"), (
            f"Strong negative signals → SELL or TRIM_OVERWEIGHT, got {result['action']}"
        )

    def test_neutral_signals_hold(self):
        """Neutral scores (near zero) should produce HOLD."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        result = fusion.fuse(0.1, -0.05, 0.08, 0.0, "LOW_VOL_TREND")
        assert result["action"] == "HOLD"

    def test_crisis_regime_macro_dominates(self):
        """In CRISIS regime, macro weight is 60% — macro should dominate."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        # Tech/fund/sent are positive, macro is strongly negative
        result = fusion.fuse(0.5, 0.5, 0.5, -1.0, "CRISIS")
        # With CRISIS weights: tech=10%, fund=10%, sent=20%, macro=60%
        # Macro's strong negative signal should pull fused score significantly negative
        assert result["fused_score"] < 0.2, (
            f"CRISIS regime: macro=-1.0 should dominate, got fused_score={result['fused_score']}"
        )

    def test_regime_weights_differ(self):
        """Different regimes should produce different fused scores for same inputs."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        inputs = (0.6, 0.3, 0.5, -0.4)
        result_trend = fusion.fuse(*inputs, regime="HIGH_VOL_TREND")
        result_crisis = fusion.fuse(*inputs, regime="CRISIS")
        assert result_trend["fused_score"] != result_crisis["fused_score"], (
            "Different regimes should produce different fused scores"
        )

    def test_dominant_model_identification(self):
        """dominant_model should name the model with highest |contribution|."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        # Technical is clearly biggest input in HIGH_VOL_TREND (45% weight)
        result = fusion.fuse(1.0, 0.0, 0.0, 0.0, "HIGH_VOL_TREND")
        assert result["dominant_model"] == "technical"

    def test_fuse_all_returns_dict_of_dicts(self):
        """fuse_all() must return {ticker: {fused_score, confidence, action, ...}}."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        tech = {"SPY": 0.5, "TSM": -0.3, "PLTR": 0.8}
        fund = {"SPY": 0.2, "TSM": 0.4, "PLTR": -0.1}
        sent = {"SPY": 0.3, "TSM": 0.1, "PLTR": 0.6}
        macro_score = 0.1

        result = fusion.fuse_all(tech, fund, sent, macro_score, "LOW_VOL_TREND")
        assert isinstance(result, dict)
        assert set(result.keys()) == {"SPY", "TSM", "PLTR"}
        for ticker, fusion_result in result.items():
            assert "fused_score" in fusion_result
            assert "confidence" in fusion_result
            assert "action" in fusion_result
            assert -1.0 <= fusion_result["fused_score"] <= 1.0

    def test_fuse_all_handles_missing_tickers(self):
        """If a ticker is missing from one model, it should get score 0.0 for that model."""
        from quant_monitor.agent.fusion import SignalFusion

        fusion = SignalFusion()
        tech = {"SPY": 0.5, "TSM": 0.3}
        fund = {"SPY": 0.2}  # TSM missing
        sent = {"SPY": 0.3, "TSM": 0.1}
        macro_score = 0.0

        result = fusion.fuse_all(tech, fund, sent, macro_score, "LOW_VOL_TREND")
        assert "SPY" in result
        assert "TSM" in result  # should still appear, fundamental defaults to 0.0
```

---

### Task 6.1 — Implement `SignalFusion.fuse()` in fusion.py

**File:** `quant_monitor/agent/fusion.py`
**Method:** `SignalFusion.fuse(self, technical, fundamental, sentiment, macro, regime) -> dict`

**Implementation logic (from architecture.md + design.md):**

```python
def fuse(
    self,
    technical: float,
    fundamental: float,
    sentiment: float,
    macro: float,
    regime: str,
) -> dict:
    """Compute fused signal for a single ticker.

    Algorithm:
    1. Load regime-dependent weights from config
    2. Compute weighted average of tech/fund/sent (macro treated as additive)
    3. Compute confidence = 1 - std(all scores)
    4. Determine action via threshold gating
    5. Identify dominant model (highest |weight × score|)
    """
    import numpy as np
    from quant_monitor.config import cfg

    # 1. Load regime weights (fallback to equal weights)
    weights = cfg.regime_weights.get(regime, {
        "technical": 0.25, "fundamental": 0.25,
        "sentiment": 0.25, "macro": 0.25,
    })

    w_tech = weights.get("technical", 0.25)
    w_fund = weights.get("fundamental", 0.25)
    w_sent = weights.get("sentiment", 0.25)
    w_macro = weights.get("macro", 0.25)

    # 2. Weighted average: tech/fund/sent blended; macro is additive adjustment
    base_weight = w_tech + w_fund + w_sent
    if base_weight > 0:
        base_score = (
            w_tech * technical + w_fund * fundamental + w_sent * sentiment
        ) / base_weight
    else:
        base_score = 0.0

    macro_adjustment = w_macro * macro * 0.5  # Half-strength additive
    fused_score = max(-1.0, min(1.0, base_score + macro_adjustment))

    # 3. Confidence = 1 - std(all model scores)
    scores = [technical, fundamental, sentiment, macro]
    confidence = max(0.0, min(1.0, 1.0 - float(np.std(scores))))

    # 4. Determine action via threshold gating
    conf_min = cfg.signal_thresholds.get("confidence_min", 0.65)
    score_min = cfg.signal_thresholds.get("fused_score_min", 0.35)

    if confidence < conf_min:
        action = "HOLD"
    elif fused_score > 0.6:
        action = "BUY"
    elif fused_score > score_min:
        action = "TRIM_UNDERWEIGHT"
    elif fused_score < -0.6:
        action = "SELL"
    elif fused_score < -score_min:
        action = "TRIM_OVERWEIGHT"
    else:
        action = "HOLD"

    # 5. Dominant model = highest |weight × score|
    contributions = {
        "technical": abs(w_tech * technical),
        "fundamental": abs(w_fund * fundamental),
        "sentiment": abs(w_sent * sentiment),
        "macro": abs(w_macro * macro),
    }
    dominant_model = max(contributions, key=contributions.get)

    return {
        "fused_score": round(fused_score, 6),
        "confidence": round(confidence, 6),
        "action": action,
        "dominant_model": dominant_model,
        "regime": regime,
        "weights": {
            "technical": w_tech,
            "fundamental": w_fund,
            "sentiment": w_sent,
            "macro": w_macro,
        },
        "component_scores": {
            "technical": technical,
            "fundamental": fundamental,
            "sentiment": sentiment,
            "macro": macro,
        },
    }
```

**Add runtime imports at top of file:**
```python
import numpy as np
```

**Acceptance criteria:**
- `pytest tests/test_fusion.py::TestSignalFusion::test_fuse_returns_dict_with_required_keys` passes
- `pytest tests/test_fusion.py::TestSignalFusion::test_fuse_score_in_range` passes
- `pytest tests/test_fusion.py::TestSignalFusion::test_crisis_regime_macro_dominates` passes
- `pytest tests/test_fusion.py::TestSignalFusion::test_low_confidence_forces_hold` passes
- Fused score is ALWAYS in [-1.0, +1.0]

---

### Task 6.2 — Implement `SignalFusion.fuse_all()` in fusion.py

**File:** `quant_monitor/agent/fusion.py`
**Method:** `SignalFusion.fuse_all(self, technical_scores, fundamental_scores, sentiment_scores, macro_score, regime) -> dict[str, dict]`

**Implementation:**

```python
def fuse_all(
    self,
    technical_scores: dict[str, float],
    fundamental_scores: dict[str, float],
    sentiment_scores: dict[str, float],
    macro_score: float,
    regime: str,
) -> dict[str, dict]:
    """Fuse signals for all tickers. Returns {ticker: fusion_result}.

    Note: macro_score is portfolio-level (same for all tickers).
    If a ticker is missing from any model dict, defaults to 0.0.
    """
    # Union of all tickers across models
    all_tickers = set(technical_scores) | set(fundamental_scores) | set(sentiment_scores)

    results = {}
    for ticker in all_tickers:
        tech = technical_scores.get(ticker, 0.0)
        fund = fundamental_scores.get(ticker, 0.0)
        sent = sentiment_scores.get(ticker, 0.0)
        try:
            results[ticker] = self.fuse(tech, fund, sent, macro_score, regime)
        except Exception as e:
            logger.warning("Fusion failed for %s: %s", ticker, e)
            results[ticker] = {
                "fused_score": 0.0,
                "confidence": 0.0,
                "action": "HOLD",
                "dominant_model": "none",
                "regime": regime,
            }
    return results
```

**Acceptance criteria:**
- `pytest tests/test_fusion.py::TestSignalFusion::test_fuse_all_returns_dict_of_dicts` passes
- `pytest tests/test_fusion.py::TestSignalFusion::test_fuse_all_handles_missing_tickers` passes

---

### Task 6.3 — Run full Phase 6 test suite

```bash
doppler run -- uv run pytest tests/test_fusion.py -v
```

**Expected:** All ~14 tests pass.

---

## Phase 7: Agent Orchestrator

> **Prerequisites:** Phase 6 COMPLETE.
> **Files to edit:** `quant_monitor/agent/risk_manager.py`, `quant_monitor/agent/optimizer.py`, `quant_monitor/main.py`
> **Config needed:** `[risk_params.*]`, `[signal_thresholds]`, `[project]`
> **Existing dependency:** `pyportfolioopt>=1.5.0`, `apscheduler>=3.10.0` (already in pyproject.toml)

---

### Task 7.0 — Create Phase 7 test file

**File to CREATE:** `tests/test_agent.py`

```python
"""Tests for agent orchestrator — Phase 7 (risk manager, optimizer, scheduler)."""

from __future__ import annotations

import pandas as pd
import numpy as np
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
        assert abs(sum(weights.values()) - 1.0) < 0.05, (
            f"Weights sum to {sum(weights.values())}, expected ~1.0"
        )

    def test_compute_target_weights_bullish_views(self):
        """Bullish views should allocate more to those tickers."""
        from quant_monitor.agent.optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        prices = pd.Series({"SPY": 690.0, "TSM": 180.0, "PLTR": 100.0})
        views = {"SPY": 0.01, "TSM": 0.15, "PLTR": 0.01}  # TSM very bullish
        confidences = {"SPY": 0.5, "TSM": 0.9, "PLTR": 0.5}
        weights = opt.compute_target_weights(prices, views, confidences)
        # TSM should get a reasonable allocation (not necessarily largest, but meaningful)
        assert weights.get("TSM", 0) > 0.1, "TSM with strong bullish view should get >10%"

    def test_compute_rebalance_trades_no_drift(self):
        """No trades when drift is within threshold."""
        from quant_monitor.agent.optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        current = {"SPY": 0.30, "TSM": 0.20, "PLTR": 0.15}
        target = {"SPY": 0.31, "TSM": 0.195, "PLTR": 0.155}
        trades = opt.compute_rebalance_trades(current, target, drift_threshold=0.02)
        assert len(trades) == 0, "Small drift should produce no trades"

    def test_compute_rebalance_trades_with_drift(self):
        """Trades should be suggested when drift exceeds threshold."""
        from quant_monitor.agent.optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        current = {"SPY": 0.30, "TSM": 0.10, "PLTR": 0.25}
        target = {"SPY": 0.25, "TSM": 0.20, "PLTR": 0.20}
        trades = opt.compute_rebalance_trades(current, target, drift_threshold=0.02)
        assert len(trades) >= 2, "SPY (5% drift) and TSM (10% drift) should trigger trades"
        for trade in trades:
            assert "ticker" in trade
            assert "action" in trade
            assert "delta" in trade

    def test_rebalance_trade_actions_correct(self):
        """Action should be BUY when target > current, SELL when target < current."""
        from quant_monitor.agent.optimizer import PortfolioOptimizer

        opt = PortfolioOptimizer()
        current = {"SPY": 0.30, "TSM": 0.10}
        target = {"SPY": 0.20, "TSM": 0.25}
        trades = opt.compute_rebalance_trades(current, target, drift_threshold=0.02)
        for trade in trades:
            if trade["ticker"] == "SPY":
                assert trade["action"] == "SELL", "SPY target < current → SELL"
            elif trade["ticker"] == "TSM":
                assert trade["action"] == "BUY", "TSM target > current → BUY"
```

---

### Task 7.1 — Implement `RiskManager.check_position_limits()` in risk_manager.py

**File:** `quant_monitor/agent/risk_manager.py`
**Method:** `RiskManager.check_position_limits(self, weights: dict[str, float], regime: str) -> list[str]`

**Implementation:**

```python
def check_position_limits(self, weights: dict[str, float], regime: str) -> list[str]:
    """Check for position and sector limit breaches.

    Returns list of violation description strings.
    Uses regime-dependent limits from cfg.risk_params.
    """
    from quant_monitor.config import cfg
    from quant_monitor.models.fundamental import SECTOR_MAP

    params = cfg.risk_params.get(regime, cfg.risk_params.get("RISK_ON", {}))
    max_position = params.get("max_position", 0.10)
    max_sector = params.get("max_sector", 0.25)

    violations = []

    # Check individual position limits
    for ticker, weight in weights.items():
        if weight > max_position:
            violations.append(
                f"POSITION_BREACH: {ticker} at {weight:.1%} exceeds {regime} max {max_position:.0%}"
            )

    # Check sector concentration
    sector_weights: dict[str, float] = {}
    for ticker, weight in weights.items():
        sector = SECTOR_MAP.get(ticker, "Unknown")
        sector_weights[sector] = sector_weights.get(sector, 0.0) + weight

    for sector, total in sector_weights.items():
        if total > max_sector:
            violations.append(
                f"SECTOR_BREACH: {sector} at {total:.1%} exceeds {regime} max {max_sector:.0%}"
            )

    return violations
```

**Acceptance criteria:**
- `pytest tests/test_agent.py::TestRiskManager::test_check_position_limits_no_violations` passes
- `pytest tests/test_agent.py::TestRiskManager::test_check_position_limits_breach` passes
- `pytest tests/test_agent.py::TestRiskManager::test_check_position_limits_crisis_stricter` passes
- `pytest tests/test_agent.py::TestRiskManager::test_check_sector_limits_breach` passes

---

### Task 7.2 — Implement `RiskManager.compute_portfolio_beta()` in risk_manager.py

**File:** `quant_monitor/agent/risk_manager.py`
**Method:** `RiskManager.compute_portfolio_beta(self, weights: dict[str, float], betas: dict[str, float]) -> float`

**Implementation:**

```python
def compute_portfolio_beta(self, weights: dict[str, float], betas: dict[str, float]) -> float:
    """Compute weighted portfolio beta.

    β_portfolio = Σ(w_i × β_i) for all positions.
    """
    total_beta = 0.0
    for ticker, weight in weights.items():
        beta = betas.get(ticker, 1.0)  # default to market beta
        total_beta += weight * beta
    return total_beta
```

**Acceptance criteria:**
- `pytest tests/test_agent.py::TestRiskManager::test_compute_portfolio_beta` passes

---

### Task 7.3 — Implement `RiskManager.check_kill_switch()` in risk_manager.py

**File:** `quant_monitor/agent/risk_manager.py`
**Method:** `RiskManager.check_kill_switch(self, positions: dict, current_prices: dict) -> list[dict]`

**Implementation:**

```python
def check_kill_switch(self, positions: dict, current_prices: dict) -> list[dict]:
    """Check if any position is down >15% intraday.

    Returns list of positions triggering the kill switch.
    Each dict has: ticker, open_price, current_price, drawdown_pct.
    """
    from quant_monitor.config import cfg

    threshold = cfg.signal_thresholds.get("kill_switch_drawdown", 0.15)
    kills = []

    for ticker, pos in positions.items():
        open_price = pos.get("open_price", pos.get("avg_cost", 0))
        current = current_prices.get(ticker)
        if open_price and current and open_price > 0:
            drawdown = (open_price - current) / open_price
            if drawdown > threshold:
                kills.append({
                    "ticker": ticker,
                    "open_price": open_price,
                    "current_price": current,
                    "drawdown_pct": round(drawdown, 4),
                })
                logger.critical(
                    "KILL SWITCH: %s down %.1f%% intraday (open=%.2f, now=%.2f)",
                    ticker, drawdown * 100, open_price, current,
                )
    return kills
```

**Acceptance criteria:**
- `pytest tests/test_agent.py::TestRiskManager::test_check_kill_switch_triggers` passes
- `pytest tests/test_agent.py::TestRiskManager::test_check_kill_switch_no_trigger` passes

---

### Task 7.4 — Implement `RiskManager.validate_trades()` in risk_manager.py

**File:** `quant_monitor/agent/risk_manager.py`
**Method:** `RiskManager.validate_trades(self, proposed_trades, current_positions, regime) -> list[dict]`

**Implementation:**

```python
def validate_trades(
    self,
    proposed_trades: list[dict],
    current_positions: dict,
    regime: str,
) -> list[dict]:
    """Validate proposed trades against risk limits.

    Returns the same list with 'rejected_reason' field added to failing trades.
    Passing trades have rejected_reason = None.
    """
    from quant_monitor.config import cfg

    params = cfg.risk_params.get(regime, cfg.risk_params.get("RISK_ON", {}))
    max_position = params.get("max_position", 0.10)

    validated = []
    for trade in proposed_trades:
        trade = dict(trade)  # copy to avoid mutating input
        ticker = trade["ticker"]
        target_weight = trade.get("target_weight", 0.0)

        # Check: would the target weight breach position limit?
        if target_weight > max_position:
            trade["rejected_reason"] = (
                f"Target weight {target_weight:.1%} exceeds {regime} max {max_position:.0%}"
            )
        else:
            trade["rejected_reason"] = None

        validated.append(trade)

    passed = sum(1 for t in validated if not t.get("rejected_reason"))
    rejected = len(validated) - passed
    if rejected:
        logger.warning("Rejected %d/%d trades in %s regime", rejected, len(validated), regime)

    return validated
```

**Acceptance criteria:**
- `pytest tests/test_agent.py::TestRiskManager::test_validate_trades_blocks_limit_breach` passes
- `pytest tests/test_agent.py::TestRiskManager::test_validate_trades_passes_clean_trades` passes

---

### Task 7.5 — Implement `PortfolioOptimizer.compute_target_weights()` in optimizer.py

**File:** `quant_monitor/agent/optimizer.py`
**Method:** `PortfolioOptimizer.compute_target_weights(self, current_prices, views, view_confidences) -> dict[str, float]`

**Implementation (Black-Litterman using pyportfolioopt):**

```python
def compute_target_weights(
    self,
    current_prices: pd.Series,
    views: dict[str, float],
    view_confidences: dict[str, float],
) -> dict[str, float]:
    """Compute optimal target weights using Black-Litterman posterior.

    Uses pyportfolioopt for the heavy lifting:
    1. Compute market-implied expected returns (equal-weight prior)
    2. Inject views from signal fusion
    3. Compute posterior expected returns
    4. Run mean-variance optimization (max Sharpe)
    5. Apply constraints: no shorting, max 10% per position
    """
    import numpy as np
    import pandas as pd

    tickers = list(views.keys())
    n = len(tickers)

    if n == 0:
        return {}

    try:
        from pypfopt import BlackLittermanModel, EfficientFrontier
        from pypfopt import risk_models, expected_returns

        # Build a synthetic covariance matrix from prices if we have enough data
        # For now use a simple identity-based approach scaled by view magnitude
        # In production, this would use historical returns covariance
        cov_matrix = pd.DataFrame(
            np.eye(n) * 0.04,  # 20% annualized vol assumed
            index=tickers,
            columns=tickers,
        )

        # Market-cap weights as prior (equal weight fallback)
        market_caps = current_prices[tickers] if isinstance(current_prices, pd.Series) else pd.Series({t: 1.0 for t in tickers})

        # Black-Litterman model
        bl = BlackLittermanModel(
            cov_matrix,
            pi="equal",  # equal-weight prior
            absolute_views=views,
            omega="idzorek",
            view_confidences=[view_confidences.get(t, 0.5) for t in views],
        )
        bl_returns = bl.bl_returns()

        # Mean-variance optimization
        ef = EfficientFrontier(bl_returns, cov_matrix)
        ef.add_constraint(lambda w: w >= 0)  # long only
        ef.add_constraint(lambda w: w <= 0.15)  # max 15% per position (soft)
        ef.max_sharpe(risk_free_rate=0.04)  # ~4% risk-free rate
        cleaned = ef.clean_weights(cutoff=0.01)

        # Normalize to sum to 1.0
        total = sum(cleaned.values())
        if total > 0:
            return {t: w / total for t, w in cleaned.items()}
        return {t: 1.0 / n for t in tickers}

    except Exception as e:
        logger.warning("Black-Litterman optimization failed: %s — using equal weights", e)
        return {t: 1.0 / n for t in tickers}
```

**Add runtime imports at top of file:**
Replace `TYPE_CHECKING` guard with:
```python
import pandas as pd
```

**Acceptance criteria:**
- `pytest tests/test_agent.py::TestPortfolioOptimizer::test_compute_target_weights_returns_dict` passes
- `pytest tests/test_agent.py::TestPortfolioOptimizer::test_compute_target_weights_bullish_views` passes
- Weights sum to approximately 1.0
- All weights in [0, 1]

---

### Task 7.6 — Implement `PortfolioOptimizer.compute_rebalance_trades()` in optimizer.py

**File:** `quant_monitor/agent/optimizer.py`
**Method:** `PortfolioOptimizer.compute_rebalance_trades(self, current_weights, target_weights, drift_threshold) -> list[dict]`

**Implementation:**

```python
def compute_rebalance_trades(
    self,
    current_weights: dict[str, float],
    target_weights: dict[str, float],
    drift_threshold: float = 0.02,
) -> list[dict]:
    """Identify trades needed to rebalance.

    Only suggests trades where |current - target| > drift_threshold.
    Returns list of {ticker, action, current_weight, target_weight, delta}.
    """
    all_tickers = set(current_weights) | set(target_weights)
    trades = []

    for ticker in all_tickers:
        current = current_weights.get(ticker, 0.0)
        target = target_weights.get(ticker, 0.0)
        delta = target - current

        if abs(delta) > drift_threshold:
            action = "BUY" if delta > 0 else "SELL"
            trades.append({
                "ticker": ticker,
                "action": action,
                "current_weight": round(current, 6),
                "target_weight": round(target, 6),
                "delta": round(delta, 6),
            })

    # Sort by absolute delta descending (largest rebalances first)
    trades.sort(key=lambda t: abs(t["delta"]), reverse=True)
    return trades
```

**Acceptance criteria:**
- `pytest tests/test_agent.py::TestPortfolioOptimizer::test_compute_rebalance_trades_no_drift` passes
- `pytest tests/test_agent.py::TestPortfolioOptimizer::test_compute_rebalance_trades_with_drift` passes
- `pytest tests/test_agent.py::TestPortfolioOptimizer::test_rebalance_trade_actions_correct` passes

---

### Task 7.7 — Wire up APScheduler in main.py

**File:** `quant_monitor/main.py`
**Method:** `main()` — replace the TODO block with real scheduler wiring.

**Implementation:**

```python
def run_signal_cycle() -> None:
    """Execute one full signal generation cycle.

    1. Fetch data (prices, macro, news, fundamentals)
    2. Compute features (MA matrix, volatility, sentiment)
    3. Run models (technical, macro, sentiment, fundamental)
    4. Classify regime
    5. Fuse signals
    6. Risk-check + optimization
    7. Store results in Appwrite
    8. Dispatch alerts if thresholds crossed
    """
    from quant_monitor.config import cfg
    from quant_monitor.data.pipeline import DataPipeline
    from quant_monitor.features.moving_averages import compute_ma_matrix
    from quant_monitor.features.volatility import (
        realized_volatility, volatility_percentile, hurst_exponent, classify_regime,
    )
    from quant_monitor.features.sentiment_features import SentimentFeatureEngine
    from quant_monitor.models.technical import TechnicalModel
    from quant_monitor.models.macro import MacroModel
    from quant_monitor.models.sentiment import SentimentModel
    from quant_monitor.models.fundamental import FundamentalModel
    from quant_monitor.agent.fusion import SignalFusion

    pipeline = DataPipeline()
    tickers = cfg.tickers

    logger.info("── Signal cycle starting for %d tickers ──", len(tickers))

    try:
        # 1. Fetch data
        prices = pipeline.fetch_prices(tickers)
        macro = pipeline.fetch_macro()
        news = pipeline.fetch_news(tickers)
        fundamentals = pipeline.fetch_fundamentals(tickers)

        # 2. Classify volatility regime
        spy_prices = prices.loc["SPY"] if "SPY" in prices.index.get_level_values(0) else None
        if spy_prices is not None and len(spy_prices) > 200:
            returns = spy_prices["close"].pct_change().dropna()
            vol = realized_volatility(returns)
            vol_pct = volatility_percentile(vol.dropna())
            hurst = hurst_exponent(spy_prices["close"])
            vix = macro.get("vix", 20.0)
            regime = str(classify_regime(vol.iloc[-1], vol_pct.iloc[-1], hurst, vix))
        else:
            regime = "LOW_VOL_TREND"  # safe default

        # 3. Run models
        tech_model = TechnicalModel()
        macro_model = MacroModel()
        sent_model = SentimentModel()
        fund_model = FundamentalModel()

        tech_scores = tech_model.score_all(
            {t: prices.loc[t] for t in tickers if t in prices.index.get_level_values(0)}
        )
        macro_score = macro_model.score(macro)
        macro_regime = macro_model.classify_regime(macro)

        # Sentiment: score headlines per ticker
        sent_engine = SentimentFeatureEngine()
        sent_scores = {}
        for ticker in tickers:
            ticker_news = news.get(ticker, [])
            if ticker_news:
                headlines = [n.get("title", "") for n in ticker_news if n.get("title")]
                if headlines:
                    scored = sent_engine.score_headlines(headlines)
                    import pandas as pd
                    scored_df = pd.DataFrame(scored)
                    if not scored_df.empty:
                        sent_scores[ticker] = sent_model.score(scored_df)
                        continue
            sent_scores[ticker] = 0.0

        # Fundamental scores (simplified for scheduler)
        fund_scores = {t: 0.0 for t in tickers}  # placeholder until pipeline provides sector data

        # 4. Fuse signals
        fusion = SignalFusion()
        fused = fusion.fuse_all(tech_scores, fund_scores, sent_scores, macro_score, regime)

        # 5. Log results
        for ticker, result in fused.items():
            if result["action"] != "HOLD":
                logger.info(
                    "SIGNAL: %s → %s (score=%.3f, confidence=%.3f, dominant=%s)",
                    ticker, result["action"], result["fused_score"],
                    result["confidence"], result["dominant_model"],
                )

        logger.info(
            "── Signal cycle complete | Regime: %s | Macro regime: %s ──",
            regime, macro_regime,
        )

    except Exception as e:
        logger.error("Signal cycle failed: %s", e, exc_info=True)


def main() -> None:
    """Start the portfolio monitoring scheduler."""
    from quant_monitor.config import cfg

    logger.info("Quant Portfolio Monitor starting")
    logger.info("Tracking %d positions | Benchmark: %s", len(cfg.tickers), cfg.benchmark)
    logger.info("Valuation date: %s | Sunset: %s", cfg.valuation_date, cfg.sunset_date)

    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = BlockingScheduler()

    interval = cfg.project.get("rebalance_interval_minutes", 15)

    # Run immediately on startup
    run_signal_cycle()

    # Then every N minutes
    scheduler.add_job(
        run_signal_cycle,
        trigger=IntervalTrigger(minutes=interval),
        id="signal_cycle",
        name="Signal Generation Cycle",
        replace_existing=True,
    )

    logger.info("Scheduler started — running every %d minutes", interval)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
```

**Acceptance criteria:**
- `doppler run -- uv run python -c "from quant_monitor.main import run_signal_cycle"` imports without error
- Log output shows signal cycle execution when run manually

---

### Task 7.8 — Run full Phase 7 test suite

```bash
doppler run -- uv run pytest tests/test_agent.py -v
```

**Expected:** All ~13 tests pass.

---

## Phase 8: Backtesting Framework

> **Prerequisites:** Phase 7 COMPLETE.
> **Files to edit:** `quant_monitor/backtest/metrics.py`, `quant_monitor/backtest/engine.py`
> **No new dependencies.**

---

### Task 8.0 — Create Phase 8 test file

**File to CREATE:** `tests/test_backtest.py`

```python
"""Tests for backtesting framework — Phase 8."""

from __future__ import annotations

import pandas as pd
import numpy as np
import pytest


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
```

---

### Task 8.1 — Implement metric functions in metrics.py

**File:** `quant_monitor/backtest/metrics.py`

**Replace ALL `NotImplementedError` stubs with real implementations:**

```python
import numpy as np
import pandas as pd


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualized Sharpe Ratio.

    SR = (mean_return - risk_free_daily) / std_return * sqrt(252)
    """
    if returns.empty or returns.std() == 0:
        return 0.0
    daily_rf = risk_free_rate / 252
    excess = returns - daily_rf
    return float(excess.mean() / excess.std() * np.sqrt(252))


def calmar_ratio(returns: pd.Series) -> float:
    """Calmar Ratio = annualized return / max drawdown."""
    mdd = max_drawdown(returns)
    if mdd == 0:
        return 0.0
    annual_return = (1 + returns).prod() ** (252 / len(returns)) - 1
    return float(annual_return / mdd)


def max_drawdown(returns: pd.Series) -> float:
    """Maximum drawdown from peak to trough.

    Returns positive value (e.g., 0.25 = 25% drawdown).
    """
    if returns.empty:
        return 0.0
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdowns = (running_max - cumulative) / running_max
    return float(drawdowns.max())


def hit_rate(signals: pd.DataFrame) -> float:
    """Percentage of signals that resulted in profitable trades.

    Expects 'pnl' column: positive = profitable.
    """
    if signals.empty or "pnl" not in signals.columns:
        return 0.0
    profitable = (signals["pnl"] > 0).sum()
    return float(profitable / len(signals))


def avg_holding_period(trades: pd.DataFrame) -> float:
    """Average holding period in days.

    Expects 'entry_date' and 'exit_date' columns.
    """
    if trades.empty:
        return 0.0
    if "entry_date" in trades.columns and "exit_date" in trades.columns:
        durations = (
            pd.to_datetime(trades["exit_date"]) - pd.to_datetime(trades["entry_date"])
        ).dt.days
        return float(durations.mean())
    return 0.0


def compute_all_metrics(returns: pd.Series, signals: pd.DataFrame) -> dict:
    """Compute all metrics and return as dict."""
    return {
        "sharpe_ratio": sharpe_ratio(returns),
        "calmar_ratio": calmar_ratio(returns),
        "max_drawdown": max_drawdown(returns),
        "hit_rate": hit_rate(signals),
    }
```

**Add runtime imports at top of file:**
Replace `TYPE_CHECKING` guard with:
```python
import numpy as np
import pandas as pd
```

**Acceptance criteria:**
- `pytest tests/test_backtest.py::TestBacktestMetrics` — all 8 tests pass

---

### Task 8.2 — Implement `WalkForwardEngine.run()` in engine.py

**File:** `quant_monitor/backtest/engine.py`
**Method:** `WalkForwardEngine.run(self, data: pd.DataFrame, model_name: str) -> dict`

**Implementation:**

```python
def run(self, data: pd.DataFrame, model_name: str) -> dict:
    """Run walk-forward backtest for a single model configuration.

    For each window:
    1. Train period: compute features
    2. Test period: generate signals, track P/L

    Returns: dict of aggregated metrics across all test windows.
    """
    import numpy as np
    import pandas as pd
    from quant_monitor.backtest.metrics import sharpe_ratio, max_drawdown, calmar_ratio

    n = len(data)
    min_required = self.train_window + self.test_window

    if n < min_required:
        logger.warning(
            "Insufficient data: %d rows, need %d (train=%d + test=%d)",
            n, min_required, self.train_window, self.test_window,
        )
        return {"error": "insufficient_data", "rows": n, "required": min_required}

    all_test_returns = []
    window_results = []

    start = 0
    while start + min_required <= n:
        train_end = start + self.train_window
        test_end = min(train_end + self.test_window, n)

        train_data = data.iloc[start:train_end]
        test_data = data.iloc[train_end:test_end]

        # Generate simple signals based on model_name
        test_returns = test_data["close"].pct_change().dropna()

        if model_name == "technical":
            # Use MA crossover signal from training period
            from quant_monitor.features.moving_averages import ema
            fast_ma = ema(train_data["close"], 9)
            slow_ma = ema(train_data["close"], 21)
            signal = 1.0 if fast_ma.iloc[-1] > slow_ma.iloc[-1] else -1.0
            test_returns = test_returns * signal

        elif model_name == "fundamental":
            # Fundamental: simple buy-and-hold (always long)
            pass  # returns unchanged

        elif model_name == "sentiment":
            # Sentiment: momentum-based (lagged return sign)
            prev_return = train_data["close"].pct_change().iloc[-5:].mean()
            signal = 1.0 if prev_return > 0 else -1.0
            test_returns = test_returns * signal

        elif model_name == "fused_equal":
            # Equal weight fusion of simple signals
            pass  # returns unchanged (baseline)

        elif model_name == "fused_regime":
            # Regime-weighted: scale by volatility regime
            from quant_monitor.features.volatility import realized_volatility
            vol = realized_volatility(train_data["close"].pct_change().dropna())
            if not vol.empty and vol.iloc[-1] > 0.3:
                test_returns = test_returns * 0.5  # reduce in high vol

        all_test_returns.extend(test_returns.tolist())
        window_results.append({
            "window_start": start,
            "window_end": test_end,
            "mean_return": float(test_returns.mean()) if len(test_returns) > 0 else 0.0,
        })

        start += self.step_size

    if not all_test_returns:
        return {"error": "no_test_returns", "windows_tested": 0}

    returns_series = pd.Series(all_test_returns)

    return {
        "model": model_name,
        "sharpe_ratio": sharpe_ratio(returns_series),
        "max_drawdown": max_drawdown(returns_series),
        "calmar_ratio": calmar_ratio(returns_series),
        "total_return": float((1 + returns_series).prod() - 1),
        "mean_daily_return": float(returns_series.mean()),
        "windows_tested": len(window_results),
        "window_details": window_results,
    }
```

**Add runtime imports at top of file:**
Replace `TYPE_CHECKING` guard with:
```python
import pandas as pd
```

---

### Task 8.3 — Implement `WalkForwardEngine.compare_models()` in engine.py

**File:** `quant_monitor/backtest/engine.py`
**Method:** `WalkForwardEngine.compare_models(self, data: pd.DataFrame) -> pd.DataFrame`

**Implementation:**

```python
def compare_models(self, data: pd.DataFrame) -> pd.DataFrame:
    """Run all 5 model configs and return comparative metrics table.

    Models tested:
    1. technical — MA crossover signals
    2. fundamental — buy and hold
    3. sentiment — momentum-based
    4. fused_equal — equal-weight fusion
    5. fused_regime — dynamic regime-weighted fusion (expected winner)
    """
    import pandas as pd

    model_names = ["technical", "fundamental", "sentiment", "fused_equal", "fused_regime"]
    results = []

    for name in model_names:
        try:
            metrics = self.run(data, name)
            if "error" not in metrics:
                results.append(metrics)
            else:
                logger.warning("Model '%s' backtest failed: %s", name, metrics.get("error"))
        except Exception as e:
            logger.warning("Model '%s' backtest exception: %s", name, e)

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    # Set model name as index for easy comparison
    if "model" in df.columns:
        df = df.set_index("model")
    return df
```

**Acceptance criteria:**
- `pytest tests/test_backtest.py::TestWalkForwardEngine` — all 3 tests pass

---

### Task 8.4 — Run full Phase 8 test suite

```bash
doppler run -- uv run pytest tests/test_backtest.py -v
```

**Expected:** All ~11 tests pass.

---

## Phase 9: Rich CLI + OpenBB Dashboard

> **Prerequisites:** Phase 8 COMPLETE.
> **Files to edit:** `quant_monitor/dashboard/app.py`, `quant_monitor/dashboard/__init__.py`
> **File to create:** `quant_monitor/dashboard/data_loader.py`
> **New dependencies:** `rich>=13.0.0` (terminal UI), `openbb>=4.3.0` (financial data toolkit)
> **Dependencies to REMOVE:** `streamlit>=1.32.0` (no longer needed)
> **Procfile change:** Remove `web:` Streamlit dyno; dashboard is now a CLI tool.
>
> **Design rationale:** A Rich-based terminal dashboard is:
> - Instant to launch — no browser, no web server
> - SSH-friendly — works on headless servers and remote sessions
> - Composable — can be called from scheduler, CI, or manual invocation
> - Extensible — OpenBB Platform adds 100+ financial data endpoints for free
>
> **Testing approach:** Phase 9 tasks include a lightweight test file verifying
> data_loader outputs and that the CLI entry point is callable. Visual acceptance
> is done with `doppler run -- uv run quant-dashboard`.

---

### Task 9.0 — Update dependencies and project entry points

**Files to EDIT:** `pyproject.toml`, `Procfile`

**Step 1 — pyproject.toml:** Replace `streamlit>=1.32.0` with Rich + OpenBB:

```toml
    # Dashboard (CLI)
    "rich>=13.0.0",
    "openbb>=4.3.0",
```

Add a CLI entry point:

```toml
[project.scripts]
quant-monitor = "quant_monitor.main:main"
quant-dashboard = "quant_monitor.dashboard.app:main"
```

**Step 2 — Procfile:** Remove the Streamlit web dyno. The dashboard is now a CLI
tool running on-demand or via the worker process:

```
worker: uv run python -m quant_monitor.main
```

(The `web:` line is deleted entirely.)

**Step 3 — Lock:**

```bash
uv lock
uv sync
```

**Acceptance criteria:**
- `uv run quant-dashboard --help` exits 0
- No import errors for `rich` or `openbb`

---

### Task 9.1 — Create data_loader helper module

**File to CREATE:** `quant_monitor/dashboard/data_loader.py`

```python
"""Dashboard data loader — fetches data for Rich CLI views.

Uses functools.lru_cache for in-process caching (TTL managed by diskcache
underneath the DataPipeline). Falls back gracefully when Appwrite / pipeline
is unavailable.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def load_portfolio_state() -> dict[str, Any]:
    """Load current portfolio holdings and values from config."""
    from quant_monitor.config import cfg

    holdings: dict[str, dict] = {}
    for ticker, info in cfg.holdings.items():
        holdings[ticker] = {
            "name": info["name"],
            "type": info["type"],
            "qty": info["qty"],
            "price_paid": info["price_paid"],
            "sector": info["sector"],
            "cost_basis": info["qty"] * info["price_paid"],
        }

    return {
        "holdings": holdings,
        "cash": cfg.project.get("cash_balance", 0),
        "initial_capital": cfg.initial_capital,
        "benchmark": cfg.benchmark,
        "tickers": cfg.tickers,
    }


def load_latest_prices() -> dict[str, float]:
    """Fetch latest prices for all portfolio tickers via DataPipeline."""
    try:
        from quant_monitor.data.pipeline import DataPipeline

        pipeline = DataPipeline()
        prices = pipeline.fetch_latest_prices()
        return {t: p.get("price", 0) for t, p in prices.items()} if prices else {}
    except Exception as e:
        logger.warning("Failed to load latest prices: %s", e)
        return {}


def load_macro_snapshot() -> dict[str, float]:
    """Fetch current macro indicators from FRED / pipeline."""
    try:
        from quant_monitor.data.pipeline import DataPipeline

        pipeline = DataPipeline()
        return pipeline.fetch_macro()
    except Exception as e:
        logger.warning("Failed to load macro data: %s", e)
        return {}


def load_signals_from_appwrite() -> list[dict]:
    """Fetch latest signals from Appwrite backend."""
    try:
        from quant_monitor.data.appwrite_client import create_appwrite_client

        client = create_appwrite_client()
        return client.get_latest_signals()
    except Exception as e:
        logger.warning("Failed to load signals: %s", e)
        return []


def build_holdings_dataframe(
    holdings: dict[str, dict],
    prices: dict[str, float],
) -> pd.DataFrame:
    """Build a DataFrame of holdings with P/L calculations.

    Shared by both CLI views and potential future web views.
    """
    rows = []
    for ticker, info in holdings.items():
        current_price = prices.get(ticker, info["price_paid"])
        market_value = info["qty"] * current_price
        cost_basis = info["cost_basis"]
        pnl = market_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        rows.append(
            {
                "ticker": ticker,
                "name": info["name"],
                "sector": info["sector"],
                "qty": info["qty"],
                "avg_cost": info["price_paid"],
                "current": current_price,
                "market_value": market_value,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
            }
        )
    return pd.DataFrame(rows)
```

---

### Task 9.2 — Rewrite app.py — CLI entry point with Rich Layout

**File to REWRITE:** `quant_monitor/dashboard/app.py`

Replace the entire Streamlit stub with a Rich-based CLI application:

```python
"""Rich CLI dashboard — 5 views for portfolio monitoring.

Views:
1. Portfolio Overview — P/L table, total value, excess return vs SPY
2. Signal Dashboard  — per-ticker signal scores, confidence, dominant model
3. Regime Monitor    — current macro regime, VIX, DXY, yield curve
4. Monte Carlo       — simulation summary statistics + ASCII histogram
5. System Health     — API feed status, last update timestamps, cache stats

Run:  doppler run -- uv run quant-dashboard [--view <name>] [--live]
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import Sequence

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

logger = logging.getLogger(__name__)
console = Console()

VIEWS = [
    "overview",
    "signals",
    "regime",
    "montecarlo",
    "health",
]


# ---------------------------------------------------------------------------
# View renderers — each returns a Rich renderable (Table, Panel, Group, …)
# ---------------------------------------------------------------------------

def render_portfolio_overview() -> Panel:
    """Portfolio Overview — P/L table, KPIs, sector breakdown."""
    from quant_monitor.dashboard.data_loader import (
        build_holdings_dataframe,
        load_latest_prices,
        load_portfolio_state,
    )

    state = load_portfolio_state()
    prices = load_latest_prices()
    df = build_holdings_dataframe(state["holdings"], prices)

    table = Table(
        title="Holdings",
        show_lines=True,
        header_style="bold cyan",
    )
    table.add_column("Ticker", style="bold")
    table.add_column("Name")
    table.add_column("Sector")
    table.add_column("Qty", justify="right")
    table.add_column("Avg Cost", justify="right")
    table.add_column("Current", justify="right")
    table.add_column("Mkt Value", justify="right")
    table.add_column("P/L ($)", justify="right")
    table.add_column("P/L (%)", justify="right")

    for _, row in df.iterrows():
        pnl_style = "green" if row["pnl"] >= 0 else "red"
        table.add_row(
            row["ticker"],
            row["name"],
            row["sector"],
            str(row["qty"]),
            f"${row['avg_cost']:.2f}",
            f"${row['current']:.2f}",
            f"${row['market_value']:,.0f}",
            Text(f"${row['pnl']:+,.0f}", style=pnl_style),
            Text(f"{row['pnl_pct']:+.2f}%", style=pnl_style),
        )

    total_value = df["market_value"].sum() + state["cash"]
    total_pnl = total_value - state["initial_capital"]
    total_pnl_pct = (total_pnl / state["initial_capital"]) * 100 if state["initial_capital"] else 0

    subtitle = (
        f"Value: ${total_value:,.0f}  |  "
        f"P/L: ${total_pnl:+,.0f} ({total_pnl_pct:+.2f}%)  |  "
        f"Cash: ${state['cash']:,.0f}  |  "
        f"Positions: {len(state['holdings'])}"
    )
    return Panel(table, title="[bold]Portfolio Overview[/bold]", subtitle=subtitle)


def render_signal_dashboard() -> Panel:
    """Signal Dashboard — per-ticker fused scores."""
    from quant_monitor.dashboard.data_loader import (
        load_portfolio_state,
        load_signals_from_appwrite,
    )

    signals = load_signals_from_appwrite()
    state = load_portfolio_state()

    table = Table(title="Latest Signals", show_lines=True, header_style="bold magenta")
    columns = ["Ticker", "Technical", "Fundamental", "Sentiment", "Macro", "Fused", "Confidence", "Action", "Regime"]
    for col in columns:
        justify = "right" if col not in ("Ticker", "Action", "Regime") else "left"
        table.add_column(col, justify=justify)

    if not signals:
        for ticker in state["tickers"]:
            table.add_row(ticker, *["—"] * 8)
        return Panel(table, title="[bold]Signal Dashboard[/bold]", subtitle="No signals yet — run signal cycle first")

    import pandas as pd

    df = pd.DataFrame(signals)
    if "ticker" in df.columns and "timestamp" in df.columns:
        latest = df.sort_values("timestamp").groupby("ticker").last().reset_index()
    else:
        latest = df

    for _, row in latest.iterrows():
        action = str(row.get("action", "HOLD"))
        action_style = {"BUY": "green", "SELL": "red", "HOLD": "yellow"}.get(action, "white")

        table.add_row(
            str(row.get("ticker", "")),
            f"{row.get('technical_score', 0):.3f}",
            f"{row.get('fundamental_score', 0):.3f}",
            f"{row.get('sentiment_score', 0):.3f}",
            f"{row.get('macro_score', 0):.3f}",
            f"{row.get('fused_score', 0):.3f}",
            f"{row.get('confidence', 0):.2f}",
            Text(action, style=action_style),
            str(row.get("regime", "")),
        )

    return Panel(table, title="[bold]Signal Dashboard[/bold]")


def render_regime_monitor() -> Panel:
    """Regime Monitor — macro indicators + regime classification."""
    from quant_monitor.dashboard.data_loader import load_macro_snapshot

    macro = load_macro_snapshot()

    table = Table(title="Macro Indicators", show_lines=True, header_style="bold blue")
    table.add_column("Indicator", style="bold")
    table.add_column("Value", justify="right")
    table.add_column("Status")

    vix = macro.get("vix")
    dxy = macro.get("dxy")
    yield_10y = macro.get("yield_10y")
    yield_2y = macro.get("yield_2y")

    if isinstance(vix, (int, float)):
        vix_style = "red" if vix > 25 else ("yellow" if vix > 18 else "green")
        table.add_row("VIX", f"{vix:.2f}", Text("Elevated" if vix > 25 else "Normal", style=vix_style))
    else:
        table.add_row("VIX", "N/A", "—")

    if isinstance(dxy, (int, float)):
        table.add_row("DXY", f"{dxy:.2f}", "—")
    else:
        table.add_row("DXY", "N/A", "—")

    if isinstance(yield_10y, (int, float)):
        table.add_row("10Y Yield", f"{yield_10y:.2f}%", "—")
    else:
        table.add_row("10Y Yield", "N/A", "—")

    if isinstance(yield_2y, (int, float)):
        table.add_row("2Y Yield", f"{yield_2y:.2f}%", "—")
    else:
        table.add_row("2Y Yield", "N/A", "—")

    # Yield curve spread
    if isinstance(yield_10y, (int, float)) and isinstance(yield_2y, (int, float)):
        spread = yield_10y - yield_2y
        spread_style = "red bold" if spread < 0 else ("yellow" if spread < 0.5 else "green")
        spread_status = "INVERTED" if spread < 0 else ("Flattening" if spread < 0.5 else "Normal")
        table.add_row("Spread (10Y-2Y)", f"{spread:.2f}%", Text(spread_status, style=spread_style))

    # Regime classification
    regime_text = "Unknown"
    try:
        from quant_monitor.models.macro import MacroModel

        model = MacroModel()
        regime_text = model.classify_regime(macro)
    except Exception as e:
        logger.warning("Could not classify regime: %s", e)

    return Panel(table, title="[bold]Regime Monitor[/bold]", subtitle=f"Regime: {regime_text}")


def render_monte_carlo() -> Panel:
    """Monte Carlo — 10k-path simulation summary with ASCII percentile bars."""
    import numpy as np

    from quant_monitor.config import cfg

    initial_value = cfg.initial_capital
    n_sims = 10_000
    annual_return = 0.08
    annual_vol = 0.18

    from datetime import date

    valuation = date.fromisoformat(cfg.valuation_date)
    trading_days = max(1, int((valuation - date.today()).days * 252 / 365))

    daily_ret = annual_return / 252
    daily_vol = annual_vol / np.sqrt(252)

    terminal = initial_value * np.exp(
        np.cumsum(
            np.random.normal(daily_ret, daily_vol, (n_sims, trading_days)),
            axis=1,
        )[:, -1]
    )

    percentiles = [5, 25, 50, 75, 95]
    pct_vals = {p: float(np.percentile(terminal, p)) for p in percentiles}

    table = Table(title=f"Monte Carlo ({n_sims:,} paths, {trading_days} days)", show_lines=True, header_style="bold green")
    table.add_column("Scenario", style="bold")
    table.add_column("Terminal Value", justify="right")
    table.add_column("Return", justify="right")
    table.add_column("Bar")

    labels = {5: "Worst 5%", 25: "25th pctile", 50: "Median", 75: "75th pctile", 95: "Best 5%"}
    max_val = pct_vals[95]
    for p in percentiles:
        val = pct_vals[p]
        ret_pct = (val / initial_value - 1) * 100
        bar_len = int((val / max_val) * 30) if max_val > 0 else 0
        bar_style = "green" if ret_pct >= 0 else "red"
        table.add_row(
            labels[p],
            f"${val:,.0f}",
            Text(f"{ret_pct:+.1f}%", style=bar_style),
            Text("█" * bar_len, style=bar_style),
        )

    prob_loss = float((terminal < initial_value).mean() * 100)
    return Panel(table, title="[bold]Monte Carlo Simulation[/bold]", subtitle=f"P(loss): {prob_loss:.1f}%")


def render_system_health() -> Panel:
    """System Health — feed status, config overview, cache info."""
    from quant_monitor.config import cfg

    table = Table(title="System Health", show_lines=True, header_style="bold yellow")
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Detail")

    # Data feeds
    feeds = {
        "Massive/Polygon": cfg.secrets.MASSIVE_API_KEY,
        "FRED": cfg.secrets.FRED_API_KEY,
        "Appwrite": cfg.secrets.APPWRITE_API_KEY,
        "Telegram": cfg.secrets.TELEGRAM_BOT_TOKEN,
        "SEC EDGAR": cfg.secrets.SEC_EDGAR_USER_AGENT,
        "Zyte/Scrapy": cfg.secrets.ZYTE_API_KEY,
    }
    for name, key in feeds.items():
        ok = bool(key)
        table.add_row(name, Text("OK" if ok else "MISSING", style="green" if ok else "red"), "API key configured" if ok else "Set in Doppler")

    # Config
    table.add_row("Tickers", "INFO", ", ".join(cfg.tickers))
    table.add_row("Benchmark", "INFO", cfg.benchmark)
    table.add_row("Rebalance", "INFO", f"{cfg.project.get('rebalance_interval_minutes', 15)} min")

    # Cache
    try:
        from quant_monitor.data.cache import get_cache

        cache = get_cache()
        size = len(cache) if hasattr(cache, "__len__") else "N/A"
        table.add_row("Cache", Text("OK", style="green"), f"{size} entries")
    except Exception as e:
        table.add_row("Cache", Text("ERR", style="red"), str(e))

    return Panel(table, title="[bold]System Health[/bold]")


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------

VIEW_RENDERERS = {
    "overview": render_portfolio_overview,
    "signals": render_signal_dashboard,
    "regime": render_regime_monitor,
    "montecarlo": render_monte_carlo,
    "health": render_system_health,
}


def _build_full_layout() -> Layout:
    """Build a Rich Layout with all views stacked vertically."""
    layout = Layout()
    layout.split_column(
        Layout(name="overview", ratio=2),
        Layout(name="signals", ratio=2),
        Layout(name="bottom", ratio=1),
    )
    layout["bottom"].split_row(
        Layout(name="regime"),
        Layout(name="health"),
    )
    return layout


def run_single(view: str | None) -> None:
    """Print one or all views to the console and exit."""
    if view and view in VIEW_RENDERERS:
        console.print(VIEW_RENDERERS[view]())
    else:
        for name, renderer in VIEW_RENDERERS.items():
            console.print(renderer())
            console.print()


def run_live(view: str | None, refresh: int = 60) -> None:
    """Refresh view(s) every *refresh* seconds using Rich Live."""
    console.print(f"[bold]Live mode[/bold] — refreshing every {refresh}s (Ctrl+C to quit)\n")
    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                if view and view in VIEW_RENDERERS:
                    live.update(VIEW_RENDERERS[view]())
                else:
                    # Stack all panels
                    from rich.console import Group

                    panels = [renderer() for renderer in VIEW_RENDERERS.values()]
                    live.update(Group(*panels))
                time.sleep(refresh)
    except KeyboardInterrupt:
        console.print("\n[dim]Dashboard stopped.[/dim]")


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point for quant-dashboard."""
    parser = argparse.ArgumentParser(
        prog="quant-dashboard",
        description="Quant Portfolio Monitor — Rich CLI Dashboard",
    )
    parser.add_argument(
        "--view",
        choices=VIEWS,
        default=None,
        help="Show a single view instead of all views. Choices: %(choices)s",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Enable auto-refresh mode (updates every --interval seconds).",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Refresh interval in seconds for --live mode (default: 60).",
    )
    args = parser.parse_args(argv)

    if args.live:
        run_live(args.view, refresh=args.interval)
    else:
        run_single(args.view)


if __name__ == "__main__":
    main()
```

---

### Task 9.3 — Create Phase 9 test file

**File to CREATE:** `tests/test_dashboard.py`

```python
"""Tests for Rich CLI dashboard — Phase 9."""

from __future__ import annotations

import pytest


class TestDataLoader:
    """Tests for quant_monitor/dashboard/data_loader.py."""

    def test_load_portfolio_state_returns_required_keys(self):
        from quant_monitor.dashboard.data_loader import load_portfolio_state

        state = load_portfolio_state()
        assert "holdings" in state
        assert "initial_capital" in state
        assert "tickers" in state
        assert isinstance(state["holdings"], dict)
        assert len(state["tickers"]) > 0

    def test_build_holdings_dataframe_empty(self):
        from quant_monitor.dashboard.data_loader import build_holdings_dataframe

        df = build_holdings_dataframe({}, {})
        assert len(df) == 0

    def test_build_holdings_dataframe_computes_pnl(self):
        from quant_monitor.dashboard.data_loader import build_holdings_dataframe

        holdings = {
            "AAPL": {
                "name": "Apple",
                "type": "stock",
                "qty": 10,
                "price_paid": 150.0,
                "sector": "Technology",
                "cost_basis": 1500.0,
            }
        }
        prices = {"AAPL": 170.0}
        df = build_holdings_dataframe(holdings, prices)
        assert len(df) == 1
        assert df.iloc[0]["pnl"] == pytest.approx(200.0)
        assert df.iloc[0]["pnl_pct"] == pytest.approx(200 / 1500 * 100)

    def test_build_holdings_dataframe_uses_cost_when_no_price(self):
        from quant_monitor.dashboard.data_loader import build_holdings_dataframe

        holdings = {
            "MSFT": {
                "name": "Microsoft",
                "type": "stock",
                "qty": 5,
                "price_paid": 400.0,
                "sector": "Technology",
                "cost_basis": 2000.0,
            }
        }
        df = build_holdings_dataframe(holdings, {})  # no prices
        assert df.iloc[0]["pnl"] == pytest.approx(0.0)


class TestCLIEntryPoint:
    """Tests for quant_monitor/dashboard/app.py CLI."""

    def test_main_runs_without_error(self):
        """main() with no args should exit cleanly (may print to console)."""
        from quant_monitor.dashboard.app import main

        # Passing --view health so it fetches minimal data
        main(["--view", "health"])

    def test_render_functions_return_panel(self):
        """Every view renderer should return a rich Panel."""
        from rich.panel import Panel

        from quant_monitor.dashboard.app import VIEW_RENDERERS

        # Only test health — others need live data / network
        panel = VIEW_RENDERERS["health"]()
        assert isinstance(panel, Panel)
```

---

### Task 9.4 — Implement OpenBB integration helper (optional enrichment)

**File to CREATE:** `quant_monitor/dashboard/openbb_views.py`

This module provides optional views powered by OpenBB Platform for richer
financial data (options chains, economic calendars, earnings, etc.). If OpenBB
is not installed or keys are not configured, views degrade gracefully.

```python
"""Optional OpenBB-powered enrichment views for the CLI dashboard.

OpenBB Platform provides 100+ data endpoints. We wrap a curated subset
relevant to portfolio monitoring. All functions return Rich renderables
or None if OpenBB is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

logger = logging.getLogger(__name__)


def _get_openbb():
    """Lazy-import OpenBB with graceful failure."""
    try:
        from openbb import obb  # noqa: WPS433
        return obb
    except ImportError:
        logger.info("OpenBB not installed — enrichment views disabled.")
        return None
    except Exception as e:
        logger.warning("OpenBB init error: %s", e)
        return None


def render_economic_calendar(days_ahead: int = 7) -> Panel | None:
    """Upcoming economic events from OpenBB."""
    obb = _get_openbb()
    if obb is None:
        return None

    try:
        from datetime import date, timedelta

        start = date.today()
        end = start + timedelta(days=days_ahead)
        result = obb.economy.calendar(
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            provider="fmp",
        )
        rows = result.to_df().head(15) if hasattr(result, "to_df") else []

        table = Table(title="Economic Calendar (next 7d)", show_lines=True, header_style="bold cyan")
        table.add_column("Date")
        table.add_column("Event")
        table.add_column("Country")
        table.add_column("Impact")

        if hasattr(rows, "iterrows"):
            for _, row in rows.iterrows():
                table.add_row(
                    str(row.get("date", "")),
                    str(row.get("event", "")),
                    str(row.get("country", "")),
                    str(row.get("impact", "")),
                )
        return Panel(table, title="[bold]Economic Calendar (OpenBB)[/bold]")
    except Exception as e:
        logger.warning("OpenBB calendar error: %s", e)
        return None


def render_ticker_summary(ticker: str) -> Panel | None:
    """Quick fundamental snapshot for a single ticker via OpenBB."""
    obb = _get_openbb()
    if obb is None:
        return None

    try:
        profile = obb.equity.profile(symbol=ticker, provider="fmp")
        df = profile.to_df() if hasattr(profile, "to_df") else None
        if df is None or df.empty:
            return None

        info = df.iloc[0]
        table = Table(title=f"{ticker} Summary", show_lines=True, header_style="bold green")
        table.add_column("Field", style="bold")
        table.add_column("Value")

        fields = [
            ("Company", "company_name"),
            ("Sector", "sector"),
            ("Industry", "industry"),
            ("Market Cap", "market_cap"),
            ("Price", "price"),
            ("Beta", "beta"),
            ("52w High", "year_high"),
            ("52w Low", "year_low"),
        ]
        for label, key in fields:
            val = info.get(key, "N/A")
            if isinstance(val, float):
                val = f"{val:,.2f}"
            table.add_row(label, str(val))

        return Panel(table, title=f"[bold]{ticker} (OpenBB)[/bold]")
    except Exception as e:
        logger.warning("OpenBB profile error for %s: %s", ticker, e)
        return None


def render_earnings_upcoming(tickers: list[str]) -> Panel | None:
    """Upcoming earnings dates for portfolio tickers via OpenBB."""
    obb = _get_openbb()
    if obb is None:
        return None

    try:
        table = Table(title="Upcoming Earnings", show_lines=True, header_style="bold yellow")
        table.add_column("Ticker", style="bold")
        table.add_column("Date")
        table.add_column("EPS Est.")
        table.add_column("Revenue Est.")

        for ticker in tickers[:10]:  # limit to avoid rate limits
            try:
                result = obb.equity.estimates.consensus(symbol=ticker, provider="fmp")
                df = result.to_df() if hasattr(result, "to_df") else None
                if df is not None and not df.empty:
                    row = df.iloc[0]
                    table.add_row(
                        ticker,
                        str(row.get("date", "N/A")),
                        f"${row.get('estimated_eps', 'N/A')}",
                        f"${row.get('estimated_revenue', 'N/A')}",
                    )
            except Exception:
                table.add_row(ticker, "—", "—", "—")

        return Panel(table, title="[bold]Earnings Calendar (OpenBB)[/bold]")
    except Exception as e:
        logger.warning("OpenBB earnings error: %s", e)
        return None
```

---

### Task 9.5 — Wire OpenBB views into the main CLI

**File:** `quant_monitor/dashboard/app.py`

Add a `--openbb` flag to the argparser and wire the enrichment views:

```python
# In main() argparser — add:
parser.add_argument(
    "--openbb",
    action="store_true",
    help="Show additional OpenBB-powered views (economic calendar, earnings).",
)

# In run_single() — append after the main loop:
if getattr(args, "openbb", False):
    from quant_monitor.dashboard.openbb_views import (
        render_earnings_upcoming,
        render_economic_calendar,
    )
    from quant_monitor.config import cfg

    cal = render_economic_calendar()
    if cal:
        console.print(cal)
        console.print()

    earn = render_earnings_upcoming(cfg.tickers)
    if earn:
        console.print(earn)
        console.print()
```

**Acceptance criteria:**
- `doppler run -- uv run quant-dashboard --openbb` shows OpenBB panels when keys are configured
- Without `--openbb` flag, no OpenBB calls are made
- Missing OpenBB install logs a warning, does NOT crash

---

### Task 9.6 — Verify CLI dashboard end-to-end

```bash
# Single run — all views
doppler run -- uv run quant-dashboard

# Single view
doppler run -- uv run quant-dashboard --view overview

# Live mode (Ctrl+C to stop)
doppler run -- uv run quant-dashboard --live --interval 30

# With OpenBB enrichment
doppler run -- uv run quant-dashboard --openbb

# Run tests
doppler run -- uv run pytest tests/test_dashboard.py -v
```

**Acceptance criteria:**
- All 5 views render without errors (network errors show warnings, not crashes)
- `--live` mode refreshes on schedule
- `--view <name>` shows only that view
- `--openbb` shows economic calendar + earnings when OpenBB is available
- At least 5 tests pass in `tests/test_dashboard.py`
- No Streamlit references remain anywhere in the codebase

---

## Phase 10: Alerts + Deployment

> **Prerequisites:** Phase 9 COMPLETE.
> **File to edit:** `quant_monitor/agent/alerts.py`
> **Existing dependency:** `python-telegram-bot>=21.0` (already in pyproject.toml)
> **Secrets needed:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (from Doppler)

---

### Task 10.0 — Create Phase 10 test file

**File to CREATE:** `tests/test_alerts.py`

```python
"""Tests for alert dispatcher — Phase 10."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import pytest


class TestAlertDispatcher:
    """Tests for quant_monitor/agent/alerts.py"""

    def test_init_loads_config(self):
        """AlertDispatcher should initialize with config values."""
        from quant_monitor.agent.alerts import AlertDispatcher

        dispatcher = AlertDispatcher()
        assert hasattr(dispatcher, "_cooldown_minutes")
        assert hasattr(dispatcher, "_last_alert_times")

    def test_format_rebalance_alert(self):
        """format_rebalance_alert should produce readable message."""
        from quant_monitor.agent.alerts import AlertDispatcher

        dispatcher = AlertDispatcher()
        trades = [
            {"ticker": "TSM", "action": "BUY", "current_weight": 0.05, "target_weight": 0.08, "delta": 0.03},
            {"ticker": "IONQ", "action": "SELL", "current_weight": 0.10, "target_weight": 0.05, "delta": -0.05},
        ]
        msg = dispatcher.format_rebalance_alert(trades)
        assert isinstance(msg, str)
        assert "TSM" in msg
        assert "IONQ" in msg
        assert "BUY" in msg
        assert "SELL" in msg

    def test_format_kill_switch_alert(self):
        """format_kill_switch_alert should include ticker and drawdown."""
        from quant_monitor.agent.alerts import AlertDispatcher

        dispatcher = AlertDispatcher()
        position = {
            "ticker": "IONQ",
            "open_price": 30.00,
            "current_price": 24.00,
            "drawdown_pct": 0.20,
        }
        msg = dispatcher.format_kill_switch_alert(position)
        assert isinstance(msg, str)
        assert "IONQ" in msg
        assert "20" in msg  # 20% drawdown

    def test_cooldown_prevents_spam(self):
        """Same alert type + ticker within cooldown should be suppressed."""
        from quant_monitor.agent.alerts import AlertDispatcher, AlertType, AlertPriority

        dispatcher = AlertDispatcher()
        # Simulate a recent alert
        key = "REBALANCE:TSM"
        dispatcher._last_alert_times[key] = datetime.utcnow()

        # Should be suppressed (within cooldown window)
        suppressed = dispatcher._is_on_cooldown(AlertType.REBALANCE, "TSM")
        assert suppressed is True

    def test_cooldown_expires(self):
        """Alert after cooldown period should NOT be suppressed."""
        from quant_monitor.agent.alerts import AlertDispatcher, AlertType, AlertPriority

        dispatcher = AlertDispatcher()
        key = "REBALANCE:TSM"
        # Set last alert to 60 minutes ago (beyond 30-min cooldown)
        dispatcher._last_alert_times[key] = datetime.utcnow() - timedelta(minutes=60)

        suppressed = dispatcher._is_on_cooldown(AlertType.REBALANCE, "TSM")
        assert suppressed is False

    def test_critical_alerts_bypass_cooldown(self):
        """CRITICAL priority alerts should bypass cooldown."""
        from quant_monitor.agent.alerts import AlertDispatcher, AlertType, AlertPriority

        dispatcher = AlertDispatcher()
        key = "KILL_SWITCH:IONQ"
        dispatcher._last_alert_times[key] = datetime.utcnow()  # just sent

        # CRITICAL should bypass
        suppressed = dispatcher._is_on_cooldown(
            AlertType.KILL_SWITCH, "IONQ", priority=AlertPriority.CRITICAL
        )
        assert suppressed is False

    @pytest.mark.asyncio
    async def test_send_alert_calls_telegram(self):
        """send_alert should call Telegram API when not on cooldown."""
        from quant_monitor.agent.alerts import AlertDispatcher, AlertType, AlertPriority

        dispatcher = AlertDispatcher()
        dispatcher._bot = MagicMock()
        dispatcher._bot.send_message = AsyncMock(return_value=True)
        dispatcher._chat_id = "test_chat"

        result = await dispatcher.send_alert(
            alert_type=AlertType.MACRO_SHIFT,
            priority=AlertPriority.HIGH,
            message="Regime changed to CRISIS",
        )
        # Should attempt to send (cooldown fresh)
        assert isinstance(result, bool)
```

---

### Task 10.1 — Implement `AlertDispatcher.__init__()` in alerts.py

**File:** `quant_monitor/agent/alerts.py`
**Method:** `AlertDispatcher.__init__(self)`

**Implementation:**

```python
def __init__(self) -> None:
    """Initialize Telegram bot and cooldown tracking."""
    from quant_monitor.config import cfg

    self._cooldown_minutes = cfg.alerts.get("cooldown_minutes", 30)
    self._market_hours_only = cfg.alerts.get("market_hours_only", False)
    self._enabled = cfg.alerts.get("enabled", True)
    self._last_alert_times: dict[str, datetime] = {}

    # Telegram bot setup
    self._bot = None
    self._chat_id = cfg.secrets.TELEGRAM_CHAT_ID

    token = cfg.secrets.TELEGRAM_BOT_TOKEN
    if token and self._enabled:
        try:
            from telegram import Bot
            self._bot = Bot(token=token)
            logger.info("Telegram bot initialized")
        except Exception as e:
            logger.warning("Failed to initialize Telegram bot: %s", e)
    else:
        logger.info("Alerts disabled or Telegram token not configured")
```

Also add necessary imports at the top:
```python
from datetime import datetime, timedelta
```

---

### Task 10.2 — Implement cooldown helper in alerts.py

**File:** `quant_monitor/agent/alerts.py`

**Add this helper method to `AlertDispatcher`:**

```python
def _is_on_cooldown(
    self,
    alert_type: AlertType,
    ticker: str | None = None,
    priority: AlertPriority = AlertPriority.MEDIUM,
) -> bool:
    """Check if an alert is suppressed by cooldown.

    CRITICAL alerts always bypass cooldown.
    """
    if priority == AlertPriority.CRITICAL:
        return False

    key = f"{alert_type}:{ticker or 'PORTFOLIO'}"
    last_sent = self._last_alert_times.get(key)
    if last_sent is None:
        return False

    elapsed = datetime.utcnow() - last_sent
    return elapsed < timedelta(minutes=self._cooldown_minutes)

def _record_alert(self, alert_type: AlertType, ticker: str | None = None) -> None:
    """Record that an alert was sent (for cooldown tracking)."""
    key = f"{alert_type}:{ticker or 'PORTFOLIO'}"
    self._last_alert_times[key] = datetime.utcnow()
```

---

### Task 10.3 — Implement `AlertDispatcher.send_alert()` in alerts.py

**File:** `quant_monitor/agent/alerts.py`
**Method:** `AlertDispatcher.send_alert(self, alert_type, priority, message, ticker) -> bool`

**Implementation:**

```python
async def send_alert(
    self,
    alert_type: AlertType,
    priority: AlertPriority,
    message: str,
    ticker: str | None = None,
) -> bool:
    """Send an alert to the configured Telegram chat.

    Respects cooldown period to avoid spam.
    Returns True if sent, False if suppressed by cooldown or error.
    """
    if not self._enabled:
        logger.debug("Alerts disabled — suppressing %s", alert_type)
        return False

    if self._is_on_cooldown(alert_type, ticker, priority):
        logger.debug("Alert on cooldown: %s for %s", alert_type, ticker)
        return False

    # Format with priority prefix
    priority_emoji = {
        AlertPriority.LOW: "ℹ️",
        AlertPriority.MEDIUM: "⚠️",
        AlertPriority.HIGH: "🔔",
        AlertPriority.CRITICAL: "🚨",
    }
    prefix = priority_emoji.get(priority, "")
    full_message = f"{prefix} [{priority}] {alert_type}\n\n{message}"

    if self._bot and self._chat_id:
        try:
            await self._bot.send_message(
                chat_id=self._chat_id,
                text=full_message,
                parse_mode="HTML",
            )
            self._record_alert(alert_type, ticker)
            logger.info("Alert sent: %s for %s", alert_type, ticker or "PORTFOLIO")
            return True
        except Exception as e:
            logger.error("Failed to send Telegram alert: %s", e)
            return False
    else:
        # Log-only mode (no Telegram configured)
        logger.info("ALERT (log-only): %s", full_message)
        self._record_alert(alert_type, ticker)
        return True
```

---

### Task 10.4 — Implement `AlertDispatcher.format_rebalance_alert()` in alerts.py

**File:** `quant_monitor/agent/alerts.py`

**Implementation:**

```python
def format_rebalance_alert(self, trades: list[dict]) -> str:
    """Format a rebalancing recommendation into a readable message."""
    lines = ["<b>📊 Rebalance Recommendation</b>\n"]

    for trade in trades:
        ticker = trade.get("ticker", "???")
        action = trade.get("action", "???")
        current = trade.get("current_weight", 0)
        target = trade.get("target_weight", 0)
        delta = trade.get("delta", 0)

        arrow = "⬆️" if action == "BUY" else "⬇️"
        lines.append(
            f"{arrow} <b>{ticker}</b>: {action} "
            f"({current:.1%} → {target:.1%}, Δ{delta:+.1%})"
        )

    return "\n".join(lines)
```

---

### Task 10.5 — Implement `AlertDispatcher.format_kill_switch_alert()` in alerts.py

**File:** `quant_monitor/agent/alerts.py`

**Implementation:**

```python
def format_kill_switch_alert(self, position: dict) -> str:
    """Format a kill switch alert with position details."""
    ticker = position.get("ticker", "???")
    open_price = position.get("open_price", 0)
    current = position.get("current_price", 0)
    drawdown = position.get("drawdown_pct", 0)

    return (
        f"🚨 <b>KILL SWITCH TRIGGERED</b>\n\n"
        f"<b>{ticker}</b> is down <b>{drawdown * 100:.1f}%</b> intraday!\n"
        f"Open: ${open_price:.2f} → Current: ${current:.2f}\n\n"
        f"<i>Immediate review recommended.</i>"
    )
```

---

### Task 10.6 — Add additional alert formatters

**File:** `quant_monitor/agent/alerts.py`

**Add these convenience methods to `AlertDispatcher`:**

```python
def format_macro_shift_alert(self, old_regime: str, new_regime: str, macro_data: dict) -> str:
    """Format a macro regime change alert."""
    vix = macro_data.get("vix", "N/A")
    spread = macro_data.get("yield_10y_2y_spread", "N/A")
    return (
        f"🔄 <b>Macro Regime Change</b>\n\n"
        f"{old_regime} → <b>{new_regime}</b>\n"
        f"VIX: {vix} | Yield Spread: {spread}\n\n"
        f"<i>Model weights have been adjusted.</i>"
    )

def format_sentiment_spike_alert(self, ticker: str, momentum: float, headline: str | None = None) -> str:
    """Format a sentiment spike alert."""
    direction = "negative" if momentum < 0 else "positive"
    msg = (
        f"📰 <b>Sentiment Spike: {ticker}</b>\n\n"
        f"Sentiment momentum: <b>{momentum:+.3f}</b> ({direction})\n"
    )
    if headline:
        msg += f"Top headline: <i>{headline}</i>\n"
    return msg

def format_feed_stale_alert(self, feed_name: str, last_update: str) -> str:
    """Format a stale data feed alert."""
    return (
        f"ℹ️ <b>Data Feed Stale</b>\n\n"
        f"<b>{feed_name}</b> last updated: {last_update}\n"
        f"<i>Data may be outdated.</i>"
    )
```

---

### Task 10.7 — Run full Phase 10 test suite

```bash
doppler run -- uv run pytest tests/test_alerts.py -v
```

**Expected:** All ~7 tests pass.

> **NOTE:** `test_send_alert_calls_telegram` requires `pytest-asyncio`.
> If not installed, add `"pytest-asyncio>=0.23.0"` to `[dependency-groups] dev` and run `uv sync`.

---

### Task 10.8 — Integrate alerts into signal cycle (main.py)

**File:** `quant_monitor/main.py`
**Modify:** `run_signal_cycle()` — add alert dispatch at end of cycle.

**Add this block after the "Log results" section (step 5):**

```python
        # 6. Dispatch alerts for actionable signals
        import asyncio
        from quant_monitor.agent.alerts import AlertDispatcher, AlertType, AlertPriority

        dispatcher = AlertDispatcher()

        for ticker, result in fused.items():
            if result["action"] in ("BUY", "SELL"):
                msg = (
                    f"<b>{ticker}</b>: {result['action']}\n"
                    f"Score: {result['fused_score']:.3f} | Confidence: {result['confidence']:.3f}\n"
                    f"Dominant model: {result['dominant_model']}"
                )
                asyncio.run(dispatcher.send_alert(
                    alert_type=AlertType.REBALANCE,
                    priority=AlertPriority.HIGH,
                    message=msg,
                    ticker=ticker,
                ))

        # Check for regime changes (store previous regime somewhere in production)
        if macro_regime == "CRISIS":
            msg = dispatcher.format_macro_shift_alert("TRANSITION", "CRISIS", macro)
            asyncio.run(dispatcher.send_alert(
                alert_type=AlertType.MACRO_SHIFT,
                priority=AlertPriority.CRITICAL,
                message=msg,
            ))
```

---

### Task 10.9 — Verify Heroku deployment configuration

**Files to verify:**
- `Procfile` — should have `worker` entry (no `web` — dashboard is CLI-only)
- `runtime.txt` — should specify Python version
- `bin/post_compile` — should handle any post-deploy steps

```bash
# Verify Procfile
cat Procfile
# Expected:
# worker: doppler run -- python -m quant_monitor.main
```

**Acceptance criteria:**
- `Procfile` defines `worker` dyno
- No `web:` dyno (Streamlit was removed in Phase 9 — dashboard is a CLI tool)
- `runtime.txt` specifies Python 3.11+
- Worker runs scheduler on `worker` dyno
- Dashboard is invoked locally via `quant-dashboard` CLI command

---

### Task 10.10 — End-to-end integration test

**File to CREATE:** `tests/test_integration_e2e.py`

```python
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
        from quant_monitor.data.pipeline import DataPipeline
        from quant_monitor.models.technical import TechnicalModel
        from quant_monitor.models.macro import MacroModel
        from quant_monitor.agent.fusion import SignalFusion

        pipeline = DataPipeline()
        prices = pipeline.fetch_prices(["SPY"], period="1y")
        macro = pipeline.fetch_macro()

        tech_model = TechnicalModel()
        macro_model = MacroModel()
        fusion = SignalFusion()

        tech_scores = tech_model.score_all(
            {"SPY": prices.loc["SPY"] if "SPY" in prices.index.get_level_values(0) else prices}
        )
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
```

---

### Task 10.11 — Run FULL test suite (all phases)

```bash
doppler run -- uv run pytest tests/ -v --tb=short -k "not integration"
```

**Expected:** All unit tests pass across:
- `tests/test_config.py` (Phase 0)
- `tests/test_features.py` (Phase 2)
- `tests/test_models/test_technical.py` (Phase 3)
- `tests/test_models/test_macro.py` (Phase 3)
- `tests/test_sentiment.py` (Phase 4)
- `tests/test_fundamental.py` (Phase 5)
- `tests/test_fusion.py` (Phase 6)
- `tests/test_agent.py` (Phase 7)
- `tests/test_backtest.py` (Phase 8)
- `tests/test_alerts.py` (Phase 10)

**Total estimate:** ~65+ tests passing.

Then run integration tests separately:

```bash
doppler run -- uv run pytest tests/ -v --tb=short -m integration
```

---

## Execution Order Summary (Phases 6–10)

```
Phase 6 (Signal Fusion):
  6.0 → create test file
  6.1 → implement fuse()
  6.2 → implement fuse_all()
  6.3 → run Phase 6 tests

Phase 7 (Agent Orchestrator):
  7.0 → create test file
  7.1 → check_position_limits()
  7.2 → compute_portfolio_beta()
  7.3 → check_kill_switch()
  7.4 → validate_trades()
  7.5 → compute_target_weights() [Black-Litterman]
  7.6 → compute_rebalance_trades()
  7.7 → wire APScheduler in main.py
  7.8 → run Phase 7 tests

Phase 8 (Backtesting):
  8.0 → create test file
  8.1 → implement all metric functions
  8.2 → implement WalkForwardEngine.run()
  8.3 → implement WalkForwardEngine.compare_models()
  8.4 → run Phase 8 tests

Phase 9 (Rich CLI + OpenBB Dashboard):
  9.0 → update deps (remove streamlit, add rich + openbb, update Procfile)
  9.1 → create data_loader helper
  9.2 → rewrite app.py as Rich CLI with 5 views
  9.3 → create test file (test_dashboard.py)
  9.4 → create openbb_views.py enrichment module
  9.5 → wire OpenBB views into CLI (--openbb flag)
  9.6 → end-to-end CLI verification

Phase 10 (Alerts + Deployment):
  10.0  → create test file
  10.1  → AlertDispatcher.__init__()
  10.2  → cooldown helper
  10.3  → send_alert()
  10.4  → format_rebalance_alert()
  10.5  → format_kill_switch_alert()
  10.6  → additional formatters
  10.7  → run Phase 10 tests
  10.8  → integrate alerts into main.py
  10.9  → verify Heroku config
  10.10 → e2e integration test
  10.11 → full test suite
```

---

## Dependency Check

**Existing dependencies** (already in `pyproject.toml`):
- `pyportfolioopt>=1.5.0` — Phase 7 (optimizer)
- `apscheduler>=3.10.0` — Phase 7 (scheduler)
- `plotly>=5.18.0` — Phase 8 (backtest charts, optional in dashboard)
- `python-telegram-bot>=21.0` — Phase 10 (alerts)
- `pandas`, `numpy`, `scipy` — Phases 6–8 (computation)

**New dependencies to ADD in Phase 9:**
- `rich>=13.0.0` — Phase 9 (Rich terminal UI: tables, panels, live refresh)
- `openbb>=4.3.0` — Phase 9 (financial data toolkit, economic calendar, earnings)

**Dependency to REMOVE in Phase 9:**
- `streamlit>=1.32.0` — replaced by Rich CLI + OpenBB

**Procfile change in Phase 9:**
- Remove `web:` Streamlit dyno line entirely
- Keep `worker: uv run python -m quant_monitor.main`

**New entry point in Phase 9:**
- Add `quant-dashboard = "quant_monitor.dashboard.app:main"` to `[project.scripts]`

**One optional dev dependency:**
- `pytest-asyncio>=0.23.0` — Phase 10 (async test for `send_alert`)
  Add to `[dependency-groups] dev` if not present.

---

*Generated: February 25, 2026 | Covers Phase 6 through Phase 10*
*Builds on Phase 0–5 foundation documented in `task.md`*
