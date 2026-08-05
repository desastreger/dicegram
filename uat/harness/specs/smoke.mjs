// Smoke test: the app boots, the editor renders, nothing explodes.
// Run: node specs/smoke.mjs
import { runSpec, openEditor, setDsl, nodePositions, shot, BASE, FIXTURES } from '../lib/harness.mjs';

const r = await runSpec('smoke', async (page, t) => {
  // ─── Landing ───
  await page.goto(BASE, { waitUntil: 'networkidle' });
  t.check('landing responds', true, await page.title());
  t.check(
    'landing has a call to action',
    (await page.locator('text=/without signing up/i').count()) > 0,
  );
  await shot(page, 'smoke-01-landing');

  // ─── Editor ───
  await openEditor(page);
  const nodes = await nodePositions(page);
  t.check('demo editor renders default diagram', nodes.length > 0, `${nodes.length} nodes`);
  await shot(page, 'smoke-02-editor');

  // ─── Round trip ───
  await setDsl(page, FIXTURES.WITH_STEP);
  const after = await nodePositions(page);
  t.check('accepts a pasted document', after.length === 6, `${after.length} nodes (want 6)`);
  t.check(
    'renders the labels we asked for',
    after.some((n) => n.label === 'Order received'),
    after.map((n) => n.label).join(', '),
  );
  await shot(page, 'smoke-03-pasted');

  // ─── Health of the page itself ───
  t.check('no uncaught page errors', page.errors.page.length === 0, page.errors.page.join(' | '));
  t.check('no blocking dialogs', page.errors.dialogs.length === 0, page.errors.dialogs.join(' | '));
  if (page.errors.console.length) t.note(`console errors: ${page.errors.console.length}`);
});

process.exit(r.failed ? 1 : 0);
