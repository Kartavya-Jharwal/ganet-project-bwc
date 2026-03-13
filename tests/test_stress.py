"""Tests for historical stress testing."""
import pandas as pd
import numpy as np

from quant_monitor.backtest.stress import historical_scenario_replay, define_stress_scenarios

def test_historical_scenario_replay():
    weights = pd.Series({"AAPL": 0.5, "TLT": 0.5})
    
    # 5 days of returns
    dates = pd.date_range("2020-02-19", periods=5)
    returns = pd.DataFrame({
        "AAPL": [-0.05, -0.02, -0.10, 0.01, -0.05],
        "TLT":  [ 0.01,  0.02,  0.03, -0.01,  0.02]
    }, index=dates)
    
    result = historical_scenario_replay(weights, returns)
    
    # daily returns should be average of AAPL and TLT
    # Day 1: -0.02
    assert np.isclose(result["daily_returns"].iloc[0], -0.02)
    assert result["max_drawdown"] > 0
    assert result["total_return"] < 0

def test_define_stress_scenarios():
    scenarios = define_stress_scenarios()
    assert "2020_COVID_Crash" in scenarios
    assert len(scenarios["2020_COVID_Crash"]) == 2
