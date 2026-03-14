# Ganet - Project BWC (Brownies with White Chocolate)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package%20manager-blueviolet)](https://github.com/astral-sh/uv)
[![CI/CD](https://github.com/Kartavya-Jharwal/ganet-project-bwc/actions/workflows/ci.yml/badge.svg)](https://github.com/Kartavya-Jharwal/ganet-project-bwc/actions)

> **An Institutional-Grade Market Simulation & Topological Forward Tracker.**

## The Narrative & Systemic Pivot
BWC represents an autonomous, highly-defensive quantitative portfolio tracking engine. Originating as a university simulation case study, the architecture pivoted heavily away from naive NLP scraping into a **Zero-Config, Reproducible Math Pipeline**. 

We operate entirely on local structures using **DuckDB**, zero-copy **Polars**, strict **Topological Parity algorithms**, and **Geometric Brownian Motion (GBM)** to mathematically prove risk, track factors (Alpha/Beta orthogonality), and project deep probabilistic Monte Carlo futures until the **Final Data Freeze Boundary (May 1, 2026)**.

## Live Telemetry & GitHub Actions Infrastructure
Because this is built on top of extreme mathematical rigor natively relying on `uv` reproducibility, we deploy utilizing strict security standards:

- 🔒 **Doppler Service Tokens (OIDC):** The pipelines and GitHub Action endpoints pull API secrets directly via ephemeral Doppler Service Tokens bounded to exact configs (e.g. `prd` only) via the Principle of Least Privilege, completely abandoning risky legacy `.env` injections or broad Personal Access Tokens.
- ⚡ **Lightning CI via UV:** All mathematical validation tests—including intense Fama-French stress testing and inverse covariance bounds checks—run dynamically inside CI utilizing heavily-cached `uv` pipelining over Git Actions workflows.
- 📊 **Real-time WebSockets (Appwrite):** The frontend relies on Vercel/Netlify structural scaffolding pushing out an institutional-styled Brutalist HTML tracking surface that subscribes and morphs dynamically via CDN when the core backend fires metric updates.
- 🛠️ **Config-Driven Architecture & Logging:** Every macro assumption (down to the exact Poisson string parameters for Jump Diffusion) lives decoupled inside TOML configurations or Doppler, wired tightly into structured Datadog/Appwrite system logging streams. We do not hide our edge cases; we emit them aggressively.

### Launching the Pipeline Locally
```bash
# 1) Sync dependencies ensuring strict ticker-agnostic scientific reproduciblity
uv sync --frozen

# 2) View configuration (experiment-driven parameters)
cat config.toml

# 3) Sync historical pricing and execute matrices via local engine securely
doppler run -- uv run cli ingest
doppler run -- uv run cli backtest

# 4) Output the Instutional Tearsheet PDF
uv run python scripts/generate_tearsheet.py --benchmark SPY
```

### Rendering the 3Blue1Brown Calculus Architectures
Our visual proofs are driven directly by **Manim**. To prevent repository bloat, we strictly `.gitignore` the computational output arrays (`media/`) but ship highly contextual visual artifacts inside the UI framework mapping ValueAtRisk geometry, Kelly Criterion parables, and Fama-French equilibrium balances.
```bash
uv run python -m manim -pqm docs/scenes.py Scene5_ValueAtRiskSweep
```

## Architecture Layers

```text
┌────────────────────────────────────────────────────────┐
│              LAYER 4: INSTITUTIONAL UI                 │
│ Appwrite WebSockets | Manim Mathematics | Brutalist UI │
├────────────────────────────────────────────────────────┤
│           LAYER 3: THE QUANTITATIVE ENGINE             │
│   GBM Jump Diffusion | Brinson-Fachler | Cornish VaR   │
├────────────────────────────────────────────────────────┤
│           LAYER 2: TOPOLOGICAL REBALANCING             │
│   Sparse Inverse Covariance | HRP | Kelly Criterion    │
├────────────────────────────────────────────────────────┤
│            LAYER 1: ZERO-CONFIG PIPELINE               │
│ Config Logs | DuckDB | Polars | Doppler Service Tokens │
└────────────────────────────────────────────────────────┘
```

## The Endgame Constraint (May 1, 2026)
> *The portfolio simulation has a strict expiration.*

The repository contains `scripts/export_for_archive.py`, which is fundamentally engineered to lock down and freeze all live backend connections marking the project completely static. A physical python failsafe exists within this sequence throwing a `sys.exit(1)` if any developer or CI agent attempts the freeze prior to **May 1, 2026**. This explicitly, aggressively defends the scientific validity of the final 29-day forward Monte Carlo window simulations.

*MIT License — see [LICENSE](LICENSE) for details.*