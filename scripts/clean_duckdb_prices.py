"""Remove legacy tickers and fix SPY duplicate-scale rows in eod_price_matrix."""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import duckdb

from quant_monitor.config import cfg

LEGACY = ("AAPL", "MSFT", "QQQ")
# Old SPY proxy rows used a different scale (~0.7) vs yfinance (~500+)
SPY_SCALE_CUTOFF = 50.0


def main() -> None:
    conn = duckdb.connect("portfolio.duckdb", read_only=False)
    try:
        before = conn.execute("SELECT COUNT(*) FROM eod_price_matrix").fetchone()[0]

        conn.execute(
            "DELETE FROM eod_price_matrix WHERE ticker IN (SELECT UNNEST(?))",
            [list(LEGACY)],
        )
        conn.execute(
            "DELETE FROM eod_price_matrix WHERE ticker = 'SPY' AND close < ?",
            [SPY_SCALE_CUTOFF],
        )

        # Keep only configured holdings (+ SPY already in holdings)
        conn.execute(
            "DELETE FROM eod_price_matrix WHERE ticker NOT IN (SELECT UNNEST(?))",
            [cfg.tickers],
        )

        after = conn.execute("SELECT COUNT(*) FROM eod_price_matrix").fetchone()[0]
        tickers = conn.execute(
            "SELECT ticker, COUNT(*) n, MIN(timestamp), MAX(timestamp) FROM eod_price_matrix GROUP BY 1 ORDER BY 1"
        ).fetchdf()
    finally:
        conn.close()

    print(f"Rows: {before:,} -> {after:,}")
    print(tickers.to_string(index=False))


if __name__ == "__main__":
    main()
