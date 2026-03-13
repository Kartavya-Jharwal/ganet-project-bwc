# Phase 11-21 Track: The Critical Simulation & Vanguard Showcase

## The Philosophy: A "High-Ticket" Operation

This pipeline is no longer a standard algorithmic trading script—it is a **critical market simulation** engineered to solve granular microstructure issues (like 15-minute platform latency) while operating under strict, elegant architectural constraints.

By eliminating heavy NLP (HuggingFace) and brittle cloud deployments, we build an infallible **Local-First Mathematical Engine** backed by **Appwrite Cloud Caching**. Anyone—a professor, a teammate, or an evaluator—can clone, sync, and run the complete simulation with strictly zero API configuration. 

Ultimately, this project morphs from a mere "Python script" into a **Museum-Grade Algorithmic Showcase**. Through the introduction of theoretical topological graph pruning, `manim` powered mathematical storytelling, and an **Awwwards-level Vanguard Vanilla Web Frontend**, this becomes a high-conviction portfolio signaling tool *and* a masterclass in Technical Product Management and Engineering Taste.

---

## Part I: The Sterile Foundation & Data Engine

### Phase 11: Architectural Clean Slate & Strict Dependency Locking
**Objective:** Strip away the noise to establish an unassailable codebase.
- **Granular Tasks:**
  - Enforce strict `pyproject.toml` dependency boundaries (e.g., `uv`, `scikit-learn`, `networkx`, `scipy`).
  - Add `manim` for math animation and `rich` for CLI aesthetics.
  - Implement a deeply structured project skeleton: `/math`, `/data`, `/simulation`, `/viz`.
  - Set up pre-commit hooks (`ruff`, `mypy`) to assert aesthetic, typed Python across all commits.
- **Vibe:** Brutalist, zero-tolerance codebase logic. No orphaned files, no unused imports.

### Phase 12: Dual-State Appwrite Caching Engine (Zero-Config Ops)
**Objective:** Guarantee reproducibility by centralizing data ingestion.
- **Granular Tasks:**
  - Build `Ingestor.py`: Runs solely on the PM's machine, polling live APIs and normalizing to strict JSON arrays.
  - Push arrays sequentially into **Appwrite Cloud** collections: `eod_price_matrix`, `live_spy_proxy`, `correlations_cache`.
  - Build `Consumer.py`: The default read-only client. If `.env` is empty, it fails-over cleanly to read Appwrite streams and caches them into a local, single-file `duckdb`.
- **The Magic:** Teammates run `uv run sim`. The terminal spins up identically on their machine using cloud-synchronized arrays, sidestepping all rate-limits.

---

## Part II: The Topological Math Engine

### Phase 13: Phase 1 — Weighted Correlation Graph (Sparse Inverse Covariance)
**Objective:** Expose the "Illusion of Diversification."
- **Granular Tasks:**
  - Compute daily rolling standardized returns arrays ($R$).
  - Deploy Scikit-learn’s `GraphicalLassoCV` across a multi-fold cross-validation scheme to find the precision matrix ($\Theta$).
  - Establish an absolute Adjacency Matrix highlighting exact correlation topologies.
- **Output:** A strict Edgelist mapping the internal systemic risks hidden beneath standard fundamental sector classifications.

### Phase 14: Phase 2 — Hierarchical Risk Parity (HRP) Position Sizing
**Objective:** Algorithmically neutralize variance impacts without using "dumb stops."
- **Granular Tasks:**
  - Compute a quasi-distance matrix from the correlation graph.
  - Use SciPy `linkage` to calculate Tree Clustering (Quasi-Diagonalization).
  - Implement Recursive Bisection to assign capital proportionally to the *Inverse Trailing Variance* (using ATR) of each isolated node cluster.
- **Output:** The absolute quantitative portfolio weights to equalize market forces across the 27-asset closed universe.

