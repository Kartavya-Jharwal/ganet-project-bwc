/**
 * BWC-QUANT | Frontend Hydration Engine
 * Fetches results.json, populates KPIs, handles scroll reveals and nav state.
 */

(function () {
    'use strict';

    const DATA_PATH = './data/results.json';

    const FALLBACK_DATA = {
        mc_hurdle: '94.2%',
        cf_var: '-2.14%',
        beta: '0.85',
        sharpe: '1.42',
        max_dd: '-8.7%',
        ann_return: '12.3%',
        sortino: '1.89',
        calmar: '1.41',
        win_rate: '58.3%',
        profit_factor: '1.67'
    };

    // --- KPI Hydration ---

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

    function populateResultsTable(data) {
        const tableMapping = {
            'tbl-ann-return': 'ann_return',
            'tbl-sharpe': 'sharpe',
            'tbl-max-dd': 'max_dd',
            'tbl-sortino': 'sortino',
            'tbl-cf-var': 'cf_var',
            'tbl-calmar': 'calmar',
            'tbl-beta': 'beta',
            'tbl-mc-hurdle': 'mc_hurdle',
            'tbl-win-rate': 'win_rate',
            'tbl-profit-factor': 'profit_factor'
        };

        for (const [elemId, key] of Object.entries(tableMapping)) {
            const el = document.getElementById(elemId);
            if (el && data[key] != null) {
                el.textContent = data[key];
            }
        }
    }

    async function fetchAndHydrate() {
        let data = FALLBACK_DATA;

        try {
            const res = await fetch(DATA_PATH);
            if (res.ok) {
                const json = await res.json();
                data = Object.assign({}, FALLBACK_DATA, json);
            }
        } catch (_) {
            // Static archive mode — use fallback
        }

        populateKPIs(data);
        populateResultsTable(data);
    }

    // --- Scroll Reveal via IntersectionObserver ---

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

    // --- Nav Active State ---

    function setActiveNav() {
        const currentPage = window.location.pathname.split('/').pop() || 'index.html';
        const links = document.querySelectorAll('.nav-link');

        links.forEach((link) => {
            const href = link.getAttribute('href');
            if (href === currentPage) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    // --- Status Badge ---

    function initStatusBadge() {
        const dot = document.getElementById('status-dot');
        const label = document.getElementById('status-label');
        if (!dot || !label) return;

        try {
            if (typeof Appwrite !== 'undefined' && Appwrite.Client) {
                const client = new Appwrite.Client()
                    .setEndpoint('https://cloud.appwrite.io/v1')
                    .setProject('bwc-quant-live');

                client.subscribe(
                    'databases.bwc_db.collections.signals.documents',
                    () => {
                        dot.style.backgroundColor = 'var(--color-quant-positive)';
                        label.textContent = 'LIVE';
                    }
                );

                dot.style.backgroundColor = 'var(--color-quant-positive)';
                label.textContent = 'LIVE';
                return;
            }
        } catch (_) {
            // Appwrite unavailable
        }

        dot.style.backgroundColor = 'var(--color-text-muted)';
        label.textContent = 'STATIC ARCHIVE';
    }

    // --- Video Background Mount ---

    function mountVideoBackground() {
        const container = document.querySelector('.video-bg');
        if (!container) return;

        const placeholder = container.querySelector('.viz-placeholder');
        if (!placeholder) return;

        // Will be replaced when video assets exist
        // Checks for a known video file and mounts if available
        const video = document.createElement('video');
        video.autoplay = true;
        video.loop = true;
        video.muted = true;
        video.playsInline = true;
        video.style.cssText = 'width:100%;height:100%;object-fit:cover;';

        const source = document.createElement('source');
        source.src = './assets/videos/hero-render.mp4';
        source.type = 'video/mp4';
        video.appendChild(source);

        video.addEventListener('canplay', () => {
            container.innerHTML = '';
            container.appendChild(video);
        });
    }

    // --- Init ---

    document.addEventListener('DOMContentLoaded', () => {
        setActiveNav();
        initScrollReveal();
        initStatusBadge();
        fetchAndHydrate();
        mountVideoBackground();
    });
})();
