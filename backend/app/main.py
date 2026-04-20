import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from .config import settings
from .db import init_db
from .rate_limit import limiter
from .routers import auth, dicegrams, export, render, shares


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Dicegram API", lifespan=lifespan)

# Rate limiting — defaults are generous; per-endpoint limits live on the
# individual route decorators. See app/rate_limit.py for the shared limiter.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="dicegram_session",
    max_age=settings.session_max_age_seconds,
    same_site="lax",
    https_only=settings.session_cookie_secure,
)

app.include_router(auth.router)
app.include_router(dicegrams.router)
app.include_router(render.router)
app.include_router(export.router)
app.include_router(shares.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# --- Static frontend (optional) --------------------------------------------
# When FRONTEND_DIST points at a built SvelteKit (adapter-static) directory,
# mount the hashed `_app/` assets and fall back to index.html for SPA routes.
# API requests (/api/*) are handled by routers above and take precedence.

FRONTEND_DIST = os.environ.get("FRONTEND_DIST", "/app/frontend_dist")
_dist = Path(FRONTEND_DIST)

if _dist.is_dir() and (_dist / "index.html").is_file():
    # Hashed asset directory from SvelteKit's adapter-static.
    _app_dir = _dist / "_app"
    if _app_dir.is_dir():
        app.mount("/_app", StaticFiles(directory=_app_dir), name="sveltekit_app")

    _index = _dist / "index.html"

    @app.get("/{path:path}", include_in_schema=False)
    async def spa_fallback(path: str, request: Request):
        if path.startswith("api/"):
            return JSONResponse({"detail": "not found"}, status_code=404)
        # Serve any concrete file from the dist directory directly.
        candidate = (_dist / path).resolve()
        try:
            candidate.relative_to(_dist.resolve())
        except ValueError:
            return FileResponse(_index)
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_index)