### Phase 15: Phase 3 — The Continuous 15-Minute Drift Predictor
**Objective:** Out-engineer the simulation platform's forced 15-minute price lag latency.
- **Granular Tasks:**
  - Compute rolling 60-day structural Beta against the S&P 500 (`SPY`).
  - Wire a live-feed ping to standard `SPY` spot prices (available globally with 1-second latency).
  - Inject Drift formula: $P_{asset(synthetic)} = P_{platform(t-15)} + (\Delta SPY 	imes eta_{asset})$.
- **Output:** Execution terminal outputs precisely padded **Limit Order** pricing, ensuring the human operator never chases a stale trend.

### Phase 16: Phase 4 — Minimum Spanning Tree (MST) Pruning
**Objective:** Simplify complex capital interactions to only their most structurally significant edges.
- **Granular Tasks:**
  - Feed the Covariance distance map into `NetworkX`.
  - Apply Kruskal's Algorithm to generate an acyclic Minimum Spanning Tree.
  - Identify redundant "Branch" nodes connected merely as risk amplifiers.
- **Output:** Autonomous "Prune/Sell" signals to isolate "Hubs" (Systemic foundations) and "Islands" (Independent Alpha) in the network.

---

## Part III: Orchestration & The "Zero-IQ" Runbook

### Phase 17: Local Headless Orchestration
**Objective:** Merge the 4 math phases into a continuous time-series loop.
- **Granular Tasks:**
  - Develop `SimulationRunner`: a step-by-step looping protocol covering the exact timeline of the BBA Investment Simulation.
  - Track simulated P&L vs Market P&L internally in `duckdb`.

### Phase 18: Systemic Validation (Out-of-Sample Backtesting)
**Objective:** Pure statistical proof of edge.
- **Granular Tasks:**
  - Compare "Naive Equal Weight" vs "HRP Optimized" paths.
  - Measure Sharpe, Sortino ratios, and maximum drawdowns using the pre-simulation period structure.

### Phase 19: The "Executive Runbook" & CLI Aesthetics
**Objective:** The presentation begins in the terminal.
- **Granular Tasks:**
  - Create a master `Makefile` (or `justfile`): `make install`, `make sync-cache`, `make run-sim`.
  - Implement `rich` terminal panels: glowing progress spinners, live ASCII math rendering, formatted summary tables of the Spanning Tree. Professional typography inside the command line.

---

## Part IV: The Vanguard Showcase (The Art of Quant)

### Phase 20: Algorithmic Storytelling via `Manim`
**Objective:** Prove you understand the underlying mathematics by literally animating its topology.
- **Granular Tasks:**
  - Write declarative Python `manim` scenes to produce 4K 60fps MP4s/WebMs.
  - **Scene 1 (The Illusion):** 27 standard stock logos morph into a concentrated web of 3 actual risk hubs.
  - **Scene 2 (The Prune):** The web visually strips down via MST Kruskal's simulation, leaving only the structural branch lines.
  - **Scene 3 (The Parity):** HRP scaling node sizes on screen relative to their Inverse ATR variance.

### Phase 21: Awwwards-Level Vanilla HTML/CSS Web Delivery
**Objective:** Break from generic MkDocs. Host the final research findings via a bespoke, brutalist, typography-first static site on the `gh-pages` branch.
- **Granular Tasks:**
  - Design a Swiss-grid, minimalist web presentation utilizing Vanilla HTML5, CSS3, and lightweight Javascript (No heavy JS frameworks natively needed, pure DOM mastery).
  - Integrate **Locomotive Scroll** or **GSAP** for butter-smooth narrative presentation padding.
  - Embed the exported `manim` WebM sequences as seamless, scroll-triggered contextual backgrounds driving the technical analysis reading.
  - Serve interactive SVG exports of the `NetworkX` charts.
  - Implement balanced layouts, absolute CSS visual hierarchy, intentioned whitespace, and professional `.woff2` font face pairings (e.g., Inter, JetBrains Mono, or custom grotesks).
- **The Final Result:** When an evaluator or quantitative recruiter views the GitHub Pages link, they don't see a standard Jupyter Notebook or basic Streamlit page. They experience a polished, narrative-driven case study proving holistic systems thinking, engineering restraint, mathematical prowess, and absolute professional taste.
