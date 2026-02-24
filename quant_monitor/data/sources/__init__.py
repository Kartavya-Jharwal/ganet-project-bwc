"""Data source feeds.

- Massive (Polygon.io): PRIMARY for OHLCV and moving averages
- yfinance: Fallback for prices, fundamentals
- FRED: Macro indicators
- SEC EDGAR: Filings, insider transactions
- News: Google RSS and financial feeds
"""

from quant_monitor.data.sources.yfinance_feed import yfinance_feed, YFinanceFeed
from quant_monitor.data.sources.massive_feed import get_massive_feed, MassiveFeed, create_massive_feed
from quant_monitor.data.sources.fred_feed import create_fred_feed, FredFeed
from quant_monitor.data.sources.sec_feed import create_sec_feed, SecEdgarFeed, get_sec_feed
from quant_monitor.data.sources.news_feed import create_news_feed, NewsFeed, get_news_feed

__all__ = [
    # yfinance
    "yfinance_feed",
    "YFinanceFeed",
    # Massive (Polygon)
    "get_massive_feed",
    "MassiveFeed",
    "create_massive_feed",
    # FRED
    "create_fred_feed",
    "FredFeed",
    # SEC EDGAR
    "create_sec_feed",
    "SecEdgarFeed",
    "get_sec_feed",
    # News
    "create_news_feed",
    "NewsFeed",
    "get_news_feed",
]
