# Development Roadmap

Complete phase-by-phase implementation plan from scaffold to production.

---

## Timeline Overview

```
Feb 24 ──────────────────────────────────────────────── May 1
   │                                                      │
   ├─ Phase 0: Scaffold ✅                                │
   ├─ Phase 1: Data Pipeline                              │
   ├─ Phase 2: Feature Engineering                        │
   ├─ Phase 3: Technical + Macro Models                   │
   ├─ Phase 4: Sentiment Model                            │
   ├─ Phase 5: Fundamental Model                          │
   ├─ Phase 6: Signal Fusion                              │
   ├─ Phase 7: Agent Orchestrator                         │
   ├─ Phase 8: Backtesting                                │
   ├─ Phase 9: Dashboard                                  │
   ├─ Phase 10: Alerts + Deployment                       │
   │                           │                          │
   │                     Apr 10: Valuation         May 1: Sunset
```

**Total estimated effort:** ~8.5 focused days

## Status Update (March 13, 2026)

- Phase 0-6: Complete
- Phase 7-9: Implemented for prototype and actively used
- Phase 10: In hardening (deployment readiness, UX polish, reliability fixes)
- Demo-day executable: YES (with required Doppler secrets configured)

---

## Phase 0: Project Scaffold ✅

**Status:** Complete  
**Duration:** ~2 hours

### Deliverables
- [x] Git repository with .gitignore
- [x] uv project with pyproject.toml
- [x] 68 files, 6,244 lines
- [x] 188 dependencies in uv.lock
- [x] config.toml with all 15 holdings
- [x] config.py TOML + secrets loader
- [x] All module stubs with TODO markers
- [x] 6 tests passing
- [x] ruff + pre-commit configured
- [x] GitHub Actions CI/CD
- [x] Heroku Procfile + runtime.txt
- [x] MkDocs documentation scaffold
- [x] Pushed to GitHub

### Documentation
- [Phase 0 Details](phase-0-scaffold.md)

---

## Phase 1: Data Pipeline

**Status:** 🔄 In Progress  
**Estimated:** 1 day

### Objectives
Build the multi-source data pipeline with caching and failover.

### Tasks

#### Alpaca Feed
- [ ] Initialize Alpaca client with API keys from Doppler
- [ ] Implement `get_bars()` — fetch OHLCV for multiple tickers
- [ ] Implement `get_latest_quotes()` — real-time quotes
- [ ] Implement `get_news()` — news feed for tickers
- [ ] Implement `is_market_open()` — market status check
- [ ] Add rate limiting (200 req/min)
- [ ] Add error handling with retries

#### FRED Feed
- [ ] Initialize FRED client with API key
- [ ] Implement `get_series()` — fetch single series
- [ ] Implement `get_macro_snapshot()` — VIX, DXY, yields
- [ ] Define `FRED_SERIES` mapping for all macro indicators

#### Cache
- [ ] Initialize diskcache with configurable directory
- [ ] Implement TTL-aware `get()` and `set()`
- [ ] Implement `stats()` for cache hit rate monitoring
- [ ] Configure TTLs from config.toml

#### Appwrite Client
- [ ] Initialize Appwrite SDK with Doppler secrets
- [ ] Implement `ensure_collections()` — idempotent setup
- [ ] Implement `write_document()` — single doc write
- [ ] Implement `write_batch()` — bulk writes
- [ ] Implement `query_documents()` — filtered reads
- [ ] Create all 6 collections on first run

#### Pipeline Orchestrator
- [ ] Implement `fetch_prices()` with Alpaca → Appwrite fallback
- [ ] Implement `fetch_news()` with deduplication
- [ ] Implement `fetch_macro()` from FRED
- [ ] Implement `fetch_fundamentals()` from Appwrite
- [ ] Add cross-source price validation (flag >0.5% divergence)

#### Scrapy Spiders
- [ ] Complete SEC EDGAR spider — map tickers to CIKs
- [ ] Complete Google RSS spider — build URLs per ticker
- [ ] Complete yfinance spider — price + fundamentals fallback
- [ ] Implement Appwrite pipeline — push items to scraped_data
- [ ] Deploy to Zyte Scrapy Cloud
- [ ] Configure spider schedules

### Tests
- [ ] Test Alpaca feed with mocked responses
- [ ] Test FRED feed with mocked responses
- [ ] Test cache TTL expiration
- [ ] Test Appwrite client CRUD operations
- [ ] Test pipeline failover logic

### Definition of Done
- `doppler run -- uv run python -c "from quant_monitor.data.pipeline import DataPipeline; p = DataPipeline(); print(p.fetch_macro())"` returns VIX, DXY, yields
- Spiders deployed and running on Zyte
- Data visible in Appwrite console

---

