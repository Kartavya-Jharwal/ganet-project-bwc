# Project BWC microsite — finish plan

**Audience:** economists, finance recruiters, external code reviewers, design-curious humans.  
**Job of the site:** a **5-minute reviewer brief** and case study for lateral-entry finance proof-of-work — not a second committee submission.

**Brand anchors:** Team **BWC** (named desk, not “Team 5”), **violet** accent (`#a78bfa`), honest red return, filed artifacts up front.

---

## Design principles (non-negotiable)

| Principle | What it means |
|-----------|----------------|
| **Scroll path stays thin** | Hero → summary → **filed sources** → results → faculty score → contact. Reviewers must reach **422/430** without wading through optional depth. |
| **Depth in modals, not new sections** | Behavioural audit, memo pull-quotes, ratio drill-downs, and tech JSON open in **`<dialog>`** panels using the existing `ic-dialog` token system — same chrome as “Full program brief”. |
| **No fabricated social proof** | No professor paraphrases, no peer quote strips, no team contribution essays. Faculty were satisfied with deck + report; this site is **independent initiative**. |
| **No team deep-dives** | Roster stays minimal (name + LinkedIn/email). **Cancelled:** per-member dialogs, duty write-ups, “Hire the Team” climax. |
| **Artifacts = `#sources`** | Excel, memo, deck, charter, peer eval live in the first pillar section. No separate artifact hub page. |
| **Honest splash disclaimer** | Entry overlay is **legal/ethical framing**, not marketing. Institutional tone, but explicit: vibe-coded presentation, **AI-assisted** site build and quant overlay documentation. |
| **Motion & cursor stay** | Custom cursor and scroll polish target **human reviewers** (economist or design portfolio). Not stripped for “enterprise bland”. |
| **Discoverability = the brief** | SEO/OG metadata sell **“Team BWC — Hult IC post-mortem + audit”**, not generic quant blog keywords. The page *is* the case study. |

---

## What is already done

- Single-page narrative (`index.html`) with honest headline metrics and desk vs overlay separation
- Three filed pillars + manifest in `<details>`
- Desk timeline (JSON-driven snake), results charts, faculty score block, defense Q&A
- Python validator section + engineering docs under `frontend/docs/`
- Redirect stubs (`story.html`, `results.html`, `research.html` → anchors)
- Sunset freeze run; `verify_repo_health.py` passes
- Static archive badge (no live Appwrite)

---

## Gaps to close

### 1. Splash / disclaimer (broken UX → fixed role)

**Problem:** Splash reads like a second hero and competes with the real headline. Implementation feels disjointed (overlay + sessionStorage + long generic IC copy).

**Target behaviour:**

1. First visit per session: **modal disclaimer** blocks scroll until acknowledged.
2. Copy structure:
   - **What this is:** independent post-sunset archive of Team BWC (CHL-0200).
   - **What it is not:** official Hult publication; not coordinated with professor or teammates for this microsite.
   - **Transparency:** presentation is heavily edited (“vibe-coded”); **site layout and quant documentation layer were AI-assisted**; graded marks remain Excel + filed memo only.
   - **Enter** → dismiss; sessionStorage `bwc-splash-dismissed`.
3. Trim splash body: drop textbook IC paragraph; keep 2–3 sentences max outside the disclaimer box.
4. Fix edge cases: `splash-seen` on reload removes overlay without flash; `prefers-reduced-motion` respected; focus returns to `#main-content` / skip link after dismiss.

**Do not:** add a “reviewer mode” that hides design — reviewers are humans who should see the curated polish.

---

### 2. Modal layer for optional rigor (anti-bloat)

Use **one dialog pattern** (`ic-dialog` + `data-dialog-target`) for everything that would otherwise become a new on-page section.

| Trigger (on-page) | Modal content | Data source |
|-------------------|---------------|-------------|
| “Behavioural audit” link on Results | 4 metrics + interpretation (timing, disposition, turnover) | `data/behavioural-audit.json` |
| “Memo excerpts” on committee pillar | 3–4 kickers + short pulls + link to full HTM | `data/report-excerpts.json` |
| “Overlay metrics” (already table) | keep inline; optional “method notes” modal | static copy |
| Program brief | **already shipped** | inline in dialog |

**Rules:**

- On-page: one line + button, never a wall.
- Modal: scrollable panel, max-width matches `ic-dialog__panel`, close on backdrop + Esc.
- Open modal **does not** navigate away — reviewer keeps scroll position on return.

**Cancelled / do not build:**

- PPTX PNG carousel (deck stays PDF/PPTX download)
- `landing-proof-placeholder` section
- `#artifacts` hub page
- Team member dialogs
- Extracted social proof blocks

---

### 3. Routing & naming cleanup

