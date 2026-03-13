"""Tests for advanced capital allocation."""
import pandas as pd
import numpy as np

from quant_monitor.backtest.allocation import risk_parity_weights, fractional_kelly_size

def test_risk_parity_weights():
    # Construct a sample covariance matrix for 3 assets
    # Asset A is low vol, Asset B is medium, Asset C is high vol
    # Expected: Asset A should have highest weight, C lowest
    cov = np.array([
        [0.01,  0.0,   0.0],
        [0.0,   0.04,  0.0],
        [0.0,   0.0,   0.09]
    ])
    cov_df = pd.DataFrame(cov, index=['A', 'B', 'C'], columns=['A', 'B', 'C'])
    
    weights = risk_parity_weights(cov_df)
    
    assert np.isclose(weights.sum(), 1.0)
    assert weights['A'] > weights['B'] > weights['C']
    assert weights['A'] > 0.5  # With those variances, A will dominate
    
def test_fractional_kelly_size():
    # 60% win rate, 1:1 payout
    p = 0.6
    b = 1.0
    # Expected Full Kelly: 0.6 - (0.4 / 1) = 0.20
    # Half Kelly: 0.10
    
    kf = fractional_kelly_size(p, b, fraction=0.5)
    assert np.isclose(kf, 0.10)
    
    # 50% win rate, 1:1 payout -> Expected: 0
    kf_zero = fractional_kelly_size(0.5, 1.0)
    assert np.isclose(kf_zero, 0.0)
    
    # Losing bet -> Expected clamped to 0
    kf_neg = fractional_kelly_size(0.4, 1.0)
    assert np.isclose(kf_neg, 0.0)
