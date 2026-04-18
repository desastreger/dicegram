from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .db import init_db
from .routers import auth, dicegrams, export, render, shares


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Dicegram API", lifespan=lifespan)

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
