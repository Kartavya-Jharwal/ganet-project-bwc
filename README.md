# Project Ganet · Adaptive Efficiency

[![Live site](https://img.shields.io/badge/site-GitHub%20Pages-24292f?style=flat-square&logo=github)](https://kartavya-jharwal.github.io/ganet-project-bwc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-a78bfa?style=flat-square)](LICENSE)
[![Archive](https://img.shields.io/badge/status-read--mostly-6b7280?style=flat-square)](REVIEWERS.md#publication-checklist-archive-seal)
[![Sunset](https://img.shields.io/badge/sunset-2026--05--01-6b7280?style=flat-square)](frontend/PLAN.md)

**Team BWC** · Hult CHL-0200 · independent unofficial archive

This repository is a localized deployment within the **Project Ganet** framework, an independent initiative mapping systemic financial literacy through an opinionated, first-principles design lens.

Where the upstream project isolates the abstract architecture of fluency, **Adaptive Efficiency** operates as a standalone case study. It represents one of a sequence of empirical trials designed to stress-test theoretical models against the messy constraints of live execution.

**June 2026 polish:** engineering sunset freeze completed **2026-05-01** (valuation `2026-04-10`). The repo is now read-mostly and being refined for academic, quant, and general audiences. Publication seal commit is still open. See [frontend/PLAN.md](frontend/PLAN.md).

**Maintainer:** [Kartavya Jharwal](https://kartavya.tech) · MIT — forks must retain [LICENSE](LICENSE) attribution.

> **Disclaimer** (from [live splash](frontend/index.html)): This archive is an independent, unofficial presentation of Team BWC's investment simulation. It is not affiliated with Hult, the Professor, or former teammates. While the layout and development were AI-assisted, official graded marks remain strictly bound to the submitted deliverables. All narrative reflections and interpretations are entirely my own. Faculty sign-off is closed (`422 / 430`). If this repository disagrees with the Excel close or filed memo, **the filed artifacts win**.

---

## Brand hierarchy

| Name | Role |
|------|------|
| **Ganet** / **Project Ganet** | Parent framework: financial literacy, first-principles design, case-study portfolio |
| **Adaptive Efficiency** | This standalone case study / empirical trial (Andrew Lo adaptive-markets lens on a short simulation) |
| **Team BWC** | Hult CHL-0200 desk that managed the $1M paper book (Team 5) |
| **Kartavya Jharwal** | Maintainer · [kartavya.tech](https://kartavya.tech) · logos at [`frontend/assets/PB_logos/`](frontend/assets/PB_logos/) |

Adaptive Efficiency is **not** a claim the desk beat the simulation (`-4.37%` graded close). It names how this case study is framed and presented.

---

## Start here

| Surface | URL / path |
|---------|------------|
| **Live site** | [kartavya-jharwal.github.io/ganet-project-bwc](https://kartavya-jharwal.github.io/ganet-project-bwc/) |
| Committee packet | [deliverables/](deliverables/README.md) (grading authority) · [download table](frontend/deliverables/index.html) |
| Presentation layer | [frontend/](frontend/index.html) · [frontend/README.md](frontend/README.md) · [frontend/PLAN.md](frontend/PLAN.md) |
| Engineering docs | MkDocs **source:** [docs/](docs/index.md) → rebuild to [frontend/docs/](frontend/docs/) |
| Code review | [REVIEWERS.md](REVIEWERS.md) (includes [archive seal checklist](REVIEWERS.md#publication-checklist-archive-seal)) |
| Agent / fork guide | [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) |

| Audience | Path |
|----------|------|
| Economist / PM | Live splash disclaimer → **Sources** → **Desk** results → faculty **422/430** |
| Recruiter | Hero + executive summary + contact on the [live site](https://kartavya-jharwal.github.io/ganet-project-bwc/) |
| Code auditor | **Stack** section → [frontend/docs/](frontend/docs/) → [REVIEWERS.md](REVIEWERS.md) |

Machine-readable index: [frontend/llms.txt](frontend/llms.txt) · [frontend/data/site-summary.json](frontend/data/site-summary.json)

---

## Repository layers

| Layer | Path | Role |
|-------|------|------|
| Filed narrative | `deliverables/` | Committee PDF, Excel, charter, journals (**grading authority**) |
| Audit engine | `quant_monitor/` | Reproducible Python overlay (walk-forward, stress, behavioural audit) |
| Public presentation | `frontend/` | Single-page archive, charts, JSON hydration |
| Engineering depth | `docs/` | Ganet technical docs for this freeze (phases, backtest JSON, architecture) |

**Docs policy:** edit markdown under `docs/` only. Do not hand-edit built HTML in `frontend/docs/`. Rebuild with `uv run python -m mkdocs build -f docs/mkdocs.yml --strict`.

---

## GitHub repository metadata

| Field | Value |
|-------|-------|
| Homepage | [kartavya-jharwal.github.io/ganet-project-bwc/](https://kartavya-jharwal.github.io/ganet-project-bwc/) |
| Social preview image | [assets/og-card.png](https://kartavya-jharwal.github.io/ganet-project-bwc/assets/og-card.png) |

GitHub does not expose social preview upload through the `gh` CLI or REST API. Set it manually:

1. Open **Settings → General → Social preview** on the repository.
2. Upload the OG card from the live site URL above, or download from `frontend/assets/og-card.png` in this repo.

Full instructions: [docs/github-social-preview.md](docs/github-social-preview.md).

---

## Quick start

```bash
uv sync --frozen
.\scripts\sunset_freeze.ps1    # Windows — or scripts/sunset_freeze.sh
```

Manual steps:

```bash
uv run python scripts/prep_duckdb_and_sync.py
uv run python scripts/clean_duckdb_prices.py
uv run python -m pytest tests/ -m "not integration"
uv run python scripts/build_frontend_assets.py
bun run minify:frontend
uv run python -m mkdocs build -f docs/mkdocs.yml --strict
```

Before publication seal:

```bash
bun run minify:frontend
uv run python scripts/sync_deliverables_manual.py
uv run python scripts/verify_repo_health.py --strict-artifacts
```

---

## Repository map

```
deliverables/       Filed committee packet (PDF, Excel, charter, journals)
frontend/           Adaptive Efficiency public site (Ganet presentation layer)
quant_monitor/      Python audit engine (config, data, models, backtest, CLI)
scripts/            prep_duckdb, build_frontend_assets, export, sunset_freeze
tests/              Unit tests + journal_transaction_history.csv
docs/               Ganet MkDocs source, phases/, exported JSON/MD
docker/             Optional container entrypoint
```

**Not in git:** `portfolio.duckdb`, `.venv/`, secrets (Doppler).

---

## CLI (`project`)

| Command | Notes |
|---------|--------|
| `project doctor` | Environment check |
| `project run-backtest` | Walk-forward test |

Prefer `scripts/` for sunset. Avoid `project sync-data` (may start scheduler).

---

## License

MIT — see [LICENSE](LICENSE).
