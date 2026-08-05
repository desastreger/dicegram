// The Quick-Insert toolbar and the canvas lock, all of which used to lie:
//
//  - the padlock flipped its icon but nodes still dragged, and each drag
//    pinned an @(x,y) into the source
//  - "+ Box" promised "inside the nearest swimlane" but appended an orphan
//    after the lane's closing brace and rendered nothing
//  - "+ Note" twice attached a note to a note (the id scan matched `[note]`)
//
// Run: node specs/toolbar-inserts.mjs
import { runSpec, openEditor, setDsl, getDsl, nodePositions, shot } from '../lib/harness.mjs';

const BASE_DOC = `direction top-to-bottom

[circle] a "Start" step:0 type:start
[rect] b "Middle" step:1
[circle] c "End" step:2 type:end

a -> b
b -> c
`;

// Exact attribute match, not getByRole(name). These buttons are labelled via
// `title`, and a loose regex like /insert swimlane/i also substring-matches
// "Insert box inside the nearest swimlane" — which silently clicked the wrong
// control. Match the full string on either attribute instead.
const click = (page, label) =>
  page.locator(`button[title="${label}"], button[aria-label="${label}"]`).first().click();

const SWIMLANE = 'Insert swimlane';
const BOX = 'Insert box inside the nearest swimlane';
const NOTE = 'Insert sticky note attached to the last shape';
const LOCK = 'Toggle Interactivity';

const r = await runSpec('toolbar-inserts', async (page, t) => {
  // ─── The canvas lock must actually prevent dragging ───
  await openEditor(page);
  await setDsl(page, BASE_DOC);
  await click(page, LOCK);
  await page.waitForTimeout(600);

  const before = (await nodePositions(page)).find((n) => n.label === 'Middle');
  const box = await page.locator('.svelte-flow__node').nth(1).boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 140, box.y + box.height / 2 + 100, { steps: 12 });
  await page.mouse.up();
  await page.waitForTimeout(1800);
  const after = (await nodePositions(page)).find((n) => n.label === 'Middle');
  await shot(page, 'toolbar-01-locked-drag');

  t.check(
    'locked canvas does not move the node',
    before.x === after.x && before.y === after.y,
    `${JSON.stringify(before)} -> ${JSON.stringify(after)}`,
  );
  const lockedDoc = await getDsl(page);
  t.check(
    'locked canvas does not pin an @(x,y) into the source',
    !/@\(/.test(lockedDoc),
    `@() pins present: ${(lockedDoc.match(/@\([^)]*\)/g) || []).join(' ') || 'none'}`,
  );

  // ─── "+ Box" must land inside the swimlane ───
  await openEditor(page);
  await setDsl(page, BASE_DOC);
  await click(page, SWIMLANE);
  await page.waitForTimeout(1200);
  await click(page, BOX);
  await page.waitForTimeout(1800);
  const boxDoc = await getDsl(page);
  await shot(page, 'toolbar-02-box-in-lane');

  // The box body must appear before the lane's closing brace, not after it.
  const laneIdx = boxDoc.indexOf('swimlane "');
  const boxIdx = boxDoc.indexOf('box "');
  const closeIdx = boxDoc.indexOf('\n}', laneIdx);
  t.check(
    '"+ Box" places the box inside the swimlane block',
    laneIdx !== -1 && boxIdx > laneIdx && (closeIdx === -1 || boxIdx < closeIdx),
    boxDoc.replace(/\n/g, ' ⏎ '),
  );

  // ─── "+ Note" twice must attach both notes to shapes, not to a note ───
  await openEditor(page);
  await setDsl(page, BASE_DOC);
  await click(page, NOTE);
  await page.waitForTimeout(1200);
  await click(page, NOTE);
  await page.waitForTimeout(1800);
  const noteDoc = await getDsl(page);
  await shot(page, 'toolbar-03-two-notes');

  const noteTargets = [...noteDoc.matchAll(/\[note\][^\n]*target:(\w+)/g)].map((m) => m[1]);
  const noteIds = [...noteDoc.matchAll(/\[note\]\s+(\w+)\s/g)].map((m) => m[1]);
  t.check(
    'no note is attached to another note',
    noteTargets.every((tg) => !noteIds.includes(tg)),
    `targets=${JSON.stringify(noteTargets)} noteIds=${JSON.stringify(noteIds)}`,
  );
  t.check(
    'no line was commented out as an unknown reference',
    !/\/\/ unknown/.test(noteDoc),
    noteDoc.replace(/\n/g, ' ⏎ '),
  );
});

process.exit(r.failed ? 1 : 0);
