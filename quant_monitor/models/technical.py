"""Technical analysis model — MA crossovers, RSI, MACD, Bollinger, volume.

Produces a signal score ∈ [-1.0, +1.0].
Volume confirmation required for high-confidence signals.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class TechnicalModel:
    """Technical analysis signal generator."""

    def score(self, ohlcv: pd.DataFrame, ma_matrix: pd.DataFrame) -> float:
        """Generate technical signal score for a single ticker.

        Components:
        - MA crossover matrix (EMA9/21, SMA50/200)
        - RSI divergence
        - MACD histogram direction
        - Bollinger Band squeeze detection
        - Volume confirmation multiplier

        Returns: signal ∈ [-1.0, +1.0]
        """
        # TODO Phase 3
        raise NotImplementedError

    def score_all(self, data: dict[str, pd.DataFrame]) -> dict[str, float]:
        """Score all tickers. Returns {ticker: signal_score}."""
        # TODO Phase 3
        raise NotImplementedError
