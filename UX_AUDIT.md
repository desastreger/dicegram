# Dicegram UX audit — 2026-04-18

Combined findings from (a) a UX-expert code review, (b) backend API smoke
tests via `curl`, and (c) rendering four example dicegrams at escalating
proficiency through the backend and visually inspecting the SVGs.

Examples authored: `tmp-ux-examples/0{1,2,3,4}-*.dgm` (+ rendered `.svg`).

## Status (end of session 2026-04-18)

Resolved this session — see CHANGELOG 4.1.0 for details:

- B1 — DB rename to `dicegram.db`; `.env` / `.env.example` updated.
- B2 — Timestamps serialize as UTC with `Z` suffix.
- B3 — Parse-error SVG card replaces the empty 100×100 square.
- B5 — `type:end` without explicit step is placed at `max(step)+1`.
- Item 1 — Dblclick node → focus Inspector label.
- Item 2 — Default template is now `flowchart`.
- Item 3a — `beforeunload` guard when dirty.
- Item 3b — Debounced autosave (2 s).
- Item 4 — `?next=` login round-trip.
- Item 5 — Share / Revoke popover in editor toolbar.
- Item 6 — Landing embeds the real mini editor; `?demo=1` local-only mode.
- Item 7 — New shapes inserted at viewport center.
- Item 8 — Ctrl+N/O/E/B/./F keybindings.
- Item 9 — Edge inspector panel + every container kind (swimlane/box/group/note)
  gets an Inspector panel.
- Orthogonal connectors everywhere — no diagonals, no curves.
- `reset-dev.bat` dev runner; vite pinned to 5173.

Still open:

- B4 — Pydantic `EmailStr` rejects `.local` TLD; signup form surfaces the
  raw 422. Reword in the form.
- Thumbnail fallback on the `/dicegrams` list when the server SVG 500s.
- Filter-input help popover / chips.
- Shape picker semantic tooltips (Visio names).
- Multi-select delete in tree; line→node reverse highlight.
- PDF export; step-band rendering.

---

## Backend / runtime bugs

| id | severity | area | finding |
|----|---|---|---|
| B1 | high | config | `backend/.env` and `backend/.env.example` still say `diagram.db`; `config.py:8` defaults to `dicegram.db` and memory records the rename. Runtime currently uses stale DB file. |
| B2 | medium | API serialization | CRUD responses serialize datetimes without a timezone suffix (e.g. `"2026-04-18T17:57:12.208313"`). The backend writes `datetime.now(timezone.utc)` on update but SQLite loses the tzinfo. Frontend `new Date(...)` parses as local time → visible clock drift. |
| B3 | high | share viewer | `POST /api/shares/{slug}/svg` renders `render_svg(parse(source))` with no error handling. A dicegram whose source fails to parse returns `<svg viewBox="0 0 100 100"></svg>` (68 bytes) with HTTP 200. Public viewer shows a blank square. `shares.py:87-95`, `export.py:14-18`. |
| B4 | low | signup | `pydantic.EmailStr` rejects `.local` TLD (and other reserved-TLD emails). If the signup page bubbles the raw 422 payload, users see `"The part after the @-sign is a special-use or reserved name..."`. Consider catching and rephrasing in the form. |
| B5 | medium | layout | A `type:end` node **without** an explicit `step:N` attr is placed at step 0 alongside `type:start`. Visible in `02-intermediate.svg`: `done` ends up on the top row next to `start` and the final edge loops diagonally across the whole diagram. Layout should default `type:end` to `max(step)+1`. |

## UX blockers & friction (from the audit agent)

Top 10 prioritized items:

1. **Dblclick on a canvas node does nothing.** Figma/Miro users expect inline label edit. `ShapeNode.svelte` has no `ondblclick`; `Canvas.svelte:416-422` only selects. Fix: open Inspector + focus label textarea on dblclick.
2. **Default editor template is the meta-dicegram** (`templates.ts:128`). First-time users land on the hardest possible example. Change `DEFAULT_TEMPLATE_ID` to `flowchart`.
3. **No autosave, no beforeunload guard** (`editor/+page.svelte`). Closing the tab discards unsaved work. Add `beforeunload` warn when `dirty`; debounced autosave once saved.
4. **`/editor?id=NN` drops the id on login redirect** (`editor/+page.svelte:55-57`, `login`). A teammate's link goes to `/login` and loses context. Needs a `?next=` round-trip.
5. **Share link only reachable from `/dicegrams`** — no Share button in the editor toolbar. `shares.py` revoke endpoint exists but has no UI at all.
6. **Landing page** (`+page.svelte:44-64`) has no preview, no "try without signup" sandbox.
7. **Insert-shape lands at (0,0)/layout default**, overlaps the last node. Power users expect insert near viewport center or beside the selected node.
8. **Sparse keybindings** — only Ctrl+S, Ctrl+Z, Ctrl+Shift+Z, Delete. Missing: Ctrl+N/O/E, Ctrl+B (tree), Ctrl+. (inspector), Ctrl+F (filter), `/` (quick jump).
9. **Edges are not editable in the Inspector** — selection filters to `kind === 'shape'`. Label, color, kind can only be changed in DSL. `Canvas.svelte:416`.
10. **Public viewer has no "Copy DSL" button** — only Copy link / Download SVG. `d/[slug]/+page.svelte:104-123`.

Secondary items worth noting:

- Delete confirmation button reuses focus, double-click lands a real delete.
- The "undo stash" toast and the global Ctrl+Z undo are two independent stacks — documented nowhere, the user can lose data if two deletes happen in <5s.
- Filter input placeholder is dense (`"Filter  (owner:alice #tag …)"`) — needs help popover or chips.
- Thumbnails via `/api/dicegrams/{id}/svg` have no fallback; a parse error shows a broken-image icon.
- Shape picker uses technical names (hexagon, stadium, cylinder) without Visio-style semantic tooltips.

## Positive surprises (worth preserving)

- Canonical DSL + self-healing compiler with "Undo" toast.
- Selecting a canvas node reveals & highlights its DSL line (`CodeEditor.svelte:206`).
- Godot-style tree drag-and-drop with before/into/after zones and cycle prevention.
- Inspector live shape preview.
- Inline rename in dicegram list with Enter/Escape.
- Dirty-dot in tab title.

## Proposed fix order

**Trivial (fix now):**
- B1 — point `.env(.example)` at `dicegram.db`.
- Item 2 — default template to `flowchart`.
- Item 10 — Copy DSL on public viewer.
- Item 3a — `beforeunload` warn when dirty.
- B3 — render an error SVG card when parse fails (share viewer).

**Cheap (fix soon):**
- B2 — ensure UTC Z suffix on timestamps.
- Item 4 — `?next=` login round-trip.
- Item 8a — Ctrl+B toggle tree, Ctrl+. toggle inspector.
- Item 7 — insert shape at viewport center.
- Item 1 — dblclick node → focus Inspector label.

**Medium (needs design):**
- Item 5 — Share/revoke UI in editor toolbar.
- Item 9 — edge editing in Inspector (selection model change).
- B5 — step-band auto-assignment for `type:end` without step.
- Item 3b — actual autosave.

**Large (defer):**
- Item 6 — landing preview / try-without-signup.
