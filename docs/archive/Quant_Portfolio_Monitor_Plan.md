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

### 4-Phase Core Engine

```
┌─────────────────────────────────────────────────────┐
│  PHASE 4: MINIMUM SPANNING TREE (MST) OPTIMIZATION  │
│  Network skeleton extraction & redundancy pruning   │
├─────────────────────────────────────────────────────┤
│  PHASE 3: 15-MINUTE DRIFT MODEL                     │
│  SPY Beta prediction & limit order real-time offset │
├─────────────────────────────────────────────────────┤
│  PHASE 2: HIERARCHICAL RISK PARITY (HRP)            │
│  Inverse volatility / ATR based position sizing     │
├─────────────────────────────────────────────────────┤
│  PHASE 1: WEIGHTED CORRELATION GRAPH                │
│  Sparse inverse covariance & structural clustering  │
└─────────────────────────────────────────────────────┘
```

**Crucial System Constraint Addressed:**
Moving away from HuggingFace/FinBERT NLP. A $6/mo DigitalOcean Basic Droplet (1 vCPU, 1GB RAM) inherently suffers OOM (Out Of Memory) crashes when loading multi-gigabyte transformer models. This revised architecture drops heavy NLP inference in favor of robust, highly compute-efficient mathematical modeling (`networkx`, `scikit-learn`, `scipy`).

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
│   └── cache.py               # diskcache wrapper with TTL config
│
├── features/
│   ├── drift_model.py         # 15-min SPY Beta proxy calculator
│   ├── volatility.py          # ATR, moving variance
│   └── correlation.py         # returns matrix, pearson/spearman
│
├── models/
│   ├── graph_network.py       # scikit-learn GraphicalLasso
│   ├── risk_parity.py         # Hierarchical Risk Parity (HRP)
│   └── mst_clustering.py      # NetworkX Min Spanning Tree solver
│
├── agent/
│   ├── execution.py           # Limit order generator
│   ├── risk_manager.py        # Position limits, beta targets, kill switch
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

## 4. Layer-by-Layer Specification (The 4 Phases)

### Phase 1: The Weighted Correlation Graph (The Map)
The program treats the closed universe of positions as nodes in a network. The "weight" of the edges between them represents statistical correlation rather than absolute price.
- **The Math:** Calculates Pearson/Spearman correlation coefficients (-1 to +1) for every pair in the portfolio. Uses Scikit-learn's `GraphicalLasso` to compute the "Sparse Inverse Covariance."
- **The Insight:** Identifies structural clusters based on actual market movement behavior. Ten conventionally "different" stocks with heavily correlated edges (>0.8) are flagged as a single implicit bet, revealing true portfolio diversification vs. illusory diversification.

### Phase 2: Hierarchical Risk Parity (The Solution to Volatility)
Trailing stops fail because they are unaware of distinct asset variance (e.g., stopping out safely on a tech stock vs. a utility is statistically different).
- **The Protocol:** Replaces standard 5% stop-loss logic with mathematical Position Sizing via Hierarchical Risk Parity (HRP).
- **The Math:** Uses the Inverse Volatility / Average True Range (ATR) of each structural node. If Asset A has an ATR of $10 and Asset B has an ATR of $2, the model allocates 5x more capital weighting to Asset B.
- **The Impact:** Standardizes variance impact horizontally across the closed universe. Volatility is neutralized as high-variance assets are simply held in proportionately smaller sizing blocks.

### Phase 3: The "15-Minute Drift" Model
Because execution is manual and platform data lags by 15 minutes, standard reactive strategies result in chasing stale prices.
- **Slippage Modeling:** The system calculates the real-time "Beta" of the tracked stocks against a live market proxy (e.g., SPY, which is freely accessible in real-time via Yahoo/mobile).
- **Execution Logic:** If the live SPY proxy moves +1% in the blind 15-minute window, the drift model utilizes historical asset Beta to synthesize an estimated real-time price map.
- **The Action:** It outputs synthesized Limit Order prices pegged to the modeled drift, preempting the 15-minute gap and preventing "chasing" prices that have already cleared in live markets.

### Phase 4: Minimum Spanning Tree (MST) Optimization
Extracts the fundamental risk structure required to make execution decisions on a closed universe.
- **The Math:** Applies NetworkX MST (Minimum Spanning Tree) algorithms over the weighted correlation graph to strip statistical noise.
- **The Protocol:** Creates the essential core skeleton connecting all portfolio nodes without redundant cycles.
- **The Output:** Yields concentration risk flags. If growth holdings form branches originating from a single keystone node (e.g., NVDA), the program generates an alert to "prune" redundant branches (sell over-correlated assets) and allocate capital to "Islands" — nodes with no substantial edges to broader market variance.

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
| Graph/Math | Scikit-learn, NetworkX, SciPy | Heavy NLP (FinBERT) |
| Dashboard | Streamlit | React frontend |
| Alerts | python-telegram-bot | Slack/PagerDuty |

### Python Dependencies
```
yfinance
alpaca-trade-api
duckdb
diskcache
scikit-learn           # Sparse Inverse Covariance
networkx               # Minimum Spanning Tree
apscheduler
streamlit
pypfopt                # Hierarchical Risk Parity
pandas
numpy
scipy                  # Correlation math & optimization
python-telegram-bot
requests
```

---

## 9. Build Order and Time Estimates

Given background: Python (advanced), Linux/SSH, Docker, Postgres, Redis, Math frameworks.

| Phase | Components | Estimated Time |
|-------|-----------|---------------|
| 1 | Data pipeline — all sources, caching | 0.5 day |
| 2 | Model Phase 1: Weighted Correlation Graph / GraphicalLasso | 1 day |
| 3 | Model Phase 2: Hierarchical Risk Parity (Position Sizing) | 1 day |
| 4 | Model Phase 3: 15-Minute Drift Model (Live SPY Beta Predictor) | 1 day |
| 5 | Model Phase 4: Minimum Spanning Tree (NetworkX graph prune) | 1 day |
| 6 | Agent orchestrator + execution logic | 1 day |
| 7 | Backtest framework (Out-of-sample graph structure validation) | 1 day |
| 8 | Streamlit dashboard (Visualizing the Network + HRP targets) | 1 day |
| 9 | Telegram alerting + DigitalOcean deploy (1GB RAM safe) | 0.5 day |
| **Total** | | **~8 days focused work** |

**Recommended approach:** Build the math engine layer-by-layer. 
Focus first on getting pristine EOD data arrays to supply the Covariance Matrix, as garbage-in will completely ruin the Minimum Spanning Tree topology.

---

## 10. Quant Story for Professor

> "We pivoted away from standard fundamental and technical screens to solve the fundamental issues of manual execution on delayed platforms. First, we addressed illusion of diversification using a GraphicalLasso-derived Sparse Inverse Covariance matrix, modeling our universe as a weighted correlation graph.
>
> We observed that fixed stop-losses failed due to variable asset variance. We solved this mathematically by discarding stops in favor of Hierarchical Risk Parity (HRP)—sizing positions inversely to their Average True Range, equalizing variance impact across all nodes.
>
> To counteract the platform's 15-minute data lag, we engineered a drift-prediction model using live SPY proxies against asset Beta to synthesize preemptive limit-order pricing. Finally, we stripped market noise using a Minimum Spanning Tree (MST) algorithm to isolate concentration risks and prune redundant network branches. Our edge comes from execution structure and mathematical risk-budgeting, rather than attempting to out-guess market direction."

---

*Generated: February 24, 2026 | Portfolio Simulation End Date: April 10, 2026*
