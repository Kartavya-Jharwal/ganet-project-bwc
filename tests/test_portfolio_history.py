"""Tests for PortfolioHistoryEngine -- CSV parsing, NAV, returns, weights, metrics."""

from __future__ import annotations

import textwrap
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_CSV = textwrap.dedent("""\
    Symbol,TransactionType,CompanyName,Exchange,Quantity,FXRate,Currency,SecurityType,Price,Amount,CreateDate
    SPY,Market - Buy,SPDR S&P 500 ETF,US,100,1.00,USD,Equities,$500.00,"-$50,000.0000",02/12/2026 - 17:42
    AAPL,Market - Buy,Apple Inc,US,50,1.00,USD,Equities,$200.00,"-$10,000.0000",02/12/2026 - 18:00
    AAPL,Market - Sell,Apple Inc,US,-20,1.00,USD,Equities,$220.00,"$4,400.0000",02/20/2026 - 14:00
    SPY,Dividends,SPDR S&P 500 ETF,US,100,1.00,USD,Equities,$1.50,$150.0000,02/24/2026 - 05:00
""")


@pytest.fixture()
def csv_path(tmp_path: Path) -> Path:
    p = tmp_path / "tx.csv"
    p.write_text(_SAMPLE_CSV, encoding="utf-8")
    return p


def _mock_cfg():
    """Return a lightweight mock of quant_monitor.config.cfg."""
    cfg = MagicMock()
    cfg.project = {}
    cfg.initial_capital = 1_000_000
    cfg.benchmark = "SPY"
    return cfg


def _make_prices(tickers: list[str], start: str, periods: int, base: float = 100.0) -> pd.DataFrame:
    """Deterministic price frame with a slight upward drift."""
    idx = pd.bdate_range(start=start, periods=periods)
    rng = np.random.default_rng(0)
    data = {}
    for t in tickers:
        data[t] = base + np.cumsum(rng.normal(0.2, 1.0, periods))
    return pd.DataFrame(data, index=idx)


# ---------------------------------------------------------------------------
# _parse_dollar
# ---------------------------------------------------------------------------

class TestParseDollar:
    def test_positive(self):
        from quant_monitor.data.portfolio_history import _parse_dollar
        assert _parse_dollar("$1,234.56") == pytest.approx(1234.56)

    def test_negative(self):
        from quant_monitor.data.portfolio_history import _parse_dollar
        assert _parse_dollar("-$50,000.0000") == pytest.approx(-50_000.0)

    def test_quoted(self):
        from quant_monitor.data.portfolio_history import _parse_dollar
        assert _parse_dollar('"$1,234.56"') == pytest.approx(1234.56)

    def test_garbage(self):
        from quant_monitor.data.portfolio_history import _parse_dollar
        assert _parse_dollar("N/A") == 0.0


# ---------------------------------------------------------------------------
# Trade log parsing
# ---------------------------------------------------------------------------

class TestTradeLog:
    @patch("quant_monitor.data.portfolio_history.PortfolioHistoryEngine.__init__", lambda self, **kw: None)
    def _make_engine(self, csv_path: Path):
        from quant_monitor.data.portfolio_history import PortfolioHistoryEngine
        engine = PortfolioHistoryEngine()
        engine._csv_path = csv_path
        engine._initial_capital = 1_000_000
        engine._benchmark = "SPY"
        engine._trade_log = None
        engine._prices = None
        engine._nav = None
        engine._daily_returns = None
        engine._daily_weights = None
        engine._benchmark_returns = None
        engine._factor_returns = None
        return engine

    def test_parses_correct_row_count(self, csv_path: Path):
        engine = self._make_engine(csv_path)
        log = engine.get_trade_log()
        assert len(log) == 4

    def test_actions_classified(self, csv_path: Path):
        engine = self._make_engine(csv_path)
        log = engine.get_trade_log()
        assert set(log["action"]) == {"BUY", "SELL", "DIVIDEND"}

    def test_amounts_parsed(self, csv_path: Path):
        engine = self._make_engine(csv_path)
        log = engine.get_trade_log()
        buy_spy = log[(log["symbol"] == "SPY") & (log["action"] == "BUY")].iloc[0]
        assert buy_spy["amount"] == pytest.approx(-50_000.0)

    def test_sorted_by_datetime(self, csv_path: Path):
        engine = self._make_engine(csv_path)
        log = engine.get_trade_log()
        assert log["datetime"].is_monotonic_increasing

    def test_sector_mapping(self, csv_path: Path):
        engine = self._make_engine(csv_path)
        log = engine.get_trade_log()
        spy_row = log[log["symbol"] == "SPY"].iloc[0]
        assert spy_row["sector"] == "Broad Market"

    def test_caching(self, csv_path: Path):
        engine = self._make_engine(csv_path)
        log1 = engine.get_trade_log()
        log2 = engine.get_trade_log()
        assert log1 is log2


# ---------------------------------------------------------------------------
# Position reconstruction & NAV
# ---------------------------------------------------------------------------

