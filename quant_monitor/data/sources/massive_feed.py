"""Massive (formerly Polygon.io) data feed — primary source for OHLCV and moving averages.

Polygon.io rebranded to Massive.com on Oct 30, 2025. The SDK defaults to api.massive.com
but api.polygon.io continues to work.

This is the PRIMARY source for moving averages due to better data quality.
Falls back to yfinance if Massive is unavailable.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from polygon import RESTClient

from quant_monitor.data.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# Massive API base (new default) — api.polygon.io also still works
MASSIVE_BASE_URL = "https://api.massive.com"


class MassiveFeed:
    """Massive (Polygon) data feed with rate limiting.
    
    Primary source for OHLCV data and moving average calculations.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Massive feed.
        
        Args:
            api_key: Massive/Polygon API key. If None, reads from MASSIVE_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("MASSIVE_API_KEY")
        self._client: RESTClient | None = None
        
        if self.api_key:
            try:
                self._client = RESTClient(api_key=self.api_key)
                logger.info("Massive client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Massive client: {e}")
                self._client = None
        else:
            logger.warning("MASSIVE_API_KEY not set, Massive feed disabled")

    @property
    def is_available(self) -> bool:
        """Check if Massive feed is available."""
        return self._client is not None

    @rate_limiter.rate_limited("massive")
    def get_bars(
        self,
        ticker: str,
        timespan: str = "day",
        from_date: str | datetime | None = None,
        to_date: str | datetime | None = None,
        limit: int = 5000,
    ) -> pd.DataFrame:
        """Fetch OHLCV bars for a single ticker.
        
        Args:
            ticker: Stock ticker symbol
            timespan: Bar timespan (minute, hour, day, week, month, quarter, year)
            from_date: Start date (YYYY-MM-DD string or datetime)
            to_date: End date (YYYY-MM-DD string or datetime)
            limit: Max bars to return (up to 50000)
            
        Returns:
            DataFrame with columns: open, high, low, close, volume, vwap, timestamp
        """
        if not self._client:
            logger.warning("Massive client not available")
            return pd.DataFrame()
        
        # Default to last year if no dates provided
        if to_date is None:
            to_date = datetime.now()
        if from_date is None:
            from_date = datetime.now() - timedelta(days=365)
            
        # Convert to strings if datetime
        if isinstance(from_date, datetime):
            from_date = from_date.strftime("%Y-%m-%d")
        if isinstance(to_date, datetime):
            to_date = to_date.strftime("%Y-%m-%d")
            
        try:
            aggs = list(self._client.list_aggs(
                ticker=ticker,
                multiplier=1,
                timespan=timespan,
                from_=from_date,
                to=to_date,
                limit=limit,
            ))
            
            if not aggs:
                logger.warning(f"No bars returned for {ticker}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for agg in aggs:
                data.append({
                    "timestamp": pd.to_datetime(agg.timestamp, unit="ms"),
                    "open": agg.open,
                    "high": agg.high,
                    "low": agg.low,
                    "close": agg.close,
                    "volume": agg.volume,
                    "vwap": agg.vwap,
                    "transactions": agg.transactions,
                })
            
            df = pd.DataFrame(data)
            df = df.set_index("timestamp")
            df = df.sort_index()
            
            logger.info(f"Fetched {len(df)} bars for {ticker} from Massive")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching bars from Massive for {ticker}: {e}")
            return pd.DataFrame()

    @rate_limiter.rate_limited("massive")
    def get_bars_multi(
        self,
        tickers: list[str],
        timespan: str = "day",
        from_date: str | datetime | None = None,
        to_date: str | datetime | None = None,
        limit: int = 5000,
    ) -> dict[str, pd.DataFrame]:
        """Fetch OHLCV bars for multiple tickers.
        
        Note: Makes one API call per ticker due to Massive API design.
        
        Args:
            tickers: List of stock ticker symbols
            timespan: Bar timespan
            from_date: Start date
            to_date: End date
            limit: Max bars per ticker
            
        Returns:
            Dict mapping ticker -> DataFrame
        """
        results = {}
        for ticker in tickers:
            df = self.get_bars(ticker, timespan, from_date, to_date, limit)
            if not df.empty:
                results[ticker] = df
        return results

    @rate_limiter.rate_limited("massive")
    def get_previous_close(self, ticker: str) -> dict[str, Any] | None:
        """Get previous day's close data.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with open, high, low, close, volume, vwap, or None
        """
        if not self._client:
            return None
            
        try:
            result = self._client.get_previous_close_agg(ticker)
            if result and len(result) > 0:
                agg = result[0]
                return {
                    "open": agg.open,
                    "high": agg.high,
                    "low": agg.low,
                    "close": agg.close,
                    "volume": agg.volume,
                    "vwap": agg.vwap,
                    "timestamp": pd.to_datetime(agg.timestamp, unit="ms"),
                }
        except Exception as e:
            logger.error(f"Error fetching previous close for {ticker}: {e}")
        return None

    @rate_limiter.rate_limited("massive")
    def get_snapshot(self, ticker: str) -> dict[str, Any] | None:
        """Get current snapshot (quote + day bars).
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with current price, day change, volume, etc.
        """
        if not self._client:
            return None
            
        try:
            snap = self._client.get_snapshot_ticker("stocks", ticker)
            if snap:
                return {
                    "ticker": snap.ticker,
                    "price": snap.day.close if snap.day else None,
                    "open": snap.day.open if snap.day else None,
                    "high": snap.day.high if snap.day else None,
                    "low": snap.day.low if snap.day else None,
                    "volume": snap.day.volume if snap.day else None,
                    "vwap": snap.day.vwap if snap.day else None,
                    "prev_close": snap.prev_day.close if snap.prev_day else None,
                    "change": (snap.day.close - snap.prev_day.close) if snap.day and snap.prev_day else None,
                    "change_percent": snap.todays_change_percent,
                    "updated": snap.updated,
                }
        except Exception as e:
            logger.error(f"Error fetching snapshot for {ticker}: {e}")
        return None

    def calculate_sma(
        self,
        ticker: str,
        periods: list[int] = [5, 10, 20, 50, 200],
        timespan: str = "day",
    ) -> dict[str, float | None]:
        """Calculate Simple Moving Averages for a ticker.
        
        This is the PRIMARY use case for Massive — cleaner OHLCV data.
        
        Args:
            ticker: Stock ticker symbol
            periods: List of MA periods to calculate
            timespan: Bar timespan
            
        Returns:
            Dict mapping period -> SMA value (e.g., {5: 150.23, 10: 149.87, ...})
        """
        max_period = max(periods)
        # Fetch enough data for longest MA (add buffer for weekends/holidays)
        from_date = datetime.now() - timedelta(days=max_period * 2)
        
        df = self.get_bars(ticker, timespan, from_date, datetime.now())
        
        if df.empty:
            return {p: None for p in periods}
        
        results = {}
        for period in periods:
            if len(df) >= period:
                results[period] = df["close"].rolling(window=period).mean().iloc[-1]
            else:
                results[period] = None
                
        return results

    def calculate_ema(
        self,
        ticker: str,
        periods: list[int] = [12, 26, 50, 200],
        timespan: str = "day",
    ) -> dict[str, float | None]:
        """Calculate Exponential Moving Averages for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            periods: List of EMA periods to calculate
            timespan: Bar timespan
            
        Returns:
            Dict mapping period -> EMA value
        """
        max_period = max(periods)
        from_date = datetime.now() - timedelta(days=max_period * 3)
        
        df = self.get_bars(ticker, timespan, from_date, datetime.now())
        
        if df.empty:
            return {p: None for p in periods}
        
        results = {}
        for period in periods:
            if len(df) >= period:
                results[period] = df["close"].ewm(span=period, adjust=False).mean().iloc[-1]
            else:
                results[period] = None
                
        return results

    def get_ma_matrix(
        self,
        tickers: list[str],
        sma_periods: list[int] = [5, 10, 20, 50, 200],
        ema_periods: list[int] = [12, 26],
    ) -> dict[str, dict[str, dict[str, float | None]]]:
        """Get full Moving Average matrix for multiple tickers.
        
        This is the KEY function for technical analysis integration.
        
        Args:
            tickers: List of stock tickers
            sma_periods: SMA periods to calculate
            ema_periods: EMA periods to calculate
            
        Returns:
            Nested dict: {ticker: {"sma": {period: value}, "ema": {period: value}}}
        """
        results = {}
        for ticker in tickers:
            results[ticker] = {
                "sma": self.calculate_sma(ticker, sma_periods),
                "ema": self.calculate_ema(ticker, ema_periods),
            }
        return results

    @rate_limiter.rate_limited("massive")
    def get_ticker_news(
        self,
        ticker: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get recent news articles for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            limit: Max number of articles
            
        Returns:
            List of news article dicts
        """
        if not self._client:
            return []
            
        try:
            news = list(self._client.list_ticker_news(ticker, limit=limit))
            return [
                {
                    "id": item.id,
                    "title": item.title,
                    "author": item.author,
                    "published_utc": item.published_utc,
                    "article_url": item.article_url,
                    "tickers": item.tickers,
                    "description": getattr(item, "description", None),
                    "keywords": getattr(item, "keywords", []),
                }
                for item in news
            ]
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return []


def create_massive_feed(api_key: str | None = None) -> MassiveFeed:
    """Factory function to create a MassiveFeed instance.
    
    Args:
        api_key: Optional API key. Reads from MASSIVE_API_KEY env var if not provided.
        
    Returns:
        Configured MassiveFeed instance
    """
    return MassiveFeed(api_key=api_key)


# Module-level convenience instance
_feed: MassiveFeed | None = None


def get_massive_feed() -> MassiveFeed:
    """Get or create the global MassiveFeed instance."""
    global _feed
    if _feed is None:
        _feed = create_massive_feed()
    return _feed
