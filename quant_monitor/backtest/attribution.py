"""Brinson-Fachler Performance Attribution.

Decomposes portfolio returns into:
- Allocation Effect (Sector weighting vs Benchmark)
- Selection Effect (Stock picking vs Benchmark Sector Return)
- Interaction Effect (Combined effect)
"""
from __future__ import annotations

import pandas as pd

def brinson_fachler_attribution(
    portfolio_weights: pd.Series,
    portfolio_returns: pd.Series,
    benchmark_weights: pd.Series,
    benchmark_returns: pd.Series
) -> pd.DataFrame:
    """Calculate Brinson-Fachler attribution effects per sector/grouped asset.
    
    Args:
        portfolio_weights (pd.Series): Portfolio weights for each group (e.g. sectors).
        portfolio_returns (pd.Series): Portfolio returns for each group.
        benchmark_weights (pd.Series): Benchmark weights for each group.
        benchmark_returns (pd.Series): Benchmark returns for each group.
        
    Returns:
        pd.DataFrame with 'Allocation', 'Selection', 'Interaction', and 'Total' columns.
    """
    # Align indices
    df = pd.DataFrame({
        'w_p': portfolio_weights,
        'r_p': portfolio_returns,
        'w_b': benchmark_weights,
        'r_b': benchmark_returns
    }).fillna(0)
    
    overall_benchmark_return = (df['w_b'] * df['r_b']).sum()
    
    # Allocation: (w_p - w_b) * (r_b - r_b_overall)
    df['Allocation'] = (df['w_p'] - df['w_b']) * (df['r_b'] - overall_benchmark_return)
    
    # Selection: w_b * (r_p - r_b)
    df['Selection'] = df['w_b'] * (df['r_p'] - df['r_b'])
    
    # Interaction: (w_p - w_b) * (r_p - r_b)
    df['Interaction'] = (df['w_p'] - df['w_b']) * (df['r_p'] - df['r_b'])
    
    df['Total'] = df['Allocation'] + df['Selection'] + df['Interaction']
    
    return df[['Allocation', 'Selection', 'Interaction', 'Total']]
