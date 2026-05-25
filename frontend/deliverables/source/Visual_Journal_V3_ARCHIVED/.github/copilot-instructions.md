## Quick orientation

This is a small static web gallery (no build step). Key files:

- `index.html` — app shell with splash screen and gallery container.
- `main.js` — gallery logic, image probing and lazy-loading; look for `fetchImages()` and `probeImage()` implementations.
- `main.css` — design tokens & layout; many runtime behaviors assume CSS class names (e.g. `.gallery-track`, `.gallery-item`).

## High-level architecture and data flow

- App is client-only. On start `main.js` probes the `images/` folder for sequential numbered files (`1.png`, `2.png`, ... `8.png`) and builds `images[]` dynamically.
- `initGallery()` creates DOM `.gallery-item` nodes and lazy-loads images via `data-src` attributes; `observePendingLazyImages()` is used to attach IntersectionObserver logic (search for function name in `main.js`).

## Project-specific conventions (important to follow)

- Image naming: use simple numbered names `1.png`, `2.png`, `3.png`, ... in the `images/` folder. The loader probes sequentially starting from 1 until several consecutive misses.
- Add new images by placing files in `images/` using the numeric sequence — the runtime probes sequentially until several misses.
- Do not change the HTML structure for the gallery container or class names unless you update every selector in `main.js` and styles in `main.css`.

## Common modification tasks — examples

- To change per-image captions: edit the `captions` array inside `initGallery()` in `main.js` (captions are applied by index).
- To add keyboard shortcuts, update the keyboard handling code near the top of `main.js` (there is a `keyboardLegend` and `keyboard-icon` injection).

## Dev / debug workflow

- No npm scripts or bundlers required. Recommended ways to serve locally (choose one):
  - VS Code: Live Server extension -> Open `index.html`.
  - Python: `python -m http.server 8000` (run from project root) — serves files with correct MIME types.
  - Node: `npx http-server -c-1` if you prefer Node-based servers.

- Smoke test after changes: open the page, check DevTools Console for errors, and confirm the loading indicator finds images and that `Gallery found X image(s)` is announced (main.js creates a status node).

## Safety rules for AI agents

- Avoid changing class names used by CSS/JS unless you update both files. Many behaviors rely on exact class selectors (e.g. `.gallery-track`, `.zoomable-image`).
- When touching image probing code, respect the existing timeouts in `probeImage()` — reducing them may cause false negatives on slow I/O.

## Known issues / Notes

- The placeholder `src` for images is a transparent 1x1 PNG data-URI to avoid flashing a template image during lazy-load. See `initGallery()` in `main.js`.

## Where to look first when debugging

- Console errors -> usually point to a missing image path or an unexpected null `querySelector` (DOM queries are run on DOMContentLoaded).
- If images are not discovered, inspect `fetchImages()` flow in `main.js` (look for `probeImage` and `maxConsecutiveMisses`).

If anything here is unclear or you'd like specific examples added (e.g. a small unit-test harness or local debug scripts), tell me which area to expand and I'll iterate.
