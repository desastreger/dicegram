# Dicegram

**Text-first diagram editor with a living DSL.** Edit in code, canvas,
scene tree, and inspector — all four stay in sync. Self-hostable or use
the hosted instance.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](./LICENSE)
[![Live demo](https://img.shields.io/badge/live-dicegram.desastreger.cloud-22c55e)](https://dicegram.desastreger.cloud)

---

## Try it

- **Hosted**: **[https://dicegram.desastreger.cloud](https://dicegram.desastreger.cloud)**
- **No-signup demo**: [dicegram.desastreger.cloud/editor?demo=1](https://dicegram.desastreger.cloud/editor?demo=1) (runs entirely in your browser, saves to `localStorage`)

## Why Dicegram

| | Dicegram | Mermaid | draw.io | Excalidraw |
|---|---|---|---|---|
| Text is the source of truth | ✓ | ✓ | — | — |
| Edit in both text **and** visual, staying in sync | ✓ | — | ✓ | ✓ |
| Orthogonal obstacle-routed connectors | ✓ | partial | ✓ | — |
| Visio CSV round-trip | ✓ | — | partial | — |
| Self-host with one command | ✓ | n/a | ✓ | ✓ |
| Hosted + self-hostable under the same source | ✓ (AGPL) | ✓ | ✓ | ✓ |

## Features

- **Four synced surfaces** — code editor (DSL), canvas (Svelte Flow), scene
  tree (Godot-style drag-to-reparent), inspector (every object kind has a
  panel).
- **8 shapes** — rect, rounded, diamond, circle, parallelogram, hexagon,
  cylinder, stadium. Plus swimlanes, boxes, groups, and notes.
- **5 connector styles** — `->`, `-->`, `==>`, `---`, `-.-`. All orthogonal,
  all obstacle-avoiding via an A\* grid router.
- **Exports** — SVG, PNG, PDF, standalone HTML, Visio Data Visualizer CSV
  (round-trips to Microsoft Visio). Also clipboard DSL/SVG and an LLM-prompt
  template for AI-assisted authoring.
- **Accounts + shares** — Argon2 password hashing, signed-cookie sessions,
  read-only `/d/{slug}` share links you can revoke.
- **Autosave** — 2 s debounced `PUT`, plus `Ctrl+S` for the impatient.
- **Self-healing compiler** — trims trailing whitespace, snaps pinned
  positions to the grid, drops dangling refs, renames duplicates. Every
  normalization surfaces an inline Undo toast.

## DSL snippet

```
direction: top-to-bottom

swimlane "Backend"
swimlane "Frontend"

[circle] request "Request" type:start swimlane:"Frontend" step:0
[rect]   api     "FastAPI"          swimlane:"Backend"  step:1
[cylinder] db    "SQLite"           swimlane:"Backend"  step:2
[circle] reply   "Response" type:end swimlane:"Frontend" step:3

request -> api "POST /dicegrams"
api --> db "write"
db ==> api
api -> reply
```

Full grammar, shape types, attributes, swimlanes, boxes, groups, and notes:
see [**GUIDE.md**](./GUIDE.md). Ready-made examples live in
[`examples/`](./examples).

## Self-host in one command

You need Docker Engine + the Compose plugin on a box you control.

```bash
git clone https://github.com/desastreger/dicegram.git
cd dicegram
chmod +x deploy.sh docker-entrypoint.sh
./deploy.sh --caddy    # with built-in Let's Encrypt TLS (needs a domain)
./deploy.sh            # app-only, behind your own reverse proxy
```

`deploy.sh` bootstraps `.env` with a generated `SECRET_KEY`, validates
required variables (`DOMAIN`, `ACME_EMAIL` for the Caddy profile), builds
the image, starts the stack, and polls the healthcheck. The app persists
to a named Docker volume at `/data`; SQLite is fine for small deployments,
or swap to Postgres via `DATABASE_URL`.

Tuned out of the box for a 4 vCPU / 16 GB VPS. See
[`docker-compose.yml`](./docker-compose.yml) for resource limits and the
[`Caddyfile`](./Caddyfile) for the reverse-proxy config.

### Running on Postgres instead of SQLite

SQLite on a named Docker volume is the default and is fine for personal
and small-team use. If you want multi-instance deploys, off-box backups,
or encryption at rest, point the app at a Postgres server:

1. `pip install psycopg[binary]>=3.1` (or add it to
   `backend/requirements.txt` and rebuild).
2. Edit `.env`:
   ```
   DATABASE_URL=postgresql+psycopg://user:pass@db-host:5432/dicegram
   ```
3. Restart the container. The app runs `SQLModel.metadata.create_all` on
   startup, so a fresh database picks up the schema automatically. For
   already-populated SQLite instances, dump and restore with
   [pgloader](https://pgloader.readthedocs.io/en/latest/) or a bespoke
   `sqlite3 .dump | psql` pipeline — the column types line up 1:1.
4. The idempotent `_ensure_schema()` ALTER-TABLE pass in
   [`backend/app/db.py`](./backend/app/db.py) also works on Postgres —
   it only runs when a known column is missing.

Once on Postgres, `WEB_CONCURRENCY` can safely scale past 3; SQLite's
single-writer limit is the reason that's the recommended cap.

## Need it hosted for you?

If you'd rather not run infrastructure, use the hosted instance at
**[dicegram.desastreger.cloud](https://dicegram.desastreger.cloud)**, or
reach out via **[desastregerstudio.com](https://desastregerstudio.com)**
for a managed deployment, SLA, or commercial license (see *Licensing*
below).

## Local development

```bash
# Backend (FastAPI on :8000)
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Frontend (Vite on :5173)
cd frontend
npm install
npm run dev
```

Vite proxies `/api/*` → `http://localhost:8000`, so both live on the same
origin. Open http://localhost:5173.

## Architecture

- **Backend**: FastAPI + SQLModel + SQLite (WAL + multi-worker ready),
  Argon2 password hashing, itsdangerous-signed session cookies.
- **Frontend**: SvelteKit 2 + Svelte 5 (runes) + TailwindCSS v4 +
  TypeScript + `@xyflow/svelte` + CodeMirror 6. Built with
  `@sveltejs/adapter-static` — the backend serves the SPA as static files.
- **Single container**: multi-stage Dockerfile (Node builder → Python
  runtime). Optional Caddy sidecar for auto-TLS.

```
backend/
  app/
    dsl/          parser, compiler (self-heal), layout, svg export, tree
    routers/      auth, dicegrams, render, export, shares
    main.py  models.py  db.py  config.py  deps.py  security.py
  requirements.txt
frontend/
  src/
    lib/          api, auth, render, patch, themes, …
    routes/
      +page.svelte              landing + embedded mini editor
      login/ signup/ dicegrams/ d/[slug]/
      editor/                   Canvas, CodeEditor, Inspector, TreePanel,
                                Toolbar, SettingsPane, EdgePanel,
                                ObjectPanel, SmartEdge, ShapeNode, …
examples/         *.dgm / *.txt ready-to-load diagrams
deploy.sh  Dockerfile  docker-compose.yml  Caddyfile
GUIDE.md   CHANGELOG.md   CONTRIBUTING.md   SECURITY.md
```

## Keyboard shortcuts

<details>
<summary>Global (outside CodeMirror)</summary>

| Shortcut | Action |
|---|---|
| Ctrl/Cmd+S | Save |
| Ctrl/Cmd+Z / Ctrl/Cmd+Shift+Z | Undo / redo |
| Ctrl/Cmd+N | New dicegram |
| Ctrl/Cmd+O | Open list |
| Ctrl/Cmd+E | Export SVG |
| Ctrl/Cmd+B | Toggle scene tree |
| Ctrl/Cmd+. | Toggle inspector |
| Ctrl/Cmd+F | Focus filter input |
| Double-click node | Focus label in inspector |
| Delete | Remove selected node |

</details>

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Security reports go to the
address in [SECURITY.md](./SECURITY.md). Release notes live in
[CHANGELOG.md](./CHANGELOG.md).

## Licensing

Dicegram is **GNU AGPL-3.0-or-later** — you can use, modify, and self-host
freely. If you run a modified version as a network service, you must
publish your modifications under AGPL-3.0 too.

If AGPL's copyleft doesn't fit your use case (e.g. you're embedding Dicegram
in a closed-source commercial product), a **commercial license** is
available — contact [desastregerstudio.com](https://desastregerstudio.com).

Third-party dependencies and their licenses are listed in
[THIRD_PARTY_LICENSES.md](./THIRD_PARTY_LICENSES.md).

## Archived desktop app

The original PySide6 desktop editor is preserved on tag
`v3.0-desktop-final` and branch `archive/pyside-desktop`. The web app
supersedes it; it's kept for history only.