## Phase 2: Feature Engineering

**Status:** ⬜ Planned  
**Estimated:** 1 day

### Objectives
Implement the complete moving average matrix, volatility features, and sentiment preprocessing.

### Tasks

#### Moving Averages
- [ ] Implement `ema()` — Exponential MA
- [ ] Implement `sma()` — Simple MA
- [ ] Implement `kama()` — Kaufman Adaptive MA
- [ ] Implement `vwap()` — Session-anchored VWAP
- [ ] Implement `mvwap()` — Moving VWAP
- [ ] Implement `hma()` — Hull MA (low lag)
- [ ] Implement `compute_ma_matrix()` — all MAs for one ticker

#### Volatility
- [ ] Implement `realized_volatility()` — annualized rolling vol
- [ ] Implement `volatility_percentile()` — percentile rank vs history
- [ ] Implement `hurst_exponent()` — R/S analysis ⚠️ Hard
- [ ] Implement `classify_regime()` — 5-regime classifier

#### Sentiment Features
- [ ] Lazy-load FinBERT model to save memory
- [ ] Implement `score_headlines()` — batch FinBERT inference
- [ ] Implement `compute_sentiment_ma()` — 3h/24h/72h rolling
- [ ] Implement `sentiment_momentum()` — short vs long MA
- [ ] Implement `deduplicate_news()` — cosine similarity filter

### Tests
- [ ] Test EMA matches pandas ewm
- [ ] Test Hurst on synthetic trending/ranging series
- [ ] Test regime classification edge cases
- [ ] Test sentiment scoring on known examples

### Definition of Done
- `compute_ma_matrix()` returns DataFrame with all 8 MAs
- `classify_regime()` correctly identifies all 5 regimes
- Hurst exponent gives H>0.6 on trending series, H<0.4 on mean-reverting

---

## Phase 3: Technical + Macro Models

**Status:** ⬜ Planned  
**Estimated:** 1 day

### Objectives
Implement the technical analysis model and macro regime model.

### Tasks

#### Technical Model
- [ ] MA crossover detection (EMA9/21, SMA50/200)
- [ ] RSI calculation and divergence detection
- [ ] MACD histogram direction
- [ ] Bollinger Band squeeze detection
- [ ] Volume confirmation multiplier
- [ ] Implement `score()` — combine signals into [-1, 1]
- [ ] Implement `score_all()` — batch scoring

#### Macro Model
- [ ] VIX threshold logic (>25 = risk-off)
- [ ] Yield curve inversion detection
- [ ] DXY spike detection (weekly % change)
- [ ] 10Y yield spike detection (weekly bps change)
- [ ] Implement `score()` — portfolio-level macro signal
- [ ] Implement `classify_regime()` — RISK_ON/TRANSITION/CRISIS
- [ ] Implement `per_ticker_impact()` — ticker-specific adjustments

### Tests
- [ ] Test MA crossover on known price series
- [ ] Test RSI bounds [0, 100]
- [ ] Test macro regime classification
- [ ] Test yield curve inversion logic

### Definition of Done
- Technical model scores 15 tickers in <1 second
- Macro model correctly identifies regime from FRED snapshot

---

## Phase 4: Sentiment Model

**Status:** ⬜ Planned  
**Estimated:** 1 day

### Objectives
Implement the FinBERT-driven sentiment model.

### Tasks
- [ ] Load FinBERT model and tokenizer
- [ ] Process news from Appwrite scraped_data
- [ ] Aggregate sentiment per ticker
- [ ] Weight recent news higher than stale
- [ ] Track sentiment momentum (3h - 72h)
- [ ] Implement `score()` — sentiment signal per ticker
- [ ] Add 8-K classification (earnings surprise, guidance cut)

### Tests
- [ ] Test FinBERT on known positive/negative headlines
- [ ] Test sentiment aggregation logic
- [ ] Test momentum calculation

### Definition of Done
- Sentiment model scores in <5 seconds (batch mode)
- Correctly identifies negative sentiment spike

---

## Phase 5: Fundamental Model

**Status:** ⬜ Planned  
**Estimated:** 0.5 day

### Objectives
Implement the top-down fundamental screening model.

### Tasks
- [ ] Define sector classifications
- [ ] Compute P/E relative to sector median
- [ ] Compute P/S relative to sector median
- [ ] Compute EV/EBITDA relative to sector median
- [ ] Fetch analyst estimate revisions (from Appwrite)
- [ ] Implement `score()` — relative valuation score

### Tests
- [ ] Test relative valuation calculation
- [ ] Test sector assignment

### Definition of Done
- Fundamental model identifies expensive/cheap tickers vs peers

---

## Phase 6: Signal Fusion Engine

**Status:** ⬜ Planned  
**Estimated:** 1 day

