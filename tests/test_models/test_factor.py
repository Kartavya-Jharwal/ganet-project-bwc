"""Tests for factor models."""

import numpy as np
import pandas as pd

from quant_monitor.models.factor import carhart_4_factor, fama_french_3_factor, q_factor_model


def test_fama_french_3_factor():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=100)
    returns = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)
    factors = pd.DataFrame(
        {
            "MKT-RF": np.random.normal(0.001, 0.015, 100),
            "SMB": np.random.normal(0.0, 0.01, 100),
            "HML": np.random.normal(0.0, 0.01, 100),
        },
        index=dates,
    )

    # Portfolio return loosely based on market
    returns = factors["MKT-RF"] * 1.2 + factors["SMB"] * 0.5 + np.random.normal(0, 0.005, 100)

    res = fama_french_3_factor(returns, factors)
    assert "MKT-RF" in res.params
    assert "SMB" in res.params
    assert "HML" in res.params
    assert np.isclose(res.params["MKT-RF"], 1.2, atol=0.1)
    assert np.isclose(res.params["SMB"], 0.5, atol=0.1)


def test_carhart_4_factor():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=100)
    returns = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)
    factors = pd.DataFrame(
        {
            "MKT-RF": np.random.normal(0.001, 0.015, 100),
            "SMB": np.random.normal(0.0, 0.01, 100),
            "HML": np.random.normal(0.0, 0.01, 100),
            "MOM": np.random.normal(0.001, 0.01, 100),
        },
        index=dates,
    )

    returns = factors["MOM"] * 0.8 + np.random.normal(0, 0.005, 100)

    res = carhart_4_factor(returns, factors)
    assert "MOM" in res.params
    assert np.isclose(res.params["MOM"], 0.8, atol=0.1)


def test_q_factor_model():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=100)
    returns = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)
    factors = pd.DataFrame(
        {
            "MKT-RF": np.random.normal(0.001, 0.015, 100),
            "ME": np.random.normal(0.0, 0.01, 100),
            "IA": np.random.normal(0.0, 0.01, 100),
            "ROE": np.random.normal(0.001, 0.01, 100),
        },
        index=dates,
    )

    returns = factors["IA"] * -0.5 + factors["ROE"] * 0.6 + np.random.normal(0, 0.005, 100)

    res = q_factor_model(returns, factors)
    assert "IA" in res.params
    assert "ROE" in res.params
    assert np.isclose(res.params["IA"], -0.5, atol=0.1)
    assert np.isclose(res.params["ROE"], 0.6, atol=0.1)
