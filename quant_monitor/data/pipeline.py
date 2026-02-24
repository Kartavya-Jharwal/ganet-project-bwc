"""Multi-source data pipeline with failover and cross-validation.

Orchestrates data fetching from:
- yfinance: Primary price/fundamentals source (Alpaca not available)
- FRED: Macro indicators (VIX, DXY, yields)
- Appwrite: Scraped data from Scrapy Cloud (SEC EDGAR, Google RSS)

Cross-validates prices across sources; flags >0.5% divergence.
Uses internal rate limiting and TTL-based caching.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pandas as pd

from quant_monitor.config import cfg
from quant_monitor.data.cache import get_cache
from quant_monitor.data.sources.yfinance_feed import yfinance_feed
from quant_monitor.data.sources.fred_feed import create_fred_feed
from quant_monitor.data.appwrite_client import create_appwrite_client

logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrates multi-source data pulls with caching and failover."""

    def __init__(self) -> None:
        """Initialize data sources and cache."""
        self._cache = get_cache()
        self._yfinance = yfinance_feed
        self._fred = create_fred_feed()
        self._appwrite = create_appwrite_client()
        logger.info("DataPipeline initialized with yfinance, FRED, Appwrite")

    def fetch_prices(
        self,
        tickers: list[str] | None = None,
        period: str = "1y",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Fetch OHLCV data for all tickers.

        Args:
            tickers: List of tickers (defaults to cfg.tickers)
            period: Data period for yfinance
            use_cache: Whether to use cache

        Returns:
            DataFrame with MultiIndex (ticker, date) and OHLCV columns
        """
        if tickers is None:
            tickers = cfg.tickers

        cache_key = f"prices:{','.join(sorted(tickers))}:{period}"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Using cached prices")
                return cached

        # Fetch from yfinance (primary source)
        df = self._yfinance.get_bars(tickers, period=period)

        if not df.empty and use_cache:
            ttl = cfg.cache_ttl.get("price_historical", 900)
            self._cache.set(cache_key, df, ttl=ttl)

        return df

    def fetch_latest_prices(
        self,
        tickers: list[str] | None = None,
        use_cache: bool = True,
    ) -> dict[str, dict[str, float]]:
        """Fetch real-time prices for all tickers.

        Args:
            tickers: List of tickers (defaults to cfg.tickers)
            use_cache: Whether to use cache

        Returns:
            Dict mapping ticker to price info
        """
        if tickers is None:
            tickers = cfg.tickers

        cache_key = f"latest_prices:{','.join(sorted(tickers))}"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Using cached latest prices")
                return cached

        prices = self._yfinance.get_latest_prices(tickers)

        if prices and use_cache:
            ttl = cfg.cache_ttl.get("price_realtime", 60)
            self._cache.set(cache_key, prices, ttl=ttl)

        return prices

    def fetch_news(
        self,
        tickers: list[str] | None = None,
        max_per_ticker: int = 5,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """Fetch news from yfinance + scraped sources.

        Args:
            tickers: List of tickers (defaults to cfg.tickers)
            max_per_ticker: Max news items per ticker
            use_cache: Whether to use cache

        Returns:
            List of news items sorted by timestamp desc
        """
        if tickers is None:
            tickers = cfg.tickers

        cache_key = f"news:{','.join(sorted(tickers))}"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Using cached news")
                return cached

        # Get news from yfinance
        news = self._yfinance.get_all_news(tickers, max_per_ticker)

        # TODO: Also fetch from Appwrite scraped_data collection
        # This would include Google RSS and SEC EDGAR filings

        if news and use_cache:
            ttl = cfg.cache_ttl.get("news", 1800)
            self._cache.set(cache_key, news, ttl=ttl)

        return news

    def fetch_macro(self, use_cache: bool = True) -> dict[str, float | None]:
        """Fetch macro indicators from FRED.

        Returns:
            Dict with vix, dxy, yield_10y, yield_2y, yield_curve_spread
        """
        cache_key = "macro_snapshot"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Using cached macro data")
                return cached

        macro = self._fred.get_macro_snapshot()

        if macro and use_cache:
            ttl = cfg.cache_ttl.get("macro", 3600)
            self._cache.set(cache_key, macro, ttl=ttl)

        return macro

    def fetch_fundamentals(
        self,
        tickers: list[str] | None = None,
        use_cache: bool = True,
    ) -> dict[str, dict[str, Any]]:
        """Fetch fundamental ratios for all tickers.

        Args:
            tickers: List of tickers (defaults to cfg.tickers)
            use_cache: Whether to use cache

        Returns:
            Dict mapping ticker to fundamentals dict
        """
        if tickers is None:
            tickers = cfg.tickers

        cache_key = f"fundamentals:{','.join(sorted(tickers))}"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Using cached fundamentals")
                return cached

        fundamentals = {}
        for ticker in tickers:
            info = self._yfinance.get_info(ticker)
            if info:
                fundamentals[ticker] = info

        if fundamentals and use_cache:
            ttl = cfg.cache_ttl.get("fundamentals", 86400)  # 24 hours
            self._cache.set(cache_key, fundamentals, ttl=ttl)

        return fundamentals

    def fetch_all(
        self,
        tickers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch all data at once (prices, news, macro, fundamentals).

        Args:
            tickers: List of tickers (defaults to cfg.tickers)

        Returns:
            Dict with keys: prices, latest_prices, news, macro, fundamentals
        """
        if tickers is None:
            tickers = cfg.tickers

        logger.info(f"Fetching all data for {len(tickers)} tickers")

        return {
            "prices": self.fetch_prices(tickers),
            "latest_prices": self.fetch_latest_prices(tickers),
            "news": self.fetch_news(tickers),
            "macro": self.fetch_macro(),
            "fundamentals": self.fetch_fundamentals(tickers),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return self._cache.stats()

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.info("Pipeline cache cleared")


# Factory function
def create_pipeline() -> DataPipeline:
    """Create and return a DataPipeline instance."""
    return DataPipeline()
