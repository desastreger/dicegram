// Shared plumbing for the Dicegram Playwright specs.
//
// Drives the *local* dev stack (scripts/dev-up) at http://localhost:5173.
// Use `localhost`, never 127.0.0.1 — Vite binds IPv6 loopback only.
//
// We use playwright-core against the system Chrome rather than the full
// `playwright` package: no ~400MB browser download, and it exercises the
// same engine real users are on.

import { chromium } from 'playwright-core';
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const HERE = dirname(fileURLToPath(import.meta.url));
export const SHOTS = join(HERE, '..', 'shots');
export const BASE = process.env.DICEGRAM_BASE ?? 'http://localhost:5173';

mkdirSync(SHOTS, { recursive: true });

const CHROME = process.env.CHROME_PATH ?? '/usr/bin/google-chrome';

/** Launch Chrome. `headed:true` (or HEADED=1) to watch it work. */
export async function launch({ headed = !!process.env.HEADED } = {}) {
  return chromium.launch({
    executablePath: CHROME,
    headless: !headed,
    // --no-sandbox: required when running as a non-root user without a
    // user namespace; --disable-dev-shm-usage avoids /dev/shm exhaustion.
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
}

/**
 * A page with console errors, page errors and dialogs captured. Dialogs are
 * auto-dismissed: an open modal blocks every subsequent CDP command, which
 * would wedge the whole run.
 */
export async function newPage(browser, { viewport = { width: 1440, height: 900 } } = {}) {
  const ctx = await browser.newContext({ viewport });
  const page = await ctx.newPage();
  page.errors = { console: [], page: [], dialogs: [] };
  page.on('console', (m) => m.type() === 'error' && page.errors.console.push(m.text()));
  page.on('pageerror', (e) => page.errors.page.push(String(e)));
  page.on('dialog', async (d) => {
    page.errors.dialogs.push(d.message());
    await d.dismiss().catch(() => {});
  });
  return page;
}

/** Open the demo editor (no account needed) and wait for first render. */
export async function openEditor(page, { demo = true } = {}) {
  await page.goto(`${BASE}/editor${demo ? '?demo=1' : ''}`, { waitUntil: 'networkidle' });
  await page.waitForSelector('.cm-content', { timeout: 15000 });
  await page.waitForTimeout(1200);
  return page;
}

/**
 * Replace the document via a real paste event.
 *
 * This is the *clean* path: a genuine ClipboardEvent lands as one CodeMirror
 * transaction, so the compiler's auto-fix rewriter can't interleave with it.
 * Use typeDsl() when you specifically want to exercise that race.
 */
export async function setDsl(page, text) {
  await page.evaluate((doc) => {
    const cm = document.querySelector('.cm-content');
    cm.focus();
    document.execCommand('selectAll');
    const dt = new DataTransfer();
    dt.setData('text/plain', doc);
    cm.dispatchEvent(
      new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }),
    );
  }, text);
  await page.waitForTimeout(2000); // debounced /api/render round-trip
}

/**
 * Type the document keystroke-by-keystroke, like a human at `delay` ms.
 * delay:0 reproduces the auto-fix race that mangles the buffer.
 */
export async function typeDsl(page, text, { delay = 0 } = {}) {
  await page.click('.cm-content');
  await page.keyboard.press('Control+a');
  await page.keyboard.type(text, { delay });
  await page.waitForTimeout(2500);
}

export const getDsl = (page) => page.evaluate(() => document.querySelector('.cm-content').innerText);

/** Rendered node labels + their canvas transforms. */
export const nodePositions = (page) =>
  page.evaluate(() =>
    [...document.querySelectorAll('.svelte-flow__node')].map((n) => {
      const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform) ?? [];
      return { label: n.innerText.trim().split('\n')[0], x: +m[1], y: +m[2] };
    }),
  );

export const viewportTransform = (page) =>
  page.evaluate(() => document.querySelector('.svelte-flow__viewport')?.style.transform ?? null);

/** Any parse/compile error the editor is currently surfacing. */
export const errorText = (page) =>
  page.evaluate(() => {
    const el = [...document.querySelectorAll('*')].find(
      (e) => e.children.length === 0 && /^Line \d+, column \d+:/.test(e.textContent.trim()),
    );
    return el ? el.textContent.trim() : null;
  });

export async function shot(page, name) {
  const path = join(SHOTS, `${name}.png`);
  await page.screenshot({ path, fullPage: false });
  return path;
}

