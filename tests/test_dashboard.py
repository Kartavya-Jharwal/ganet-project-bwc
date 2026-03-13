"""Tests for Rich CLI dashboard — Phase 9."""

from __future__ import annotations

import pytest


class TestDataLoader:
    """Tests for quant_monitor/dashboard/data_loader.py."""

    def test_load_portfolio_state_returns_required_keys(self):
        from quant_monitor.dashboard.data_loader import load_portfolio_state

        state = load_portfolio_state()
        assert "holdings" in state
        assert "initial_capital" in state
        assert "tickers" in state
        assert isinstance(state["holdings"], dict)
        assert len(state["tickers"]) > 0

    def test_build_holdings_dataframe_empty(self):
        from quant_monitor.dashboard.data_loader import build_holdings_dataframe

        df = build_holdings_dataframe({}, {})
        assert len(df) == 0

    def test_build_holdings_dataframe_computes_pnl(self):
        from quant_monitor.dashboard.data_loader import build_holdings_dataframe

        holdings = {
            "AAPL": {
                "name": "Apple",
                "type": "stock",
                "qty": 10,
                "price_paid": 150.0,
                "sector": "Technology",
                "cost_basis": 1500.0,
            }
        }
        prices = {"AAPL": 170.0}
        df = build_holdings_dataframe(holdings, prices)
        assert len(df) == 1
        assert df.iloc[0]["pnl"] == pytest.approx(200.0)
        assert df.iloc[0]["pnl_pct"] == pytest.approx(200 / 1500 * 100)

    def test_build_holdings_dataframe_uses_cost_when_no_price(self):
        from quant_monitor.dashboard.data_loader import build_holdings_dataframe

        holdings = {
            "MSFT": {
                "name": "Microsoft",
                "type": "stock",
                "qty": 5,
                "price_paid": 400.0,
                "sector": "Technology",
                "cost_basis": 2000.0,
            }
        }
        df = build_holdings_dataframe(holdings, {})  # no prices
        assert df.iloc[0]["pnl"] == pytest.approx(0.0)


class TestCLIEntryPoint:
    """Tests for quant_monitor/dashboard/app.py CLI."""

    def test_main_runs_without_error(self):
        """main() with no args should exit cleanly (may print to console)."""
        from quant_monitor.dashboard.app import main

        # Passing --view health so it fetches minimal data
        main(["--view", "health"])

    def test_render_functions_return_panel(self):
        """Every view renderer should return a rich Panel."""
        from rich.panel import Panel

        from quant_monitor.dashboard.app import VIEW_RENDERERS

        # Only test health — others need live data / network
        panel = VIEW_RENDERERS["health"]()
        assert isinstance(panel, Panel)
