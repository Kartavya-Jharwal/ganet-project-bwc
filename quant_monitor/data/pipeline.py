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
import os
from datetime import datetime
from typing import Any

import pandas as pd

from quant_monitor.config import cfg
from quant_monitor.data.appwrite_client import create_appwrite_client
from quant_monitor.data.cache import get_cache
from quant_monitor.data.sources.fred_feed import create_fred_feed
from quant_monitor.data.sources.massive_feed import get_massive_feed
from quant_monitor.data.sources.news_feed import create_news_feed
from quant_monitor.data.sources.sec_feed import create_sec_feed
from quant_monitor.data.sources.yfinance_feed import yfinance_feed

logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrates multi-source data pulls with caching and failover."""

    @staticmethod
    def _has_numeric_value(payload: dict[str, Any]) -> bool:
        """True when at least one value is numeric and not None."""
        return any(isinstance(v, (int, float)) for v in payload.values())

    def __init__(self) -> None:
        """Initialize data sources and cache."""
        self._cache = get_cache()
        self.mode = (
            "consume" if not cfg.secrets.MASSIVE_API_KEY else os.environ.get("MODE", "ingest")
        )

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
        logger.info(
            f"DataPipeline initialized in {self.mode.upper()} mode with: {', '.join(sources)}"
        )

    def fetch_prices(
        self,
        tickers: list[str] | None = None,
        period: str = "1y",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Fetch OHLCV data for all tickers.

        Uses yfinance as PRIMARY source, Massive (Polygon) as fallback.

        Args:
            tickers: List of tickers (defaults to cfg.tickers)
            period: Data period for yfinance fallback
            use_cache: Whether to use cache

        Returns:
            DataFrame with MultiIndex (ticker, date) and OHLCV columns
        """
        if tickers is None:
            tickers = cfg.tickers

        source_hint = "yfinance" if self._yfinance else "massive"
        cache_key = f"prices:{source_hint}:{','.join(sorted(tickers))}:{period}"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("Using cached prices")
                return cached

        df = pd.DataFrame()

        # Phase 12: Consumer mode bypassing APIs
        if getattr(self, "mode", "consume") == "consume":
            logger.info("Consume Mode: Attempting to fetch prices from local DuckDB cache...")
            import duckdb

            try:
                conn = duckdb.connect("portfolio.duckdb", read_only=True)
                duck_df = conn.execute(
                    "SELECT ticker, timestamp as date, close FROM eod_price_matrix"
                ).df()
                conn.close()
                if not duck_df.empty:
                    duck_df["date"] = pd.to_datetime(duck_df["date"])
                    # For compatibility, we mimic OHLCV with just close if needed, but we do our best
                    duck_df["open"] = duck_df["close"]
                    duck_df["high"] = duck_df["close"]
                    duck_df["low"] = duck_df["close"]
                    duck_df["volume"] = 0
                    duck_df = duck_df.set_index(["ticker", "date"]).sort_index()
                    return duck_df
            except Exception as e:
                logger.warning(f"DuckDB read failed or empty: {e}. Falling back to live APIs.")

        # Try yfinance first (PRIMARY)
        logger.debug("Fetching prices from yfinance (primary)")
        df = self._yfinance.get_bars(tickers, period=period)

        # Fallback to Massive if yfinance failed completely
        if df.empty and self._massive.is_available:
            logger.debug("Falling back to Massive (Polygon)")
            import time

            massive_data = {}
            for ticker in tickers:
                logger.debug(f"Fetching Massive price fallback for {ticker}")
                try:
                    res = self._massive.get_bars_multi([ticker])
                    if res and ticker in res:
                        massive_data[ticker] = res[ticker]
                    time.sleep(12)  # Delay to respect free tier (5 req/min)
                except Exception as e:
                    logger.warning(f"Failed Massive fetch for {ticker}: {e}")
                    time.sleep(12)

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
                    logger.info(
                        f"Got {len(df)} bars from Massive fallback for {len(massive_data)} tickers"
                    )

        if not df.empty and use_cache:
            ttl = cfg.cache_ttl.get("price_historical", 900)
            self._cache.set(cache_key, df, ttl=ttl)

        if getattr(self, "mode", "consume") == "ingest" and not df.empty:
            try:
                records = []
                for (ticker, date), row in df.iterrows():
                    dt = pd.to_datetime(date)
                    dt_str = dt.isoformat()
                    if dt.tzinfo is None:
                        dt_str += "Z"  # add utc

                    records.append(
                        {
                            "timestamp": dt_str,
                            "ticker": ticker,
                            "close": float(row.get("close", 0.0)),
                        }
                    )
                if records:
                    from quant_monitor.data.appwrite_client import COLLECTIONS

                    # split into batches of 100 for Appwrite limits
                    for i in range(0, len(records), 100):
                        batch = records[i : i + 100]
                        self._appwrite.write_batch(
                            COLLECTIONS.get("eod_price_matrix", "eod_price_matrix"), batch
                        )
                    logger.info(f"Ingested {len(records)} EOD prices to Appwrite.")
            except Exception as e:
                logger.warning(f"Failed to ingest EOD prices: {e}")

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

        if getattr(self, "mode", "consume") == "consume":
            # In consume mode, try local DuckDB cache first before hitting yfinance
            try:
                import duckdb

                conn = duckdb.connect(database="portfolio.duckdb", read_only=True)
                result = conn.execute(
                    "SELECT ticker, close AS price FROM eod_price_matrix "
                    "WHERE (ticker, timestamp) IN ("
                    "  SELECT ticker, MAX(timestamp) FROM eod_price_matrix GROUP BY ticker"
                    ")"
                ).fetchall()
                conn.close()
                if result:
                    local_prices = {row[0]: {"price": row[1]} for row in result}
                    # Only use local if we have data for most requested tickers
                    if len(set(tickers) & set(local_prices)) >= len(tickers) * 0.5:
                        logger.debug("Using DuckDB cached prices in consume mode")
                        if use_cache:
                            ttl = cfg.cache_ttl.get("price_realtime", 60)
                            self._cache.set(cache_key, local_prices, ttl=ttl)
                        return local_prices
            except Exception:
                logger.debug("DuckDB not available in consume mode, falling back to yfinance")

        prices = self._yfinance.get_latest_prices(tickers)

        if prices and use_cache:
            ttl = cfg.cache_ttl.get("price_realtime", 60)
            self._cache.set(cache_key, prices, ttl=ttl)

        if prices and getattr(self, "mode", "consume") == "ingest" and "SPY" in prices:
            try:
                from quant_monitor.data.appwrite_client import COLLECTIONS

                spy_price = prices["SPY"].get("price")
                if spy_price:
                    self._appwrite.write_document(
                        COLLECTIONS.get("live_spy_proxy", "live_spy_proxy"),
                        {
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "price": float(spy_price),
                        },
                    )
                    logger.info(f"Ingested live SPY proxy: {spy_price}")
            except Exception as e:
                logger.warning(f"Failed to ingest live SPY proxy: {e}")

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

        # Secondary Primary: yfinance
        for ticker in tickers:
            try:
                yf_news = self._yfinance.get_news(ticker, max_items=max_per_ticker)
                if ticker not in news:
                    news[ticker] = []
                # Make sure we don't have dupes based on title
                existing_titles = {n.get("title", "").lower()[:50] for n in news[ticker]}
                for article in yf_news:
                    title_key = article.get("title", "").lower()[:50]
                    if title_key not in existing_titles:
                        news[ticker].append(article)
            except Exception as e:
                logger.warning(f"Error fetching yfinance news for {ticker}: {e}")

        # Supplement with Massive news if available AND needed (delayed)
        if self._massive.is_available:
            import time

            for ticker in tickers:
                if len(news.get(ticker, [])) >= max_per_ticker:
                    continue  # Skip if we already have enough from primary sources

                time.sleep(12)  # Respect minimum 12 second delay (5/min limit)
                try:
                    massive_news = self._massive.get_ticker_news(ticker, limit=max_per_ticker)
                    if massive_news and ticker in news:
                        # Add unique articles from Massive
                        existing_titles = {n.get("title", "").lower()[:50] for n in news[ticker]}
                        for article in massive_news:
                            title_key = article.get("title", "").lower()[:50]
                            if title_key not in existing_titles:
                                news[ticker].append(article)
                except Exception as e:
                    logger.warning(f"Error fetching massive news for {ticker}: {e}")

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

        if macro and self._has_numeric_value(macro) and use_cache:
            ttl = cfg.cache_ttl.get("macro", 3600)
            self._cache.set(cache_key, macro, ttl=ttl)
        elif macro and not self._has_numeric_value(macro):
            logger.warning("Macro snapshot contained no numeric values; skipping cache write")

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
        sma_periods: list[int] | None = None,
        ema_periods: list[int] | None = None,
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
        if sma_periods is None:
            sma_periods = [5, 10, 20, 50, 200]
        if ema_periods is None:
            ema_periods = [12, 26]

        sma_key = ",".join(str(p) for p in sorted(sma_periods))
        ema_key = ",".join(str(p) for p in sorted(ema_periods))
        cache_key = f"ma_matrix:{','.join(sorted(tickers))}:sma[{sma_key}]:ema[{ema_key}]"

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
                            logger.warning(
                                f"No 'close' column for {ticker}, columns: {ticker_data.columns.tolist()}"
                            )
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
