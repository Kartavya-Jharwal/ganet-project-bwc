"""Dynamic regime-weighted signal fusion engine.

Arbitrates between 4 model signals using regime-dependent weights.
Macro is an additive adjustment (preserves regime-override role).

Confidence score = 1 - std(model_scores): measures inter-model agreement.
Only generates action when confidence > 0.65 AND |fused_score| > 0.35.
High score + low confidence = HOLD (models disagree).
"""

from __future__ import annotations

import logging

import numpy as np

from quant_monitor.config import cfg

logger = logging.getLogger(__name__)


class SignalFusion:
    """Fuses 4 model signals with dynamic regime-dependent weights."""

    def fuse(
        self,
        technical: float,
        fundamental: float,
        sentiment: float,
        macro: float,
        regime: str,
    ) -> dict:
        """Compute fused signal for a single ticker.

        Args:
            technical: score ∈ [-1, 1]
            fundamental: score ∈ [-1, 1]
            sentiment: score ∈ [-1, 1]
            macro: score ∈ [-1, 1] (additive adjustment)
            regime: current vol regime name

        Returns:
            dict with keys: fused_score, confidence, action, dominant_model
        """
        regime_weights = cfg.regime_weights.get(regime)
        if regime_weights is None:
            logger.warning("Unknown regime %s; defaulting to LOW_VOL_TREND", regime)
            regime_weights = cfg.regime_weights.get("LOW_VOL_TREND", {})

        model_scores = {
            "technical": float(technical),
            "fundamental": float(fundamental),
            "sentiment": float(sentiment),
            "macro": float(macro),
        }
        contributions = {
            model: float(regime_weights.get(model, 0.0)) * score
            for model, score in model_scores.items()
        }

        base_weight = sum(
            float(regime_weights.get(model, 0.0))
            for model in ("technical", "fundamental", "sentiment")
        )
        if base_weight > 0:
            base_score = (
                contributions["technical"]
                + contributions["fundamental"]
                + contributions["sentiment"]
            ) / base_weight
        else:
            base_score = 0.0

        macro_adjustment = float(regime_weights.get("macro", 0.0)) * model_scores["macro"] * 0.5
        fused_score = float(np.clip(base_score + macro_adjustment, -1.0, 1.0))

        confidence = float(np.clip(1.0 - np.std(list(model_scores.values())), 0.0, 1.0))
        confidence_min = float(cfg.signal_thresholds.get("confidence_min", 0.65))
        fused_score_min = float(cfg.signal_thresholds.get("fused_score_min", 0.35))

        if confidence < confidence_min:
            action = "HOLD"
        elif fused_score > fused_score_min:
            action = "BUY" if fused_score > 0.6 else "TRIM_UNDERWEIGHT"
        elif fused_score < -fused_score_min:
            action = "SELL" if fused_score < -0.6 else "TRIM_OVERWEIGHT"
        else:
            action = "HOLD"

        dominant_model = max(contributions, key=lambda model: abs(contributions[model]))
        return {
            "fused_score": fused_score,
            "confidence": confidence,
            "action": action,
            "dominant_model": dominant_model,
        }

    def fuse_all(
        self,
        technical_scores: dict[str, float],
        fundamental_scores: dict[str, float],
        sentiment_scores: dict[str, float],
        macro_score: float,
        regime: str,
    ) -> dict[str, dict]:
        """Fuse signals for all tickers. Returns {ticker: fusion_result}."""
        tickers = set(technical_scores) | set(fundamental_scores) | set(sentiment_scores)
        results: dict[str, dict] = {}
        for ticker in sorted(tickers):
            results[ticker] = self.fuse(
                technical=technical_scores.get(ticker, 0.0),
                fundamental=fundamental_scores.get(ticker, 0.0),
                sentiment=sentiment_scores.get(ticker, 0.0),
                macro=macro_score,
                regime=regime,
            )
        return results
