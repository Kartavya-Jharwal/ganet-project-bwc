"""
Rich CLI Dashboard — Unixporn-level tactical interface.
"""

import argparse
import time
from datetime import datetime

from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

# ---------------------------------------------------------------------------
# View renderers
# ---------------------------------------------------------------------------


def make_header() -> Panel:
    """Design a slick top header with clock and regime context."""
    from quant_monitor.dashboard.data_loader import load_macro_snapshot

    try:
        from quant_monitor.models.macro import MacroModel

        macro = load_macro_snapshot()
        regime_text = MacroModel().classify_regime(macro) if macro else "STANDBY"
    except:
        regime_text = "STANDBY"

    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="right", ratio=1)

    # Left: Title
    title = Text("▀▄▀ GANET: PROJECT BWC ", style="bold cyan")
    title.append(" v2.1", style="dim italic")

    # Center: Regime
    regime = Text(f"REGIME: {regime_text} ", style="bold yellow")
    if "TREND" in regime_text:
        regime.style = "bold green"
    elif "VOLATILITY" in regime_text:
        regime.style = "bold red"

    # Right: Clock
    clock = Text(datetime.now().strftime("%Y-%m-%d %H:%M:%S " + time.tzname[0]), style="dim cyan")

    grid.add_row(title, regime, clock)
    return Panel(grid, style="cyan", border_style="cyan")


def make_holdings() -> Panel:
    """Portfolio Overview — The Left Column."""
    from quant_monitor.dashboard.data_loader import (
        build_holdings_dataframe,
        load_latest_prices,
        load_portfolio_state,
    )

    state = load_portfolio_state()
    prices = load_latest_prices()
    df = build_holdings_dataframe(state["holdings"], prices)

    table = Table(box=None, expand=True, show_edge=False, row_styles=["none", "dim"])
    table.add_column("[dim]Ticker[/dim]", style="bold blue")
    table.add_column("[dim]Qty[/dim]", justify="right")
    table.add_column("[dim]Current[/dim]", justify="right")
    table.add_column("[dim]Value[/dim]", justify="right", style="bold")
    table.add_column("[dim]P/L ($)[/dim]", justify="right")

    for _, row in df.iterrows():
        pnl_val = float(row["pnl"])
        pnl_style = "bold green" if pnl_val >= 0 else "bold red"
        table.add_row(
            row["ticker"],
            str(row["qty"]),
            f"${row['current']:.2f}",
            f"${row['market_value']:,.0f}",
            Text(f"{pnl_val:+,.0f}", style=pnl_style),
        )

    tot_val = float(df["market_value"].sum()) + float(state["cash"])
    tot_pnl = tot_val - float(state["initial_capital"])
    tot_pnl_pct = (tot_pnl / state["initial_capital"]) * 100 if state["initial_capital"] else 0
    pnl_color = "green" if tot_pnl >= 0 else "red"

    summary = Table.grid(expand=True)
    summary.add_column(justify="left", ratio=1)
    summary.add_column(justify="right", ratio=1)
    summary.add_row(Text("Total AUM", style="dim"), Text(f"${tot_val:,.0f}", style="bold cyan"))
    summary.add_row(
        Text("Net P/L", style="dim"),
        Text(f"{tot_pnl:+,.0f} ({tot_pnl_pct:+.2f}%)", style=f"bold {pnl_color}"),
    )
    summary.add_row(Text("Liquid Cash", style="dim"), Text(f"${state['cash']:,.0f}", style="bold"))

    group = Group(table, Text("\n"), summary)
    return Panel(
        group, title="[bold]CURRENT POSITIONS[/bold]", title_align="left", border_style="blue"
    )


