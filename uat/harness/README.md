# UAT harness

Playwright scripts that drive a **local** Dicegram. The screenshots in `uat/`
were originally produced by hand with scripts that were never committed — this
directory exists so that never happens again.

## Prerequisites

The frontend needs Node ≥20.19 (Vite 8 / rolldown) but this box ships Node
v20.14, and `frontend/.npmrc` sets `engine-strict=true`, so `npm install` will
refuse. A portable Node 22 lives outside the repo:

```bash
export PATH="$HOME/.local/lib/node-v22.20.0-linux-x64/bin:$PATH"
```

Override with `DICEGRAM_NODE_HOME` if you put it elsewhere.

Browser: uses **system Chrome** (`/usr/bin/google-chrome`) via `playwright-core`,
so there is no ~400 MB browser download. Override with `CHROME_PATH`.

## Running

```bash
scripts/dev-up                  # FastAPI :8000 + Vite :5173
cd uat/harness && npm install   # once

node run-all.mjs                # every spec
node run-all.mjs layout typing  # only specs matching these substrings
node specs/smoke.mjs            # one spec directly
HEADED=1 node run-all.mjs       # watch the browser work

scripts/dev-down
```

`run-all.mjs` exits with the number of failed specs, so CI can gate on it.
Screenshots land in `shots/` (gitignored).

Point it at any instance with `DICEGRAM_BASE`:

```bash
DICEGRAM_BASE=https://dicegram.desastreger.cloud node specs/smoke.mjs
```

> Always use `localhost`, never `127.0.0.1` — **Vite binds IPv6 loopback only**,
> so a literal `127.0.0.1:5173` returns nothing even while the server is up.

## Specs

All six specs are green as of 2026-08-05. Each one guards a bug that was real
and has since been fixed, so a failure here means a regression, not a flaky
test.

| Spec | What it covers |
|---|---|
| `smoke.mjs` | Landing loads, demo editor renders, paste round-trips, no uncaught errors |
| `layout-ranking.mjs` | Rank derived from the arrow graph when no `step:` is given; explicit steps still win |
| `document-integrity.mjs` | The compiler never deletes user text and never fails silently: commented-out dangling refs, unclosed `{` reported, duplicate rename can't steal an id |
| `toolbar-inserts.mjs` | Canvas lock actually locks; "+ Box" nests in the swimlane; "+ Note" won't attach a note to a note |
| `canvas-controls.mjs` | `?` opens the shortcuts overlay; Fit View reframes overflowing content |
| `editor-typing.mjs` | Document integrity while typing at 0/10/30 ms per key. Guards a corruption seen once on production that has never reproduced locally — a failure here means it finally did |

## Writing your own

`lib/harness.mjs` is the whole API:

```js
import { runSpec, openEditor, setDsl, nodePositions, shot, FIXTURES } from '../lib/harness.mjs';

const r = await runSpec('my-spec', async (page, t) => {
  await openEditor(page);                    // demo editor, no account needed
  await setDsl(page, FIXTURES.WITH_STEP);    // paste (single transaction)
  t.check('renders six nodes', (await nodePositions(page)).length === 6);
  await shot(page, 'my-spec-01');
});
process.exit(r.failed ? 1 : 0);
```

- `setDsl()` pastes via a real `ClipboardEvent` — one CodeMirror transaction,
  so the auto-fix rewriter cannot interleave. Use `typeDsl(page, text, {delay})`
  when you specifically want to exercise that race.
- `page.errors` collects `.console`, `.page` and `.dialogs`. Dialogs are
  auto-dismissed: an open modal blocks every later CDP command and would
  otherwise wedge the run.
- `nodePositions()` → `[{label, x, y}]`, `viewportTransform()`, `errorText()`
  (the editor's current `Line N, column M:` message).

Scratch/exploratory scripts go in `explore/` (gitignored).