| Item | Action |
|------|--------|
| `deliverables/index.html` | Redirect to `index.html#sources` (not `#artifacts`) |
| `id="sources"` | Optionally add `id="artifacts"` as alias on same `<section>` for old links |
| Dead CSS | Remove unused `.landing-proof-placeholder`, `.team-dialog`, `.carousel-scaffold` after confirming no references |
| Refactor scripts | **Deleted** (`refactor*.ps1`, `refactor*.py`) — one-off migration, not product |

---

### 4. Spacing & padding consolidation

**Problem:** Three layers fight each other:

- `tokens.css` — fluid `--space-*` + legacy `--spacing-*` aliases (with collisions: `--spacing-2` and `--spacing-3` both map to `--space-fluid-sm`)
- `spatial.css` — `.ic-section`, `.section-anchor`, `.ic-section-header` padding
- `rhythm.css` — section header `padding-bottom`
- `pages.css` — component-level hardcoded `rem` and undefined `--spacing-7`

**Target system (single pass):**

1. **Tokens:** define complete scale `--spacing-1` … `--spacing-8` with no duplicate aliases; add missing `--spacing-7`.
2. **Section vertical rhythm:** only `.section-anchor` gets `padding-top: var(--section-gap)`; remove duplicate padding from nested `.ic-section`.
3. **Headers:** `.ic-section-header` gets `gap: var(--stack-gap)` + `padding-bottom: var(--inline-gap)` in **one file** (`spatial.css`); delete conflicting rules in `rhythm.css`.
4. **Blocks:** `.ic-block` uses `padding: var(--spacing-6)` consistently; grep `pages.css` for bare `0.85rem`, `1.75rem` in narrative sections and replace with tokens.
5. **Bleed sections:** `#evidence.layout-bleed` must not double-apply gutter (already partially handled).

**Acceptance:** visual pass at 375px, 768px, 1280px — no section feels “double padded”; faculty score block visible within ~3 screens on laptop.

---

### 5. Discoverability (SEO / share cards)

The site **is** the 5-minute brief — metadata should say that outright.

**`<head>` additions (`index.html`):**

```html
<meta property="og:type" content="website">
<meta property="og:title" content="Team BWC | Hult Investment Challenge Post-Mortem">
<meta property="og:description" content="Honest $1M paper desk archive: -4.37% close, March drawdown vs SPY, 422/430 faculty score, filed memo + Excel + Python audit layer.">
<meta property="og:url" content="https://kartavya-jharwal.github.io/ganet-project-bwc/">
<meta property="og:image" content="https://kartavya-jharwal.github.io/ganet-project-bwc/assets/og-card.png">
<meta name="twitter:card" content="summary_large_image">
```

**`assets/og-card.png`:** simple branded card — BWC wordmark, violet accent bar, three numbers (-4.37%, -6.44% vs SPY Apr 2 trough, 422/430). No stock photo.

**JSON-LD:** `CreativeWork` with `name`, `author`, `datePublished` (2026-05-01), `description`, `url`, `keywords`: Team BWC, Hult CHL-0200, investment challenge post-mortem.

**Title/description tuning:** lead with **Team BWC** and **post-mortem**, not “quant telemetry”.

---

### 6. Contact CTA (solo lead, not team hire)

Replace generic “Continue the conversation” framing with:

- **Proof-of-work audit offer:** 15-minute walkthrough of filed vs built layers
- Route operational questions to **Kartavya** only (already stated)
- No “hire the team” — team context is roster only

---

## Implementation order

| Phase | Work | Est. |
|-------|------|------|
| **A** | Trash refactor scripts; fix `#artifacts` → `#sources`; dead CSS prune | 30 min |
| **B** | Splash rewrite + JS dismiss fixes + AI-assisted transparency | 1–2 h |
| **C** | Wire behavioural + memo modals (JSON hydrate) | 2 h |
| **D** | Spacing token pass (tokens → spatial → rhythm → pages grep) | 2–3 h |
| **E** | OG image + meta + JSON-LD | 1 h |
| **F** | Visual QA on live GitHub Pages URL | 30 min |

**Stop line:** when a reviewer can (1) read disclaimer, (2) hit filed Excel in one click, (3) see loss + March story + 422/430 without modal, (4) optionally open behavioural/memo modals, (5) share link with rich preview.

---

## Explicitly out of scope

- Contacting professor for endorsements
- Team contribution documentation
- New quant features or live data
- MkDocs content expansion (docs stay for auditors who want depth)
- Manim hero video (optional forever)
- Appwrite / scheduler re-enable

---

## Verification

```bash
uv run python scripts/verify_repo_health.py --strict-artifacts
```

Manual:

1. Open site fresh session → disclaimer → enter → hero visible, no flash
2. `deliverables/` redirect lands on sources pillars
3. Modal open/close preserves scroll; JSON loads from `data/`
4. LinkedIn debugger shows OG card
5. Mobile: reach faculty score in ≤4 thumb scrolls from hero
