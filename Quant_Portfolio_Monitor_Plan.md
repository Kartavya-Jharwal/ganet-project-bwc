# Quant Portfolio Monitoring System
## Comprehensive Build Plan — Team 5 Investment Simulation

> **Context:** BBA Investment Simulation at Hult International Business School London.
> Portfolio: $1,000,000 simulated capital on StockTrak. April 10, 2026 valuation checkpoint.
> Operator: Solo (team AWOL). No StockTrak API — all execution is manual.
> Purpose: Forward-looking autonomous signal generation, risk monitoring, and rebalancing recommendations.

---

## 1. Portfolio Context

### Current Holdings (as of Feb 24, 2026)

| Ticker | Asset Name | Type | Qty | Price Paid | Sector |
|--------|-----------|------|-----|-----------|--------|
| SPY | SPDR S&P 500 ETF | ETF | 295 | $684.89 | Broad Market |
| TSM | Taiwan Semiconductor ADR | Stock | 230 | $363.94 | AI Infrastructure |
| MU | Micron Technology | Stock | 110 | $408.82 | AI Memory |
| PLTR | Palantir Technologies | Stock | 388 | $131.48 | AI Software |
| AMZN | Amazon.com | Stock | 250 | $200.87 | E-commerce/Cloud |
| GOOGL | Alphabet Class A | Stock | 130 | $302.22 | Big Tech/AI |
| GE | GE Aerospace | Stock | 140 | $329.44 | Industrial/Aerospace |
| JPM | JPMorgan Chase | Stock | 150 | $306.82 | Financials |
| LMT | Lockheed Martin | Stock | 100 | $643.25 | Defense/Space |
| WMT | Walmart Inc | Stock | 570 | $132.95 | Defensive Retail |
| XLP | Consumer Staples SPDR | ETF | 875 | $89.52 | Staples |
| PG | Procter & Gamble | Stock | 235 | $162.45 | FMCG Defensive |
| JNJ | Johnson & Johnson | Stock | 260 | $244.64 | Healthcare |
| XLU | Utilities Select SPDR | ETF | 800 | $45.45 | Utilities |
| IONQ | IonQ Inc | Stock | 800 | $33.60 | Quantum/Speculative |

### Performance Snapshot (Feb 24, 2026)
- **Portfolio Value:** $1,001,255.56
- **Portfolio Return:** +0.13%
- **S&P 500 Benchmark:** -1.87%
- **Excess Return:** +2.00% ✅
- **Portfolio Beta:** 0.331 (low — defensive structure working)
- **Cash Balance:** $53,955.71

### Investment Charter Constraints
- Max 10% per single position
- Max 25% per sector
- 60/40 equity/bond moderate risk profile
- Fundamentals-first, medium-term horizon
- No shorting

---

## 2. System Objectives

This system does NOT execute trades. StockTrak has no public API.

**What it does:**
1. Monitors all 15 positions continuously across multiple data sources
2. Generates buy/hold/trim/exit signals per position
3. Flags macro regime shifts that require portfolio rebalancing
4. Produces daily rebalancing recommendations with confidence scores
5. Alerts via Telegram when action thresholds are crossed
6. Provides a live Streamlit dashboard for monitoring and presentation

**Design principle:** Autonomous recommendations. Human-confirmed execution.

---

## 3. System Architecture

### 5-Layer Stack

```
┌─────────────────────────────────────────────────────┐
│  LAYER 5: AGENT ORCHESTRATOR                        │
│  Decision engine, risk manager, alert dispatcher    │
├─────────────────────────────────────────────────────┤
│  LAYER 4: SIGNAL FUSION ENGINE                      │
│  Dynamic regime-weighted multi-model arbitration    │
├─────────────────────────────────────────────────────┤
│  LAYER 3: ANALYSIS MODELS                           │
│  Technical | Fundamental | Sentiment | Macro        │
├─────────────────────────────────────────────────────┤
│  LAYER 2: FEATURE ENGINEERING                       │
│  MA matrix | Hurst exponent | Vol regimes | NLP     │
├─────────────────────────────────────────────────────┤
│  LAYER 1: MULTI-SOURCE DATA PIPELINE                │
│  Pull → Cache → Normalize → Timestamp-align         │
└─────────────────────────────────────────────────────┘
```

### Repository Structure

