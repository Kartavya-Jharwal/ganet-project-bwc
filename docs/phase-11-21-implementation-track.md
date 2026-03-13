# Phase 11-21 Track: The Critical Simulation & Vanguard Showcase

## The Philosophy: A "High-Ticket" Operation Building on Phases 1-10

This pipeline is no longer a standard algorithmic trading script—it is a **critical market simulation** engineered to solve granular microstructure issues (like 15-minute platform latency) while operating under strict, elegant architectural constraints.

**Crucially, this is NOT a ground-up rewrite.** We are building directly on top of the robust data pipelines, scheduling (APScheduler), and DuckDB infrastructure established in Phases 1-10. Phase 11 is about **surgical pruning** of incompatible heavy tech (like NLP/FinBERT and Heroku droplet configs) and laying the scaffolding for our deeply mathematical Phase 12-21 future.

Ultimately, this project morphs from a mere "Python script" into a **Museum-Grade Algorithmic Showcase**. Through the introduction of theoretical topological graph pruning, `manim` powered mathematical storytelling, and an **Awwwards-level Vanguard Vanilla Web Frontend**, this becomes a high-conviction portfolio signaling tool *and* a masterclass in Technical Product Management and Engineering Taste.

---

## Part I: Surgical Pruning & Data Engine Enhancements

### Phase 11: Surgical Pruning & Future Scaffolding
**Objective:** Cleanly remove the dead weight from Phase 1-10 and scaffold the directories for the new topological math engine, while preserving all valid data acquisition and caching pipelines.
- **Granular Tasks:**
  - **Prune Legacy NLP:** Eradicate all `sentiment.py`, `FinBERT` transformers dependencies, and Heroku deployment files (`Procfile`, `runtime.txt`).
  - **Retain Core Infrastructure:** Keep the existing `quant_monitor/data/pipeline.py` and `DuckDB`/`diskcache` mechanisms intact.
  - **Blueprint the Scaffold:** Create empty blueprint classes in a new `quant_monitor/models/math/` directory: `correlation_graph.py`, `hrp_sizer.py`, `drift_predictor.py`, and `mst_pruner.py`.
  - **Dependency Injection:** Seamlessly integrate `scikit-learn`, `networkx`, `scipy`, `manim`, and `rich` into the `uv` environment without breaking existing Phase 1-10 configurations.
  - **Linting Pass:** Run complete `ruff check` and `mypy` type validations to ensure the existing framework remains totally stable after pruning.

### Phase 12: Dual-State Appwrite Caching Engine (Zero-Config Ops)
**Objective:** Guarantee reproducibility by centralizing data ingestion, allowing teammates to run the system without API keys.
- **Granular Tasks:**
  - **Ingestor Mode (`--mode=ingest`):** Modify existing data pipelines so the PM's machine polls live APIs (Polygon, AlphaVantage) and normalizes them into strict JSON arrays.
  - **Appwrite Schema Automation:** Create dynamic Appwrite collections: `eod_price_matrix` (Tickers x Dates), `live_spy_proxy`, and `correlations_cache`. Push batches of 100+ documents using async I/O.
  - **Consumer Mode (`--mode=consume`):** If a local `.env` is empty, the pipeline auto-switches to fetch from Appwrite via `list_documents`, bypassing API rate limits.
  - **DuckDB Sync:** Write a reconciliation script that takes the Consumer Mode Appwrite payload and efficiently `INSERT OR REPLACE` into the local Phase 1-10 `portfolio.duckdb`.

---

## Part II: The Topological Math Engine

