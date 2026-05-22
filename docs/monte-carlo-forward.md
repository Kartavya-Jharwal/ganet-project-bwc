# Monte Carlo forward projection

**Freeze window:** 21 calendar days from `valuation_date` (`2026-04-10`) to `sunset_date` (`2026-05-01`).

Model: correlated geometric Brownian motion with optional Poisson jump diffusion (`quant_monitor/backtest/simulation.py`), estimated on **16 holdings** from the DuckDB EOD matrix.

## Latest run (post matrix cleanup)

| Statistic | Value |
|-----------|-------|
| Simulations | 10,000 |
| Median terminal return | +1.70% |
| Mean | +1.83% |
| P5 (VaR 95) | −6.40% |
| P95 | +10.63% |
| P(positive) | 63.1% |
| P(loss > 5%) | 9.0% |

!!! note "Data hygiene"
    Legacy SPY proxy rows at the wrong price scale were removed via `scripts/clean_duckdb_prices.py` before this run. See [mc-forward-results.json](mc-forward-results.json) for machine-readable output.

```bash
uv run python scripts/prep_duckdb_and_sync.py
uv run python scripts/clean_duckdb_prices.py
# Recompute: see scripts in session notes or regenerate via simulation module
```
