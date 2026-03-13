"""Scrapy item pipelines — push scraped data to Appwrite."""

from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AppwritePipeline:
    """Push scraped items to Appwrite database via REST API."""

    def open_spider(self, spider):
        """Initialize Appwrite client when spider starts."""
        try:
            from quant_monitor.data.appwrite_client import create_appwrite_client

            self._client = create_appwrite_client()
            self._count = 0
            logger.info("AppwritePipeline: connected for spider %s", spider.name)
        except Exception as e:
            logger.warning("AppwritePipeline: Appwrite unavailable — %s", e)
            self._client = None
            self._count = 0

    def process_item(self, item, spider):
        """Write item to Appwrite scraped_data collection."""
        if not self._client:
            return item

        data = dict(item)
        data["source_spider"] = spider.name
        data["item_type"] = type(item).__name__
        data["scraped_at"] = datetime.utcnow().isoformat()

        try:
            # We assume a valid `write_document` on the Appwrite client
            self._client.write_document("scraped_data", data)
            self._count += 1
        except Exception as e:
            logger.warning(
                "AppwritePipeline: write failed for %s — %s",
                data.get("ticker", "?"),
                e,
            )

        return item

    def close_spider(self, spider):
        """Log stats when spider finishes."""
        logger.info(
            "AppwritePipeline: spider %s finished — %d items written to Appwrite",
            spider.name,
            getattr(self, "_count", 0),
        )
