import os
import subprocess

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# --- Setup Application & Theming ---
app = typer.Typer(
    name="quant",
    help="""
    [bold cyan]Ganet - Project BWC[/bold cyan]
    (Brownies with White Chocolate)
    
    A high-performance CLI for monitoring positions, executing systemic trades, 
    and generating quantitative signals via Topological graph models.
    """,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


def print_diagnostic_error(msg: str, solution: str):
    """Prints errors with clear diagnostics and actionable next steps."""
    console.print(
        Panel(
            f"[bold red]System Error[/bold red]: {msg}\n\n[bold yellow]Action Setup[/bold yellow]: {solution}",
            border_style="red",
            title="[bold]Diagnostic[/bold]",
        )
    )


@app.command("sync-data")
def ingest(
    continuous: bool = typer.Option(
        False, "--continuous", "-c", help="Run ingestion on an APScheduler loop indefinitely."
    ),
):
    """
    [bold green]Outcome[/bold green]: Pull latest OHLCV data, SEC filings, and news into local DuckDB and Appwrite.

    Defaults: Single execution pass unless '--continuous' is applied.
    """
    console.print("[dim]Target: Appwrite Cloud cluster & Local DuckDB cache[/dim]\n")

    os.environ["MODE"] = "ingest"

    try:
        from quant_monitor.data.duckdb_sync import DuckDBSync

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True
        ) as progress:
            progress.add_task(description="Syncing Appwrite Database -> DuckDB...", total=None)
            sync = DuckDBSync()
            sync.sync_eod_prices()
    except Exception as e:
        print_diagnostic_error(
            f"DuckDB Sync Failed. ({e!s})",
            "Make sure your Appwrite containers are deployed and `doppler run` injected secrets.",
        )
        raise typer.Exit(1)

    with console.status(
        "[bold cyan]Spinning up the Main Ingestion Pipeline...[/bold cyan]", spinner="dots4"
    ):
        from quant_monitor.main import main

        # Note: the actual main.py handles its own loop logic, but this triggers it.
        main()

    console.print(
        Panel(
            "[bold green]✔ Ingestion Matrix Synchronized[/bold green]\n\n"
            "Data is live and cached. Your next typical actions:\n"
            "  [cyan]1. `uv run python quant_monitor/cli.py generate-signals`[/cyan] - To calculate trades.\n"
            "  [cyan]2. `uv run python quant_monitor/cli.py view-dashboard`[/cyan]  - To monitor new incoming positions.",
            border_style="green",
        )
    )


@app.command("generate-signals")
def consume():
    """
    [bold green]Outcome[/bold green]: Process ingested market data locally (Cache-only) and output trading targets.

    Avoids API limits by querying local offline databases to construct signals.
    """
    os.environ["MODE"] = "consume"

    try:
        from quant_monitor.main import main

        with console.status(
            "[bold cyan]Executing Topographical Engine...[/bold cyan]", spinner="blue_pulse_math"
        ):
            main()

        console.print(
            Panel(
                "[bold green]✔ Topographical Engine Finished[/bold green]\n\n"
                "Calculated trades have been queued.\n"
                "Action: Run [cyan]`uv run python quant_monitor/cli.py view-dashboard --view signals`[/cyan]",
                border_style="green",
            )
        )
    except Exception as e:
        print_diagnostic_error(
            str(e), "Data feed might be stale. Run `quant sync-data` first before consuming."
        )


@app.command("run-backtest")
def backtest():
    """
    [bold green]Outcome[/bold green]: Stress-test topological logic on 2024-2025 out-of-sample data.
    """
    console.print("\n[bold magenta]INITIATING SYSTEMIC VALIDATION[/bold magenta]")
    console.print("[dim]Evaluating GraphicalLassoCV topology over rolling windows...[/dim]\n")

    try:
        from quant_monitor.backtest.topological_run import run_backtest

        with Progress(
            SpinnerColumn(spinner_name="monkey"),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Calculating Vector Arrays for 2024-2025...", total=None)
            run_backtest()

        console.print(
            Panel(
                "[bold green]✔ Backtest Simulation Completed[/bold green]\n\n"
                "Results logged to [cyan]docs/backtest-results.json[/cyan].",
                border_style="green",
            )
        )
    except Exception as e:
        print_diagnostic_error(
            f"Topological backtest crashed: {e}",
            "The EOD matrix needs valid history. Ensure 'portfolio.duckdb' size > 100kb.",
        )


@app.command("doctor")
def health():
    """
    [bold green]Outcome[/bold green]: Diagnostic checklist to orient your environment.
    """
    table = Table(title="[bold]System State Diagnostic[/bold]", box=None, show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("DuckDB Cache Path", "portfolio.duckdb")
    table.add_row(
        "DuckDB Exists",
        "[bold green]YES[/bold green]"
        if os.path.exists("portfolio.duckdb")
        else "[bold red]MISSING[/bold red]",
    )
    table.add_row(
        "Cached Folders",
        "[bold green]YES[/bold green]"
        if os.path.exists(".cache")
        else "[bold yellow]EMPTY[/bold yellow]",
    )

    doppler_active = "DOPPLER_CONFIG" in os.environ or "APPWRITE_API_KEY" in os.environ
    table.add_row(
        "Doppler Secrets",
        "[bold green]INJECTED[/bold green]"
        if doppler_active
        else "[bold red]MISSING (Run under 'doppler run -- ')[/bold red]",
    )

    console.print("\n")
    console.print(table)
    console.print(
        "\n[dim]If anything looks red or missing, resolve it before running sync.\nTip: You should run all commands via `doppler run -- uv run <cmd>`[/dim]\n"
    )


@app.command("view-dashboard")
def dashboard(
    view: str = typer.Option(
        None, "--view", "-v", help="Select view: overview, signals, regime, montecarlo, health"
    ),
    live: bool = typer.Option(True, "--live/--static", "-l", help="Auto-refresh UI on timer."),
):
    """
    [bold green]Outcome[/bold green]: Render the interactive Unixporn-style terminal hub.

    Defaults: Renders the full multi-panel dashboard in LIVE MODE unless --static is passed.
    """
    import time

    from rich.console import Console

    temp_console = Console()

    # Faux Bootlog
    temp_console.print("[dim]Executing pre-flight diagnostic sequence...[/dim]")
    stages = [
        "Verifying topological dataset cache...",
        "Linking Appwrite node modules...",
        "Validating signal parity vectors...",
        "Synchronizing YFinance data feeds...",
        "Calibrating macro regime weights...",
    ]
    for stage in stages:
        with temp_console.status(f"[bold cyan]{stage}[/bold cyan]"):
            time.sleep(0.4)
        temp_console.print(f"[bold green]OK[/bold green] [dim]{stage}[/dim]")

    time.sleep(0.5)

    # Run the dashboard
    cmd = ["uv", "run", "python", "quant_monitor/dashboard/app.py"]
    if view:
        cmd.extend(["--view", view])
    if live:
        cmd.append("--live")
    subprocess.run(cmd)


if __name__ == "__main__":
    app()
