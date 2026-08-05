// The compiler must never destroy text the user wrote, and must never fail
// silently. Each check below corresponds to a bug found on 2026-08-05:
//
//  - a typo in one line caused a DIFFERENT correct line to be deleted
//  - an unclosed '{' swallowed the rest of the document with errors == []
//  - an unclosed edge block dropped the edge with no error and no notice
//  - duplicate-id rename stole an id the user had already used
//  - `<->` and bracket-form edges escaped the unknown-node prune entirely
//
// Run: node specs/document-integrity.mjs
import { runSpec, openEditor, setDsl, getDsl, errorText, nodePositions } from '../lib/harness.mjs';

const r = await runSpec('document-integrity', async (page, t) => {
  await openEditor(page);

  // ─── A typo must not delete an unrelated, correct line ───
  await setDsl(page, '[rect] a "A\\"\n[rect] b "B"\na -> b\n');
  const afterTypo = await getDsl(page);
  t.check(
    'a broken line does not delete the correct "a -> b"',
    afterTypo.includes('a -> b'),
    afterTypo.replace(/\n/g, ' ⏎ '),
  );
  t.check(
    'the neutralised line is commented, not removed',
    /\/\/.*a -> b/.test(afterTypo),
    'expected a // comment preserving the original text',
  );

  // ─── Unclosed container must be reported ───
  await openEditor(page);
  await setDsl(
    page,
    '[rect] a "A"\ngroup "G" {\na\n[rect] b "B"\n[rect] c "C"\nb -> c\n',
  );
  const groupErr = await errorText(page);
  t.check(
    'an unclosed group reports an error instead of silently swallowing',
    !!groupErr && /unclosed/i.test(groupErr),
    `errorText = ${JSON.stringify(groupErr)}`,
  );

  // ─── Unclosed edge block must be reported, and the edge kept ───
  await openEditor(page);
  await setDsl(page, '[rect] a "A"\n[rect] b "B"\na -> b {\nlabel: "hi"\n');
  const edgeErr = await errorText(page);
  t.check(
    'an unclosed edge block reports an error',
    !!edgeErr && /unclosed/i.test(edgeErr),
    `errorText = ${JSON.stringify(edgeErr)}`,
  );

  // ─── Duplicate rename must not steal a user-owned id ───
  await openEditor(page);
  await setDsl(
    page,
    '[rect] a "One"\n[rect] a "Two"\n[rect] a_2 "REAL TARGET"\n[rect] b "B"\nb -> a_2\n',
  );
  const doc = await getDsl(page);
  t.check(
    'the user\'s own "a_2" keeps its id and its label',
    /\[rect\]\s+a_2\s+"REAL TARGET"/.test(doc),
    doc.replace(/\n/g, ' ⏎ '),
  );
  const labels = (await nodePositions(page)).map((n) => n.label);
  t.check('all four nodes still render', labels.length === 4, labels.join(', '));

  // ─── Dangling refs in every edge form ───
  for (const [form, src] of [
    ['inline ->', '[rect] a "A"\na -> ghost\n'],
    ['bidirectional <->', '[rect] a "A"\na <-> ghost\n'],
    ['bracket form', '[rect] a "A"\n[solid_line] e1 from:a to:ghost\n'],
  ]) {
    await openEditor(page);
    await setDsl(page, src);
    const out = await getDsl(page);
    t.check(
      `${form}: dangling reference is neutralised but the text survives`,
      /\/\/.*ghost/.test(out),
      out.replace(/\n/g, ' ⏎ '),
    );
  }
});

process.exit(r.failed ? 1 : 0);
