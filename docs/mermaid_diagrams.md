# Project BWC — Mermaid Diagrams

> For Excalidraw renderer, static architecture/infrastructure documentation.
> Paste any block into [mermaid.live](https://mermaid.live) or Excalidraw's Mermaid import.

---

## 1. Full System Architecture

```mermaid
graph TB
    subgraph INGEST["Data Ingestion Layer"]
        YF[yfinance API]
        MV[Massive/Polygon]
        FRED[FRED Macro API]
        SEC[SEC EDGAR]
        RSS[Google RSS News]
    end

    subgraph CACHE["Caching & Rate Limiting"]
        RL[Rate Limiter<br/>120 req/min]
        TC[TTL Cache<br/>prices: 300s]
        XV[Cross-Validator<br/>divergence > 0.5%]
    end

    subgraph STORAGE["Persistence Layer"]
        AW[(Appwrite Cloud<br/>9 collections)]
        DK[(DuckDB Local<br/>eod_price_matrix)]
    end

    subgraph COMPUTE["Compute Engine"]
        FE[Feature Engine<br/>MA, Volatility, Bollinger]
        MM[Macro Model<br/>VIX, Yield, DXY, Regime]
        FA[Fusion Agent<br/>Regime-Weighted Scoring]
    end

    subgraph OPTIMIZE["Optimization Layer"]
        BL[Black-Litterman<br/>Posterior Returns]
        MVO[Mean-Variance Optimizer<br/>Max Sharpe, 15% cap]
        RM[Risk Manager<br/>Position Limits, Kill Switch]
    end

    subgraph VALIDATE["Validation Layer"]
        BT[Backtest Engine<br/>Walk-Forward 252d/21d]
        HRP[HRP Sizer<br/>Hierarchical Risk Parity]
        MT[Metrics Engine<br/>Sharpe, Sortino, CVaR]
    end

    subgraph OUTPUT["Output Layer"]
        DB[Rich CLI Dashboard]
        PD[Plotly Dashboards]
        FE2[Frontend HTML/JS]
    end

    YF --> RL
    MV --> RL
    FRED --> RL
    SEC --> RL
    RSS --> RL
    RL --> TC --> XV
    XV --> AW
    AW --> DK
    DK --> FE
    DK --> MM
    FE --> FA
    MM --> FA
    FA --> BL --> MVO
    MVO --> RM
    RM --> BT
    BT --> HRP
    HRP --> MT
    MT --> DB
    MT --> PD
    MT --> FE2

    style INGEST fill:#1e1e2e,stroke:#3b82f6,color:#f4f4f5
    style CACHE fill:#1e1e2e,stroke:#f59e0b,color:#f4f4f5
    style STORAGE fill:#1e1e2e,stroke:#8b5cf6,color:#f4f4f5
    style COMPUTE fill:#1e1e2e,stroke:#14b8a6,color:#f4f4f5
    style OPTIMIZE fill:#1e1e2e,stroke:#eb5e28,color:#f4f4f5
    style VALIDATE fill:#1e1e2e,stroke:#00ff88,color:#f4f4f5
    style OUTPUT fill:#1e1e2e,stroke:#f4f4f5,color:#f4f4f5
```

---

## 2. Data Pipeline Sequence Diagram

```mermaid
sequenceDiagram
    participant S as Spiders
    participant RL as Rate Limiter
    participant YF as yfinance
    participant MV as Massive API
    participant C as TTL Cache
    participant AW as Appwrite
    participant DK as DuckDB
    participant FE as Features

    S->>RL: request(AAPL, OHLCV)
    RL-->>RL: check token bucket
    alt tokens available
        RL->>YF: GET /v8/finance
        YF-->>RL: 200 OK (OHLCV)
    else rate limited
        RL->>RL: exponential backoff 2^n
        RL->>MV: GET /prices (fallback)
        MV-->>RL: 200 OK
    end
    RL->>C: cache.set(AAPL, data, ttl=300)
    C->>AW: upsert eod_price_matrix
    AW-->>DK: DuckDBSync.pull()
    DK->>DK: INSERT ON CONFLICT UPDATE
    DK->>FE: SELECT * WHERE ticker='AAPL'
    FE-->>FE: compute MA, σ, Bollinger
```

---

## 3. Macro Regime State Machine

```mermaid
stateDiagram-v2
    [*] --> RISK_ON

    RISK_ON --> TRANSITION : VIX > 25 OR spread < 0
    RISK_ON --> RISK_ON : VIX < 25 AND spread > 0

    TRANSITION --> CRISIS : n_crisis ≥ 3
    TRANSITION --> RISK_ON : signals clear
    TRANSITION --> TRANSITION : 1 ≤ n_crisis < 3

    CRISIS --> TRANSITION : VIX drops below 25
    CRISIS --> CRISIS : VIX > 35

    state RISK_ON {
        [*] --> NormalTrading
        NormalTrading : max_position = 10%
        NormalTrading : max_sector = 25%
        NormalTrading : full signal weight
    }

    state TRANSITION {
        [*] --> ReducedExposure
        ReducedExposure : max_position = 8%
        ReducedExposure : max_sector = 20%
        ReducedExposure : damped signals
    }

    state CRISIS {
        [*] --> DefensiveMode
        DefensiveMode : max_position = 5%
        DefensiveMode : max_sector = 15%
        DefensiveMode : kill switch active
    }
```

---

## 4. Agent Optimizer Decision Flow

```mermaid
flowchart TD
    A[Market Data Arrives] --> B{Stale Cache?}
    B -->|Yes| C[Fetch Fresh via Pipeline]
    B -->|No| D[Use Cached Data]
    C --> D
    D --> E[Feature Engine]
    E --> F[Technical Signals]
    E --> G[Fundamental Signals]
    E --> H[Sentiment Signals]
    E --> I[Macro Regime Signal]

    F --> J[Fusion Agent]
    G --> J
    H --> J
    I --> J

    J --> K{Confidence > θ?}
    K -->|No| L[Hold / No Trade]
    K -->|Yes| M[Black-Litterman]

    M --> N[Compute Posterior E_R]
    N --> O[Mean-Variance Optimizer]
    O --> P[Target Weights w*]

    P --> Q{Drift > 2%?}
    Q -->|No| L
    Q -->|Yes| R[Risk Manager]

    R --> S{Position < Max?}
    S -->|No| T[Reject / Scale Down]
    S -->|Yes| U{Kill Switch OK?}
    U -->|No| V[Emergency Liquidate]
    U -->|Yes| W[Execute Rebalance]

    W --> X[Log to Appwrite]
    X --> Y[Dashboard Update]

    style A fill:#3b82f6,color:#fff
    style W fill:#00ff88,color:#000
    style V fill:#ff3366,color:#fff
    style L fill:#52525b,color:#fff
```

---

## 5. Module Dependency Graph

```mermaid
graph LR
    subgraph quant_monitor
        config[config.py<br/>TOML + Doppler]
        
        subgraph data
            pipeline[pipeline.py]
            appwrite[appwrite_client.py]
            duckdb[duckdb_sync.py]
            portfolio[portfolio_history.py]
            sources[sources/fred_feed.py]
        end

        subgraph models
            macro[macro.py]
            hrp[math/hrp_sizer.py]
        end

        subgraph agent
            fusion[fusion.py]
            optimizer[optimizer.py]
            risk[risk_manager.py]
        end

        subgraph backtest
            topo[topological_run.py]
            metrics[metrics.py]
            behav[behavioural.py]
        end

        subgraph dashboard
            app[app.py]
        end
    end

    config --> pipeline
    config --> macro
    config --> optimizer
    config --> risk

    pipeline --> appwrite
    pipeline --> sources
    appwrite --> duckdb
    duckdb --> topo
    duckdb --> portfolio

    macro --> fusion
    pipeline --> fusion
    fusion --> optimizer
    optimizer --> risk

    risk --> topo
    topo --> metrics
    topo --> hrp
    metrics --> app
    portfolio --> app

    style config fill:#f59e0b,stroke:#f59e0b,color:#000
    style fusion fill:#eb5e28,stroke:#eb5e28,color:#fff
    style optimizer fill:#eb5e28,stroke:#eb5e28,color:#fff
    style app fill:#00ff88,stroke:#00ff88,color:#000
```

---

## 6. Backtest Walk-Forward Timeline

```mermaid
gantt
    title Walk-Forward Backtest Windows (252d train / 21d test)
    dateFormat YYYY-MM-DD
    axisFormat %Y-%m

    section Window 1
    Train (252d)       :t1, 2019-01-01, 252d
    Test (21d)         :crit, after t1, 21d

    section Window 2
    Train (252d)       :t2, 2019-01-22, 252d
    Test (21d)         :crit, after t2, 21d

    section Window 3
    Train (252d)       :t3, 2019-02-12, 252d
    Test (21d)         :crit, after t3, 21d

    section Window 4
    Train (252d)       :t4, 2019-03-05, 252d
    Test (21d)         :crit, after t4, 21d

    section Window 5
    Train (252d)       :t5, 2019-03-26, 252d
    Test (21d)         :crit, after t5, 21d
```

---

## 7. HRP Recursive Bisection Tree

```mermaid
graph TD
    ROOT["Portfolio<br/>w = 1.00"] --> C0["Cluster 0<br/>α = 0.62"]
    ROOT --> C1["Cluster 1<br/>1 - α = 0.38"]

    C0 --> L0["AAPL<br/>σ = 0.28<br/>w = 0.35"]
    C0 --> L1["NVDA<br/>σ = 0.35<br/>w = 0.27"]

    C1 --> L2["TSLA<br/>σ = 0.52<br/>w = 0.21"]
    C1 --> L3["PLTR<br/>σ = 0.61<br/>w = 0.17"]

    style ROOT fill:#eb5e28,color:#fff
    style C0 fill:#3b82f6,color:#fff
    style C1 fill:#8b5cf6,color:#fff
    style L0 fill:#1e1e2e,stroke:#3b82f6,color:#f4f4f5
    style L1 fill:#1e1e2e,stroke:#3b82f6,color:#f4f4f5
    style L2 fill:#1e1e2e,stroke:#8b5cf6,color:#f4f4f5
    style L3 fill:#1e1e2e,stroke:#8b5cf6,color:#f4f4f5
```

---

## 8. Black-Litterman Pipeline

```mermaid
flowchart LR
    subgraph PRIOR["Market Prior"]
        MW[Market-Cap Weights<br/>w_mkt] --> PI["Π = δΣw_mkt<br/>Implied Returns"]
    end

    subgraph VIEWS["Investor Views"]
        S1[Technical Score] --> P[Pick Matrix P]
        S2[Fundamental Score] --> P
        S3[Macro Score] --> P
        P --> Q["View Returns Q"]
        P --> OM["Ω = diag(Idzorek)"]
    end

    subgraph POSTERIOR["Posterior"]
        PI --> BL["BL Formula<br/>E[R] = [(τΣ)⁻¹ + PᵀΩ⁻¹P]⁻¹<br/>× [(τΣ)⁻¹Π + PᵀΩ⁻¹Q]"]
        Q --> BL
        OM --> BL
        BL --> ER["Posterior E[R]"]
    end

    ER --> MVO["Max Sharpe MVO<br/>w* = argmax SR"]

    style PRIOR fill:#1e1e2e,stroke:#3b82f6,color:#f4f4f5
    style VIEWS fill:#1e1e2e,stroke:#f59e0b,color:#f4f4f5
    style POSTERIOR fill:#1e1e2e,stroke:#00ff88,color:#f4f4f5
    style MVO fill:#eb5e28,color:#fff
```

---

## 9. Risk Manager Guard Rails

```mermaid
flowchart TD
    TRADE[Proposed Trade] --> CHK1{Position Size<br/>< max_position?}
    CHK1 -->|No| REJECT[Reject / Scale]
    CHK1 -->|Yes| CHK2{Sector Exposure<br/>< max_sector?}
    CHK2 -->|No| REJECT
    CHK2 -->|Yes| CHK3{Portfolio Beta<br/>< β_max?}
    CHK3 -->|No| REJECT
    CHK3 -->|Yes| CHK4{Kill Switch<br/>loss < 15%?}
    CHK4 -->|No| KILL[Emergency Liquidate]
    CHK4 -->|Yes| APPROVE[Execute Trade]

    APPROVE --> LOG[Log to Appwrite]

    style TRADE fill:#3b82f6,color:#fff
    style REJECT fill:#ff3366,color:#fff
    style KILL fill:#ff3366,color:#fff
    style APPROVE fill:#00ff88,color:#000
```

---

## 10. CI/CD Pipeline

```mermaid
flowchart LR
    subgraph DEV["Developer"]
        CODE[Write Code] --> PUSH[git push]
    end

    subgraph CI["GitHub Actions"]
        PUSH --> LINT[Ruff Lint]
        LINT --> TYPE[Pyright Type Check]
        TYPE --> TEST[pytest<br/>84 unit tests]
        TEST --> COV[Coverage Report]
    end

    subgraph DEPLOY["Deployment"]
        COV -->|pass| BUILD[Build Frontend Assets]
        BUILD --> DASH[Deploy Dashboard]
        COV -->|fail| NOTIFY[Slack/Email Alert]
    end

    style DEV fill:#1e1e2e,stroke:#3b82f6,color:#f4f4f5
    style CI fill:#1e1e2e,stroke:#f59e0b,color:#f4f4f5
    style DEPLOY fill:#1e1e2e,stroke:#00ff88,color:#f4f4f5
```

---

## 11. Appwrite Collections Schema

```mermaid
erDiagram
    PORTFOLIO_SNAPSHOTS {
        string snapshot_id PK
        datetime timestamp
        float total_value
        float cash
        string regime
    }

    POSITION_SNAPSHOTS {
        string position_id PK
        string snapshot_id FK
        string ticker
        float shares
        float market_value
        float weight
        float unrealized_pnl
    }

    SIGNALS {
        string signal_id PK
        datetime timestamp
        string ticker
        float technical_score
        float fundamental_score
        float sentiment_score
        float fused_score
        float confidence
    }

    EOD_PRICE_MATRIX {
        string price_id PK
        datetime timestamp
        string ticker
        float close
    }

    REGIME_HISTORY {
        string regime_id PK
        datetime timestamp
        string regime
        float vix
        float spread_10y2y
        float dxy_change
        int crisis_count
    }

    ALERTS {
        string alert_id PK
        datetime timestamp
        string severity
        string message
        string source
    }

    CORRELATIONS_CACHE {
        string cache_id PK
        datetime computed_at
        string ticker_pair
        float correlation
        int window_days
    }

    PORTFOLIO_SNAPSHOTS ||--o{ POSITION_SNAPSHOTS : contains
    PORTFOLIO_SNAPSHOTS ||--o{ REGIME_HISTORY : tagged_with
    SIGNALS ||--o{ PORTFOLIO_SNAPSHOTS : drives
    EOD_PRICE_MATRIX ||--o{ CORRELATIONS_CACHE : computed_from
```

---

## 12. Fama-French Factor Model

```mermaid
flowchart LR
    RP["R_p - R_f<br/>Excess Return"] --> DECOMP["Factor Regression"]
    
    DECOMP --> MKT["β₁(R_m - R_f)<br/>Market Risk Premium"]
    DECOMP --> SMB["β₂ × SMB<br/>Small Minus Big"]
    DECOMP --> HML["β₃ × HML<br/>High Minus Low"]
    DECOMP --> ALPHA["α (Alpha)<br/>Manager Skill"]
    DECOMP --> EPS["ε<br/>Residual Noise"]

    subgraph BRINSON["Brinson Attribution"]
        AA["Allocation Effect<br/>Σ(wP - wB)(rB - R)"]
        SE["Selection Effect<br/>Σ wB(rP - rB)"]
        IE["Interaction Effect<br/>Σ(wP - wB)(rP - rB)"]
    end

    ALPHA --> AA
    ALPHA --> SE
    ALPHA --> IE

    style RP fill:#3b82f6,color:#fff
    style ALPHA fill:#00ff88,color:#000
    style MKT fill:#1e1e2e,stroke:#3b82f6,color:#f4f4f5
    style SMB fill:#1e1e2e,stroke:#8b5cf6,color:#f4f4f5
    style HML fill:#1e1e2e,stroke:#f59e0b,color:#f4f4f5
```

---

## 13. Topological Backtest Flow

```mermaid
flowchart TD
    START[Load DuckDB<br/>eod_price_matrix] --> SPLIT[Walk-Forward Split<br/>252d train / 21d test]
    
    SPLIT --> TRAIN[Training Window]
    TRAIN --> LRET[Log Returns<br/>ln(P_t / P_{t-1})]
    LRET --> GLASSO[Graphical Lasso CV<br/>Sparse Precision Matrix]
    GLASSO --> PCORR["Partial Correlation<br/>ρ_ij = -Θ_ij / √(Θ_ii·Θ_jj)"]
    PCORR --> DIST["Distance Matrix<br/>D_ij = √(½(1-ρ_ij))"]
    DIST --> LINK[Single-Linkage<br/>Clustering]
    LINK --> HRP[HRP Recursive<br/>Bisection Weights]
    
    SPLIT --> TEST[Test Window]
    HRP --> EVAL[Apply Weights<br/>to Test Period]
    TEST --> EVAL
    
    EVAL --> METRICS[Compute Metrics]
    METRICS --> SHARP[Sharpe Ratio<br/>(μ-rf)/σ × √252]
    METRICS --> SORT[Sortino Ratio<br/>Downside Only]
    METRICS --> CALMAR[Calmar Ratio<br/>CAGR / Max DD]
    METRICS --> CVAR["CVaR 5%<br/>Cornish-Fisher"]
    METRICS --> MDD[Max Drawdown]

    style START fill:#8b5cf6,color:#fff
    style GLASSO fill:#eb5e28,color:#fff
    style HRP fill:#00ff88,color:#000
    style METRICS fill:#3b82f6,color:#fff
```

---

## 14. FRED Macro Data Sources

```mermaid
graph TD
    FRED[FRED API] --> VIX["VIXCLS<br/>VIX Index"]
    FRED --> DXY["DTWEXBGS<br/>Dollar Index"]
    FRED --> Y10["DGS10<br/>10-Year Yield"]
    FRED --> Y2["DGS2<br/>2-Year Yield"]
    FRED --> Y3M["DTB3<br/>3-Month T-Bill"]
    FRED --> FF["FEDFUNDS<br/>Fed Funds Rate"]
    FRED --> UNEMP["UNRATE<br/>Unemployment"]

    VIX --> VSIG["VIX Signal<br/>15-25: +1→0<br/>25-35: 0→-1"]
    Y10 --> SPREAD["Spread = 10Y - 2Y"]
    Y2 --> SPREAD
    SPREAD --> INV{Inverted?<br/>spread < 0}
    DXY --> DCHG["Weekly Δ%<br/>penalty if > 2%"]
    Y10 --> YSPK["Weekly Δbps<br/>penalty if > 20bps"]

    VSIG --> REGIME[Regime Classifier]
    INV --> REGIME
    DCHG --> REGIME
    YSPK --> REGIME

    style FRED fill:#14b8a6,color:#fff
    style REGIME fill:#eb5e28,color:#fff
```

---

## 15. Frontend Architecture

```mermaid
graph TD
    subgraph PAGES["HTML Pages"]
        IDX[index.html<br/>Main Dashboard]
        RES[results.html<br/>Backtest Results]
        JRN[journal.html<br/>Trade Journal]
        RSH[research.html<br/>Research Notes]
    end

    subgraph STYLES["CSS Layer"]
        TOK[tokens.css<br/>Design Tokens]
        PG[pages.css<br/>Page Layouts]
    end

    subgraph JS["JavaScript"]
        MAIN[main.js<br/>DOM + Fetch]
    end

    subgraph BACKEND["Python Backend"]
        PLOTLY[generate_plotly_dashboard.py]
        TEAR[generate_tearsheet.py]
        BUILD[build_frontend_assets.py]
    end

    TOK --> IDX
    TOK --> RES
    PG --> IDX
    PG --> RES
    MAIN --> IDX
    PLOTLY --> RES
    TEAR --> RES
    BUILD --> PAGES

    style PAGES fill:#1e1e2e,stroke:#3b82f6,color:#f4f4f5
    style STYLES fill:#1e1e2e,stroke:#8b5cf6,color:#f4f4f5
    style JS fill:#1e1e2e,stroke:#f59e0b,color:#f4f4f5
    style BACKEND fill:#1e1e2e,stroke:#00ff88,color:#f4f4f5
```

---

## 16. Metrics Computation Reference

| Metric | Formula | Module |
|--------|---------|--------|
| **Sharpe Ratio** | `(μ - r_f) / σ × √252` | `backtest/metrics.py` |
| **Sortino Ratio** | `(μ - r_f) / σ_down × √252` | `backtest/metrics.py` |
| **Calmar Ratio** | `CAGR / \|Max Drawdown\|` | `backtest/metrics.py` |
| **Treynor Ratio** | `(μ - r_f) / β` | `dashboard/app.py` |
| **Jensen's Alpha** | `R_p - [r_f + β(R_m - r_f)]` | `dashboard/app.py` |
| **VaR (Cornish-Fisher)** | `μ + z_CF × σ` | `backtest/metrics.py` |
| **CVaR** | `E[R \| R ≤ VaR]` | `backtest/metrics.py` |
| **Max Drawdown** | `min((NAV - peak) / peak)` | `backtest/metrics.py` |
| **Drawdown Duration** | `max consecutive days below peak` | `backtest/metrics.py` |
| **Tail Ratio** | `\|percentile(95)\| / \|percentile(5)\|` | `backtest/metrics.py` |
| **Portfolio Beta** | `Σ w_i × β_i` | `agent/risk_manager.py` |
| **HRP Distance** | `√(½(1 - ρ_ij))` | `models/math/hrp_sizer.py` |

---

## 17. Configuration Reference

| Section | Key | Default | Purpose |
|---------|-----|---------|---------|
| `[holdings]` | `tickers` | AAPL,NVDA,TSLA... | Universe |
| `[risk]` | `max_position_pct` | 15% | Per-stock cap |
| `[risk]` | `max_sector_pct` | 25% | Sector cap |
| `[risk]` | `kill_switch_loss` | 15% | Emergency exit |
| `[risk]` | `drift_threshold` | 2% | Rebalance trigger |
| `[optimizer]` | `risk_free_rate` | 4% | BL prior |
| `[optimizer]` | `risk_aversion` | 2.5 | MVO λ |
| `[macro]` | `vix_threshold_high` | 35 | Crisis VIX |
| `[macro]` | `spread_inversion` | 0 | Yield curve |
| `[macro]` | `dxy_spike_pct` | 2% | Dollar shock |
| `[cache]` | `prices_ttl` | 300s | Price freshness |
| `[cache]` | `fundamentals_ttl` | 3600s | Fundamental data |

---

## 18. Fusion Agent Scoring

```mermaid
flowchart TD
    subgraph SIGNALS["Signal Sources (0-1 each)"]
        TECH["Technical<br/>MA crossover, RSI, MACD"]
        FUND["Fundamental<br/>P/E, EV/EBITDA, FCF"]
        SENT["Sentiment<br/>News NLP, social"]
        MACRO["Macro<br/>VIX, yield, regime"]
    end

    subgraph FUSION["Regime-Weighted Fusion"]
        RW["Regime Weights:<br/>RISK_ON: [0.3, 0.3, 0.2, 0.2]<br/>TRANSITION: [0.2, 0.2, 0.2, 0.4]<br/>CRISIS: [0.1, 0.1, 0.1, 0.7]"]
        SCORE["fused = Σ w_i × score_i"]
        CONF["confidence = 1 - std(scores)"]
    end

    TECH --> RW
    FUND --> RW
    SENT --> RW
    MACRO --> RW
    RW --> SCORE
    RW --> CONF

    SCORE --> DECISION{score > threshold?}
    CONF --> DECISION
    DECISION -->|Yes + High Conf| BUY[Generate Buy Signal]
    DECISION -->|No / Low Conf| HOLD[Hold / No Action]

    style SIGNALS fill:#1e1e2e,stroke:#3b82f6,color:#f4f4f5
    style FUSION fill:#1e1e2e,stroke:#eb5e28,color:#f4f4f5
    style BUY fill:#00ff88,color:#000
```

---

## 19. DuckDB Sync Flow

```mermaid
sequenceDiagram
    participant APP as Appwrite
    participant SYNC as DuckDBSync
    participant DB as DuckDB
    participant BT as Backtest

    SYNC->>APP: query eod_price_matrix<br/>(offset pagination)
    APP-->>SYNC: List[Document]
    SYNC->>SYNC: parse → DataFrame
    SYNC->>DB: CREATE TABLE IF NOT EXISTS<br/>eod_price_matrix
    SYNC->>DB: INSERT INTO eod_price_matrix<br/>ON CONFLICT(timestamp,ticker)<br/>DO UPDATE SET close = excluded.close
    SYNC->>APP: query live_spy_proxy
    APP-->>SYNC: SPY prices
    SYNC->>DB: INSERT INTO live_spy_proxy

    BT->>DB: SELECT ticker, timestamp, close<br/>FROM eod_price_matrix<br/>ORDER BY timestamp
    DB-->>BT: pd.DataFrame (pivoted)
    BT->>BT: compute log returns
    BT->>BT: GraphicalLassoCV → precision
    BT->>BT: HRP allocation
```

---

## 20. Kill Switch & Emergency Flow

```mermaid
flowchart TD
    MONITOR[Position Monitor<br/>runs every tick] --> CHECK{Any position<br/>loss > 15%?}
    CHECK -->|No| CONTINUE[Continue Trading]
    CHECK -->|Yes| KILL[KILL SWITCH TRIGGERED]
    
    KILL --> FREEZE[Freeze All Orders]
    FREEZE --> LIQUIDATE[Market Sell Position]
    LIQUIDATE --> ALERT[Push Alert to Appwrite]
    ALERT --> NOTIFY[Dashboard Warning<br/>+ Slack Webhook]
    NOTIFY --> REVIEW[Human Review Required]

    REVIEW --> RESUME{Manually Cleared?}
    RESUME -->|Yes| CONTINUE
    RESUME -->|No| HALT[System Halted]

    style KILL fill:#ff3366,color:#fff,stroke:#ff3366
    style LIQUIDATE fill:#ff3366,color:#fff
    style HALT fill:#ff3366,color:#fff
    style CONTINUE fill:#00ff88,color:#000
```
