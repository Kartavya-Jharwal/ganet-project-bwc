"""Rich CLI dashboard — 5 views for portfolio monitoring.

Views:
1. Portfolio Overview — P/L table, total value, excess return vs SPY
2. Signal Dashboard  — per-ticker signal scores, confidence, dominant model
3. Regime Monitor    — current macro regime, VIX, DXY, yield curve
4. Monte Carlo       — simulation summary statistics + ASCII histogram
5. System Health     — API feed status, last update timestamps, cache stats

Run:  doppler run -- uv run quant-dashboard [--view <name>] [--live]
"""

from __future__ import annotations

import argparse
import logging
import time
from collections.abc import Callable, Sequence

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

logger = logging.getLogger(__name__)
console = Console()

VIEWS = [
    "overview",
    "signals",
    "regime",
    "montecarlo",
    "health",
]


# ---------------------------------------------------------------------------
# View renderers — each returns a Rich renderable (Table, Panel, Group, …)
# ---------------------------------------------------------------------------

def render_portfolio_overview() -> Panel:
    """Portfolio Overview — P/L table, KPIs, sector breakdown."""
    from quant_monitor.dashboard.data_loader import (
        build_holdings_dataframe,
        load_latest_prices,
        load_portfolio_state,
    )

    state = load_portfolio_state()
    prices = load_latest_prices()
    df = build_holdings_dataframe(state["holdings"], prices)

    table = Table(
        title="Holdings",
        show_lines=True,
        header_style="bold cyan",
    )
    table.add_column("Ticker", style="bold")
    table.add_column("Name")
    table.add_column("Sector")
    table.add_column("Qty", justify="right")
    table.add_column("Avg Cost", justify="right")
    table.add_column("Current", justify="right")
    table.add_column("Mkt Value", justify="right")
    table.add_column("P/L ($)", justify="right")
    table.add_column("P/L (%)", justify="right")

    for _, row in df.iterrows():
        pnl_style = "green" if row["pnl"] >= 0 else "red"
        table.add_row(
            row["ticker"],
            row["name"],
            row["sector"],
            str(row["qty"]),
            f"${row['avg_cost']:.2f}",
            f"${row['current']:.2f}",
            f"${row['market_value']:,.0f}",
            Text(f"${row['pnl']:+,.0f}", style=pnl_style),
            Text(f"{row['pnl_pct']:+.2f}%", style=pnl_style),
        )

    total_value = df["market_value"].sum() + state["cash"]
    total_pnl = total_value - state["initial_capital"]
    total_pnl_pct = (total_pnl / state["initial_capital"]) * 100 if state["initial_capital"] else 0

    subtitle = (
        f"Value: ${total_value:,.0f}  |  "
        f"P/L: ${total_pnl:+,.0f} ({total_pnl_pct:+.2f}%)  |  "
        f"Cash: ${state['cash']:,.0f}  |  "
        f"Positions: {len(state['holdings'])}"
    )
    return Panel(table, title="[bold]Portfolio Overview[/bold]", subtitle=subtitle)


def render_signal_dashboard() -> Panel:
    """Signal Dashboard — per-ticker fused scores."""
    from quant_monitor.dashboard.data_loader import (
        load_portfolio_state,
        load_signals_from_appwrite,
    )

    signals = load_signals_from_appwrite()
    state = load_portfolio_state()

    table = Table(title="Latest Signals", show_lines=True, header_style="bold magenta")
    columns = ["Ticker", "Technical", "Fundamental", "Sentiment", "Macro", "Fused", "Confidence", "Action", "Regime"]
    for col in columns:
        justify = "right" if col not in ("Ticker", "Action", "Regime") else "left"
        table.add_column(col, justify=justify)

    if not signals:
        for ticker in state["tickers"]:
            table.add_row(ticker, *["—"] * 8)
        return Panel(table, title="[bold]Signal Dashboard[/bold]", subtitle="No signals yet — run signal cycle first")

    import pandas as pd

    df = pd.DataFrame(signals)
    if "ticker" in df.columns and "timestamp" in df.columns:
        latest = df.sort_values("timestamp").groupby("ticker").last().reset_index()
    else:
        latest = df

    for _, row in latest.iterrows():
        action = str(row.get("action", "HOLD"))
        action_style = {"BUY": "green", "SELL": "red", "HOLD": "yellow"}.get(action, "white")

        table.add_row(
            str(row.get("ticker", "")),
            f"{row.get('technical_score', 0):.3f}",
            f"{row.get('fundamental_score', 0):.3f}",
            f"{row.get('sentiment_score', 0):.3f}",
            f"{row.get('macro_score', 0):.3f}",
            f"{row.get('fused_score', 0):.3f}",
            f"{row.get('confidence', 0):.2f}",
            Text(action, style=action_style),
            str(row.get("regime", "")),
        )

    return Panel(table, title="[bold]Signal Dashboard[/bold]")


