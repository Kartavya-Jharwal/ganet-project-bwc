"""Confidence-Filtered Signal Engine.

Monitoring layer that measures realized vs. expected portfolio performance and
filters signals below a confidence threshold before they reach the allocator.

This is NOT a trading bot — it is a signal quality gate that:
1. Wraps the SignalFusion engine with performance tracking
2. Compares realized returns against expected returns from fused signals
3. Maintains a rolling accuracy ledger per ticker
4. Dynamically adjusts confidence thresholds based on historical accuracy
5. Filters out signals whose expected accuracy falls below the gate threshold

Architecture:
    Models → SignalFusion → ConfidenceFilteredSignalEngine → Allocator
                                    ↕
                            PerformanceLedger (realized vs expected)
"""

from __future__ import annotations

import logging
from collections import defaultdict

import numpy as np
import pandas as pd

from quant_monitor.agent.fusion import SignalFusion
from quant_monitor.config import cfg

logger = logging.getLogger(__name__)

# Minimum number of historical signals before accuracy filtering kicks in
_MIN_HISTORY_FOR_FILTERING = 5

# Exponential decay factor for rolling accuracy (recent signals weighted more)
_ACCURACY_DECAY = 0.9


class SignalRecord:
    """A single signal event with realized outcome tracking."""

    __slots__ = (
        "action",
        "confidence",
        "dominant_model",
        "expected_return",
        "fused_score",
        "realized_return",
        "ticker",
        "timestamp",
    )

    def __init__(
        self,
        ticker: str,
        timestamp: str,
        action: str,
        fused_score: float,
        confidence: float,
        expected_return: float,
        dominant_model: str,
    ) -> None:
        self.ticker = ticker
        self.timestamp = timestamp
        self.action = action
        self.fused_score = fused_score
        self.confidence = confidence
        self.expected_return = expected_return
        self.realized_return: float | None = None
        self.dominant_model = dominant_model

    @property
    def is_resolved(self) -> bool:
        return self.realized_return is not None

    @property
    def is_accurate(self) -> bool:
        """Signal was accurate if realized return direction matched expected."""
        if not self.is_resolved:
            return False
        if self.action == "HOLD":
            return True
        return (self.expected_return >= 0) == (self.realized_return >= 0)

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "timestamp": self.timestamp,
            "action": self.action,
            "fused_score": self.fused_score,
            "confidence": self.confidence,
            "expected_return": self.expected_return,
            "realized_return": self.realized_return,
            "dominant_model": self.dominant_model,
            "is_accurate": self.is_accurate if self.is_resolved else None,
        }


class PerformanceLedger:
    """Tracks realized vs expected performance per ticker.

    Maintains a rolling accuracy metric using exponential decay weighting
    so that recent signal accuracy matters more than historical.
    """

    def __init__(self) -> None:
        self._records: list[SignalRecord] = []
        self._by_ticker: dict[str, list[SignalRecord]] = defaultdict(list)

    def record_signal(self, signal: SignalRecord) -> None:
        """Add a new signal to the ledger."""
        self._records.append(signal)
        self._by_ticker[signal.ticker].append(signal)

    def resolve_signal(self, ticker: str, realized_return: float) -> None:
        """Resolve the most recent unresolved signal for a ticker."""
        for record in reversed(self._by_ticker.get(ticker, [])):
            if not record.is_resolved:
                record.realized_return = realized_return
                return
        logger.debug("No unresolved signal found for %s", ticker)

    def ticker_accuracy(self, ticker: str) -> float | None:
        """Compute exponentially-weighted rolling accuracy for a ticker.

        Returns None if insufficient history.
        """
        resolved = [r for r in self._by_ticker.get(ticker, []) if r.is_resolved]
        if len(resolved) < _MIN_HISTORY_FOR_FILTERING:
            return None

        weights = np.array([_ACCURACY_DECAY**i for i in range(len(resolved) - 1, -1, -1)])
        accuracies = np.array([1.0 if r.is_accurate else 0.0 for r in resolved])
        return float(np.average(accuracies, weights=weights))

    def overall_accuracy(self) -> float | None:
        """Compute overall accuracy across all tickers."""
        resolved = [r for r in self._records if r.is_resolved]
        if not resolved:
            return None
        accurate = sum(1 for r in resolved if r.is_accurate)
        return accurate / len(resolved)

    def model_accuracy(self) -> dict[str, float]:
        """Compute accuracy broken down by dominant model."""
        by_model: dict[str, list[bool]] = defaultdict(list)
        for r in self._records:
            if r.is_resolved:
                by_model[r.dominant_model].append(r.is_accurate)
        return {
            model: sum(accs) / len(accs) if accs else 0.0
            for model, accs in by_model.items()
        }

    def performance_summary(self) -> dict:
        """Generate a summary of realized vs expected performance."""
        resolved = [r for r in self._records if r.is_resolved]
        if not resolved:
            return {
                "total_signals": len(self._records),
                "resolved_signals": 0,
                "overall_accuracy": None,
                "mean_expected_return": 0.0,
                "mean_realized_return": 0.0,
                "tracking_error": 0.0,
                "model_accuracy": {},
            }

        expected = np.array([r.expected_return for r in resolved])
        realized = np.array([r.realized_return for r in resolved])
        tracking_errors = realized - expected

        return {
            "total_signals": len(self._records),
            "resolved_signals": len(resolved),
            "overall_accuracy": self.overall_accuracy(),
            "mean_expected_return": float(np.mean(expected)),
            "mean_realized_return": float(np.mean(realized)),
            "tracking_error": float(np.std(tracking_errors)),
            "information_ratio": (
                float(np.mean(tracking_errors) / np.std(tracking_errors))
                if np.std(tracking_errors) > 0
                else 0.0
            ),
            "model_accuracy": self.model_accuracy(),
        }


