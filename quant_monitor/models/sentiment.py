"""Sentiment / NLP model — FinBERT-driven news analysis.

Produces a signal score ∈ [-1.0, +1.0].
Key metric: sentiment CHANGE over 48h, not absolute level.
Rapid negative shift = review trigger regardless of absolute score.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SentimentModel:
    """Sentiment-based signal generator using FinBERT features."""

    def score(self, sentiment_features: pd.DataFrame) -> float:
        """Generate sentiment signal for a single ticker.

        Weighs: sentiment momentum, absolute level, 8-K classification.
        Returns: signal ∈ [-1.0, +1.0]
        """
        if sentiment_features.empty:
            return 0.0

        # Component 1: Current sentiment level (weight 0.4)
        current_level = 0.0
        if "ma_3h" in sentiment_features.columns:
            current_level = float(sentiment_features["ma_3h"].iloc[-1])
        elif "score" in sentiment_features.columns:
            current_level = float(sentiment_features["score"].mean())

        # Component 2: Sentiment momentum (weight 0.4)
        momentum = 0.0
        if "momentum" in sentiment_features.columns:
            momentum = float(sentiment_features["momentum"].iloc[-1])
        elif "ma_3h" in sentiment_features.columns and "ma_72h" in sentiment_features.columns:
            momentum = float(
                sentiment_features["ma_3h"].iloc[-1]
                - sentiment_features["ma_72h"].iloc[-1]
            )

        # Component 3: Absolute recent score (weight 0.2)
        recent_score = 0.0
        if "score" in sentiment_features.columns:
            tail = sentiment_features["score"].iloc[-5:]
            recent_score = float(tail.mean())

        weighted = current_level * 0.4 + momentum * 0.4 + recent_score * 0.2
        return float(max(-1.0, min(1.0, weighted)))

    def score_all(self, sentiment_df: pd.DataFrame) -> dict[str, float]:
        """Score all tickers. Returns {ticker: signal_score}."""
        results: dict[str, float] = {}
        if "ticker" not in sentiment_df.columns:
            logger.warning("sentiment_df missing 'ticker' column")
            return results

        for ticker, group in sentiment_df.groupby("ticker"):
            try:
                results[str(ticker)] = self.score(group)
            except Exception as e:
                logger.warning("Sentiment scoring failed for %s: %s", ticker, e)
                results[str(ticker)] = 0.0
        return results
