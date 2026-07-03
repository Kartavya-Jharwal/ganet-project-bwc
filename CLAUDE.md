# Claude / Cursor context: Ganet (Adaptive Efficiency archive)

Archived Hult Investment Challenge repo under the **Ganet** finance program. Case study title: **Adaptive Efficiency**. Desk: **Team BWC**. Treat as a **static publication and audit trail**.

## Maintainer & license

- **Author:** Kartavya Jharwal ([kartavya.tech](https://kartavya.tech))
- **License:** MIT ([LICENSE](LICENSE)): forks must preserve copyright and license text.

## What “done” means here

- **Engineering sunset** (`2026-05-01`): quant data frozen, live Appwrite retired, `verify_repo_health` passes on built artifacts.
- **Publication seal** (`2026-07-03`): sealed on `main`, health gate and Pages deploy green. GitHub repo archive (read-only) is a manual step on the website. See [frontend/PLAN.md](frontend/PLAN.md) and [REVIEWERS.md#publication-checklist-archive-seal](REVIEWERS.md#publication-checklist-archive-seal).
- **Public site:** `frontend/`: **STATIC ARCHIVE** (no `FALLBACK_DATA`, no Appwrite LIVE in `frontend/js/main.js`).
- **Committee story:** `deliverables/source/` → mirrored under `frontend/deliverables/` and `frontend/assets/post-mortem.pdf`.

## Typical human follow-ups (post-sunset)

1. **Presentation layer:** copy and assets in `frontend/`; before seal run `bun run minify:frontend` and `sync_deliverables_manual.py` (data/charts already built).
2. **Publication seal:** checklist in [REVIEWERS.md#publication-checklist-archive-seal](REVIEWERS.md#publication-checklist-archive-seal).
3. **Archive repo** on GitHub (mark read-only, pin Pages URL) and start new projects separately.

## Docs policy

- Edit **source** `.md` under `docs/` and root guides only.
- Do **not** hand-edit built HTML under `frontend/docs/`. Rebuild with `mkdocs build -f docs/mkdocs.yml --strict`.

## Do not

- Start APScheduler / `project sync-data` in CI or docs without explicit ask.
- Add secrets to git or reintroduce `quant_monitor/cli_old.py`.
- Lint `docs/archive/manim/` (excluded in `ruff.toml`).

## Verification

```bash
uv run python scripts/verify_repo_health.py --strict-artifacts
```

Publication checklist: [REVIEWERS.md#publication-checklist-archive-seal](REVIEWERS.md#publication-checklist-archive-seal).
