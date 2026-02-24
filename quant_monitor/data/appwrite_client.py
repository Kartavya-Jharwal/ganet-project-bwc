"""Appwrite client — read/write helper for the Appwrite backend.

Manages collections: portfolio_snapshots, position_snapshots, signals,
alerts, regime_history, scraped_data.

All secrets (endpoint, project ID, API key) injected via Doppler.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AppwriteClient:
    """Wrapper around Appwrite Python SDK for database operations."""

    def __init__(self) -> None:
        # TODO Phase 1: Initialize Appwrite client from cfg.secrets
        pass

    def write_document(self, collection: str, data: dict[str, Any]) -> str:
        """Write a document to the specified collection. Returns document ID."""
        # TODO Phase 1
        raise NotImplementedError

    def query_documents(
        self, collection: str, queries: list[str] | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Query documents from a collection with optional filters."""
        # TODO Phase 1
        raise NotImplementedError

    def write_batch(self, collection: str, documents: list[dict[str, Any]]) -> int:
        """Write multiple documents. Returns count written."""
        # TODO Phase 1
        raise NotImplementedError

    def ensure_collections(self) -> None:
        """Create database and collections if they don't exist (idempotent setup)."""
        # TODO Phase 1
        raise NotImplementedError
