"""Deployment bootstrap checks for prototype readiness.

Run:
    doppler run -- uv run quant-bootstrap
"""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from quant_monitor.config import cfg

console = Console()


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    required: bool = True


def _check_python() -> CheckResult:
    major, minor = sys.version_info[:2]
    ok = (major, minor) >= (3, 11)
    return CheckResult(
        name="Python",
        status="OK" if ok else "FAIL",
        detail=f"{platform.python_version()} (requires >=3.11)",
        required=True,
    )


def _check_config() -> CheckResult:
    tickers = len(cfg.tickers)
    ok = tickers > 0 and cfg.initial_capital > 0
    return CheckResult(
        name="Config",
        status="OK" if ok else "FAIL",
        detail=f"{tickers} tickers, initial_capital=${cfg.initial_capital:,.0f}",
        required=True,
    )


def _check_required_secrets() -> CheckResult:
    required = ["APPWRITE_ENDPOINT", "APPWRITE_PROJECT_ID", "APPWRITE_API_KEY"]
    missing = [k for k in required if not getattr(cfg.secrets, k, "")]
    ok = not missing
    detail = "all required secrets present" if ok else f"missing: {', '.join(missing)}"
    return CheckResult("Required secrets", "OK" if ok else "FAIL", detail, required=True)


def _check_appwrite() -> CheckResult:
    try:
        from quant_monitor.data.appwrite_client import create_appwrite_client

        client = create_appwrite_client()
        _ = client.get_latest_signals()
        return CheckResult(
            name="Appwrite connectivity",
            status="OK",
            detail="query to signals collection succeeded",
            required=True,
        )
    except Exception as exc:  # pragma: no cover - network/env dependent
        return CheckResult(
            name="Appwrite connectivity",
            status="FAIL",
            detail=str(exc),
            required=True,
        )


def _check_openbb_optional() -> CheckResult:
    try:
        from openbb import obb  # noqa: F401

        return CheckResult(
            name="OpenBB",
            status="OK",
            detail="installed and importable",
            required=False,
        )
    except Exception as exc:
        return CheckResult(
            name="OpenBB",
            status="WARN",
            detail=f"optional unavailable: {exc}",
            required=False,
        )


def _check_telegram_optional() -> CheckResult:
    token = bool(cfg.secrets.TELEGRAM_BOT_TOKEN)
    chat = bool(cfg.secrets.TELEGRAM_CHAT_ID)
    if token and chat:
        return CheckResult("Telegram", "OK", "token + chat id configured", required=False)
    return CheckResult("Telegram", "WARN", "optional: token/chat id not fully set", required=False)


def _check_scrapy_mode() -> CheckResult:
    local_spiders = bool(cfg.scrapy_cloud.get("local_spiders", False))
    mode = "local+cloud" if local_spiders else "cloud-first"
    return CheckResult("Scrapy mode", "OK", mode, required=False)


def run_checks() -> list[CheckResult]:
    checks = [
        _check_python,
        _check_config,
        _check_required_secrets,
        _check_appwrite,
        _check_openbb_optional,
        _check_telegram_optional,
        _check_scrapy_mode,
    ]

    results: list[CheckResult] = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        for fn in checks:
            task = progress.add_task(f"Running {fn.__name__.replace('_', ' ')}", total=None)
            result = fn()
            results.append(result)
            progress.update(task, completed=True)
    return results


def _print_results(results: list[CheckResult]) -> None:
    table = Table(title="Bootstrap Readiness")
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Detail")

    for r in results:
        if r.status == "OK":
            status = "[green]OK[/green]"
        elif r.status == "WARN":
            status = "[yellow]WARN[/yellow]"
        else:
            status = "[red]FAIL[/red]"
        table.add_row(r.name, status, r.detail)

    console.print(table)


def main() -> int:
    console.print("[bold]Quant Monitor bootstrap checks[/bold]")
    results = run_checks()
    _print_results(results)

    has_required_failures = any(r.required and r.status == "FAIL" for r in results)
    if has_required_failures:
        console.print("[red]Bootstrap failed: fix required checks before deployment.[/red]")
        return 1

    console.print("[green]Bootstrap passed: required checks are healthy.[/green]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
