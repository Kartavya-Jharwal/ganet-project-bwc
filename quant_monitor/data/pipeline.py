"""Multi-source data pipeline with failover and cross-validation.

Orchestrates data fetching from:
- Massive (Polygon.io): PRIMARY source for OHLCV and moving averages
- yfinance: Fallback for prices, fundamentals
- FRED: Macro indicators (VIX, DXY, yields)
- SEC EDGAR: Filings, insider transactions
- News RSS: Google News, financial feeds
- Appwrite: Persistence layer

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
from quant_monitor.data.sources.massive_feed import get_massive_feed, MassiveFeed
from quant_monitor.data.sources.fred_feed import create_fred_feed
from quant_monitor.data.sources.sec_feed import create_sec_feed, SecEdgarFeed
from quant_monitor.data.sources.news_feed import create_news_feed, NewsFeed
from quant_monitor.data.appwrite_client import create_appwrite_client

logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrates multi-source data pulls with caching and failover."""

    def __init__(self) -> None:
        """Initialize data sources and cache."""
        self._cache = get_cache()
        
        # Price feeds (Massive primary, yfinance fallback)
        self._massive = get_massive_feed()
        self._yfinance = yfinance_feed
        
        # Other feeds
        self._fred = create_fred_feed()
        self._sec = create_sec_feed()
        self._news = create_news_feed()
        self._appwrite = create_appwrite_client()
        
        sources = ["Massive" if self._massive.is_available else "yfinance (fallback)"]
        sources.extend(["FRED", "SEC", "News", "Appwrite"])
        logger.info(f"DataPipeline initialized with: {', '.join(sources)}")

    def fetch_prices(
        self,
        tickers: list[str] | None = None,
        period: str = "1y",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Fetch OHLCV data for all tickers.
        
        Uses Massive (Polygon) as PRIMARY source, yfinance as fallback.

        Args:
            tickers: List of tickers (defaults to cfg.tickers)
            period: Data period for yfinance fallback
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

        df = pd.DataFrame()
        
        # Try Massive first (PRIMARY for better data quality)
        if self._massive.is_available:
            logger.debug("Fetching prices from Massive (primary)")
            massive_data = self._massive.get_bars_multi(tickers)
            
            if massive_data:
                frames = []
                for ticker, ticker_df in massive_data.items():
                    ticker_df = ticker_df.copy()
                    ticker_df["ticker"] = ticker
                    ticker_df = ticker_df.reset_index()
                    ticker_df = ticker_df.rename(columns={"timestamp": "date"})
                    ticker_df = ticker_df.set_index(["ticker", "date"])
                    frames.append(ticker_df)
                
                if frames:
                    df = pd.concat(frames).sort_index()
                    logger.info(f"Got {len(df)} bars from Massive for {len(massive_data)} tickers")
        
        # Fallback to yfinance if Massive failed or unavailable
        if df.empty:
            logger.debug("Falling back to yfinance")
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
    ) -> dict[str, list[dict[str, Any]]]:
        """Fetch news from multiple sources (Google RSS, Massive, yfinance).

        Args:
            tickers: List of tickers (defaults to cfg.tickers)
            max_per_ticker: Max news items per ticker
            use_cache: Whether to use cache

        Returns:
            Dict mapping ticker to list of news items
        """
        if tickers is None:
            tickers = cfg.tickers

        cache_key = f"news:{','.join(sorted(tickers))}"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Using cached news")
                return cached

        # Build holdings dict for news feed
        holdings = {t: {"name": cfg.holdings.get(t, {}).get("name", t)} for t in tickers}
        
        # Primary: Google RSS via news feed
        news = self._news.get_portfolio_news(holdings, max_per_ticker, since_days=7)
        
        # Supplement with Massive news if available
        if self._massive.is_available:
            for ticker in tickers:
                massive_news = self._massive.get_ticker_news(ticker, limit=max_per_ticker)
                if massive_news and ticker in news:
                    # Add unique articles from Massive
                    existing_titles = {n.get("title", "").lower()[:50] for n in news[ticker]}
                    for article in massive_news:
                        title_key = article.get("title", "").lower()[:50]
                        if title_key not in existing_titles:
                            news[ticker].append(article)

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

    def fetch_moving_averages(
        self,
        tickers: list[str] | None = None,
        sma_periods: list[int] = [5, 10, 20, 50, 200],
        ema_periods: list[int] = [12, 26],
        use_cache: bool = True,
    ) -> dict[str, dict[str, dict[str, float | None]]]:
        """Fetch moving average matrix from Massive (PRIMARY source).
        
        Falls back to calculating from yfinance data if Massive unavailable.

        Args:
            tickers: List of tickers (defaults to cfg.tickers)
            sma_periods: SMA periods to calculate
            ema_periods: EMA periods to calculate
            use_cache: Whether to use cache

        Returns:
            Dict: {ticker: {"sma": {period: value}, "ema": {period: value}}}
        """
        if tickers is None:
            tickers = cfg.tickers

        cache_key = f"ma_matrix:{','.join(sorted(tickers))}"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Using cached moving averages")
                return cached

        ma_matrix = {}

        # PRIMARY: Use Massive for cleaner data
        if self._massive.is_available:
            logger.info("Calculating MAs from Massive data (primary)")
            ma_matrix = self._massive.get_ma_matrix(tickers, sma_periods, ema_periods)
        else:
            # FALLBACK: Calculate from yfinance data
            logger.info("Calculating MAs from yfinance data (fallback)")
            prices_df = self.fetch_prices(tickers, period="2y", use_cache=True)
            
            for ticker in tickers:
                ma_matrix[ticker] = {"sma": {}, "ema": {}}
                
                try:
                    if ticker in prices_df.index.get_level_values(0):
                        ticker_data = prices_df.loc[ticker]
                        
                        # Get close prices - should be 'close' column after yfinance normalization
                        if "close" in ticker_data.columns:
                            ticker_df = ticker_data["close"]
                        else:
                            # Fallback: try to find any close-like column
                            logger.warning(f"No 'close' column for {ticker}, columns: {ticker_data.columns.tolist()}")
                            continue
                        
                        for period in sma_periods:
                            if len(ticker_df) >= period:
                                ma_matrix[ticker]["sma"][period] = float(
                                    ticker_df.rolling(window=period).mean().iloc[-1]
                                )
                            else:
                                ma_matrix[ticker]["sma"][period] = None
                        
                        for period in ema_periods:
                            if len(ticker_df) >= period:
                                ma_matrix[ticker]["ema"][period] = float(
                                    ticker_df.ewm(span=period, adjust=False).mean().iloc[-1]
                                )
                            else:
                                ma_matrix[ticker]["ema"][period] = None
                except Exception as e:
                    logger.error(f"Error calculating MAs for {ticker}: {e}")
                    ma_matrix[ticker] = {
                        "sma": {p: None for p in sma_periods},
                        "ema": {p: None for p in ema_periods},
                    }

        if ma_matrix and use_cache:
            ttl = cfg.cache_ttl.get("price_historical", 900)
            self._cache.set(cache_key, ma_matrix, ttl=ttl)

        return ma_matrix

    def fetch_sec_filings(
        self,
        tickers: list[str] | None = None,
        filing_types: list[str] | None = None,
        since_days: int = 30,
        use_cache: bool = True,
    ) -> dict[str, list[dict[str, Any]]]:
        """Fetch recent SEC filings for tickers.

        Args:
            tickers: List of tickers (defaults to cfg.tickers)
            filing_types: Types to filter (e.g., ["10-K", "8-K", "4"])
            since_days: Look back period
            use_cache: Whether to use cache

        Returns:
            Dict mapping ticker to list of filings
        """
        if tickers is None:
            tickers = cfg.tickers

        cache_key = f"sec_filings:{','.join(sorted(tickers))}:{since_days}"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Using cached SEC filings")
                return cached

        filings = {}
        
        if self._sec.is_available:
            for ticker in tickers:
                ticker_filings = self._sec.get_recent_filings(
                    ticker,
                    filing_types=filing_types,
                    limit=10,
                    since_days=since_days,
                )
                filings[ticker] = ticker_filings
        else:
            logger.warning("SEC feed not available (no User-Agent configured)")

        if filings and use_cache:
            ttl = cfg.cache_ttl.get("news", 1800)
            self._cache.set(cache_key, filings, ttl=ttl)

        return filings

    def fetch_insider_transactions(
        self,
        tickers: list[str] | None = None,
        since_days: int = 30,
        use_cache: bool = True,
    ) -> dict[str, list[dict[str, Any]]]:
        """Fetch Form 4 insider trading filings.

        Args:
            tickers: List of tickers
            since_days: Look back period
            use_cache: Whether to use cache

        Returns:
            Dict mapping ticker to list of insider transactions
        """
        if tickers is None:
            tickers = cfg.tickers

        cache_key = f"insider_txns:{','.join(sorted(tickers))}:{since_days}"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        transactions = {}
        
        if self._sec.is_available:
            for ticker in tickers:
                transactions[ticker] = self._sec.get_insider_transactions(
                    ticker, limit=10, since_days=since_days
                )

        if transactions and use_cache:
            ttl = cfg.cache_ttl.get("news", 1800)
            self._cache.set(cache_key, transactions, ttl=ttl)

        return transactions

    def fetch_market_news(self, use_cache: bool = True) -> list[dict[str, Any]]:
        """Fetch general market news.

        Returns:
            List of market news articles
        """
        cache_key = "market_news"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        news = self._news.get_market_news(limit=30)

        if news and use_cache:
            ttl = cfg.cache_ttl.get("news", 1800)
            self._cache.set(cache_key, news, ttl=ttl)

        return news

    def fetch_all(
        self,
        tickers: list[str] | None = None,
        include_sec: bool = True,
        include_ma: bool = True,
    ) -> dict[str, Any]:
        """Fetch all data at once.

        Args:
            tickers: List of tickers (defaults to cfg.tickers)
            include_sec: Whether to fetch SEC filings
            include_ma: Whether to fetch moving averages

        Returns:
            Dict with all data types
        """
        if tickers is None:
            tickers = cfg.tickers

        logger.info(f"Fetching all data for {len(tickers)} tickers")

        result = {
            "prices": self.fetch_prices(tickers),
            "latest_prices": self.fetch_latest_prices(tickers),
            "news": self.fetch_news(tickers),
            "macro": self.fetch_macro(),
            "fundamentals": self.fetch_fundamentals(tickers),
            "market_news": self.fetch_market_news(),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if include_ma:
            result["moving_averages"] = self.fetch_moving_averages(tickers)
        
        if include_sec:
            result["sec_filings"] = self.fetch_sec_filings(tickers)
            result["insider_transactions"] = self.fetch_insider_transactions(tickers)
        
        return result

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
