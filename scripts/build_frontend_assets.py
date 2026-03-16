"""Build all static frontend assets for the GitHub Pages microsite.

Orchestrates chart generation, results JSON, and tearsheet PDF into
the frontend/ directory tree. Uses PortfolioHistoryEngine for real data.

Usage:
    uv run python scripts/build_frontend_assets.py
    uv run python scripts/build_frontend_assets.py --output-dir frontend
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure project root and scripts/ are importable
_project_root = str(Path(__file__).parent.parent)
_scripts_dir = str(Path(__file__).parent)
for p in (_project_root, _scripts_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_all(output_dir: str = "frontend") -> None:
    """Generate every static asset the frontend needs."""
    root = Path(output_dir)
    charts_dir = root / "charts"
    data_dir = root / "data"
    assets_dir = root / "assets"

    for d in (charts_dir, data_dir, assets_dir):
        d.mkdir(parents=True, exist_ok=True)

    # --- 0. Initialize PortfolioHistoryEngine (real data source) ---
    engine = None
    try:
        from quant_monitor.data.portfolio_history import PortfolioHistoryEngine

        engine = PortfolioHistoryEngine()
        nav = engine.get_portfolio_nav()
        logger.info(
            "PortfolioHistoryEngine loaded: %d trading days, NAV $%s -> $%s",
            len(nav),
            f"{nav.iloc[0]:,.0f}" if len(nav) > 0 else "?",
            f"{nav.iloc[-1]:,.0f}" if len(nav) > 0 else "?",
        )
    except Exception as e:
        logger.warning("PortfolioHistoryEngine unavailable: %s -- using synthetic fallbacks", e)

    # --- 1. Plotly Charts ---
    logger.info("=== Generating Plotly charts ===")
    try:
        from generate_plotly_dashboard import generate_all_charts

        generate_all_charts(str(charts_dir))
        logger.info("Plotly charts complete -> %s", charts_dir)

        results_src = charts_dir / "results.json"
        results_dst = data_dir / "results.json"
        if results_src.exists():
            results_dst.write_text(results_src.read_text(encoding="utf-8"), encoding="utf-8")
            results_src.unlink()
            logger.info("results.json moved to %s", results_dst)
    except Exception as e:
        logger.error("Plotly chart generation failed: %s", e, exc_info=True)

    # --- 2. Behavioural audit JSON ---
    if engine is not None:
        logger.info("=== Running behavioural audit ===")
        try:
            from quant_monitor.backtest.behavioural import run_full_behavioural_audit

            trades = engine.get_trade_log()
            prices = engine._fetch_prices()
            audit = run_full_behavioural_audit(
                trades, prices, engine._initial_capital
            )
            audit_path = data_dir / "behavioural-audit.json"
            audit_path.write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
            logger.info("Behavioural audit complete -> %s", audit_path)
        except Exception as e:
            logger.warning("Behavioural audit failed: %s", e)

    # --- 3. Full metrics JSON (superset of results.json) ---
    if engine is not None:
        logger.info("=== Computing full metrics ===")
        try:
            metrics = engine.compute_all_metrics()
            factor_reg = engine.run_factor_regression()
            metrics["factor_regression"] = factor_reg

            full_path = data_dir / "full-metrics.json"
            full_path.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
            logger.info("Full metrics complete -> %s", full_path)
        except Exception as e:
            logger.warning("Full metrics failed: %s", e)

    # --- 4. PDF Tearsheet ---
    logger.info("=== Generating PDF tearsheet ===")
    try:
        from generate_tearsheet import generate_tearsheet

        generate_tearsheet(
            output_path=str(assets_dir / "tearsheet.pdf"),
            benchmark="SPY",
        )
        logger.info("Tearsheet complete -> %s", assets_dir / "tearsheet.pdf")
    except Exception as e:
        logger.error("Tearsheet generation failed: %s", e, exc_info=True)

    # --- 5. Copy backtest results JSON ---
    logger.info("=== Copying backtest results ===")
    backtest_src = Path("docs/backtest-results.json")
    backtest_dst = data_dir / "backtest-results.json"
    if backtest_src.exists():
        backtest_dst.write_text(backtest_src.read_text(encoding="utf-8"), encoding="utf-8")
        logger.info("Backtest results copied -> %s", backtest_dst)
    else:
        logger.warning("No backtest-results.json found at %s", backtest_src)

    logger.info("=== Build complete ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build all frontend static assets")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="frontend",
        help="Root output directory (default: frontend)",
    )
    args = parser.parse_args()
    build_all(output_dir=args.output_dir)
