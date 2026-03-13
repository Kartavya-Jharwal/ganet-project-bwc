"""Advanced Capital Allocation logic.

Implements Risk Parity Constraints and Fractional Kelly Sizing.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from scipy.optimize import minimize

def risk_parity_weights(cov_matrix: pd.DataFrame) -> pd.Series:
    """Calculate Risk Parity / Equal Risk Contribution weights.
    
    Args:
        cov_matrix: nxn covariance matrix of asset returns.
        
    Returns:
        Series of asset weights.
    """
    n = cov_matrix.shape[0]
    
    # Portfolio variance function
    def portfolio_variance(w, cov):
        return w.T @ cov @ w
    
    # Risk contribution of each asset
    def risk_contribution(w, cov):
        port_var = portfolio_variance(w, cov)
        # Marginal Risk Contribution
        mrc = (cov @ w)
        # Total Risk Contribution
        rc = w * mrc
        # Percentage Risk Contribution
        rc_pct = rc / port_var
        return rc_pct
    
    # Objective function: minimize sum of squared differences from equal risk (1/n)
    def objective(w, cov):
        target_rc = np.ones(n) / n
        rc = risk_contribution(w, cov)
        return np.sum((rc - target_rc)**2)
    
    # Constraints: weights sum to 1, no short selling (long only)
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
    bounds = tuple((0.0, 1.0) for _ in range(n))
    
    # Initial guess: equal weights
    w0 = np.ones(n) / n
    
    result = minimize(
        objective, 
        w0, 
        args=(cov_matrix.values,), 
        method='SLSQP', 
        bounds=bounds, 
        constraints=constraints
    )
    
    if result.success:
        return pd.Series(result.x, index=cov_matrix.index)
    else:
        # Fallback to inverse volatility heuristic if optimization fails
        inv_vol = 1.0 / np.sqrt(np.diag(cov_matrix))
        return pd.Series(inv_vol / np.sum(inv_vol), index=cov_matrix.index)

def fractional_kelly_size(
    win_probability: float, 
    win_loss_ratio: float, 
    fraction: float = 0.5
) -> float:
    """Calculate the Kelly Criterion for optimal bet sizing.
    
    Equation: f* = p - (1-p)/b
    Where:
        p = win probability
        b = win/loss ratio (e.g. average win / absolute average loss)
        fraction = Kelly fraction to execute (e.g. 0.5 for Half-Kelly to reduce volatility)
        
    Returns:
        Float representing the optimal fraction of unallocated capital to deploy.
        Clamped between 0.0 and 1.0.
    """
    if win_loss_ratio <= 0:
        return 0.0
        
    q = 1.0 - win_probability
    kelly_pct = win_probability - (q / win_loss_ratio)
    
    adjusted_kelly = kelly_pct * fraction
    
    # Return clamped value [0, 1]
    return float(max(0.0, min(1.0, adjusted_kelly)))
