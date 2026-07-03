# Adaptive Efficiency — presentation status

**Last updated:** June 2026  
**Maintainer:** [Kartavya Jharwal](https://kartavya.tech)

## Repo status

| Milestone | When | State |
|-----------|------|-------|
| Engineering sunset freeze | `2026-05-01` | **Done** — quant pipeline frozen, static data, no live Appwrite |
| Publication seal commit | — | **Not done** — `data/` and `charts/` already built; remaining: **minify** bundles + **deliverables sync**, then one clean commit |
| GitHub Pages deploy | live | Serves current `main`; may lag local WIP until seal lands |

The original phased finish plan (splash rewrite, OG retitle, deliverables redirect, spacing pass) is **retired**. This file tracks what the code actually does and what remains before the one-shot archive seal.

---

## Site identity (as built)

- **Project title:** *Adaptive Efficiency* — names the full repository and public archive (thesis frame, Andrew Lo adaptive-markets lens). Not a performance claim.
- **Desk name:** Team **BWC** · Hult **CHL-0200** · violet accent `#a78bfa`.
- **Framing:** independent **unofficial** archive. Faculty marks (`422/430`) are filed and closed. Maintainer presentation on the same data, not an official Hult publication.

---

## What is shipped

### Entry and chrome

- Liquid-gradient splash (`site-splash`) with WebGL backdrop, oscilloscope waveform, session dismiss via `bwc-splash-dismissed`, `splash-seen` anti-flash on reload, data-load gate on Enter.
- Disclaimer: unofficial archive, AI-assisted build, not affiliated with Hult/professor/teammates.
- Dock nav, custom cursor, scroll reveals, static-archive status (no Appwrite LIVE).
- Sunset bar: simulation closed 11 Apr 2026, term-end snapshot 2026-05-01.

### Single-page narrative (`index.html`)

Scroll path: hero (`#summary`) → executive summary → **filed sources** (`#sources`) → program brief (`#context`) → desk story + behavioural audit (`#story`) → graded Excel results (`#evidence`) → Python overlay research (`#research`) → stack (`#stack`) → faculty evaluation (`#evaluation`) → principles → team roster → contact (`#contact`).

### Modals (`ic-dialog` + `data-dialog-target`)

| Dialog | Trigger | Data |
|--------|---------|------|
| Program brief | Context section | Inline HTML |
| Memo excerpts | Sources / research lanes | `data/report-excerpts.json` |
| Desk post-mortem | Evidence section | Inline HTML |
| Video popout | Research viz cards | Inline iframe |

Behavioural audit is an **on-page** block under `#story` (hydrated from `data/behavioural-audit.json`), not a modal.

### Assets and build

**Current state (June 2026):** narrative JSON, Plotly charts, and related `frontend/data/` artifacts are **already built**. Production bundles and the deliverables mirror are **not** sealed yet.

| Layer | Location | Status |
|-------|----------|--------|
| Data + charts | `frontend/data/`, `frontend/charts/` | **Built** (from prior `build_frontend_assets.py` run) |
| Deliverables mirror | `frontend/deliverables/source/` | **Needs sync** — run asset builder for `_sync_deliverables` + manifest |
| Production bundles | `bundle.min.css`, `*.min.js` | **Needs minify** — run after any JS/CSS source edits |

- **Production entrypoints:** `styles/bundle.min.css`, `js/main.min.js`, `js/base-path.min.js`, `js/splash-liquid-gradient.min.js`.
- **Sources:** edit `styles/*.css` and `js/*.js` (not min files), then `bun run minify:frontend` (repo root `package.json`).
- **Sync step:** `uv run python scripts/sync_deliverables_manual.py` copies `deliverables/source/` into `frontend/deliverables/source/`, refreshes `deliverables-manifest.json`, and updates the download table in `deliverables/index.html` (preserves hand-edited page chrome). Does not run chart/data rebuild.
- **Full rebuild** only when quant outputs or Excel/memo sources change (re-runs chart generation and narrative extract).
- **SEO:** OG/Twitter meta, JSON-LD, `assets/og-card.png`, `llms.txt`, `sitemap.xml`.

### Routing

- `story.html`, `results.html`, `research.html` → anchor redirects on `index.html`.
- `deliverables/index.html` → **standalone download table** (full committee mirror), not a redirect to `#sources`.

### Engineering depth

- MkDocs export under `frontend/docs/`.
- Copy lint: `scripts/verify_frontend_copy.py` (no em dashes or prose semicolons in site HTML).

---

## Before publication seal

Use [REVIEWERS.md § archive seal](../REVIEWERS.md#publication-checklist-archive-seal) when ready to close the repo.

**Pre-seal build (lean):** data and charts are already on disk. Run only:

```bash
bun run minify:frontend
uv run python scripts/sync_deliverables_manual.py
```

Then:

1. `uv run python scripts/verify_repo_health.py --strict-artifacts --require-clean-git`
2. Manual pass: fresh session splash → sources one-click → `422/430` without modals → OG preview on share URL.
3. One archive seal commit on `main`, push Pages deploy.

Skip `sunset_freeze` unless DuckDB, tests, or MkDocs exports need a refresh.

Optional tidy (not blocking seal): redirect `deliverables/index.html` to `#sources` if the standalone table is no longer wanted.

---

## Explicitly out of scope

- Live Appwrite ingestion or scheduler re-enable
- New quant features or trading logic
- Professor endorsements or fabricated social proof
- Team contribution essays or “hire the team” climax
- MkDocs narrative expansion (auditors use `frontend/docs/` as-is)
- Manim hero reel (optional forever)

---

## Verification

```bash
bun run minify:frontend
uv run python scripts/build_frontend_assets.py
uv run python scripts/verify_repo_health.py --strict-artifacts
```
