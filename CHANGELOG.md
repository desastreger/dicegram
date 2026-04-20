# Changelog

All notable changes to Dicegram are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [4.2.0] — 2026-04-20

Connector grammar upgrade. Edges now have the same authoring depth as
nodes — they can be named, referenced, inspector-edited, and carry
structured anchor fields the self-healer understands.

### Added
- **`[connector]` bracket form** — one-line object-style syntax mirroring
  node declarations: `[connector] c1 from:A@r to:B@l kind:dashed
  tip:arrow back:circle label:"yes"`. Round-trips through the inspector,
  counts as an edge for ordinal purposes, and survives normalization.
- **`from_anchor:` / `to_anchor:` fields** — explicit source/target
  anchor sides (`top`/`bottom`/`left`/`right`) separable from the node
  reference. Gives the self-healing compiler a structured signal for
  fixing layout drift without guessing author intent.
- **`tip:` / `back:` keywords** — user-friendly aliases for `end:` /
  `start:` edge decorations in both inline and block/bracket forms.
- **`[linebreak]` label token** — multi-line labels as `"First part"
  [linebreak] "Second part"` in node labels, edge labels, note text, and
  connector `label:` values. Replaces the programmer-ism of `\n` escapes
  in strings. Old files with `\n` still parse.
- **Standalone "LLM prompt" button** on the editor toolbar — previously
  buried inside the Export dropdown.
- **Autocomplete** surfaces `[connector]`, `[linebreak]`, `tip:` / `back:`
  values, `kind:` values, anchor sides, and all bracket-form keys when
  the cursor sits inside a `[connector]` line.

### Fixed
- **Arrow tips now render reliably** — `SmartEdge` was dropping
  `markerStart` (no source-side tips reached the DOM). Markers also
  depended on SVG-2 `context-stroke` support which isn't universal yet;
  switched to a CSS variable (`--th-edge`) set by the editor wrapper.
- **`[connector] ... to:b` no longer collapses `b` into the port alias
  for "bottom"** when the target is a node literally named `b`. The
  bare-port interpretation now only applies in block-form headers where
  source/target is already bound.

### Changed
- **LLM prompt** rewritten for the new grammar. Documents bracket form,
  block form, anchor fields, `tip:`/`back:`, and `[linebreak]` — so
  LLM-generated DSL pasted into the editor stays consistent.
- **Syntax highlighter** colours `[connector]` and `[linebreak]` as
  keywords (distinct from shape brackets).

---

## [4.1.0] — 2026-04-18

Live-editor polish round: UX audit findings (most of the top-10), inspector
coverage for every object kind, orthogonal-only connectors, demo mode, and a
hard-reset dev runner.

### Added
- **Mini live editor on the landing page** — real `CodeEditor` + `Canvas`
  components embedded at `/`, no Toolbar / Inspector / Tree. Edit the DSL on
  the left, see the diagram on the right, live.
- **Demo mode** at `/editor?demo=1` — no account required, source persists
  to `localStorage['dicegram:demo:source']`. Save prompts to sign up.
  Reachable from the landing via a "Try without an account" CTA.
- **Debounced autosave** — logged-in users on a saved dicegram get a silent
  `PUT` 2 s after the last edit; toolbar shows `Saving…` / `Saved`.
- **Share from the editor toolbar** — popover with URL input, Copy, Revoke
  (the `DELETE /api/dicegrams/{id}/share` endpoint was orphaned before).
- **Double-click shape → focus label** — new `labelFocusTrigger` prop pipes
  from Canvas → +page → Inspector.
- **Edge inspector** — clicking a connector opens an `EdgePanel` with
  from/to (readonly), kind dropdown, label input, Delete. Backed by new
  `setEdgeLabel` / `setEdgeKind` / `removeEdge` patch helpers.
- **Object inspector for every container kind** — swimlanes, boxes, groups,
  notes now show an `ObjectPanel` with rename / style / delete. Patch
  helpers: `setSwimlaneName`, `removeSwimlane`, `setBoxLabel`, `setBoxStyle`,
  `removeBox`, `setGroupName`, `removeGroup`, `setNoteText`, `setNoteTarget`,
  `removeNote`.
- **Parse-error SVG card** — `render_svg` on a dicegram with parse errors
  now emits a visible "Dicegram could not be rendered" card with the first
  error message, instead of a 100×100 empty SVG.
- **Global keybindings** — Ctrl+N / Ctrl+O / Ctrl+E / Ctrl+B / Ctrl+. /
  Ctrl+F in addition to the existing Ctrl+S and Ctrl+Z.
- **`beforeunload` guard** when the dicegram is dirty.
- **`?next=` round-trip** — protected routes redirect to
  `/login?next=<path>`; login page consumes the `next` query.
- **Public viewer "Copy DSL"** button alongside Copy link / Download SVG.
- **Copy-shape at viewport center** — new shapes from the Insert toolbar
  now pin at the canvas viewport center (via a tiny `ViewportRegister`
  component that calls `useSvelteFlow().screenToFlowPosition`) rather than
  piling on at layout origin.
- **Hard-reset dev runner** (`reset-dev.bat`) — kills ports 8000 and
  5173-5180, nukes orphan uvicorn / vite / esbuild workers, restarts both
  servers, opens the browser.
- **`UX_AUDIT.md`** — running log of UX-audit findings (backend bugs +
  UX friction + priority order).

### Changed
- **Connectors are orthogonal only** — no diagonals, no curves. Both the
  canvas (`obstacle-routing.ts` `orthogonalL` + straight-line
  `polylineToPath`) and backend SVG export (`export_svg.py`) emit pure
  H/V segments with a single elbow on the long leg.
