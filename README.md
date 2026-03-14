# Ganet - Project BWC

> A regime-aware quantitative portfolio tracking engine. Built to test structural alpha decay, hierarchical risk parity bisection, and topological model fusion on out-of-sample data.

## Setup
### The Data Layer
BWC relies on a zero-config, reproducible math pipeline. Pricing and macroeconomic data are cached into a structured local **DuckDB** file (`portfolio.duckdb`). Matrix transformations are executed zero-copy via **Polars** ensuring performance over massive structural sets.

### Environment
We utilize `uv` for explicitly-locked dependency management and strict scientific reproducibility. Secrets are managed via decoupled **Doppler** environments.

```bash
# Sync strictly-locked environment
uv sync --frozen

# Ingest historical pricing and execute matrices
doppler run -- uv run cli ingest
```

## Method
### Signals & Features
We employ feature engineering focused on momentum variance, regime shifts, and cross-asset correlations, bypassing noisy NLP scraping for statistically sound baseline metrics.

### Strategy & Topological Fusion
The system conditionally fuses multi-model signals based on macroeconomic regimes:
- **Topological Risk Parity**: Computes sparse inverse covariance graphs (`GraphicalLassoCV`) to map true correlation structures.
- **HRP Allocation**: Calculates risk sizing via Hierarchical Risk Parity cluster bisections.
- **Dynamic Regime-Weighting**: Blends execution vectors conditionally based on ongoing volatility architectures.

### Backtesting Engine
A robust walk-forward simulation engine tests signal decay out-of-sample. It computes advanced metrics:
- Brinson-Fachler attribution arrays
- Cornish-Fisher Value-at-Risk expansions
- Probability of Backtest Overfitting (PBO)
- Geometric Brownian Motion (GBM) Monte Carlo projections

## Results
*(Pending May 2026 Archive Freeze)*
The final out-of-sample forward simulation tracks the model's predictive validity against a live market structure terminating on **May 1, 2026**.
- **OOS Sharpe & Sortino**: Pending final snapshot.
- **Drawdown Resilience**: Preliminary stress tests on 2024-2025 vectors show topological risk parities heavily restricting maximum drawdowns compared to standard benchmark models.

## Behavioural Analysis
The engine natively evaluates algorithmic degradation versus emotional human intervention. By deploying autonomous regime weighting, the system strictly bypasses behavioral biases such as loss aversion and yield chasing.

## Lessons
- **Tooling vs Theory**: Heavy reliance on advanced DevOps pipelines initially obfuscated the underlying quantitative core. A robust statistical model requires highly legible narrative reporting, not just extreme CI/CD coverage.
- **Complexity Decay**: Walk-forward stress tests continually reveal that complex, over-engineered models decay drastically faster out-of-sample compared to simple, robust heuristics systematically sized via HRP logic.

---
*MIT License — see [LICENSE](LICENSE) for details.*