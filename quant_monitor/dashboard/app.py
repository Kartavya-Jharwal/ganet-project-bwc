"""Streamlit dashboard — 5 views for portfolio monitoring.

Views:
1. Portfolio Overview — live P/L heatmap, total value, excess return vs SPY
2. Signal Dashboard — per-ticker signal scores, confidence, dominant model
3. Regime Monitor — current macro regime, VIX, DXY, yield curve chart
4. Monte Carlo — 10,000 path simulation to April 10, fan chart + probability table
5. System Health — API feed status, last update timestamps, cache hit rates

Run locally:  doppler run -- uv run streamlit run quant_monitor/dashboard/app.py
Run on Heroku: see Procfile (web dyno)
"""

from __future__ import annotations

import streamlit as st


def main() -> None:
    """Streamlit app entry point."""
    st.set_page_config(
        page_title="Quant Portfolio Monitor",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📊 Quant Portfolio Monitor")
    st.caption("Team 5 Investment Simulation — Hult International Business School")

    # Sidebar navigation
    page = st.sidebar.radio(
        "Navigation",
        [
            "Portfolio Overview",
            "Signal Dashboard",
            "Regime Monitor",
            "Monte Carlo",
            "System Health",
        ],
    )

    if page == "Portfolio Overview":
        _page_portfolio_overview()
    elif page == "Signal Dashboard":
        _page_signal_dashboard()
    elif page == "Regime Monitor":
        _page_regime_monitor()
    elif page == "Monte Carlo":
        _page_monte_carlo()
    elif page == "System Health":
        _page_system_health()


def _page_portfolio_overview() -> None:
    st.header("Portfolio Overview")
    # TODO Phase 9: P/L heatmap, total value, excess return vs SPY
    st.info("Portfolio overview will be implemented in Phase 9")


def _page_signal_dashboard() -> None:
    st.header("Signal Dashboard")
    # TODO Phase 9: Per-ticker signal scores, confidence levels, dominant model
    st.info("Signal dashboard will be implemented in Phase 9")


def _page_regime_monitor() -> None:
    st.header("Regime Monitor")
    # TODO Phase 9: Current macro regime, VIX, DXY, yield curve chart
    st.info("Regime monitor will be implemented in Phase 9")


def _page_monte_carlo() -> None:
    st.header("Monte Carlo Simulation")
    # TODO Phase 9: 10,000 path simulation to April 10
    st.info("Monte Carlo simulation will be implemented in Phase 9")


def _page_system_health() -> None:
    st.header("System Health")
    # TODO Phase 9: API feed status, update timestamps, cache hit rates
    st.info("System health view will be implemented in Phase 9")


if __name__ == "__main__":
    main()
