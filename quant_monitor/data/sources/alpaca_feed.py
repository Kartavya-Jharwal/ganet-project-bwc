"""Alpaca Markets feed — real-time OHLCV prices and news.

Uses alpaca-py SDK. Rate limit: 200 req/min.
Failover: if Alpaca is down, pipeline falls back to Appwrite (scraped data).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class AlpacaFeed:
    """Real-time price and news data from Alpaca Markets API."""

    def __init__(self) -> None:
        # TODO Phase 1: Initialize Alpaca client from cfg.secrets
        pass

    def get_bars(
        self, tickers: list[str], timeframe: str = "1Day", limit: int = 252
    ) -> pd.DataFrame:
        """Fetch OHLCV bars for multiple tickers."""
        # TODO Phase 1
        raise NotImplementedError

    def get_latest_quotes(self, tickers: list[str]) -> pd.DataFrame:
        """Fetch latest bid/ask quotes."""
        # TODO Phase 1
        raise NotImplementedError

    def get_news(self, tickers: list[str], limit: int = 50) -> pd.DataFrame:
        """Fetch recent news articles mentioning any of the tickers."""
        # TODO Phase 1
        raise NotImplementedError

    def is_market_open(self) -> bool:
        """Check if US equity market is currently open."""
        # TODO Phase 1
        raise NotImplementedError
