# Claude / Cursor context — Project BWC

Archived Hult Investment Challenge repo (**Team BWC**). Treat as **static publication + audit trail**, not an active trading system.

## Maintainer & license

- **Author:** Kartavya Jharwal — [kartavya.tech](https://kartavya.tech)
- **License:** MIT ([LICENSE](LICENSE)) — forks must preserve copyright and license text.

## What “done” means here

- **Engineering sunset** (`2026-05-01`): quant data frozen, live Appwrite retired, `verify_repo_health` passes on built artifacts.
- **Publication seal** (still open): one clean commit on `main`, `--require-clean-git` health gate, Pages deploy — blocked on landing `frontend/` microsite WIP. See [frontend/PLAN.md](frontend/PLAN.md).
- Microsite: `frontend/` — **STATIC ARCHIVE** (no `FALLBACK_DATA`, no Appwrite LIVE in `frontend/js/main.js`).
- Committee story: `deliverables/source/` → mirrored under `frontend/deliverables/` and `frontend/assets/post-mortem.pdf`.

## Typical human follow-ups (post-sunset)

1. **Finish microsite** — design and copy in `frontend/`; before seal run `bun run minify:frontend` and `build_frontend_assets.py` for deliverables sync (data/charts already built).
2. **Publication seal** — checklist in [REVIEWERS.md#publication-checklist-archive-seal](REVIEWERS.md#publication-checklist-archive-seal).
3. **Archive repo** on GitHub (mark read-only, pin Pages URL) and start new projects separately.

## Do not

- Start APScheduler / `project sync-data` in CI or docs without explicit ask.
- Add secrets to git or reintroduce `quant_monitor/cli_old.py`.
- Lint `docs/archive/manim/` (excluded in `ruff.toml`).

## Verification

```bash
uv run python scripts/verify_repo_health.py --strict-artifacts
```

Publication checklist: [REVIEWERS.md#publication-checklist-archive-seal](REVIEWERS.md#publication-checklist-archive-seal).
