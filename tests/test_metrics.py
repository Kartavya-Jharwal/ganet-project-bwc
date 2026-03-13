"""Tests for Phase 22 metrics."""
import pandas as pd
import numpy as np
from scipy.stats import norm

from quant_monitor.backtest.metrics import (
    sortino_ratio,
    kappa_ratio,
    cornish_fisher_var,
    conditional_var,
    tail_ratio,
    drawdown_duration,
)


def test_sortino_ratio():
    returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.04, -0.05])
    # Target return is 0.0
    # Downside: -0.02, -0.01, -0.05
    # Squared: 0.0004, 0.0001, 0.0025 -> mean = 0.001 -> sqrt = 0.031622
    # Mean return: 0.0
    # SR: 0.0
    sr = sortino_ratio(returns)
    assert isinstance(sr, float)


def test_cornish_fisher_var():
    # Simulate a fat-tailed distribution (negative skew)
    # Using np.random or specific values
    returns = pd.Series([-0.10, -0.08, -0.05, 0.01, 0.02, 0.03, 0.01, 0.02, 0.01, 0.01])
    cf_var = cornish_fisher_var(returns)
    assert cf_var > 0
    # Expected normal VaR vs CF VaR
    # Given negative skew, CF VaR should be larger than normal VaR if properly adjusted
    z_c = norm.ppf(0.05)
    normal_var = -(returns.mean() + z_c * returns.std())
    assert cf_var > normal_var, "CF VaR should be higher due to fat tails"


def test_conditional_var():
    returns = pd.Series([-0.10, -0.05, -0.01, 0.01, 0.02, 0.03, 0.04])
    # 5% alpha quantile for 7 values is the worst one (-0.10)
    c_var = conditional_var(returns, alpha=0.15)
    assert c_var > 0
    assert c_var == 0.10, f"Expected 0.10, got {c_var}"


def test_tail_ratio():
    returns = pd.Series([-0.05, -0.02, 0.00, 0.01, 0.02, 0.03, 0.05])
    tr = tail_ratio(returns)
    assert tr > 0


def test_drawdown_duration():
    returns = pd.Series([0.01, -0.02, -0.01, 0.01, 0.04, -0.01, -0.02, -0.03, 0.05])
    # cumulative: 1.01, 0.9898, 0.9799, 0.9897, 1.029, 1.018, 0.998, ...
    dur = drawdown_duration(returns)
    assert dur == 4 # First drawdown stretch is 4 days
