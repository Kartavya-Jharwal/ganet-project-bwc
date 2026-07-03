# Adaptive Efficiency

*Team BWC · Hult CHL-0200 · independent unofficial archive*

**Adaptive Efficiency** is the public name for this entire repository: filed committee deliverables, the `quant_monitor/` Python audit overlay, engineering docs, and the GitHub Pages presentation layer. **Team BWC** (Team 5) is the desk that ran the simulation. The legacy repo slug `ganet-project-bwc` is unchanged on GitHub.

**Sunset freeze:** valuation `2026-04-10` · reporting `2026-05-01` · **archived** (read-mostly)

**Maintainer:** [Kartavya Jharwal](https://kartavya.tech) · MIT — forks must retain [LICENSE](LICENSE) attribution.

> **Disclaimer** (from [live splash](frontend/index.html)): This archive is an independent, unofficial presentation of Team BWC's investment simulation. It is not affiliated with Hult, the Professor, or former teammates. While the layout and development were AI-assisted, official graded marks remain strictly bound to the submitted deliverables. All narrative reflections and interpretations are entirely my own. Faculty sign-off is closed (`422 / 430`). If this repository disagrees with the Excel close or filed memo, **the filed artifacts win**.

| Surface | URL / path |
|---------|------------|
| **Live site** | [kartavya-jharwal.github.io/ganet-project-bwc](https://kartavya-jharwal.github.io/ganet-project-bwc/) |
| Presentation | [frontend/index.html](frontend/index.html) · [frontend/README.md](frontend/README.md) · [frontend/PLAN.md](frontend/PLAN.md) |
| Technical docs | `uv run python -m mkdocs build -f docs/mkdocs.yml` → [frontend/docs/](frontend/docs/) |
| Committee packet | [deliverables/](deliverables/README.md) |
| Code review | [REVIEWERS.md](REVIEWERS.md) (includes [archive seal checklist](REVIEWERS.md#publication-checklist-archive-seal)) |
| Agent / fork guide | [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) |

---

## What Adaptive Efficiency is

A personal thesis frame (Andrew Lo adaptive-markets lens) for a ten-week **$1M paper desk** at Hult. It is **not** a claim that the desk beat the simulation (`-4.37%` graded close). The project bundles:

| Layer | Path | Role |
|-------|------|------|
| Filed narrative | `deliverables/` | Committee PDF, Excel, charter, journals (grading authority) |
| Audit engine | `quant_monitor/` | Reproducible Python overlay (walk-forward, stress, behavioural audit) |
| Public presentation | `frontend/` | Single-page archive, charts, JSON hydration, MkDocs export |
| Engineering depth | `docs/` | Phase docs, backtest JSON, architecture |

**Thesis name:** Adaptive Efficiency · **Desk name:** Team BWC · **Accent:** `#a78bfa`

| Audience | Start here |
|----------|------------|
| Economist / PM | Live splash disclaimer → **Sources** → **Desk** results → faculty **422/430** |
| Recruiter | Hero + executive summary + contact on the live site |
| Code auditor | **Stack** section → [frontend/docs/](frontend/docs/) → [REVIEWERS.md](REVIEWERS.md) |

Machine-readable index: [frontend/llms.txt](frontend/llms.txt) · [frontend/data/site-summary.json](frontend/data/site-summary.json)

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

Optional Manim hero reel:

```bash
uv run python scripts/render_manim.py --quality 720p --scene Scene01_GeometricBrownianMotion
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
frontend/           Adaptive Efficiency public site (HTML, js/, styles/, data/, charts/)
quant_monitor/      Python audit engine (config, data, models, backtest, CLI)
scripts/            prep_duckdb, build_frontend_assets, export, sunset_freeze
tests/              Unit tests + journal_transaction_history.csv
docs/               MkDocs source, phases/, exported JSON/MD
docker/             Optional container entrypoint
```

**Not in git:** `portfolio.duckdb`, `.venv/`, secrets (Doppler).

---

## CLI (`project`)

| Command | Notes |
|---------|--------|
| `project doctor` | Environment check |
| `project run-backtest` | Walk-forward test |

Prefer `scripts/` for sunset—avoid `project sync-data` (may start scheduler).

---

## License

MIT — see [LICENSE](LICENSE).
