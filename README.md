# Quant Portfolio Monitor

[![CI](https://github.com/Kartavya-Jharwal/quant-portfolio-monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/Kartavya-Jharwal/quant-portfolio-monitor/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package%20manager-blueviolet)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Autonomous signal generation, risk monitoring, and rebalancing recommendations for a $1M simulated portfolio.**

## Overview

Quant Portfolio Monitor is a 5-layer quantitative trading system built for the BBA Investment Simulation at Hult International Business School London. It monitors 15 positions across AI infrastructure, defense, financials, and defensive sectors, generating buy/hold/trim/exit signals through a dynamic regime-weighted multi-model fusion engine.

**Key differentiators:**
- 🧠 **4-model signal fusion** — Technical, Fundamental, Sentiment (FinBERT), Macro
- 📊 **Dynamic regime weighting** — Hurst exponent-based volatility classifier shifts model weights
- 🔄 **Black-Litterman optimization** — Posterior expected returns with confidence-weighted views
- 🚨 **Autonomous alerts** — Telegram notifications when action thresholds are crossed
- 📈 **Live dashboard** — Streamlit UI for monitoring and presentation

## Quick Start

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- [Doppler CLI](https://docs.doppler.com/docs/install-cli) for secrets management

### Installation

```bash
# Clone the repository
git clone https://github.com/Kartavya-Jharwal/quant-portfolio-monitor.git
cd quant-portfolio-monitor

# Install dependencies
uv sync

# Run with Doppler secrets injection
doppler run -- uv run python -m quant_monitor.main
```

### Development

```bash
# Run tests
uv run pytest tests/ -v

# Lint & format
uv run ruff check .
uv run ruff format .

# Start Streamlit dashboard
doppler run -- uv run streamlit run quant_monitor/dashboard/app.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: AGENT ORCHESTRATOR                            │
│  Decision engine, risk manager, alert dispatcher        │
├─────────────────────────────────────────────────────────┤
│  LAYER 4: SIGNAL FUSION ENGINE                          │
│  Dynamic regime-weighted multi-model arbitration        │
├─────────────────────────────────────────────────────────┤
│  LAYER 3: ANALYSIS MODELS                               │
│  Technical | Fundamental | Sentiment | Macro            │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: FEATURE ENGINEERING                           │
│  MA matrix | Hurst exponent | Vol regimes | NLP         │
├─────────────────────────────────────────────────────────┤
│  LAYER 1: MULTI-SOURCE DATA PIPELINE                    │
│  Pull → Cache → Normalize → Timestamp-align             │
└─────────────────────────────────────────────────────────┘
```

See [docs/architecture.md](docs/architecture.md) for detailed system design.

## Portfolio

| Ticker | Name | Sector | Qty |
|--------|------|--------|-----|
| SPY | SPDR S&P 500 ETF | Broad Market | 295 |
| TSM | Taiwan Semiconductor | AI Infrastructure | 230 |
| MU | Micron Technology | AI Memory | 110 |
| PLTR | Palantir Technologies | AI Software | 388 |
| AMZN | Amazon.com | E-commerce/Cloud | 250 |
| GOOGL | Alphabet Class A | Big Tech/AI | 130 |
| GE | GE Aerospace | Industrial/Aerospace | 140 |
| JPM | JPMorgan Chase | Financials | 150 |
| LMT | Lockheed Martin | Defense/Space | 100 |
| WMT | Walmart Inc | Defensive Retail | 570 |
| XLP | Consumer Staples SPDR | Staples | 875 |
| PG | Procter & Gamble | FMCG Defensive | 235 |
| JNJ | Johnson & Johnson | Healthcare | 260 |
| XLU | Utilities Select SPDR | Utilities | 800 |
| IONQ | IonQ Inc | Quantum/Speculative | 800 |

**Initial Capital:** $1,000,000 | **Benchmark:** SPY | **Beta:** 0.33

## Project Timeline

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Project scaffold & infrastructure | ✅ Complete |
| 1 | Data pipeline (Massive, yfinance, FRED, SEC, News) | ✅ Complete |
| 2 | Feature engineering (MA matrix, Hurst, vol regimes) | 🔄 In Progress |
| 3 | Technical & Macro models | ⬜ Planned |
| 4 | Sentiment model (FinBERT pipeline) | ⬜ Planned |
| 5 | Fundamental model | ⬜ Planned |
| 6 | Signal fusion engine | ⬜ Planned |
| 7 | Agent orchestrator & risk manager | ⬜ Planned |
| 8 | Backtesting framework | ⬜ Planned |
| 9 | Streamlit dashboard | ⬜ Planned |
| 10 | Telegram alerts & deployment | ⬜ Planned |

**Valuation Date:** April 10, 2026 | **Hard Sunset:** May 1, 2026

## Infrastructure

| Component | Service | Purpose |
|-----------|---------|---------|
| Compute | Heroku | Worker + Web dynos |
| Backend | Appwrite Cloud | Database, storage, REST API |
| Scraping | Zyte Scrapy Cloud | SEC EDGAR, Google RSS, price fallback |
| Secrets | Doppler | Environment-aware secret injection |
| CI/CD | GitHub Actions | Lint, test, deploy |
| Docs | GitHub Pages | Post-sunset static archive |

## Documentation

- [Architecture & Design](docs/architecture.md)
- [Design Decisions](docs/design.md)
- [Development Guide](docs/development.md)
- [Phase 0: Scaffold](docs/phase-0-scaffold.md)
- [Performance Report](docs/performance.md) *(populated at sunset)*
- [Backtest Results](docs/backtest-results.md) *(populated at sunset)*

## Contributing

This is a personal academic project. The codebase will be archived after May 1, 2026.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built for Team 5 Investment Simulation — Hult International Business School London*
