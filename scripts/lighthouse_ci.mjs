#!/usr/bin/env node
/**
 * Serve frontend/ locally and run Lighthouse (mobile).
 * Requires: bun install (or npm install) for lighthouse + serve devDependencies.
 * CI/local: bun scripts/lighthouse_ci.mjs
 */
import { spawn, spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as sleep } from 'node:timers/promises';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const frontend = join(root, 'frontend');
const port = Number(process.env.LH_PORT || 4173);
const host = process.env.LH_HOST || '127.0.0.1';
const reportPath = join(root, 'lighthouse-report.json');
const serveEntry = join(root, 'node_modules', 'serve', 'build', 'main.js');
const lighthouseEntry = join(root, 'node_modules', 'lighthouse', 'cli', 'index.js');

const GATES = {
    accessibility: Number(process.env.LH_MIN_ACCESSIBILITY || 0.96),
    'best-practices': Number(process.env.LH_MIN_BEST_PRACTICES || 0.96),
    seo: Number(process.env.LH_MIN_SEO || 0.96),
};

/** Logged every run; does not fail CI (splash + WebGL archive is timing-heavy). */
const REPORT_ONLY = ['performance'];

function pickRunner() {
    if (process.env.LH_RUNNER) return process.env.LH_RUNNER;
    const nodeOk = spawnSync('node', ['--version'], { stdio: 'ignore' }).status === 0;
    if (nodeOk) return 'node';
    const bunOk = spawnSync('bun', ['--version'], { stdio: 'ignore' }).status === 0;
    if (bunOk) return 'bun';
    throw new Error('Need node or bun on PATH to run Lighthouse CI');
}

function runCommand(runner, entry, args, { inherit = false } = {}) {
    return new Promise((resolve, reject) => {
        const child = spawn(runner, [entry, ...args], {
            stdio: inherit ? 'inherit' : ['ignore', 'pipe', 'pipe'],
            shell: false,
        });
        let stdout = '';
        let stderr = '';
        if (!inherit) {
            child.stdout?.on('data', (chunk) => {
                stdout += chunk.toString();
            });
            child.stderr?.on('data', (chunk) => {
                stderr += chunk.toString();
            });
        }
        child.on('error', reject);
        child.on('close', (code) => {
            if (code === 0) {
                resolve({ stdout, stderr });
                return;
            }
            reject(
                new Error(
                    `${runner} ${entry} ${args.join(' ')} failed (${code})\n${stderr || stdout}`
                )
            );
        });
    });
}

async function startStaticServer(runner) {
    const child = spawn(
        runner,
        [serveEntry, frontend, '-l', String(port), '--no-clipboard', '-L'],
        {
            stdio: ['ignore', 'pipe', 'pipe'],
            shell: false,
        }
    );

    await new Promise((resolve, reject) => {
        let settled = false;
        const finish = (err) => {
            if (settled) return;
            settled = true;
            clearTimeout(timer);
            if (err) reject(err);
            else resolve();
        };
        const timer = setTimeout(() => finish(), 12000);
        const onReady = (chunk) => {
            const text = chunk.toString();
            if (/Accepting connections|localhost/i.test(text)) finish();
        };
        child.stdout?.on('data', onReady);
        child.stderr?.on('data', onReady);
        child.on('error', (err) => finish(err));
        child.on('exit', (code) => {
            if (!settled && code !== 0) finish(new Error(`serve exited early (${code})`));
        });
    });

    return child;
}

async function main() {
    if (!existsSync(serveEntry) || !existsSync(lighthouseEntry)) {
        throw new Error('Missing lighthouse or serve. Run: bun install');
    }

    const runner = pickRunner();
    console.log(`Runner: ${runner}`);

    const server = await startStaticServer(runner);
    await sleep(2000);

    const url = `http://${host}:${port}/index.html`;
    console.log(`Lighthouse target: ${url}`);

    try {
        await runCommand(
            runner,
            lighthouseEntry,
            [
                url,
                '--form-factor=mobile',
                '--only-categories=performance,accessibility,best-practices,seo',
                '--output=json',
                `--output-path=${reportPath}`,
                '--quiet',
                '--chrome-flags=--headless --no-sandbox --disable-gpu',
            ],
            { inherit: true }
        );

        const report = JSON.parse(await readFile(reportPath, 'utf8'));
        let failed = false;

        for (const [category, minimum] of Object.entries(GATES)) {
            const score = report.categories?.[category]?.score ?? 0;
            const pct = Math.round(score * 100);
            const minPct = Math.round(minimum * 100);
            const ok = score >= minimum;
            console.log(`${category}: ${pct} (min ${minPct}) ${ok ? 'OK' : 'FAIL'}`);
            if (!ok) failed = true;
        }

        for (const category of REPORT_ONLY) {
            const score = report.categories?.[category]?.score ?? 0;
            const pct = Math.round(score * 100);
            console.log(`${category}: ${pct} (report only)`);
        }

        if (failed) {
            process.exit(1);
        }
    } finally {
        server.kill('SIGTERM');
    }
}

main().catch((err) => {
    console.error(err.message || err);
    process.exit(1);
});
