"""Monte Carlo Forward Simulation for Portfolio.

Implements correlated Geometric Brownian Motion (GBM) with Jump Diffusion.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def run_monte_carlo_simulation(
    historical_returns: pd.DataFrame,
    days_forward: int = 29,
    num_simulations: int = 10000,
    jump_diffusion: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Run a Monte Carlo simulation using Cholesky Decomposition.

    Args:
        historical_returns: DataFrame of historical daily returns for N assets.
        days_forward: Number of days to simulate.
        num_simulations: Number of parallel paths.
        jump_diffusion: Whether to include Poisson jump diffusion.

    Returns:
        Tuple of (portfolio_simulated_paths, terminal_values)
        portfolio_simulated_paths: (num_simulations x days_forward) aggregate portfolio return
        terminal_values: (num_simulations,) array of total returns after days_forward
    """
    if historical_returns.empty:
        return np.array([]), np.array([])

    num_assets = historical_returns.shape[1]

    # Calculate empirical mean and covariance
    mu = historical_returns.mean().values
    cov = historical_returns.cov().values

    try:
        # Cholesky decomposition to maintain exact cross-asset correlation
        L = np.linalg.cholesky(cov)
    except np.linalg.LinAlgError:
        # Fallback if not positive definite (add small ridge)
        cov = cov + np.eye(num_assets) * 1e-6
        L = np.linalg.cholesky(cov)

    paths = np.zeros((num_simulations, days_forward, num_assets))

    for t in range(days_forward):
        # Base GBM (Standard Normal) (num_simulations x num_assets)
        Z = np.random.standard_normal((num_simulations, num_assets))

        # Apply Cholesky
        correlated_shocks = Z.dot(L.T)

        step_returns = mu + correlated_shocks

        if jump_diffusion:
            # Simple Poisson jump diffusion
            # Assume jumps happen ~1% of days, with a larger variance
            jumps = np.random.poisson(lam=0.01, size=(num_simulations, num_assets))
            jump_sizes = np.random.normal(-0.02, 0.05, size=(num_simulations, num_assets))
            step_returns += jumps * jump_sizes

        paths[:, t, :] = step_returns

    # Assume equal weight for simplicity of output, or user can apply custom weights
    weights = np.ones(num_assets) / num_assets

    # Calculate daily portfolio returns
    portfolio_daily_returns = np.sum(paths * weights, axis=2)

    # Calculate cumulative paths (wealth multipliers)
    cumulative_paths = np.cumprod(1 + portfolio_daily_returns, axis=1)

    terminal_values = cumulative_paths[:, -1] - 1  # Total return

    return portfolio_daily_returns, terminal_values
