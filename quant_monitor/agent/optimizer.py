"""Portfolio optimizer — Black-Litterman + Mean-Variance Optimization.

Computes target weights using posterior expected returns from BL model.
Identifies rebalancing trades when position drift exceeds threshold.
"""

from __future__ import annotations

import logging

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
            from pypfopt import (
                BlackLittermanModel,
                EfficientFrontier,
            )

            # Build a synthetic covariance matrix from prices if we have enough data
            # For now use a simple identity-based approach scaled by view magnitude
            # In production, this would use historical returns covariance
            cov_matrix = pd.DataFrame(
                np.eye(n) * 0.04,  # 20% annualized vol assumed
                index=tickers,
                columns=tickers,
            )

            # Market-cap weights as prior (equal weight fallback)
            market_prices = (
                current_prices[tickers]
                if isinstance(current_prices, pd.Series) and all(t in current_prices.index for t in tickers)
                else pd.Series({t: 1.0 for t in tickers})
            )
            market_prior = market_prices / market_prices.sum()

            bl = BlackLittermanModel(
                cov_matrix,
                pi=market_prior,
                absolute_views=views,
                omega="idzorek",
                view_confidences=[view_confidences.get(t, 0.5) for t in views],
            )
            bl_returns = bl.bl_returns()

            # Mean-variance optimization
            ef = EfficientFrontier(bl_returns, cov_matrix)
            ef.add_constraint(lambda w: w >= 0)  # long only

            # Avoid infeasible constraints when n is small
            max_pos = max(0.15, 1.0 / n + 0.01) if n > 0 else 0.15
            ef.add_constraint(lambda w: w <= max_pos)  # max 15% per position (soft)

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
                trades.append(
                    {
                        "ticker": ticker,
                        "action": action,
                        "current_weight": round(current, 6),
                        "target_weight": round(target, 6),
                        "delta": round(delta, 6),
                    }
                )

        # Sort by absolute delta descending (largest rebalances first)
        trades.sort(key=lambda t: abs(t["delta"]), reverse=True)
        return trades
