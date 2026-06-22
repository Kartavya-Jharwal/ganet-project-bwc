#!/usr/bin/env bun
/**
 * Minify and bundle frontend CSS/JS for GitHub Pages.
 * Run from repo root: bun run scripts/minify_frontend_assets.mjs
 */
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const frontend = join(root, 'frontend');
const stylesDir = join(frontend, 'styles');
const jsDir = join(frontend, 'js');

const cssFiles = [
    'tokens.css',
    'body-background.css',
    'layout.css',
    'nav.css',
    'spatial.css',
    'rhythm.css',
    'pages.css',
    'motion.css',
];

async function bundleCss() {
    const parts = await Promise.all(
        cssFiles.map((name) => readFile(join(stylesDir, name), 'utf8'))
    );
    const bundle = parts.join('\n');
    await writeFile(join(stylesDir, 'bundle.css'), bundle, 'utf8');

    const result = await Bun.build({
        entrypoints: [join(stylesDir, 'bundle.css')],
        outdir: stylesDir,
        naming: 'bundle.min.[ext]',
        minify: true,
    });
    if (!result.success) {
        console.error(result.logs);
        process.exit(1);
    }
    console.log('Wrote styles/bundle.css and styles/bundle.min.css');
}

async function minifyJs(name) {
    const input = join(jsDir, name);
    const output = join(jsDir, name.replace(/\.js$/, '.min.js'));
    const result = await Bun.build({
        entrypoints: [input],
        outdir: jsDir,
        naming: name.replace(/\.js$/, '.min.[ext]'),
        minify: true,
        target: 'browser',
    });
    if (!result.success) {
        console.error(result.logs);
        process.exit(1);
    }
    console.log(`Wrote js/${name.replace(/\.js$/, '.min.js')}`);
}

await mkdir(stylesDir, { recursive: true });
await bundleCss();
for (const file of ['base-path.js', 'splash-liquid-gradient.js', 'main.js']) {
    await minifyJs(file);
}
