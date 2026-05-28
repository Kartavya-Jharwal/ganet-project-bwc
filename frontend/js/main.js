/**
 * BWC-QUANT | Frontend Hydration Engine
 * Static archive: loads metrics from data/results.json only (no live Appwrite).
 */

(function () {
    'use strict';

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
                fetch('./data/full-metrics.json'),
                fetch(DATA_PATH),
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

    const DECK_PDF =
        './deliverables/source/Client_Post_Mortem_Investment_Challenge-Team-5-BWC_CH200.pdf';
    const PPTX_SLIDE_BASE =
        './deliverables/source/Client_Post_Mortem_Investment_Challenge-Team-5-BWC_CH200/';
    const PPTX_SLIDE_COUNT = 20;

    function probeImageSrc(url) {
        return new Promise((resolve) => {
            const probe = new Image();
            probe.onload = () => resolve(true);
            probe.onerror = () => resolve(false);
            probe.src = url;
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
            const res = await fetch('./data/excel-metrics.json');
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

    async function renderReportExcerpts() {
        try {
            const res = await fetch('./data/report-excerpts.json');
            if (!res.ok) return;
            const data = await res.json();
            const byId = Object.fromEntries(
                (data.excerpts || []).map((e) => [e.id, e])
            );
            document.querySelectorAll('.report-excerpt[data-excerpt-id]').forEach((el) => {
                const ex = byId[el.dataset.excerptId];
                if (!ex) return;
                el.innerHTML = `
                    <p class="text-mono text-accent excerpt-kicker">${ex.kicker} / FROM WRITTEN MEMO</p>
                    <p class="excerpt-body text-body leading-relaxed text-muted">${ex.text}</p>
                    <footer class="excerpt-footer text-mono">
                        <a href="./report.html" target="_blank" rel="noopener" class="link-underline">Full IC memo (report) ↗</a>
                    </footer>`;
            });
        } catch (_) {
            /* static fallbacks remain in first executive block if present */
        }
    }

    async function initDeckViewer() {
        const scaffold = document.getElementById('pptx-carousel-scaffold');
        const pdfWrap = document.getElementById('deck-pdf-viewer');
        const controls = document.getElementById('pptx-carousel-controls');
        const note = document.getElementById('deck-viewer-note');
        const label = document.getElementById('pptx-slide-label');
        const prev = document.getElementById('pptx-prev');
        const next = document.getElementById('pptx-next');
        if (!scaffold) return;

        const slideExt = 'PNG';

        function showPdfMode(message) {
            if (pdfWrap) pdfWrap.hidden = false;
            scaffold.hidden = true;
            if (controls) controls.hidden = true;
            if (note) {
                note.hidden = false;
                note.textContent =
                    message || 'Slide PNGs unavailable; showing PDF instead.';
            }
        }

        function showCarouselMode() {
            if (pdfWrap) pdfWrap.hidden = true;
            scaffold.hidden = false;
            if (controls) controls.hidden = false;
            if (note) note.hidden = true;
        }

        showCarouselMode();
        const images = [];

        for (let i = 1; i <= PPTX_SLIDE_COUNT; i += 1) {
            const img = document.createElement('img');
            img.src = `${PPTX_SLIDE_BASE}Slide${i}.${slideExt}`;
            img.alt = `Post-mortem deck slide ${i} of ${PPTX_SLIDE_COUNT}`;
            img.loading = i <= 3 ? 'eager' : 'lazy';
            img.decoding = 'async';
            img.addEventListener('error', () => {
                if (i === 1) showPdfMode(`Slide ${i} could not load; showing PDF.`);
            });
            scaffold.appendChild(img);
            images.push(img);
        }

        let current = 0;

        function update() {
            images.forEach((img, i) => {
                img.style.opacity = i === current ? '1' : '0';
                img.style.pointerEvents = i === current ? 'auto' : 'none';
                img.setAttribute('aria-hidden', i === current ? 'false' : 'true');
            });
            if (label) label.textContent = `Slide ${current + 1} of ${PPTX_SLIDE_COUNT}`;
        }

        images.forEach((img) => {
            img.style.position = 'absolute';
            img.style.inset = '0';
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'contain';
            img.style.transition = 'opacity 0.5s cubic-bezier(0.16, 1, 0.3, 1)';
        });

        if (prev) {
            prev.addEventListener('click', () => {
                current = current > 0 ? current - 1 : PPTX_SLIDE_COUNT - 1;
                update();
            });
        }
        if (next) {
            next.addEventListener('click', () => {
                current = current < PPTX_SLIDE_COUNT - 1 ? current + 1 : 0;
                update();
            });
        }

        document.addEventListener('keydown', (e) => {
            if (scaffold.hidden) return;
            const evidence = document.getElementById('evidence');
            if (!evidence?.getBoundingClientRect) return;
            const r = evidence.getBoundingClientRect();
            if (r.bottom < 0 || r.top > window.innerHeight) return;
            if (e.key === 'ArrowLeft') prev?.click();
            if (e.key === 'ArrowRight') next?.click();
        });

        update();
    }

    async function renderDeliverablesManifest() {
        const list = document.getElementById('deliverables-manifest-list');
        if (!list) return;
        try {
            const res = await fetch('./data/deliverables-manifest.json');
            if (!res.ok) return;
            const manifest = await res.json();
            const files = manifest.files || [];
            list.innerHTML = files
                .map((f) => {
                    const sizeKb = f.size_bytes ? ` (${Math.round(f.size_bytes / 1024)} KB)` : '';
                    return `<li><a href="${f.href}" download class="link-underline">${f.name}</a><span class="text-muted text-mono">${sizeKb}</span></li>`;
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

    function initDrawdownBars() {
        const fills = document.querySelectorAll('.drawdown-fill[data-drawdown-pct]');
        if (!fills.length) return;
        const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) return;
                    const fill = entry.target;
                    if (prefersReduced) {
                        fill.classList.add('drawdown-animated');
                    } else {
                        requestAnimationFrame(() => fill.classList.add('drawdown-animated'));
                    }
                    observer.unobserve(fill);
                });
            },
            { threshold: 0.25 }
        );
        fills.forEach((f) => observer.observe(f));
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

        const hash = window.location.hash.replace('#', '');
        if (hash && sectionIds.includes(hash)) {
            setActive(hash);
        } else if (sections.length) {
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

    function mountVideoBackground() {
        const video = document.querySelector('.hero-video');
        const fallback = document.getElementById('hero-fallback');
        if (!video) return;

        const hideFallback = () => {
            if (fallback) fallback.style.display = 'none';
            video.style.display = 'block';
        };

        video.addEventListener('canplay', hideFallback);
        video.addEventListener('error', () => {
            video.style.display = 'none';
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        initScrollSpy();
        initScrollReveal();
        initStatusBadge();
        fetchAndHydrate();
        renderExcelMetricsGrid();
        renderReportExcerpts();
        renderDeliverablesManifest();
        initDeckViewer();
        initStatAnimations();
        initDrawdownBars();
        initCustomCursor();
        initDisclaimer();
        hookNewScrollReveal();
        mountVideoBackground();
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

        const interactables = document.querySelectorAll('a, button, .team-trigger, canvas, video');
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
        const targets = document.querySelectorAll('.fade-up');
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
    /* =========================================================
       FIRST VISIT DISCLAIMER (JS)
       ========================================================= */
       
    function initDisclaimer() {
        if (!localStorage.getItem('bwc_disclaimer_seen')) {
            const dialog = document.createElement('dialog');
            dialog.id = 'first-visit-disclaimer';
            dialog.style.padding = '0';
            dialog.style.border = 'none';
            dialog.style.background = 'transparent';
            
            dialog.innerHTML = \
                <div class="dialog-content" style="max-width: 600px; padding: var(--spacing-6); background: var(--color-bg-surface-elevated); border: 1px solid var(--border-color); color: var(--color-text-primary); margin: auto;">
                    <button class="dialog-close" onclick="this.closest('dialog').close(); localStorage.setItem('bwc_disclaimer_seen', 'true');" style="position:absolute; right:1.5rem; top:1.5rem; background:transparent; border:none; color:inherit; font-size:1.5rem; cursor:pointer;">×</button>
                    <h3 class="text-display text-accent mb-tight">Creative Protocol</h3>
                    <h4 class="text-mono text-muted mb-loose">THE INVESTMENT CHALLENGE &bull; CHL-0200</h4>
                    <div class="text-body leading-relaxed mb-loose">
                        <p class="mb-tight">Welcome to the Project BWC Post-Mortem.</p>
                        <p class="mb-tight" style="color:var(--color-accent-primary);"><strong>Disclaimer:</strong> This website takes professional and creative liberty in presenting our performance data.</p>
                        <p class="mb-tight">This specific digital format was not explicitly requested or vetted by Professor Daniela Neiderer, nor our teammates. It serves as an independent proof-of-work showcasing our strategy, combining top-down research approaches, technical analysis, risk management, and discretionary human reasoning mapped in our Trading Diary.</p>
                    </div>
                    <button onclick="this.closest('dialog').close(); localStorage.setItem('bwc_disclaimer_seen', 'true');" style="background:var(--color-text-primary); color:var(--color-bg-base); border:none; padding:var(--spacing-2) var(--spacing-4); cursor:pointer; font-family:var(--font-mono); font-weight:600;">ACKNOWLEDGE</button>
                </div>
            \;
            
            // Add a simple backdrop style if browsers need it
            dialog.style.position = 'fixed';
            dialog.style.inset = '0';
            dialog.style.margin = 'auto';
            document.body.appendChild(dialog);
            
            dialog.showModal();
        }
    }
