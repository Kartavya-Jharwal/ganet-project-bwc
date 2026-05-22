# Team BWX — Project BWC

> Hult Investment Challenge · public engineering archive · sunset `2026-05-01`

!!! success "Post-mortem framing"
    **Deliverables** ([committee packet](deliverables-index.md)) describe the full investment program. **`quant_monitor/`** documents the systematic audit layer—topology, walk-forward tests, and behavioural metrics—not the entire BWX capability surface.

## What this site contains

- **Implementation phases 0–21:** [phase index](phases/README.md)
- **Advanced analytics (22+):** [phase-22-onwards-advanced-analytics.md](phase-22-onwards-advanced-analytics.md)
- **Sunset / endgame:** [phase-finale-endgame.md](phase-finale-endgame.md)
- **Results:** [performance](performance.md), [backtest](backtest-results.md), [Monte Carlo forward](monte-carlo-forward.md)
- **Microsite:** [telemetry & charts](https://kartavya-jharwal.github.io/ganet-project-bwc/results.html)

Faculty grades and peer feedback are reflected in the client deliverables; this docs tree is the **final engineering freeze**.

## Audit module (quant)

Sparse inverse covariance graphs (`GraphicalLassoCV`), HRP sizing, regime-weighted signal fusion, DuckDB EOD matrix, and journal-driven NAV reconstruction. See [external review](external-review.md) and [REVIEWERS.md](https://github.com/Kartavya-Jharwal/ganet-project-bwc/blob/main/REVIEWERS.md).

## Rebuild

```bash
uv run python scripts/build_frontend_assets.py
uv run python -m mkdocs build -f docs/mkdocs.yml --strict
```

---

_Deployed via GitHub Pages · optional Appwrite · secrets via Doppler · Team BWX 2026._
