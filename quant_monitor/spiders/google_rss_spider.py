"""Google RSS news spider — scrapes news headlines for held tickers.

Fetches Google News RSS for each portfolio ticker.
Results pushed to Appwrite via AppwritePipeline.
"""

from __future__ import annotations

import logging
from typing import ClassVar

import scrapy

from quant_monitor.spiders.items import NewsItem

logger = logging.getLogger(__name__)


class GoogleRssSpider(scrapy.Spider):
    name = "google_rss"
    allowed_domains: ClassVar[list[str]] = ["news.google.com"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from quant_monitor.config import cfg
        self._tickers = cfg.tickers
        self._holdings = cfg.holdings

    def start_requests(self):
        """Generate Google News RSS requests per ticker."""
        for ticker in self._tickers:
            name = self._holdings.get(ticker, {}).get("name", ticker)
            # Use company name for better results when available
            query = f"{name}+stock" if name != ticker else f"{ticker}+stock"
            url = (
                f"https://news.google.com/rss/search"
                f"?q={query}&hl=en-US&gl=US&ceid=US:en"
            )
            yield scrapy.Request(url, callback=self.parse, meta={"ticker": ticker})

    def parse(self, response):
        """Parse Google News RSS and extract news items."""
        ticker = response.meta["ticker"]
        items = response.xpath("//item")

        for item_node in items[:10]:  # cap at 10 per ticker
            title = item_node.xpath("title/text()").get("")
            link = item_node.xpath("link/text()").get("")
            pub_date = item_node.xpath("pubDate/text()").get("")
            description = item_node.xpath("description/text()").get("")

            if title:
                yield NewsItem(
                    source="google_rss",
                    ticker=ticker,
                    headline=title.strip(),
                    url=link.strip(),
                    published_at=pub_date.strip(),
                    snippet=description.strip()[:500] if description else "",
                )