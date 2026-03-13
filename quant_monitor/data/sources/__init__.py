"""Data source feeds.

- Massive (Polygon.io): PRIMARY for OHLCV and moving averages
- yfinance: Fallback for prices, fundamentals
- FRED: Macro indicators
- SEC EDGAR: Filings, insider transactions
- News: Google RSS and financial feeds
"""

from quant_monitor.data.sources.fred_feed import FredFeed, create_fred_feed
from quant_monitor.data.sources.massive_feed import (
    MassiveFeed,
    create_massive_feed,
    get_massive_feed,
)
from quant_monitor.data.sources.news_feed import NewsFeed, create_news_feed, get_news_feed
from quant_monitor.data.sources.sec_feed import SecEdgarFeed, create_sec_feed, get_sec_feed
from quant_monitor.data.sources.yfinance_feed import YFinanceFeed, yfinance_feed

__all__ = [
    "FredFeed",
    "MassiveFeed",
    "NewsFeed",
    "SecEdgarFeed",
    "YFinanceFeed",
    # FRED
    "create_fred_feed",
    "create_massive_feed",
    # News
    "create_news_feed",
    # SEC EDGAR
    "create_sec_feed",
    # Massive (Polygon)
    "get_massive_feed",
    "get_news_feed",
    "get_sec_feed",
    # yfinance
    "yfinance_feed",
]
