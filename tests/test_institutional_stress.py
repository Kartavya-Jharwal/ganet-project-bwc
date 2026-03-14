"""Institutional Stress Tests for Quantitative Models.

This suite ensures that the analytics engines can handle pathological data,
edge cases, and mathematically unstable states gracefully without crashing,
which is critical for rigorous academic/institutional environments.
"""

import numpy as np
import pandas as pd

from quant_monitor.backtest.allocation import fractional_kelly_size, risk_parity_weights
from quant_monitor.backtest.attribution import brinson_fachler_attribution

# Target modules
from quant_monitor.backtest.metrics import (
    conditional_var,
    cornish_fisher_var,
    kappa_ratio,
    sortino_ratio,
)
from quant_monitor.backtest.modern_metrics import deflated_sharpe_ratio, probabilistic_sharpe_ratio
from quant_monitor.backtest.simulation import run_monte_carlo_simulation
from quant_monitor.models.factor import fama_french_3_factor


class TestMetricsEdgeCases:
    def test_empty_or_zero_returns(self):
        empty = pd.Series(dtype=float)
        zeros = pd.Series([0.0] * 100)

        # Sortino
        assert sortino_ratio(empty) == 0.0
        assert sortino_ratio(zeros) == 0.0

        # CF VaR
        assert cornish_fisher_var(empty) == 0.0
        assert cornish_fisher_var(zeros) == 0.0

        # CVaR
        assert conditional_var(empty) == 0.0
        assert conditional_var(zeros) == 0.0

    def test_extreme_skew_kurtosis(self):
        # A jump process simulating sudden extreme crash
        returns = pd.Series([0.01] * 99 + [-0.99])
        cf_var = cornish_fisher_var(returns)
        # Should be strictly bounded and not NaN
        assert not np.isnan(cf_var)
        assert cf_var > 0.0

    def test_kappa_ratio_zero_denominator(self):
        # If no returns are below threshold
        returns = pd.Series([0.01, 0.02, 0.03])
        kappa = kappa_ratio(returns, threshold=0.0)
        # Assuming our implementation returns inf or large number safely
        assert kappa == float("inf")


class TestModernMetricsEdgeCases:
    def test_psr_zero_variance(self):
        zeros = pd.Series([0.0] * 100)
        psr = probabilistic_sharpe_ratio(zeros)
        assert psr == 0.0

    def test_dsr_extreme_trials(self):
        returns = pd.Series(np.random.normal(0.001, 0.01, 100))
        dsr_low = deflated_sharpe_ratio(returns, num_trials=1, variance_of_trials=0.1)
        dsr_high = deflated_sharpe_ratio(returns, num_trials=1000000, variance_of_trials=0.1)
        # High selection bias should heavily penalize the ratio
        assert dsr_high < dsr_low

    def test_dsr_invalid_trials(self):
        returns = pd.Series(np.random.normal(0.001, 0.01, 100))
        # Negative or zero trials should gracefully fallback
        dsr = deflated_sharpe_ratio(returns, num_trials=-5, variance_of_trials=0.1)
        assert not np.isnan(dsr)


class TestSimulationEdgeCases:
    def test_singular_covariance_matrix(self):
        # Perfectly collinear assets (will cause Cholesky to fail if not handled)
        returns = pd.DataFrame(
            {
                "A": np.random.normal(0, 0.01, 100),
            }
        )
        returns["B"] = returns["A"] * 2.0  # Perfect linear combination

        # Should gracefully fall back from Cholesky failure via regularization
        paths, terminal = run_monte_carlo_simulation(returns, days_forward=5, num_simulations=10)
        # Paths is aggregated portfolio return, so shape should be (num_simulations, days_forward)
        assert paths.shape == (10, 5)
        assert not np.isnan(terminal).any()

    def test_extreme_volatility(self):
        # Returns that are extremely wild
        returns = pd.DataFrame(
            {
                "A": np.random.normal(0, 5.0, 100),  # 500% daily vol
            }
        )
        paths, terminal = run_monte_carlo_simulation(returns, days_forward=5, num_simulations=10)
        assert not np.isnan(terminal).any()


class TestAllocationEdgeCases:
    def test_risk_parity_singular_cov(self):
        # Perfect correlation
        cov = np.array([[0.01, 0.01], [0.01, 0.01]])
        weights = risk_parity_weights(pd.DataFrame(cov, index=["A", "B"], columns=["A", "B"]))
        assert np.isclose(weights.sum(), 1.0)
        assert not weights.isna().any()

    def test_risk_parity_zero_variance(self):
        # Zero variance asset
        cov = np.array([[0.00, 0.00], [0.00, 0.01]])
        weights = risk_parity_weights(pd.DataFrame(cov, index=["A", "B"], columns=["A", "B"]))
        assert np.isclose(weights.sum(), 1.0)
        assert not weights.isna().any()

    def test_kelly_zero_win_ratio(self):
        assert fractional_kelly_size(0.5, 0.0) == 0.0
        assert fractional_kelly_size(0.5, -1.0) == 0.0

    def test_kelly_guaranteed_loss(self):
        assert fractional_kelly_size(0.0, 10.0) == 0.0


class TestFactorEdgeCases:
    def test_fama_french_multicollinearity(self):
        # Factor perfectly explains returns
        factors = pd.DataFrame(
            {
                "MKT-RF": np.random.normal(0, 0.01, 100),
                "SMB": np.random.normal(0, 0.01, 100),
                "HML": np.random.normal(0, 0.01, 100),
            }
        )
        returns = factors["MKT-RF"]
        res = fama_french_3_factor(returns, factors)
        # Should gracefully resolve without crashing (statsmodels uses pseudoinverse)
        assert np.isclose(res.params["MKT-RF"], 1.0)


class TestAttributionEdgeCases:
    def test_mismatched_indices(self):
        wp = pd.Series([1.0], index=["Tech"])
        rp = pd.Series([0.1], index=["Tech"])

        # Benchmark has different categories
        wb = pd.Series([1.0], index=["Health"])
        rb = pd.Series([0.05], index=["Health"])

        attr = brinson_fachler_attribution(wp, rp, wb, rb)
        # Should handle NaN fills automatically and calculate
        assert "Tech" in attr.index
        assert "Health" in attr.index
        assert not attr.isna().any().any()
