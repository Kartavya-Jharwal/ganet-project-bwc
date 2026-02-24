"""Portfolio optimizer — Black-Litterman + Mean-Variance Optimization.

Computes target weights using posterior expected returns from BL model.
Identifies rebalancing trades when position drift exceeds threshold.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """Black-Litterman + MVO rebalancing engine."""

    def compute_target_weights(
        self,
        current_prices: pd.Series,
        views: dict[str, float],
        view_confidences: dict[str, float],
    ) -> dict[str, float]:
        """Compute optimal target weights using Black-Litterman posterior.

        Args:
            current_prices: latest prices for all tickers
            views: {ticker: expected_excess_return} from signal fusion
            view_confidences: {ticker: confidence} from signal fusion

        Returns: {ticker: target_weight}
        """
        # TODO Phase 7
        raise NotImplementedError

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
        # TODO Phase 7
        raise NotImplementedError
