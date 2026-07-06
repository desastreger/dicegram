#!/bin/sh
set -eu

# Ensure the persistent data dir exists and is writable by the app user.
# Docker named volumes mount as root:root on first create; SQLite writes fail
# without this. Skip the chown if ownership is already correct to avoid
# touching WAL/SHM files on every restart.
DATA_DIR="${DATA_DIR:-/data}"
mkdir -p "$DATA_DIR"
target_uid=$(id -u dicegram)
current_uid=$(stat -c '%u' "$DATA_DIR" 2>/dev/null || echo 0)
if [ "$current_uid" != "$target_uid" ]; then
    chown -R dicegram:dicegram "$DATA_DIR"
fi

WORKERS="${WEB_CONCURRENCY:-3}"
PORT="${PORT:-8000}"

# Trust proxy headers only from the docker bridge range (where Caddy sits)
# and localhost. If you deploy without a proxy, set FORWARDED_IPS=127.0.0.1.
FORWARDED_IPS="${FORWARDED_IPS:-127.0.0.1,172.16.0.0/12}"

exec gosu dicegram uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers "$WORKERS" \
    --proxy-headers \
    --forwarded-allow-ips="$FORWARDED_IPS"
