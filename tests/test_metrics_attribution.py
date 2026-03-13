"""Tests for performance attribution."""
import pandas as pd
import numpy as np

from quant_monitor.backtest.attribution import brinson_fachler_attribution

def test_brinson_fachler():
    # Example data
    # Sectors: Tech, Health, Energy
    sectors = ['Tech', 'Health', 'Energy']
    wp = pd.Series([0.5, 0.3, 0.2], index=sectors)
    rp = pd.Series([0.10, 0.05, -0.02], index=sectors)
    
    wb = pd.Series([0.4, 0.4, 0.2], index=sectors)
    rb = pd.Series([0.08, 0.06, -0.01], index=sectors)
    
    attr = brinson_fachler_attribution(wp, rp, wb, rb)
    
    # Check overall return consistency
    portfolio_total = (wp * rp).sum()
    benchmark_total = (wb * rb).sum()
    excess_return = portfolio_total - benchmark_total
    
    assert np.isclose(attr['Total'].sum(), excess_return)
    
    # Check specific calculation for Tech
    overall_bm = benchmark_total  # (0.4*0.08 + 0.4*0.06 + 0.2*-0.01) = 0.032 + 0.024 - 0.002 = 0.054
    # Tech Allocation -> (0.5 - 0.4) * (0.08 - 0.054) = 0.1 * 0.026 = 0.0026
    assert np.isclose(attr.loc['Tech', 'Allocation'], 0.0026)
    
    # Tech Selection -> 0.4 * (0.10 - 0.08) = 0.4 * 0.02 = 0.008
    assert np.isclose(attr.loc['Tech', 'Selection'], 0.008)
    
    # Tech Interaction -> (0.5 - 0.4) * (0.10 - 0.08) = 0.1 * 0.02 = 0.002
    assert np.isclose(attr.loc['Tech', 'Interaction'], 0.002)
    
    # Tech Total -> 0.0026 + 0.008 + 0.002 = 0.0126
    assert np.isclose(attr.loc['Tech', 'Total'], 0.0126)
