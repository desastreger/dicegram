import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from .config import settings
from .db import init_db
from .rate_limit import limiter
from .routers import auth, dicegrams, export, render, shares

# Hard cap on request body size, checked via Content-Length before the
# body is read. Generous headroom over `settings.max_source_bytes` (1
# MiB) for JSON escaping overhead on the largest legitimate payload.
# Rejects oversized bodies (e.g. against the un-rate-limited-by-endpoint
# /api/render) before FastAPI buffers the whole thing into memory.
MAX_BODY_BYTES = 2 * 1024 * 1024


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                too_big = int(content_length) > MAX_BODY_BYTES
            except ValueError:
                too_big = False
            if too_big:
                return JSONResponse(
                    {"detail": "request body too large"}, status_code=413
                )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Baseline security headers on every response. This app is sometimes
    deployed standalone (no Caddy/nginx in front), so it can't rely on a
    reverse proxy to set these."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if settings.session_cookie_secure:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
            )
        return response


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

# SlowAPIMiddleware makes `limiter.default_limits` ("120/minute") apply to
# routes declared directly on `app` (e.g. /api/health) that carry no
# `@limiter.limit(...)` of their own. NOTE: with the installed fastapi
# (routes registered via `include_router` are wrapped in an internal
# `_IncludedRouter` that slowapi 0.1.x's route-matching in
# `SlowAPIMiddleware.dispatch` doesn't see — see slowapi/middleware.py
# `_find_route_handler`), this middleware does NOT reach any router-module
# endpoint. Every endpoint that needs a limit (signup/login/hint_lookup,
# export, render, …) therefore carries its own explicit
# `@limiter.limit(...)` decorator, which works regardless of this gap —
# do not assume "no decorator" means "uncapped" without checking this.
app.add_middleware(SlowAPIMiddleware)

# Middleware order: Starlette runs the LAST-added middleware outermost
# (first on the request, last on the response), so BodySizeLimit — which
# should reject before anything else even looks at the body — is added
# last. Security headers just need to wrap every response.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BodySizeLimitMiddleware)

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
