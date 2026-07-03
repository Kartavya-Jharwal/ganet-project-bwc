# Adaptive Efficiency

**Team BWC · Hult CHL-0200 · mock $1M paper desk post-mortem**

[![Open live site](https://img.shields.io/badge/Open-Live%20Site-6d28d9?style=for-the-badge&logo=github)](https://kartavya-jharwal.github.io/ganet-project-bwc/)
[![Engineering docs](https://img.shields.io/badge/Read-Engineering%20Docs-24292f?style=for-the-badge&logo=readthedocs)](frontend/docs/)
[![Audit the repo](https://img.shields.io/badge/Audit-REVIEWERS.md-a78bfa?style=for-the-badge)](REVIEWERS.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-a78bfa?style=flat-square)](LICENSE)
[![Archive](https://img.shields.io/badge/status-static%20archive-6b7280?style=flat-square)](REVIEWERS.md#publication-checklist-archive-seal)
[![Sunset](https://img.shields.io/badge/sunset-2026--05--01-6b7280?style=flat-square)](frontend/PLAN.md)

An opinionated post-mortem on implementing investment fundamentals, qualitative book management, and strict risk discipline under Q1 2026 stress. **Start on the live site** for the narrative, charts, and filed sources. Use this repository for engineering depth and audit trails.

---

## What this is

This repo is a **localized deployment** within [**Project Ganet**](https://kartavya.tech): an independent initiative mapping systemic financial literacy through first-principles design.

**Adaptive Efficiency** is one empirical trial in that sequence. It stress-tests theory against live execution constraints: a ten-week Hult simulation (20 Jan → 1 May 2026), a $1M paper book managed by **Team BWC** (Team 5), and a Python audit overlay on filed Excel, journals, and committee deliverables.

Engineering sunset freeze completed **2026-05-01** (valuation snapshot **2026-04-10**). **June 2026 polish** refines the archive for academics, quants, and recruiters. Publication seal commit is still open. See [frontend/PLAN.md](frontend/PLAN.md).

> **Disclaimer:** Independent, unofficial archive of Team BWC's simulation. Not affiliated with Hult, the professor, or former teammates. AI-assisted layout; official grades bind to submitted deliverables only. Faculty sign-off closed (**422 / 430**). If this repo disagrees with the Excel close or filed memo, **the filed artifacts win**.

---

## Three paths

| | Where to go | Best for |
|---|-------------|----------|
| **1** | [**Open the live site →**](https://kartavya-jharwal.github.io/ganet-project-bwc/) | Story, desk results, faculty evaluation, contact |
| **2** | [**Engineering docs →**](frontend/docs/) | Phases, architecture, backtest JSON, MkDocs depth |
| **3** | [**Audit the code →**](REVIEWERS.md) | Grading authority paths, archive seal checklist, reviewer map |

**Grading authority:** [deliverables/](deliverables/README.md) · **Presentation source:** [frontend/](frontend/index.html) · **MkDocs source:** [docs/](docs/index.md) (rebuild to `frontend/docs/`)

---

## Proof points

| Metric | Value | Context |
|--------|-------|---------|
| **Graded desk close** | **-4.37%** | Excel close, 11 Apr 2026 |
| **Faculty score** | **422 / 430** | Sign-off closed |
| **Apr 2 trough** | **-6.44%** desk vs **-11.72%** SPY | **+5.28pp** relative preservation at the low |
| **Archive status** | Static / read-only | Simulation closed · term-end snapshot 2026-05-01 |

Adaptive Efficiency names the framing, not a claim the desk beat the simulation.

---

## For whom

| Audience | Start here |
|----------|------------|
| **Academics** | Live site → [Sources](https://kartavya-jharwal.github.io/ganet-project-bwc/#sources) → [Faculty](https://kartavya-jharwal.github.io/ganet-project-bwc/#evaluation) → filed [deliverables/](deliverables/README.md) |
| **Quants** | Live site → [Desk](https://kartavya-jharwal.github.io/ganet-project-bwc/#evidence) → [Stack](https://kartavya-jharwal.github.io/ganet-project-bwc/#stack) → [engineering docs](frontend/docs/) |
| **Recruiters** | [Live site hero + contact](https://kartavya-jharwal.github.io/ganet-project-bwc/#contact) · executive summary on-page |

Machine-readable: [frontend/llms.txt](frontend/llms.txt) · [frontend/data/site-summary.json](frontend/data/site-summary.json)

---

## Maintainer

**[Kartavya Jharwal](https://kartavya.tech)** · MIT ([LICENSE](LICENSE); forks retain attribution)

Logos: [`frontend/assets/PB_logos/`](frontend/assets/PB_logos/)

---

<details>
<summary><strong>Repository map</strong></summary>

| Layer | Path | Role |
|-------|------|------|
| Filed narrative | `deliverables/` | Committee PDF, Excel, charter, journals (**grading authority**) |
| Audit engine | `quant_monitor/` | Walk-forward, stress, behavioural audit |
| Public site | `frontend/` | Single-page archive, charts, JSON hydration |
| Engineering docs | `docs/` → `frontend/docs/` | Ganet technical depth for this freeze |

```
deliverables/       Filed committee packet
frontend/           Adaptive Efficiency public site
quant_monitor/      Python audit engine
scripts/            prep_duckdb, build_frontend_assets, sunset_freeze
tests/              Unit tests + journal fixtures
docs/               MkDocs source (do not hand-edit built HTML)
```

**Docs policy:** edit markdown under `docs/` only. Rebuild with `uv run python -m mkdocs build -f docs/mkdocs.yml --strict`.

**Not in git:** `portfolio.duckdb`, `.venv/`, secrets.

</details>

<details>
<summary><strong>Quick start (developers)</strong></summary>

```bash
uv sync --frozen
.\scripts\sunset_freeze.ps1    # Windows — or scripts/sunset_freeze.sh
```

Manual rebuild:

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

| CLI | Notes |
|-----|-------|
| `project doctor` | Environment check |
| `project run-backtest` | Walk-forward test |

Prefer `scripts/` for sunset. Avoid `project sync-data` (may start scheduler).

Agent / fork guide: [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md)

</details>

<details>
<summary><strong>GitHub social preview</strong></summary>

Homepage: [kartavya-jharwal.github.io/ganet-project-bwc/](https://kartavya-jharwal.github.io/ganet-project-bwc/)

OG card: [assets/og-card.png](https://kartavya-jharwal.github.io/ganet-project-bwc/assets/og-card.png) · upload via **Settings → General → Social preview**. Full steps: [docs/github-social-preview.md](docs/github-social-preview.md).

</details>

---

## License

MIT — see [LICENSE](LICENSE).
