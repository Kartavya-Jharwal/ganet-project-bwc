/**
 * GitHub Pages + local static server base-path resolver.
 * Must load before CSS/JS that use relative ./ paths (inject <base> early).
 */
(function (global) {
    'use strict';

    /** GitHub Pages project URL without trailing slash breaks ./ relative URLs. */
    function normalizeProjectRootUrl() {
        if (global.location.protocol === 'file:') return;
        const path = global.location.pathname || '/';
        if (path.endsWith('/') || /\/index\.html$/i.test(path)) return;
        const segments = path.split('/').filter(Boolean);
        const last = segments[segments.length - 1] || '';
        if (segments.length === 1 && !/\.[a-z0-9]{2,8}$/i.test(last)) {
            global.location.replace(
                `${path}/${global.location.search}${global.location.hash}`
            );
        }
    }

    function computeSiteBase() {
        if (global.location.protocol === 'file:') {
            const path = global.location.pathname.replace(/\\/g, '/');
            const lastSlash = path.lastIndexOf('/');
            return lastSlash >= 0 ? path.slice(0, lastSlash + 1) : '/';
        }

        let path = global.location.pathname || '/';

        if (/\/index\.html$/i.test(path)) {
            path = path.slice(0, -'/index.html'.length) || '/';
        }

        if (!path.endsWith('/')) {
            const last = path.split('/').filter(Boolean).pop() || '';
            const isFile = /\.[a-z0-9]{2,8}$/i.test(last);
            path = isFile ? path.slice(0, -(last.length + 1)) || '/' : `${path}/`;
        }

        if (!path.startsWith('/')) {
            path = `/${path}`;
        }
        return path;
    }

    function encodePathSegments(relative) {
        return relative
            .split('/')
            .map((seg) => {
                if (!seg) return seg;
                try {
                    return encodeURIComponent(decodeURIComponent(seg));
                } catch (_) {
                    return encodeURIComponent(seg);
                }
            })
            .join('/');
    }

    function assetPath(relative) {
        const rel = String(relative || '').replace(/^\.\//, '').replace(/^\//, '');
        const base = computeSiteBase();
        return `${base}${encodePathSegments(rel)}`;
    }

    function resolveHref(href) {
        if (!href) return href;
        if (/^(https?:|mailto:|#|data:)/i.test(href)) return href;
        if (href.startsWith('/')) return href;
        return assetPath(href.replace(/^\.\//, ''));
    }

    function injectBaseTag() {
        if (document.querySelector('base[data-bwc-base]')) return;
        const baseEl = document.createElement('base');
        baseEl.setAttribute('data-bwc-base', '');
        baseEl.href = computeSiteBase();
        const head = document.head || document.getElementsByTagName('head')[0];
        if (head) {
            head.insertBefore(baseEl, head.firstChild);
        }
    }

    function rewriteRelativeUrls(root) {
        const scope = root || document;
        scope.querySelectorAll('[href^="./"], [src^="./"], [data-src^="./"]').forEach((el) => {
            const attr = el.hasAttribute('href') ? 'href' : el.hasAttribute('src') ? 'src' : 'data-src';
            const raw = el.getAttribute(attr);
            if (raw) el.setAttribute(attr, resolveHref(raw));
        });
    }

    function redirectTo(target) {
        global.location.replace(resolveHref(target));
    }

    normalizeProjectRootUrl();
    injectBaseTag();

    global.BWC = global.BWC || {};
    global.BWC.siteBase = computeSiteBase();
    global.BWC.asset = assetPath;
    global.BWC.resolveHref = resolveHref;
    global.BWC.rewriteRelativeUrls = rewriteRelativeUrls;
    global.BWC.redirectTo = redirectTo;
})(window);
