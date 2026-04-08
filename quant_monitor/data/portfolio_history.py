"""Portfolio History Engine -- single source of truth for real portfolio data.

Parses the transaction CSV, reconstructs daily position snapshots from
the first trade to today, fetches historical OHLCV, and computes the
canonical DataFrames that every downstream consumer needs:

    engine = PortfolioHistoryEngine()
    returns = engine.get_daily_returns()       # pd.Series
    nav     = engine.get_portfolio_nav()        # pd.Series ($1M start)
    weights = engine.get_daily_weights()        # pd.DataFrame (date x ticker)
    bench   = engine.get_benchmark_returns()    # pd.Series (SPY)
    factors = engine.get_factor_returns()       # pd.DataFrame (FF3 + MOM)
    trades  = engine.get_trade_log()            # pd.DataFrame
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_SECTOR_MAP: dict[str, str] = {
    "SPY": "Broad Market",
    "TSM": "AI Infrastructure",
    "MU": "AI Memory",
    "PLTR": "AI Software",
    "AMZN": "E-commerce/Cloud",
    "NVDA": "AI Infrastructure",
    "ITA": "Defense/Aerospace",
    "NBIS": "AI Infrastructure",
    "LMT": "Defense/Space",
    "TGT": "Defensive Retail",
    "XLP": "Staples",
    "PG": "FMCG Defensive",
    "JNJ": "Healthcare",
    "XLU": "Utilities",
    "IONQ": "Quantum/Speculative",
    "XLE": "Energy",
    "XOM": "Energy",
    "GOOGL": "Big Tech/AI",
    "GE": "Industrial/Aerospace",
    "JPM": "Financials",
    "WMT": "Defensive Retail",
    "IBB": "Healthcare",
    "ORCL": "Software",
    "SIEGY": "Industrials/Infrastructure",
}


def _parse_dollar(val: str) -> float:
    """Convert '$1,234.56' or '-$1,234.56' or '"$1,234.56"' to float."""
    s = str(val).replace('"', "").replace(",", "").strip()
    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        return float(s)
    except ValueError:
        return 0.0


class PortfolioHistoryEngine:
    """Reconstructs the full portfolio history from the transaction CSV."""

    def __init__(
        self,
        csv_path: str | Path | None = None,
        initial_capital: float | None = None,
        benchmark: str | None = None,
    ) -> None:
        from quant_monitor.config import cfg

        if csv_path is None:
            csv_path = cfg.project.get(
                "trade_history", "tests/test_data/TransactionHistory_2026-03-13.csv"
            )
        self._csv_path = Path(csv_path)
        self._initial_capital = initial_capital or cfg.initial_capital
        self._benchmark = benchmark or cfg.benchmark

        self._trade_log: pd.DataFrame | None = None
        self._prices: pd.DataFrame | None = None
        self._nav: pd.Series | None = None
        self._daily_returns: pd.Series | None = None
        self._daily_weights: pd.DataFrame | None = None
        self._benchmark_returns: pd.Series | None = None
        self._factor_returns: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Trade log parsing
    # ------------------------------------------------------------------

    def get_trade_log(self) -> pd.DataFrame:
        """Parse the transaction CSV into a clean DataFrame."""
        if self._trade_log is not None:
            return self._trade_log

        df = pd.read_csv(self._csv_path)

        records = []
        for _, row in df.iterrows():
            symbol = str(row["Symbol"]).strip()
            tx_type = str(row["TransactionType"]).strip()
            qty = int(row["Quantity"])
            price = _parse_dollar(row["Price"])
            amount = _parse_dollar(row["Amount"])
            date_str = str(row["CreateDate"]).strip()
            dt = pd.to_datetime(date_str, format="%m/%d/%Y - %H:%M")

            if "Buy" in tx_type:
                action = "BUY"
            elif "Sell" in tx_type:
                action = "SELL"
            elif "Dividend" in tx_type:
                action = "DIVIDEND"
            else:
                action = tx_type

            records.append(
                {
                    "date": dt.normalize(),
                    "datetime": dt,
                    "symbol": symbol,
                    "action": action,
                    "qty": abs(qty),
                    "price": price,
                    "amount": amount,
                    "sector": _SECTOR_MAP.get(symbol, "Other"),
                }
            )

        self._trade_log = (
            pd.DataFrame(records).sort_values("datetime").reset_index(drop=True)
        )
        return self._trade_log

    # ------------------------------------------------------------------
    # Historical prices
    # ------------------------------------------------------------------

    def _fetch_prices(self) -> pd.DataFrame:
        """Fetch historical close prices for every ticker that ever appeared."""
        if self._prices is not None:
            return self._prices

        trades = self.get_trade_log()
        all_tickers = sorted(set(trades["symbol"].unique()) | {self._benchmark})
        start_date = trades["date"].min() - pd.Timedelta(days=5)

        try:
            import yfinance as yf

            data = yf.download(
                list(all_tickers),
                start=start_date.strftime("%Y-%m-%d"),
                auto_adjust=True,
                progress=False,
            )
            if isinstance(data.columns, pd.MultiIndex):
                prices = data["Close"]
            else:
                prices = data[["Close"]].rename(columns={"Close": all_tickers[0]})
        except Exception as e:
            logger.error("yfinance download failed: %s", e)
            prices = pd.DataFrame()

        prices = prices.ffill().bfill()
        self._prices = prices
        return self._prices

    # ------------------------------------------------------------------
    # Position reconstruction
    # ------------------------------------------------------------------

    def _reconstruct_positions(self) -> tuple[pd.DataFrame, pd.Series]:
        """Reconstruct daily position quantities and cash from trade log.

        Returns (positions_df, cash_series) where positions_df has columns
        per ticker and rows per business day.
        """
        trades = self.get_trade_log()
        prices = self._fetch_prices()

        bdays = pd.bdate_range(
            start=trades["date"].min(),
            end=pd.Timestamp.now().normalize(),
        )
        bdays = bdays[bdays.isin(prices.index) | (bdays <= prices.index.max())]
        bdays = bdays.intersection(prices.index)

        all_tickers = sorted(
            set(trades["symbol"].unique()) - {self._benchmark}
        )

        positions = pd.DataFrame(0.0, index=bdays, columns=all_tickers)
        cash = pd.Series(self._initial_capital, index=bdays, dtype=float)

        current_pos: dict[str, float] = {}
        current_cash = self._initial_capital
        dividend_total = 0.0

        sorted_trades = trades.sort_values("datetime")

        for day in bdays:
            day_trades = sorted_trades[sorted_trades["date"] == day]
            for _, t in day_trades.iterrows():
                sym = t["symbol"]
                if t["action"] == "BUY":
                    current_pos[sym] = current_pos.get(sym, 0) + t["qty"]
                    current_cash += t["amount"]  # amount is negative for buys
                elif t["action"] == "SELL":
                    current_pos[sym] = current_pos.get(sym, 0) - t["qty"]
                    current_cash += t["amount"]  # amount is positive for sells
                    if current_pos.get(sym, 0) <= 0:
                        current_pos.pop(sym, None)
                elif t["action"] == "DIVIDEND":
                    current_cash += t["amount"]
                    dividend_total += t["amount"]

            for sym, qty in current_pos.items():
                if sym in positions.columns:
                    positions.loc[day, sym] = qty
            cash.loc[day] = current_cash

        return positions, cash

    # ------------------------------------------------------------------
    # NAV and returns
    # ------------------------------------------------------------------

    def get_portfolio_nav(self) -> pd.Series:
        """Daily portfolio NAV (Net Asset Value) from $1M start."""
        if self._nav is not None:
            return self._nav

        positions, cash = self._reconstruct_positions()
        prices = self._fetch_prices()

        nav_values = []
        for day in positions.index:
            if day not in prices.index:
                continue
            equity = 0.0
            for ticker in positions.columns:
                qty = positions.loc[day, ticker]
                if qty > 0 and ticker in prices.columns:
                    px = prices.loc[day, ticker]
                    if pd.notna(px):
                        equity += qty * px
            nav_values.append(equity + cash.loc[day])

        valid_days = [d for d in positions.index if d in prices.index]
        self._nav = pd.Series(nav_values, index=valid_days, name="portfolio_nav")
        return self._nav

    def get_daily_returns(self) -> pd.Series:
        """Daily simple returns of the portfolio."""
        if self._daily_returns is not None:
            return self._daily_returns

        nav = self.get_portfolio_nav()
        self._daily_returns = nav.pct_change().dropna().rename("daily_returns")
        return self._daily_returns

    # ------------------------------------------------------------------
    # Weights
    # ------------------------------------------------------------------

    def get_daily_weights(self) -> pd.DataFrame:
        """Daily position weights (market value / NAV) for each ticker."""
        if self._daily_weights is not None:
            return self._daily_weights

        positions, cash = self._reconstruct_positions()
        prices = self._fetch_prices()
        nav = self.get_portfolio_nav()

        weights = pd.DataFrame(0.0, index=nav.index, columns=positions.columns)
        for day in nav.index:
            if day not in prices.index or nav.loc[day] == 0:
                continue
            for ticker in positions.columns:
                qty = positions.loc[day, ticker]
                if qty > 0 and ticker in prices.columns:
                    px = prices.loc[day, ticker]
                    if pd.notna(px):
                        weights.loc[day, ticker] = (qty * px) / nav.loc[day]

        # Add cash weight
        weights["CASH"] = 0.0
        for day in nav.index:
            if nav.loc[day] > 0:
                weights.loc[day, "CASH"] = cash.loc[day] / nav.loc[day]

        self._daily_weights = weights
        return self._daily_weights

    def get_sector_weights(self) -> pd.DataFrame:
        """Daily sector-level weights."""
        weights = self.get_daily_weights()
        sector_weights = pd.DataFrame(0.0, index=weights.index, columns=[])

        for ticker in weights.columns:
            if ticker == "CASH":
                sector = "Cash"
            else:
                sector = _SECTOR_MAP.get(ticker, "Other")
            if sector not in sector_weights.columns:
                sector_weights[sector] = 0.0
            sector_weights[sector] += weights[ticker]

        return sector_weights

    # ------------------------------------------------------------------
    # Benchmark
    # ------------------------------------------------------------------

    def get_benchmark_returns(self) -> pd.Series:
        """Daily returns for the benchmark (SPY)."""
        if self._benchmark_returns is not None:
            return self._benchmark_returns

        prices = self._fetch_prices()
        if self._benchmark in prices.columns:
            bench = prices[self._benchmark].pct_change().dropna()
            port_returns = self.get_daily_returns()
            bench = bench.reindex(port_returns.index).fillna(0)
            self._benchmark_returns = bench.rename("benchmark_returns")
        else:
            self._benchmark_returns = pd.Series(
                dtype=float, name="benchmark_returns"
            )

        return self._benchmark_returns

    # ------------------------------------------------------------------
    # Factor returns (FF3 + MOM via ETF proxies)
    # ------------------------------------------------------------------

    def get_factor_returns(self) -> pd.DataFrame:
        """Fama-French factor returns approximated via ETF proxies.

        MKT-RF ~ SPY returns - 3M T-bill rate (approximated)
        SMB    ~ IWM - SPY  (small minus big)
        HML    ~ IWD - IWF  (value minus growth)
        MOM    ~ MTUM returns (momentum factor ETF)
        """
        if self._factor_returns is not None:
            return self._factor_returns

        port_returns = self.get_daily_returns()
        start = port_returns.index.min() - pd.Timedelta(days=5)

        try:
            import yfinance as yf

            etfs = yf.download(
                ["SPY", "IWM", "IWD", "IWF", "MTUM"],
                start=start.strftime("%Y-%m-%d"),
                auto_adjust=True,
                progress=False,
            )
            if isinstance(etfs.columns, pd.MultiIndex):
                closes = etfs["Close"]
            else:
                closes = etfs

            rets = closes.pct_change().dropna()
            rf_daily = 0.04 / 252  # ~4% annualized risk-free proxy

            factors = pd.DataFrame(index=rets.index)
            factors["MKT-RF"] = rets["SPY"] - rf_daily
            factors["SMB"] = rets["IWM"] - rets["SPY"]
            factors["HML"] = rets["IWD"] - rets["IWF"]
            factors["MOM"] = rets.get("MTUM", rets["SPY"] * 0)  # fallback
            factors["RF"] = rf_daily

            factors = factors.reindex(port_returns.index).fillna(0)
            self._factor_returns = factors
        except Exception as e:
            logger.warning("Factor return fetch failed: %s -- using zeros", e)
            self._factor_returns = pd.DataFrame(
                0.0,
                index=port_returns.index,
                columns=["MKT-RF", "SMB", "HML", "MOM", "RF"],
            )

        return self._factor_returns

    # ------------------------------------------------------------------
    # Convenience: all metrics in one call
    # ------------------------------------------------------------------

    def compute_all_metrics(self) -> dict[str, float]:
        """Compute the full suite of risk/return metrics from real data."""
        from quant_monitor.backtest.metrics import (
            calmar_ratio,
            conditional_var,
            cornish_fisher_var,
            max_drawdown,
            sharpe_ratio,
            sortino_ratio,
            tail_ratio,
            drawdown_duration,
        )

        returns = self.get_daily_returns()
        nav = self.get_portfolio_nav()
        bench = self.get_benchmark_returns()

        if returns.empty:
            return {}

        total_return = float(nav.iloc[-1] / nav.iloc[0] - 1)
        n_days = len(returns)
        ann_return = float((1 + returns.mean()) ** 252 - 1)
        ann_vol = float(returns.std() * np.sqrt(252))

        # Beta via covariance
        if not bench.empty and len(bench) > 1:
            aligned = pd.DataFrame({"port": returns, "bench": bench}).dropna()
            cov_pb = aligned["port"].cov(aligned["bench"])
            var_b = aligned["bench"].var()
            beta = float(cov_pb / var_b) if var_b > 0 else 1.0
            # Treynor = (ann_return - rf) / beta
            rf = 0.04
            treynor = float((ann_return - rf) / beta) if beta != 0 else 0.0
            # Jensen's alpha = ann_return - (rf + beta * (bench_ann - rf))
            bench_ann = float((1 + aligned["bench"].mean()) ** 252 - 1)
            jensens_alpha = float(ann_return - (rf + beta * (bench_ann - rf)))
        else:
            beta = 1.0
            treynor = 0.0
            jensens_alpha = 0.0

        return {
            "total_return": round(total_return, 6),
            "annualized_return": round(ann_return, 6),
            "annualized_volatility": round(ann_vol, 6),
            "sharpe_ratio": round(sharpe_ratio(returns), 4),
            "sortino_ratio": round(sortino_ratio(returns), 4),
            "calmar_ratio": round(calmar_ratio(returns), 4),
            "max_drawdown": round(max_drawdown(returns), 6),
            "cornish_fisher_var": round(cornish_fisher_var(returns), 6),
            "conditional_var": round(conditional_var(returns), 6),
            "tail_ratio": round(tail_ratio(returns), 4),
            "drawdown_duration_days": drawdown_duration(returns),
            "beta": round(beta, 4),
            "treynor_ratio": round(treynor, 6),
            "jensens_alpha": round(jensens_alpha, 6),
            "n_trading_days": n_days,
            "portfolio_value": round(float(nav.iloc[-1]), 2),
        }

    def run_factor_regression(self) -> dict:
        """Run Fama-French 3-factor + Carhart 4-factor regression on real data."""
        from quant_monitor.models.factor import carhart_4_factor, fama_french_3_factor

        returns = self.get_daily_returns()
        factors = self.get_factor_returns()
        rf = factors.get("RF", 0)
        excess_returns = returns - rf

        aligned = pd.concat([excess_returns, factors], axis=1).dropna()
        if len(aligned) < 10:
            return {"error": "insufficient data"}

        port_excess = aligned["daily_returns"]
        factor_df = aligned[["MKT-RF", "SMB", "HML", "MOM"]]

        ff3 = fama_french_3_factor(port_excess, factor_df)
        c4 = carhart_4_factor(port_excess, factor_df)

        return {
            "ff3_alpha": round(float(ff3.params.get("const", 0)), 6),
            "ff3_beta_mkt": round(float(ff3.params.get("MKT-RF", 0)), 4),
            "ff3_beta_smb": round(float(ff3.params.get("SMB", 0)), 4),
            "ff3_beta_hml": round(float(ff3.params.get("HML", 0)), 4),
            "ff3_r_squared": round(float(ff3.rsquared), 4),
            "c4_alpha": round(float(c4.params.get("const", 0)), 6),
            "c4_beta_mkt": round(float(c4.params.get("MKT-RF", 0)), 4),
            "c4_beta_smb": round(float(c4.params.get("SMB", 0)), 4),
            "c4_beta_hml": round(float(c4.params.get("HML", 0)), 4),
            "c4_beta_mom": round(float(c4.params.get("MOM", 0)), 4),
            "c4_r_squared": round(float(c4.rsquared), 4),
        }

    def run_brinson_attribution(self) -> pd.DataFrame:
        """Run Brinson-Fachler attribution using real sector weights vs SPY."""
        from quant_monitor.backtest.attribution import brinson_fachler_attribution

        weights = self.get_daily_weights()
        prices = self._fetch_prices()
        returns = self.get_daily_returns()

        if returns.empty or weights.empty:
            return pd.DataFrame()

        # Aggregate to sector level for the full period
        sector_port_weights = {}
        sector_port_returns = {}
        tickers_by_sector: dict[str, list[str]] = {}

        for ticker in weights.columns:
            if ticker == "CASH":
                continue
            sector = _SECTOR_MAP.get(ticker, "Other")
            tickers_by_sector.setdefault(sector, []).append(ticker)

        for sector, tickers in tickers_by_sector.items():
            sec_weight = sum(
                weights[t].mean() for t in tickers if t in weights.columns
            )
            sec_return = 0.0
            for t in tickers:
                if t in prices.columns:
                    t_ret = (prices[t].iloc[-1] / prices[t].iloc[0] - 1) if len(prices[t]) > 1 else 0
                    t_weight = weights[t].mean() if t in weights.columns else 0
                    sec_return += t_ret * (t_weight / sec_weight if sec_weight > 0 else 0)
            sector_port_weights[sector] = sec_weight
            sector_port_returns[sector] = sec_return

        # SPY sector weights (approximate using GICS-like breakdown)
        spy_sector_weights = {
            "Broad Market": 0.0,
            "AI Infrastructure": 0.15,
            "AI Memory": 0.02,
            "AI Software": 0.03,
            "E-commerce/Cloud": 0.04,
            "Defense/Aerospace": 0.02,
            "Defense/Space": 0.01,
            "Defensive Retail": 0.03,
            "Staples": 0.06,
            "FMCG Defensive": 0.03,
            "Healthcare": 0.12,
            "Utilities": 0.03,
            "Quantum/Speculative": 0.005,
            "Energy": 0.04,
            "Big Tech/AI": 0.08,
            "Industrial/Aerospace": 0.03,
            "Financials": 0.13,
            "Other": 0.10,
            "Cash": 0.0,
        }

        bench_returns = self.get_benchmark_returns()
        bench_total = float((1 + bench_returns).prod() - 1) if not bench_returns.empty else 0

        # Use benchmark total return as proxy for each sector's benchmark return
        spy_sector_returns = {s: bench_total for s in spy_sector_weights}

        all_sectors = sorted(set(sector_port_weights) | set(spy_sector_weights))
        pw = pd.Series({s: sector_port_weights.get(s, 0) for s in all_sectors})
        pr = pd.Series({s: sector_port_returns.get(s, 0) for s in all_sectors})
        bw = pd.Series({s: spy_sector_weights.get(s, 0) for s in all_sectors})
        br = pd.Series({s: spy_sector_returns.get(s, 0) for s in all_sectors})

        return brinson_fachler_attribution(pw, pr, bw, br)

    def run_monte_carlo(
        self, days_forward: int = 29, num_simulations: int = 10_000
    ) -> tuple[np.ndarray, np.ndarray]:
        """Run Monte Carlo simulation using real historical covariance."""
        from quant_monitor.backtest.simulation import run_monte_carlo_simulation

        prices = self._fetch_prices()
        weights = self.get_daily_weights()

        # Build per-asset returns for assets currently held
        held = [c for c in weights.columns if c != "CASH" and weights[c].iloc[-1] > 0.01]
        if not held:
            return np.array([]), np.array([])

        asset_returns = pd.DataFrame()
        for t in held:
            if t in prices.columns:
                asset_returns[t] = prices[t].pct_change()
        asset_returns = asset_returns.dropna()

        if asset_returns.empty or len(asset_returns) < 20:
            return np.array([]), np.array([])

        return run_monte_carlo_simulation(
            asset_returns,
            days_forward=days_forward,
            num_simulations=num_simulations,
        )
