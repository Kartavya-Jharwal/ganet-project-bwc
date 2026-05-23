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
        try {
            const res = await fetch(DATA_PATH);
            if (!res.ok) {
                return;
            }
            const data = await res.json();
            populateKPIs(data);
            populateResultsTable(data);
        } catch (_) {
            // Static archive — metrics appear after build_frontend_assets
        }
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
        setActiveNav();
        initScrollReveal();
        initStatusBadge();
        fetchAndHydrate();
        mountVideoBackground();
    });
})();