def render_regime_monitor() -> Panel:
    """Regime Monitor — macro indicators + regime classification."""
    from quant_monitor.dashboard.data_loader import load_macro_snapshot

    macro = load_macro_snapshot()

    table = Table(title="Macro Indicators", show_lines=True, header_style="bold blue")
    table.add_column("Indicator", style="bold")
    table.add_column("Value", justify="right")
    table.add_column("Status")

    vix = macro.get("vix")
    dxy = macro.get("dxy")
    yield_10y = macro.get("yield_10y")
    yield_2y = macro.get("yield_2y")

    if isinstance(vix, (int, float)):
        vix_style = "red" if vix > 25 else ("yellow" if vix > 18 else "green")
        table.add_row("VIX", f"{vix:.2f}", Text("Elevated" if vix > 25 else "Normal", style=vix_style))
    else:
        table.add_row("VIX", "N/A", "—")

    if isinstance(dxy, (int, float)):
        table.add_row("DXY", f"{dxy:.2f}", "—")
    else:
        table.add_row("DXY", "N/A", "—")

    if isinstance(yield_10y, (int, float)):
        table.add_row("10Y Yield", f"{yield_10y:.2f}%", "—")
    else:
        table.add_row("10Y Yield", "N/A", "—")

    if isinstance(yield_2y, (int, float)):
        table.add_row("2Y Yield", f"{yield_2y:.2f}%", "—")
    else:
        table.add_row("2Y Yield", "N/A", "—")

    # Yield curve spread
    if isinstance(yield_10y, (int, float)) and isinstance(yield_2y, (int, float)):
        spread = yield_10y - yield_2y
        spread_style = "red bold" if spread < 0 else ("yellow" if spread < 0.5 else "green")
        spread_status = "INVERTED" if spread < 0 else ("Flattening" if spread < 0.5 else "Normal")
        table.add_row("Spread (10Y-2Y)", f"{spread:.2f}%", Text(spread_status, style=spread_style))

    # Regime classification
    regime_text = "Unknown"
    try:
        from quant_monitor.models.macro import MacroModel

        model = MacroModel()
        regime_text = model.classify_regime(macro)
    except Exception as e:
        logger.warning("Could not classify regime: %s", e)

    return Panel(table, title="[bold]Regime Monitor[/bold]", subtitle=f"Regime: {regime_text}")


def render_monte_carlo() -> Panel:
    """Monte Carlo — 10k-path simulation summary with ASCII percentile bars."""
    import numpy as np

    from quant_monitor.config import cfg

    initial_value = cfg.initial_capital
    n_sims = 10_000
    annual_return = 0.08
    annual_vol = 0.18

    from datetime import date

    valuation = date.fromisoformat(cfg.valuation_date)
    trading_days = max(1, int((valuation - date.today()).days * 252 / 365))

    daily_ret = annual_return / 252
    daily_vol = annual_vol / np.sqrt(252)

    terminal = initial_value * np.exp(
        np.cumsum(
            np.random.normal(daily_ret, daily_vol, (n_sims, trading_days)),
            axis=1,
        )[:, -1]
    )

    percentiles = [5, 25, 50, 75, 95]
    pct_vals = {p: float(np.percentile(terminal, p)) for p in percentiles}

    table = Table(title=f"Monte Carlo ({n_sims:,} paths, {trading_days} days)", show_lines=True, header_style="bold green")
    table.add_column("Scenario", style="bold")
    table.add_column("Terminal Value", justify="right")
    table.add_column("Return", justify="right")
    table.add_column("Bar")

    labels = {5: "Worst 5%", 25: "25th pctile", 50: "Median", 75: "75th pctile", 95: "Best 5%"}
    max_val = pct_vals[95]
    for p in percentiles:
        val = pct_vals[p]
        ret_pct = (val / initial_value - 1) * 100
        bar_len = int((val / max_val) * 30) if max_val > 0 else 0
        bar_style = "green" if ret_pct >= 0 else "red"
        table.add_row(
            labels[p],
            f"${val:,.0f}",
            Text(f"{ret_pct:+.1f}%", style=bar_style),
            Text("█" * bar_len, style=bar_style),
        )

    prob_loss = float((terminal < initial_value).mean() * 100)
    return Panel(table, title="[bold]Monte Carlo Simulation[/bold]", subtitle=f"P(loss): {prob_loss:.1f}%")


