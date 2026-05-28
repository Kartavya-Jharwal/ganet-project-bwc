/**
 * BWC-QUANT | Frontend Hydration Engine
 * Static archive: loads metrics from data/results.json only (no live Appwrite).
 */

(function () {
    'use strict';

    function asset(path) {
        if (window.BWC && typeof window.BWC.asset === 'function') {
            return window.BWC.asset(path);
        }
        return path;
    }

    function resolveHref(href) {
        if (window.BWC && typeof window.BWC.resolveHref === 'function') {
            return window.BWC.resolveHref(href);
        }
        return href;
    }

    const DATA_PATH = './data/results.json';

    function populateKPIs(data) {
        const mapping = {
            'kpi-mc-hurdle': 'mc_hurdle',
            'kpi-cf-var': 'cf_var',
            'kpi-beta': 'beta',
            'kpi-sharpe': 'sharpe',
            'kpi-max-dd': 'max_dd',
            'kpi-ann-return': 'ann_return'
        };

        for (const [elemId, key] of Object.entries(mapping)) {
            const el = document.getElementById(elemId);
            if (el && data[key] != null) {
                el.textContent = data[key];
            }
        }
    }

    function setOverlayCell(id, value) {
        const el = document.getElementById(id);
        if (el && value != null && value !== '') {
            el.textContent = value;
        }
    }

    function formatOverlayPct(value, digits = 1) {
        const n = Number(value);
        if (Number.isNaN(n)) return null;
        const pct = Math.abs(n) <= 1 ? n * 100 : n;
        const sign = pct >= 0 ? '+' : '';
        return `${sign}${pct.toFixed(digits)}%`;
    }

    function populateOverlayTable(full, results) {
        if (full) {
            setOverlayCell('tbl-ann-return', formatOverlayPct(full.annualized_return, 1));
            setOverlayCell('tbl-sharpe', Number(full.sharpe_ratio).toFixed(2));
            setOverlayCell('tbl-max-dd', formatOverlayPct(full.max_drawdown, 1));
            setOverlayCell('tbl-sortino', Number(full.sortino_ratio).toFixed(2));
            setOverlayCell('tbl-calmar', Number(full.calmar_ratio).toFixed(2));
            setOverlayCell('tbl-beta', Number(full.beta).toFixed(2));
            setOverlayCell(
                'tbl-cf-var',
                formatOverlayPct(full.cornish_fisher_var, 2)
            );
            setOverlayCell('tbl-jensen', Number(full.jensens_alpha).toFixed(3));
        }
        if (results) {
            if (results.sharpe != null) setOverlayCell('tbl-sharpe', results.sharpe);
            if (results.max_dd != null) setOverlayCell('tbl-max-dd', results.max_dd);
            if (results.sortino != null) setOverlayCell('tbl-sortino', results.sortino);
            if (results.calmar != null) setOverlayCell('tbl-calmar', results.calmar);
            if (results.cf_var != null) setOverlayCell('tbl-cf-var', results.cf_var);
            if (results.beta != null) setOverlayCell('tbl-beta', results.beta);
            if (results.ann_return != null) setOverlayCell('tbl-ann-return', results.ann_return);
            setOverlayCell('tbl-mc-hurdle', results.mc_hurdle);
        }
    }

    function showMetricsEmptyNote(show) {
        const note = document.getElementById('metrics-empty-note');
        if (note) note.hidden = !show;
    }

    async function fetchAndHydrate() {
        let full = null;
        let results = null;
        try {
            const [fullRes, resultsRes] = await Promise.all([
                fetch(asset('./data/full-metrics.json')),
                fetch(asset(DATA_PATH)),
            ]);
            if (fullRes.ok) full = await fullRes.json();
            if (resultsRes.ok) {
                results = await resultsRes.json();
                populateKPIs(results);
            }
            populateOverlayTable(full, results);
            showMetricsEmptyNote(!(full || results));
        } catch (_) {
            showMetricsEmptyNote(true);
        }
    }

    const DECK_PDF_REL =
        'deliverables/source/Client_Post_Mortem_Investment_Challenge-Team-5-BWC_CH200.pdf';
    const PPTX_SLIDE_BASE_REL =
        'deliverables/source/Client_Post_Mortem_Investment_Challenge-Team-5-BWC_CH200/';
    const PPTX_SLIDE_COUNT = 20;

    function probeImageUrl(url) {
        return new Promise((resolve) => {
            const probe = new Image();
            probe.onload = () => resolve(true);
            probe.onerror = () => resolve(false);
            probe.src = url;
        });
    }

    async function probeAsset(relativePath) {
        const url = asset(relativePath);
        const isImage = /\.(png|jpe?g|gif|webp|svg)$/i.test(relativePath);
        if (isImage && (await probeImageUrl(url))) return true;
        try {
            const res = await fetch(url, { method: 'HEAD', cache: 'force-cache' });
            if (res.ok) return true;
        } catch (_) {
            /* file:// or HEAD blocked — fall through */
        }
        return isImage ? false : probeImageUrl(url);
    }

    function initResolvedAssets() {
        document.querySelectorAll('iframe[src^="./"]').forEach((frame) => {
            if (frame.dataset.bwcResolved === '1') return;
            const src = frame.getAttribute('src');
            if (src) {
                frame.src = resolveHref(src);
                frame.dataset.bwcResolved = '1';
            }
        });
        document
            .querySelectorAll('.deck-action-row a[href^="./"]')
            .forEach((link) => {
                const href = link.getAttribute('href');
                if (href) link.setAttribute('href', resolveHref(href));
            });
    }

    function renderMetricsGrid(container, items, groups, highlightKeys) {
        if (!container) return;
        const byGroup = {};
        for (const item of items || []) {
            if (!byGroup[item.group]) byGroup[item.group] = [];
            byGroup[item.group].push(item);
        }
        container.innerHTML = groups
            .filter((g) => byGroup[g]?.length)
            .map(
                (g) => `
                <div class="kpi-group">
                    <h4 class="text-mono kpi-group-label">${g}</h4>
                    <div class="kpi-group-grid">
                        ${byGroup[g]
                            .map(
                                (m) => `
                            <div class="kpi-cell ${highlightKeys.has(m.key) ? 'kpi-cell-highlight' : ''}">
                                <span class="kpi-label text-mono">${m.label}</span>
                                <span class="kpi-value text-display">${m.value}</span>
                            </div>`
                            )
                            .join('')}
                    </div>
                </div>`
            )
            .join('');
    }

    async function renderExcelMetricsGrid() {
        const grid = document.getElementById('excel-metrics-grid');
        const deskGrid = document.getElementById('desk-metrics-grid');
        const prov = document.getElementById('excel-metrics-provenance');
        if (!grid && !deskGrid) return;
        try {
            const res = await fetch(asset('./data/excel-metrics.json'));
            if (!res.ok) return;
            const data = await res.json();
            if (prov && data.trading_start && data.trading_end) {
                prov.textContent = `Hult simulation desk freeze (Excel sheet005 + sheet011 + sheet013). Trading window: ${data.trading_start} to ${data.trading_end}.`;
            }
            renderMetricsGrid(
                deskGrid,
                data.advanced_grid,
                ['RISK_ADJ', 'TRADES'],
                new Set(['sharpe', 'profit_factor', 'expectancy'])
            );
            renderMetricsGrid(
                grid,
                data.grid,
                ['CAPITAL', 'RETURNS', 'RISK', 'INCOME', 'ACTIVITY'],
                new Set(['total_return', 'pnl', 'excess_return'])
            );
        } catch (_) {
            if (grid) {
                grid.innerHTML =
                    '<p class="text-mono text-muted">Run scripts/extract_frontend_narrative_data.py to generate excel-metrics.json</p>';
            }
        }
    }

    function initFooterYear() {
        const el = document.getElementById('footer-year');
        if (el) el.textContent = String(new Date().getFullYear());
    }

    const SPLASH_STORAGE_KEY = 'bwc-splash-dismissed';

    function dismissSplash(splash) {
        if (!splash) return;
        splash.classList.add('site-splash--out');
        splash.setAttribute('aria-hidden', 'true');
        try {
            sessionStorage.setItem(SPLASH_STORAGE_KEY, '1');
            document.documentElement.classList.add('splash-seen');
            document.documentElement.classList.remove('splash-pending');
        } catch (_) {
            /* ignore */
        }
        document.body.classList.remove('splash-active');
        const enterBtn = document.getElementById('splash-enter');
        if (enterBtn && typeof enterBtn.blur === 'function') {
            enterBtn.blur();
        }

        window.setTimeout(() => {
            document.body.classList.add('splash-dismissed');
            try {
                splash.remove();
            } catch (_) {
                /* ignore */
            }
        }, 480);
    }

    function initSplash() {
        const splash = document.getElementById('site-splash');
        const enterBtn = document.getElementById('splash-enter');
        if (!splash) return;

        let skipSplash = false;
        try {
            skipSplash = sessionStorage.getItem(SPLASH_STORAGE_KEY) === '1';
        } catch (_) {
            skipSplash = false;
        }

        if (skipSplash || document.documentElement.classList.contains('splash-seen')) {
            document.documentElement.classList.remove('splash-pending');
            return;
        }

        document.body.classList.add('splash-active');
        splash.removeAttribute('aria-hidden');

        function onEnter() {
            dismissSplash(splash);
        }

        enterBtn?.addEventListener('click', onEnter);

        document.addEventListener('keydown', (e) => {
            if (splash.classList.contains('site-splash--out')) return;
            if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
                if (e.target === enterBtn || !/input|textarea|select/i.test(e.target?.tagName || '')) {
                    e.preventDefault();
                    onEnter();
                }
            }
        });

        splash.querySelector('.site-splash__skip')?.addEventListener('click', () => {
            requestAnimationFrame(onEnter);
        });
    }

    function phaseForDate(phases, dateStr) {
        const d = new Date(dateStr);
        for (const p of phases || []) {
            const start = new Date(p.start);
            const end = new Date(p.end);
            if (d >= start && d <= end) return p;
        }
        return null;
    }

    function milestoneTone(event) {
        const e = String(event || '').toLowerCase();
        if (e.includes('emergency') || e.includes('triage')) return 'is-crisis';
        if (e.includes('close') || e.includes('simulation')) return 'is-close';
        if (e.includes('ceasefire') || e.includes('reconstruction')) return 'is-recovery';
        if (e.includes('stop-loss') || e.includes('collapse') || e.includes('tariff')) {
            return 'is-stress';
        }
        return '';
    }

    function formatDeskDate(dateStr) {
        const d = new Date(`${dateStr}T12:00:00`);
        if (Number.isNaN(d.getTime())) return dateStr;
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    function formatPhaseBadge(label) {
        const match = String(label || '').match(/Ph\s*(\d+)\s*(.+)/i);
        if (match) return `Phase ${match[1]}: ${match[2].trim()}`;
        return label || '';
    }

    function metricToneClass(value) {
        const num = Number(value);
        if (Number.isNaN(num) || num === 0) return 'is-flat';
        return num > 0 ? 'is-pos' : 'is-neg';
    }

    function formatSignedPct(value) {
        const num = Number(value);
        if (Number.isNaN(num)) return '—';
        const sign = num > 0 ? '+' : '';
        return `${sign}${num.toFixed(2)}%`;
    }

    function metricPillHtml(label, value, { kind = 'pct' } = {}) {
        const valueClass = kind === 'pct' ? metricToneClass(value) : 'is-neutral';
        const display =
            kind === 'nav'
                ? `$${Number(value).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
                : formatSignedPct(value);
        return `<span class="snake-metric-pill"><span class="snake-metric-pill__label text-mono">${label}</span><span class="snake-metric-pill__value text-mono ${valueClass}">${display}</span></span>`;
    }

    function deskTimelineCellHtml(m, phases, opts = {}) {
        const phase = phaseForDate(phases, m.date);
        const tone = milestoneTone(m.event);
        const step = String(opts.step ?? 0).padStart(2, '0');
        const phaseId = phase?.id ? ` data-phase="${phase.id}"` : '';
        const nav = m.portfolio_nav != null ? Number(m.portfolio_nav) : null;

        return `
            <article class="snake-milestone desk-timeline-entry ${tone}" role="listitem"${phaseId}>
                <header class="snake-milestone__meta">
                    <span class="snake-milestone__id text-mono">${step}</span>
                    <time class="snake-milestone__date text-mono" datetime="${m.date}">${formatDeskDate(m.date)}</time>
                </header>
                <h3 class="snake-milestone__title text-display">${m.event}</h3>
                <div class="snake-milestone__badges">
                    ${phase ? `<span class="snake-phase-badge text-mono">${formatPhaseBadge(phase.label)}</span>` : ''}
                </div>
                <div class="snake-milestone__metrics-row">
                    ${metricPillHtml('Desk', m.portfolio_return_pct)}
                    ${metricPillHtml('SPY', m.spy_return_pct)}
                    ${nav != null ? metricPillHtml('NAV', nav, { kind: 'nav' }) : ''}
                </div>
            </article>`;
    }

    function buildSnakeTimelineHtml(milestones, phases, cols = 4) {
        const items = Array.isArray(milestones) ? milestones.slice() : [];
        if (!items.length) return '';

        const first = items.shift();
        const rows = [];
        for (let i = 0; i < items.length; i += cols) {
            rows.push(items.slice(i, i + cols));
        }

        const parts = [];
        let stepCounter = 0;

        function buildSnakeStrokeSvg() {
            // SVG is a container; path is computed from DOM geometry after render.
            return `
                <svg class="snake-stroke" aria-hidden="true">
                    <path class="snake-stroke__path" d="" />
                </svg>`;
        }

        // Intro: Box 1 alone (top-left) + vertical drop to grid
        stepCounter += 1;
        const introCells = [
            deskTimelineCellHtml(first, phases, { step: stepCounter }),
            ...Array.from({ length: Math.max(0, cols - 1) }).map(
                () => `<div class="snake-spacer" aria-hidden="true"></div>`
            ),
        ].join('');
        parts.push(`
            <div class="snake-row snake-row--ltr snake-row--intro" role="list" data-snake-row="intro" style="--row-items: ${cols}">
                <div class="snake-row__cells">${introCells}</div>
            </div>`);

        rows.forEach((row, rowIndex) => {
            const isAlt = rowIndex % 2 === 1;
            const isLastRow = rowIndex === rows.length - 1;

            let cellsHtml = '';
            row.forEach((m) => {
                stepCounter += 1;
                cellsHtml += deskTimelineCellHtml(m, phases, { step: stepCounter });
            });

            // Pad with placeholders so the grid stays perfectly regular
            if (row.length < cols) {
                cellsHtml += Array.from({ length: cols - row.length })
                    .map(() => `<div class="snake-spacer" aria-hidden="true"></div>`)
                    .join('');
            }

            parts.push(`
                <div class="snake-row snake-row--ltr ${isAlt ? 'snake-row--alt' : ''} ${isLastRow ? 'snake-row--last' : ''}" role="list" data-snake-row="${rowIndex}" style="--row-items: ${cols}">
                    <div class="snake-row__cells">${cellsHtml}</div>
                </div>`);
        });

        // Outro: trading freeze + sunset (static)
        parts.push(`
            <div class="snake-row snake-row--ltr snake-row--outro" role="list" data-snake-row="outro" style="--row-items: ${cols}">
                <div class="snake-row__cells">
                    <div class="snake-spacer" aria-hidden="true"></div>
                    <div class="snake-spacer" aria-hidden="true"></div>
                    <div class="snake-spacer" aria-hidden="true"></div>
                    <article class="snake-milestone snake-milestone--outro" role="listitem">
                        <header class="snake-milestone__meta">
                            <span class="snake-milestone__id text-mono">TF</span>
                            <span class="snake-milestone__date text-mono">Freeze</span>
                        </header>
                        <h3 class="snake-milestone__title text-display">Trading freeze</h3>
                        <div class="snake-milestone__badges">
                            <span class="snake-phase-badge text-mono">Sunset path</span>
                        </div>
                        <div class="snake-milestone__metrics-row">
                            <span class="snake-metric-pill"><span class="snake-metric-pill__label text-mono">Status</span><span class="snake-metric-pill__value text-mono is-neutral">ARCHIVE</span></span>
                        </div>
                    </article>
                </div>
            </div>
            <div class="snake-row snake-row--ltr snake-row--outro2" role="list" data-snake-row="outro2" style="--row-items: ${cols}">
                <div class="snake-row__cells">
                    <div class="snake-spacer" aria-hidden="true"></div>
                    <div class="snake-spacer" aria-hidden="true"></div>
                    <div class="snake-spacer" aria-hidden="true"></div>
                    <article class="snake-milestone snake-milestone--sunset" role="listitem">
                        <header class="snake-milestone__meta">
                            <span class="snake-milestone__id text-mono">SS</span>
                            <span class="snake-milestone__date text-mono">Seal</span>
                        </header>
                        <h3 class="snake-milestone__title text-display">Sunset</h3>
                        <div class="snake-milestone__badges">
                            <span class="snake-phase-badge text-mono">Static publication</span>
                        </div>
                        <div class="snake-milestone__metrics-row">
                            <span class="snake-metric-pill"><span class="snake-metric-pill__label text-mono">Mode</span><span class="snake-metric-pill__value text-mono is-neutral">READ‑ONLY</span></span>
                        </div>
                    </article>
                </div>
            </div>`);

        return `<div class="desk-timeline-snake__inner"><div class="snake-grid-backdrop" aria-hidden="true"></div>${buildSnakeStrokeSvg()}${parts.join('')}</div>`;
    }

    // Base-up approach: standardized geometry with minimal measuring.
    // We measure only the row midlines to prevent drift across rows.
    function renderSnakeStrokeDeterministic(root, { cols = 4, rowCount = 4 } = {}) {
        const inner = root?.querySelector('.desk-timeline-snake__inner');
        const svg = inner?.querySelector('svg.snake-stroke');
        const path = svg?.querySelector('path.snake-stroke__path');
        if (!inner || !svg || !path) return;

        const W = Math.max(1, inner.clientWidth);
        const cellW = W / cols;
        const xStart = cellW * 0.5;
        const xEnd = W - xStart;

        // Standardize drop based on median card height (consistent across rows).
        const cardEls = Array.from(
            inner.querySelectorAll(
                '.snake-milestone:not(.snake-milestone--outro):not(.snake-milestone--sunset)'
            )
        );
        const heights = cardEls
            .map((el) => el.getBoundingClientRect().height)
            .filter((h) => Number.isFinite(h) && h > 0)
            .sort((a, b) => a - b);
        const medianH = heights.length ? heights[Math.floor(heights.length / 2)] : 150;
        const cardH = Math.max(120, Math.min(230, medianH));

        function rowMidY(rowEl) {
            const firstCard = rowEl?.querySelector('.snake-milestone');
            if (!firstCard) return null;
            const innerRect = inner.getBoundingClientRect();
            const r = firstCard.getBoundingClientRect();
            return r.top - innerRect.top + r.height / 2;
        }

        // Collect actual midlines for milestone rows 0..rowCount-1
        const yRows = [];
        for (let i = 0; i < rowCount; i += 1) {
            const rowEl = inner.querySelector(`.snake-row[data-snake-row="${i}"]`);
            const y = rowMidY(rowEl);
            if (y != null) yRows.push(y);
        }
        if (!yRows.length) return;

        // Bigger “bracket” turns: ensure the return run is visible between rows,
        // but clamp so the turn NEVER overshoots into the next row midline.
        let minGap = 240;
        for (let i = 0; i < yRows.length - 1; i += 1) {
            minGap = Math.min(minGap, Math.max(1, yRows[i + 1] - yRows[i]));
        }
        const desiredDrop = Math.round(cardH * 1.35);
        const maxDrop = Math.max(110, Math.round(minGap - cardH * 0.24));
        const drop = Math.max(110, Math.min(desiredDrop, maxDrop)); // equal vertical drop on both sides

        const introRow = inner.querySelector('.snake-row--intro');
        const yIntro = rowMidY(introRow) ?? Math.max(0, yRows[0] - (cardH + drop));

        let d = `M ${xStart.toFixed(2)} ${yIntro.toFixed(2)} V ${yRows[0].toFixed(2)}`;
        for (let i = 0; i < yRows.length; i += 1) {
            d += ` H ${xEnd}`;
            if (i === yRows.length - 1) break;
            const yTurn = Math.min(yRows[i] + drop, yRows[i + 1] - 32);
            d += ` V ${yTurn.toFixed(2)} H ${xStart.toFixed(2)} V ${yRows[i + 1].toFixed(2)}`;
        }

        // drop to trading freeze and sunset (right side)
        const lastY = yRows[yRows.length - 1];
        const yTf = lastY + drop + Math.max(10, Math.round(cardH * 0.15));
        const ySs = yTf + cardH + Math.max(56, Math.round(cardH * 0.46));
        d += ` V ${yTf} V ${ySs}`;

        const H = Math.max(1, inner.scrollHeight);
        svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
        svg.setAttribute('preserveAspectRatio', 'none');
        path.setAttribute('d', d);
    }

    async function renderDeskTimeline() {
        const root = document.getElementById('desk-timeline');
        if (!root) return;
        try {
            const res = await fetch(asset('./data/desk-timeline.json'));
            if (!res.ok) throw new Error('desk-timeline.json missing');
            const data = await res.json();
            const milestones = data.milestones || [];
            const phases = data.phases || [];

            if (!milestones.length) {
                root.innerHTML =
                    '<p class="text-mono text-muted">Timeline unavailable. Run build_frontend_assets.</p>';
                return;
            }

            root.innerHTML = buildSnakeTimelineHtml(milestones, phases, 4);
            const paintStroke = () => renderSnakeStrokeDeterministic(root, { cols: 4, rowCount: 4 });
            requestAnimationFrame(paintStroke);

            // Keep it aligned on responsive reflow.
            if (root.dataset.snakeStrokeBound !== '1') {
                root.dataset.snakeStrokeBound = '1';
                let t = null;
                window.addEventListener(
                    'resize',
                    () => {
                        if (t) window.clearTimeout(t);
                        t = window.setTimeout(() => requestAnimationFrame(paintStroke), 60);
                    },
                    { passive: true }
                );
            }
        } catch (_) {
            root.innerHTML =
                '<p class="text-mono text-muted">Timeline unavailable. Run scripts/extract_frontend_narrative_data.py.</p>';
        }
    }

    async function renderDeliverablesManifest() {
        const list = document.getElementById('deliverables-manifest-list');
        if (!list) return;
        try {
            const res = await fetch(asset('./data/deliverables-manifest.json'));
            if (!res.ok) return;
            const manifest = await res.json();
            const files = manifest.files || [];
            list.innerHTML = files
                .map((f) => {
                    const sizeKb = f.size_bytes ? ` (${Math.round(f.size_bytes / 1024)} KB)` : '';
                    const href = resolveHref(f.href);
                    return `<li><a href="${href}" download class="link-underline">${f.name}</a><span class="text-muted text-mono">${sizeKb}</span></li>`;
                })
                .join('');
        } catch (_) {
            list.innerHTML = '<li class="text-muted text-mono">Manifest unavailable - run build_frontend_assets</li>';
        }
    }

    function initKaTeX() {
        if (typeof renderMathInElement !== 'function') return;
        renderMathInElement(document.body, {
            delimiters: [
                { left: '$$', right: '$$', display: true },
                { left: '$', right: '$', display: false },
            ],
            throwOnError: false,
        });
    }

    function initScrollReveal() {
        const targets = document.querySelectorAll('.reveal-on-scroll');
        if (!targets.length) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('revealed');
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.08, rootMargin: '0px 0px -40px 0px' }
        );

        targets.forEach((el) => observer.observe(el));
    }

    function initStatAnimations() {
        const stats = document.querySelectorAll('[data-stat-animate]');
        if (!stats.length) return;

        const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        function formatStat(value, decimals, suffix) {
            const sign = value > 0 && suffix === '%' ? '+' : '';
            const body = Number(value).toFixed(decimals);
            return `${sign}${body}${suffix}`;
        }

        function animateEl(el) {
            if (el.dataset.statDone === '1') return;
            el.dataset.statDone = '1';
            const target = parseFloat(el.dataset.statValue || '0', 10);
            const decimals = parseInt(el.dataset.statDecimals || '2', 10);
            const suffix = el.dataset.statSuffix || '';
            if (prefersReduced || Number.isNaN(target)) {
                el.textContent = formatStat(target, decimals, suffix);
                el.classList.add('stat-animate-done');
                return;
            }
            el.classList.add('stat-animate-ready');
            const start = performance.now();
            const duration = 900;
            function tick(now) {
                const t = Math.min(1, (now - start) / duration);
                const eased = 1 - Math.pow(1 - t, 3);
                const current = target * eased;
                el.textContent = formatStat(current, decimals, suffix);
                if (t < 1) {
                    requestAnimationFrame(tick);
                } else {
                    el.classList.remove('stat-animate-ready');
                    el.classList.add('stat-animate-done');
                }
            }
            requestAnimationFrame(tick);
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        animateEl(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.35 }
        );
        stats.forEach((el) => observer.observe(el));
    }

    function initNavDock() {
        const nav = document.getElementById('site-nav-dock');
        const sentinel = document.getElementById('nav-reveal-sentinel');
        if (!nav || !sentinel) return;

        const revealOffset = 8;

        function updateNavDock() {
            const pastExecSummary = sentinel.getBoundingClientRect().top <= revealOffset;
            document.body.classList.toggle('nav-dock-visible', pastExecSummary);
            if (pastExecSummary) {
                nav.removeAttribute('aria-hidden');
                nav.removeAttribute('inert');
            } else {
                nav.setAttribute('aria-hidden', 'true');
                nav.setAttribute('inert', '');
            }
        }

        updateNavDock();
        window.addEventListener('scroll', updateNavDock, { passive: true });
        window.addEventListener('resize', updateNavDock, { passive: true });
    }

    function initScrollSpy() {
        const links = document.querySelectorAll('.nav-link[data-section]');
        if (!links.length) return;

        const sectionIds = Array.from(links).map((l) => l.dataset.section);
        const sections = sectionIds
            .map((id) => document.getElementById(id))
            .filter(Boolean);

        function setActive(sectionId) {
            links.forEach((link) => {
                link.classList.toggle('active', link.dataset.section === sectionId);
                if (link.dataset.section === sectionId) {
                    link.setAttribute('aria-current', 'true');
                } else {
                    link.removeAttribute('aria-current');
                }
            });
        }

        const observer = new IntersectionObserver(
            (entries) => {
                const visible = entries
                    .filter((e) => e.isIntersecting)
                    .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
                if (visible.length) {
                    setActive(visible[0].target.id);
                }
            },
            { rootMargin: '-20% 0px -55% 0px', threshold: [0, 0.1, 0.25] }
        );

        sections.forEach((s) => observer.observe(s));

        function syncHashActive() {
            const hash = window.location.hash.replace('#', '');
            if (hash && sectionIds.includes(hash)) {
                setActive(hash);
            }
        }

        window.addEventListener('hashchange', syncHashActive);
        syncHashActive();
        if (!window.location.hash.replace('#', '') && sections.length) {
            setActive(sections[0].id);
        }
    }

    function initStatusBadge() {
        const dot = document.getElementById('status-dot');
        const label = document.getElementById('status-label');
        if (!dot || !label) return;

        dot.style.backgroundColor = 'var(--color-text-muted)';
        label.textContent = 'STATIC ARCHIVE';
    }

    function initDialogs() {
        const triggers = document.querySelectorAll('[data-dialog-target]');
        if (!triggers.length) return;

        triggers.forEach((trigger) => {
            const dialogId = trigger.getAttribute('data-dialog-target');
            if (!dialogId) return;
            const dialog = document.getElementById(dialogId);
            if (!(dialog instanceof HTMLDialogElement)) return;

            const closeBtn = dialog.querySelector('[data-dialog-close]');
            closeBtn?.addEventListener('click', () => dialog.close());

            trigger.addEventListener('click', () => {
                if (typeof dialog.showModal === 'function') dialog.showModal();
                else dialog.setAttribute('open', '');
            });

            dialog.addEventListener('click', (e) => {
                // Click on backdrop closes (native dialog behavior is inconsistent across browsers)
                const rect = dialog.getBoundingClientRect();
                const isInDialog =
                    rect.top <= e.clientY &&
                    e.clientY <= rect.bottom &&
                    rect.left <= e.clientX &&
                    e.clientX <= rect.right;
                if (!isInDialog) dialog.close();
            });
        });
    }

    function initPagesDiagnostics() {
        if (!window.BWC) return;
        window.BWC.pagesDiag = {
            siteBase: window.BWC.siteBase,
            pathname: window.location.pathname,
            sampleSlide: asset(`${PPTX_SLIDE_BASE_REL}Slide1.PNG`),
            sampleData: asset('./data/results.json'),
        };
    }

    document.addEventListener('DOMContentLoaded', () => {
        if (window.BWC && typeof window.BWC.rewriteRelativeUrls === 'function') {
            window.BWC.rewriteRelativeUrls(document.body);
        }
        initResolvedAssets();
        initPagesDiagnostics();
        initNavDock();
        initScrollSpy();
        initScrollReveal();
        initStatusBadge();
        initDialogs();
        fetchAndHydrate();
        renderExcelMetricsGrid();
        renderDeskTimeline();
        renderDeliverablesManifest();
        initStatAnimations();
        initSplash();
        initFooterYear();
        initCustomCursor();
        hookNewScrollReveal();
        if (typeof renderMathInElement === 'function') {
            initKaTeX();
        } else {
            window.addEventListener('load', initKaTeX);
        }
    });
})();

    /* =========================================================
       AWWWARDS NARRATIVE EXTENSIONS (JS)
       ========================================================= */

    function initCustomCursor() {
        const cursor = document.querySelector('.custom-cursor');
        if (!cursor) return;

        let mouseX = window.innerWidth / 2;
        let mouseY = window.innerHeight / 2;
        let cursorX = mouseX;
        let cursorY = mouseY;
        let isHovering = false;

        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });

        const interactables = document.querySelectorAll('a, button, .team-trigger, canvas');
        interactables.forEach(el => {
            el.addEventListener('mouseenter', () => {
                isHovering = true;
                cursor.style.transform = 'translate(-50%, -50%) scale(2.5)';
                cursor.style.backgroundColor = 'var(--color-bg-base)';
                cursor.style.border = '1px solid var(--color-accent-primary)';
            });
            el.addEventListener('mouseleave', () => {
                isHovering = false;
                cursor.style.transform = 'translate(-50%, -50%) scale(1)';
                cursor.style.backgroundColor = 'var(--color-accent-primary)';
                cursor.style.border = 'none';
            });
        });

        function animateCursor() {
            // Lerp formulation for smooth trail
            cursorX += (mouseX - cursorX) * 0.15;
            cursorY += (mouseY - cursorY) * 0.15;
            
            // Apply coordinates
            cursor.style.left = cursorX + 'px';
            cursor.style.top = cursorY + 'px';

            requestAnimationFrame(animateCursor);
        }
        
        animateCursor();
    }

    function hookNewScrollReveal() {
        const targets = document.querySelectorAll('.fade-up:not(.site-footer)');
        if (!targets.length) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('revealed');
                    }
                });
            },
            { threshold: 0.1 }
        );

        targets.forEach((el) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(30px)';
            el.style.transition = 'opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)';
            observer.observe(el);
        });

        // Add a global css class when revealed
        document.head.insertAdjacentHTML('beforeend', '<style>.fade-up.revealed { opacity: 1 !important; transform: translateY(0) !important; }</style>');
    }

    /* =========================================================
       AWWWARDS CAROUSEL EXTENSION (JS)
       ========================================================= */
       
    function initCarousels() {
        const scaffolds = document.querySelectorAll('.carousel-scaffold');
        
        scaffolds.forEach(scaffold => {
            const container = scaffold.parentElement;
            const prevBtn = container.querySelector('.carousel-btn:first-of-type');
            const nextBtn = container.querySelector('.carousel-btn:last-of-type');
            const images = Array.from(scaffold.querySelectorAll('img'));
            
            if (images.length === 0) return; // No images yet

            let currentIndex = 0;

            // Initialize display
            images.forEach((img, i) => {
                img.style.position = 'absolute';
                img.style.top = '0';
                img.style.left = '0';
                img.style.width = '100%';
                img.style.height = '100%';
                img.style.objectFit = 'contain';
                img.style.transition = 'opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
                img.style.opacity = i === 0 ? '1' : '0';
                img.style.pointerEvents = i === 0 ? 'auto' : 'none';
            });
            
            // Hide the placeholder text if images exist
            const placeholder = scaffold.querySelector('.carousel-placeholder-copy');
            if (placeholder) placeholder.style.display = 'none';

            function updateCarousel() {
                images.forEach((img, i) => {
                    img.style.opacity = i === currentIndex ? '1' : '0';
                    img.style.pointerEvents = i === currentIndex ? 'auto' : 'none';
                });
            }

            if (prevBtn) {
                prevBtn.addEventListener('click', () => {
                    currentIndex = (currentIndex > 0) ? currentIndex - 1 : images.length - 1;
                    updateCarousel();
                });
            }
            if (nextBtn) {
                nextBtn.addEventListener('click', () => {
                    currentIndex = (currentIndex < images.length - 1) ? currentIndex + 1 : 0;
                    updateCarousel();
                });
            }
        });
    }