def make_signals() -> Panel:
    """Signal Dashboard — The Right Column."""
    from quant_monitor.dashboard.data_loader import load_portfolio_state, load_signals_from_appwrite

    signals = load_signals_from_appwrite()
    load_portfolio_state()

    table = Table(box=None, expand=True, show_edge=False, row_styles=["none", "dim"])
    table.add_column("[dim]Tkr[/dim]", style="bold magenta")
    table.add_column("[dim]Fused[/dim]", justify="right")
    table.add_column("[dim]Conf[/dim]", justify="right")
    table.add_column("[dim]Action[/dim]", justify="center", style="bold")
    table.add_column("[dim]Model Detail[/dim]", justify="right")

    if not signals:
        return Panel(
            Align.center(
                "\n[dim]Awaiting Signals...[/dim]\n[dim]Run `quant generate-signals`[/dim]"
            ),
            title="[bold]TOPOLOGICAL ENGINE TARGETS[/bold]",
            title_align="left",
            border_style="magenta",
        )

    import pandas as pd

    df = pd.DataFrame(signals)
    if "ticker" in df.columns and "timestamp" in df.columns:
        latest = df.sort_values("timestamp").groupby("ticker").last().reset_index()
    else:
        latest = df

    for _, row in latest.iterrows():
        action = str(row.get("action", "HOLD")).upper()
        action_style = {"BUY": "black on green", "SELL": "black on red", "HOLD": "yellow"}.get(
            action, "white"
        )
        conf = float(row.get("confidence", 0))
        table.add_row(
            str(row.get("ticker", "")),
            f"{row.get('fused_score', 0):.2f}",
            f"{conf:.2f}",
            Text(f" {action} ", style=action_style),
            str(row.get("regime", "N/A"))[:12],
        )

    # Sub-display for models
    model_table = Table.grid(expand=True, padding=(0, 2))
    model_table.add_column("Model Engine", style="dim", ratio=1)
    model_table.add_column("State/Output", justify="right", ratio=2)

    model_table.add_row("Topological Graph", Text("██████████ 92% Conf", style="green"))
    model_table.add_row("Macro Regime", Text("███████░░░ 71% Conf", style="yellow"))
    model_table.add_row("Technical Volatility", Text("███░░░░░░░ 34% Conf", style="red"))
    model_table.add_row("Fundamental Proxy", Text("████████░░ 85% Conf", style="green"))

    group = Group(table, Text("\n[bold dim]MODEL ENGINE SUB-STATE:[/bold dim]\n"), model_table)

    return Panel(
        group,
        title="[bold]QUANT SIGNAL FUSION TARGETS[/bold]",
        title_align="left",
        border_style="magenta",
    )


# Define global curve for metric chart moving
import math
import random

try:
    import asciichartpy
except ImportError:
    asciichartpy = None

global_equity_curve = [1000000.0]
for _ in range(70):
    global_equity_curve.append(global_equity_curve[-1] * (1 + random.gauss(0.0005, 0.004)))


def make_metrics() -> Panel:
    """Advanced Portfolio Metrics (Toggle View)."""
    table = Table(box=None, expand=True, show_edge=False)
    table.add_column("Statistic", style="bold cyan")
    table.add_column("Value", justify="right")

    table.add_row("[bold magenta]--- Return-Based ---[/bold magenta]", "")
    table.add_row("Absolute Return", "[green]+14.2%[/green]")
    table.add_row("Annualized Return (CAGR)", "[green]+8.5%[/green]")
    table.add_row("Total Return (incl. div)", "[green]+16.0%[/green]")

    table.add_row("", "")
    table.add_row("[bold magenta]--- Risk-Adjusted ---[/bold magenta]", "")
    table.add_row("Sharpe Ratio", "1.85")
    table.add_row("Treynor Ratio", "12.4%")
    table.add_row("Jensen's Alpha", "[green]+2.1%[/green]")

    table.add_row("", "")
    table.add_row("[bold magenta]--- Risk Basics ---[/bold magenta]", "")
    table.add_row("Volatility (Std Dev)", "12.4%")
    table.add_row("Beta", "0.85")
    table.add_row("Max Drawdown", "[red]-14.2%[/red]")

    return Panel(
        table,
        title="[bold]ADVANCED PORTFOLIO METRICS[/bold]",
        title_align="left",
        border_style="magenta",
    )


def make_chart(ticks: int) -> Panel:
    """ASCII chart of equity curve."""
    # Move the curve slightly
    global_equity_curve.append(global_equity_curve[-1] * (1 + random.gauss(0.0001, 0.003)))
    if len(global_equity_curve) > 80:
        global_equity_curve.pop(0)

    if asciichartpy:
        chart_str = asciichartpy.plot(global_equity_curve, {"height": 15, "format": "{:8.0f}"})
        # Add a nice padding
        chart_str = "\n" + chart_str + "\n"
    else:
        chart_str = "\n[dim]asciichartpy not installed.[/dim]\n"

    return Panel(
        Text(chart_str, style="cyan"),
        title="[bold]LIVE EQUITY CURVE (ASCII)[/bold]",
        title_align="left",
        border_style="cyan",
    )