### Objectives
Implement the dynamic regime-weighted signal fusion.

### Tasks
- [ ] Load regime weights from config.toml
- [ ] Compute weighted average of tech/fund/sent scores
- [ ] Apply macro adjustment (additive, not weighted)
- [ ] Compute confidence = 1 - std(scores)
- [ ] Determine dominant model
- [ ] Generate action (BUY/SELL/HOLD) based on thresholds
- [ ] Implement `fuse()` — single ticker fusion
- [ ] Implement `fuse_all()` — batch fusion

### Tests
- [ ] Test fusion with mocked model scores
- [ ] Test confidence calculation
- [ ] Test threshold gating

### Definition of Done
- Fusion engine respects regime-dependent weights
- High signal + low confidence = HOLD

---

## Phase 7: Agent Orchestrator

**Status:** ⬜ Planned  
**Estimated:** 1 day

### Objectives
Implement the decision engine, risk manager, and APScheduler integration.

### Tasks

#### Risk Manager
- [ ] Implement `validate_trades()` — check position/sector limits
- [ ] Implement `check_kill_switch()` — >15% intraday loss
- [ ] Implement `check_position_limits()` — per-regime limits
- [ ] Implement `compute_portfolio_beta()` — weighted beta

#### Optimizer
- [ ] Implement Black-Litterman posterior computation
- [ ] Use pyportfolioopt for MVO
- [ ] Implement `compute_target_weights()`
- [ ] Implement `compute_rebalance_trades()`

#### Orchestrator
- [ ] Set up APScheduler with 15-minute interval
- [ ] Implement full signal cycle function
- [ ] Write snapshots to Appwrite
- [ ] Integrate risk manager validation

### Tests
- [ ] Test position limit validation
- [ ] Test kill switch trigger
- [ ] Test Black-Litterman output shape

### Definition of Done
- Main runs 15-minute signal loop
- Risk manager blocks charter-violating trades
- Portfolio snapshots appear in Appwrite

---

## Phase 8: Backtesting Framework

**Status:** ⬜ Planned  
**Estimated:** 1 day

### Objectives
Implement walk-forward backtesting with proper metrics.

### Tasks
- [ ] Implement walk-forward engine (252/21/21 windows)
- [ ] Implement metrics: Sharpe, Calmar, max DD, hit rate
- [ ] Run backtests for all 5 model configs
- [ ] Generate comparison table
- [ ] Store results for documentation

### Tests
- [ ] Test Sharpe calculation against known values
- [ ] Test walk-forward window logic

### Definition of Done
- Backtest engine produces metrics for all model configurations
- Regime-weighted fusion outperforms equal-weighted

---

## Phase 9: Streamlit Dashboard

**Status:** ⬜ Planned  
**Estimated:** 0.5 day

### Objectives
Implement the 5-view monitoring dashboard.

### Tasks
- [ ] Portfolio Overview — P/L heatmap, return vs benchmark
- [ ] Signal Dashboard — per-ticker scores, confidence, dominant model
- [ ] Regime Monitor — VIX/DXY/yield curve charts
- [ ] Monte Carlo — 10,000 path simulation to Apr 10
- [ ] System Health — feed status, cache stats

### Definition of Done
- Dashboard loads from Appwrite data
- All 5 views functional and presentable

---

## Phase 10: Alerts + Deployment

**Status:** ⬜ Planned  
**Estimated:** 0.5 day

### Objectives
Complete Telegram integration and production deployment.

### Tasks
- [ ] Set up Telegram bot via BotFather
- [ ] Implement all alert formatters
- [ ] Implement cooldown logic
- [ ] Deploy to Heroku (web + worker dynos)
- [ ] Verify GitHub Actions deployment
- [ ] Test end-to-end signal → alert flow

### Definition of Done
- Alerts appear in Telegram when thresholds crossed
- Both dynos running on Heroku
- System operational for valuation checkpoint

---

## Post-Implementation

### Before Valuation (April 10)
- [ ] Run full backtest with final parameters
- [ ] Document model performance
- [ ] Prepare presentation materials

### Before Sunset (May 1)
- [ ] Run `scripts/export_for_archive.py`
- [ ] Generate final performance charts
- [ ] Export complete signal history
- [ ] Build final MkDocs site
- [ ] Deploy to GitHub Pages
- [ ] Delete Heroku app
- [ ] Archive repository

---

## Risk Register

| Risk | Mitigation |
|------|------------|
| API rate limits | Aggressive caching, fallback sources |
| Heroku dyno sleep | Use Basic plan or two dynos |
| FinBERT slow inference | Batch processing, not real-time |
| Data quality issues | Cross-validation, data integrity checks |
| Time constraints | Prioritize core signal loop over polish |

---

*Last updated: February 24, 2026*
