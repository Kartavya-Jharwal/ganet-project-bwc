"""Tests for the behavioural audit module (Layer 5)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_monitor.backtest.behavioural import (
    analyse_conviction,
    analyse_disposition_effect,
    analyse_trade_timing,
    analyse_turnover,
    run_full_behavioural_audit,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def trade_log() -> pd.DataFrame:
    """Minimal trade log with buys, sells, and a dividend."""
    return pd.DataFrame([
        {"date": pd.Timestamp("2026-02-12"), "symbol": "AAPL", "action": "BUY",  "qty": 100, "price": 200.0, "amount": -20_000.0},
        {"date": pd.Timestamp("2026-02-12"), "symbol": "MSFT", "action": "BUY",  "qty": 50,  "price": 400.0, "amount": -20_000.0},
        {"date": pd.Timestamp("2026-02-20"), "symbol": "AAPL", "action": "SELL", "qty": 50,  "price": 220.0, "amount": 11_000.0},
        {"date": pd.Timestamp("2026-03-01"), "symbol": "MSFT", "action": "SELL", "qty": 50,  "price": 380.0, "amount": 19_000.0},
        {"date": pd.Timestamp("2026-02-24"), "symbol": "AAPL", "action": "DIVIDEND", "qty": 100, "price": 0.5, "amount": 50.0},
    ])


@pytest.fixture()
def prices() -> pd.DataFrame:
    """Synthetic daily close prices covering the trade window."""
    idx = pd.bdate_range("2026-02-01", "2026-03-15")
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "AAPL": 200 + np.cumsum(rng.normal(0.3, 2.0, len(idx))),
        "MSFT": 400 + np.cumsum(rng.normal(-0.1, 3.0, len(idx))),
    }, index=idx)


# ---------------------------------------------------------------------------
# Trade timing
# ---------------------------------------------------------------------------

class TestTradeTiming:
    def test_returns_expected_keys(self, trade_log, prices):
        result = analyse_trade_timing(trade_log, prices)
        assert "avg_buy_timing_score" in result
        assert "avg_sell_timing_score" in result
        assert "interpretation" in result

    def test_scores_bounded(self, trade_log, prices):
        result = analyse_trade_timing(trade_log, prices)
        assert 0.0 <= result["avg_buy_timing_score"] <= 1.0
        assert 0.0 <= result["avg_sell_timing_score"] <= 1.0

    def test_counts_match(self, trade_log, prices):
        result = analyse_trade_timing(trade_log, prices)
        assert result["n_buys_analysed"] == 2
        assert result["n_sells_analysed"] == 2


# ---------------------------------------------------------------------------
# Disposition effect
# ---------------------------------------------------------------------------

class TestDisposition:
    def test_returns_expected_keys(self, trade_log, prices):
        result = analyse_disposition_effect(trade_log, prices)
        assert "disposition_ratio" in result
        assert "interpretation" in result

    def test_winner_sell_detected(self, trade_log, prices):
        result = analyse_disposition_effect(trade_log, prices)
        assert result["n_winning_sells"] + result["n_losing_sells"] > 0

    def test_no_sells(self, prices):
        log = pd.DataFrame([
            {"date": pd.Timestamp("2026-02-12"), "symbol": "AAPL", "action": "BUY", "qty": 10, "price": 200.0, "amount": -2000.0},
        ])
        result = analyse_disposition_effect(log, prices)
        assert result["disposition_ratio"] == 0


# ---------------------------------------------------------------------------
# Conviction
# ---------------------------------------------------------------------------

class TestConviction:
    def test_returns_expected_keys(self, trade_log):
        result = analyse_conviction(trade_log, initial_capital=1_000_000)
        assert "avg_position_size_pct" in result
        assert "concentration_top3_pct" in result

    def test_position_sizes_positive(self, trade_log):
        result = analyse_conviction(trade_log, initial_capital=1_000_000)
        assert result["avg_position_size_pct"] > 0

    def test_empty_log(self):
        empty = pd.DataFrame(columns=["date", "symbol", "action", "qty", "price", "amount"])
        result = analyse_conviction(empty, initial_capital=1_000_000)
        assert "interpretation" in result


# ---------------------------------------------------------------------------
# Turnover
# ---------------------------------------------------------------------------

class TestTurnover:
    def test_returns_expected_keys(self, trade_log):
        result = analyse_turnover(trade_log)
        assert "total_trades" in result
        assert "trades_per_week" in result

    def test_counts(self, trade_log):
        result = analyse_turnover(trade_log)
        assert result["total_buys"] == 2
        assert result["total_sells"] == 2
        assert result["total_dividends"] == 1

    def test_dividend_income(self, trade_log):
        result = analyse_turnover(trade_log)
        assert result["dividend_income"] == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# Full audit
# ---------------------------------------------------------------------------

class TestFullAudit:
    def test_all_sections_present(self, trade_log, prices):
        result = run_full_behavioural_audit(trade_log, prices, initial_capital=1_000_000)
        assert set(result.keys()) == {"timing", "disposition", "conviction", "turnover"}
