"""APScheduler entry point — orchestrates the 15-minute signal generation cycle.

Run locally:  doppler run -- uv run python -m quant_monitor.main
Run on Heroku: see Procfile (worker dyno)
"""

from __future__ import annotations

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Start the portfolio monitoring scheduler."""
    from quant_monitor.config import cfg

    logger.info("Quant Portfolio Monitor starting")
    logger.info("Tracking %d positions | Benchmark: %s", len(cfg.tickers), cfg.benchmark)
    logger.info("Valuation date: %s | Sunset: %s", cfg.valuation_date, cfg.sunset_date)

    # TODO Phase 7: Wire up APScheduler
    # - Every 15 min (market hours): full signal cycle
    # - Every 1 hour (off hours): macro + sentiment only
    # - Daily 9:00 AM ET: portfolio snapshot to Appwrite
    # - On startup: immediate first run
    #
    # from apscheduler.schedulers.blocking import BlockingScheduler
    # scheduler = BlockingScheduler()
    # scheduler.add_job(run_signal_cycle, 'interval', minutes=cfg.project['rebalance_interval_minutes'])
    # scheduler.start()

    logger.info("Scheduler not yet implemented — exiting cleanly")


if __name__ == "__main__":
    main()
