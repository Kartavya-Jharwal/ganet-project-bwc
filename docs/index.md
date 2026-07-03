# Project Ganet · Adaptive Efficiency

> **Project Ganet** parent framework · **Team BWC** desk · Hult CHL-0200 · sunset `2026-05-01`

**Project Ganet** is the parent framework mapping systemic financial literacy through first-principles design. **Adaptive Efficiency** is this repository's standalone case study: a ten-week $1M paper desk post-mortem with filed deliverables, `quant_monitor/` audit code, and a static presentation site.

These MkDocs pages document the engineering freeze for this archive. The graded investment narrative lives in [deliverables](deliverables-index.md). The [live site](https://kartavya-jharwal.github.io/ganet-project-bwc/) is the primary human entry point.

!!! info "Archive status"
    Engineering sunset is **complete**. Live Appwrite ingestion and schedulers are **retired**. The public site is a static GitHub Pages archive. Publication seal landed **2026-07-03**. See [REVIEWERS.md](https://github.com/Kartavya-Jharwal/ganet-project-bwc/blob/main/REVIEWERS.md).

!!! warning "Disclaimer"
    Independent, unofficial archive. Not affiliated with Hult, the professor, or former teammates. AI-assisted layout and development. Graded marks bound to filed deliverables only. If these docs disagree with the Excel close or memo, **filed artifacts win**.

## Brand hierarchy

| Name | Role |
|------|------|
| **Ganet** / **Project Ganet** | Parent framework (financial literacy, first-principles design, case-study portfolio) |
| **Adaptive Efficiency** | Standalone empirical trial for this archive (adaptive-markets lens, not a performance claim) |
| **Team BWC** | Hult CHL-0200 desk that ran the simulation |

## What this site contains

- **Implementation phases 0–21:** [phase index](phases/README.md)
- **Advanced analytics (22+):** [phase-22-onwards-advanced-analytics.md](phase-22-onwards-advanced-analytics.md)
- **Sunset / endgame:** [phase-finale-endgame.md](phase-finale-endgame.md)
- **Results:** [performance](performance.md), [backtest](backtest-results.md), [Monte Carlo forward](monte-carlo-forward.md)
- **Public presentation:** [Adaptive Efficiency live site](https://kartavya-jharwal.github.io/ganet-project-bwc/)

Faculty grades and peer feedback are reflected in the client deliverables. This docs tree is the **final engineering freeze** for this Ganet case study.

## Audit module (`quant_monitor/`)

Sparse inverse covariance graphs (`GraphicalLassoCV`), HRP sizing, regime-weighted signal fusion, DuckDB EOD matrix, and journal-driven NAV reconstruction. See [external review](external-review.md) and [REVIEWERS.md](https://github.com/Kartavya-Jharwal/ganet-project-bwc/blob/main/REVIEWERS.md).

## Rebuild (source only)

Rebuilds `frontend/docs/` from this folder. Do not hand-edit built HTML under `frontend/docs/`.

```bash
bun run minify:frontend
uv run python -m mkdocs build -f docs/mkdocs.yml --strict
```

Optional chart and narrative JSON refresh: `uv run python scripts/build_frontend_assets.py`

---

_Static archive · Ganet · GitHub Pages · Team BWC 2026._
