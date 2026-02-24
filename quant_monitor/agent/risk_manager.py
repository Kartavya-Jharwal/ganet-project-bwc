"""Risk manager — position limits, beta targets, kill switch.

Validates proposed trades against charter constraints and dynamic risk params.
Adjusts limits based on current macro regime.

| Macro Regime | Max Position | Max Sector | Target Beta |
|-------------|-------------|-----------|------------|
| RISK_ON     | 10%         | 25%       | 0.50       |
| TRANSITION  | 8%          | 20%       | 0.35       |
| CRISIS      | 5%          | 15%       | 0.20       |
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class RiskManager:
    """Validates trades and monitors portfolio risk constraints."""

    def validate_trades(
        self,
        proposed_trades: list[dict],
        current_positions: dict,
        regime: str,
    ) -> list[dict]:
        """Validate proposed trades against risk limits.

        Returns filtered list of trades that pass all constraints.
        Rejected trades get a 'rejected_reason' field.
        """
        # TODO Phase 7
        raise NotImplementedError

    def check_kill_switch(self, positions: dict, current_prices: dict) -> list[dict]:
        """Check if any position is down >15% intraday.

        Returns list of positions triggering the kill switch.
        """
        # TODO Phase 7
        raise NotImplementedError

    def check_position_limits(self, weights: dict[str, float], regime: str) -> list[str]:
        """Check for position and sector limit breaches. Returns list of violations."""
        # TODO Phase 7
        raise NotImplementedError

    def compute_portfolio_beta(self, weights: dict[str, float], betas: dict[str, float]) -> float:
        """Compute weighted portfolio beta."""
        # TODO Phase 7
        raise NotImplementedError
