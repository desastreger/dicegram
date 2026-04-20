# syntax=docker/dockerfile:1.7

# ─── Stage 1: build the SvelteKit SPA ─────────────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /src

# Install dependencies first so layer caches survive source edits.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN npm run build


# ─── Stage 2: Python runtime ──────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FRONTEND_DIST=/app/frontend_dist \
    DATA_DIR=/data \
    PORT=8000 \
    WEB_CONCURRENCY=2

WORKDIR /app

# curl for healthchecks, gosu to drop privileges after chowning the volume.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl gosu \
 && rm -rf /var/lib/apt/lists/* \
 && gosu nobody true

# Backend deps. Wheels are available for argon2-cffi on slim-bookworm.
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Application code.
COPY backend/app ./app

# Built frontend from stage 1.
COPY --from=frontend-build /src/build ./frontend_dist

# Non-root runtime user. Entrypoint runs as root briefly to chown /data,
# then execs uvicorn as this user.
RUN useradd --create-home --shell /bin/bash dicegram \
 && chown -R dicegram:dicegram /app

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/api/health" || exit 1

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
