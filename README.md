
# Ganet - Project BWC (Brownies with White Chocolate)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package%20manager-blueviolet)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **A museum-grade market simulation and structural topology showcase.**

## The Systemic Pivot
This system underwent a massive architectural pivot (Phases 11-21). It abandoned legacy predictive NLP and heavy cloud deployments (Heroku, rigid CI/CD actions) in favor of a **Zero-Config Local Runbook**. It operates entirely locally using embedded DuckDB, zero-copy Polars, and strict topological mathematics (Sparse Inverse Covariance & Hierarchical Risk Parity). 

Because the project lives and executes locally on your machine, complex GitHub Actions and Doppler secret injection are no longer strictly mandatory to run the core simulation!

## Launching the Demo & Web Showcase
The showcase features Awwwards-level brutalist HTML, PyVis topological graphs, and Manim-generated mathematical storytelling. It is designed to run locally and deploy directly to GitHub Pages effortlessly.

### 1. Local Execution & Data Simulation
```bash
# 1) Sync dependencies entirely locally via uv
uv sync

# 2) Sync historical pricing directly into the local DuckDB (No Doppler required!)
uv run cli ingest

# 3) Run the Out-of-Sample Topological Backtest (Generates the JSON metrics)
uv run cli backtest

# 4) Calculate Live Orders to mitigate the forced 15-minute sim delay
uv run python quant_monitor/main.py
```

### 2. Rendering the Visual Artifacts
```powershell
# Generate the actual Manim simulation mathematical MP4 loops
.\bin\render_manim.ps1
```

### 3. Deploying the Final GUI to GitHub Pages
To "launch" the completed showcase live to the web directly from your local environment:
```bash
# Stage the generated artifacts
git add docs/

# Commit the deployment payload
git commit -m "chore: deploy vanguard showcase and simulation metrics"

# Push to the remote
git push origin main
```
*Note: Ensure your GitHub repository settings under `Settings -> Pages` are configured to deploy from the `/docs` folder on the `main` branch. This serves the `index.html` frontend.*

## Overview
This simulation out-engineers traditional forced latency and diversification illusions by implementing:
- 🕸️ **Sparse Inverse Covariance:** Calculates the true conditional independence graph using Scikit-Learn `GraphicalLassoCV`.
- 🌳 **Minimum Spanning Tree (MST):** Prunes noisy edges to isolate risk hubs and alpha leaves via NetworkX algorithms.
- ⚖️ **Hierarchical Risk Parity (HRP):** Clusters assets dynamically via SciPy and sizes targets inversely to their trailing variance without relying on generic stop-losses.
- ⏱️ **15-Minute Drift Forecaster:** Fires a sub-second live SPY spot ping to synthetically offset the forced 15-minute data reporting delay inherent to standard simulation platforms.

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: VANGUARD SHOWCASE                             │
│  Manim Animations | PyVis D3 Graphs | Brutalist HTML    │
├─────────────────────────────────────────────────────────┤
│  LAYER 3: THE TOPOLOGICAL MATH ENGINE                   │
│  GraphicalLassoCV | HRP Bisection | Centrality Pruning  │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: BLAZING FAST PIPELINES                        │
│  DuckDB Native Storage <-> Zero-Copy Polars Pivoting    │
├─────────────────────────────────────────────────────────┤
│  LAYER 1: ZERO-CONFIG INGESTION                         │
│  yFinance | pandas_market_calendars | OpenBB Sectors    │
└─────────────────────────────────────────────────────────┘
```

## Portfolio Set

| Ticker | Name | Dynamic Sector Resolution (via OpenBB/yFinance) |
|--------|------|-------------------------------------------------|
| SPY | SPDR S&P 500 ETF | Broad Market |
| TSM | Taiwan Semiconductor | AI Infrastructure |
| MU | Micron Technology | AI Memory |
| PLTR | Palantir Technologies | AI Software |
| AMZN | Amazon.com | E-commerce/Cloud |
| GOOGL | Alphabet Class A | Big Tech/AI |
| GE | GE Aerospace | Industrial/Aerospace |
| JPM | JPMorgan Chase | Financials |
| LMT | Lockheed Martin | Defense/Space |
| WMT | Walmart Inc | Defensive Retail |
| XLP | Consumer Staples SPDR | Staples |
| PG | Procter & Gamble | FMCG Defensive |
| JNJ | Johnson & Johnson | Healthcare |
| XLU | Utilities Select SPDR | Utilities |
| IONQ | IonQ Inc | Quantum/Speculative |

## Project Timeline

| Phase | Description | Status |
|-------|-------------|--------|
| 11 | Surgical Pruning & Architecture Pivot | ✅ Complete |
| 12 | DuckDB Zero-Copy Local Caching | ✅ Complete |
| 13 | Weighted Correlation Graph (Lasso CV) | ✅ Complete |
| 14 | Hierarchical Risk Parity (HRP) Engine | ✅ Complete |
| 15 | Continuous Drift Predictor (Latency mitigation) | ✅ Complete |
| 16 | MST Topology Pruning via NetworkX | ✅ Complete |
| 17 | Local Loop Typer CLI Integration | ✅ Complete |
| 18 | Out-of-Sample Systemic Validation Backtests | ✅ Complete |
| 19 | Executive Terminal UI (Rich Tables) | ✅ Complete |
| 20 | Algorithmic Storytelling (Python Manim MP4s) | ✅ Complete |
| 21 | Vanguard HTML Showcase & PyVis Map Deployment | ✅ Complete |

## Documentation

All critical project context currently resides in the generated `docs/index.html` delivery or explicitly within `docs/phase-11-21-implementation-track.md` methodology logs.

Legacy planning/task artifacts have been organized under `docs/tasks/` and historical snapshots/logs under `docs/archive/`.

## License

MIT License — see [LICENSE](LICENSE) for details.

