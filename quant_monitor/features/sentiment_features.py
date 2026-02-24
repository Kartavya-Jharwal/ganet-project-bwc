"""Sentiment feature engineering — FinBERT scoring, sentiment MAs.

Processes news headlines through FinBERT, computes:
- Raw sentiment scores per headline per ticker
- Sentiment MA: 3h, 24h, 72h
- Sentiment momentum: 3h_sentiment - 72h_sentiment
- Entity extraction for held tickers
- SEC 8-K classification
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class SentimentFeatureEngine:
    """Compute sentiment features from news text using FinBERT."""

    def __init__(self) -> None:
        # TODO Phase 4: Load FinBERT model (lazy init to save memory)
        self._model = None
        self._tokenizer = None

    def score_headlines(self, headlines: list[str]) -> list[dict]:
        """Score a batch of headlines through FinBERT.

        Returns list of {text, positive, negative, neutral, label, score}.
        """
        # TODO Phase 4
        raise NotImplementedError

    def compute_sentiment_ma(self, scored_df: pd.DataFrame, windows: list[int]) -> pd.DataFrame:
        """Compute rolling sentiment MAs over time windows (in hours)."""
        # TODO Phase 4
        raise NotImplementedError

    def sentiment_momentum(self, scored_df: pd.DataFrame) -> pd.Series:
        """3h sentiment - 72h sentiment. Rapid negative shift = review trigger."""
        # TODO Phase 4
        raise NotImplementedError

    def deduplicate_news(self, headlines: list[str], threshold: float = 0.85) -> list[str]:
        """Deduplicate headlines via cosine similarity (sentence-transformers)."""
        # TODO Phase 4
        raise NotImplementedError