```
quant_monitor/
├── main.py                    # APScheduler entry point
├── config.py                  # tickers, weights, thresholds
├── requirements.txt
├── portfolio.duckdb           # entire time-series DB, single file
├── .cache/                    # diskcache API response cache
│
├── data/
│   ├── pipeline.py            # multi-source pull with failover
│   ├── sources/
│   │   ├── alpaca_feed.py     # primary price + news feed
│   │   ├── yfinance_feed.py   # price fallback
│   │   ├── fred_feed.py       # macro (VIX, DXY, yields)
│   │   ├── sec_edgar_feed.py  # 8-K, earnings filings
│   │   └── google_rss_feed.py # broad news sentiment
│   └── cache.py               # diskcache wrapper with TTL config
│
├── features/
│   ├── moving_averages.py     # EMA, SMA, KAMA, VWAP, HMA, MVWAP
│   ├── volatility.py          # realized vol, Hurst exponent, regimes
│   └── sentiment_features.py  # FinBERT scoring, sentiment MA
│
├── models/
│   ├── technical.py           # MA crossovers, RSI, MACD, Bollinger
│   ├── fundamental.py         # top-down screening, valuation ratios
│   ├── sentiment.py           # NLP pipeline, entity extraction
│   └── macro.py               # VIX/yield/DXY regime classifier
│
├── agent/
│   ├── fusion.py              # dynamic regime-weighted signal fusion
│   ├── optimizer.py           # Black-Litterman + MVO rebalancing
│   ├── risk_manager.py        # position limits, beta targets, kill switch
│   └── alerts.py              # Telegram bot dispatcher
│
├── backtest/
│   ├── engine.py              # walk-forward validation
│   └── metrics.py             # Sharpe, Calmar, max drawdown, hit rate
│
└── dashboard/
    └── app.py                 # Streamlit live monitoring UI
```

---

## 4. Layer-by-Layer Specification

### Layer 1: Multi-Source Data Pipeline

**Sources and priority:**

| Source | Data Type | Rate Limit | Caching TTL | Failover |
|--------|-----------|-----------|-------------|---------|
| Alpaca Markets | Real-time OHLCV + News | 200 req/min | 1 min (price), 15 min (news) | → yfinance |
| yfinance | Historical OHLCV, fundamentals | ~100 req/hr (self-imposed) | 15 min | → polygon |
| FRED | VIX, DXY, 10Y yield, yield curve | 120 req/min | 1 hour | None (daily data) |
| SEC EDGAR RSS | 8-K, earnings filings | Unlimited | 30 min | None |
| Google RSS | Ticker news headlines | Unlimited | 30 min | None |

**Source arbitration rules:**
- Cross-validate prices across 2 sources; flag >0.5% divergence as data quality issue
- News deduplication via cosine similarity (sentence-transformers) before NLP scoring
- All timestamps normalized to UTC
- Missing bars forward-filled with flag in metadata

**Caching strategy (diskcache, no Redis needed):**
```python
CACHE_TTL = {
    'price_realtime':   60,       # 1 minute
    'price_historical': 900,      # 15 minutes
    'news':             1800,     # 30 minutes
    'macro':            3600,     # 1 hour
    'fundamentals':     86400,    # 24 hours
    'earnings_cal':     86400,    # 24 hours
}
```

### Layer 2: Feature Engineering

**Moving Average Matrix:**

| MA Type | Config | Use Case |
|---------|--------|----------|
| EMA 9 | Fast trend | Short-term momentum |
| EMA 21 | Medium trend | Crossover signal |
| SMA 50 | Trend confirmation | Medium-term trend |
| SMA 200 | Long-term trend | Bull/bear regime |
| KAMA 10 | Adaptive (vol-adjusted) | Noisy market filter |
| VWAP | Session-anchored | Intraday mean reversion |
| MVWAP 20 | 20-day VWAP MA | Institutional price reference |
| HMA 16 | Hull MA (low lag) | Responsive trend signal |

**Volatility Regime Classifier:**

Regimes: `LOW_VOL_TREND | HIGH_VOL_TREND | LOW_VOL_RANGE | HIGH_VOL_RANGE | CRISIS`

Inputs:
- Realized volatility (20-day rolling, annualized)
- Volatility percentile rank (vs trailing 252 days)
- **Hurst Exponent** — distinguishes trending (H>0.6) from mean-reverting (H<0.4) from random (H≈0.5)
- VIX level from FRED

**Why Hurst matters:** Most systems use vol alone. Hurst separates "volatile but trending" (ride it) from "volatile and choppy" (reduce size). CRISIS regime triggers when VIX > 30.

**Sentiment Feature Engineering:**
- Raw FinBERT scores per headline per ticker
- Sentiment MA: 3h, 24h, 72h (same concept as price MA on sentiment)
- Sentiment momentum: `3h_sentiment - 72h_sentiment`
- Entity extraction: flag explicit mentions of held tickers
- SEC 8-K classifier: earnings surprise / guidance cut / insider buying

