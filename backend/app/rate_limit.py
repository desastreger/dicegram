"""Shared slowapi Limiter.

Uses the client IP (or the first hop in X-Forwarded-For when uvicorn is run
with --proxy-headers, which our docker-entrypoint.sh does) as the key.
In-memory storage — good enough for single-container deployments. Swap to
Redis via `storage_uri` if we ever scale out horizontally.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address


# Default limit is applied to every rate-limited route that doesn't set its
# own. Chosen to be generous enough for normal interactive use.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    headers_enabled=True,
)
