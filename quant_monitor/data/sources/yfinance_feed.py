"""yfinance data feed — primary source for price data.

Replaces Alpaca API (not available due to geographic restrictions).
Uses yfinance for OHLCV data and basic fundamentals.

Rate limited internally to avoid being blocked.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pandas as pd
import yfinance as yf

from quant_monitor.data.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


class YFinanceFeed:
    """yfinance data feed with rate limiting."""

    def __init__(self) -> None:
        """Initialize yfinance feed."""
        self._cache: dict[str, tuple[datetime, Any]] = {}

    @rate_limiter.rate_limited("yfinance")
    def get_bars(
        self,
        tickers: list[str],
        period: str = "1y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Fetch OHLCV bars for multiple tickers.

        Args:
            tickers: List of ticker symbols
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max)
            interval: Bar interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            DataFrame with MultiIndex (ticker, date) and OHLCV columns
        """
        logger.debug(f"Fetching bars for {len(tickers)} tickers, period={period}")

        try:
            # yfinance downloads multiple tickers efficiently
            data = yf.download(
                tickers=tickers,
                period=period,
                interval=interval,
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True,
            )

            if data.empty:
                logger.warning("No data returned from yfinance")
                return pd.DataFrame()

            # Reshape to MultiIndex format
            frames = []
            for ticker in tickers:
                if len(tickers) == 1:
                    ticker_data = data.copy()
                else:
                    if ticker not in data.columns.get_level_values(0):
                        logger.warning(f"No data for {ticker}")
                        continue
                    ticker_data = data[ticker].copy()

                ticker_data = ticker_data.dropna(how="all")
                if ticker_data.empty:
                    continue

                # Handle column names - may be tuples like ('AAPL', 'Close') or strings
                new_cols = []
                for c in ticker_data.columns:
                    if isinstance(c, tuple):
                        # Extract actual column name (e.g., 'Close' from ('AAPL', 'Close'))
                        new_cols.append(c[1].lower() if len(c) > 1 else c[0].lower())
                    else:
                        new_cols.append(str(c).lower())
                ticker_data.columns = new_cols
                ticker_data["ticker"] = ticker
                frames.append(ticker_data)

            if not frames:
                return pd.DataFrame()

            result = pd.concat(frames)
            result = result.reset_index()
            result = result.rename(columns={"Date": "date", "Datetime": "date"})
            result = result.set_index(["ticker", "date"])
            result = result.sort_index()

            logger.info(f"Fetched {len(result)} bars for {len(tickers)} tickers")
            return result

        except Exception as e:
            logger.error(f"Error fetching bars: {e}")
            return pd.DataFrame()

    @rate_limiter.rate_limited("yfinance")
    def get_latest_price(self, ticker: str) -> dict[str, float] | None:
        """Get latest price for a single ticker.

        Args:
            ticker: Ticker symbol

        Returns:
            Dict with price, change, change_percent, volume, or None if failed
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.fast_info

            return {
                "price": info.last_price,
                "previous_close": info.previous_close,
                "change": info.last_price - info.previous_close,
                "change_percent": (info.last_price / info.previous_close - 1) * 100,
                "volume": info.last_volume,
                "market_cap": info.market_cap,
            }
        except Exception as e:
            logger.error(f"Error fetching price for {ticker}: {e}")
            return None

    def get_latest_prices(self, tickers: list[str]) -> dict[str, dict[str, float]]:
        """Get latest prices for multiple tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dict mapping ticker to price info
        """
        results = {}
        for ticker in tickers:
            price = self.get_latest_price(ticker)
            if price:
                results[ticker] = price
        return results

    @rate_limiter.rate_limited("yfinance")
    def get_info(self, ticker: str) -> dict[str, Any] | None:
        """Get detailed info/fundamentals for a ticker.

        Args:
            ticker: Ticker symbol

        Returns:
            Dict with company info and fundamentals
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract key fields
            return {
                "name": info.get("shortName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "ps_ratio": info.get("priceToSalesTrailing12Months"),
                "pb_ratio": info.get("priceToBook"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "avg_volume": info.get("averageVolume"),
                "revenue": info.get("totalRevenue"),
                "profit_margin": info.get("profitMargins"),
            }
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {e}")
            return None

    @rate_limiter.rate_limited("yfinance")
    def get_news(self, ticker: str, max_items: int = 10) -> list[dict[str, Any]]:
        """Get news headlines for a ticker.

        Args:
            ticker: Ticker symbol
            max_items: Maximum news items to return

        Returns:
            List of news items with title, link, publisher, timestamp
        """
        try:
            stock = yf.Ticker(ticker)
            news = stock.news or []

            results = []
            for item in news[:max_items]:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "publisher": item.get("publisher", ""),
                        "timestamp": datetime.fromtimestamp(
                            item.get("providerPublishTime", 0)
                        ),
                        "type": item.get("type", ""),
                        "ticker": ticker,
                    }
                )

            return results
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return []

    def get_all_news(
        self, tickers: list[str], max_per_ticker: int = 5
    ) -> list[dict[str, Any]]:
        """Get news for multiple tickers.

        Args:
            tickers: List of ticker symbols
            max_per_ticker: Max news items per ticker

        Returns:
            Combined list of news items, sorted by timestamp descending
        """
        all_news = []
        for ticker in tickers:
            news = self.get_news(ticker, max_per_ticker)
            all_news.extend(news)

        # Sort by timestamp descending
        all_news.sort(key=lambda x: x["timestamp"], reverse=True)
        return all_news

    def is_market_open(self) -> bool:
        """Check if US market is currently open.

        Returns:
            True if market is open (approximate, doesn't account for holidays)
        """
        now = datetime.now()
        # US market hours: 9:30 AM - 4:00 PM ET
        # Approximate: assume UTC-5
        # This is a rough check - for production, use proper market calendar
        if now.weekday() >= 5:  # Weekend
            return False

        hour = now.hour
        # Rough approximation for different timezones
        # Should use pytz for proper timezone handling in production
        return 14 <= hour <= 21  # Very rough UTC approximation


# Singleton instance
yfinance_feed = YFinanceFeed()
