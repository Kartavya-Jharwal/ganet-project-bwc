"""Scrapy item definitions for all spiders.

Items are serialized and pushed to Appwrite via the pipeline.
"""

from __future__ import annotations

import scrapy


class NewsItem(scrapy.Item):
    """News headline item from Google RSS or Alpaca."""

    source = scrapy.Field()  # "google_rss" | "alpaca"
    ticker = scrapy.Field()  # matched ticker symbol
    headline = scrapy.Field()  # article title
    url = scrapy.Field()  # article URL
    published_at = scrapy.Field()  # ISO 8601 timestamp
    snippet = scrapy.Field()  # article summary if available


class FilingItem(scrapy.Item):
    """SEC EDGAR filing item."""

    ticker = scrapy.Field()  # matched ticker symbol
    filing_type = scrapy.Field()  # "8-K" | "10-Q" | "10-K"
    title = scrapy.Field()  # filing title
    url = scrapy.Field()  # EDGAR URL
    filed_at = scrapy.Field()  # filing date
    accession_number = scrapy.Field()


class PriceItem(scrapy.Item):
    """Price data item (yfinance fallback)."""

    ticker = scrapy.Field()
    date = scrapy.Field()  # trading date
    open = scrapy.Field()
    high = scrapy.Field()
    low = scrapy.Field()
    close = scrapy.Field()
    volume = scrapy.Field()
    source = scrapy.Field()  # "yfinance"


class FundamentalItem(scrapy.Item):
    """Fundamental data item (yfinance fallback)."""

    ticker = scrapy.Field()
    pe_ratio = scrapy.Field()
    ps_ratio = scrapy.Field()
    ev_ebitda = scrapy.Field()
    market_cap = scrapy.Field()
    beta = scrapy.Field()
    fetched_at = scrapy.Field()
