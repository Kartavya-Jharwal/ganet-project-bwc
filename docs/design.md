# Design Decisions

This document captures the key architectural and design decisions made for the Ganet - Project BWC system, along with the rationale behind each choice.

## Table of Contents

- [Philosophy](#philosophy)
- [Technology Stack](#technology-stack)
- [Data Architecture](#data-architecture)
- [Signal Generation](#signal-generation)
- [Risk Management](#risk-management)
- [Infrastructure](#infrastructure)
- [Trade-offs](#trade-offs)

---

## Philosophy

### Design Principles

1. **Autonomous recommendations, human-confirmed execution**
   - The system does NOT execute trades. StockTrak has no public API.
   - All signals are advisory; final execution is manual.
   - This removes the need for order management complexity.

2. **Forward-looking, not backward-fitting**
   - Walk-forward validation only — no simple backtests.
   - Prevents lookahead bias and overfitting to historical data.

3. **Regime-aware, not one-size-fits-all**
   - Market conditions change. Model weights should change with them.
   - Hurst exponent distinguishes trending from mean-reverting markets.

4. **Confidence-gated actions**
   - High signal + low confidence = HOLD (models disagree).
   - Only act when inter-model agreement exceeds threshold.

5. **Epistemic Honesty via Advanced Analytics**
   - Standard P&L reporting is insufficient. We decompose returns into Allocation, Selection, and Interaction effects using Brinson-Fachler.
   - Forward-looking analysis runs on 10,000-path stochastic Monte Carlo (calibrated to our empirical covariance) to turn hopes into quantified probabilistic forecasts.

6. **Hard sunset planning**
   - Project ends May 1, 2026. All infrastructure choices optimize for this timeline.
   - Post-sunset documentation via GitHub Pages as a permanent, interactive portfolio case study, tightly marrying live tracking with institutional-grade factor regressions.

---

## Technology Stack

### Python Environment: uv over pip/poetry

**Decision:** Use [uv](https://github.com/astral-sh/uv) for package management.

**Rationale:**
- 10-100x faster dependency resolution than pip/poetry
- Single tool replaces venv + pip + pip-tools
- Lockfile (`uv.lock`) ensures reproducible builds
- Native support for dependency groups (dev, test, etc.)
- Active development, backed by Astral (ruff maintainers)

**Trade-off:** Newer tool, less ecosystem documentation than pip.

### Secrets: Doppler over .env files

**Decision:** Use Doppler for all secret management.

**Rationale:**
- Centralized secrets, no risk of committing keys
- Environment-aware (dev/stg/prd configs)
- Same CLI pattern works locally and in production
- Audit trail for secret access
- Free tier sufficient for this project

**Trade-off:** Adds external dependency. Requires `doppler run --` prefix.

### Database: DuckDB over PostgreSQL

**Decision:** Use DuckDB (single-file embedded DB) for local analytics.

**Rationale:**
- No server process to manage
- Excellent for analytical queries (columnar storage)
- Single file (`portfolio.duckdb`) — easy backup/restore
- Fits in 1GB RAM Heroku dyno
- SQL interface familiar to all

**Trade-off:** Not suitable for high-concurrency writes. Fine for single-user system.

### Cache: diskcache over Redis

**Decision:** Use diskcache (SQLite-backed) for API response caching.

**Rationale:**
- No external server needed
- TTL-aware caching built-in
- Persistent across restarts
- Zero infrastructure overhead

**Trade-off:** Not distributed. Fine for single-process system.

### Backend: Appwrite over Firebase/Supabase

**Decision:** Use Appwrite Cloud as the backend-as-a-service layer.

**Rationale:**
- Open-source, self-hostable if needed
- GitHub Education credits ($13/mo for 24 months)
- REST API + Python SDK
- Database, storage, and functions in one platform
- No vendor lock-in

**Trade-off:** Smaller community than Firebase. Documentation less comprehensive.

### Scraping: Zyte Scrapy Cloud over in-process scraping

**Decision:** Offload all web scraping to Zyte Scrapy Cloud.

**Rationale:**
- GitHub Education credits available
- Managed infrastructure for spider scheduling
- Handles rate limiting, retries, proxy rotation
- Keeps Heroku worker focused on signal computation
- Spiders push directly to Appwrite

**Trade-off:** Adds another external service. Latency for scraped data.

### NLP: Local FinBERT over API-based sentiment

**Decision:** Run FinBERT inference locally via HuggingFace transformers.

**Rationale:**
- No per-request API costs
- Full control over model behavior
- Offline capability for development
- FinBERT specifically tuned for financial text

**Trade-off:** Requires torch (~108MB). Slower than API on first load.

### Dashboard: Rich CLI + OpenBB over Streamlit

**Decision:** Use Rich (terminal UI) + OpenBB Platform (financial data toolkit) for the monitoring dashboard, delivered as a CLI tool.

**Rationale:**
- Instant to launch — no browser, no web server, no frontend build
- SSH-friendly — works on headless servers and remote terminal sessions
- Rich provides beautiful tables, panels, live-refresh displays
- OpenBB Platform gives 100+ financial data endpoints (calendar, earnings, profiles)
- Composable — can be called from scheduler, CI, or manual invocation
- Lighter dependency footprint than Streamlit

**Trade-off:** No graphical charts (ASCII histograms instead). For richer viz, consider a future web layer.

### Linting: ruff over black+isort+flake8

**Decision:** Use ruff as the single linting/formatting tool.

**Rationale:**
- 10-100x faster than alternatives
- Replaces black, isort, flake8, pyupgrade in one tool
- Same maintainers as uv (Astral)
- Auto-fix capabilities

**Trade-off:** Newer tool. Some edge cases may differ from black.

---

## Data Architecture

### Multi-Source Strategy

```
Primary → Fallback → Scraped Fallback

Prices:  Alpaca API → yfinance → Scrapy Cloud spider
News:    Alpaca API → Google RSS spider
Filings: SEC EDGAR spider (direct)
Macro:   FRED API (no fallback needed, daily data)
```

**Rationale:**
- No single point of failure for critical data
- Cross-validation catches data quality issues
- Scraped fallback covers API outages

### Caching Strategy

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Real-time prices | 60s | Balance freshness vs API limits |
| Historical prices | 15min | Doesn't change during session |
| News | 30min | New articles don't need instant refresh |
| Macro | 1hr | FRED data is daily anyway |
| Fundamentals | 24hr | Changes quarterly |

### Timestamp Normalization

All timestamps normalized to UTC before storage. Display layer converts to ET for user.

---

## Signal Generation

### Why 4 Models?

Each model captures different market dynamics:

| Model | Captures | Timeframe |
|-------|----------|-----------|
| Technical | Price momentum, support/resistance | Days to weeks |
| Fundamental | Valuation, earnings quality | Quarters |
| Sentiment | News-driven moves, fear/greed | Hours to days |
| Macro | Regime shifts, risk-on/off | Weeks to months |

Single-model systems miss regime changes. Multi-model fusion adapts.

### Why Dynamic Regime Weights?

Static equal weighting assumes all models are equally useful in all conditions. This is false.

| Regime | Technical | Fundamental | Sentiment | Macro |
|--------|-----------|-------------|-----------|-------|
| HIGH_VOL_TREND | 45% | 15% | 30% | 10% |
| LOW_VOL_TREND | 30% | 40% | 15% | 15% |
| CRISIS | 10% | 10% | 20% | 60% |

**Example:** In a crisis (VIX > 30), macro signals dominate. Fundamentals are irrelevant when correlation goes to 1.

### Hurst Exponent: The Key Insight

Most systems use volatility alone. Hurst separates:
- **H > 0.6:** Trending (ride it)
- **H ≈ 0.5:** Random walk (reduce size)
- **H < 0.4:** Mean-reverting (fade extremes)

"Volatile but trending" (high vol, high Hurst) is very different from "volatile and choppy" (high vol, low Hurst).

### Confidence Gating

```
fusion_score = weighted_avg(tech, fund, sent) + macro_adjustment
confidence = 1 - std(tech, fund, sent, macro)

if confidence > 0.65 AND |fusion_score| > 0.35:
    generate_signal()
else:
    HOLD  # Models disagree
```

High signal + low confidence = conflicting views. Better to wait.

---

## Analytics & Epistemic Honesty

### Why Institutional-Grade Analytics?

A standard student simulation reports P&L and basic Sharpe ratios. This repository actively pays homage to true institutional fund architectures (e.g., AQR, BlackRock) by rigorously enforcing **Epistemic Honesty** through a dedicated analytics lifecycle (Phases 22+). 

| Standard Student Approach | Institutional Approach (Project BWC) |
|---------------------------|--------------------------------------|
| **"We made 3%"** | Brinson-Fachler Attribution (Allocation vs. Selection vs. Interaction) |
| **"Our Beta is 1.2"** | Fama-French 3-Factor & Carhart 4-Factor Regression mapping implicit tilts (SMB, HML, MOM) |
| **"Sharpe is 1.5"** | Deflated Sharpe Ratio (DSR), Probability of Backtest Overfitting (PBO), Cornish-Fisher VaR |
| **"We hope to hit +5% by May 1"** | 10,000-path Monte Carlo forward simulation generating probability density curves |

**Rationale:** The simulation data (dates, fills, prices) is real. By layering these models atop our 29-day checkpoint, the repository transitions from a basic project into a documented, mathematically robust portfolio management case study.

---

## Risk Management

### Charter Constraints

From the investment simulation rules:
- Max 10% per single position
- Max 25% per sector
- No shorting

### Dynamic Risk Adjustment

| Regime | Max Position | Max Sector | Target Beta |
|--------|-------------|-----------|------------|
| RISK_ON | 10% | 25% | 0.50 |
| TRANSITION | 8% | 20% | 0.35 |
| CRISIS | 5% | 15% | 0.20 |

In crisis mode, reduce concentration and beta target.

### Kill Switch

Any single position down >15% intraday → immediate Telegram alert.

This bypasses the normal signal cycle for time-critical situations.

---

## Infrastructure

### Why Heroku over DigitalOcean Droplet?

Original plan: $6/mo DO droplet.

**Revised:** Heroku with GitHub Education credits.

**Rationale:**
- Managed platform, no server administration
- Automatic deploys from GitHub
- Easy scaling (just add dynos)
- Better fit for 2-month project lifespan
- "Just delete the app" on May 1

**Trade-off:** Less control. No persistent filesystem (use Appwrite instead).

### Two-Dyno Architecture

```
worker: APScheduler signal loop
```

Dashboard is a Rich CLI tool (`quant-dashboard`) run on-demand, not a web dyno.
Worker runs the signal loop. Dashboard reads from Appwrite when invoked.

### GitHub Pages for Post-Sunset

Project has a hard end date. But the work should persist.

MkDocs-Material generates a static site from Markdown. Pre-sunset export script pulls all data from Appwrite, renders charts, writes to `docs/`. GitHub Pages serves forever.

---

## Trade-offs

### Accepted Limitations

1. **No real-time streaming**
   - Polling every 15 minutes, not WebSocket.
   - Sufficient for medium-term signals.

2. **No multi-user support**
   - Single-user personal tool. No auth complexity.

3. **CPU-only torch**
   - No GPU. FinBERT inference is slow on first call.
   - Acceptable for batch processing, not real-time.

4. **Scrapy Cloud latency**
   - Scraped data has 15-30 minute delay.
   - Price fallback only; primary source is Alpaca.

5. **Limited backtest depth**
   - Walk-forward on 1 year of data.
   - More data would improve statistical significance.

### What We'd Do Differently at Scale

| Current | At Scale |
|---------|----------|
| DuckDB | TimescaleDB or ClickHouse |
| diskcache | Redis Cluster |
| Heroku | Kubernetes on AWS/GCP |
| Rich CLI + OpenBB | React + FastAPI |
| Single process | Celery workers |
| torch CPU | GPU inference server |

But for a 2-month academic project? Current stack is optimal.

---

*Last updated: February 24, 2026*
