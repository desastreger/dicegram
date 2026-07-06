#!/usr/bin/env bash
# One-shot deploy helper for a fresh VPS.
# Usage (on the VPS, after `git clone` and `cd dicegram`):
#   ./deploy.sh            # app only, listens on 127.0.0.1:8000
#   ./deploy.sh --caddy    # app + Caddy auto-TLS on :80/:443 (needs DOMAIN in .env)

set -euo pipefail

cd "$(dirname "$0")"

log()  { printf '\033[1;34m→\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m✗\033[0m %s\n' "$*" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || fail "docker is not installed. Install Docker Engine first."
docker compose version >/dev/null 2>&1 || fail "docker compose plugin not found."

USE_CADDY=0
if [ "${1:-}" = "--caddy" ]; then
    USE_CADDY=1
fi

# ─── .env bootstrap ────────────────────────────────────────────────────────
if [ ! -f .env ]; then
    log "Creating .env from .env.example"
    cp .env.example .env
    SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))" 2>/dev/null \
             || openssl rand -base64 48 | tr -d '\n/=+' | cut -c1-64)
    tmp=$(mktemp)
    sed "s#^SECRET_KEY=.*#SECRET_KEY=${SECRET}#" .env > "$tmp" && mv "$tmp" .env
    chmod 600 .env
    ok ".env created with a generated SECRET_KEY. Review it before going live."
fi

# ─── Validate .env ─────────────────────────────────────────────────────────
if ! grep -Eq '^SECRET_KEY=.{16,}$' .env; then
    fail "SECRET_KEY in .env is missing or too short. Generate one with: python3 -c 'import secrets; print(secrets.token_urlsafe(48))'"
fi
if grep -Eq '^SECRET_KEY=replace-me' .env; then
    fail "SECRET_KEY in .env is still the placeholder. Edit .env and set a real value."
fi

if [ "$USE_CADDY" = "1" ]; then
    if ! grep -Eq '^DOMAIN=[^[:space:]]+\.[^[:space:]]+$' .env; then
        fail "--caddy requires DOMAIN=your.domain.tld in .env"
    fi
    if ! grep -Eq '^ACME_EMAIL=[^@[:space:]]+@[^@[:space:]]+$' .env; then
        fail "--caddy requires ACME_EMAIL=you@domain.tld in .env (used for Let's Encrypt)"
    fi
    DOMAIN=$(grep -E '^DOMAIN=' .env | head -1 | cut -d= -f2-)
    ok "Caddy profile enabled for domain: $DOMAIN"
fi

PROFILE_ARGS=()
if [ "$USE_CADDY" = "1" ]; then
    PROFILE_ARGS=(--profile caddy)
fi

log "Building image (first build on a fresh VPS takes 3–5 minutes)…"
docker compose "${PROFILE_ARGS[@]:-}" build

log "Starting services…"
docker compose "${PROFILE_ARGS[@]:-}" up -d

log "Waiting for health check (up to 90s)…"
healthy=0
for i in $(seq 1 45); do
    status=$(docker inspect -f '{{.State.Health.Status}}' dicegram 2>/dev/null || echo "missing")
    case "$status" in
        healthy)  healthy=1; break ;;
        unhealthy)
            printf '\n'
            docker compose "${PROFILE_ARGS[@]:-}" logs --tail=80 dicegram
            fail "dicegram is unhealthy — see logs above."
            ;;
    esac
    printf '.'
    sleep 2
done
printf '\n'

if [ "$healthy" != "1" ]; then
    docker compose "${PROFILE_ARGS[@]:-}" logs --tail=80 dicegram
    fail "dicegram did not become healthy in 90s — see logs above."
fi
ok "dicegram is healthy"

docker compose "${PROFILE_ARGS[@]:-}" ps

if [ "$USE_CADDY" = "1" ]; then
    ok "Visit https://$DOMAIN — Caddy will fetch a Let's Encrypt cert on first request."
else
    ok "App is listening on http://127.0.0.1:8000 — put your reverse proxy in front of it."
fi
