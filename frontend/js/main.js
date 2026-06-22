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

    const jsonCache = new Map();
    const IFRAME_LOAD_CONCURRENCY = 2;
    const iframeLoadQueue = [];
    let iframeLoadsActive = 0;
    let cachedExcelMetrics = null;

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

    function formatDeskPct(value, digits = 2) {
        const n = Number(String(value).replace('%', '').trim());
        if (Number.isNaN(n)) return null;
        const sign = n > 0 ? '+' : '';
        return `${sign}${n.toFixed(digits)}%`;
    }

    function populateOverlayMetrics(full, results) {
        if (full) {
            setOverlayCell('tbl-total-return', formatOverlayPct(full.total_return, 1));
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
            if (results.total_return != null) {
                setOverlayCell('tbl-total-return', formatOverlayPct(results.total_return, 1));
            }
            setOverlayCell('tbl-mc-hurdle', results.mc_hurdle);
        }
    }

    function showMetricsEmptyNote(show) {
        const note = document.getElementById('metrics-empty-note');
        if (note) note.hidden = !show;
    }

    function hydrateFromBootstrapData(full, results) {
        if (results) populateKPIs(results);
        populateOverlayMetrics(full, results);
        showMetricsEmptyNote(!(full || results));
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
            /* file:// or HEAD blocked: fall through */
        }
        return isImage ? false : probeImageUrl(url);
    }

    function initResolvedAssets() {
        document
            .querySelectorAll('.deck-action-row a[href^="./"]')
            .forEach((link) => {
                const href = link.getAttribute('href');
                if (href) link.setAttribute('href', resolveHref(href));
            });
    }

    function isPriorityIframe(frame) {
        return Boolean(frame?.closest('.desk-performance-embed, #evidence'));
    }

    function isDeskChartIframe(frame) {
        return Boolean(frame?.closest('#evidence'));
    }

    function drainIframeQueue() {
        while (iframeLoadsActive < IFRAME_LOAD_CONCURRENCY && iframeLoadQueue.length) {
            const frame = iframeLoadQueue.shift();
            if (!frame || frame.dataset.bwcResolved === '1') continue;

            const src = frame.getAttribute('data-src');
            if (!src) continue;

            iframeLoadsActive += 1;
            const onDone = () => {
                frame.dataset.bwcLoaded = '1';
                iframeLoadsActive -= 1;
                drainIframeQueue();
            };
            frame.addEventListener('load', onDone, { once: true });
            frame.addEventListener('error', onDone, { once: true });
            if (!isDeskChartIframe(frame)) {
                frame.loading = 'lazy';
            }
            frame.src = resolveHref(src);
            frame.dataset.bwcResolved = '1';
            delete frame.dataset.bwcQueued;
        }
    }

    function loadChartIframe(frame, { priority = false } = {}) {
        if (!frame || frame.dataset.bwcResolved === '1' || frame.dataset.bwcQueued === '1') return;
        frame.dataset.bwcQueued = '1';
        if (priority || isPriorityIframe(frame)) {
            iframeLoadQueue.unshift(frame);
        } else {
            iframeLoadQueue.push(frame);
        }
        drainIframeQueue();
    }

    function waitForPriorityCharts({ timeoutMs = 4500 } = {}) {
        const frames = Array.from(document.querySelectorAll('#evidence iframe[data-src]'));
        if (!frames.length) return Promise.resolve(true);

        frames.forEach((frame) => loadChartIframe(frame, { priority: true }));

        const waits = frames.map(
            (frame) =>
                new Promise((resolve) => {
                    if (frame.dataset.bwcLoaded === '1') {
                        resolve(true);
                        return;
                    }
                    const done = () => resolve(true);
                    frame.addEventListener('load', done, { once: true });
                    frame.addEventListener('error', done, { once: true });
                })
        );

        const timeout = new Promise((resolve) => window.setTimeout(() => resolve(true), timeoutMs));
        return Promise.race([Promise.all(waits).then(() => true), timeout]);
    }

    function preloadJson(relativePath) {
        if (!jsonCache.has(relativePath)) {
            jsonCache.set(
                relativePath,
                fetch(asset(relativePath), { cache: 'force-cache' })
                    .then((res) => (res.ok ? res.json() : null))
                    .catch(() => null)
            );
        }
        return jsonCache.get(relativePath);
    }

    function waitForFonts() {
        if (document.fonts && typeof document.fonts.ready?.then === 'function') {
            return document.fonts.ready.catch(() => {});
        }
        return Promise.resolve();
    }

    function chartLookaheadPx() {
        return Math.max(560, Math.round((window.innerHeight || 800) * 1.15));
    }

    function revealNearbyFadeUps(marginPx) {
        document.querySelectorAll('.fade-up:not(.revealed):not(.ic-section)').forEach((el) => {
            if (isElementInViewport(el, marginPx)) el.classList.add('revealed');
        });
    }

    function isGalleryChartRegion(frame) {
        return Boolean(frame?.closest('.research-band--gallery, .viz-gallery-grid'));
    }

    function isGalleryRegionInView(frame) {
        const region = frame?.closest('.research-band--gallery, .viz-gallery-grid');
        if (!region) return true;
        return isElementInViewport(region, chartLookaheadPx());
    }

    function prefetchNearbyCharts() {
        const margin = chartLookaheadPx();
        document.querySelectorAll('iframe[data-src]').forEach((frame) => {
            if (frame.dataset.bwcResolved === '1' || frame.dataset.bwcQueued === '1') return;
            const priority = isPriorityIframe(frame);
            if (!priority && isGalleryChartRegion(frame) && !isGalleryRegionInView(frame)) return;
            if (!isElementInViewport(frame, margin)) return;
            loadChartIframe(frame, { priority });
        });
    }

    function eagerLoadDeskCharts() {
        document.querySelectorAll('#evidence iframe[data-src]').forEach((frame) => {
            loadChartIframe(frame, { priority: true });
        });
    }

    function resumeVisibleVideos() {
        if (document.documentElement.classList.contains('is-scroll-active')) return;
        const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (reduceMotion) return;

        document.querySelectorAll('video[data-src]').forEach((video) => {
            const rect = video.getBoundingClientRect();
            const inView =
                rect.top < window.innerHeight * 0.9 && rect.bottom > window.innerHeight * 0.1;
            if (!inView) {
                syncLazyVideoPlayback(video, false);
                return;
            }
            loadLazyVideo(video, { play: true });
        });
    }

    function initMediaCoordinator() {
        let scrolling = false;
        let scrollEndTimer = 0;
        let chartThrottleTimer = 0;

        function setScrolling(active) {
            if (scrolling === active) return;
            scrolling = active;
            document.documentElement.classList.toggle('is-scroll-active', active);
            if (active) {
                pauseAllLazyVideos();
                return;
            }
            prefetchNearbyCharts();
            resumeVisibleVideos();
        }

        function syncPageVisible() {
            document.documentElement.classList.toggle('is-page-visible', !document.hidden);
            if (document.hidden) pauseAllLazyVideos();
            else resumeVisibleVideos();
        }

        syncPageVisible();
        document.addEventListener('visibilitychange', syncPageVisible);

        prefetchNearbyCharts();
        revealNearbyFadeUps(chartLookaheadPx());

        window.addEventListener(
            'scroll',
            () => {
                setScrolling(true);
                clearTimeout(scrollEndTimer);
                scrollEndTimer = window.setTimeout(() => setScrolling(false), 140);

                revealNearbyFadeUps(chartLookaheadPx());
                if (!chartThrottleTimer) {
                    chartThrottleTimer = window.setTimeout(() => {
                        chartThrottleTimer = 0;
                        prefetchNearbyCharts();
                    }, 120);
                }
            },
            { passive: true }
        );

        window.addEventListener('resize', () => {
            prefetchNearbyCharts();
            resumeVisibleVideos();
        }, { passive: true });
        window.addEventListener('pageshow', () => {
            prefetchNearbyCharts();
            resumeVisibleVideos();
        }, { passive: true });
    }

    function pauseAllLazyVideos() {
        document.querySelectorAll('video[data-src]').forEach((video) => {
            if (video.dataset.bwcVideoLoaded === '1') video.pause();
        });
    }

    function initLazyChartIframes() {
        const frames = document.querySelectorAll('iframe[data-src]');
        if (!frames.length) return;
        const marginPx = chartLookaheadPx();
        if (!('IntersectionObserver' in window)) {
            frames.forEach((frame) => loadChartIframe(frame, { priority: isPriorityIframe(frame) }));
            return;
        }
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) return;
                    loadChartIframe(entry.target, { priority: isPriorityIframe(entry.target) });
                    observer.unobserve(entry.target);
                });
            },
            { rootMargin: `${marginPx}px 0px`, threshold: 0.01 }
        );
        frames.forEach((frame) => observer.observe(frame));
    }

    function isElementInViewport(el, marginPx = 320) {
        if (!el || typeof el.getBoundingClientRect !== 'function') return false;
        const rect = el.getBoundingClientRect();
        return rect.bottom >= -marginPx && rect.top <= window.innerHeight + marginPx;
    }

    function hydrateMediaRoot(root) {
        if (!root) return;
        const margin = chartLookaheadPx();
        root.querySelectorAll('iframe[data-src]').forEach((frame) => {
            if (!isElementInViewport(frame, margin)) return;
            loadChartIframe(frame, { priority: isPriorityIframe(frame) });
        });
    }

    function initBwcMediaZones() {
        const zones = document.querySelectorAll('#validator, #stack .stack-table-media, #stack .stack-primer');
        if (!zones.length) return;

        const flushVisible = () => {
            const margin = chartLookaheadPx();
            zones.forEach((zone) => {
                if (isElementInViewport(zone, margin)) hydrateMediaRoot(zone);
            });
        };

        flushVisible();

        if (!('IntersectionObserver' in window)) {
            zones.forEach((zone) => hydrateMediaRoot(zone));
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) return;
                    hydrateMediaRoot(entry.target);
                });
            },
            { rootMargin: `${chartLookaheadPx()}px 0px`, threshold: 0.01 }
        );

        zones.forEach((zone) => observer.observe(zone));
        window.addEventListener('hashchange', flushVisible, { passive: true });
        window.addEventListener('pageshow', flushVisible, { passive: true });
    }

    function primeLazyVideo(video) {
        if (video.dataset.bwcVideoLoaded === '1') return;
        const src = video.getAttribute('data-src');
        if (!src) return;
        video.src = resolveHref(src);
        video.dataset.bwcVideoLoaded = '1';
        video.preload = 'metadata';
        const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (reduceMotion) {
            video.removeAttribute('autoplay');
            video.controls = true;
        }
        if (typeof video.load === 'function') {
            video.load();
        }
    }

    function warmupLazyVideoMetadata({ limit = 3, timeoutMs = 3500 } = {}) {
        const videos = Array.from(document.querySelectorAll('video[data-src]')).slice(0, limit);
        if (!videos.length) return Promise.resolve(true);

        videos.forEach((video) => primeLazyVideo(video));

        const waits = videos.map(
            (video) =>
                new Promise((resolve) => {
                    if (video.readyState >= 1) {
                        resolve(true);
                        return;
                    }
                    const done = () => resolve(true);
                    video.addEventListener('loadedmetadata', done, { once: true });
                    video.addEventListener('error', done, { once: true });
                })
        );

        const timeout = new Promise((resolve) => window.setTimeout(() => resolve(true), timeoutMs));
        return Promise.race([Promise.all(waits).then(() => true), timeout]);
    }

    function loadLazyVideo(video, { play = true } = {}) {
        primeLazyVideo(video);
        if (play) syncLazyVideoPlayback(video, true);
    }

    function syncLazyVideoPlayback(video, inView) {
        if (video.dataset.bwcVideoLoaded !== '1') return;
        const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (reduceMotion) return;
        if (inView) {
            const playPromise = video.play();
            if (playPromise && typeof playPromise.catch === 'function') {
                playPromise.catch(() => {});
            }
        } else {
            video.pause();
        }
    }

    function initLazyVideos() {
        const videos = document.querySelectorAll('video[data-src]');
        if (!videos.length) return;
        if (!('IntersectionObserver' in window)) {
            videos.forEach(loadLazyVideo);
            return;
        }
        const marginPx = 120;
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    const video = entry.target;
                    if (!entry.isIntersecting || entry.intersectionRatio < 0.2) {
                        syncLazyVideoPlayback(video, false);
                        return;
                    }
                    if (document.documentElement.classList.contains('is-scroll-active')) return;
                    loadLazyVideo(video, { play: true });
                });
            },
            { rootMargin: `${marginPx}px 0px`, threshold: [0, 0.2, 0.45] }
        );
        videos.forEach((video) => observer.observe(video));
    }

    function deferWhenVisible(target, fn, rootMargin = '100% 0px') {
        const el = typeof target === 'string' ? document.querySelector(target) : target;
        if (!el || el.dataset.bwcDeferred === '1') return;
        const run = () => {
            if (el.dataset.bwcDeferred === '1') return;
            el.dataset.bwcDeferred = '1';
            fn();
        };
        if (!('IntersectionObserver' in window)) {
            run();
            return;
        }
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries.some((entry) => entry.isIntersecting)) {
                    run();
                    observer.disconnect();
                }
            },
            { rootMargin }
        );
        observer.observe(el);
    }

    function runWhenIdle(fn, timeoutMs = 1800) {
        if ('requestIdleCallback' in window) {
            requestIdleCallback(() => fn(), { timeout: timeoutMs });
        } else {
            setTimeout(fn, 120);
        }
    }

    let deskTimelinePromise = null;

    function getDeskTimeline() {
        if (!deskTimelinePromise) {
            deskTimelinePromise = fetch(asset('./data/desk-timeline.json'))
                .then((res) => (res.ok ? res.json() : null))
                .catch(() => null);
        }
        return deskTimelinePromise;
    }

    const METRIC_GROUP_LABELS = {
        RISK_ADJ: 'Risk-adjusted',
        TRADES: 'Trade statistics',
        CAPITAL: 'Capital',
        RETURNS: 'Returns',
        RISK: 'Risk',
        INCOME: 'Income',
        ACTIVITY: 'Activity',
    };

    const MARQUEE_GROUP_ORDER = ['RISK_ADJ', 'TRADES', 'CAPITAL', 'RETURNS', 'RISK', 'INCOME', 'ACTIVITY'];

    const EXCEL_MARQUEE_FALLBACK = [
        { key: 'sharpe', label: 'Sharpe Ratio', value: '-2.111', group: 'RISK_ADJ', title: 'Memo §3: static Sharpe penalizes crisis-hedge volatility the same as crash volatility' },
        { key: 'sortino', label: 'Sortino Ratio', value: '-4.156', group: 'RISK_ADJ' },
        { key: 'calmar', label: 'Calmar Ratio', value: '-0.645', group: 'RISK_ADJ' },
        { key: 'omega', label: 'Omega Ratio', value: '0.166', group: 'RISK_ADJ' },
        { key: 'information_ratio', label: 'Vs benchmark (info ratio)', value: '-2.000', group: 'RISK_ADJ', title: 'How consistently we beat or lagged SPY per unit of tracking error' },
        { key: 'treynor', label: 'Treynor', value: '-0.138', group: 'RISK_ADJ' },
        { key: 'm2', label: 'M2 (Modigliani)', value: '-0.274', group: 'RISK_ADJ', title: 'Risk-adjusted return scaled to match benchmark volatility' },
        { key: 'jensen_alpha', label: 'Alpha vs CAPM', value: '-0.000443', group: 'RISK_ADJ', title: 'Excess return vs CAPM expectation given our beta' },
        { key: 'beta', label: 'Beta (close)', value: '0.628', group: 'RISK_ADJ', title: 'End-of-simulation snapshot. Filed memo targeted ~1.0 average portfolio beta' },
        { key: 'profit_factor', label: 'Profit Factor', value: '0.166', group: 'TRADES' },
        { key: 'win_rate', label: 'Win Rate', value: '28.57%', group: 'TRADES' },
        { key: 'avg_win', label: 'Avg Win ($)', value: '$3,176.75', group: 'TRADES' },
        { key: 'avg_loss', label: 'Avg Loss ($)', value: '-$7,653.18', group: 'TRADES' },
        { key: 'expectancy', label: 'Expectancy ($)', value: '-$4,558.91', group: 'TRADES' },
        { key: 'initial_capital', label: 'Initial Capital', value: '$1,000,000.00', group: 'CAPITAL' },
        { key: 'final_value', label: 'Final Portfolio Value', value: '$956,279.80', group: 'CAPITAL' },
        { key: 'cash', label: 'Cash Balance', value: '$1,221.28', group: 'CAPITAL' },
        { key: 'loan', label: 'Loan Balance', value: '$0.00', group: 'CAPITAL' },
        { key: 'market_long', label: 'Market value long', value: '$955,867.54', group: 'CAPITAL' },
        { key: 'market_short', label: 'Market value short', value: '$0.00', group: 'CAPITAL' },
        { key: 'buying_power', label: 'Buying Power', value: '$958,310.10', group: 'CAPITAL' },
        { key: 'total_return', label: 'Portfolio Total Return', value: '-4.37%', group: 'RETURNS' },
        { key: 'annualized_return', label: 'Annualized return (68-day)', value: '-23.5%', group: 'RETURNS', title: 'TWR^(365/68)−1 on a 68-day window. Context only, not investable' },
        { key: 'benchmark_return', label: 'Benchmark Return (S&P 500)', value: '-2.29%', group: 'RETURNS' },
        { key: 'excess_return', label: 'Excess Return vs Benchmark', value: '-2.08%', group: 'RETURNS' },
        { key: 'pnl', label: 'P&L Dollar Amount', value: '($43,720.20)', group: 'RETURNS' },
        { key: 'dividends', label: 'Total Dividends Received', value: '$2,043.95', group: 'INCOME' },
        { key: 'commissions', label: 'Total Commissions Paid', value: '$680.00', group: 'INCOME' },
    ];

    const MARQUEE_HIGHLIGHT_KEYS = new Set([
        'sharpe',
        'profit_factor',
        'expectancy',
        'final_value',
        'total_return',
        'excess_return',
        'pnl',
        'annualized_return',
    ]);

    function renderMetricCard(item, highlightKeys) {
        const group = METRIC_GROUP_LABELS[item.group] || item.group;
        const highlight = highlightKeys.has(item.key) ? ' is-highlight' : '';
        const title = item.title ? ` title="${item.title.replace(/"/g, '&quot;')}"` : '';
        const idAttr = item.key === 'annualized_return' ? ' id="kpi-desk-ann-return"' : '';
        return `<article class="excel-metric-card${highlight}"${title}>
            <span class="excel-metric-group text-mono">${group}</span>
            <span class="excel-metric-label text-mono">${item.label}</span>
            <span class="excel-metric-value text-display"${idAttr}>${item.value}</span>
        </article>`;
    }

    function orderMarqueeItems(items) {
        const byGroup = {};
        for (const item of items || []) {
            if (!byGroup[item.group]) byGroup[item.group] = [];
            byGroup[item.group].push(item);
        }
        const ordered = [];
        for (const group of MARQUEE_GROUP_ORDER) {
            if (byGroup[group]?.length) ordered.push(...byGroup[group]);
        }
        return ordered;
    }

    function splitMarqueeLanes(items, laneCount = 2) {
        const mid = Math.ceil(items.length / laneCount);
        return [items.slice(0, mid), items.slice(mid)];
    }

    function renderLaneCards(items, highlightKeys) {
        const cards = items.map((item) => renderMetricCard(item, highlightKeys)).join('');
        return `
            <div class="excel-marquee-lane__set">${cards}</div>
            <div class="excel-marquee-lane__set" aria-hidden="true">${cards}</div>`;
    }

    function renderMetricsMarquee(container, items, highlightKeys) {
        const lanesEl = container?.querySelector('.excel-marquee-lanes');
        if (!lanesEl || !items?.length) return;
        const ordered = orderMarqueeItems(items);
        const [rowA, rowB] = splitMarqueeLanes(ordered, 2);
        lanesEl.innerHTML = `
            <div class="excel-marquee-lane">
                <div class="excel-marquee-lane__track">${renderLaneCards(rowA, highlightKeys)}</div>
            </div>
            <div class="excel-marquee-lane excel-marquee-lane--reverse">
                <div class="excel-marquee-lane__track">${renderLaneCards(rowB, highlightKeys)}</div>
            </div>`;
    }

    function hydrateExcelMetricsFromData(data) {
        const prov = document.getElementById('excel-metrics-provenance');
        if (prov && data?.trading_start && data?.trading_end) {
            prov.textContent = `Hult simulation desk freeze (Excel sheet005 + sheet011 + sheet013). Trading window: ${data.trading_start} to ${data.trading_end}.`;
        }
        const annItem = (data?.grid || []).find((g) => g.key === 'annualized_return');
        if (annItem) {
            setOverlayCell('kpi-desk-ann-return', annItem.value);
            setOverlayCell('outcome-desk-ann-return', annItem.value);
        }
    }

    function marqueeItemsFromExcelData(data) {
        let items = EXCEL_MARQUEE_FALLBACK;
        if (data) {
            const fromJson = [...(data.advanced_grid || []), ...(data.grid || [])];
            if (fromJson.length > 1) items = fromJson;
        }
        return items;
    }

    function renderMetricsMarqueeFromCache() {
        const marquee = document.getElementById('excel-metrics-marquee');
        if (!marquee || marquee.dataset.bwcMarqueeRendered === '1') return;
        marquee.dataset.bwcMarqueeRendered = '1';
        renderMetricsMarquee(
            marquee,
            marqueeItemsFromExcelData(cachedExcelMetrics),
            MARQUEE_HIGHLIGHT_KEYS
        );
    }

    function initDeferredMarquee() {
        const marquee = document.getElementById('excel-metrics-marquee');
        if (!marquee) return;

        const render = () => runWhenIdle(renderMetricsMarqueeFromCache, 120);

        if (isElementInViewport(marquee, 320)) {
            render();
            return;
        }
        deferWhenVisible(marquee, render, '120% 0px');
    }

    function initFooterYear() {
        const el = document.getElementById('footer-year');
        if (el) el.textContent = String(new Date().getFullYear());
    }

    async function initFooterCommitLog() {
        const list = document.getElementById('footer-commit-log');
        if (!list) return;
        try {
            const res = await fetch(asset('./data/commit-log.json'));
            if (!res.ok) throw new Error('fetch failed');
            const data = await res.json();
            const commits = Array.isArray(data?.commits) ? data.commits.slice(0, 24) : [];
            if (!commits.length) return;
            list.innerHTML = commits
                .map((row) => {
                    const hash = row.hash || '';
                    const date = row.date || '';
                    const subject = row.subject || '';
                    const href = `${data.repository || 'https://github.com/Kartavya-Jharwal/ganet-project-bwc'}/commit/${hash}`;
                    return `<li><a href="${href}" rel="noopener noreferrer">${date} ${hash}</a> ${subject}</li>`;
                })
                .join('');
        } catch (_) {
            list.innerHTML = '<li><a href="https://github.com/Kartavya-Jharwal/ganet-project-bwc/commits/main" rel="noopener noreferrer">View commit history on GitHub</a></li>';
        }
    }

    const SPLASH_STORAGE_KEY = 'bwc-splash-dismissed';
    const SPLASH_REFRESH_COUNT_KEY = 'bwc-splash-refresh-count';
    const SPLASH_EXIT_MS = 600;
    const THREE_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';

    let splashWaveformFrameId = 0;
    let splashWaveformTeardown = null;
    let splashLiquidTeardown = null;
    let splashFocalResizeHandler = null;
    let splashFocalObserver = null;
    let splashWaveformFocalUpdate = null;
    const externalScriptPromises = new Map();

    const SPLASH_FOCAL_X = 0.5;
    const SPLASH_FOCAL_Y = 0.5;

    function readSplashFocal(splash, width, height) {
        const w = width || splash?.clientWidth || 0;
        const h = height || splash?.clientHeight || 0;
        return {
            cx: w * SPLASH_FOCAL_X,
            cy: h * SPLASH_FOCAL_Y,
            nx: SPLASH_FOCAL_X,
            ny: SPLASH_FOCAL_Y,
        };
    }

    function syncSplashFocal(splash) {
        if (!splash) return;
        const width = splash.clientWidth;
        const height = splash.clientHeight;
        if (!width || !height) return;
        const focal = readSplashFocal(splash, width, height);
        if (typeof splashWaveformFocalUpdate === 'function') {
            splashWaveformFocalUpdate(focal);
        }
        if (window.BWC?.SplashLiquidGradient?.setFocal) {
            window.BWC.SplashLiquidGradient.setFocal(focal.nx, 1 - focal.ny);
        }
    }

    function loadExternalScript(url) {
        if (externalScriptPromises.has(url)) {
            return externalScriptPromises.get(url);
        }
        const promise = new Promise((resolve, reject) => {
            const existing = document.querySelector(`script[data-bwc-src="${url}"]`);
            if (existing) {
                if (existing.dataset.bwcLoaded === '1') {
                    resolve();
                    return;
                }
                existing.addEventListener('load', () => resolve(), { once: true });
                existing.addEventListener('error', () => reject(new Error(url)), { once: true });
                return;
            }
            const script = document.createElement('script');
            script.src = url;
            script.async = true;
            script.dataset.bwcSrc = url;
            script.onload = () => {
                script.dataset.bwcLoaded = '1';
                resolve();
            };
            script.onerror = () => reject(new Error(url));
            document.head.appendChild(script);
        });
        externalScriptPromises.set(url, promise);
        return promise;
    }

    function stopSplashLiquidGradient() {
        if (typeof splashLiquidTeardown === 'function') {
            splashLiquidTeardown();
            splashLiquidTeardown = null;
        } else if (window.BWC?.SplashLiquidGradient) {
            window.BWC.SplashLiquidGradient.destroy();
        }
    }

    async function initSplashLiquidGradient(splash) {
        const host = splash?.querySelector('.site-splash__liquid');
        if (!host) return;
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        try {
            if (!window.THREE) {
                await loadExternalScript(THREE_CDN);
            }
            if (!window.BWC?.SplashLiquidGradient) {
                await loadExternalScript(asset('./js/splash-liquid-gradient.min.js'));
            }
            const instance = window.BWC.SplashLiquidGradient.init(host);
            if (!instance) return;
            splash.classList.add('site-splash--liquid');
            splashLiquidTeardown = () => window.BWC.SplashLiquidGradient.destroy();
            syncSplashFocal(splash);
            requestAnimationFrame(() => syncSplashFocal(splash));
        } catch (_) {
            /* CSS gradient fallback */
        }
    }

    async function runSiteBootstrap(onProgress) {
        let completed = 0;
        const total = 7;

        const reportProgress = () => {
            if (typeof onProgress !== 'function') return;
            const pct = Math.min(100, Math.round((completed / total) * 100));
            onProgress(pct);
        };

        const track = (promise) =>
            Promise.resolve(promise).then((value) => {
                completed += 1;
                reportProgress();
                return value;
            });

        reportProgress();

        try {
            const [timeline, results, full, excel] = await Promise.all([
                track(preloadJson('./data/desk-timeline.json')),
                track(preloadJson('./data/results.json')),
                track(preloadJson('./data/full-metrics.json')),
                track(preloadJson('./data/excel-metrics.json')),
                track(waitForFonts()),
                track(waitForPriorityCharts()),
                track(warmupLazyVideoMetadata()),
            ]);

            deskTimelinePromise = Promise.resolve(timeline);
            cachedExcelMetrics = excel;
            hydrateFromBootstrapData(full, results);
            hydrateExcelMetricsFromData(excel);
        } catch (_) {
            showMetricsEmptyNote(true);
        }

        completed = total;
        reportProgress();
        return true;
    }

    function updateSplashCtaProgress(enterBtn, pct) {
        if (!enterBtn || enterBtn.classList.contains('site-splash__cta--ready')) return;
        const clamped = Math.max(0, Math.min(100, Math.round(pct)));
        enterBtn.style.setProperty('--splash-cta-progress', `${clamped}%`);
        const label = enterBtn.querySelector('.site-splash__cta-label');
        if (label) {
            label.textContent = `Loading data\u2026 (${clamped}%)`;
        }
    }

    function markSplashEnterReady(enterBtn) {
        if (!enterBtn || enterBtn.classList.contains('site-splash__cta--ready')) return;
        enterBtn.style.setProperty('--splash-cta-progress', '100%');
        const label = enterBtn.querySelector('.site-splash__cta-label');
        if (label) {
            label.textContent = 'Enter microsite';
        }
        enterBtn.classList.add('site-splash__cta--ready');
        enterBtn.disabled = false;
        enterBtn.removeAttribute('aria-busy');
        if (typeof enterBtn.focus === 'function') {
            enterBtn.focus({ preventScroll: true });
        }
    }

    function stopSplashWaveform() {
        if (splashWaveformFrameId) {
            cancelAnimationFrame(splashWaveformFrameId);
            splashWaveformFrameId = 0;
        }
        if (typeof splashWaveformTeardown === 'function') {
            splashWaveformTeardown();
            splashWaveformTeardown = null;
        }
    }

    function initSplashWaveform(splash) {
        const canvas = splash?.querySelector('.site-splash__waveform');
        if (!canvas) return;

        const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (reduceMotion) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let width = 0;
        let height = 0;
        let timeline = 0;
        let focalCx = 0;
        let focalCy = 0;

        splashWaveformFocalUpdate = ({ cx, cy }) => {
            focalCx = cx;
            focalCy = cy;
        };

        const bootFocal = readSplashFocal(splash, splash.clientWidth, splash.clientHeight);
        focalCx = bootFocal.cx;
        focalCy = bootFocal.cy;

        const waveColors = ['191, 176, 248', '199, 16, 204', '109, 28, 242'];
        const accentRgb = '167, 139, 250';
        const accentHex = '#a78bfa';
        const waveCount = 9;
        const matrixWaves = Array.from({ length: waveCount }, (_, idx) => ({
            speed: 0.01 + Math.random() * 0.055,
            amp: 45 + Math.random() * 65,
            offset: Math.random() * Math.PI * 2,
            volatility: 0.1 + Math.random() * 0.45,
            driftPhase: Math.random() * Math.PI * 2,
            driftSpeed: 0.003 + Math.random() * 0.015,
            lineW: 1 + Math.random() * 1.2,
            colorIdx: idx % waveColors.length,
        }));

        let travelingPulses = [];

        function handleResize() {
            if (!canvas.parentElement) return;
            width = canvas.parentElement.clientWidth;
            height = canvas.parentElement.clientHeight;
            canvas.width = width;
            canvas.height = height;
            const focal = readSplashFocal(splash, width, height);
            focalCx = focal.cx;
            focalCy = focal.cy;
            syncSplashFocal(splash);
        }

        function drawFluidBase() {
            if (splash.classList.contains('site-splash--liquid')) return;

            const t = timeline * 0.0065;
            const cxBase = focalCx;
            const cyBase = focalCy;

            const blobs = [
                {
                    x: cxBase + Math.sin(t) * width * 0.11,
                    y: cyBase + Math.cos(t * 0.73) * height * 0.07,
                    r: Math.max(width, height) * (0.34 + Math.sin(t * 0.4) * 0.04),
                    inner: 'rgba(109, 28, 242, 0.07)',
                },
                {
                    x: cxBase + Math.cos(t * 0.58 + 1.2) * width * 0.14,
                    y: cyBase + Math.sin(t * 0.51 + 0.8) * height * 0.09,
                    r: Math.max(width, height) * (0.28 + Math.cos(t * 0.33) * 0.03),
                    inner: 'rgba(191, 176, 248, 0.06)',
                },
                {
                    x: cxBase + Math.sin(t * 0.37 + 2.1) * width * 0.08,
                    y: cyBase + Math.cos(t * 0.62 + 1.6) * height * 0.05,
                    r: Math.max(width, height) * 0.22,
                    inner: 'rgba(167, 139, 250, 0.05)',
                },
            ];

            blobs.forEach((blob) => {
                const gradient = ctx.createRadialGradient(blob.x, blob.y, 0, blob.x, blob.y, blob.r);
                gradient.addColorStop(0, blob.inner);
                gradient.addColorStop(0.55, 'rgba(10, 0, 26, 0.02)');
                gradient.addColorStop(1, 'transparent');
                ctx.fillStyle = gradient;
                ctx.fillRect(0, 0, width, height);
            });
        }

        function renderEngineLoop() {
            if (!canvas.parentElement || !width || !height || focalCy <= 0) {
                splashWaveformFrameId = requestAnimationFrame(renderEngineLoop);
                return;
            }
            ctx.clearRect(0, 0, width, height);

            timeline += 1.5;
            drawFluidBase();

            const cy = focalCy;
            const cx = focalCx;

            const glowRadius = Math.max(width, height) * 0.62;
            const focalGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, glowRadius);
            focalGlow.addColorStop(0, 'rgba(167, 139, 250, 0.11)');
            focalGlow.addColorStop(0.22, 'rgba(109, 28, 242, 0.06)');
            focalGlow.addColorStop(0.55, 'rgba(109, 28, 242, 0.025)');
            focalGlow.addColorStop(1, 'transparent');
            ctx.fillStyle = focalGlow;
            ctx.fillRect(0, 0, width, height);

            ctx.save();
            ctx.translate(cx, cy);
            ctx.scale(1.75, 0.9);
            ctx.translate(-cx, -cy);
            const sideGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, width * 0.55);
            sideGlow.addColorStop(0, 'rgba(191, 176, 248, 0.04)');
            sideGlow.addColorStop(0.45, 'rgba(109, 28, 242, 0.02)');
            sideGlow.addColorStop(1, 'transparent');
            ctx.fillStyle = sideGlow;
            ctx.fillRect(0, 0, width, height);
            ctx.restore();

            matrixWaves.forEach((wave, idx) => {
                ctx.beginPath();
                ctx.lineWidth = wave.lineW + 0.25;
                const colorAlpha = 0.4 + Math.sin(timeline * 0.05 + idx) * 0.14;
                ctx.strokeStyle = `rgba(${waveColors[wave.colorIdx]}, ${colorAlpha})`;

                wave.driftPhase += wave.driftSpeed;
                const ampWobble = 1 + Math.sin(wave.driftPhase) * wave.volatility;

                for (let x = 0; x <= cx; x += 3) {
                    const horizontalProgress = x / Math.max(cx, 1);
                    const dampening = 1 - horizontalProgress ** 4;
                    const cyclicSine = Math.sin(x * wave.speed - timeline * wave.speed + wave.offset) * wave.amp * ampWobble;
                    const yPosition = cy + cyclicSine * dampening;

                    if (x === 0) ctx.moveTo(x, yPosition);
                    else ctx.lineTo(x, yPosition);
                }
                ctx.lineTo(cx, cy);
                ctx.stroke();
            });

            ctx.beginPath();
            ctx.lineWidth = 1.75;
            ctx.strokeStyle = `rgba(${accentRgb}, 0.78)`;
            ctx.moveTo(cx, cy);
            ctx.lineTo(width, cy);
            ctx.stroke();

            ctx.save();
            ctx.shadowColor = 'rgba(167, 139, 250, 0.55)';
            ctx.shadowBlur = 10;
            ctx.beginPath();
            ctx.strokeStyle = accentHex;
            ctx.fillStyle = '#ffffff';
            ctx.lineWidth = 3.5;
            ctx.arc(cx, cy, 5, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            ctx.restore();

            if (Math.random() < 0.02) {
                travelingPulses.push({ x: cx, alive: true });
            }

            travelingPulses.forEach((pulse, index) => {
                if (!pulse.alive) return;
                pulse.x += 8.5;

                if (pulse.x > cx) {
                    ctx.beginPath();
                    ctx.strokeStyle = accentHex;
                    ctx.lineWidth = 3;

                    const envelopeBounds = 40;
                    for (let px = pulse.x - envelopeBounds; px < pulse.x + envelopeBounds; px += 2) {
                        if (px < cx || px > width) continue;
                        const normalizedDist = (px - pulse.x) / (envelopeBounds / 2.5);
                        const highFreqSpike = -58 * Math.exp(-(normalizedDist * normalizedDist));

                        if (px === Math.max(cx, pulse.x - envelopeBounds)) ctx.moveTo(px, cy);
                        ctx.lineTo(px, cy + highFreqSpike);
                    }
                    ctx.stroke();

                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(${accentRgb}, 0.3)`;
                    ctx.moveTo(pulse.x, cy);
                        ctx.lineTo(pulse.x, cy + 38);
                    ctx.stroke();
                }

                if (pulse.x > width) {
                    pulse.alive = false;
                    travelingPulses.splice(index, 1);
                }
            });

            splashWaveformFrameId = requestAnimationFrame(renderEngineLoop);
        }

        window.addEventListener('resize', handleResize);
        handleResize();
        splashWaveformTeardown = () => {
            window.removeEventListener('resize', handleResize);
            splashWaveformFocalUpdate = null;
        };
        handleResize();
        renderEngineLoop();
    }

    function bindSplashFocalSync(splash) {
        if (!splash || splashFocalResizeHandler) return;
        splashFocalResizeHandler = () => syncSplashFocal(splash);
        window.addEventListener('resize', splashFocalResizeHandler, { passive: true });
        if ('ResizeObserver' in window) {
            splashFocalObserver = new ResizeObserver(splashFocalResizeHandler);
            splashFocalObserver.observe(splash);
        }
        requestAnimationFrame(() => {
            requestAnimationFrame(() => syncSplashFocal(splash));
        });
    }

    function unbindSplashFocalSync() {
        if (splashFocalResizeHandler) {
            window.removeEventListener('resize', splashFocalResizeHandler);
            splashFocalResizeHandler = null;
        }
        if (splashFocalObserver) {
            splashFocalObserver.disconnect();
            splashFocalObserver = null;
        }
    }

    function focusMainLandmark() {
        const main = document.getElementById('main-content');
        if (!main || typeof main.focus !== 'function') return;
        if (!main.hasAttribute('tabindex')) {
            main.setAttribute('tabindex', '-1');
        }
        main.focus({ preventScroll: true });
    }

    function dismissSplash(splash, { focusMain = false } = {}) {
        if (!splash) return;
        stopSplashWaveform();
        stopSplashLiquidGradient();
        unbindSplashFocalSync();
        splash.classList.add('site-splash--out');
        splash.setAttribute('aria-hidden', 'true');
        try {
            sessionStorage.setItem(SPLASH_STORAGE_KEY, '1');
            sessionStorage.setItem(SPLASH_REFRESH_COUNT_KEY, '0');
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
            if (focusMain) {
                focusMainLandmark();
            }
        }, SPLASH_EXIT_MS);
    }

    function initSplash(bootstrapPromise) {
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
            document.body.classList.remove('splash-active', 'splash-dismissed');
            try {
                splash.remove();
            } catch (_) {
                /* ignore */
            }
            return;
        }

        document.body.classList.add('splash-active');
        splash.removeAttribute('aria-hidden');
        bindSplashFocalSync(splash);
        initSplashWaveform(splash);
        initSplashLiquidGradient(splash);

        let splashEnterReady = false;

        if (enterBtn) {
            if (bootstrapPromise && typeof bootstrapPromise.then === 'function') {
                bootstrapPromise
                    .then(() => {
                        markSplashEnterReady(enterBtn);
                        splashEnterReady = true;
                    })
                    .catch(() => {
                        markSplashEnterReady(enterBtn);
                        splashEnterReady = true;
                    });
            } else {
                markSplashEnterReady(enterBtn);
                splashEnterReady = true;
            }
        } else {
            splashEnterReady = true;
        }

        function onEnter({ focusMain = false, force = false } = {}) {
            if (!splashEnterReady && !force) return;
            dismissSplash(splash, { focusMain });
        }

        enterBtn?.addEventListener('click', () => onEnter());

        document.addEventListener('keydown', (e) => {
            if (splash.classList.contains('site-splash--out')) return;
            if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
                if (e.target === enterBtn || !/input|textarea|select/i.test(e.target?.tagName || '')) {
                    if (!splashEnterReady) return;
                    e.preventDefault();
                    onEnter();
                }
            }
        });

        splash.querySelector('.site-splash__skip')?.addEventListener('click', () => {
            requestAnimationFrame(() => onEnter({ focusMain: true, force: true }));
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
        if (Number.isNaN(num)) return 'n/a';
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

        // Outro: one horizontal row (17 → 18 → 19), same pipe logic as milestone rows
        parts.push(`
            <div class="snake-row snake-row--ltr snake-row--outro" role="list" data-snake-row="outro" style="--row-items: ${cols}">
                <div class="snake-row__cells">
                    <article class="snake-milestone snake-milestone--outro" role="listitem">
                        <header class="snake-milestone__meta">
                            <span class="snake-milestone__id text-mono">17</span>
                            <time class="snake-milestone__date text-mono" datetime="2026-04-28">Apr 28, 2026</time>
                        </header>
                        <h3 class="snake-milestone__title text-display">Post‑mortem + client report presentation</h3>
                        <div class="snake-milestone__badges">
                            <span class="snake-phase-badge text-mono">Sunset path</span>
                        </div>
                        <div class="snake-milestone__metrics-row">
                            <span class="snake-metric-pill"><span class="snake-metric-pill__label text-mono">Deliverable</span><span class="snake-metric-pill__value text-mono is-neutral">DECK</span></span>
                        </div>
                    </article>
                    <article class="snake-milestone snake-milestone--sunset" role="listitem">
                        <header class="snake-milestone__meta">
                            <span class="snake-milestone__id text-mono">18</span>
                            <time class="snake-milestone__date text-mono" datetime="2026-05-01">May 1, 2026</time>
                        </header>
                        <h3 class="snake-milestone__title text-display">Model + archive sunset seal</h3>
                        <div class="snake-milestone__badges">
                            <span class="snake-phase-badge text-mono">Static publication</span>
                        </div>
                        <div class="snake-milestone__metrics-row">
                            <span class="snake-metric-pill"><span class="snake-metric-pill__label text-mono">Mode</span><span class="snake-metric-pill__value text-mono is-neutral">READ‑ONLY</span></span>
                        </div>
                    </article>
                    <article class="snake-milestone snake-milestone--grades" role="listitem">
                        <header class="snake-milestone__meta">
                            <span class="snake-milestone__id text-mono">19</span>
                            <time class="snake-milestone__date text-mono" datetime="2026-05-19">May 19, 2026</time>
                        </header>
                        <h3 class="snake-milestone__title text-display">Grades + IC audit released</h3>
                        <div class="snake-milestone__badges">
                            <span class="snake-phase-badge text-mono">Committee close</span>
                        </div>
                        <div class="snake-milestone__metrics-row">
                            <span class="snake-metric-pill"><span class="snake-metric-pill__label text-mono">Status</span><span class="snake-metric-pill__value text-mono is-neutral">FINAL</span></span>
                        </div>
                    </article>
                    <div class="snake-spacer" aria-hidden="true"></div>
                </div>
            </div>`);

        return `<div class="desk-timeline-snake__inner"><div class="snake-grid-backdrop" aria-hidden="true"></div>${buildSnakeStrokeSvg()}${parts.join('')}</div>`;
    }

    function snakeCardCenter(el, innerRect) {
        const r = el.getBoundingClientRect();
        return {
            x: r.left - innerRect.left + r.width / 2,
            y: r.top - innerRect.top + r.height / 2,
        };
    }

    function snakeGapElbowY(band, nextBand) {
        const gapTop = band.yBottom;
        const gapBottom = nextBand.yTop;
        const gap = gapBottom - gapTop;
        if (!Number.isFinite(gap) || gap <= 2) {
            return (band.end.y + nextBand.start.y) / 2;
        }
        const minLeg = Math.max(12, gap * 0.2);
        if (gap <= minLeg * 2) return gapTop + gap / 2;
        const elbow = gapTop + gap * 0.5;
        return Math.min(Math.max(elbow, gapTop + minLeg), gapBottom - minLeg);
    }

    function bindSnakeStrokeRepaint(root, paintStroke) {
        if (root.dataset.snakeStrokeBound === '1') return;
        root.dataset.snakeStrokeBound = '1';

        let t = null;
        const queue = () => {
            if (t) window.clearTimeout(t);
            t = window.setTimeout(() => requestAnimationFrame(paintStroke), 48);
        };

        window.addEventListener('resize', queue, { passive: true });

        const inner = root.querySelector('.desk-timeline-snake__inner');
        if (inner && typeof ResizeObserver !== 'undefined') {
            const ro = new ResizeObserver(queue);
            ro.observe(inner);
        }

        if (document.fonts?.ready) {
            document.fonts.ready.then(queue).catch(() => {});
        }
    }

    // Single continuous stroke: measure row bands only (intro → grid rows → outro).
    function renderSnakeStroke(root) {
        const inner = root?.querySelector('.desk-timeline-snake__inner');
        const svg = inner?.querySelector('svg.snake-stroke');
        const path = svg?.querySelector('path.snake-stroke__path');
        if (!inner || !svg || !path) return;

        const innerRect = inner.getBoundingClientRect();
        const W = Math.max(1, innerRect.width);
        const H = Math.max(1, innerRect.height);

        const gridRows = Array.from(inner.querySelectorAll('.snake-row[data-snake-row]'))
            .filter((row) => /^\d+$/.test(String(row.dataset.snakeRow)) || row.dataset.snakeRow === 'outro')
            .sort((a, b) => {
                const key = (row) => (row.dataset.snakeRow === 'outro' ? 9999 : Number(row.dataset.snakeRow));
                return key(a) - key(b);
            });

        const rowBands = gridRows
            .map((row) => {
                const rowCells = row.querySelector('.snake-row__cells');
                const cards = rowCells ? Array.from(rowCells.querySelectorAll('.snake-milestone')) : [];
                if (!rowCells || !cards.length) return null;

                const cellsRect = rowCells.getBoundingClientRect();
                const firstCard = cards[0];
                const lastCard = cards[cards.length - 1];
                const startPt = snakeCardCenter(firstCard, innerRect);
                const endPt = snakeCardCenter(lastCard, innerRect);

                return {
                    start: { x: startPt.x, y: startPt.y },
                    end: { x: endPt.x, y: endPt.y },
                    yTop: cellsRect.top - innerRect.top,
                    yBottom: cellsRect.bottom - innerRect.top,
                };
            })
            .filter(Boolean);

        if (!rowBands.length) return;

        const introCard = inner.querySelector('.snake-row--intro .snake-milestone');
        const introPt = introCard ? snakeCardCenter(introCard, innerRect) : null;

        let d = '';
        if (introPt) {
            d += `M ${introPt.x.toFixed(2)} ${introPt.y.toFixed(2)} V ${rowBands[0].start.y.toFixed(2)}`;
        } else {
            d += `M ${rowBands[0].start.x.toFixed(2)} ${rowBands[0].start.y.toFixed(2)}`;
        }

        for (let i = 0; i < rowBands.length; i += 1) {
            const band = rowBands[i];
            if (!introPt && i === 0) {
                /* already at start */
            } else if (i > 0) {
                d += ` V ${band.start.y.toFixed(2)}`;
            }
            d += ` H ${band.end.x.toFixed(2)}`;
            if (i === rowBands.length - 1) break;
            const nextBand = rowBands[i + 1];
            const yTurn = snakeGapElbowY(band, nextBand);
            d += ` V ${yTurn.toFixed(2)} H ${nextBand.start.x.toFixed(2)}`;
        }

        svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
        svg.setAttribute('preserveAspectRatio', 'none');
        path.setAttribute('d', d);
    }

    function applyTroughMetrics(data) {
        const slots = document.querySelectorAll('[data-metric]');
        if (!slots.length || !data) return;
        const troughDate = data.annotations?.trough?.date;
        const ms = (data.milestones || []).find((m) => m.date === troughDate);
        const deskPct = ms?.portfolio_return_pct ?? data.annotations?.trough?.max_drawdown_pct;
        const spyPct = ms?.spy_return_pct ?? data.annotations?.trough?.spy_return_pct;
        if (deskPct == null || spyPct == null) return;

        const deskStr = formatDeskPct(deskPct);
        const spyStr = formatDeskPct(spyPct);
        const excessPp = `${deskPct - spyPct >= 0 ? '+' : ''}${(deskPct - spyPct).toFixed(2)}pp`;

        document.querySelectorAll('[data-metric="trough-desk"]').forEach((el) => {
            el.textContent = deskStr;
        });
        document.querySelectorAll('[data-metric="trough-spy"]').forEach((el) => {
            el.textContent = spyStr;
        });
        document.querySelectorAll('[data-metric="trough-excess"]').forEach((el) => {
            el.textContent = excessPp;
        });
    }

    function renderDeskTimelineFromData(data) {
        const root = document.getElementById('desk-timeline');
        if (!root || !data) return;
        const milestones = data.milestones || [];
        const phases = data.phases || [];
        if (!milestones.length) {
            root.innerHTML =
                '<p class="text-mono text-muted">Timeline unavailable. Run build_frontend_assets.</p>';
            return;
        }
        root.innerHTML = buildSnakeTimelineHtml(milestones, phases, 4);
        const paintStroke = () => renderSnakeStroke(root);
        requestAnimationFrame(() => requestAnimationFrame(paintStroke));
        bindSnakeStrokeRepaint(root, paintStroke);
    }

    async function renderDeskTimeline() {
        const root = document.getElementById('desk-timeline');
        if (!root) return;
        try {
            const data = await getDeskTimeline();
            if (!data) throw new Error('desk-timeline.json missing');
            renderDeskTimelineFromData(data);
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

    function initDeferredHydration() {
        const manifestDetails = document.querySelector('.sources-supplement');
        if (manifestDetails) {
            const loadManifest = () => {
                if (manifestDetails.dataset.bwcManifestLoaded === '1') return;
                manifestDetails.dataset.bwcManifestLoaded = '1';
                renderDeliverablesManifest();
            };
            manifestDetails.addEventListener('toggle', () => {
                if (manifestDetails.open) loadManifest();
            });
            deferWhenVisible(manifestDetails, loadManifest);
        }

        deferWhenVisible('#desk-timeline', async () => {
            const data = await getDeskTimeline();
            applyTroughMetrics(data);
            renderDeskTimelineFromData(data);
        }, '150% 0px');

        deferWhenVisible('#desk-behavioural-audit', () => hydrateBehaviouralAudit(), '100% 0px');
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
            { threshold: 0.05, rootMargin: '0px 0px 20% 0px' }
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

    function initMarqueePause() {
        const marquee = document.getElementById('excel-metrics-marquee');
        if (!marquee || !('IntersectionObserver' in window)) return;

        const observer = new IntersectionObserver(
            ([entry]) => {
                marquee.classList.toggle('is-offscreen', !entry.isIntersecting);
            },
            { rootMargin: '120px 0px' }
        );
        observer.observe(marquee);
    }

    function initSiteDock() {
        const dock = document.getElementById('site-nav-dock');
        const sentinel = document.getElementById('nav-reveal-sentinel');
        const toggle = document.getElementById('site-nav-toggle');
        const panel = document.getElementById('site-nav-panel');
        if (!dock) return;

        const mobileMq = window.matchMedia('(max-width: 1023px)');

        function setMenuOpen(open) {
            dock.classList.toggle('is-menu-open', open);
            if (toggle) toggle.setAttribute('aria-expanded', String(open));
            if (panel) panel.toggleAttribute('hidden', !open && mobileMq.matches);
        }

        function closeMenu() {
            setMenuOpen(false);
        }

        function updateDockState() {
            if (mobileMq.matches) {
                dock.classList.remove('is-docked');
                document.body.classList.remove('site-dock-active');
                return;
            }
            const pastIntro = sentinel
                ? sentinel.getBoundingClientRect().top <= 0
                : window.scrollY > 120;
            dock.classList.toggle('is-docked', pastIntro);
            document.body.classList.toggle('site-dock-active', pastIntro);
            if (pastIntro) closeMenu();
        }

        if (panel && mobileMq.matches) {
            panel.setAttribute('hidden', '');
        }

        toggle?.addEventListener('click', () => {
            setMenuOpen(!dock.classList.contains('is-menu-open'));
        });

        panel?.querySelectorAll('.site-dock__link').forEach((link) => {
            link.addEventListener('click', closeMenu);
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && dock.classList.contains('is-menu-open')) {
                closeMenu();
                toggle?.focus();
            }
        });

        mobileMq.addEventListener('change', () => {
            if (!mobileMq.matches) {
                panel?.removeAttribute('hidden');
                closeMenu();
            } else {
                panel?.setAttribute('hidden', '');
            }
            updateDockState();
        });

        let dockTicking = false;

        function requestDockUpdate() {
            if (dockTicking) return;
            dockTicking = true;
            requestAnimationFrame(() => {
                dockTicking = false;
                updateDockState();
            });
        }

        updateDockState();
        window.addEventListener('scroll', requestDockUpdate, { passive: true });
        window.addEventListener('resize', requestDockUpdate, { passive: true });
    }

    function initScrollSpy() {
        const links = document.querySelectorAll('.site-dock__link[data-section]');
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

    function attachCursorToTopLayer(layer) {
        const cursor = document.querySelector('.custom-cursor');
        if (!cursor || !layer) return;
        layer.appendChild(cursor);
    }

    function attachCursorToBody() {
        const cursor = document.querySelector('.custom-cursor');
        if (!cursor) return;
        document.body.appendChild(cursor);
    }

    function initDialogs() {
        const triggers = document.querySelectorAll('[data-dialog-target]');
        if (!triggers.length) return;

        const lazyDialogHydrators = {
            'memo-excerpts-dialog': hydrateMemoExcerpts,
        };

        document.addEventListener('click', (e) => {
            const closeEl = e.target.closest('[data-dialog-close]');
            if (!closeEl) return;
            const dialog = closeEl.closest('dialog');
            if (dialog instanceof HTMLDialogElement) dialog.close();
        });

        triggers.forEach((trigger) => {
            const dialogId = trigger.getAttribute('data-dialog-target');
            if (!dialogId) return;
            const dialog = document.getElementById(dialogId);
            if (!(dialog instanceof HTMLDialogElement)) return;

            const closeBtn = dialog.querySelector('[data-dialog-close]');
            closeBtn?.addEventListener('click', () => dialog.close());

            trigger.addEventListener('click', () => {
                const hydrate = lazyDialogHydrators[dialogId];
                if (hydrate && dialog.dataset.bwcHydrated !== '1') {
                    dialog.dataset.bwcHydrated = '1';
                    hydrate();
                }
                if (typeof dialog.showModal === 'function') dialog.showModal();
                else dialog.setAttribute('open', '');
                attachCursorToTopLayer(dialog);
                closeBtn?.focus();
            });

            dialog.addEventListener('click', (e) => {
                const rect = dialog.getBoundingClientRect();
                const isInDialog =
                    rect.top <= e.clientY &&
                    e.clientY <= rect.bottom &&
                    rect.left <= e.clientX &&
                    e.clientX <= rect.right;
                if (!isInDialog) dialog.close();
            });

            dialog.addEventListener('cancel', (e) => {
                e.preventDefault();
                dialog.close();
            });

            dialog.addEventListener('close', () => {
                attachCursorToBody();
                if (document.activeElement instanceof HTMLElement) {
                    document.activeElement.blur();
                }
                trigger.focus({ preventScroll: true });
            });
        });
    }

    function initVideoPopout() {
        const dialog = document.getElementById('video-popout-dialog');
        const player = document.getElementById('video-popout-player');
        if (!(dialog instanceof HTMLDialogElement)) return;
        if (!(player instanceof HTMLVideoElement)) return;

        const closeBtn = dialog.querySelector('[data-dialog-close]');

        const openWith = (sourceVideo) => {
            if (!(sourceVideo instanceof HTMLVideoElement)) return;
            const src = sourceVideo.getAttribute('data-src') || sourceVideo.currentSrc || sourceVideo.src;
            if (!src) return;

            // Freeze background motion and pause any playing loops.
            document.body.classList.add('is-video-popout-open');
            document.documentElement.classList.add('is-modal-open');
            pauseAllLazyVideos();

            player.pause();
            player.replaceChildren();
            const sourceTrack = sourceVideo.querySelector('track[kind="captions"]');
            if (sourceTrack) {
                const track = sourceTrack.cloneNode(true);
                player.appendChild(track);
            } else {
                const track = document.createElement('track');
                track.kind = 'captions';
                track.srclang = 'en';
                track.label = 'English';
                track.src = asset('./assets/captions/video-popout.vtt');
                track.default = true;
                player.appendChild(track);
            }

            player.removeAttribute('src');
            player.load();

            player.src = resolveHref(src);
            player.currentTime = Math.max(0, sourceVideo.currentTime || 0);

            if (typeof dialog.showModal === 'function') dialog.showModal();
            else dialog.setAttribute('open', '');

            attachCursorToTopLayer(dialog);
            if (closeBtn instanceof HTMLElement) closeBtn.focus();

            const playPromise = player.play();
            if (playPromise && typeof playPromise.catch === 'function') {
                playPromise.catch(() => {});
            }
        };

        document.addEventListener(
            'click',
            (e) => {
                const target = e.target;
                if (!(target instanceof HTMLElement)) return;
                const video = target.closest('.bwc-media-frame--video video');
                if (!(video instanceof HTMLVideoElement)) return;
                e.preventDefault();
                openWith(video);
            },
            { passive: false }
        );

        dialog.addEventListener('close', () => {
            document.body.classList.remove('is-video-popout-open');
            document.documentElement.classList.remove('is-modal-open');
            player.pause();
            player.removeAttribute('src');
            player.load();
            attachCursorToBody();
            resumeVisibleVideos();
        });

        dialog.addEventListener('cancel', (e) => {
            e.preventDefault();
            dialog.close();
        });

        dialog.addEventListener('click', (e) => {
            const rect = dialog.getBoundingClientRect();
            const isInDialog =
                rect.top <= e.clientY &&
                e.clientY <= rect.bottom &&
                rect.left <= e.clientX &&
                e.clientX <= rect.right;
            if (!isInDialog) dialog.close();
        });
    }

    function formatAuditValue(value) {
        if (value == null) return 'n/a';
        if (typeof value === 'number') {
            if (Math.abs(value) >= 10) return value.toFixed(1);
            if (Math.abs(value) >= 1) return value.toFixed(2);
            return value.toFixed(4);
        }
        return String(value);
    }

    function buildBehaviouralAuditHtml(data) {
        if (!data) return '';

        const sections = [
            {
                title: 'Timing',
                metrics: [
                    ['Buy timing score', data.timing?.avg_buy_timing_score],
                    ['Sell timing score', data.timing?.avg_sell_timing_score],
                    ['Buys at highs', data.timing?.buy_at_highs_pct, true],
                    ['Sells at lows', data.timing?.sell_at_lows_pct, true],
                ],
                note: data.timing?.interpretation,
            },
            {
                title: 'Disposition',
                metrics: [
                    ['Avg winner hold (days)', data.disposition?.avg_winner_holding_days],
                    ['Avg loser hold (days)', data.disposition?.avg_loser_holding_days],
                    ['Disposition ratio', data.disposition?.disposition_ratio],
                ],
                note: data.disposition?.interpretation,
            },
            {
                title: 'Turnover',
                metrics: [
                    ['Total trades', data.turnover?.total_trades],
                    ['Trades per week', data.turnover?.trades_per_week],
                    ['Active days', data.turnover?.active_days],
                ],
                note: null,
            },
        ];

        return sections
            .map((section) => {
                const metrics = section.metrics
                    .map(([label, val, isPct]) => {
                        const display =
                            isPct && typeof val === 'number'
                                ? `${(val * 100).toFixed(1)}%`
                                : formatAuditValue(val);
                        return `<div class="ic-dialog__metric"><dt>${label}</dt><dd>${display}</dd></div>`;
                    })
                    .join('');
                const note = section.note
                    ? `<p class="ic-dialog__interpret">${section.note}</p>`
                    : '';
                return `
                    <section class="ic-behavioural-audit__block">
                        <h4 class="ic-kicker">${section.title}</h4>
                        <dl class="ic-dialog__metric-grid">${metrics}</dl>
                        ${note}
                    </section>`;
            })
            .join('');
    }

    function renderBehaviouralAudit(data, container) {
        if (!container || !data) return;
        container.innerHTML = buildBehaviouralAuditHtml(data);
        container.dataset.bwcAuditLoaded = '1';
    }

    let behaviouralAuditDataPromise = null;

    function fetchBehaviouralAuditData() {
        if (!behaviouralAuditDataPromise) {
            behaviouralAuditDataPromise = fetch(asset('./data/behavioural-audit.json'))
                .then((res) => {
                    if (!res.ok) throw new Error('fetch failed');
                    return res.json();
                })
                .catch(() => null);
        }
        return behaviouralAuditDataPromise;
    }

    async function hydrateBehaviouralAudit() {
        const targets = [
            document.getElementById('desk-behavioural-audit'),
        ].filter((el) => el && el.dataset.bwcAuditLoaded !== '1');

        if (!targets.length) return;

        const data = await fetchBehaviouralAuditData();
        if (!data) {
            const fallback =
                '<p class="ic-outcome-plain text-muted">Behavioural audit data unavailable in this snapshot.</p>';
            targets.forEach((el) => {
                el.innerHTML = fallback;
                el.dataset.bwcAuditLoaded = '1';
            });
            return;
        }

        targets.forEach((el) => renderBehaviouralAudit(data, el));
    }

    function renderMemoExcerpts(data) {
        const body = document.getElementById('memo-excerpts-body');
        if (!body || !data?.excerpts?.length) return;

        const picks = data.excerpts.slice(0, 4);
        const href = resolveHref(
            picks[0]?.full_report_href ||
                './deliverables/source/Investment-CHL-Team-5-BWC-1-memo.docx'
        );

        body.innerHTML = `
            <p class="ic-outcome-plain text-muted">${data.word_count ? `${data.word_count.toLocaleString()} words filed` : 'Committee memo'}. Pull quotes below. Full memo download is authoritative.</p>
            ${picks
                .map(
                    (ex) => `
                <article class="ic-dialog__excerpt">
                    <p class="ic-kicker">${ex.kicker || 'Excerpt'}</p>
                    <p>${ex.text}</p>
                </article>`
                )
                .join('')}
            <footer class="ic-dialog__footer">
                <a href="${href}" download class="cta-btn cta-primary cta-compact">Full memo</a>
                <a href="#sources-memo" class="cta-btn cta-secondary cta-compact" data-dialog-close>Pillar links</a>
            </footer>`;
    }

    async function hydrateMemoExcerpts() {
        const body = document.getElementById('memo-excerpts-body');
        if (!body) return;
        try {
            const res = await fetch(asset('./data/report-excerpts.json'));
            if (!res.ok) throw new Error('fetch failed');
            renderMemoExcerpts(await res.json());
        } catch (_) {
            body.innerHTML =
                '<p class="ic-outcome-plain text-muted">Memo excerpts unavailable in this snapshot.</p>';
        }
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

        initLazyChartIframes();
        initLazyVideos();
        initMediaCoordinator();
        eagerLoadDeskCharts();
        hookNewScrollReveal();

        const bootstrapPromise = runSiteBootstrap((pct) => {
            updateSplashCtaProgress(document.getElementById('splash-enter'), pct);
        });

        initSplash(bootstrapPromise);
        initResolvedAssets();
        initPagesDiagnostics();
        initSiteDock();
        initScrollSpy();
        initScrollReveal();
        initStatusBadge();
        initDialogs();
        initVideoPopout();
        initStatAnimations();
        initMarqueePause();
        initFooterYear();
        initFooterCommitLog();

        initBwcMediaZones();
        bootstrapPromise.then(() => {
            initDeferredHydration();
            initDeferredMarquee();
        });

        runWhenIdle(() => {
            initCustomCursor();
        });
    });
})();

    /* =========================================================
       AWWWARDS NARRATIVE EXTENSIONS (JS)
       ========================================================= */

    function initCustomCursor() {
        const cursor = document.querySelector('.custom-cursor');
        if (!cursor) return;

        const finePointer = window.matchMedia('(pointer: fine)').matches;
        const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (!finePointer || reduceMotion) return;

        let mouseX = window.innerWidth / 2;
        let mouseY = window.innerHeight / 2;
        let cursorX = mouseX;
        let cursorY = mouseY;
        let hoverScale = 1;
        let rafId = 0;
        let paintActive = !document.hidden;
        let scrolling = false;
        let scrollEndTimer = 0;
        let cursorStarted = false;

        window.addEventListener(
            'scroll',
            () => {
                scrolling = true;
                clearTimeout(scrollEndTimer);
                scrollEndTimer = window.setTimeout(() => {
                    scrolling = false;
                    if (cursorStarted) startPaint();
                }, 120);
            },
            { passive: true }
        );

        document.addEventListener(
            'mousemove',
            (e) => {
                mouseX = e.clientX;
                mouseY = e.clientY;
                document.body.classList.add('is-cursor-active');
                if (!cursorStarted) {
                    cursorStarted = true;
                    cursorX = mouseX;
                    cursorY = mouseY;
                }
                if (!rafId && paintActive && !scrolling) startPaint();
            },
            { passive: true }
        );

        const interactables = document.querySelectorAll('a, button, canvas');
        interactables.forEach((el) => {
            el.addEventListener('mouseenter', () => {
                hoverScale = 2.5;
                cursor.style.backgroundColor = 'var(--color-bg-base)';
                cursor.style.border = '1px solid var(--color-accent-primary)';
            });
            el.addEventListener('mouseleave', () => {
                hoverScale = 1;
                cursor.style.backgroundColor = 'var(--color-accent-primary)';
                cursor.style.border = 'none';
            });
        });

        function paintCursor() {
            if (!paintActive) {
                rafId = 0;
                return;
            }
            if (scrolling) {
                rafId = 0;
                return;
            }
            cursorX += (mouseX - cursorX) * 0.45;
            cursorY += (mouseY - cursorY) * 0.45;
            cursor.style.transform = `translate3d(${cursorX}px, ${cursorY}px, 0) translate(-50%, -50%) scale(${hoverScale})`;
            rafId = requestAnimationFrame(paintCursor);
        }

        function startPaint() {
            if (!rafId && paintActive) {
                rafId = requestAnimationFrame(paintCursor);
            }
        }

        document.addEventListener('visibilitychange', () => {
            paintActive = !document.hidden;
            if (paintActive && cursorStarted) startPaint();
        });
    }

    function hookNewScrollReveal() {
        const targets = document.querySelectorAll(
            '.fade-up:not(.site-footer):not(.hero-case-study):not(.bwc-no-reveal):not(#research):not(#research *)'
        );
        if (!targets.length) return;

        const reveal = (el) => {
            el.classList.add('revealed');
        };

        const inView = (el) => {
            const rect = el.getBoundingClientRect();
            return rect.bottom >= 0 && rect.top <= window.innerHeight;
        };

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        reveal(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.04, rootMargin: '0px 0px 40% 0px' }
        );

        targets.forEach((el) => {
            if (inView(el)) {
                reveal(el);
                return;
            }
            observer.observe(el);
        });
    }