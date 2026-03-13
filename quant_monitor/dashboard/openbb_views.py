"""Optional OpenBB-powered enrichment views for the CLI dashboard.

OpenBB Platform provides 100+ data endpoints. We wrap a curated subset
relevant to portfolio monitoring. All functions return Rich renderables
or None if OpenBB is unavailable.
"""

from __future__ import annotations

import logging

from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)


def _get_openbb():
    """Lazy-import OpenBB with graceful failure."""
    try:
        from openbb import obb

        return obb
    except ImportError:
        logger.info("OpenBB not installed — enrichment views disabled.")
        return None
    except Exception as e:
        logger.warning("OpenBB init error: %s", e)
        return None


def render_economic_calendar(days_ahead: int = 7) -> Panel | None:
    """Upcoming economic events from OpenBB."""
    obb = _get_openbb()
    if obb is None:
        return None

    try:
        from datetime import date, timedelta

        start = date.today()
        end = start + timedelta(days=days_ahead)
        result = obb.economy.calendar(
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            provider="fmp",
        )
        rows = result.to_df().head(15) if hasattr(result, "to_df") else []

        table = Table(
            title="Economic Calendar (next 7d)", show_lines=True, header_style="bold cyan"
        )
        table.add_column("Date")
        table.add_column("Event")
        table.add_column("Country")
        table.add_column("Impact")

        if hasattr(rows, "iterrows"):
            for _, row in rows.iterrows():
                table.add_row(
                    str(row.get("date", "")),
                    str(row.get("event", "")),
                    str(row.get("country", "")),
                    str(row.get("impact", "")),
                )
        return Panel(table, title="[bold]Economic Calendar (OpenBB)[/bold]")
    except Exception as e:
        logger.warning("OpenBB calendar error: %s", e)
        return None


def render_ticker_summary(ticker: str) -> Panel | None:
    """Quick fundamental snapshot for a single ticker via OpenBB."""
    obb = _get_openbb()
    if obb is None:
        return None

    try:
        profile = obb.equity.profile(symbol=ticker, provider="fmp")
        df = profile.to_df() if hasattr(profile, "to_df") else None
        if df is None or df.empty:
            return None

        info = df.iloc[0]
        table = Table(title=f"{ticker} Summary", show_lines=True, header_style="bold green")
        table.add_column("Field", style="bold")
        table.add_column("Value")

        fields = [
            ("Company", "company_name"),
            ("Sector", "sector"),
            ("Industry", "industry"),
            ("Market Cap", "market_cap"),
            ("Price", "price"),
            ("Beta", "beta"),
            ("52w High", "year_high"),
            ("52w Low", "year_low"),
        ]
        for label, key in fields:
            val = info.get(key, "N/A")
            if isinstance(val, float):
                val = f"{val:,.2f}"
            table.add_row(label, str(val))

        return Panel(table, title=f"[bold]{ticker} (OpenBB)[/bold]")
    except Exception as e:
        logger.warning("OpenBB profile error for %s: %s", ticker, e)
        return None


def render_earnings_upcoming(tickers: list[str]) -> Panel | None:
    """Upcoming earnings dates for portfolio tickers via OpenBB."""
    obb = _get_openbb()
    if obb is None:
        return None

    try:
        table = Table(title="Upcoming Earnings", show_lines=True, header_style="bold yellow")
        table.add_column("Ticker", style="bold")
        table.add_column("Date")
        table.add_column("EPS Est.")
        table.add_column("Revenue Est.")

        for ticker in tickers[:10]:  # limit to avoid rate limits
            try:
                result = obb.equity.estimates.consensus(symbol=ticker, provider="fmp")
                df = result.to_df() if hasattr(result, "to_df") else None
                if df is not None and not df.empty:
                    row = df.iloc[0]
                    table.add_row(
                        ticker,
                        str(row.get("date", "N/A")),
                        f"${row.get('estimated_eps', 'N/A')}",
                        f"${row.get('estimated_revenue', 'N/A')}",
                    )
            except Exception:
                table.add_row(ticker, "—", "—", "—")

        return Panel(table, title="[bold]Earnings Calendar (OpenBB)[/bold]")
    except Exception as e:
        logger.warning("OpenBB earnings error: %s", e)
        return None
