# Adaptive Efficiency

**Project Ganet** parent framework · **Team BWC** · Hult CHL-0200 · engineering sunset `2026-05-01` · publication seal pending

**Maintainer:** [Kartavya Jharwal](https://kartavya.tech) · logos: [`assets/PB_logos/`](./assets/PB_logos/)

**Live:** [kartavya-jharwal.github.io/ganet-project-bwc](https://kartavya-jharwal.github.io/ganet-project-bwc/)

**Project Ganet** is the parent framework for systemic financial literacy and first-principles design. **Adaptive Efficiency** is this standalone empirical case study (`deliverables/`, `quant_monitor/`, docs, and this site). `frontend/` is the public presentation layer. Independent **unofficial archive**, not an official Hult course publication.

> **Disclaimer:** Independent, unofficial presentation of Team BWC's investment simulation. Not affiliated with Hult, the Professor, or former teammates. AI-assisted layout and development. Graded marks bound to filed deliverables. Maintainer interpretations are personal. Filed artifacts win on any conflict.

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

**Section anchors:** `#summary`, `#executive-summary`, `#sources`, `#context`, `#story`, `#evidence`, `#research`, `#stack`, `#evaluation`, `#principles`, `#team-roster`, `#contact`. See [llms.txt](./llms.txt) for machine-readable detail.

---

## UX patterns

1. **Splash:** mandatory disclaimer overlay, liquid gradient, data-load gate, `sessionStorage` dismiss key `bwc-splash-dismissed`.
2. **Optional depth in dialogs:** program brief, memo excerpts (`report-excerpts.json`), desk post-mortem, video popout via `ic-dialog` + `data-dialog-target`.
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
uv run python scripts/sync_deliverables_manual.py
uv run python scripts/verify_repo_health.py --strict-artifacts
```

**Do not run** `build_frontend_assets.py` for chart HTML. `charts/*.html` were hand-edited after generation and regen would overwrite presentation fixes. JSON-only refresh is a separate, explicit decision.

- **Sync:** `uv run python scripts/sync_deliverables_manual.py` mirrors committee files, manifest, and download table rows. Keeps hand-edited `deliverables/index.html` chrome.

Before the publication seal: add `--require-clean-git` to the health script and run CI parity per [REVIEWERS.md](../REVIEWERS.md#publication-checklist-archive-seal).

---

## Performance loading (cold first visit)

**Fonts:** The microsite (`index.html`) uses **self-hosted** variable fonts under `assets/fonts/` via `styles/fonts.css`. Each face is served as **woff2 (brotli) first** with the original `.ttf` as fallback. This cut the cold font payload ~67% (e.g. Playfair 294 KB → 103 KB, Source Sans 627 KB → 164 KB), the dominant lever for cold LCP/FCP under mobile throttling. Regenerate the woff2 files with `scripts/build_woff2.py` if the `.ttf` sources change. No Google Fonts CDN on the narrative page. MkDocs under `docs/` still pulls Roboto from Google (engineering docs only).

**Splash window:** On a cold visit, Playfair Display (splash title, the LCP element) is preloaded at high priority as woff2. Darker Grotesque (hero) preloads without competing `fetchpriority`. The decorative splash waveform (canvas rAF loop) and the Three.js liquid gradient (~600 KB) are **deferred off the first-paint critical path** (`requestAnimationFrame` + `requestIdleCallback`) so the title + LCP font paint first. The CSS gradient fallback covers the backdrop meanwhile. Plotly desk charts do **not** load on `DOMContentLoaded`.

**Staggered desk charts:** After ~3.8s (splash read window) + `requestIdleCallback`, the three `#evidence` iframes load one at a time (~650ms apart). Return visits (`splash-seen`) use a shorter ~450ms delay.

**Fast scrollers:** `IntersectionObserver` on all chart iframes and scroll-throttled `prefetchNearbyCharts()` still load desk/gallery charts as soon as they enter the lookahead zone (~1.15× viewport). Stagger only removes Plotly from the splash critical path. It does not block doomscrollers.

**Other async patterns:** JSON `prefetch` (not preload), Plotly script `prefetch`, chart `fetchpriority=low`, iframe concurrency 3, splash `inert` on background chrome, self-hosted Three.js for splash WebGL (deferred, CDN fallback).

**Measuring locally:** `bun run lighthouse:ci` (mobile, `simulate` throttling). **CI gates** a11y, best-practices, and SEO at ≥96. **Performance is report-only** (logged, never fails the job). Note the performance score is sensitive to the host CPU: Lighthouse scales its CPU multiplier off `benchmarkIndex`, so a busy dev machine (index ≲1400) inflates Total Blocking Time dramatically and depresses the score. A quiet machine (index ≳2000) or the CI Linux runner is the representative reading. a11y / best-practices / SEO are host-independent and hold at 100.

---

## Spacing and styles

Edit source files under `styles/` (not `bundle.min.css` directly). Token scale lives in `tokens.css` (`--spacing-1` … `--spacing-8`, `--section-gap`, `--stack-gap`, `--inline-gap`). Rebuild bundles after CSS changes.

---

## Licence

MIT, same as repository root. Forks must retain copyright notice.