class TestNAV:
    @patch("quant_monitor.data.portfolio_history.PortfolioHistoryEngine.__init__", lambda self, **kw: None)
    def _make_engine(self, csv_path: Path, prices: pd.DataFrame):
        from quant_monitor.data.portfolio_history import PortfolioHistoryEngine
        engine = PortfolioHistoryEngine()
        engine._csv_path = csv_path
        engine._initial_capital = 1_000_000
        engine._benchmark = "SPY"
        engine._trade_log = None
        engine._prices = prices
        engine._nav = None
        engine._daily_returns = None
        engine._daily_weights = None
        engine._benchmark_returns = None
        engine._factor_returns = None
        return engine

    def test_nav_starts_near_initial_capital(self, csv_path: Path):
        prices = _make_prices(["SPY", "AAPL"], "2026-02-10", 30, base=500.0)
        engine = self._make_engine(csv_path, prices)
        nav = engine.get_portfolio_nav()
        assert not nav.empty
        assert nav.iloc[0] > 900_000

    def test_nav_series_monotonic_index(self, csv_path: Path):
        prices = _make_prices(["SPY", "AAPL"], "2026-02-10", 30, base=500.0)
        engine = self._make_engine(csv_path, prices)
        nav = engine.get_portfolio_nav()
        assert nav.index.is_monotonic_increasing

    def test_daily_returns_length(self, csv_path: Path):
        prices = _make_prices(["SPY", "AAPL"], "2026-02-10", 30, base=500.0)
        engine = self._make_engine(csv_path, prices)
        returns = engine.get_daily_returns()
        nav = engine.get_portfolio_nav()
        assert len(returns) == len(nav) - 1

    def test_daily_returns_bounded(self, csv_path: Path):
        prices = _make_prices(["SPY", "AAPL"], "2026-02-10", 30, base=500.0)
        engine = self._make_engine(csv_path, prices)
        returns = engine.get_daily_returns()
        assert returns.abs().max() < 1.0  # no single-day 100% move


# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------

class TestWeights:
    @patch("quant_monitor.data.portfolio_history.PortfolioHistoryEngine.__init__", lambda self, **kw: None)
    def _make_engine(self, csv_path: Path, prices: pd.DataFrame):
        from quant_monitor.data.portfolio_history import PortfolioHistoryEngine
        engine = PortfolioHistoryEngine()
        engine._csv_path = csv_path
        engine._initial_capital = 1_000_000
        engine._benchmark = "SPY"
        engine._trade_log = None
        engine._prices = prices
        engine._nav = None
        engine._daily_returns = None
        engine._daily_weights = None
        engine._benchmark_returns = None
        engine._factor_returns = None
        return engine

    def test_weights_sum_to_one(self, csv_path: Path):
        prices = _make_prices(["SPY", "AAPL"], "2026-02-10", 30, base=500.0)
        engine = self._make_engine(csv_path, prices)
        weights = engine.get_daily_weights()
        row_sums = weights.sum(axis=1)
        np.testing.assert_allclose(row_sums.values, 1.0, atol=0.02)

    def test_cash_column_present(self, csv_path: Path):
        prices = _make_prices(["SPY", "AAPL"], "2026-02-10", 30, base=500.0)
        engine = self._make_engine(csv_path, prices)
        weights = engine.get_daily_weights()
        assert "CASH" in weights.columns


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class TestMetrics:
    @patch("quant_monitor.data.portfolio_history.PortfolioHistoryEngine.__init__", lambda self, **kw: None)
    def _make_engine(self, csv_path: Path, prices: pd.DataFrame):
        from quant_monitor.data.portfolio_history import PortfolioHistoryEngine
        engine = PortfolioHistoryEngine()
        engine._csv_path = csv_path
        engine._initial_capital = 1_000_000
        engine._benchmark = "SPY"
        engine._trade_log = None
        engine._prices = prices
        engine._nav = None
        engine._daily_returns = None
        engine._daily_weights = None
        engine._benchmark_returns = None
        engine._factor_returns = None
        return engine

    def test_compute_all_metrics_keys(self, csv_path: Path):
        prices = _make_prices(["SPY", "AAPL"], "2026-02-10", 30, base=500.0)
        engine = self._make_engine(csv_path, prices)
        metrics = engine.compute_all_metrics()
        expected_keys = {
            "total_return", "annualized_return", "annualized_volatility",
            "sharpe_ratio", "sortino_ratio", "calmar_ratio",
            "max_drawdown", "cornish_fisher_var", "conditional_var",
            "tail_ratio", "drawdown_duration_days", "beta",
            "treynor_ratio", "jensens_alpha", "n_trading_days",
            "portfolio_value",
        }
        assert expected_keys.issubset(metrics.keys())

    def test_metrics_types(self, csv_path: Path):
        prices = _make_prices(["SPY", "AAPL"], "2026-02-10", 30, base=500.0)
        engine = self._make_engine(csv_path, prices)
        metrics = engine.compute_all_metrics()
        for k, v in metrics.items():
            assert isinstance(v, (int, float)), f"{k} should be numeric, got {type(v)}"