### Layer 3: Analysis Models

Each model produces a **signal score ∈ [-1.0, +1.0]** independently.

**Model A — Technical Analysis:**
- Inputs: OHLCV + full MA matrix above
- Signals: MA crossover matrix, RSI divergence, MACD histogram, Bollinger squeeze, volume confirmation
- Key insight: Volume confirmation required for high-confidence signals (price move without volume = low confidence)

**Model B — Fundamental Screening (Top-Down):**
```
Macro → Sector → Industry → Stock
Is the sector in favor?
  → Is this industry growing within it?
    → Is this stock cheap/expensive vs peers?
```
- Inputs: P/E, P/S, EV/EBITDA, earnings revision direction, analyst consensus delta
- Outputs: relative valuation score vs sector median

**Model C — Sentiment + News NLP:**
- FinBERT (finance-tuned BERT, local inference via HuggingFace transformers)
- Runs on: Alpaca news feed + SEC EDGAR filings + Google RSS headlines
- Key metric: sentiment **change** over 48h, not absolute level
- Rapid negative shift = review trigger regardless of absolute score

**Model D — Macro Regime Model:**

| Signal | Threshold | Portfolio Impact |
|--------|-----------|-----------------|
| VIX | > 25 | Risk-off: reduce beta, increase XLU/JNJ/XLP |
| Yield curve (10Y-2Y) | Inverting | Recession signal: shift defensive |
| DXY | Spiking | Headwind for TSM (ADR FX risk), AMZN international |
| 10Y yield | Rising >20bps/week | Headwind for PLTR/IONQ high-multiple names |

### Layer 4: Signal Fusion Engine

**Dynamic regime-weighted model arbitration:**

| Regime | Technical | Fundamental | Sentiment | Macro |
|--------|-----------|------------|-----------|-------|
| HIGH_VOL_TREND | 45% | 15% | 30% | 10% |
| LOW_VOL_TREND | 30% | 40% | 15% | 15% |
| LOW_VOL_RANGE | 25% | 35% | 25% | 15% |
| CRISIS | 10% | 10% | 20% | 60% |

- Macro is an **additive adjustment** (not part of weighted average) to preserve its regime-override role
- **Confidence score** = 1 - std(model_scores): measures inter-model agreement
- Only generate action signal when confidence > 0.65 AND |fused_score| > 0.35
- High score + low confidence = HOLD (models disagree)

### Layer 5: Agent Orchestrator

**Run cycle (every 15 minutes during market hours):**
1. Fetch latest prices and news via data pipeline
2. Compute features for all 15 tickers
3. Run all 4 models → fuse signals
4. Compute current vs target weights (Black-Litterman posterior)
5. Identify rebalancing trades exceeding drift threshold (±2%)
6. Validate against risk manager
7. If validated: push Telegram alert with recommended trades
8. Log everything to DuckDB

**Dynamic risk parameter adjustment:**

| Macro Regime | Max Position | Max Sector | Target Beta |
|-------------|-------------|-----------|------------|
| RISK_ON | 10% | 25% | 0.50 |
| TRANSITION | 8% | 20% | 0.35 |
| CRISIS | 5% | 15% | 0.20 |

**Kill switch:** Any single position down >15% intraday → immediate Telegram alert regardless of other signals.

---

## 5. Backtesting Framework

Walk-forward validation only — no simple backtests (avoids lookahead bias).

- Training window: 252 days (1 year)
- Test window: 21 days (1 month)
- Roll forward: 21 days at a time

**Models tested independently then compared:**
1. Technical only
2. Fundamental only
3. Sentiment only
4. Fused (static equal weights)
5. Fused (dynamic regime weights) ← expected winner

**Metrics reported:**
- Sharpe Ratio (annualized)
- Calmar Ratio (return / max drawdown)
- Maximum Drawdown
- Hit Rate (% of signals that were profitable)
- Average Holding Period

---

## 6. Dashboard (Streamlit)

**5 views:**

1. **Portfolio Overview** — live P/L heatmap, total value, excess return vs SPY
2. **Signal Dashboard** — per-ticker signal scores (color-coded), confidence levels, dominant model
3. **Regime Monitor** — current macro regime, VIX, DXY, yield curve chart
4. **Monte Carlo** — 10,000 path simulation to April 10, fan chart + probability table
5. **System Health** — API feed status, last update timestamps, cache hit rates (Datadog integration)

---

## 7. Alerting (Telegram Bot)

