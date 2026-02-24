"""Google RSS news spider — scrapes news headlines for held tickers.

Fetches Google News RSS for each portfolio ticker.
Results pushed to Appwrite via AppwritePipeline.
"""

from __future__ import annotations

from typing import ClassVar

import scrapy


class GoogleRssSpider(scrapy.Spider):
    name = "google_rss"
    allowed_domains: ClassVar[list[str]] = ["news.google.com"]

    def start_requests(self):
        """Generate Google News RSS requests per ticker."""
        # TODO Phase 1: Build Google News RSS URLs per ticker
        # Example: https://news.google.com/rss/search?q=AAPL+stock&hl=en-US&gl=US&ceid=US:en
        yield from []

    def parse(self, response):
        """Parse Google News RSS and extract news items."""
        # TODO Phase 1: Parse RSS XML, yield NewsItem per headline
        pass
