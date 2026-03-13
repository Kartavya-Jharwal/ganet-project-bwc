"""Tests for modern backtest metrics."""
import pandas as pd
import numpy as np

from quant_monitor.backtest.modern_metrics import probabilistic_sharpe_ratio, deflated_sharpe_ratio, probability_of_backtest_overfitting

def test_probabilistic_sharpe_ratio():
    np.random.seed(42)
    # create 2 years of daily positive returns
    returns = pd.Series(np.random.normal(0.001, 0.01, 500))
    
    psr = probabilistic_sharpe_ratio(returns, benchmark_sharpe=0.0)
    # Should be very high probability
    assert psr > 0.90
    
    # Against a high benchmark Sharpe
    psr_high_bm = probabilistic_sharpe_ratio(returns, benchmark_sharpe=3.0)
    assert psr_high_bm < 0.50

def test_deflated_sharpe_ratio():
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.01, 500))
    
    dsr = deflated_sharpe_ratio(returns, num_trials=100, variance_of_trials=0.5)
    
    # Because of many trials, the benchmark SR will be high, lowering the DSR prob
    assert isinstance(dsr, float)
    assert 0 <= dsr <= 1.0

def test_pbo():
    df = pd.DataFrame(np.random.normal(0, 0.01, size=(100, 10)))
    pbo = probability_of_backtest_overfitting(df)
    assert isinstance(pbo, float)
