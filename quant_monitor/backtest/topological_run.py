import json
import logging
import os

import duckdb
import numpy as np
import pandas as pd
from sklearn.covariance import GraphicalLassoCV
from sklearn.preprocessing import StandardScaler

from quant_monitor.models.math.hrp_sizer import HRPSizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "portfolio.duckdb"


def extract_all_data(db_path: str) -> pd.DataFrame:
    """Extract all available EOD close prices utilizing Polars for fast pivoting."""
    if not os.path.exists(db_path):
        logger.warning(f"Database {db_path} not found. Cannot run Systemic Validation.")
        return pd.DataFrame()

    import polars as pl

    pl_df = pl.DataFrame()
    conn = duckdb.connect(db_path, read_only=True)
    try:
        query = """
            SELECT timestamp::DATE as date, ticker, close
            FROM eod_price_matrix
            ORDER BY date ASC
        """
        pl_df = conn.execute(query).pl()
    except duckdb.CatalogException:
        logger.error("eod_price_matrix missing from DuckDB.")
        return pd.DataFrame()
    finally:
        conn.close()

    if pl_df.is_empty():
        return pd.DataFrame()

    # Utilize Polars blazing fast pivot capabilities
    pl_pivoted = pl_df.pivot(values="close", index="date", on="ticker", aggregate_function="last")

    # Back-fill / Forward-fill in Polars and drop date to yield pure matrix
    pl_pivoted = pl_pivoted.select(
        pl.all().fill_null(strategy="forward").fill_null(strategy="backward")
    )

    # Convert immediately to target Pandas DataFrame format expected by Scikit-Learn
    pivoted = pl_pivoted.to_pandas().set_index("date")
    # Cast date index correctly
    pivoted.index = pd.to_datetime(pivoted.index)
    return pivoted


def compute_drawdown(returns_series: pd.Series) -> float:
    cumulative = (1 + returns_series).cumprod()
    peak = cumulative.expanding(min_periods=1).max()
    drawdown = (cumulative - peak) / peak
    return float(drawdown.min())


def compute_sharpe(returns_series: pd.Series, risk_free_rate=0.0) -> float:
    mean_return = returns_series.mean() * 252
    volatility = returns_series.std() * np.sqrt(252)
    if volatility == 0:
        return 0.0
    return float((mean_return - risk_free_rate) / volatility)


def compute_sortino(returns_series: pd.Series, risk_free_rate=0.0) -> float:
    mean_return = returns_series.mean() * 252
    downside = returns_series[returns_series < 0]
    downside_vol = downside.std() * np.sqrt(252)
    if pd.isna(downside_vol) or downside_vol == 0:
        return 0.0
    return float((mean_return - risk_free_rate) / downside_vol)


def run_backtest():
    """Runs a 21-day step-forward topological backtest, producing metrics."""
    logger.info("Initializing Phase 18 Topological Walk-Forward Backtester...")
    pivoted = extract_all_data(DB_PATH)
    if pivoted.empty:
        logger.error("No historical data to backtest.")
        return

    # We require 252 days for first train window.
    TRAIN_WINDOW = 252
    TEST_WINDOW = 21

    if len(pivoted) < TRAIN_WINDOW + TEST_WINDOW:
        logger.error(f"Insufficient data. Need {TRAIN_WINDOW + TEST_WINDOW}, got {len(pivoted)}")
        return

    naive_returns = []
    hrp_returns = []
    dates_tested = []

    # Filter out columns with all NaN or zeroes
    pivoted = pivoted.dropna(axis=1, how="all")

    start_idx = 0
    while start_idx + TRAIN_WINDOW + TEST_WINDOW <= len(pivoted):
        train_data = pivoted.iloc[start_idx : start_idx + TRAIN_WINDOW]
        test_data = pivoted.iloc[start_idx + TRAIN_WINDOW : start_idx + TRAIN_WINDOW + TEST_WINDOW]

        # 1. Compute Returns & Clean
        returns = np.log(train_data / train_data.shift(1)).dropna(how="all")
        returns = returns.fillna(0.0)
        tickers = list(returns.columns)

        # Naive Equal Weight
        test_daily_returns = test_data.pct_change().fillna(0.0)
        naive_w = np.ones(len(tickers)) / len(tickers)
        naive_port_returns = test_daily_returns.dot(naive_w)
        naive_returns.extend(naive_port_returns.tolist())
        dates_tested.extend(test_daily_returns.index.tolist())

        try:
            # 2. Topology / Covariance
            scaler = StandardScaler()
            scaled_returns = scaler.fit_transform(returns)
            np.clip(scaled_returns, -5.0, 5.0, out=scaled_returns)

            model = GraphicalLassoCV(cv=3, max_iter=500, verbose=False, n_jobs=1)
            model.fit(scaled_returns)

            precision = model.precision_
            d = np.diag(precision)
            d_inv_sqrt = np.diag(1.0 / np.sqrt(np.clip(d, a_min=1e-12, a_max=None)))
            partial_corr = -(d_inv_sqrt @ precision @ d_inv_sqrt)
            np.fill_diagonal(partial_corr, 1.0)

            # Simple Variance estimate (proxy for ATR variance)
            variances = returns.var().values

            # 3. HRP Sizing
            sizer = HRPSizer(partial_corr, tickers, variances)
            weights_dict = sizer.allocate()

            # Convert to vector for test
            hrp_w = np.array([weights_dict.get(t, 0.0) for t in tickers])

            hrp_port_returns = test_daily_returns.dot(hrp_w)
            hrp_returns.extend(hrp_port_returns.tolist())

        except Exception as e:
            logger.warning(f"Lasso failed at index {start_idx}: {e}. Falling back to Naive.")
            hrp_returns.extend(naive_port_returns.tolist())

        start_idx += TEST_WINDOW
        logger.info(f"Stepped forward 21 days... (Current index: {start_idx})")

    # Final stats computation
    naive_series = pd.Series(naive_returns, index=dates_tested)
    hrp_series = pd.Series(hrp_returns, index=dates_tested)

    metrics = {
        "naive_equal_weight": {
            "total_return": float((1 + naive_series).prod() - 1),
            "annualized_sharpe": compute_sharpe(naive_series),
            "annualized_sortino": compute_sortino(naive_series),
            "max_drawdown": compute_drawdown(naive_series),
        },
        "topological_hrp": {
            "total_return": float((1 + hrp_series).prod() - 1),
            "annualized_sharpe": compute_sharpe(hrp_series),
            "annualized_sortino": compute_sortino(hrp_series),
            "max_drawdown": compute_drawdown(hrp_series),
        },
        "delta": {
            "sharpe_improvement": compute_sharpe(hrp_series) - compute_sharpe(naive_series),
            "drawdown_reduction": compute_drawdown(naive_series) - compute_drawdown(hrp_series),
        },
        "windows_tested": len(naive_series) // TEST_WINDOW,
    }

    # Dump for Phase 21 rendering
    os.makedirs("docs", exist_ok=True)
    with open("docs/backtest-results.json", "w") as f:
        json.dump(metrics, f, indent=4)

    logger.info("Systemic Validation Complete! Results saved to docs/backtest-results.json")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    run_backtest()
