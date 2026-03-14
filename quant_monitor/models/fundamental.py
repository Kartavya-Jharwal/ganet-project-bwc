"""Fundamental screening model — top-down macro → sector → industry → stock.

Produces a signal score ∈ [-1.0, +1.0].
Compares valuation ratios vs sector median.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

# We dynamically resolve sectors using OpenBB/YFinance instead of hardcoding.
# This cache reduces redundant API calls during runtime.
SECTOR_MAP = {}


def get_dynamic_sector(ticker: str) -> str:
    """Resolve sector via OpenBB with fallback to YFinance."""
    if ticker in SECTOR_MAP:
        return SECTOR_MAP[ticker]

    # Try OpenBB primarily
    try:
        from openbb import obb

        profile = obb.equity.profile(symbol=ticker)
        df = profile.to_df()
        if not df.empty and "sector" in df.columns:
            sector = df.iloc[0]["sector"]
            if sector:
                SECTOR_MAP[ticker] = sector
                return sector
    except Exception as e:
        logger.debug("OpenBB sector lookup failed for %s: %s", ticker, e)

    # Fallback to yfinance
    try:
        import yfinance as yf

        info = yf.Ticker(ticker).info
        sector = info.get("sector", "Unknown")
        SECTOR_MAP[ticker] = sector
        return sector
    except Exception as e:
        logger.debug("YFinance sector lookup failed for %s: %s", ticker, e)     
        SECTOR_MAP[ticker] = "Unknown"
        return "Unknown"


# Sector peer groups for relative valuation
SECTOR_PEERS = {
    "AI Infrastructure": ["TSM", "MU"],
    "AI Software": ["PLTR"],
    "Big Tech/AI": ["GOOGL", "AMZN"],
    "Defensive": ["WMT", "XLP", "PG", "JNJ", "XLU"],
    "Financials": ["JPM"],
    "Industrial": ["GE", "LMT"],
    "Speculative": ["IONQ"],
}


class FundamentalModel:
    """Top-down fundamental screening signal generator.

    Flow: Macro → Sector → Industry → Stock
    Is the sector in favor?
      → Is this industry growing within it?
        → Is this stock cheap/expensive vs peers?
    """

    def score(self, fundamentals: dict, sector_data: dict) -> float:
        """Generate fundamental signal score for a single ticker.

        Compares P/E, P/S, EV/EBITDA to sector medians.
        Cheaper than sector = positive signal.
        Returns: signal ∈ [-1.0, +1.0]
        """
        if not fundamentals or not sector_data:
            return 0.0

        signals: list[tuple[str, float, float]] = []

        # 1. P/E relative to sector (weight 0.35)
        pe = fundamentals.get("pe_ratio")
        pe_median = sector_data.get("pe_median")
        if pe and pe_median and pe_median > 0:
            pe_signal = (pe_median - pe) / pe_median
            signals.append(("pe", max(-1.0, min(1.0, pe_signal)), 0.35))

        # 2. P/S relative to sector (weight 0.25)
        ps = fundamentals.get("ps_ratio")
        ps_median = sector_data.get("ps_median")
        if ps and ps_median and ps_median > 0:
            ps_signal = (ps_median - ps) / ps_median
            signals.append(("ps", max(-1.0, min(1.0, ps_signal)), 0.25))

        # 3. EV/EBITDA relative to sector (weight 0.25)
        ev_ebitda = fundamentals.get("ev_ebitda")
        ev_median = sector_data.get("ev_ebitda_median")
        if ev_ebitda and ev_median and ev_median > 0:
            ev_signal = (ev_median - ev_ebitda) / ev_median
            signals.append(("ev", max(-1.0, min(1.0, ev_signal)), 0.25))

        # 4. Earnings revision direction (weight 0.15)
        revision = fundamentals.get("earnings_revision", 0.0)
        if revision is not None:
            rev_signal = max(-1.0, min(1.0, float(revision) * 5))
            signals.append(("rev", rev_signal, 0.15))

        if not signals:
            return 0.0

        total_weight = sum(s[2] for s in signals)
        weighted_sum = sum(s[1] * s[2] for s in signals)
        return float(max(-1.0, min(1.0, weighted_sum / total_weight)))

    def score_all(self, fundamentals_df: pd.DataFrame) -> dict[str, float]:
        """Score all tickers. Returns {ticker: signal_score}."""
        results: dict[str, float] = {}
        if fundamentals_df.empty or "ticker" not in fundamentals_df.columns:
            return results

        for ticker, group in fundamentals_df.groupby("ticker"):
            try:
                row = group.iloc[-1]
                fundamentals = {
                    "pe_ratio": row.get("pe_ratio"),
                    "ps_ratio": row.get("ps_ratio"),
                    "ev_ebitda": row.get("ev_ebitda"),
                    "earnings_revision": row.get("earnings_revision", 0.0),
                }
                sector_data = {
                    "pe_median": row.get("pe_median"),
                    "ps_median": row.get("ps_median"),
                    "ev_ebitda_median": row.get("ev_ebitda_median"),
                }
                results[str(ticker)] = self.score(fundamentals, sector_data)
            except Exception as e:
                logger.warning("Fundamental scoring failed for %s: %s", ticker, e)
                results[str(ticker)] = 0.0
        return results
