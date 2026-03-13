"""Tests for Scrapy spiders and AppwritePipeline — Phase 10."""

from __future__ import annotations

from unittest.mock import MagicMock


class TestAppwritePipeline:
    """Tests for quant_monitor/spiders/pipelines.py."""

    def test_open_spider_initializes_client(self):
        from quant_monitor.spiders.pipelines import AppwritePipeline

        pipeline = AppwritePipeline()
        mock_spider = MagicMock(name="google_rss")
        pipeline.open_spider(mock_spider)
        assert pipeline._count == 0

    def test_process_item_adds_metadata(self):
        from quant_monitor.spiders.items import NewsItem
        from quant_monitor.spiders.pipelines import AppwritePipeline

        pipeline = AppwritePipeline()
        pipeline._client = MagicMock()
        pipeline._count = 0

        item = NewsItem(
            source="google_rss",
            ticker="AAPL",
            headline="Test headline",
            url="https://example.com",
            published_at="2026-02-25T10:00:00Z",
            snippet="Test snippet",
        )

        mock_spider = MagicMock()
        mock_spider.name = "google_rss"
        result = pipeline.process_item(item, mock_spider)

        assert result is item
        pipeline._client.write_document.assert_called_once()
        call_args = pipeline._client.write_document.call_args
        data = call_args[0][1]
        assert data["source_spider"] == "google_rss"
        assert data["item_type"] == "NewsItem"
        assert "scraped_at" in data

    def test_process_item_no_client_returns_item(self):
        from quant_monitor.spiders.items import PriceItem
        from quant_monitor.spiders.pipelines import AppwritePipeline

        pipeline = AppwritePipeline()
        pipeline._client = None
        pipeline._count = 0

        item = PriceItem(ticker="SPY", date="2026-02-25", open=500, high=505,
                         low=498, close=503, volume=1000000, source="yfinance")
        mock_spider = MagicMock()
        result = pipeline.process_item(item, mock_spider)
        assert result is item  # passes through without error


class TestSpiderItems:
    """Tests for quant_monitor/spiders/items.py."""

    def test_news_item_fields(self):
        from quant_monitor.spiders.items import NewsItem

        item = NewsItem()
        item["ticker"] = "TSM"
        item["headline"] = "Test"
        assert item["ticker"] == "TSM"

    def test_filing_item_fields(self):
        from quant_monitor.spiders.items import FilingItem

        item = FilingItem()
        item["ticker"] = "AMZN"
        item["filing_type"] = "8-K"
        assert item["filing_type"] == "8-K"

    def test_fundamental_item_fields(self):
        from quant_monitor.spiders.items import FundamentalItem

        item = FundamentalItem()
        item["ticker"] = "GOOGL"
        item["pe_ratio"] = 25.5
        assert item["pe_ratio"] == 25.5


class TestGoogleRssSpider:
    """Tests for GoogleRssSpider start_requests."""

    def test_start_requests_generates_urls(self):
        from quant_monitor.spiders.google_rss_spider import GoogleRssSpider

        spider = GoogleRssSpider()
        requests = list(spider.start_requests())
        assert len(requests) > 0
        assert all("news.google.com/rss" in r.url for r in requests)


class TestSecEdgarSpider:
    """Tests for SecEdgarSpider start_requests."""

    def test_start_requests_generates_urls_for_known_ciks(self):
        from quant_monitor.spiders.sec_edgar_spider import SecEdgarSpider

        spider = SecEdgarSpider()
        requests = list(spider.start_requests())
        # Should have requests for tickers with known CIKs
        assert len(requests) > 0
        assert all("efts.sec.gov" in r.url for r in requests)