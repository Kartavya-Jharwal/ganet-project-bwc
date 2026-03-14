"""Modern backtest metrics to prevent overfitting.

Implements Probabilistic Sharpe Ratio (PSR), Deflated Sharpe Ratio (DSR), and PBO stubs.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import norm


def probabilistic_sharpe_ratio(
    returns: pd.Series, benchmark_sharpe: float = 0.0, risk_free_rate: float = 0.0
) -> float:
    """Calculates the Probabilistic Sharpe Ratio (PSR).

    PSR = Z[ (SR - SR*) * sqrt(T-1) / sqrt(1 - gamma_3*SR + (gamma_4 - 1)/4 * SR^2) ]

    Args:
        returns: Period returns.
        benchmark_sharpe: The target Sharpe ratio to beat (annualized).
        risk_free_rate: Daily risk free rate.

    Returns:
        Probability that the true Sharpe ratio is greater than the benchmark.
    """
    if returns.empty or returns.std() == 0:
        return 0.0

    n = len(returns)
    sr_daily = (returns.mean() - risk_free_rate) / returns.std()
    sr_ann = sr_daily * np.sqrt(252)

    # Skewness and kurtosis of daily returns
    skew = returns.skew()
    kurt = returns.kurtosis() + 3  # scipy kurtosis represents excess kurtosis

    # Standard deviation of the estimated Sharpe ratio
    sr_std = math.sqrt((1 - skew * sr_daily + (kurt - 1) / 4 * sr_daily**2) / (n - 1))
    if sr_std == 0:
        return 1.0 if sr_daily > benchmark_sharpe else 0.0

    # The benchmark SR also evaluated on daily scale
    benchmark_sr_daily = benchmark_sharpe / np.sqrt(252)

    z_stat = (sr_daily - benchmark_sr_daily) / sr_std

    return float(norm.cdf(z_stat))


def deflated_sharpe_ratio(
    returns: pd.Series, num_trials: int, variance_of_trials: float, risk_free_rate: float = 0.0
) -> float:
    """Calculates the Deflated Sharpe Ratio (DSR).

    Adjusts the benchmark Sharpe based on the number of trials using the Expected Maximum Sharpe Ratio.

    Args:
        returns: Period returns.
        num_trials: Non-independent strategy trials evaluated.
        variance_of_trials: Variance of the Sharpe ratios across all trials.
        risk_free_rate: Daily risk free rate.
    """
    if num_trials < 1:
        num_trials = 1

    # Expected maximum Sharpe ratio (Bailey and Lopez de Prado 2014)
    emc = 0.5772156649  # Euler-Mascheroni constant
    expected_max_sr = math.sqrt(variance_of_trials) * (
        (1 - emc) * norm.ppf(1 - 1 / num_trials) + emc * norm.ppf(1 - 1 / (num_trials * math.e))
    )

    return probabilistic_sharpe_ratio(
        returns, benchmark_sharpe=expected_max_sr * np.sqrt(252), risk_free_rate=risk_free_rate
    )


def probability_of_backtest_overfitting(matrix_of_returns: pd.DataFrame) -> float:
    """Calculates Probability of Backtest Overfitting (PBO) via continuous subset combination (proxy).

    Args:
        matrix_of_returns: DataFrame of dimension (T observations x N strategies).
    """
    if matrix_of_returns.shape[1] < 2 or len(matrix_of_returns) < 10:
        return 0.0

    # Execute a simplified symmetric cross validation
    # Split the return dataset into evenly sized partitions
    T, N = matrix_of_returns.shape
    partitions = 4  # e.g., 4 subsets for combinatorial comparison
    if T < partitions:
        return 0.0
        
    subset_size = T // partitions
    subsets = [matrix_of_returns.iloc[i * subset_size:(i + 1) * subset_size] for i in range(partitions)]
    
    # Calculate performance (Sharpe) in in-sample (IS) vs out-of-sample (OOS) pairs
    degradations = 0
    total_comparisons = 0
    
    for i in range(partitions):
        # OOS is the i-th partition
        oos_df = subsets[i]
        
        # IS is the rest
        is_dfs = [subsets[j] for j in range(partitions) if j != i]
        is_df = pd.concat(is_dfs)
        
        # Calculate Sharpe for all strategies IS
        is_sharpes = is_df.mean() / (is_df.std() + 1e-8)
        # Identify the "optimal" IS strategy
        best_strat_is = is_sharpes.idxmax()
        
        # Calculate Sharpe for all strategies OOS
        oos_sharpes = oos_df.mean() / (oos_df.std() + 1e-8)
        
        # Calculate OOS rank of the strategy that was strictly "best" IS
        # If it falls below median, we consider it a degradation
        best_strat_oos_rank = oos_sharpes.rank(ascending=False)[best_strat_is]
        
        if best_strat_oos_rank > (N / 2):
            degradations += 1
            
        total_comparisons += 1

    pbo = degradations / max(total_comparisons, 1)
    return float(pbo)
