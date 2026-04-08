"""SEC EDGAR RSS spider — scrapes 8-K filings for held tickers.

Monitors SEC EDGAR full-text search feed for recent filings.
Results pushed to Appwrite via AppwritePipeline.
"""

from __future__ import annotations

import logging
from typing import ClassVar

import scrapy

from quant_monitor.spiders.items import FilingItem

logger = logging.getLogger(__name__)

# CIK lookup: ticker → SEC CIK number (subset for our portfolio)
# Full mapping available at: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=&CIK=TICKER
TICKER_TO_CIK: dict[str, str] = {
    "SPY": "0000884394",
    "TSM": "0001046179",
    "MU": "0000723125",
    "PLTR": "0001321655",
    "AMZN": "0001018724",
    "GOOGL": "0001652044",
    "GE": "0000040554",
    "JPM": "0000019617",
    "LMT": "0000936468",
    "WMT": "0000104169",
    "PG": "0000080424",
    "JNJ": "0000200406",
    "IONQ": "0001820302",
    "NVDA": "0001045810",
    "ORCL": "0001341439",
    "XOM": "0000034088",
    "TGT": "0000027419",
}


class SecEdgarSpider(scrapy.Spider):
    name = "sec_edgar"
    allowed_domains: ClassVar[list[str]] = ["efts.sec.gov", "sec.gov"]
    custom_settings: ClassVar[dict] = {
        "DOWNLOAD_DELAY": 0.5,  # SEC asks for max 10 req/s
        "USER_AGENT": "QuantMonitor/1.0 (Academic Research; Hult Business School)",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from quant_monitor.config import cfg

        self._tickers = cfg.tickers

    def start_requests(self):
        """Generate requests for each portfolio ticker's EDGAR filings."""
        for ticker in self._tickers:
            cik = TICKER_TO_CIK.get(ticker)
            if not cik:
                logger.debug("No CIK for %s — skipping", ticker)
                continue

            # EDGAR full-text search API (JSON)
            url = (
                f"https://efts.sec.gov/LATEST/search-index"
                f"?q=%22{ticker}%22&forms=8-K,10-Q,10-K"
                f"&dateRange=custom&startdt=2026-01-01"
            )
            yield scrapy.Request(url, callback=self.parse, meta={"ticker": ticker, "cik": cik})

    def parse(self, response):
        """Parse EDGAR search results and extract filing items."""
        import json

        ticker = response.meta["ticker"]

        try:
            data = json.loads(response.text)
            hits = data.get("hits", {}).get("hits", [])
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Failed to parse EDGAR response for %s", ticker)
            return

        for hit in hits[:10]:
            source = hit.get("_source", {})
            filing_type = source.get("forms", [""])[0] if source.get("forms") else ""
            title = source.get("display_names", [""])[0] if source.get("display_names") else ""
            filed_at = source.get("file_date", "")
            accession = source.get("accession_no", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{response.meta['cik']}/{accession}"

            if filing_type:
                yield FilingItem(
                    ticker=ticker,
                    filing_type=filing_type,
                    title=title or f"{ticker} {filing_type}",
                    url=url,
                    filed_at=filed_at,
                    accession_number=accession,
                )