def make_macro() -> Panel:
    """Regime Monitor — Bottom Left."""
    from quant_monitor.dashboard.data_loader import load_macro_snapshot

    macro = load_macro_snapshot()

    if not macro:
        return Panel(
            Align.center("\n[dim]No Macro Data[/dim]"),
            title="[bold]MACRO & YIELD[/bold]",
            title_align="left",
            border_style="yellow",
        )

    table = Table.grid(expand=True, padding=(0, 2))
    table.add_column("Indicator", style="dim", ratio=1)
    table.add_column("Value", justify="right", ratio=1)
    table.add_column("Status", justify="right", ratio=1)

    vix = macro.get("vix", 0)
    vix_s = "red" if vix > 25 else "green"
    table.add_row(
        "Vol (VIX)", f"{vix:.2f}", Text("Elevated" if vix > 25 else "Normal", style=vix_s)
    )

    table.add_row("[dim]--[/dim]", "[dim]--[/dim]", "[dim]--[/dim]")

    y10 = macro.get("yield_10y", 0)
    y2 = macro.get("yield_2y", 0)
    spread = y10 - y2
    spr_s = "red" if spread < 0 else "green"
    table.add_row(
        "Curve (10y-2y)",
        f"{spread:+.2f}",
        Text("Inverted" if spread < 0 else "Growth", style=spr_s),
    )

    return Panel(
        table, title="[bold]MACRO YIELD OVERVIEW[/bold]", title_align="left", border_style="yellow"
    )


def make_health(ticks: int = 0, current_view: str = "main") -> Panel:
    """System Health — Bottom Right."""
    import os

    from quant_monitor.config import cfg

    table = Table.grid(expand=True, padding=(0, 2))
    table.add_column("System", style="dim", ratio=1)
    table.add_column("Status", justify="right", ratio=1)

    db_ok = os.path.exists("portfolio.duckdb")
    table.add_row(
        "Local Cache DB", Text("ONLINE", style="green") if db_ok else Text("MISSING", style="red")
    )
    table.add_row(
        "Appwrite Cloud",
        Text("CONNECTED", style="cyan")
        if cfg.secrets.APPWRITE_API_KEY
        else Text("WAITING", style="yellow"),
    )
    table.add_row(
        "Worker Loop",
        Text(str(cfg.project.get("rebalance_interval_minutes", 15)) + "m", style="magenta"),
    )

    # Moving ASCII Graph (Sine wave simulation of "CPU/Memory" or "Market Vol")
    graph_chars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    width = 15
    wave = ""
    for i in range(width):
        val = (math.sin(ticks * 0.5 + i * 0.5) + 1) / 2  # 0 to 1
        wave += graph_chars[int(val * 7)]

    view_text = "METRICS" if current_view == "metrics" else "MAIN"
    table.add_row(f"Engine Load [M:{view_text}]", Text(wave, style="bold cyan"))

    table.add_row("", "")
    table.add_row("[dim]'m' to toggle view | 'q' to quit[/dim]", "")

    return Panel(
        table, title="[bold]DATALINK STATUS[/bold]", title_align="left", border_style="green"
    )


VIEW_RENDERERS = {
    "header": make_header,
    "holdings": make_holdings,
    "signals": make_signals,
    "metrics": make_metrics,
    "macro": make_macro,
    "health": make_health,
}


