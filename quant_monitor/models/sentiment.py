"""Sentiment / NLP model — FinBERT-driven news analysis.

Produces a signal score ∈ [-1.0, +1.0].
Key metric: sentiment CHANGE over 48h, not absolute level.
Rapid negative shift = review trigger regardless of absolute score.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class SentimentModel:
    """Sentiment-based signal generator using FinBERT features."""

    def score(self, sentiment_features: pd.DataFrame) -> float:
        """Generate sentiment signal for a single ticker.

        Weighs: sentiment momentum, absolute level, 8-K classification.
        Returns: signal ∈ [-1.0, +1.0]
        """
        # TODO Phase 4
        raise NotImplementedError

    def score_all(self, sentiment_df: pd.DataFrame) -> dict[str, float]:
        """Score all tickers. Returns {ticker: signal_score}."""
        # TODO Phase 4
        raise NotImplementedError
