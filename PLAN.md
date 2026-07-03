# Adaptive Efficiency: presentation status

**Last updated:** July 2026  
**Maintainer:** [Kartavya Jharwal](https://kartavya.tech)

## Repo status

| Milestone | When | State |
|-----------|------|-------|
| Engineering sunset freeze | `2026-05-01` | **Done**: quant pipeline frozen, static data, no live Appwrite |
| Publication seal commit | `2026-07-03` | **Done**: minify, deliverables sync, health gate, push (`98481fa`) |
| GitHub Pages deploy | live | Serves sealed `main` |

The original phased finish plan (splash rewrite, OG retitle, deliverables redirect, spacing pass) is **retired**. Publication seal landed **2026-07-03**. Remaining maintainer step: mark the GitHub repo read-only via the website archive control.

---

## Site identity (as built)

- **Parent framework:** **Project Ganet**: financial literacy, first-principles design, portfolio of empirical case studies.
- **Case study title:** *Adaptive Efficiency*: standalone trial stress-testing theoretical models against live execution constraints. Not a performance claim.
- **Desk name:** Team **BWC** · Hult **CHL-0200** · violet accent `#a78bfa`.
- **Framing:** independent **unofficial** archive. Faculty marks (`422/430`) are filed and closed. Maintainer presentation of the same filed data (unofficial archive).

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

**Current state (July 2026):** narrative JSON, Plotly charts, production bundles, and deliverables mirror are **sealed** on `main`.

| Layer | Location | Status |
|-------|----------|--------|
| Data + charts | `frontend/data/`, `frontend/charts/` | **Built** (from prior `build_frontend_assets.py` run) |
| Deliverables mirror | `frontend/deliverables/source/` | **Synced** (`sync_deliverables_manual.py`, seal `2026-07-03`) |
| Production bundles | `bundle.min.css`, `*.min.js` | **Minified** (seal `2026-07-03`) |

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

## Publication seal (completed 2026-07-03)

Seal record: [REVIEWERS.md § archive seal](../REVIEWERS.md#publication-checklist-archive-seal).

**Re-seal after edits** (data/charts already on disk unless you changed quant outputs):

```bash
bun run minify:frontend
uv run python scripts/sync_deliverables_manual.py
uv run python scripts/verify_repo_health.py --strict-artifacts --require-clean-git
```

**Manual close:** mark the GitHub repo read-only via Settings → Archive (not automated here).

Skip `sunset_freeze` unless DuckDB, tests, or MkDocs exports need a refresh.

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
