"""Factor Regression Models.

Implements Fama-French 3-Factor, Carhart 4-Factor, and q-Factor (Hou-Xue-Zhang) models.
"""
from __future__ import annotations

import pandas as pd
import statsmodels.api as sm

def fama_french_3_factor(portfolio_returns: pd.Series, factors: pd.DataFrame) -> sm.regression.linear_model.RegressionResultsWrapper:
    """Fama-French 3-Factor Model.
    
    Args:
        portfolio_returns: Series of portfolio returns minus risk-free rate.
        factors: DataFrame containing 'MKT-RF', 'SMB', 'HML' columns.
        
    Returns:
        Fitted OLS model.
    """
    X = factors[['MKT-RF', 'SMB', 'HML']]
    X = sm.add_constant(X)
    model = sm.OLS(portfolio_returns, X)
    results = model.fit()
    return results

def carhart_4_factor(portfolio_returns: pd.Series, factors: pd.DataFrame) -> sm.regression.linear_model.RegressionResultsWrapper:
    """Carhart 4-Factor Model.
    
    Args:
        portfolio_returns: Series of portfolio returns minus risk-free rate.
        factors: DataFrame containing 'MKT-RF', 'SMB', 'HML', 'MOM' columns.
        
    Returns:
        Fitted OLS model.
    """
    X = factors[['MKT-RF', 'SMB', 'HML', 'MOM']]
    X = sm.add_constant(X)
    model = sm.OLS(portfolio_returns, X)
    results = model.fit()
    return results

def q_factor_model(portfolio_returns: pd.Series, factors: pd.DataFrame) -> sm.regression.linear_model.RegressionResultsWrapper:
    """Hou-Xue-Zhang q-Factor Model.
    
    Args:
        portfolio_returns: Series of portfolio returns minus risk-free rate.
        factors: DataFrame containing 'MKT-RF', 'ME', 'IA', 'ROE' columns.
            ME (Size), IA (Investment), ROE (Profitability).
            
    Returns:
        Fitted OLS model.
    """
    X = factors[['MKT-RF', 'ME', 'IA', 'ROE']]
    X = sm.add_constant(X)
    model = sm.OLS(portfolio_returns, X)
    results = model.fit()
    return results
