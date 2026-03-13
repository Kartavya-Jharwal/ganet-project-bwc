# Ganet - Project BWC

> Team 5 Investment Simulation — Hult International Business School London

## Overview

Autonomous signal generation, risk monitoring, and rebalancing recommendation system
for a $1,000,000 simulated portfolio on StockTrak.

- **15 positions** across AI infrastructure, defense, financials, and defensives
- **4-model signal fusion** (technical, fundamental, sentiment, macro)
- **Dynamic regime-weighted arbitration** using Hurst exponent volatility classifier
- **Black-Litterman** portfolio optimization with confidence-weighted views

Demo-day status (March 13, 2026): **Executable prototype (YES)** with required secrets configured.

## Documentation

### Getting Started

| Resource | Description |
|----------|-------------|
| [Development Guide](development.md) | Setup, workflow, contributing |
| [Architecture](architecture.md) | System design and data flow |
| [Design Decisions](design.md) | Technology choices and trade-offs |

### Implementation

| Resource | Description |
|----------|-------------|
| [Phase 0: Scaffold](phase-0-scaffold.md) | Project infrastructure setup |
| [Development Roadmap](roadmap.md) | Complete phase-by-phase plan |
| [Demo Day Progress Report](progress-report.md) | Final readiness and capability status |
| [Phase 11-21 Implementation Track](phase-11-21-implementation-track.md) | Evidence-first plan for quant PM positioning |
| [Phase 22+ Advanced Analytics](phase-22-onwards-advanced-analytics.md) | Institutional metrics, Brinson attribution, and Monte Carlo |

### Results *(populated at sunset)*

| Resource | Description |
|----------|-------------|
| [Performance](performance.md) | Final portfolio performance vs benchmark |
| [Backtest Results](backtest-results.md) | Walk-forward validation metrics |
| [Signal History](signals-history.md) | Complete signal log export |

## Quick Stats (March 13 Checkpoint)

| Metric | Value |
|--------|-------|
| Current Capital | ~$982,206 |
| Positions | 18 |
| Cash Reserve | ~19.1% |
| Benchmark | SPY |
| Signal Models | 4 (Tech, Fund, Sent, Macro) |
| Post-Hoc Analytics | Fama-French, Brinson-Fachler, Monte Carlo |

## Timeline

```
Feb 24 ─────────────────────────────────────────────── May 1
   │                                                     │
   ├─ Phase 0-10: Development ────────────────────┤     │
   │                                              │     │
   │                                         Apr 10     │
   │                                      Valuation     │
   │                                                    │
   │                                              May 1 │
   │                                             Sunset │
```

- **Start:** February 24, 2026
- **Valuation Checkpoint:** April 10, 2026
- **Hard Sunset:** May 1, 2026

## Source Code

- **Repository:** [github.com/Kartavya-Jharwal/quant-portfolio-monitor](https://github.com/Kartavya-Jharwal/quant-portfolio-monitor)
- **CI Status:** [![CI](https://github.com/Kartavya-Jharwal/quant-portfolio-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/Kartavya-Jharwal/quant-portfolio-monitor/actions/workflows/ci.yml)

---

*This documentation serves as a permanent archive after the project sunset.*
