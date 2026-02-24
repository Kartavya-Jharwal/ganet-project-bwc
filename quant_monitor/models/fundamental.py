"""Fundamental screening model — top-down macro → sector → industry → stock.

Produces a signal score ∈ [-1.0, +1.0].
Compares valuation ratios vs sector median.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class FundamentalModel:
    """Top-down fundamental screening signal generator.

    Flow: Macro → Sector → Industry → Stock
    Is the sector in favor?
      → Is this industry growing within it?
        → Is this stock cheap/expensive vs peers?
    """

    def score(self, fundamentals: dict, sector_data: dict) -> float:
        """Generate fundamental signal score for a single ticker.

        Inputs: P/E, P/S, EV/EBITDA, earnings revision direction, analyst consensus delta
        Output: relative valuation score vs sector median ∈ [-1.0, +1.0]
        """
        # TODO Phase 5
        raise NotImplementedError

    def score_all(self, fundamentals_df: pd.DataFrame) -> dict[str, float]:
        """Score all tickers. Returns {ticker: signal_score}."""
        # TODO Phase 5
        raise NotImplementedError
