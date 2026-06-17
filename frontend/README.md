# Project BWC — static microsite

**Team BWC** · Hult CHL-0200 · sunset `2026-05-01`  
**Maintainer:** [Kartavya Jharwal](https://kartavya.tech)

Public **5-minute reviewer brief**: filed investment-challenge artifacts, honest desk results, faculty score, and a reproducible Python audit layer. This is an **independent archive** — not an official Hult course publication.

**Live:** [kartavya-jharwal.github.io/ganet-project-bwc](https://kartavya-jharwal.github.io/ganet-project-bwc/)  
**Finish plan:** [PLAN.md](./PLAN.md)

---

## What this site is for

| Reviewer | Path |
|----------|------|
| Economist / PM | Splash disclaimer → **Sources** (Excel + memo) → **Results** → faculty **422/430** |
| Recruiter | Hero headline + process scores + contact |
| Code auditor | **Tech** section → `frontend/docs/` → [REVIEWERS.md](../REVIEWERS.md) |

**Brand:** named desk **BWC** (not “Team 5”), violet accent `#a78bfa`, institutional tone with transparent disclaimer (vibe-coded presentation, AI-assisted build/docs).

---

## Architecture

```
frontend/
├── index.html          # Single-page narrative (all sections)
├── js/main.js          # Hydration: metrics, timeline, manifest, dialogs, splash
├── styles/
│   ├── tokens.css      # Color, type, spacing tokens (source of truth)
│   ├── spatial.css     # Grid, section rhythm
│   ├── rhythm.css      # Typography per section
│   ├── pages.css       # Components
│   ├── layout.css      # Nav, footer
│   └── motion.css      # Cursor, scroll, reveals
├── data/               # Built JSON (run build_frontend_assets.py)
├── charts/             # Plotly embeds
├── deliverables/source/  # Committee packet mirror (HTM/XLSX/PDF)
└── docs/               # MkDocs export (engineering depth)
```

**Redirects:** `story.html` → `#story`, `results.html` → `#evidence`, `research.html` → `#validator`, `deliverables/index.html` → `#sources`.

---

## UX rules (see PLAN.md)

1. **Thin scroll** — optional depth opens in `<dialog>` modals (`ic-dialog`), not new sections.
2. **Artifacts** live under `#sources` only (three pillars + manifest details).
3. **No** team deep-dives, peer quote strips, or fabricated social proof.
4. **Splash** = mandatory disclaimer (AI-assisted + independent archive), not a marketing hero.
5. **Motion/cursor** retained for human reviewers.

---

## Build & verify

From repo root (after sunset freeze):

```bash
uv run python scripts/build_frontend_assets.py
uv run python -m mkdocs build -f docs/mkdocs.yml --strict
uv run python scripts/verify_repo_health.py --strict-artifacts
```

Full rebuild: `scripts/sunset_freeze.ps1` (Windows) or `scripts/sunset_freeze.sh`.

---

## Spacing system

Use tokens from `styles/tokens.css`:

- `--section-gap` — between major sections
- `--stack-gap` — within section stacks
- `--inline-gap` — inline clusters
- `--spacing-1` … `--spacing-8` — component padding

Avoid hardcoded `rem` in narrative sections. If padding looks doubled, check for conflicts between `spatial.css` and `rhythm.css` (documented in PLAN.md §4).

---

## Licence

MIT — same as repository root. Forks must retain copyright notice.
