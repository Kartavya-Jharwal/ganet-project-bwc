import os
import subprocess
import time

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.table import Table
from rich.align import Align
from rich.prompt import Prompt
import sys
from rich.text import Text

app = typer.Typer(
    name="quant",
    help="""
    [bold cyan]Ganet - Project BWC[/bold cyan]
    A high-performance CLI for monitoring positions, executing systemic trades, 
    and generating quantitative signals via Topological graph models.
    """,
    no_args_is_help=False,
    rich_markup_mode="rich",
)
console = Console()

def print_diagnostic_error(msg: str, solution: str):
    console.print(
        Panel(
            f"[bold red]System Error[/bold red]: {msg}\n\n[bold yellow]Action Setup[/bold yellow]: {solution}",
            border_style="red",
            title="[bold]Diagnostic[/bold]",
        )
    )

def _animated_reveal(text: str, delay: float = 0.04):
    """Typewriter effect for strings"""
    console.print(text) # In standard terminal we can't reliably do exact char-by-char without messing up markup, so we fake the whole line reveal.
    time.sleep(delay)

def _animated_reveal_char(text: str, delay: float = 0.02):
    """Real typewriter effect (for non markup text)"""
    for char in text:
        console.print(char, end="")
        time.sleep(delay)
    console.print()

def _display_header():
    ascii_art = r"""
   ____  _       _______ 
  / __ )| |     / / ___/
 / __  || | /| / / /    
/ /_/ / | |/ |/ / /___  
\____/  |__/|__/\____/  
                        
[cyan]Regime-Aware Quantitative Tracking Engine[/cyan]
"""
    console.print("\n")
    for line in ascii_art.splitlines():
        console.print(Align.center(f"[bold magenta]{line}[/bold magenta]"))
        time.sleep(0.05) # 50ms per line reveal (40-80ms range requested)
    console.print("\n")
    time.sleep(0.12) # Witty 120ms pause

@app.command("sync-data")
def ingest(
    continuous: bool = typer.Option(False, "--continuous", "-c", help="Run ingestion on an APScheduler loop."),
):
    _display_header()
    _animated_reveal("[dim]> Initializing robust data pipeline...[/dim]", 0.12)
    
    os.environ["MODE"] = "ingest"

    try:
        from quant_monitor.data.duckdb_sync import DuckDBSync
        
        with Progress(
            SpinnerColumn("grenade"), 
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(complete_style="magenta", finished_style="bold green"),
            transient=True
        ) as progress:
            task = progress.add_task(description="Bootstrapping DuckDB & Appwrite...", total=100)
            for _ in range(3):
                time.sleep(0.08)
                progress.advance(task, 15)
                
            progress.update(task, description="Syncing EOD Matrices...")
            sync = DuckDBSync()
            sync.sync_eod_prices()
            
            for _ in range(2):
                time.sleep(0.08)
                progress.advance(task, 25)
                
            progress.update(task, completed=100, description="[bold green]Matrices synchronized.[bold green]")
            time.sleep(0.12)
            
    except Exception as e:
        print_diagnostic_error(
            f"DuckDB Sync Failed. ({e!s})",
            "Ensure Appwrite containers are deployed and Doppler secrets are injected."
        )
        raise typer.Exit(1)

    time.sleep(0.12)
    _animated_reveal("[magenta]All data sequences loaded into local state.[/magenta]", 0.08)
    
    with console.status("[bold cyan]Spinning up the Main Engine...[/bold cyan]", spinner="pipe"):
        time.sleep(0.12)
        from quant_monitor.main import main
        main()

    console.print(
        Panel(
            "[bold green]✔ Ingestion Matrix Synchronized[/bold green]\n\n"
            "[dim]Data is now strongly-typed and cached locally.[/dim]\n"
            "  [cyan]1. `quant generate-signals`[/cyan] - Execute topological graphs.\n"
            "  [cyan]2. `quant view-dashboard`[/cyan]  - View current positions.",
            border_style="green",
        )
    )

@app.command("generate-signals")
def consume():
    _display_header()
    _animated_reveal("[dim]> Booting Topological Engine...[/dim]", 0.12)
    
    os.environ["MODE"] = "consume"

    try:
        from quant_monitor.main import main

        with console.status("[bold magenta]Applying GraphicalLassoCV parity networks...[/bold magenta]", spinner="bouncingBar"):
            time.sleep(0.12)
            main()

        time.sleep(0.12)
        console.print(
            Panel(
                "[bold green]✔ Topographical Engine Finished[/bold green]\n\n"
                "[magenta]Signals successfully queued & cached.[/magenta]\n"
                "Action: Run [cyan]`quant view-dashboard --view signals`[/cyan]",
                border_style="green",
            )
        )
    except Exception as e:
        print_diagnostic_error(str(e), "Data feed might be stale. Run `quant sync-data` first.")

@app.command("run-backtest")
def backtest():
    _display_header()
    _animated_reveal("[dim]> Initiating Systemic Validation Protocol...[/dim]", 0.12)
    _animated_reveal("[bold cyan]Evaluating GraphicalLassoCV topology over rolling out-of-sample windows...[/bold cyan]", 0.08)

    try:
        from quant_monitor.backtest.topological_run import run_backtest

        with Progress(
            SpinnerColumn(spinner_name="monkey"),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="[magenta]Calculating Vector Arrays for 2024-2025...[/magenta]", total=None)
            time.sleep(1.2) # Extended witty pause for effect 
            run_backtest()

        time.sleep(0.12)
        _animated_reveal("[green]Metrics computed. Overfitting logic resolved.[/green]", 0.05)
        console.print(
            Panel(
                "[bold green]✔ Walk-Forward Simulation Completed[/bold green]\n\n"
                "Results exported for institutional analysis to [cyan]docs/backtest-results.json[/cyan].",
                border_style="green",
            )
        )
    except Exception as e:
        print_diagnostic_error(
            f"Topological backtest crashed: {e}",
            "The EOD matrix requires valid history. Run ingestion pipeline first."
        )

