// SUSPECTED BUG — currently NOT reproducing. Keep as a guard.
//
// Observed once by hand against dicegram.desastreger.cloud: while typing a
// document quickly, `[rect] d "Ship order" step:3` was torn in two — the
// definition relocated to the end of the file and its ` step:3` left orphaned
// on its own line, with the editor reporting
// `Line 6, column 2: unrecognized: step:3`. The suspect is the auto-fix
// rewriter ("rewrote N inline connectors to the verbose bracket form"), which
// replaces the whole buffer on a debounce; an edit landing mid-rewrite would
// be clobbered.
//
// Against the local stack this does NOT reproduce via any input path tried:
// Playwright keyboard.type at 0/10/30ms per key, nor CDP Input.insertText
// (bulk or per-line). Either the deployed commit differs from this working
// tree, or the trigger needs a state this spec does not recreate.
//
// So: these checks currently PASS. Treat a failure here as the bug finally
// reproducing, not as a regression in the spec.
//
// Run: node specs/editor-typing.mjs
import { runSpec, openEditor, typeDsl, setDsl, getDsl, errorText, shot, FIXTURES } from '../lib/harness.mjs';

const norm = (s) =>
  s
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);

/** Every node line we typed should survive verbatim, in place. */
function intact(doc) {
  const lines = norm(doc);
  const missing = [];
  for (const want of [
    '[circle] a "Order received" step:0 type:start',
    '[rect] b "Check stock" step:1',
    '[diamond] c "In stock?" step:2 type:decision',
    '[rect] d "Ship order" step:3',
    '[rect] e "Backorder" step:3',
    '[circle] f "Done" step:4 type:end',
  ]) {
    if (!lines.includes(want)) missing.push(want);
  }
  // A bare ` step:3` fragment is the signature of the tear.
  const orphans = lines.filter((l) => /^step:\d+$/.test(l));
  return { ok: missing.length === 0 && orphans.length === 0, missing, orphans };
}

const r = await runSpec('editor-typing', async (page, t) => {
  await openEditor(page);

  // ─── Baseline: a genuine paste must never corrupt ───
  await setDsl(page, FIXTURES.WITH_STEP);
  const pasted = intact(await getDsl(page));
  t.check('paste keeps the document intact', pasted.ok, JSON.stringify(pasted));
  await shot(page, 'typing-01-pasted');

  // ─── Typing at descending speeds ───
  // delay:0 is the pathological case (macro / very fast typist); 30ms is a
  // brisk human. If slower delays pass and 0 fails, it is a race, not a parser
  // bug — which is exactly what we saw by hand.
  for (const delay of [0, 10, 30]) {
    await openEditor(page);
    await typeDsl(page, FIXTURES.WITH_STEP, { delay });
    const doc = await getDsl(page);
    const res = intact(doc);
    await shot(page, `typing-02-delay${delay}`);
    const err = await errorText(page);
    t.check(
      `typing at ${delay}ms/key keeps the document intact`,
      res.ok,
      res.ok
        ? ''
        : `missing=${JSON.stringify(res.missing)} orphans=${JSON.stringify(res.orphans)}` +
          (err ? ` editorError="${err}"` : ''),
    );
  }
});

process.exit(r.failed ? 1 : 0);
