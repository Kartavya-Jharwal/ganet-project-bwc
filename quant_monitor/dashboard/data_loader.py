"""Dashboard data loader — fetches data for Rich CLI views.

Uses functools.lru_cache for in-process caching (TTL managed by diskcache
underneath the DataPipeline). Falls back gracefully when Appwrite / pipeline
is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def load_portfolio_state() -> dict[str, Any]:
    """Load current portfolio holdings and values from config."""
    from quant_monitor.config import cfg

    holdings: dict[str, dict] = {}
    for ticker, info in cfg.holdings.items():
        holdings[ticker] = {
            "name": info["name"],
            "type": info["type"],
            "qty": info["qty"],
            "price_paid": info["price_paid"],
            "sector": info["sector"],
            "cost_basis": info["qty"] * info["price_paid"],
        }

    return {
        "holdings": holdings,
        "cash": cfg.project.get("cash_balance", 0),
        "initial_capital": cfg.initial_capital,
        "benchmark": cfg.benchmark,
        "tickers": cfg.tickers,
    }


def load_latest_prices() -> dict[str, float]:
    """Fetch latest prices for all portfolio tickers via DataPipeline."""
    try:
        from quant_monitor.data.pipeline import DataPipeline

        pipeline = DataPipeline()
        prices = pipeline.fetch_latest_prices()
        return {t: p.get("price", 0) for t, p in prices.items()} if prices else {}
    except Exception as e:
        logger.warning("Failed to load latest prices: %s", e)
        return {}


def load_macro_snapshot() -> dict[str, float]:
    """Fetch current macro indicators from FRED / pipeline."""
    try:
        from quant_monitor.data.pipeline import DataPipeline

        pipeline = DataPipeline()
        macro = pipeline.fetch_macro()
        if not macro:
            return {}

        if not any(isinstance(v, (int, float)) for v in macro.values()):
            logger.warning("Macro snapshot has no numeric values; returning empty snapshot")
            return {}

        return macro
    except Exception as e:
        logger.warning("Failed to load macro data: %s", e)
        return {}


def load_signals_from_appwrite() -> list[dict]:
    """Fetch latest signals from Appwrite backend."""
    try:
        from quant_monitor.data.appwrite_client import create_appwrite_client

        client = create_appwrite_client()
        return client.get_latest_signals()
    except Exception as e:
        logger.warning("Failed to load signals: %s", e)
        return []


def build_holdings_dataframe(
    holdings: dict[str, dict],
    prices: dict[str, float],
) -> pd.DataFrame:
    """Build a DataFrame of holdings with P/L calculations.

    Shared by both CLI views and potential future web views.
    """
    rows = []
    for ticker, info in holdings.items():
        current_price = prices.get(ticker, info["price_paid"])
        market_value = info["qty"] * current_price
        cost_basis = info["cost_basis"]
        pnl = market_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        rows.append(
            {
                "ticker": ticker,
                "name": info["name"],
                "sector": info["sector"],
                "qty": info["qty"],
                "avg_cost": info["price_paid"],
                "current": current_price,
                "market_value": market_value,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
            }
        )
    return pd.DataFrame(rows)
