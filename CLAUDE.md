# Claude / Cursor context — Project BWC

Archived Hult Investment Challenge repo (**Team BWC**). Treat as **static publication + audit trail**, not an active trading system.

## Maintainer & license

- **Author:** Kartavya Jharwal — [kartavya.tech](https://kartavya.tech)
- **License:** MIT ([LICENSE](LICENSE)) — forks must preserve copyright and license text.

## What “done” means here

- Sunset seal committed; CI runs pytest, ruff, ty, bandit, deptry, `verify_repo_health`.
- Microsite: `frontend/` — **STATIC ARCHIVE** (no `FALLBACK_DATA`, no Appwrite LIVE in `frontend/js/main.js`).
- Committee story: `deliverables/source/` → mirrored under `frontend/deliverables/` and `frontend/assets/post-mortem.pdf`.

## Typical human follow-ups (post-sunset)

1. **Beautify `frontend/`** — design-only; rebuild with `build_frontend_assets.py` when charts/data change.
2. **Docs polish** — edit `docs/*.md`, then `mkdocs build --strict`.
3. **Archive repo** on GitHub (mark read-only, pin Pages URL) and start new projects separately.

## Do not

- Start APScheduler / `project sync-data` in CI or docs without explicit ask.
- Add secrets to git or reintroduce `quant_monitor/cli_old.py`.
- Lint `docs/archive/manim/` (excluded in `ruff.toml`).

## Verification

```bash
uv run python scripts/verify_repo_health.py --strict-artifacts
```

Publication checklist: [REVIEWERS.md#publication-checklist-sunset-seal](REVIEWERS.md#publication-checklist-sunset-seal).