def render_system_health() -> Panel:
    """System Health — feed status, config overview, cache info."""
    from quant_monitor.config import cfg

    table = Table(title="System Health", show_lines=True, header_style="bold yellow")
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Detail")

    # Data feeds
    feeds = {
        "Massive/Polygon": cfg.secrets.MASSIVE_API_KEY,
        "FRED": cfg.secrets.FRED_API_KEY,
        "Appwrite": cfg.secrets.APPWRITE_API_KEY,
        "Telegram": cfg.secrets.TELEGRAM_BOT_TOKEN,
        "SEC EDGAR": cfg.secrets.SEC_EDGAR_USER_AGENT,
        "Zyte/Scrapy": cfg.secrets.ZYTE_API_KEY,
    }
    for name, key in feeds.items():
        ok = bool(key)
        table.add_row(name, Text("OK" if ok else "MISSING", style="green" if ok else "red"), "API key configured" if ok else "Set in Doppler")

    # Config
    table.add_row("Tickers", "INFO", ", ".join(cfg.tickers))
    table.add_row("Benchmark", "INFO", cfg.benchmark)
    table.add_row("Rebalance", "INFO", f"{cfg.project.get('rebalance_interval_minutes', 15)} min")

    # Cache
    try:
        from quant_monitor.data.cache import get_cache

        cache = get_cache()
        size = len(cache) if hasattr(cache, "__len__") else "N/A"
        table.add_row("Cache", Text("OK", style="green"), f"{size} entries")
    except Exception as e:
        table.add_row("Cache", Text("ERR", style="red"), str(e))

    return Panel(table, title="[bold]System Health[/bold]")


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------

VIEW_RENDERERS = {
    "overview": render_portfolio_overview,
    "signals": render_signal_dashboard,
    "regime": render_regime_monitor,
    "montecarlo": render_monte_carlo,
    "health": render_system_health,
}


def _run_cold_start_probe(include_openbb: bool = False) -> None:
    """Run lightweight startup checks with progress feedback for CLI users."""
    from quant_monitor.dashboard.data_loader import (
        load_latest_prices,
        load_macro_snapshot,
        load_portfolio_state,
        load_signals_from_appwrite,
    )

    checks: list[tuple[str, Callable[[], object]]] = [
        ("Loading portfolio config", load_portfolio_state),
        ("Fetching latest prices", load_latest_prices),
        ("Fetching macro snapshot", load_macro_snapshot),
        ("Checking signals backend", load_signals_from_appwrite),
    ]

    if include_openbb:
        checks.append(("Validating OpenBB import", lambda: __import__("openbb")))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        for description, fn in checks:
            task = progress.add_task(description, total=None)
            try:
                fn()
                progress.update(task, completed=True, description=f"{description} [green]OK[/green]")
            except Exception as e:  # pragma: no cover - network/env dependent
                progress.update(task, completed=True, description=f"{description} [yellow]DEGRADED[/yellow]")
                logger.warning("Startup probe failed for '%s': %s", description, e)


def _build_full_layout() -> Layout:
    """Build a Rich Layout with all views stacked vertically."""
    layout = Layout()
    layout.split_column(
        Layout(name="overview", ratio=2),
        Layout(name="signals", ratio=2),
        Layout(name="bottom", ratio=1),
    )
    layout["bottom"].split_row(
        Layout(name="regime"),
        Layout(name="health"),
    )
    return layout


def run_single(view: str | None) -> None:
    """Print one or all views to the console and exit."""
    if view and view in VIEW_RENDERERS:
        console.print(VIEW_RENDERERS[view]())
    else:
        for renderer in VIEW_RENDERERS.values():
            console.print(renderer())
            console.print()


def run_live(view: str | None, refresh: int = 60) -> None:
    """Refresh view(s) every *refresh* seconds using Rich Live."""
    console.print(f"[bold]Live mode[/bold] — refreshing every {refresh}s (Ctrl+C to quit)\n")
    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                if view and view in VIEW_RENDERERS:
                    live.update(VIEW_RENDERERS[view]())
                else:
                    # Stack all panels
                    from rich.console import Group

                    panels = [renderer() for renderer in VIEW_RENDERERS.values()]
                    live.update(Group(*panels))
                time.sleep(refresh)
    except KeyboardInterrupt:
        console.print("\n[dim]Dashboard stopped.[/dim]")


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point for quant-dashboard."""
    parser = argparse.ArgumentParser(
        prog="quant-dashboard",
        description="Quant Portfolio Monitor — Rich CLI Dashboard",
    )
    parser.add_argument(
        "--view",
        choices=VIEWS,
        default=None,
        help="Show a single view instead of all views. Choices: %(choices)s",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Enable auto-refresh mode (updates every --interval seconds).",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Refresh interval in seconds for --live mode (default: 60).",
    )
    parser.add_argument(
        "--openbb",
        action="store_true",
        help="Show additional OpenBB-powered views (economic calendar, earnings).",
    )
    args = parser.parse_args(argv)

    _run_cold_start_probe(include_openbb=bool(args.openbb))

    if args.live:
        run_live(args.view, refresh=args.interval)
    else:
        run_single(args.view)

        if getattr(args, "openbb", False):
            from quant_monitor.config import cfg
            from quant_monitor.dashboard.openbb_views import (
                render_earnings_upcoming,
                render_economic_calendar,
            )

            cal = render_economic_calendar()
            if cal:
                console.print(cal)
                console.print()

            earn = render_earnings_upcoming(cfg.tickers)
            if earn:
                console.print(earn)
                console.print()


if __name__ == "__main__":
    main()
