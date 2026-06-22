# Ganet — Project BWC (Team BWC)

> **Public post-mortem** for a Hult $1M investment simulation. **Client deliverables** (`deliverables/`) are the main narrative; **`quant_monitor/`** is the reproducible audit module—a useful but partial slice of the program.

**Sunset freeze:** valuation `2026-04-10` · reporting `2026-05-01` · Team **BWC** · **archived** (read-mostly)

**Maintainer:** [Kartavya Jharwal](https://kartavya.tech) · MIT — forks must retain [LICENSE](LICENSE) attribution.

| Surface | URL / path |
|---------|------------|
| Microsite | [frontend/index.html](frontend/index.html) |
| Technical docs | `uv run python -m mkdocs build -f docs/mkdocs.yml` → [frontend/docs/](frontend/docs/) |
| Committee packet | [deliverables/](deliverables/README.md) |
| Code review | [REVIEWERS.md](REVIEWERS.md) (includes [archive seal checklist](REVIEWERS.md#publication-checklist-archive-seal)) |
| Microsite status | [frontend/PLAN.md](frontend/PLAN.md) |
| Agent / fork guide | [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) |

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
uv run python -m mkdocs build -f docs/mkdocs.yml --strict
```

Optional Manim hero reel:

```bash
uv run python scripts/render_manim.py --quality 720p --scene Scene01_GeometricBrownianMotion
```

---

## Repository map

```
deliverables/       Client post-mortem, charter, Excel, journals (Team BWC)
quant_monitor/      Quant audit engine (config, data, models, backtest, CLI)
scripts/            prep_duckdb, build_frontend_assets, export, sunset_freeze
tests/              Unit tests + journal_transaction_history.csv
docs/               MkDocs source, phases/, exported JSON/MD
frontend/           Static microsite (HTML, charts/, data/, assets/)
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
