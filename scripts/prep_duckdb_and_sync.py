"""One-shot: load EOD prices into DuckDB (fast) and optionally sync Appwrite.

Default is local-only (~30s). Appwrite upload is opt-in and slow (1000s of API calls).

Usage:
    doppler run -- uv run python scripts/prep_duckdb_and_sync.py
    doppler run -- uv run python scripts/prep_duckdb_and_sync.py --upload-appwrite
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import duckdb
import pandas as pd
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from quant_monitor.config import cfg
from quant_monitor.data.duckdb_sync import DuckDBSync
from quant_monitor.data.sources.yfinance_feed import yfinance_feed

console = Console()


def _upsert_prices_to_duckdb(df: pd.DataFrame, db_path: str = "portfolio.duckdb") -> int:
    if df.empty:
        return 0

    DuckDBSync(db_path)  # ensure schema + PK exist
    flat = df.reset_index()
    if "level_0" in flat.columns:
        flat = flat.rename(columns={"level_0": "ticker", "level_1": "date"})
    price_df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(flat["date"]),
            "ticker": flat["ticker"].astype(str),
            "close": flat["close"].astype(float),
        }
    )

    conn = duckdb.connect(db_path, read_only=False)
    try:
        conn.register("price_view", price_df)
        conn.execute("BEGIN TRANSACTION")
        conn.execute(
            """
            INSERT INTO eod_price_matrix (timestamp, ticker, close)
            SELECT timestamp, ticker, close FROM price_view
            ON CONFLICT (timestamp, ticker) DO UPDATE SET close = EXCLUDED.close
            """
        )
        conn.execute("COMMIT")
    finally:
        conn.close()
    return len(price_df)


def _duckdb_summary(db_path: str = "portfolio.duckdb") -> None:
    if not Path(db_path).is_file():
        console.print("[red]DuckDB: MISSING[/red]")
        return
    conn = duckdb.connect(db_path, read_only=True)
    try:
        total = conn.execute("SELECT COUNT(*) FROM eod_price_matrix").fetchone()[0]
        tickers = conn.execute(
            """
            SELECT ticker, COUNT(*) AS n, MAX(timestamp) AS last_ts
            FROM eod_price_matrix
            GROUP BY ticker
            ORDER BY ticker
            """
        ).fetchdf()
        console.print(f"[green]DuckDB[/green]: {total:,} rows | {len(tickers)} tickers")
        console.print(tickers.to_string(index=False))
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prep portfolio.duckdb for analytics/site")
    parser.add_argument("--period", default="2y", help="yfinance period (default: 2y)")
    parser.add_argument(
        "--upload-appwrite",
        action="store_true",
        help="Also push bars to Appwrite (slow: one HTTP call per row)",
    )
    parser.add_argument(
        "--pull-appwrite",
        action="store_true",
        help="Merge latest rows from Appwrite into DuckDB after local load",
    )
    args = parser.parse_args()

    tickers = cfg.tickers
    console.print(f"[cyan]Tickers:[/cyan] {len(tickers)} | [cyan]period:[/cyan] {args.period}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        dl = progress.add_task("Downloading OHLCV (yfinance)...", total=1)
        df = yfinance_feed.get_bars(tickers, period=args.period)
        progress.update(dl, completed=1)

        if df.empty:
            console.print("[red]No price data returned — aborting.[/red]")
            raise SystemExit(1)

        n_tickers = df.index.get_level_values(0).nunique()
        progress.console.print(
            f"  [dim]→ {len(df):,} bars across {n_tickers} tickers[/dim]"
        )

        db_task = progress.add_task("Writing DuckDB matrix...", total=1)
        n_rows = _upsert_prices_to_duckdb(df)
        progress.update(db_task, completed=1)
        progress.console.print(f"  [dim]→ upserted {n_rows:,} rows[/dim]")

        if args.upload_appwrite:
            from quant_monitor.data.appwrite_client import COLLECTIONS, create_appwrite_client

            aw = create_appwrite_client()
            records = []
            for (ticker, date), row in df.iterrows():
                dt = pd.to_datetime(date)
                dt_str = dt.isoformat() + ("Z" if dt.tzinfo is None else "")
                records.append(
                    {
                        "timestamp": dt_str,
                        "ticker": str(ticker),
                        "close": float(row.get("close", 0.0)),
                    }
                )
            aw_task = progress.add_task(
                "[yellow]Uploading to Appwrite (slow)...[/yellow]",
                total=len(records),
            )
            batch_size = 50
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                aw.write_batch(COLLECTIONS["eod_price_matrix"], batch, max_workers=5)
                progress.update(aw_task, advance=len(batch))

        if args.pull_appwrite:
            pull = progress.add_task("Merging Appwrite → DuckDB...", total=1)
            sync = DuckDBSync()
            sync.sync_eod_prices()
            sync.conn.close()
            progress.update(pull, completed=1)

    console.print("\n[bold]=== DuckDB state ===[/bold]")
    _duckdb_summary()
    console.print(
        "\n[dim]Next: uv run python scripts/build_frontend_assets.py[/dim]"
    )


if __name__ == "__main__":
    main()