**Alert types:**

| Alert | Trigger | Priority |
|-------|---------|---------|
| REBALANCE | Position drift >2% + confidence >0.65 | High |
| RISK_BREACH | Any position >10% or sector >25% | Critical |
| MACRO_SHIFT | Regime change detected | High |
| KILL_SWITCH | Any position down >15% intraday | Critical |
| EARNINGS_UPCOMING | Earnings within 3 trading days | Medium |
| SENTIMENT_SPIKE | Rapid negative sentiment shift on any holding | Medium |
| FEED_STALE | Any data source not updated >30 min during market hours | Low |

---

## 8. Infrastructure

### Environments

| Environment | Platform | Purpose |
|------------|---------|---------|
| Development | GitHub Codespaces (180h/mo free — Education pack) | Code, test, professor demo |
| Production | DigitalOcean Droplet ($200 credits free — Education pack) | 24/7 persistent monitoring |
| Observability | Datadog (2 years free — Education pack) | System health, API latency |

### Production Setup (DigitalOcean)
- $6/mo Basic Droplet (1 vCPU, 1GB RAM) — covered by $200 credits
- SSH deploy via existing Linux/SSH skills
- Run with `tmux` or simple `systemd` service
- Streamlit on port 8501 (accessible from anywhere)
- No Docker, no Nginx required

### Tech Stack (zero infrastructure overhead)

| Component | Tool | Replaces |
|-----------|------|---------|
| Time-series DB | DuckDB (single file) | Postgres + server |
| API cache | diskcache (SQLite-backed) | Redis |
| Scheduler | APScheduler (in-process) | Celery + Redis queue |
| NLP inference | HuggingFace transformers (local) | Paid NLP API |
| Dashboard | Streamlit | React frontend |
| Alerts | python-telegram-bot | Slack/PagerDuty |

### Python Dependencies
```
yfinance
alpaca-trade-api
duckdb
diskcache
transformers           # FinBERT
sentence-transformers  # news deduplication
apscheduler
streamlit
pypfopt               # Black-Litterman + MVO
pandas
numpy
scipy
python-telegram-bot
requests              # SEC EDGAR, Google RSS
feedparser            # RSS parsing
```

---

## 9. Build Order and Time Estimates

Given background: Python (advanced), Linux/SSH, Docker, Postgres, Redis, ML frameworks.

| Phase | Components | Estimated Time |
|-------|-----------|---------------|
| 1 | Data pipeline (Layer 1) — all sources, caching, arbitration | 1 day |
| 2 | Feature engineering (Layer 2) — MA matrix, Hurst, vol regimes | 1 day |
| 3 | Technical + Macro models (Layer 3 partial) | 1 day |
| 4 | Sentiment model + FinBERT pipeline (Layer 3 partial) | 1 day |
| 5 | Fundamental model (Layer 3 partial) | 0.5 day |
| 6 | Signal fusion engine (Layer 4) | 1 day |
| 7 | Agent orchestrator + risk manager (Layer 5) | 1 day |
| 8 | Backtest framework | 1 day |
| 9 | Streamlit dashboard | 0.5 day |
| 10 | Telegram alerting + DigitalOcean deploy | 0.5 day |
| **Total** | | **~8.5 days focused work** |

**Recommended approach:** Use Claude Code (Opus) to scaffold each phase.
Give it this document as context + layer spec. It will generate the boilerplate;
your job is architecture decisions, parameter tuning, and debugging the Hurst
exponent + dynamic fusion weight logic (the genuinely hard parts).

---

## 10. Quant Story for Professor

> "We formalized our investment thesis using a Black-Litterman model, expressing 5
> views with explicit confidence levels. Posterior weights confirmed our overweight
> in AI infrastructure (TSM, MU) and defense (LMT), while flagging consumer staples
> (WMT, XLP) as slightly above risk-adjusted optimum.
>
> Forward-looking monitoring runs a 4-model signal fusion engine (technical,
> fundamental, sentiment, macro) with dynamic regime-weighted arbitration — model
> weights shift based on a volatility regime classifier using the Hurst exponent
> to distinguish trending from mean-reverting market conditions.
>
> Monte Carlo simulation across 10,000 paths to April 10 shows a median portfolio
> value of $X with P(outperform SPY) = Y%. Our current +2.00% excess return vs
> benchmark in a risk-off week (-1.87% SPY) is consistent with the model's
> predicted alpha from our AI/defense tilt and low portfolio beta of 0.33."

---

*Generated: February 24, 2026 | Portfolio Simulation End Date: April 10, 2026*
