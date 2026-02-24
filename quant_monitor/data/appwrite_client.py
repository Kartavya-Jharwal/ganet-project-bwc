"""Appwrite client — read/write helper for the Appwrite backend.

Manages collections: portfolio_snapshots, position_snapshots, signals,
alerts, regime_history, scraped_data.

All secrets (endpoint, project ID, API key) injected via Doppler.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from appwrite.client import Client
from appwrite.id import ID
from appwrite.query import Query
from appwrite.services.databases import Databases
from appwrite.exception import AppwriteException

from quant_monitor.data.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# Database ID (created by setup script)
DATABASE_ID = "quant_db"

# Collection IDs
COLLECTIONS = {
    "portfolio_snapshots": "portfolio_snapshots",
    "position_snapshots": "position_snapshots",
    "signals": "signals",
    "alerts": "alerts",
    "regime_history": "regime_history",
    "scraped_data": "scraped_data",
}


class AppwriteClient:
    """Wrapper around Appwrite Python SDK for database operations."""

    def __init__(
        self,
        endpoint: str | None = None,
        project_id: str | None = None,
        api_key: str | None = None,
    ) -> None:
        """Initialize Appwrite client.

        Args:
            endpoint: Appwrite endpoint URL
            project_id: Appwrite project ID
            api_key: Appwrite API key

        If any arg is None, reads from environment variables (Doppler).
        """
        self.endpoint = endpoint or os.environ.get("APPWRITE_ENDPOINT", "")
        self.project_id = project_id or os.environ.get("APPWRITE_PROJECT_ID", "")
        self.api_key = api_key or os.environ.get("APPWRITE_API_KEY", "")

        if not all([self.endpoint, self.project_id, self.api_key]):
            logger.warning("Appwrite credentials incomplete - some operations will fail")

        # Initialize client
        self._client = Client()
        self._client.set_endpoint(self.endpoint)
        self._client.set_project(self.project_id)
        self._client.set_key(self.api_key)

        self._databases = Databases(self._client)
        logger.info(f"Appwrite client initialized for project: {self.project_id}")

    @rate_limiter.rate_limited("appwrite")
    def write_document(
        self,
        collection: str,
        data: dict[str, Any],
        document_id: str | None = None,
    ) -> str:
        """Write a document to the specified collection.

        Args:
            collection: Collection name (e.g., 'signals')
            data: Document data
            document_id: Optional custom ID (auto-generated if None)

        Returns:
            Document ID
        """
        collection_id = COLLECTIONS.get(collection, collection)
        doc_id = document_id or ID.unique()

        try:
            result = self._databases.create_document(
                database_id=DATABASE_ID,
                collection_id=collection_id,
                document_id=doc_id,
                data=data,
            )
            logger.debug(f"Created document in {collection}: {result['$id']}")
            return result["$id"]
        except AppwriteException as e:
            logger.error(f"Error writing to {collection}: {e}")
            raise

    @rate_limiter.rate_limited("appwrite")
    def query_documents(
        self,
        collection: str,
        queries: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Query documents from a collection with optional filters.

        Args:
            collection: Collection name
            queries: List of Query strings (e.g., Query.equal("ticker", "SPY"))
            limit: Max documents to return
            offset: Pagination offset

        Returns:
            List of documents
        """
        collection_id = COLLECTIONS.get(collection, collection)

        try:
            result = self._databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=collection_id,
                queries=queries or [],
            )
            docs = result.get("documents", [])
            logger.debug(f"Queried {len(docs)} documents from {collection}")
            return docs
        except AppwriteException as e:
            logger.error(f"Error querying {collection}: {e}")
            return []

    def write_batch(
        self,
        collection: str,
        documents: list[dict[str, Any]],
    ) -> int:
        """Write multiple documents to a collection.

        Note: Appwrite doesn't have native batch write, so we iterate.

        Args:
            collection: Collection name
            documents: List of documents to write

        Returns:
            Number of successfully written documents
        """
        success_count = 0
        for doc in documents:
            try:
                self.write_document(collection, doc)
                success_count += 1
            except AppwriteException:
                continue

        logger.info(f"Batch wrote {success_count}/{len(documents)} to {collection}")
        return success_count

    def get_latest_snapshot(self) -> dict[str, Any] | None:
        """Get the most recent portfolio snapshot.

        Returns:
            Latest snapshot document or None
        """
        docs = self.query_documents(
            "portfolio_snapshots",
            queries=[Query.order_desc("timestamp"), Query.limit(1)],
        )
        return docs[0] if docs else None

    def get_latest_signals(self, ticker: str | None = None) -> list[dict[str, Any]]:
        """Get latest signals, optionally filtered by ticker.

        Args:
            ticker: Optional ticker filter

        Returns:
            List of signal documents
        """
        queries = [Query.order_desc("timestamp"), Query.limit(100)]
        if ticker:
            queries.append(Query.equal("ticker", ticker))

        return self.query_documents("signals", queries=queries)

    def write_signal(
        self,
        ticker: str,
        technical_score: float,
        fundamental_score: float,
        sentiment_score: float,
        macro_score: float,
        fused_score: float,
        confidence: float,
        action: str,
        regime: str,
        dominant_model: str | None = None,
    ) -> str:
        """Write a signal document.

        Returns:
            Document ID
        """
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": ticker,
            "technical_score": technical_score,
            "fundamental_score": fundamental_score,
            "sentiment_score": sentiment_score,
            "macro_score": macro_score,
            "fused_score": fused_score,
            "confidence": confidence,
            "action": action,
            "regime": regime,
            "dominant_model": dominant_model,
        }
        return self.write_document("signals", data)

    def write_alert(
        self,
        alert_type: str,
        message: str,
        severity: str,
        ticker: str | None = None,
        dispatched: bool = False,
    ) -> str:
        """Write an alert document.

        Returns:
            Document ID
        """
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": ticker,
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "dispatched": dispatched,
        }
        return self.write_document("alerts", data)

    def write_regime(
        self,
        regime: str,
        vix: float,
        hurst: float,
        vol_percentile: float,
    ) -> str:
        """Write a regime history entry.

        Returns:
            Document ID
        """
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "regime": regime,
            "vix": vix,
            "hurst": hurst,
            "vol_percentile": vol_percentile,
        }
        return self.write_document("regime_history", data)


def create_appwrite_client() -> AppwriteClient:
    """Create Appwrite client with credentials from environment."""
    return AppwriteClient()
