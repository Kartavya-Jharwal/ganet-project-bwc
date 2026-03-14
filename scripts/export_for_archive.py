"""Pre-sunset export script — pulls all data from Appwrite and generates static archive.

Run before May 1, 2026 to populate docs/ with final performance data, charts, and signal history.

Usage:
    doppler run -- uv run python scripts/export_for_archive.py
"""

from __future__ import annotations

import datetime
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

DOCS_DIR = Path("docs")


def verify_sunset_date():
    """HARD ENFORCEMENT: Never run this before May 1, 2026."""
    target_date = datetime.date(2026, 5, 1)
    if datetime.date.today() < target_date:
        logger.error(f"CRITICAL: Project sunset cannot occur before {target_date}.")
        logger.error("The forward Monte Carlo window must elapse mathematically.")
        sys.exit(1)


def export_portfolio_performance():
    """Export portfolio snapshots → equity curve chart + summary table."""
    from quant_monitor.config import cfg
    from quant_monitor.dashboard.data_loader import build_holdings_dataframe, load_portfolio_state

    state = load_portfolio_state()
    holdings = state["holdings"]

    # Use cost basis prices as final snapshot when live prices unavailable
    prices = {ticker: info["price_paid"] for ticker, info in holdings.items()}
    try:
        from quant_monitor.dashboard.data_loader import load_latest_prices

        live = load_latest_prices()
        if live:
            prices.update(live)
    except Exception as exc:
        logger.warning("Could not fetch live prices, using cost basis: %s", exc)

    df = build_holdings_dataframe(holdings, prices)

    # Build Markdown report
    lines = [
        "# Portfolio Performance Summary",
        "",
        f"**Generated:** {datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Initial Capital:** ${cfg.initial_capital:,.2f}",
        f"**Cash Balance:** ${state['cash']:,.2f}",
        "",
        "## Current Holdings",
        "",
        "| Ticker | Name | Sector | Qty | Avg Cost | Current | Market Value | P/L ($) | P/L (%) |",
        "|--------|------|--------|-----|----------|---------|-------------|---------|---------|",
    ]

    for _, row in df.iterrows():
        lines.append(
            f"| {row['ticker']} | {row['name']} | {row['sector']} | {row['qty']} "
            f"| ${row['avg_cost']:,.2f} | ${row['current']:,.2f} "
            f"| ${row['market_value']:,.2f} | {row['pnl']:+,.2f} | {row['pnl_pct']:+.2f}% |"
        )

    total_market = float(df["market_value"].sum()) + state["cash"]
    total_pnl = total_market - cfg.initial_capital
    total_pnl_pct = (total_pnl / cfg.initial_capital * 100) if cfg.initial_capital else 0

    lines.extend([
        "",
        "## Summary",
        "",
        f"- **Total AUM:** ${total_market:,.2f}",
        f"- **Net P/L:** ${total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)",
        f"- **Number of Positions:** {len(df)}",
    ])

    out_path = DOCS_DIR / "performance.md"
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Portfolio performance exported to %s", out_path)


def export_signal_history():
    """Export complete signal log → Markdown table."""
    signals: list[dict] = []

    # Try Appwrite first
    try:
        from quant_monitor.data.appwrite_client import create_appwrite_client

        client = create_appwrite_client()
        signals = client.get_latest_signals()
    except Exception as exc:
        logger.warning("Could not fetch signals from Appwrite: %s", exc)

    lines = [
        "# Signal History",
        "",
        f"**Generated:** {datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]

    if not signals:
        lines.append("_No signal data available. Run `project generate-signals` first._")
    else:
        lines.extend([
            "| Timestamp | Ticker | Fused Score | Confidence | Action | Regime |",
            "|-----------|--------|------------|------------|--------|--------|",
        ])
        for sig in signals:
            lines.append(
                f"| {sig.get('timestamp', 'N/A')} "
                f"| {sig.get('ticker', 'N/A')} "
                f"| {sig.get('fused_score', 0):.3f} "
                f"| {sig.get('confidence', 0):.3f} "
                f"| {sig.get('action', 'N/A')} "
                f"| {sig.get('regime', 'N/A')} |"
            )

    lines.append(f"\n**Total signals:** {len(signals)}")

    out_path = DOCS_DIR / "signals-history.md"
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Signal history exported to %s (%d signals)", out_path, len(signals))


def export_backtest_results():
    """Export backtest metrics → comparison table + charts."""
    results_path = DOCS_DIR / "backtest-results.json"

    # Try loading cached results first
    cached_results = None
    if results_path.exists():
        try:
            cached_results = json.loads(results_path.read_text(encoding="utf-8"))
            logger.info("Loaded cached backtest results from %s", results_path)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not load cached results: %s", exc)

    # If no cached results, run a fresh backtest
    if not cached_results:
        try:
            from quant_monitor.backtest.engine import WalkForwardEngine
            from quant_monitor.data.pipeline import DataPipeline

            pipeline = DataPipeline()
            prices = pipeline.fetch_prices(period="2y")
            if prices.empty:
                logger.warning("No price data available for backtest export")
                cached_results = {"error": "no_price_data"}
            else:
                engine = WalkForwardEngine()
                comparison = engine.compare_models(prices)
                if comparison.empty:
                    cached_results = {"error": "insufficient_data_for_backtest"}
                else:
                    cached_results = json.loads(comparison.to_json(orient="index"))
                    # Save for future use
                    results_path.write_text(
                        json.dumps(cached_results, indent=2), encoding="utf-8"
                    )
        except Exception as exc:
            logger.warning("Could not run backtest: %s", exc)
            cached_results = {"error": str(exc)}

    # Generate Markdown report
    lines = [
        "# Backtest Results",
        "",
        f"**Generated:** {datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]

    if isinstance(cached_results, dict) and "error" in cached_results:
        lines.append(f"_Backtest could not be completed: {cached_results['error']}_")
    elif isinstance(cached_results, dict):
        # Build comparison table from model results
        models = list(cached_results.keys())
        if models:
            metrics_keys = [
                k for k in cached_results[models[0]]
                if k not in ("window_details",)
            ]
            lines.extend([
                "## Walk-Forward Backtest Comparison",
                "",
                "| Metric | " + " | ".join(models) + " |",
                "|--------|" + "|".join(["--------"] * len(models)) + "|",
            ])
            for metric in metrics_keys:
                row_vals = []
                for model in models:
                    val = cached_results[model].get(metric, "N/A")
                    if isinstance(val, float):
                        row_vals.append(f"{val:.4f}")
                    else:
                        row_vals.append(str(val))
                lines.append(f"| {metric} | " + " | ".join(row_vals) + " |")
    else:
        lines.append("_No backtest results available._")

    out_path = DOCS_DIR / "backtest-results.md"
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Backtest results exported to %s", out_path)


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting pre-sunset export...")

    verify_sunset_date()

    export_portfolio_performance()
    export_signal_history()
    export_backtest_results()
    logger.info("Export complete. Run 'uv run mkdocs build -f docs/mkdocs.yml' to build site.")


if __name__ == "__main__":
    main()