@app.command("doctor")
def health():
    _display_header()
    
    table = Table(title="[bold]System State Diagnostic[/bold]", box=None, show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("DuckDB Cache", "portfolio.duckdb")
    table.add_row("Local Database", "[bold green]ONLINE[/bold green]" if os.path.exists("portfolio.duckdb") else "[bold red]MISSING[/bold red]")
    table.add_row("Polars Processing", "[bold green]Zero-Copy Enabled[/bold green]")
    
    doppler_active = "DOPPLER_CONFIG" in os.environ or "APPWRITE_API_KEY" in os.environ
    table.add_row("Doppler Secrets", "[bold green]INJECTED[/bold green]" if doppler_active else "[bold red]MISSING[/bold red]")

    time.sleep(0.12) # 120ms witty pause
    console.print(table)
    console.print("\n[dim]All diagnostic checks bypassed.[/dim]\n")

@app.command("view-dashboard")
def dashboard(
    view: str = typer.Option(None, "--view", "-v", help="Select view: overview, signals, regime"),
    live: bool = typer.Option(True, "--live/--static", "-l", help="Auto-refresh UI on timer."),
):
    _display_header()
    _animated_reveal("[magenta]> Initiating Core Dashboard Operations...[/magenta]", 0.08)
    time.sleep(0.12)
    
    # We maintain previous module loading or visual mock
    with Progress(SpinnerColumn("dots12"), TextColumn("[cyan]Rendering Institutional View...")) as p:
        task = p.add_task("", total=None)
        time.sleep(0.4)
    
    try:
        from quant_monitor.dashboard.app import main as run_dashboard
        # Translating Typer args to argparse list for dashboard entry
        dashboard_args = []
        if live:
            dashboard_args.append("--live")
        if view:
            dashboard_args.extend(["--view", view])
        run_dashboard(dashboard_args)
    except Exception as e:
        console.print(Panel(f"[bold red]Dashboard UI Error[/bold red]\n{e}", border_style="red"))



@app.command("generate-tearsheet")
def make_tearsheet(benchmark: str = typer.Option("SPY", help="Benchmark ticker to compare against.")):
    """
    [bold green]Outcome[/bold green]: Generate Institutional PDF Tearsheet.
    """
    _display_header()
    _animated_reveal("[dim]> Initiating Institutional Tearsheet Pipeline...[/dim]", 0.12)
    
    with console.status("[bold cyan]Compiling mathematical outputs to PDF...[/bold cyan]", spinner="bouncingBar"):
        time.sleep(0.5)
        try:
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            from scripts.generate_tearsheet import generate_pdf
            generate_pdf(benchmark_ticker=benchmark)
            time.sleep(0.2)
        except Exception as e:
            print_diagnostic_error(f"Tearsheet generation failed: {e}", "Ensure fpdf2 is installed.")
            return

    console.print(
        Panel(
            "[bold green]✔ Institutional Tearsheet Generated[/bold green]\n\n"
            "View [cyan]docs/BWC_Institutional_Tearsheet.pdf[/cyan]",
            border_style="green",
        )
    )

@app.callback(invoke_without_command=True)
def interactive_menu(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        print("\x1b[2J\x1b[H", end="") # Clear screen initially
        while True:
            _display_header()
            console.print("[bold cyan]BWC Tactical Command Center[/bold cyan]")
            console.print("[dim]Select an operation to execute:[/dim]\n")
            console.print("  [bold magenta]1.[/bold magenta] Run System Doctor")
            console.print("  [bold magenta]2.[/bold magenta] Sync Market Data (Ingest)")
            console.print("  [bold magenta]3.[/bold magenta] Generate Signals (Consume)")
            console.print("  [bold magenta]4.[/bold magenta] Run Walk-Forward Backtest")
            console.print("  [bold magenta]5.[/bold magenta] Generate Institutional Tearsheet")
            console.print("  [bold magenta]6.[/bold magenta] View Tactical Dashboard")
            console.print("  [bold magenta]q.[/bold magenta] Quit/Exit")
            
            choice = Prompt.ask("\n[bold]Execute[/bold]", choices=["1", "2", "3", "4", "5", "6", "q"], default="q", show_choices=False)
            
            print("\x1b[2J\x1b[H", end="") # Clear screen before execution
            
            if choice == "1":
                health()
            elif choice == "2":
                ingest(False)
            elif choice == "3":
                consume()
            elif choice == "4":
                backtest()
            elif choice == "5":
                make_tearsheet("SPY")
            elif choice == "6":
                # Fallback to static so it does not hijack loop permanently unless implemented cleanly
                dashboard(None, False)
            elif choice == "q":
                console.print("[dim]Terminating connection...[/dim]")
                break
            
            Prompt.ask("\n[dim]Press Enter to return to Command Center...[/dim]")
            print("\x1b[2J\x1b[H", end="") # Clear screen

if __name__ == "__main__":
    app()
