# External code review guide

**Team BWX / Project BWC** — this guide is for **software auditors**. The primary public narrative (client post-mortem, charter, Excel model) lives in [`deliverables/`](../deliverables/README.md); faculty feedback is already incorporated there.

This document orients code reviewers who do not have Doppler secrets or live Appwrite access.

## What to review first

| Priority | Path | Purpose |
|----------|------|---------|
| 1 | `quant_monitor/config.toml` | Holdings, valuation/sunset dates, non-secret parameters |
| 2 | `quant_monitor/data/journal_trade_csv.py` | Authoritative trade journal parser (no dividend inference) |
| 3 | `quant_monitor/data/portfolio_history.py` | NAV reconstruction from journal + market prices |
| 4 | `quant_monitor/models/math/` | Graphical Lasso, HRP, drift, correlation graph |
| 5 | `quant_monitor/backtest/topological_run.py` | Walk-forward validation |
| 6 | `quant_monitor/main.py` | Single signal cycle (scheduler optional) |
| 7 | `scripts/prep_duckdb_and_sync.py` | Fast local EOD matrix load (~20s) |
| 8 | `tests/` | Regression coverage for config, features, journal parser |

## Repository layout (sanitized)

```
project-bwc/
├── deliverables/           # Team BWX committee packet (primary narrative)
├── quant_monitor/          # Application package (audit module)
│   ├── config.toml         # Version-controlled configuration
│   ├── main.py             # Signal cycle entry (scheduler in main())
│   ├── cli.py              # Typer CLI (`project` command)
│   ├── data/               # Pipeline, DuckDB sync, portfolio history
│   ├── models/             # Topological math + agent fusion
│   ├── backtest/           # Walk-forward + Monte Carlo simulation
│   └── dashboard/          # Terminal dashboard
├── scripts/                # One-shot maintenance & asset builders
├── tests/                  # Unit tests + `test_data/` fixtures
├── docs/                   # MkDocs source + exported JSON/MD results
├── frontend/               # Static microsite (GitHub Pages target)
└── REVIEWERS.md            # This file
```

Excluded from git (see `.gitignore`): `portfolio.duckdb`, `.venv/`, `BWC/` client working copy (use `deliverables/source/`), root `data/`, Manim `media/` and `frontend/assets/videos/{Tex,texts,images,videos}/`, duplicate CSV exports under `docs/`, debug logs, secrets.

## Reproducing results without cloud secrets

```bash
uv sync --frozen
uv run python scripts/prep_duckdb_and_sync.py
uv run python scripts/clean_duckdb_prices.py    # if legacy rows reappear
uv run python -m pytest tests/ -m "not integration"
uv run python scripts/build_frontend_assets.py
uv run python -m mkdocs build -f docs/mkdocs.yml
```

Optional (requires Doppler):

```bash
doppler run -- uv run python -c "from quant_monitor.main import run_signal_cycle; run_signal_cycle()"
doppler run -- uv run python scripts/export_for_archive.py
```

## Sunset freeze dates

| Field | Value |
|-------|-------|
| `valuation_date` | 2026-04-10 |
| `sunset_date` | 2026-05-01 |
| `mc_forward_days` | 21 |

Trade ledger fixture: `tests/test_data/journal_transaction_history.csv` (mirrors the discretionary export; no dividends).

## Known limitations (documented honestly)

- **Walk-forward naive vs HRP**: On thin or mixed-scale matrices, Graphical Lasso may fail; backtest falls back to equal weight for that window.
- **Appwrite sync**: `DuckDBSync` pulls a single page by default; local prep script writes the full matrix directly to DuckDB.
- **Scheduler**: `project sync-data` starts APScheduler; prefer one-shot scripts in `scripts/` for audits.

## Artifacts to cross-check

| Artifact | Location |
|----------|----------|
| Backtest JSON | `docs/backtest-results.json` |
| MC forward JSON | `docs/mc-forward-results.json` |
| Behavioural audit | `frontend/data/behavioural-audit.json` |
| Live metrics | `frontend/data/full-metrics.json` |
| Deliverables manifest | `frontend/data/deliverables-manifest.json` |

## Publication checklist (sunset seal)

Use this before tagging the archive or pushing to `main` for GitHub Pages.

1. **Rebuild static site:** `.\scripts\sunset_freeze.ps1` (or `scripts/sunset_freeze.sh`) — DuckDB prep, tests, `build_frontend_assets`, MkDocs `--strict`, optional `export_for_archive`.
2. **Health gate:** `uv run python scripts/verify_repo_health.py --strict-artifacts --require-clean-git`
3. **CI parity:** `uv run pytest tests/ -m "not integration"`, `uv run ruff check quant_monitor scripts tests`, `uv run ty check quant_monitor`, `uv run bandit -r quant_monitor/ -c pyproject.toml`, `uv run deptry .`
4. **Microsite checks:** open `frontend/index.html` — status badge reads **STATIC ARCHIVE** (no Appwrite LIVE); KPIs load from `frontend/data/results.json` after build.
5. **Deliverables:** `deliverables/source/` contains committee packet; `frontend/assets/post-mortem.pdf` mirrors client PDF.
6. **Hygiene:** no `quant_monitor/cli_old.py`, no root `BWC/` working copy, no secrets in git.
7. **Commit:** single sunset seal commit; push `main` to trigger Pages deploy job.
