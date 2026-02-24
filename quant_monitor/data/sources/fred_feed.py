"""FRED (Federal Reserve Economic Data) feed — macro indicators.

Fetches: VIX, DXY, 10Y yield, 2Y yield, yield curve spread.
Rate limit: 120 req/min. Cached for 1 hour (daily data).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# FRED series IDs
FRED_SERIES = {
    "vix": "VIXCLS",
    "dxy": "DTWEXBGS",  # Trade Weighted US Dollar Index
    "yield_10y": "DGS10",  # 10-Year Treasury Constant Maturity
    "yield_2y": "DGS2",  # 2-Year Treasury Constant Maturity
    "fed_funds": "FEDFUNDS",  # Federal Funds Effective Rate
}


class FredFeed:
    """Macro economic data from FRED API."""

    def __init__(self) -> None:
        # TODO Phase 1: Initialize with FRED API key from cfg.secrets
        pass

    def get_series(self, series_id: str, lookback_days: int = 365) -> dict:
        """Fetch a single FRED series."""
        # TODO Phase 1
        raise NotImplementedError

    def get_macro_snapshot(self) -> dict:
        """Fetch all macro indicators as a single snapshot.

        Returns:
            dict with keys: vix, dxy, yield_10y, yield_2y, yield_curve_spread
        """
        # TODO Phase 1
        raise NotImplementedError
