# Dicegram

Web app for turning plain text into living architecture diagrams — "Dicegrams". Accounts, saved
dicegrams, shareable URLs.

The DSL is the canonical source of truth: every visual property of every object lives in the
source file (like a Godot `.tscn`). The code editor, canvas and inspector are three windows
into the same text — edits on one surface immediately propagate to the others.

## Stack

- **Backend:** FastAPI + SQLModel + SQLite (Postgres in prod)
- **Frontend:** SvelteKit + Svelte 5 + TailwindCSS + TypeScript + Svelte Flow + CodeMirror 6
- **Auth:** signed session cookies, Argon2 password hashing

## Local development

### Backend (port 8000)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows (bash: source .venv/Scripts/activate)
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend (port 5173)

```bash
cd frontend
npm run dev
```

Vite proxies `/api/*` → `http://localhost:8000`, so frontend and backend share an origin in dev.
Open http://localhost:5173.

## Legacy desktop app

The original PySide6 desktop editor lives in `diagram_app.py` + `run.py`, preserved on tag
`v3.0-desktop-final` and branch `archive/pyside-desktop`. See [GUIDE.md](GUIDE.md) for the DSL
reference — still the source of truth for the grammar the web app implements.

```bash
pip install -r requirements.txt  # PySide6, fpdf2
python run.py
```
