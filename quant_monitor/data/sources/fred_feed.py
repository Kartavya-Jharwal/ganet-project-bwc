"""FRED (Federal Reserve Economic Data) feed — macro indicators.

Fetches: VIX, DXY, 10Y yield, 2Y yield, yield curve spread.
Rate limit: 120 req/min. Cached for 1 hour (daily data).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

import pandas as pd
import requests

from quant_monitor.data.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# FRED series IDs
FRED_SERIES = {
    "vix": "VIXCLS",
    "dxy": "DTWEXBGS",  # Trade Weighted US Dollar Index
    "yield_10y": "DGS10",  # 10-Year Treasury Constant Maturity
    "yield_2y": "DGS2",  # 2-Year Treasury Constant Maturity
    "yield_3m": "DTB3",  # 3-Month Treasury Bill
    "fed_funds": "FEDFUNDS",  # Federal Funds Effective Rate
    "unemployment": "UNRATE",  # Unemployment Rate
}


class FredFeed:
    """Macro economic data from FRED API."""

    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize FRED feed.

        Args:
            api_key: FRED API key. If None, reads from FRED_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("FRED_API_KEY", "")
        if not self.api_key:
            logger.warning("FRED_API_KEY not set - FRED queries will fail")

    @rate_limiter.rate_limited("fred")
    def get_series(
        self,
        series_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> pd.Series:
        """Fetch a FRED time series.

        Args:
            series_id: FRED series ID (e.g., 'VIXCLS' for VIX)
            start_date: Start date for data
            end_date: End date for data
            limit: Max observations

        Returns:
            pandas Series with date index
        """
        if not self.api_key:
            logger.error("FRED API key not configured")
            return pd.Series(dtype=float)

        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date.strftime("%Y-%m-%d"),
            "observation_end": end_date.strftime("%Y-%m-%d"),
            "sort_order": "desc",
            "limit": limit,
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/series/observations",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            observations = data.get("observations", [])
            if not observations:
                logger.warning(f"No data for FRED series {series_id}")
                return pd.Series(dtype=float)

            dates = []
            values = []
            for obs in observations:
                date = datetime.strptime(obs["date"], "%Y-%m-%d")
                value_str = obs["value"]
                if value_str != ".":  # FRED uses "." for missing
                    dates.append(date)
                    values.append(float(value_str))

            series = pd.Series(values, index=pd.DatetimeIndex(dates), name=series_id)
            series = series.sort_index()
            logger.debug(f"Fetched {len(series)} observations for {series_id}")
            return series

        except requests.RequestException as e:
            logger.error(f"Error fetching FRED series {series_id}: {e}")
            return pd.Series(dtype=float)

    def get_latest(self, series_id: str) -> float | None:
        """Get the latest value for a series."""
        series = self.get_series(series_id, limit=1)
        if series.empty:
            return None
        return float(series.iloc[-1])

    def get_macro_snapshot(self) -> dict[str, float | None]:
        """Fetch all macro indicators as a single snapshot.

        Returns:
            dict with keys: vix, dxy, yield_10y, yield_2y, yield_curve_spread
        """
        snapshot = {}

        for name, series_id in FRED_SERIES.items():
            value = self.get_latest(series_id)
            snapshot[name] = value
            if value is not None:
                logger.debug(f"{name}: {value:.2f}")

        # Compute yield curve spread
        y10 = snapshot.get("yield_10y")
        y2 = snapshot.get("yield_2y")
        if y10 is not None and y2 is not None:
            snapshot["yield_curve_spread"] = y10 - y2
            snapshot["yield_curve_inverted"] = snapshot["yield_curve_spread"] < 0
        else:
            snapshot["yield_curve_spread"] = None
            snapshot["yield_curve_inverted"] = None

        logger.info(f"Fetched macro snapshot: VIX={snapshot.get('vix')}")
        return snapshot

    def get_vix(self) -> float | None:
        """Get current VIX level."""
        return self.get_latest(FRED_SERIES["vix"])


def create_fred_feed() -> FredFeed:
    """Create FRED feed with API key from environment."""
    return FredFeed()
