"""Pre-sunset export script — pulls all data from Appwrite and generates static archive.

Run before May 1, 2026 to populate docs/ with final performance data, charts, and signal history.

Usage:
    doppler run -- uv run python scripts/export_for_archive.py
"""

from __future__ import annotations

import datetime
import logging
import sys

logger = logging.getLogger(__name__)


def verify_sunset_date():
    """HARD ENFORCEMENT: Never run this before May 1, 2026."""
    target_date = datetime.date(2026, 5, 1)
    if datetime.date.today() < target_date:
        logger.error(f"CRITICAL: Project sunset cannot occur before {target_date}.")
        logger.error("The forward Monte Carlo window must elapse mathematically.")
        sys.exit(1)


def export_portfolio_performance():
    """Export portfolio snapshots → equity curve chart + summary table."""
    # TODO: Query Appwrite portfolio_snapshots
    # TODO: Generate equity curve (plotly → HTML, matplotlib → PNG)
    # TODO: Write to docs/performance.md
    logger.info("Portfolio performance export — not yet implemented")


def export_signal_history():
    """Export complete signal log → Markdown table."""
    # TODO: Query Appwrite signals collection
    # TODO: Format as Markdown table
    # TODO: Write to docs/signals-history.md
    logger.info("Signal history export — not yet implemented")


def export_backtest_results():
    """Export backtest metrics → comparison table + charts."""
    # TODO: Run final backtest or load cached results
    # TODO: Write to docs/backtest-results.md
    logger.info("Backtest results export — not yet implemented")


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
