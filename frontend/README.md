# Adaptive Efficiency — Project BWC microsite

**Team BWC** · Hult CHL-0200 · engineering sunset `2026-05-01` · publication seal pending

**Maintainer:** [Kartavya Jharwal](https://kartavya.tech)

**Live:** [kartavya-jharwal.github.io/ganet-project-bwc](https://kartavya-jharwal.github.io/ganet-project-bwc/)

Public **5-minute reviewer brief**: filed investment-challenge artifacts, honest desk results, faculty score, and a reproducible Python audit layer. This is an **independent, unofficial archive**, not an official Hult course publication.

**Status doc:** [PLAN.md](./PLAN.md)

---

## What this site is for

| Reviewer | Path |
|----------|------|
| Economist / PM | Splash disclaimer → **Sources** (Excel + memo) → **Desk** results → faculty **422/430** |
| Recruiter | *Adaptive Efficiency* hero + executive summary + contact |
| Code auditor | **Stack** section → `frontend/docs/` → [REVIEWERS.md](../REVIEWERS.md) |

**Brand:** desk **BWC**, site frame **Adaptive Efficiency**, violet `#a78bfa`, transparent disclaimer (AI-assisted build, unofficial archive).

---

## Architecture

```
frontend/
├── index.html              # Single-page narrative (all sections)
├── js/
│   ├── main.js             # Source: hydration, splash, dialogs, timeline
│   ├── main.min.js         # Production entry (defer)
│   ├── base-path.js        # GitHub Pages base-path helper
│   ├── splash-liquid-gradient.js
│   └── *.min.js            # Built by minify script
├── styles/
│   ├── tokens.css … motion.css   # Source stylesheets
│   ├── fonts.css                 # Self-hosted / linked faces
│   ├── bundle.css / bundle.min.css   # Production concat
├── data/                   # Built JSON (build_frontend_assets.py)
├── charts/                 # Plotly embeds
├── deliverables/
│   ├── index.html          # Standalone committee download index
│   └── source/             # Packet mirror (XLSX, DOCX, PDF, CSV)
├── assets/                 # og-card.png, post-mortem.pdf, plotly, fonts
└── docs/                   # MkDocs export (engineering depth)
```

**Anchor redirects:** `story.html` → `#story`, `results.html` → `#evidence`, `research.html` → `#research`.

**Section anchors:** `#summary`, `#executive-summary`, `#sources`, `#context`, `#story`, `#evidence`, `#research`, `#stack`, `#evaluation`, `#principles`, `#team-roster`, `#contact` — see [llms.txt](./llms.txt) for machine-readable detail.

---

## UX patterns

1. **Splash:** mandatory disclaimer overlay, liquid gradient, data-load gate, `sessionStorage` dismiss key `bwc-splash-dismissed`.
2. **Optional depth in dialogs:** program brief, memo excerpts (`report-excerpts.json`), desk post-mortem, video popout — via `ic-dialog` + `data-dialog-target`.
3. **Behavioural audit:** inline under `#story`, hydrated from `behavioural-audit.json`.
4. **Filed artifacts** under `#sources` (three pillars + manifest `<details>`). Full file list also at `deliverables/index.html`.
5. **Motion and cursor** retained for human reviewers.
6. **No** fabricated social proof, team deep-dives, or live data badge.

---

## Copy style

Microsite prose must not use em dashes (Unicode U+2014) or semicolons in sentences. Rewrite with commas, periods, colons, or parentheses instead. Code syntax semicolons and CSS are exempt. Enforced by `scripts/verify_frontend_copy.py`.

---

## Build and verify

`frontend/data/` and `frontend/charts/` are **already built**. Before the publication seal, refresh production bundles and sync the deliverables mirror:

```bash
bun run minify:frontend
uv run python scripts/build_frontend_assets.py
uv run python scripts/verify_repo_health.py --strict-artifacts
```

- **Minify:** concat CSS → `bundle.min.css`, minify `main.js`, `base-path.js`, `splash-liquid-gradient.js`.
- **Sync:** `build_frontend_assets.py` copies committee files to `frontend/deliverables/source/` and updates `deliverables-manifest.json` / `commit-log.json`. Re-run is safe when charts/data are already current.

Full quant + docs rebuild (only when DuckDB or memo/Excel sources change): `scripts/sunset_freeze.ps1` (Windows) or `scripts/sunset_freeze.sh`.

Before the publication seal: add `--require-clean-git` to the health script and run CI parity per [REVIEWERS.md](../REVIEWERS.md#publication-checklist-archive-seal).

---

## Spacing and styles

Edit source files under `styles/` (not `bundle.min.css` directly). Token scale lives in `tokens.css` (`--spacing-1` … `--spacing-8`, `--section-gap`, `--stack-gap`, `--inline-gap`). Rebuild bundles after CSS changes.

---

## Licence

MIT, same as repository root. Forks must retain copyright notice.