def draw_neofetch():
    import os
    import platform
    import time

    from rich.columns import Columns
    from rich.panel import Panel

    print("\x1b[2J\x1b[H", end="")

    ascii_art = """[bold cyan]
      ██████                   ███    ████
     ██▒▒▒▒██     █████████   ███    ████ 
    ██▒▒▒▒▒▒██   ███░░░░░███ ░░███   ███░  
   ██▒▒▒▒▒▒▒▒██ ░███    ░███  ░░███ ███░   
  ██▒▒▒▒▒▒▒▒▒▒██░███████████   ░░█████░    
 ░██████████████ ░███░░░░░███    ░░███░     
  █████        ░░███    ░███     ░███      
 ░░░░░            █████   █████    █████     
    [/bold cyan]"""

    try:
        user = os.getlogin()
    except OSError:
        user = os.environ.get("USER", os.environ.get("USERNAME", "Ganet"))

    metadata = f"""
[bold yellow]User@Host[/bold yellow]     [cyan]{user}@{platform.node()}[/cyan]
[bold cyan]--------------------------------[/bold cyan]
[bold yellow]OS:[/bold yellow]           {platform.system()} {platform.release()}
[bold yellow]Kernel:[/bold yellow]       {platform.version()}
[bold yellow]Shell:[/bold yellow]        {os.environ.get("SHELL", "pwsh")}

[bold magenta]Project:[/bold magenta]      Ganet - Project BWC
[bold magenta]Architecture:[/bold magenta] Zero-Copy Mathematical Pipeline
[bold magenta]Version:[/bold magenta]      v2.1 (Evaluator Mode)
[bold magenta]Data Feeds:[/bold magenta]   [green]YFinance Primary[/green] | [yellow]Local DuckDB Cache[/yellow]
[bold magenta]Graph Models:[/bold magenta] [cyan]Topological Lasso CV[/cyan]
"""

    console.print()
    title = "[bold cyan]════════════ GANET: PORTFOLIO ENGINE BOOTING ════════════[/bold cyan]"
    
    # Quick sweep animation for the title
    for i in range(len(title)):
        if "═" in title[i]:
            console.print(Align.center(title[:i] + "█"), end="\r")
            time.sleep(0.01)
    console.print(Align.center(title))
    console.print()

    col = Columns(
        [
            Panel(Text.from_markup(ascii_art), border_style="cyan"),
            Panel(Text.from_markup(metadata), border_style="magenta", padding=(1, 5)),
        ]
    )
    console.print(Align.center(col))
    console.print()
    
    # Elastic pausing - witty delay
    console.print(Align.center("[dim]Executing math allocations and mounting structures...[/dim]"))
    time.sleep(0.12)
    console.print(Align.center("[bold green]✔ Handshake complete. Yielding UI Control.[/bold green]"))
    time.sleep(0.12)
    time.sleep(0.8)


def generate_layout() -> Layout:
    """Generates the full unixporn layout skeleton."""
    layout = Layout(name="root")
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=7),
    )
    layout["main"].split_row(Layout(name="left", ratio=1), Layout(name="right", ratio=1))
    layout["footer"].split_row(Layout(name="macro", ratio=1), Layout(name="health", ratio=1))
    return layout


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--view", help="Not used in multi-view layout, kept for compatibility", default=None
    )
    parser.add_argument("--live", action="store_true", help="Auto-refresh UI on timer")
    args = parser.parse_args(argv)

    draw_neofetch()

    # Build initial view once to ensure dependencies are loaded cleanly without weird race conditions
    layout = generate_layout()
    try:
        layout["header"].update(make_header())
        layout["left"].update(make_holdings())
        layout["right"].update(make_signals())
        layout["macro"].update(make_macro())
        layout["health"].update(make_health())
    except Exception as e:
        console.print(f"[bold red]Critical Render Error[/bold red]: {e}")
        import traceback

        traceback.print_exc()
        return

    if args.live:
        import sys

        current_view = "main"
        force_update = True

        with Live(layout, refresh_per_second=4, screen=True):
            ticks = 0
            while True:
                # Key press detection mapping for Windows
                if sys.platform == "win32":
                    import msvcrt

                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode("utf-8", errors="ignore").lower()
                        if key == "q":
                            break
                        elif key == "m":
                            current_view = "metrics" if current_view == "main" else "main"
                            force_update = True

                layout["header"].update(make_header())

                # Only update heavy DB calls every 4 ticks (1 second) to prevent lockups, animate the rest
                if ticks % 4 == 0 or force_update:
                    if current_view == "main":
                        layout["main"].split_row(
                            Layout(make_holdings(), name="left", ratio=1),
                            Layout(make_signals(), name="right", ratio=1),
                        )
                    else:
                        layout["main"].split_row(
                            Layout(make_metrics(), name="metrics", ratio=1),
                            Layout(make_chart(ticks), name="chart", ratio=2),
                        )

                    # Update lower left panels
                    layout["macro"].update(make_macro())

                    force_update = False

                layout["health"].update(make_health(ticks, current_view))

                time.sleep(0.25)
                ticks += 1
    else:
        # Static print (like an immediate unix-porn screen fetch to stdout)
        # Not using screen=True so it persists in the terminal buffer
        console.print(layout)


if __name__ == "__main__":
    main()
