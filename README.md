# Ganet — Project BWC (Team BWC)

> **Public post-mortem** for a Hult $1M investment simulation (CHL-0200, Team 5). **Client deliverables** (`deliverables/`) hold the filed committee narrative. **`quant_monitor/`** is the reproducible Python audit overlay. **`frontend/`** is an independent presentation microsite built and maintained separately by [Kartavya Jharwal](https://kartavya.tech).

**Sunset freeze:** valuation `2026-04-10` · reporting `2026-05-01` · Team **BWC** · **archived** (read-mostly)

**Maintainer:** [Kartavya Jharwal](https://kartavya.tech) · MIT — forks must retain [LICENSE](LICENSE) attribution.

| Surface | URL / path |
|---------|------------|
| **Live microsite** | [kartavya-jharwal.github.io/ganet-project-bwc](https://kartavya-jharwal.github.io/ganet-project-bwc/) |
| Microsite source | [frontend/index.html](frontend/index.html) · [frontend/README.md](frontend/README.md) · [frontend/PLAN.md](frontend/PLAN.md) |
| Technical docs | `uv run python -m mkdocs build -f docs/mkdocs.yml` → [frontend/docs/](frontend/docs/) |
| Committee packet | [deliverables/](deliverables/README.md) |
| Code review | [REVIEWERS.md](REVIEWERS.md) (includes [archive seal checklist](REVIEWERS.md#publication-checklist-archive-seal)) |
| Agent / fork guide | [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) |

---

## Adaptive Efficiency microsite (independent frontend)

The **primary public entry point** is a static single-page site under `frontend/`, framed as **Adaptive Efficiency** (Andrew Lo adaptive-markets lens). The desk remains **Team BWC**; the site is an **unofficial, maintainer-led archive** of the same filed artifacts, not an official Hult publication.

**Built independently** from the Python quant engine: hand-authored HTML/CSS/JS, self-hosted typography, liquid-gradient splash with WebGL backdrop, native `<dialog>` depth layers, Plotly chart embeds, and JSON hydration from `build_frontend_assets.py`. No React, no CMS, no live data badge.

| Audience | What to open |
|----------|----------------|
| Economist / PM | Splash disclaimer → **Sources** (Excel, memo, deck) → **Desk** results → faculty **422/430** |
| Recruiter | Hero + executive summary + contact |
| Code auditor | **Stack** section → [frontend/docs/](frontend/docs/) → [REVIEWERS.md](REVIEWERS.md) |

**Scroll path:** `#summary` → `#executive-summary` → `#sources` → `#context` → `#story` (behavioural audit) → `#evidence` → `#research` → `#stack` → `#evaluation` → `#contact`

**Also:** [deliverables/index.html](frontend/deliverables/index.html) (standalone download table) · anchor redirects (`story.html`, `results.html`, `research.html`) · [llms.txt](frontend/llms.txt) for machine-readable site map

Refresh production bundles before a publication seal:

```bash
bun run minify:frontend
uv run python scripts/sync_deliverables_manual.py
uv run python scripts/verify_repo_health.py --strict-artifacts
```

---

## Quick start (quant audit + site rebuild)

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

---

## Repository map

```
deliverables/       Filed committee packet (PDF, Excel, charter, journals)
frontend/           Adaptive Efficiency microsite (HTML, js/, styles/, data/, charts/)
quant_monitor/      Quant audit engine (config, data, models, backtest, CLI)
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