class ConfidenceFilteredSignalEngine:
    """Signal engine that gates signals based on confidence and historical accuracy.

    This is the monitoring layer — not a bot that executes trades, but a system that
    measures realized vs. expected portfolio performance and filters signals below a
    confidence threshold before they reach the allocator.

    Filtering rules:
    1. Base confidence threshold from config (default 0.65)
    2. If a ticker has sufficient history, its rolling accuracy is checked
    3. Dynamic threshold = base_threshold * (1 + penalty) where penalty
       increases when accuracy drops below 70%
    4. Signals that fail either the confidence or accuracy gate → HOLD
    """

    def __init__(
        self,
        accuracy_gate: float = 0.70,
        penalty_factor: float = 0.15,
    ) -> None:
        self._fusion = SignalFusion()
        self._ledger = PerformanceLedger()
        self._accuracy_gate = accuracy_gate
        self._penalty_factor = penalty_factor
        self._confidence_min = float(cfg.signal_thresholds.get("confidence_min", 0.65))
        self._fused_score_min = float(cfg.signal_thresholds.get("fused_score_min", 0.35))

    @property
    def ledger(self) -> PerformanceLedger:
        return self._ledger

    def _effective_threshold(self, ticker: str) -> float:
        """Compute the effective confidence threshold for a ticker.

        If the ticker has poor historical accuracy, the threshold is raised,
        making it harder for new signals to pass through.
        """
        accuracy = self._ledger.ticker_accuracy(ticker)
        if accuracy is None:
            return self._confidence_min

        if accuracy < self._accuracy_gate:
            # Increase threshold proportional to how far below the gate we are
            gap = self._accuracy_gate - accuracy
            penalty = gap * self._penalty_factor / self._accuracy_gate
            return min(1.0, self._confidence_min + penalty)

        return self._confidence_min

    def filter_signal(
        self,
        ticker: str,
        technical: float,
        fundamental: float,
        sentiment: float,
        macro: float,
        regime: str,
        timestamp: str | None = None,
    ) -> dict:
        """Fuse and filter a single signal through the confidence gate.

        Returns the fusion result with an additional 'filtered' field.
        If filtered=True, the action has been overridden to HOLD.
        """
        import datetime as dt

        result = self._fusion.fuse(technical, fundamental, sentiment, macro, regime)
        ts = timestamp or dt.datetime.now(dt.UTC).isoformat()

        effective_threshold = self._effective_threshold(ticker)
        filtered = False

        # Gate 1: Confidence below effective threshold
        if result["confidence"] < effective_threshold:
            filtered = True

        # Gate 2: Fused score magnitude below minimum
        if abs(result["fused_score"]) < self._fused_score_min:
            filtered = True

        original_action = result["action"]
        if filtered and original_action != "HOLD":
            result["action"] = "HOLD"

        # Compute expected return from the signal
        score = result["fused_score"]
        if original_action == "BUY":
            expected_return = abs(score) * 0.1
        elif original_action == "SELL":
            expected_return = -abs(score) * 0.1
        else:
            expected_return = 0.0

        # Record in ledger
        record = SignalRecord(
            ticker=ticker,
            timestamp=ts,
            action=original_action,
            fused_score=result["fused_score"],
            confidence=result["confidence"],
            expected_return=expected_return,
            dominant_model=result["dominant_model"],
        )
        self._ledger.record_signal(record)

        result["filtered"] = filtered
        result["original_action"] = original_action
        result["effective_threshold"] = effective_threshold
        result["expected_return"] = expected_return
        result["ticker_accuracy"] = self._ledger.ticker_accuracy(ticker)

        if filtered and original_action != "HOLD":
            logger.info(
                "FILTERED %s: %s → HOLD (confidence=%.3f < threshold=%.3f, accuracy=%s)",
                ticker,
                original_action,
                result["confidence"],
                effective_threshold,
                f"{result['ticker_accuracy']:.2f}"
                if result["ticker_accuracy"] is not None
                else "N/A",
            )

        return result

    def filter_all(
        self,
        technical_scores: dict[str, float],
        fundamental_scores: dict[str, float],
        sentiment_scores: dict[str, float],
        macro_score: float,
        regime: str,
        timestamp: str | None = None,
    ) -> dict[str, dict]:
        """Filter signals for all tickers. Returns {ticker: filtered_result}."""
        tickers = set(technical_scores) | set(fundamental_scores) | set(sentiment_scores)
        results: dict[str, dict] = {}
        for ticker in sorted(tickers):
            results[ticker] = self.filter_signal(
                ticker=ticker,
                technical=technical_scores.get(ticker, 0.0),
                fundamental=fundamental_scores.get(ticker, 0.0),
                sentiment=sentiment_scores.get(ticker, 0.0),
                macro=macro_score,
                regime=regime,
                timestamp=timestamp,
            )
        return results

    def resolve_signals(self, realized_returns: dict[str, float]) -> None:
        """Resolve outstanding signals with realized returns.

        Call this after a holding period to update the accuracy ledger.
        """
        for ticker, ret in realized_returns.items():
            self._ledger.resolve_signal(ticker, ret)

    def get_performance_report(self) -> dict:
        """Get a comprehensive performance report."""
        summary = self._ledger.performance_summary()
        summary["confidence_threshold"] = self._confidence_min
        summary["accuracy_gate"] = self._accuracy_gate
        return summary

    def get_signal_history(self) -> pd.DataFrame:
        """Return signal history as a DataFrame for analysis."""
        records = [r.to_dict() for r in self._ledger._records]
        if not records:
            return pd.DataFrame()
        return pd.DataFrame(records)
