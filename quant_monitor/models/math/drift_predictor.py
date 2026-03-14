"""Phase 15: Continuous 15-Minute Drift Predictor."""

import logging

import duckdb
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class DriftPredictor:
    def __init__(self, db_path: str = "portfolio.duckdb"):
        self.db_path = db_path

    def _get_60_day_returns(self) -> pd.DataFrame:
        """Fetch past 60 days of returns."""
        conn = duckdb.connect(self.db_path, read_only=True)
        try:
            query = """
                SELECT timestamp::DATE as date, ticker, close
                FROM eod_price_matrix
                WHERE timestamp >= CURRENT_DATE - INTERVAL 90 DAY
            """
            df = conn.execute(query).df()
        except duckdb.CatalogException:
            return pd.DataFrame()
        finally:
            conn.close()

        if df.empty:
            return df

        pivoted = df.pivot_table(index="date", columns="ticker", values="close")
        pivoted = pivoted.ffill().bfill()
        returns = pivoted.pct_change().dropna(how="all").tail(60)
        return returns

    def _extract_rolling_betas(self) -> dict[str, float]:
        """Calculate 60-day historical beta for all assets vs SPY."""
        returns = self._get_60_day_returns()
        if returns.empty or "SPY" not in returns.columns:
            logger.warning("No SPY data available for beta calculation.")
            return {}

        betas = {}
        spy_var = returns["SPY"].var()
        if spy_var == 0:
            return {}

        for ticker in returns.columns:
            if ticker == "SPY":
                betas[ticker] = 1.0
                continue
            cov = returns[ticker].cov(returns["SPY"])
            betas[ticker] = float(cov / spy_var)
        return betas

    def _get_live_spy_ping(self) -> float:
        """Fast un-auth query specifically for SPY spot."""
        try:
            # Setting interval to 1m, period 1d to grab literal spot
            data = yf.download("SPY", period="1d", interval="1m", progress=False)
            if not data.empty:
                return float(
                    data["Close"].iloc[-1].item()
                    if isinstance(data["Close"].iloc[-1], pd.Series)
                    else data["Close"].iloc[-1]
                )
        except Exception as e:
            logger.warning(f"Failed live SPY ping: {e}")
        return 0.0

    def generate_orders(
        self, current_platform_prices: dict[str, float], spy_t_minus_15: float
    ) -> list[str]:
        """
        Generate executed limit string using predicted drift.
        Args:
            current_platform_prices: The prices fetched at T-15.
            spy_t_minus_15: The SPY price from T-15.
        """
        logger.info("Calculating Continuous 15-Minute Drift Predictor targets.")
        betas = self._extract_rolling_betas()
        if not betas:
            return []

        spy_spot = self._get_live_spy_ping()
        if spy_spot == 0.0 or spy_t_minus_15 == 0.0:
            return []

        delta_spy = (spy_spot - spy_t_minus_15) / spy_t_minus_15

        orders = []
        for ticker, t_15_price in current_platform_prices.items():
            beta = betas.get(ticker, 1.0)

            # The Drift Formula: P_target = P_{t-15} * (1 + (beta_i * DeltaSPY_15m))
            p_target = t_15_price * (1 + (beta * delta_spy))

            action = "Buy" if p_target > t_15_price else "Sell"

            # Actionable string format
            order_str = f"[EXECUTABLE LIMIT] Asset: [{ticker}] | Platform Price: [${t_15_price:.2f}] | True Synthesized Market: [${p_target:.2f}] | Action: {action} @ Target"
            orders.append(order_str)

        return orders
