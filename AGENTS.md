# Agent guide — Adaptive Efficiency (archived)

**Status:** Engineering sunset complete (`2026-05-01`). **Adaptive Efficiency** is the project title for this read-mostly static archive (`deliverables/` + `quant_monitor/` + `frontend/`). Live Appwrite ingestion and schedulers are retired; the public site is **STATIC ARCHIVE** on GitHub Pages. **Publication seal** (one clean archive commit) is still open — see [frontend/PLAN.md](frontend/PLAN.md) and [REVIEWERS.md § archive seal](REVIEWERS.md#publication-checklist-archive-seal).

**Maintainer:** [Kartavya Jharwal](https://kartavya.tech) · MIT License — retain copyright notice when forking.

## Before you change anything

1. Read [REVIEWERS.md](REVIEWERS.md) and [README.md](README.md).
2. Primary narrative lives in [`deliverables/`](deliverables/README.md), not only `quant_monitor/`.
3. Prefer one-shot scripts under `scripts/` over `project sync-data` (scheduler).
4. After substantive edits: `uv run python scripts/verify_repo_health.py --strict-artifacts`.

## Safe commands

```bash
uv sync --frozen
uv run python -m pytest tests/ -m "not integration"
uv run python scripts/build_frontend_assets.py
uv run python -m mkdocs build -f docs/mkdocs.yml --strict
uv run python scripts/verify_repo_health.py
```

Full rebuild: `scripts/sunset_freeze.ps1` (Windows) or `scripts/sunset_freeze.sh`.

## Scope boundaries

| In scope | Out of scope (unless explicitly requested) |
|----------|---------------------------------------------|
| `frontend/` HTML/CSS/JS beautification | Re-enabling live Appwrite LIVE badge |
| `docs/` MkDocs copy and phase stubs | New trading logic or scheduler loops |
| `deliverables/` committee packet paths | Committing secrets, `.env`, Doppler tokens |
| `tests/`, `scripts/verify_repo_health.py` | Large binary churn without reason |

## Forking

You may fork under **MIT** with attribution:

- Keep `LICENSE` and copyright line for Kartavya Jharwal.
- Link back to this repository when publishing derivatives.
- Contact: [kartavya.tech](https://kartavya.tech)

## Key paths

- Config: `quant_monitor/config.toml`
- Journal parser: `quant_monitor/data/journal_trade_csv.py`
- Static data: `frontend/data/`, `frontend/charts/`, `docs/*.json`
- Internal only: `docs/archive/` (excluded from MkDocs site)
