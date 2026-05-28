# Project BWC — static microsite (`frontend/`)

**Status:** STATIC ARCHIVE (sunset freeze `2026-05-01`). Read-only GitHub Pages case study for CHL-0200.

## One-page flow (`index.html`)

| Section | Anchor | Audience |
|---------|--------|----------|
| Hero + executive summary | `#summary` | Committee scan: honest loss, March vs SPY |
| Program brief | `#context` | What an IC is, dates, setup depth |
| Desk timeline | `#story` | Week-by-week narrative |
| Filed sources | `#archive` | Excel, memo, deck pointers |
| Results | `#evidence` | Plain KPIs, desk charts only |
| Principles | `#principles` | Four takeaways (replaces old close callout) |
| Tech / quant rigor | `#validator` | Overlay vs desk; not optional framing |
| Engineering map | `#stack` | Full `quant_monitor/` stack tables |
| Files + memo embed | `#artifacts`, `#report` | **Single** iframe memo; downloads |
| Feedback + team | `#close`, `#contact` | Faculty grades, defense notes, roster |

Legacy multi-page HTML: `archive/pages/`; root `story.html`, `results.html`, `research.html`, `report.html` redirect to anchors on `index.html`.

## Data & charts

- Desk metrics: `data/excel-metrics.json`, `data/desk-timeline.json`
- Overlay hydration: `data/full-metrics.json`, `data/results.json` via `js/main.js` (no live Appwrite)
- Plotly charts: `charts/` — regenerate from repo root:

```bash
uv run python scripts/build_frontend_assets.py
# or charts only:
uv run python scripts/generate_plotly_dashboard.py
```

**Removed:** `charts/rolling-metrics.html` (equity + drawdown paired in Results).

## Deck viewer

- PDF embed visible by default (`#deck-pdf-viewer`)
- Horizontal slide gallery when `Slide{n}.PNG` exports exist under the PPTX folder, else Visual Journal `images/` fallback
- No link to `Visual_Journal_V3_ARCHIVED/index.html` on the microsite

## GitHub Pages paths

The site is published from `frontend/` as the **repo root** on `gh-pages` (`peaceiris/actions-gh-pages`, `publish_dir: ./frontend`).

| Gotcha | Fix |
|--------|-----|
| `https://user.github.io/REPO` without trailing slash breaks `./` links | `js/base-path.js` runs first in `<head>`, injects `<base href="/REPO/">` |
| Spaces in filenames (`Final Excel model.xlsx`) | `BWC.asset()` encodes path segments; manifest links rewritten in JS |
| Jekyll ignoring static assets | `frontend/.nojekyll` at publish root |

**Local preview** (always serve from `frontend/`):

```bash
cd frontend
uv run python -m http.server 8765
```

Open `http://127.0.0.1:8765/` (not the repo root). In DevTools: `window.BWC.pagesDiag` shows resolved `siteBase` and a sample slide URL.

## Maintainer

Kartavya Jharwal — [kartavya.tech](https://kartavya.tech) · MIT License
