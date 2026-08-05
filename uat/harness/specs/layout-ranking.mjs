// Regression guard for the layout-ranking bug (fixed 2026-08-05).
//
// Was: layout ranked nodes *only* by an explicit `step:`. Without it,
// `parser.py`'s `attrs.pop("step", "0")` put every node at rank 0 and the
// diagram degenerated into one straight row, ignoring the arrow graph. That
// hit the shorthand the landing page itself teaches (`a -> b`), which emits
// no `step:` — so the homepage's own example laid out wrong.
//
// Now: `layout._derive_steps_from_edges` ranks by longest path over the edge
// DAG whenever no node carries an explicit step. Documents that do carry
// explicit steps are untouched, so saved dicegrams keep their layout.
//
// Run: node specs/layout-ranking.mjs
import { runSpec, openEditor, setDsl, nodePositions, shot, FIXTURES } from '../lib/harness.mjs';

const spread = (vals) => Math.max(...vals) - Math.min(...vals);

const r = await runSpec('layout-ranking', async (page, t) => {
  await openEditor(page);

  // ─── Control: explicit step: → proper vertical hierarchy ───
  await setDsl(page, FIXTURES.WITH_STEP);
  const withStep = await nodePositions(page);
  await shot(page, 'ranking-01-with-step');
  const wy = spread(withStep.map((n) => n.y));
  const wx = spread(withStep.map((n) => n.x));
  t.check(
    'with step: — flows top-to-bottom as asked',
    wy > wx,
    `y-spread ${wy} vs x-spread ${wx}`,
  );
  t.check(
    'with step: — the two step:3 branches share a rank',
    (() => {
      const d = withStep.find((n) => n.label === 'Ship order');
      const e = withStep.find((n) => n.label === 'Backorder');
      return d && e && d.y === e.y && d.x !== e.x;
    })(),
    withStep.map((n) => `${n.label}(${n.x},${n.y})`).join(' '),
  );

  // ─── Same graph, step: removed ───
  await setDsl(page, FIXTURES.NO_STEP);
  const noStep = await nodePositions(page);
  await shot(page, 'ranking-02-no-step');
  const ny = spread(noStep.map((n) => n.y));
  const nx = spread(noStep.map((n) => n.x));

  t.note(`no step: → ${noStep.map((n) => `${n.label}(${n.x},${n.y})`).join(' ')}`);

  // Must come out the same shape as the control above: the arrows are
  // identical, so the ranks derived from them must be too.
  t.check(
    'without step: — still flows top-to-bottom (derived from arrows)',
    ny > nx,
    `y-spread ${ny} vs x-spread ${nx} (a single row here means the arrow graph was ignored)`,
  );
  t.check(
    'without step: — start and end are not on the same rank',
    noStep.find((n) => n.label === 'Order received')?.y !==
      noStep.find((n) => n.label === 'Done')?.y,
    `start.y=${noStep.find((n) => n.label === 'Order received')?.y} end.y=${noStep.find((n) => n.label === 'Done')?.y}`,
  );
});

process.exit(r.failed ? 1 : 0);
