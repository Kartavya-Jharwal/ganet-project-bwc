"""yfinance fallback spider — scrapes price and fundamental data.

Tertiary fallback for price data (behind Alpaca and direct yfinance API).
Also scrapes fundamental ratios not available via Alpaca.
Results pushed to Appwrite via AppwritePipeline.
"""

from __future__ import annotations

import scrapy


class YfinanceSpider(scrapy.Spider):
    name = "yfinance_fallback"

    def start_requests(self):
        """Fetch price and fundamental data for all tickers via yfinance."""
        # TODO Phase 1: Use yfinance library within spider to fetch data
        # This runs on Scrapy Cloud, so yfinance is a dep of the spider project
        yield from []

    def parse(self, response):
        """Parse yfinance data and yield Price + Fundamental items."""
        # TODO Phase 1: Yield PriceItem and FundamentalItem per ticker
        pass
