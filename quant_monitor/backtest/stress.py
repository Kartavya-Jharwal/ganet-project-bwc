"""Historical Stress Testing & Scenario Analysis.

Implements replay models for exogenous shocks (e.g., 2008 Financial Crisis, 2020 COVID).
"""
from __future__ import annotations

import pandas as pd
import numpy as np

def historical_scenario_replay(
    portfolio_weights: pd.Series,
    historical_returns: pd.DataFrame,
) -> dict:
    """Replay a portfolio against a specific historical block of returns.
    
    Args:
        portfolio_weights: Series mapping asset tickers to their fraction of the portfolio.
        historical_returns: DataFrame where rows are dates, cols are asset returns.
            This DataFrame should be pre-filtered to the stress period (e.g., Q1 2020).
            
    Returns:
        Dictionary containing max_drawdown, total_return, and daily_returns for the period.
    """
    if historical_returns.empty or portfolio_weights.empty:
        return {"max_drawdown": 0.0, "total_return": 0.0, "daily_returns": pd.Series()}
        
    # Align assets in case of missing data
    assets = portfolio_weights.index.intersection(historical_returns.columns)
    weights = portfolio_weights[assets]
    # Re-normalize weights to sum to 1 if some assets are missing
    if weights.sum() > 0:
        weights = weights / weights.sum()
        
    returns_slice = historical_returns[assets]
    
    # Calculate daily portfolio returns
    daily_portfolio_returns = returns_slice.dot(weights)
    
    # Calculate cumulative metrics
    cumulative_returns = (1 + daily_portfolio_returns).cumprod()
    total_return = cumulative_returns.iloc[-1] - 1 if len(cumulative_returns) > 0 else 0.0
    
    running_max = cumulative_returns.cummax()
    drawdowns = (running_max - cumulative_returns) / running_max
    max_drawdown = drawdowns.max() if len(drawdowns) > 0 else 0.0
    
    return {
        "total_return": float(total_return),
        "max_drawdown": float(max_drawdown),
        "daily_returns": daily_portfolio_returns
    }

def define_stress_scenarios() -> dict[str, tuple[str, str]]:
    """Get predefined date ranges for common market stress events.
    
    Returns:
        Dict mapping scenario name to (start_date, end_date).
    """
    return {
        "2008_Financial_Crisis": ("2008-09-01", "2009-03-31"),
        "2020_COVID_Crash": ("2020-02-19", "2020-03-23"),
        "2022_Inflation_Pivot": ("2022-01-01", "2022-10-31"),
    }
