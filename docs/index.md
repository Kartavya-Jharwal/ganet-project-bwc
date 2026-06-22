# Team BWC — Project BWC

> Hult Investment Challenge · public engineering archive · sunset `2026-05-01`

!!! success "Post-mortem framing"
    **Deliverables** ([committee packet](deliverables-index.md)) describe the full investment program. **`quant_monitor/`** documents the systematic audit layer—topology, walk-forward tests, and behavioural metrics—not the entire BWC capability surface.

!!! info "Archive status (June 2026)"
    Engineering sunset is **complete**. Live Appwrite ingestion and schedulers are **retired**. The public microsite (*Adaptive Efficiency*) is a static GitHub Pages archive. Publication seal commit is still open.

## What this site contains

- **Implementation phases 0–21:** [phase index](phases/README.md)
- **Advanced analytics (22+):** [phase-22-onwards-advanced-analytics.md](phase-22-onwards-advanced-analytics.md)
- **Sunset / endgame:** [phase-finale-endgame.md](phase-finale-endgame.md)
- **Results:** [performance](performance.md), [backtest](backtest-results.md), [Monte Carlo forward](monte-carlo-forward.md)
- **Microsite:** [Adaptive Efficiency](https://kartavya-jharwal.github.io/ganet-project-bwc/)

Faculty grades and peer feedback are reflected in the client deliverables; this docs tree is the **final engineering freeze**.

## Audit module (quant)

Sparse inverse covariance graphs (`GraphicalLassoCV`), HRP sizing, regime-weighted signal fusion, DuckDB EOD matrix, and journal-driven NAV reconstruction. See [external review](external-review.md) and [REVIEWERS.md](https://github.com/Kartavya-Jharwal/ganet-project-bwc/blob/main/REVIEWERS.md).

## Rebuild

Charts and narrative JSON: `uv run python scripts/build_frontend_assets.py` (optional; data may already be built).

```bash
bun run minify:frontend
uv run python -m mkdocs build -f docs/mkdocs.yml --strict
```

---

_Static archive · GitHub Pages · secrets via Doppler for local audits only · Team BWC 2026._