### Phase 13: Phase 1 — Weighted Correlation Graph (Sparse Inverse Covariance)
**Objective:** Expose the "Illusion of Diversification" mathematically.
- **Granular Tasks:**
  - **Query Builder:** Extract a pivoted `pandas.DataFrame` array of continuous log returns ($R$) spanning 252 days from `duckdb`.
  - **StandardScaler Processing:** Pass returns through a rigorous mean-variance scaler to neutralize anomalous outlier days (e.g., earnings gaps) before matrix correlation.
  - **GraphicalLasso CV Loop:** Implement `Scikit-learn’s` `GraphicalLassoCV` utilizing a 5-fold cross-validation loop to compute the optimized precision matrix ($\Theta$) without overfitting the noise.
  - **Inversion & Thresholding:** Invert the precision matrix to extract true conditional independence. Apply a rigid static threshold (e.g., drop edges where $\rho < 0.2$) to enforce sparsity.
  - **State Output:** Output an explicit Adjacency Matrix edgelist DataFrame and push the topology map to Appwrite to lock in the day's calculation.

### Phase 14: Phase 2 — Hierarchical Risk Parity (HRP) Position Sizing
**Objective:** Algorithmically neutralize variance impacts without using legacy "dumb stops."
- **Granular Tasks:**
  - **Distance Metric:** Transform the Sparse Matrix into a true distance matrix using: $D_{i,j} = \sqrt{0.5 \times (1 - \rho_{i,j})}$.
  - **SciPy Linkage:** Run `scipy.cluster.hierarchy.linkage` utilizing the 'single' method to compute Tree Clustering (Quasi-Diagonalization).
  - **Asset Sorting:** Rearrange the portfolio array so that highly correlated clusters sit adjacent in the vector array.
  - **Recursive Bisection Calculation:** Loop through the matrix hierarchically. At each bifurcation, allocate capital precisely proportionate to the *Inverse Trailing Variance* (using ATR computed in Phase 2 feature engine) of the respective clusters.
  - **Sizing Output:** Emit a strict `{Ticker: %_Weight}` dictionary representing the daily variance-neutralized portfolio allocation targets.

