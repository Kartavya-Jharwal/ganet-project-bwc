"""Macro regime model — VIX, yield curve, DXY, 10Y yield signals.

Produces a signal score ∈ [-1.0, +1.0] as portfolio-level adjustment.
Triggers regime classification that shifts fusion weights.

| Signal        | Threshold         | Portfolio Impact                           |
|---------------|-------------------|--------------------------------------------|
| VIX           | > 25              | Risk-off: reduce beta, increase defensives |
| Yield curve   | Inverting          | Recession signal: shift defensive          |
| DXY           | Spiking            | Headwind for TSM (FX), AMZN international  |
| 10Y yield     | Rising >20bps/week | Headwind for PLTR/IONQ high-multiple names |
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MacroModel:
    """Macro regime signal generator and classifier."""

    def score(self, macro_snapshot: dict) -> float:
        """Generate macro signal (portfolio-level, not per-ticker).

        Returns: signal ∈ [-1.0, +1.0] where:
            -1.0 = extreme risk-off
            +1.0 = extreme risk-on
        """
        # TODO Phase 3
        raise NotImplementedError

    def classify_regime(self, macro_snapshot: dict) -> str:
        """Classify current macro regime: RISK_ON | TRANSITION | CRISIS."""
        # TODO Phase 3
        raise NotImplementedError

    def per_ticker_impact(self, macro_snapshot: dict, ticker: str, sector: str) -> float:
        """Compute macro headwind/tailwind for a specific ticker.

        E.g., rising DXY → negative for TSM (ADR FX risk).
        """
        # TODO Phase 3
        raise NotImplementedError
