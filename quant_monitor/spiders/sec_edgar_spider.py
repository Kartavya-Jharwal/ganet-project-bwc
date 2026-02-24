"""SEC EDGAR RSS spider — scrapes 8-K filings for held tickers.

Monitors SEC EDGAR RSS feed for new filings by our portfolio companies.
Results pushed to Appwrite via AppwritePipeline.
"""

from __future__ import annotations

from typing import ClassVar

import scrapy


class SecEdgarSpider(scrapy.Spider):
    name = "sec_edgar"
    allowed_domains: ClassVar[list[str]] = ["sec.gov"]

    # SEC EDGAR full-text search RSS for each ticker's CIK
    # TODO Phase 1: Map tickers to CIK numbers, build start_urls

    def start_requests(self):
        """Generate requests for each portfolio ticker's EDGAR filings."""
        # TODO Phase 1: Build EDGAR RSS URLs per ticker CIK
        # Example: https://efts.sec.gov/LATEST/search-index?q=%228-K%22&dateRange=custom&startdt=2026-02-20&forms=8-K
        yield from []

    def parse(self, response):
        """Parse EDGAR RSS feed and extract filing items."""
        # TODO Phase 1: Parse RSS XML, yield FilingItem per filing
        pass
