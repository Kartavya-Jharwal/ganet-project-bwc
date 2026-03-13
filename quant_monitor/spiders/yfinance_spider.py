"""yfinance fallback spider — scrapes price and fundamental data.

Tertiary fallback for price data (behind Massive/Polygon and direct yfinance API).
Also scrapes fundamental ratios not available via Massive.
Results pushed to Appwrite via AppwritePipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime

import scrapy

from quant_monitor.spiders.items import FundamentalItem, PriceItem

logger = logging.getLogger(__name__)


class YfinanceSpider(scrapy.Spider):
    name = "yfinance_fallback"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from quant_monitor.config import cfg

        self._tickers = cfg.tickers

    def start_requests(self):
        """Fetch price and fundamental data for all tickers via yfinance.

        yfinance doesn't use HTTP requests in the normal Scrapy sense, so we
        use a dummy request to self-trigger the parse callback per ticker.
        """
        for ticker in self._tickers:
            # Dummy request — actual data fetched via yfinance lib in parse()
            yield scrapy.Request(
                f"https://finance.yahoo.com/quote/{ticker}",
                callback=self.parse,
                meta={"ticker": ticker},
                dont_filter=True,
            )

    def parse(self, response):
        """Fetch yfinance data and yield Price + Fundamental items."""
        import yfinance as yf

        ticker = response.meta["ticker"]
        logger.info("YfinanceSpider: fetching %s", ticker)

        try:
            stock = yf.Ticker(ticker)
            info = stock.info or {}

            # Fundamental item
            yield FundamentalItem(
                ticker=ticker,
                pe_ratio=info.get("trailingPE"),
                ps_ratio=info.get("priceToSalesTrailing12Months"),
                ev_ebitda=info.get("enterpriseToEbitda"),
                market_cap=info.get("marketCap"),
                beta=info.get("beta"),
                fetched_at=datetime.utcnow().isoformat(),
            )

            # Latest price item
            hist = stock.history(period="5d")
            if hist is not None and not hist.empty:
                latest = hist.iloc[-1]
                yield PriceItem(
                    ticker=ticker,
                    date=str(hist.index[-1].date()),
                    open=float(latest.get("Open", 0)),
                    high=float(latest.get("High", 0)),
                    low=float(latest.get("Low", 0)),
                    close=float(latest.get("Close", 0)),
                    volume=int(latest.get("Volume", 0)),
                    source="yfinance",
                )
        except Exception as e:
            logger.warning("YfinanceSpider: failed for %s — %s", ticker, e)
