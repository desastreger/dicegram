// BUG: `?` opens nothing, though the landing page says "hit ? for keyboard
// shortcuts" and the README documents a full table. Other shortcuts
// (Ctrl+Z, Ctrl+B) work, so the global handler is fine — just not this one.
// Reproduced on both the local dev stack and dicegram.desastreger.cloud.
//
// The Fit View checks here are a passing regression guard, not a bug. Fit View
// was initially suspected of being a no-op based on a hand-observation against
// production; this spec disproved that (scale 0.688 -> 0.414, all nodes on
// screen), so the checks stay to keep it honest.
//
// Run: node specs/canvas-controls.mjs
import { runSpec, openEditor, setDsl, viewportTransform, nodePositions, shot, FIXTURES } from '../lib/harness.mjs';

// Taller than the viewport, so Fit View has something real to do.
const TALL = `direction top-to-bottom

${Array.from({ length: 10 }, (_, i) => `[rect] n${i} "Step number ${i}" step:${i}`).join('\n')}

${Array.from({ length: 9 }, (_, i) => `n${i} -> n${i + 1}`).join('\n')}
`;

const r = await runSpec('canvas-controls', async (page, t) => {
  await openEditor(page);
  await setDsl(page, TALL);

  const nodes = await nodePositions(page);
  const span = Math.max(...nodes.map((n) => n.y)) - Math.min(...nodes.map((n) => n.y));
  t.note(`${nodes.length} nodes spanning ${span}px vertically`);

  // ─── Fit View ───
  const before = await viewportTransform(page);
  await page.click('button[aria-label="Fit View"], button[title="Fit View"]').catch(async () => {
    await page.getByRole('button', { name: /fit view/i }).click();
  });
  await page.waitForTimeout(1500);
  const after = await viewportTransform(page);
  await shot(page, 'controls-01-after-fit');

  t.check(
    'Fit View changes the viewport when content overflows',
    before !== after,
    `before=${before}\n      after =${after}`,
  );

  const allVisible = await page.evaluate(() => {
    const pane = document.querySelector('.svelte-flow__viewport').getBoundingClientRect();
    const host = document.querySelector('.svelte-flow').getBoundingClientRect();
    return [...document.querySelectorAll('.svelte-flow__node')].every((n) => {
      const b = n.getBoundingClientRect();
      return b.top >= host.top - 1 && b.bottom <= host.bottom + 1;
    }) && !!pane;
  });
  t.check('every node is on screen after Fit View', allVisible);

  // ─── `?` help overlay ───
  const dialogsBefore = await page.evaluate(
    () => document.querySelectorAll('dialog[open],[role=dialog]').length,
  );
  await page.click('.svelte-flow'); // focus the canvas, not CodeMirror
  await page.keyboard.press('Shift+Slash');
  await page.waitForTimeout(1200);
  const dialogsAfter = await page.evaluate(
    () => document.querySelectorAll('dialog[open],[role=dialog]').length,
  );
  const mentions = await page.evaluate(() => /keyboard shortcut/i.test(document.body.innerText));
  await shot(page, 'controls-02-after-question-mark');

  t.check(
    '`?` opens the keyboard-shortcuts overlay',
    dialogsAfter > dialogsBefore || mentions,
    `dialogs ${dialogsBefore} → ${dialogsAfter}, body mentions shortcuts: ${mentions}`,
  );

  // Control: a shortcut that does work, proving the handler is wired up.
  await page.keyboard.press('Control+b');
  await page.waitForTimeout(800);
  const treeOpen = await page.evaluate(() => /dicetree/i.test(document.body.innerText));
  t.check('control: Ctrl+B still toggles the dicetree', treeOpen);
});

process.exit(r.failed ? 1 : 0);