- **`<SvelteFlow>` now receives `edgeTypes`** so `type: 'smart'` actually
  resolves to our `SmartEdge` component — previously it was falling back
  to xyflow's default bezier curve despite `edgeTypes` being declared in
  Canvas. This is what caused the visible curves even after the routing
  fix landed.
- **Landing page is responsive** — title & tagline scale down at narrow
  viewports, feature cards break to 1 / 2 / 3 columns, everything wraps
  with `min-w-0 break-words` so text never clips under zoom.
- **Default editor template** is now `flowchart` (was `meta`, a
  self-referential diagram that was the hardest possible intro).
- **`type:end` without an explicit `step:N`** is now assigned
  `max(step)+1` instead of collapsing onto step 0 next to `type:start`.
- **Timestamps** in CRUD / share responses now serialize with a `Z` suffix
  so frontend `new Date(...)` treats them as UTC.
- **Vite dev server** is pinned to `5173` with `strictPort: true` and
  `host: 127.0.0.1` so it can't silently drift up the port range.

### Fixed
- `backend/diagram.db` renamed to `backend/dicegram.db`; `.env` /
  `.env.example` follow suit (completing the rename recorded in project
  memory on 2026-04-18).
- Public `/api/shares/{slug}/svg` no longer returns a 68-byte empty SVG
  when the DSL has parse errors.
- `svelte-check` introduced-this-session warnings cleared: tree-root
  `role="tree"` has `tabindex=-1`; `$state` initial-`source` capture gets
  an explicit `svelte-ignore`.

### Removed
- Static "live example" SVG on the landing page — replaced by the real
  embedded editor (no point running two rendering stacks for the same
  thing).

---

## [4.0.0] — 2026-04-18

Full rewrite as a web app. Dicegram.

### Added
- FastAPI + SQLModel + SQLite backend: `/api/auth/{signup,login,logout,me}`,
  `/api/dicegrams` CRUD, `/api/render`, `/api/export/svg`,
  `/api/dicegrams/{id}/share` + `/api/shares/{slug}` + `/api/shares/{slug}/svg`.
- SvelteKit 2 + Svelte 5 + Tailwind v4 + Svelte Flow + CodeMirror 6
  frontend with auth-gated editor, dicegram browser, and public viewer.
- Dicegram list at `/dicegrams` with thumbnails (server-rendered SVG),
  rename, delete, share.
- Scene tree with Godot-style drag-and-drop (before/into/after zones,
  cycle prevention).
- Self-healing DSL compiler (`backend/app/dsl/compiler.py`) that trims
  trailing whitespace, snaps pinned positions, drops dangling edge refs,
  renames duplicate nodes, and shifts co-located pinned siblings. Returns
  `normalized_source` + `source_changed` so the client can show an inline
  Undo toast.
- 7 color schemes (default-dark, light, solarized-dark, solarized-light,
  dracula, gruvbox, high-contrast).

### Changed
- Product name from "Diagram Editor" to "Dicegram"; source files are
  "dicegrams". Class/type/router/table names are `Dicegram` /
  `dicegrams`.

### Archived
- Desktop PySide6 app (`diagram_app.py`, `run.py`) preserved on tag
  `v3.0-desktop-final` and branch `archive/pyside-desktop`.

---

## [3.0.1] — 2026-04-13

### Fixed
- Containment logic for objects inside swimlanes and boxes
- Port-based edge routing — connections now attach to nearest port instead of node center
- Settings directives (`setting node_width 140`, etc.) now properly sync between code and settings panel

## [3.0.0] — 2026-04-13

### Added
- Complete rewrite using PySide6 (Qt) — replaces tkinter version
- QGraphicsScene-based rendering with DiagramNode and DiagramEdge items
- Bidirectional editing: drag nodes to move (writes `@(x,y)` to code), drag ports to connect (writes connection to code)
- 8 shape types: rect, rounded, diamond, circle, parallelogram, hexagon, cylinder, stadium
- 5 connection types: `->`, `-->`, `==>`, `---`, `-.-` with labels, hints, conditions, and weights
- Swimlanes, boxes (sub-containers), groups (visual overlays), and notes
- Step-based layout: same step number = same row/column (parallel placement)
- Rich attributes: type, owner, status, tags, priority, id — with visual effects (dashed for draft, red for blocked, strikethrough for deprecated, checkmark for complete)
- 7 color schemes: Default, Blueprint, Warm, Monochrome, Dark, Synthwave, Forest
- 4 layout directions: top-to-bottom, left-to-right, bottom-to-top, right-to-left
- Filter/search system with structured queries (type:, owner:, tags:, status:, step:, free text, AND/OR)
- 3 interaction modes: Select (V), Pan (H), Connect (C)
- Syntax-highlighted code editor with line numbers, error gutter, and find/replace
- Drawing palette for inserting shapes and connectors via click
- Export to PDF (fpdf2), SVG, PNG, and clipboard
- `.dgm` save format (JSON with version, code, settings) and `.txt` (raw DSL)
- LLM prompt generator (Help > Copy LLM Prompt) for AI-assisted diagram creation
- Node auto-sizing to fit text content
- Snap-to-grid (10px) on all drag operations
- Standalone executable build via PyInstaller

### Changed
- Architecture: single-file design (`diagram_app.py`) — all code in one place by design

### Previous Versions
Versions 1.x (HTML/JS with CodeMirror + dagre) and 2.x (Python/tkinter) were not formally tracked. Version 3.0 is a ground-up rewrite.
