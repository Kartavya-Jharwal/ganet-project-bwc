#!/usr/bin/env node
/**
 * Serve frontend/ locally and run Lighthouse (mobile).
 * Requires: npm install (lighthouse + serve devDependencies)
 * CI/local: node scripts/lighthouse_ci.mjs
 */
import { spawn } from 'node:child_process';
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

const THRESHOLDS = {
    accessibility: Number(process.env.LH_MIN_ACCESSIBILITY || 0.96),
    'best-practices': Number(process.env.LH_MIN_BEST_PRACTICES || 0.96),
    seo: Number(process.env.LH_MIN_SEO || 0.96),
    performance: Number(process.env.LH_MIN_PERFORMANCE || 0.65),
};

function binPath(name) {
    const ext = process.platform === 'win32' ? '.cmd' : '';
    const local = join(root, 'node_modules', '.bin', `${name}${ext}`);
    return existsSync(local) ? local : name;
}

function runCommand(command, args, { inherit = false } = {}) {
    return new Promise((resolve, reject) => {
        const child = spawn(command, args, {
            stdio: inherit ? 'inherit' : ['ignore', 'pipe', 'pipe'],
            shell: process.platform === 'win32',
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
            reject(new Error(`${command} ${args.join(' ')} failed (${code})\n${stderr || stdout}`));
        });
    });
}

async function startStaticServer() {
    const serveBin = binPath('serve');
    const child = spawn(
        serveBin,
        [frontend, '-l', String(port), '--no-port-switching', '--no-clipboard'],
        {
            stdio: ['ignore', 'pipe', 'pipe'],
            shell: process.platform === 'win32',
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
        const timer = setTimeout(() => finish(), 10000);
        const onReady = (chunk) => {
            const text = chunk.toString();
            if (/Accepting connections|Local:/i.test(text)) finish();
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
    if (!existsSync(join(root, 'node_modules', 'lighthouse')) && !existsSync(binPath('lighthouse'))) {
        throw new Error('Missing lighthouse. Run: npm install');
    }

    const server = await startStaticServer();
    await sleep(1500);

    const url = `http://${host}:${port}/index.html`;
    console.log(`Lighthouse target: ${url}`);

    try {
        await runCommand(
            binPath('lighthouse'),
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

        for (const [category, minimum] of Object.entries(THRESHOLDS)) {
            const score = report.categories?.[category]?.score ?? 0;
            const pct = Math.round(score * 100);
            const minPct = Math.round(minimum * 100);
            const ok = score >= minimum;
            console.log(`${category}: ${pct} (min ${minPct}) ${ok ? 'OK' : 'FAIL'}`);
            if (!ok) failed = true;
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
