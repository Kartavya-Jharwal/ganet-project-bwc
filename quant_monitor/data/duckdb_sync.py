
"""Sync from Appwrite to local DuckDB for local analytics and backtesting."""

from __future__ import annotations

import logging
import duckdb
import pandas as pd
from datetime import datetime

from quant_monitor.data.appwrite_client import create_appwrite_client, DATABASE_ID, COLLECTIONS

logger = logging.getLogger(__name__)

DB_PATH = "portfolio.duckdb"

class DuckDBSync:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = duckdb.connect(database=self.db_path, read_only=False)
        self.appwrite = create_appwrite_client()
        self._init_schema()

    def _init_schema(self):
        """Create tables if they do not exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS eod_price_matrix (
                timestamp TIMESTAMP,
                ticker VARCHAR,
                close DOUBLE,
                PRIMARY KEY (timestamp, ticker)
            );
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS live_spy_proxy (
                timestamp TIMESTAMP,
                price DOUBLE,
                PRIMARY KEY (timestamp)
            );
        """)

    def sync_eod_prices(self):
        """Fetch eod_price_matrix from Appwrite and merge into DuckDB."""
        logger.info("Syncing eod_price_matrix from Appwrite to DuckDB...")
        
        # We need a query loop to get all pages, but for now we list the first max 100
        # In a real sync we would filter by `timestamp > latest_local_timestamp`
        
        try:
            docs = self.appwrite._databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=COLLECTIONS["eod_price_matrix"]
            )
        except Exception as e:
            logger.error(f"Failed to fetch from Appwrite: {e}")
            return
            
        data = []
        for doc in docs.get("documents", []):
            data.append({
                "timestamp": doc.get("timestamp"),
                "ticker": doc.get("ticker"),
                "close": doc.get("close")
            })
            
        if not data:
            logger.info("No eod_price_matrix data to sync.")
            return
            
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # INSERT OR REPLACE (DuckDB uses INSERT OR IGNORE / ON CONFLICT)
        self.conn.execute("BEGIN TRANSACTION")
        self.conn.register("df_view", df)
        self.conn.execute("""
            INSERT INTO eod_price_matrix (timestamp, ticker, close)
            SELECT timestamp, ticker, close FROM df_view
            ON CONFLICT (timestamp, ticker) DO UPDATE SET
                close = EXCLUDED.close;
        """)
        self.conn.execute("COMMIT")
        logger.info(f"Synced {len(df)} records into eod_price_matrix.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync = DuckDBSync()
    sync.sync_eod_prices()

