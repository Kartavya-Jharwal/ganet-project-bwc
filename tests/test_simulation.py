"""Tests for Monte Carlo Simulation."""

import numpy as np
import pandas as pd

from quant_monitor.backtest.simulation import run_monte_carlo_simulation


def test_run_monte_carlo_simulation():
    np.random.seed(42)
    # 3 assets, 100 days
    historical_returns = pd.DataFrame(
        {
            "A": np.random.normal(0.001, 0.02, 100),
            "B": np.random.normal(0.0005, 0.015, 100),
            "C": np.random.normal(-0.001, 0.03, 100),
        }
    )

    # Induce artificial correlation
    historical_returns["B"] = historical_returns["A"] * 0.5 + np.random.normal(0, 0.01, 100)

    paths, terminal_values = run_monte_carlo_simulation(
        historical_returns, days_forward=10, num_simulations=100, jump_diffusion=True
    )

    assert paths.shape == (100, 10)
    assert terminal_values.shape == (100,)
    assert not np.isnan(terminal_values).any()
