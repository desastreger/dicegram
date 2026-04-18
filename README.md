# Dicegram

Web app for turning plain text into living architecture diagrams — "Dicegrams".
Accounts, saved dicegrams, shareable read-only URLs, and a demo mode that runs
entirely in the browser.

The DSL is the canonical source of truth: every visual property of every object
lives in the source file (like a Godot `.tscn`). The code editor, canvas,
inspector and scene tree are four windows into the same text — edits on one
surface propagate to the others immediately.

## Stack

- **Backend:** FastAPI + SQLModel + SQLite, Argon2 password hashing, signed
  session cookies.
- **Frontend:** SvelteKit 2 + Svelte 5 + TailwindCSS v4 + TypeScript + Svelte
  Flow (`@xyflow/svelte`) + CodeMirror 6.
- **Dev runner:** `reset-dev.bat` (Windows) — hard-resets both servers and the
  vite port range in one command.

## Local development

### One-shot reset (recommended)

```
reset-dev.bat
```

Kills anything on `:8000` and `:5173-5180`, restarts backend (`:8000`) +
frontend (`:5173`), opens the browser. Use this when ports get wedged after
crashes or leftover dev servers — faster and more reliable than `start-dev.bat`.

### Manual start

Backend on port 8000:

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows bash: source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend on port 5173:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api/*` → `http://localhost:8000`, so frontend and backend share
an origin in dev. Open http://localhost:5173.

## Key features

### Editing surface
- **Three-way sync** — code editor (DSL), canvas (Svelte Flow), inspector
  stay in sync at all times.
- **Inspector covers every object kind** — shapes, edges, swimlanes, boxes,
  groups, notes. Click anything on the canvas and its editable properties
  appear in the right pane.
- **Scene tree** — Godot-style drag-and-drop to reparent, Arrow keys to move
  among siblings.
- **Self-healing DSL** — `backend/app/dsl/compiler.py` normalizes the source
  (trim trailing whitespace, snap pinned positions to the grid, drop dangling
  refs, rename duplicates, shift co-located pinned siblings) on every render
  with an inline Undo toast.

### Connectors
- **Orthogonal only** — no diagonals, no curves. All connectors render as
  straight lines with L-shape elbows, on both the canvas (xyflow + custom
  `SmartEdge`) and the backend SVG export. When the edge path would cross
  an obstacle, an A\* grid router picks an orthogonal polyline around it.

### Persistence
- **Autosave** — logged-in users get a silent `PUT /api/dicegrams/{id}`
  2 s after the last edit. Ctrl+S still saves immediately.
- **Share / revoke** from the editor toolbar — read-only public URL at
  `/d/{slug}`.
- **Demo mode** at `/editor?demo=1` — no account required, source persists
  to `localStorage`. Save prompts to sign up instead of calling the API.

### Keybindings (global, outside CodeMirror)
| Shortcut | Action |
|---|---|
| Ctrl/Cmd+S | Save |
| Ctrl/Cmd+Z / Ctrl/Cmd+Shift+Z | Global undo / redo |
| Ctrl/Cmd+N | New dicegram |
| Ctrl/Cmd+O | Open dicegram list |
| Ctrl/Cmd+E | Export SVG |
| Ctrl/Cmd+B | Toggle scene tree |
| Ctrl/Cmd+. | Toggle inspector |
| Ctrl/Cmd+F | Focus filter input |
| Double-click node | Focus label in inspector |
| Delete | Remove selected node |

### Export
- `POST /api/export/svg` — backend-rendered SVG (source of truth for shares).
- Canvas → PNG rasterization, DSL copy, and an LLM-prompt template for
  AI-assisted DSL authoring.

## DSL reference

See [GUIDE.md](GUIDE.md) — DSL grammar, shape types, connection types,
attributes, swimlanes, boxes, groups, notes. The grammar is identical
between the web app and the (archived) desktop app.

## Archived desktop app

The original PySide6 desktop editor lives in `diagram_app.py` + `run.py`,
preserved on tag `v3.0-desktop-final` and branch `archive/pyside-desktop`.
The web app supersedes it and the desktop scripts will be removed once
parity is signed off.

## Layout of the repo

```
backend/
  app/
    dsl/          # parser, compiler (self-heal), layout, svg export, tree
    routers/      # auth, dicegrams, render, export, shares
    main.py, models.py, db.py, config.py, deps.py, security.py
  requirements.txt
frontend/
  src/
    lib/          # patch, render, auth, api, viewport-state, themes, …
    routes/
      +page.svelte              # landing with embedded mini editor
      login, signup, dicegrams, d/[slug]
      editor/                   # full editor: Canvas, CodeEditor, Inspector,
                                # TreePanel, Toolbar, Settings, EdgePanel,
                                # ObjectPanel, SmartEdge, ShapeNode, …
reset-dev.bat                   # hard-reset dev runner
start-dev.bat                   # first-time bootstrap + run
UX_AUDIT.md                     # running UX / bug log
GUIDE.md                        # DSL reference
```
