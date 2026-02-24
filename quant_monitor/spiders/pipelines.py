"""Scrapy item pipelines — push scraped data to Appwrite."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class AppwritePipeline:
    """Push scraped items to Appwrite database via REST API."""

    def open_spider(self, spider):
        """Initialize Appwrite client when spider starts."""
        # TODO Phase 1: Initialize Appwrite client
        pass

    def process_item(self, item, spider):
        """Write item to Appwrite scraped_data collection."""
        # TODO Phase 1: Serialize item and write to Appwrite
        return item

    def close_spider(self, spider):
        """Cleanup when spider finishes."""
        pass
