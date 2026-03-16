"""Behavioural Audit Layer -- Layer 5 of the analytical stack.

Quantifies the behavioural biases revealed by the actual trade history:

- Trade timing analysis: did buys cluster at local highs? sells at lows?
- Disposition effect: tendency to sell winners too early, hold losers too long
- Conviction metrics: position sizing relative to portfolio
- Turnover and activity analysis
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def analyse_trade_timing(
    trade_log: pd.DataFrame, prices: pd.DataFrame, lookback: int = 5
) -> dict:
    """Measure whether buys/sells happened near local extremes.

    For each trade, compare the execution price to the min/max of the
    surrounding `lookback` trading days. A score near 1.0 for buys means
    buying at local highs (bad timing); near 0.0 means buying at lows (good).
    """
    buy_scores: list[float] = []
    sell_scores: list[float] = []

    for _, row in trade_log.iterrows():
        sym = row["symbol"]
        date = row["date"]
        action = row["action"]
        exec_price = row["price"]

        if action not in ("BUY", "SELL") or sym not in prices.columns:
            continue

        window_start = date - pd.Timedelta(days=lookback * 2)
        window_end = date + pd.Timedelta(days=lookback * 2)
        window = prices.loc[window_start:window_end, sym].dropna()

        if len(window) < 3:
            continue

        lo, hi = float(window.min()), float(window.max())
        if hi == lo:
            continue

        # Normalize: 0 = bought at the low, 1 = bought at the high
        score = (exec_price - lo) / (hi - lo)

        if action == "BUY":
            buy_scores.append(score)
        elif action == "SELL":
            sell_scores.append(score)

    avg_buy = float(np.mean(buy_scores)) if buy_scores else 0.5
    avg_sell = float(np.mean(sell_scores)) if sell_scores else 0.5

    return {
        "avg_buy_timing_score": round(avg_buy, 4),
        "avg_sell_timing_score": round(avg_sell, 4),
        "buy_at_highs_pct": round(sum(1 for s in buy_scores if s > 0.7) / max(len(buy_scores), 1), 4),
        "sell_at_lows_pct": round(sum(1 for s in sell_scores if s < 0.3) / max(len(sell_scores), 1), 4),
        "n_buys_analysed": len(buy_scores),
        "n_sells_analysed": len(sell_scores),
        "interpretation": _interpret_timing(avg_buy, avg_sell),
    }


def _interpret_timing(avg_buy: float, avg_sell: float) -> str:
    parts = []
    if avg_buy > 0.65:
        parts.append("Buys tend to cluster near local highs (momentum-chasing bias)")
    elif avg_buy < 0.35:
        parts.append("Buys show good timing near local lows (contrarian entry)")
    else:
        parts.append("Buy timing is neutral relative to local price range")

    if avg_sell < 0.35:
        parts.append("Sells tend to occur near local lows (panic-selling bias)")
    elif avg_sell > 0.65:
        parts.append("Sells show disciplined exit near local highs")
    else:
        parts.append("Sell timing is neutral relative to local price range")

    return "; ".join(parts)


def analyse_disposition_effect(
    trade_log: pd.DataFrame, prices: pd.DataFrame
) -> dict:
    """Measure the disposition effect: selling winners too early, holding losers.

    For each SELL, compute the return from the original BUY price.
    Winners sold quickly vs losers held longer indicates disposition bias.
    """
    buys: dict[str, list[dict]] = {}
    sells_winner_hold: list[float] = []
    sells_loser_hold: list[float] = []

    for _, row in trade_log.iterrows():
        sym = row["symbol"]
        if row["action"] == "BUY":
            buys.setdefault(sym, []).append({
                "date": row["date"],
                "price": row["price"],
                "qty": row["qty"],
            })
        elif row["action"] == "SELL" and sym in buys and buys[sym]:
            entry = buys[sym][0]  # FIFO
            entry_price = entry["price"]
            exit_price = row["price"]
            hold_days = (row["date"] - entry["date"]).days

            if hold_days <= 0:
                continue

            trade_return = (exit_price - entry_price) / entry_price

            if trade_return > 0:
                sells_winner_hold.append(hold_days)
            else:
                sells_loser_hold.append(hold_days)

    avg_winner_hold = float(np.mean(sells_winner_hold)) if sells_winner_hold else 0
    avg_loser_hold = float(np.mean(sells_loser_hold)) if sells_loser_hold else 0

    disposition_ratio = (
        avg_loser_hold / avg_winner_hold if avg_winner_hold > 0 else 0
    )

    return {
        "avg_winner_holding_days": round(avg_winner_hold, 1),
        "avg_loser_holding_days": round(avg_loser_hold, 1),
        "disposition_ratio": round(disposition_ratio, 4),
        "n_winning_sells": len(sells_winner_hold),
        "n_losing_sells": len(sells_loser_hold),
        "interpretation": _interpret_disposition(disposition_ratio),
    }


def _interpret_disposition(ratio: float) -> str:
    if ratio > 1.5:
        return "Strong disposition effect: losers held significantly longer than winners"
    elif ratio > 1.1:
        return "Mild disposition effect: slight tendency to hold losers longer"
    elif ratio > 0.8:
        return "No significant disposition effect detected"
    else:
        return "Reverse disposition: winners held longer (disciplined conviction)"


def analyse_conviction(trade_log: pd.DataFrame, initial_capital: float) -> dict:
    """Measure position sizing conviction from the trade log.

    Analyses how capital was allocated across positions at entry.
    """
    buys = trade_log[trade_log["action"] == "BUY"].copy()
    if buys.empty:
        return {"interpretation": "No buy trades to analyse"}

    buys["cost"] = buys["qty"] * buys["price"]
    buys["pct_of_capital"] = buys["cost"] / initial_capital * 100

    return {
        "avg_position_size_pct": round(float(buys["pct_of_capital"].mean()), 2),
        "max_position_size_pct": round(float(buys["pct_of_capital"].max()), 2),
        "min_position_size_pct": round(float(buys["pct_of_capital"].min()), 2),
        "std_position_size_pct": round(float(buys["pct_of_capital"].std()), 2),
        "n_positions": len(buys),
        "concentration_top3_pct": round(
            float(buys.nlargest(3, "cost")["pct_of_capital"].sum()), 2
        ),
        "interpretation": _interpret_conviction(buys["pct_of_capital"]),
    }


def _interpret_conviction(sizes: pd.Series) -> str:
    cv = float(sizes.std() / sizes.mean()) if sizes.mean() > 0 else 0
    if cv > 0.8:
        return "High conviction dispersion: large bets on select positions"
    elif cv > 0.4:
        return "Moderate conviction: some differentiation in position sizing"
    else:
        return "Low conviction dispersion: near-equal weighting across entries"


def analyse_turnover(trade_log: pd.DataFrame) -> dict:
    """Measure portfolio activity and turnover."""
    if trade_log.empty:
        return {}

    buys = trade_log[trade_log["action"] == "BUY"]
    sells = trade_log[trade_log["action"] == "SELL"]
    dividends = trade_log[trade_log["action"] == "DIVIDEND"]

    date_range = (trade_log["date"].max() - trade_log["date"].min()).days
    weeks = max(date_range / 7, 1)

    return {
        "total_trades": len(buys) + len(sells),
        "total_buys": len(buys),
        "total_sells": len(sells),
        "total_dividends": len(dividends),
        "trades_per_week": round((len(buys) + len(sells)) / weeks, 2),
        "active_days": trade_log["date"].nunique(),
        "date_range_days": date_range,
        "dividend_income": round(float(dividends["amount"].sum()), 2) if not dividends.empty else 0,
    }


def run_full_behavioural_audit(
    trade_log: pd.DataFrame,
    prices: pd.DataFrame,
    initial_capital: float = 1_000_000,
) -> dict:
    """Run the complete behavioural audit and return a structured result."""
    return {
        "timing": analyse_trade_timing(trade_log, prices),
        "disposition": analyse_disposition_effect(trade_log, prices),
        "conviction": analyse_conviction(trade_log, initial_capital),
        "turnover": analyse_turnover(trade_log),
    }
