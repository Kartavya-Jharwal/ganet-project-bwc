# Documentation source (`docs/`)

MkDocs source for the technical site (built to `frontend/docs/`).

## Layout

| Path | Purpose |
|------|---------|
| `index.md` | Site home (Team BWC post-mortem framing) |
| `phases/` | Public implementation timeline (phases 0–21) |
| `phase-22-onwards-advanced-analytics.md` | Post-21 analytics |
| `phase-finale-endgame.md` | Sunset / endgame |
| `roadmap.md` | Detailed roadmap (reference) |
| `performance.md`, `backtest-results.md`, `signals-history.md`, `monte-carlo-forward.md` | Exported results (regenerate via `scripts/export_for_archive.py`) |
| `*.json` | Machine-readable backtest / MC outputs |
| `archive/` | Internal history: tasks, Manim sources, legacy viz HTML (~13MB), scratch |
| `stylesheets/` | MkDocs Material overrides |

## Not in this folder

- **Committee deliverables:** [`../deliverables/`](../deliverables/README.md)
- **Microsite HTML:** [`../frontend/`](../frontend/index.html)
- **Quant engine:** [`../quant_monitor/`](../quant_monitor/)

## Build

```bash
uv run python -m mkdocs build -f docs/mkdocs.yml --strict
```

Excluded from the published site (see `mkdocs.yml` `exclude_docs`): `archive/`, `*.py`, redirect stubs removed.
