"""Sync from Appwrite to local DuckDB for local analytics and backtesting."""

from __future__ import annotations

import logging

import duckdb
import pandas as pd

from quant_monitor.data.appwrite_client import COLLECTIONS, DATABASE_ID, create_appwrite_client

logger = logging.getLogger(__name__)

DB_PATH = "portfolio.duckdb"


class DuckDBSync:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = duckdb.connect(database=self.db_path, read_only=False)
        self.appwrite = create_appwrite_client()
        self._appwrite_available = getattr(self.appwrite, "_available", False)
        self._init_schema()

    def _eod_price_matrix_has_primary_key(self) -> bool:
        try:
            row = self.conn.execute(
                """
                SELECT COUNT(*) FROM duckdb_constraints()
                WHERE table_name = 'eod_price_matrix' AND constraint_type = 'PRIMARY KEY'
                """
            ).fetchone()
            if row and row[0] > 0:
                return True
        except duckdb.Error:
            pass
        row = self.conn.execute(
            "SELECT sql FROM duckdb_tables() WHERE table_name = 'eod_price_matrix'"
        ).fetchone()
        return bool(row and row[0] and "PRIMARY KEY" in row[0].upper())

    def _ensure_eod_price_matrix_upsert_key(self) -> None:
        """Legacy DBs may have eod_price_matrix without a PK; ON CONFLICT requires one."""
        exists = self.conn.execute(
            """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'main' AND table_name = 'eod_price_matrix'
            """
        ).fetchone()
        if not exists or exists[0] == 0:
            return
        if self._eod_price_matrix_has_primary_key():
            return
        logger.info(
            "Migrating eod_price_matrix: adding PRIMARY KEY (timestamp, ticker) for upsert support"
        )
        self.conn.execute("""
            CREATE TABLE eod_price_matrix__bwc_mig (
                timestamp TIMESTAMP,
                ticker VARCHAR,
                close DOUBLE,
                PRIMARY KEY (timestamp, ticker)
            );
        """)
        self.conn.execute("""
            INSERT INTO eod_price_matrix__bwc_mig (timestamp, ticker, close)
            SELECT timestamp, ticker, close FROM (
                SELECT timestamp, ticker, close,
                    ROW_NUMBER() OVER (
                        PARTITION BY timestamp, ticker ORDER BY close NULLS LAST
                    ) AS rn
                FROM eod_price_matrix
            ) sub WHERE rn = 1;
        """)
        self.conn.execute("DROP TABLE eod_price_matrix")
        self.conn.execute("ALTER TABLE eod_price_matrix__bwc_mig RENAME TO eod_price_matrix")

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
        self._ensure_eod_price_matrix_upsert_key()
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS live_spy_proxy (
                timestamp TIMESTAMP,
                price DOUBLE,
                PRIMARY KEY (timestamp)
            );
        """)

    def sync_eod_prices(self):
        """Fetch eod_price_matrix from Appwrite and merge into DuckDB."""
        if not self._appwrite_available:
            logger.info("Appwrite unavailable -- skipping sync, using local DuckDB only.")
            return

        logger.info("Syncing eod_price_matrix from Appwrite to DuckDB...")

        # We need a query loop to get all pages, but for now we list the first max 100
        # In a real sync we would filter by `timestamp > latest_local_timestamp`

        try:
            docs = self.appwrite.query_documents(COLLECTIONS["eod_price_matrix"])
        except Exception as e:
            logger.error(f"Failed to fetch from Appwrite: {e}")
            return

        data = []
        for doc in docs:
            data.append(
                {
                    "timestamp": doc.get("timestamp"),
                    "ticker": doc.get("ticker"),
                    "close": doc.get("close"),
                }
            )

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