### Phase 15: Phase 3 — The Continuous 15-Minute Drift Predictor
**Objective:** Out-engineer the simulation platform's forced 15-minute price lag latency.
- **Granular Tasks:**
  - **Rolling Beta Extraction:** Calculate standard 60-day historical Beta for all 27 assets against `SPY`.
  - **Live SPY Ping:** Wire a sub-second ping to an un-auth required live feed (like Yahoo Finance's quick-query endpoint) specifically for `SPY` spot.
  - **The Latency Trap:** Fetch the "last known" price from the simulation dashboard (Time $T-15$).
  - **The Drift Formula:** Calculate mathematical offset: $P_{target} = P_{t-15} \times (1 + (\beta_i \times \Delta SPY_{15m}))$.
  - **Order Generation:** Format the output as a literal actionable string: `[EXECUTABLE LIMIT] Asset: [AAPL] | Platform Price: [$150] | True Synthesized Market: [$151.25] | Action: Buy @ Target`.

### Phase 16: Phase 4 — Minimum Spanning Tree (MST) Pruning
**Objective:** Simplify complex capital interactions to only their most structurally significant edges.
- **Granular Tasks:**
  - **Graph Instantiation:** Feed the Phase 14 distance matrix directly into a `NetworkX.Graph()` object.
  - **Kruskal's Algorithm:** Execute `nx.minimum_spanning_tree(G)` to strip cyclical redundancy, isolating the acyclic skeleton of the market.
  - **Centrality Diagnostics:** Loop through the MST and calculate the Degree Centrality of every node. 
  - **Risk Identification Engine:** 
    * If `Degree > 4` (A Hub / Risk Amplifier): Emit a **Prune Warning** to physically reduce exposure.
    * If `Degree == 1` (A Leaf / Island): Emit an **Alpha Flag**, suggesting independent performance behavior unaffected by the index.

---

## Part III: Orchestration & The "Zero-IQ" Runbook

### Phase 17: Local Headless Orchestration Integrations
**Objective:** Merge the 4 math phases smoothly into the existing Phase 1-10 `apscheduler` loop.
- **Granular Tasks:**
  - **Execution Pathing:** Inject the topology loop explicitly into `main.py`’s cycle: `Data Pull -> Appwrite Sync -> Graph Lasso -> HRP -> MST Pruning -> Drift Adjustment`.
  - **DuckDB State Trapping:** Save every run cycle's final weight targets and NetworkX edges as JSON strings in a DuckDB `audit_log` table.
  - **Error Bubbling:** Implement `try/except` guardrails around `GraphicalLassoCV` specifically; if it fails to converge, cleanly fallback to Phase 1-10 equal-weight logic.

### Phase 18: Systemic Validation (Out-of-Sample Backtesting)
**Objective:** Pure statistical proof of edge for the final presentation.
- **Granular Tasks:**
  - **Execution Sandbox:** Write `backtest/topological_run.py` to loop strictly over 2024-2025 EOD OHLCV data.
  - **Step-Forward Logic:** Advance the simulation 21 days at a time, strictly re-computing the Covariance and HRP weights without look-ahead bias.
  - **Delta Tracking:** Compute a continuous cumulative return vector combining `Naive Equal Weight` vs `Topological HRP` performance.
  - **Metric Extraction:** Output Sharpe, Sortino ratios, and maximum drawdowns into a serialized JSON for Phase 21 rendering.

### Phase 19: The "Executive Runbook" & CLI Aesthetics
**Objective:** Make operating the system a visually commanding experience.
- **Granular Tasks:**
  - **Make/Typer Commands:** Implement `typer` in `quant_monitor/cli.py` yielding exact command syntaxes: `uv run cli dashboard`, `uv run cli ingest`.
  - **Rich Terminal UI:** 
    * Replace standard logging prints with `rich.console`. 
    * Use `rich.progress` bars to animate the cross-validation Lasso loops. 
    * Use `rich.table` to print the final 15-minute Drift Limit Order targets with styled color gradients (Green=Buy, Red=Sell).

---

## Part IV: The Vanguard Showcase (The Art of Quant)

### Phase 20: Algorithmic Storytelling via `Manim`
**Objective:** Prove you understand the underlying mathematics by literally animating its topology.
- **Granular Tasks:**
  - **Scene 1 (The Illusion):** Write a `manim` class `ScatterToNetwork` that plots the 27 tickers randomly on an XY plane, then animates thick lines drawing between highly correlated assets to reveal the hidden hubs.
  - **Scene 2 (The Prune):** Write a `KruskalSequence` class that slowly fades out weakest correlation lines, leaving precisely the Minimum Spanning Tree glowing in the center of the frame.
  - **Scene 3 (The Parity Sizing):** Write `NodeResizer` class where nodes pulse and dynamically resize their radius exactly proportional to their Inverse ATR variance (HRP output).
  - **Rendering Engine:** Compile to 1080p / 60fps MP4 loops natively through `manim -pqm scenes.py`.

### Phase 21: Awwwards-Level Vanilla HTML/CSS Web Delivery
**Objective:** Break from generic MkDocs. Host the final research findings via a bespoke, brutalist, typography-first static site on the `gh-pages` branch.
- **Granular Tasks:**
  - **Layout & Structure:** Hand-code an `index.html` featuring a sticky side-navigation and an oversized, typographic hero section introducing the simulation thesis.
  - **Locomotive / Intersection Scroll:** Write pure DOM Javascript `IntersectionObserver` loops to trigger fade-ups and text reveals as the user scrolls down the "Case Study".
  - **Background Media Loops:** Embed the Phase 20 `manim` `.mp4` files as absolute positioned, `z-index: -1`, `autoplay loop muted` backgrounds underneath translucent frosted-glass content cards.
  - **Interactive D3/SVG Maps:** Export the NetworkX MST graphs to interactive SVGs allowing hover-tooltips for the professor to click and see specific node statistics.
  - **Typographic System:** Enforce a brutally tight CSS grid system with explicit standardizations using highly legible fonts (e.g., JetBrains Mono for data points intermixed with Inter/Roboto for body text).
- **The Final Result:** When an evaluator or quantitative recruiter views the GitHub Pages link, they experience a polished, narrative-driven case study proving holistic systems thinking, engineering restraint, mathematical prowess, and absolute professional taste.