/** Just the canvas pane — for comparing on-screen rendering against exports. */
export async function shotCanvas(page, name) {
  const path = join(SHOTS, `${name}.png`);
  const el = page.locator('.svelte-flow').first();
  await el.screenshot({ path });
  return path;
}

/**
 * The export SVG, straight from the server.
 *
 * Worth knowing: this is a DIFFERENT renderer from the one on screen. The
 * canvas is @xyflow/svelte; this is backend/app/dsl/export_svg.py. They can
 * disagree, which is exactly what an export-fidelity check is looking for.
 */
export async function exportSvg(page, source) {
  return page.evaluate(async (src) => {
    const res = await fetch('/api/export/svg', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: src }),
    });
    if (!res.ok) return { ok: false, status: res.status, body: (await res.text()).slice(0, 300) };
    return { ok: true, status: res.status, svg: await res.text() };
  }, source);
}

/** Render an SVG string in a blank tab and screenshot it, so it can be eyeballed. */
export async function shotSvg(page, svg, name) {
  const path = join(SHOTS, `${name}.png`);
  await page.setContent(
    `<body style="margin:0;background:#fff;display:inline-block">${svg}</body>`,
  );
  await page.waitForTimeout(400);
  const el = page.locator('svg').first();
  await el.screenshot({ path }).catch(async () => {
    await page.screenshot({ path });
  });
  return path;
}

/** Geometry of the export SVG, for sanity checks (clipping, zero size, NaN). */
export function svgMetrics(svg) {
  const wm = /<svg[^>]*\bwidth="([\d.]+)"/.exec(svg);
  const hm = /<svg[^>]*\bheight="([\d.]+)"/.exec(svg);
  const vb = /viewBox="([^"]+)"/.exec(svg);
  return {
    width: wm ? +wm[1] : null,
    height: hm ? +hm[1] : null,
    viewBox: vb ? vb[1] : null,
    texts: (svg.match(/<text/g) || []).length,
    paths: (svg.match(/<path/g) || []).length,
    bytes: svg.length,
  };
}

// ─── Tiny test runner ──────────────────────────────────────────────────────
// Deliberately not a framework. Each spec is a plain script that can be run
// on its own (`node specs/layout-ranking.mjs`) and prints its own verdict.

export function suite(name) {
  const results = [];
  const api = {
    name,
    check(label, pass, detail = '') {
      results.push({ label, pass: !!pass, detail });
      const mark = pass ? '\x1b[32m✓\x1b[0m' : '\x1b[31m✗\x1b[0m';
      console.log(`  ${mark} ${label}${detail ? `\n      ${detail}` : ''}`);
      return !!pass;
    },
    note: (msg) => console.log(`  \x1b[2m· ${msg}\x1b[0m`),
    get results() {
      return results;
    },
    summary() {
      const failed = results.filter((r) => !r.pass);
      console.log(
        `\n${name}: ${results.length - failed.length}/${results.length} passed` +
          (failed.length ? ` — \x1b[31m${failed.length} failed\x1b[0m` : ''),
      );
      return { name, total: results.length, failed: failed.length, results };
    },
  };
  console.log(`\n\x1b[1m${name}\x1b[0m`);
  return api;
}

/** Standard spec wrapper: launches, runs body(page, t), always tears down. */
export async function runSpec(name, body, opts = {}) {
  const t = suite(name);
  const browser = await launch(opts);
  try {
    const page = await newPage(browser, opts);
    await body(page, t);
  } catch (err) {
    t.check('spec completed without throwing', false, String(err).split('\n')[0]);
  } finally {
    await browser.close();
  }
  return t.summary();
}

// Fixtures used across specs. `WITH_STEP` is the same graph as `NO_STEP`
// with explicit ranks — the pair isolates the layout-ranking bug.
export const FIXTURES = {
  WITH_STEP: `direction top-to-bottom

[circle] a "Order received" step:0 type:start
[rect] b "Check stock" step:1
[diamond] c "In stock?" step:2 type:decision
[rect] d "Ship order" step:3
[rect] e "Backorder" step:3
[circle] f "Done" step:4 type:end

a -> b
b -> c
c -> d : "yes"
c -> e : "no"
d -> f
e -> b
`,
  NO_STEP: `direction top-to-bottom

[circle] a "Order received" type:start
[rect] b "Check stock"
[diamond] c "In stock?" type:decision
[rect] d "Ship order"
[rect] e "Backorder"
[circle] f "Done" type:end

a -> b
b -> c
c -> d : "yes"
c -> e : "no"
d -> f
e -> b
`,
};
