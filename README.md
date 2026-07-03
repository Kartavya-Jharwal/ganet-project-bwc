# Ganet

**Adaptive Efficiency** · Team BWC · Hult CHL-0200 · independent unofficial archive

**Ganet** is the parent finance engineering brand. This repository is the **Adaptive Efficiency** archive: a filed Hult investment-challenge post-mortem with a reproducible Python audit overlay and static GitHub Pages presentation.

**Team BWC** (Team 5) ran the simulation desk. The GitHub slug `ganet-project-bwc` reflects the Ganet program namespace.

**Sunset freeze:** valuation `2026-04-10` · reporting `2026-05-01` · **archived** (read-mostly)

**Maintainer:** [Kartavya Jharwal](https://kartavya.tech) · MIT — forks must retain [LICENSE](LICENSE) attribution.

> **Disclaimer** (from [live splash](frontend/index.html)): This archive is an independent, unofficial presentation of Team BWC's investment simulation. It is not affiliated with Hult, the Professor, or former teammates. While the layout and development were AI-assisted, official graded marks remain strictly bound to the submitted deliverables. All narrative reflections and interpretations are entirely my own. Faculty sign-off is closed (`422 / 430`). If this repository disagrees with the Excel close or filed memo, **the filed artifacts win**.

| Surface | URL / path |
|---------|------------|
| **Live site** | [kartavya-jharwal.github.io/ganet-project-bwc](https://kartavya-jharwal.github.io/ganet-project-bwc/) |
| Presentation | [frontend/index.html](frontend/index.html) · [frontend/README.md](frontend/README.md) · [frontend/PLAN.md](frontend/PLAN.md) |
| Engineering docs | MkDocs **source:** [docs/](docs/index.md) → rebuild to [frontend/docs/](frontend/docs/) |
| Committee packet | [deliverables/](deliverables/README.md) |
| Code review | [REVIEWERS.md](REVIEWERS.md) (includes [archive seal checklist](REVIEWERS.md#publication-checklist-archive-seal)) |
| Agent / fork guide | [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) |

---

## Brand hierarchy

| Name | Scope |
|------|--------|
| **Ganet** | Parent finance engineering program (portfolio of case studies and tooling) |
| **Adaptive Efficiency** | This archive's thesis frame (Andrew Lo adaptive-markets lens on a short simulation) |
| **Team BWC** | The Hult CHL-0200 desk that managed the $1M paper book |

Adaptive Efficiency is **not** a claim the desk beat the simulation (`-4.37%` graded close). It names how this case study is framed and presented.

| Layer | Path | Role |
|-------|------|------|
| Filed narrative | `deliverables/` | Committee PDF, Excel, charter, journals (grading authority) |
| Audit engine | `quant_monitor/` | Reproducible Python overlay (walk-forward, stress, behavioural audit) |
| Public presentation | `frontend/` | Single-page archive, charts, JSON hydration |
| Engineering depth | `docs/` | Ganet technical docs for this freeze (phases, backtest JSON, architecture) |

| Audience | Start here |
|----------|------------|
| Economist / PM | Live splash disclaimer → **Sources** → **Desk** results → faculty **422/430** |
| Recruiter | Hero + executive summary + contact on the live site |
| Code auditor | **Stack** section → [frontend/docs/](frontend/docs/) → [REVIEWERS.md](REVIEWERS.md) |

Machine-readable index: [frontend/llms.txt](frontend/llms.txt) · [frontend/data/site-summary.json](frontend/data/site-summary.json)

**Docs policy:** edit markdown under `docs/` only. Do not hand-edit built HTML in `frontend/docs/`. Rebuild with `uv run python -m mkdocs build -f docs/mkdocs.yml --strict`.

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

Prefer `scripts/` for sunset—avoid `project sync-data` (may start scheduler).

---

## License

MIT — see [LICENSE](LICENSE).
