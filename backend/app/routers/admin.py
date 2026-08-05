"""Admin-only instance stats, rendered as a Dicegram.

The numbers form a funnel — requests arrive, some become edits, some of
those become accounts, some of those save work, some of that gets shared —
and a funnel is a flowchart. So rather than build a chart library into the
app, this hands back a DSL document and lets Dicegram render its own stats.

Two sources, and they are deliberately different in kind:

  * The database knows totals that survive restarts (accounts, saved
    dicegrams, shares) and, via created_at, when accounts appeared.
  * Caddy's access log knows traffic. It stores no IP, User-Agent or
    Referer by design (see the Caddyfile), so nothing here can be broken
    down by person — only by what was requested and when.

If the log is not mounted or readable — a self-hosted instance behind its
own proxy, say — traffic figures come back as None and the diagram simply
omits those nodes rather than reporting zero, which would be a lie.
"""

from __future__ import annotations

import glob
import json
import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from ..config import settings
from ..db import get_session
from ..deps import current_admin
from ..models import Dicegram, Share, User

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Cap how much log we parse per request so a large log can't turn an admin
# page load into a multi-second CPU burn.
MAX_LOG_LINES = 200_000


class Stats(BaseModel):
    accounts: int
    dicegrams: int
    shares: int
    accounts_7d: int
    dicegrams_7d: int
    # None (not 0) when the access log is unavailable — see module docstring.
    requests_7d: int | None = None
    renders_7d: int | None = None
    exports_7d: int | None = None
    errors_7d: int | None = None
    renders_by_day: list[tuple[str, int]] = []
    top_paths: list[tuple[str, int]] = []
    log_available: bool = False
    dsl: str = ""


def _read_log(cutoff: float) -> list[dict] | None:
    files = sorted(glob.glob(settings.access_log_glob))
    if not files:
        return None
    rows: list[dict] = []
    for path in files:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if len(rows) >= MAX_LOG_LINES:
                        break
                    line = line.strip()
                    if not line or not line.startswith("{"):
                        continue
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    if float(rec.get("ts", 0)) >= cutoff:
                        rows.append(rec)
        except OSError:
            # Unreadable (permissions, mid-rotation) — treat as absent rather
            # than failing the whole page.
            continue
    return rows


def _fmt(n: int) -> str:
    return f"{n:,}"


def _build_dsl(s: Stats) -> str:
    """Render the funnel as a Dicegram document.

    No `step:` anywhere on purpose: rank derives from the arrows, which is
    both the shorthand we want to be dogfooding and one fewer thing to keep
    in sync when nodes are conditionally omitted.
    """
    lines = [
        "direction top-to-bottom",
        "setting color_scheme auto",
        "",
    ]
    edges: list[str] = []
    prev: str | None = None

    def add(node_id: str, shape: str, label: str, type_attr: str = "") -> None:
        nonlocal prev
        # Labels land inside a quoted DSL string; strip anything that would
        # terminate it early or be read as a token.
        label = label.replace('"', "").replace("\n", " ")
        t = f" type:{type_attr}" if type_attr else ""
        lines.append(f'[{shape}] {node_id} "{label}"{t}')
        if prev:
            edges.append(f"{prev} -> {node_id}")
        prev = node_id

    if s.log_available:
        add("req", "circle", f"{_fmt(s.requests_7d or 0)} requests in 7d", "start")
        add("edits", "rect", f"{_fmt(s.renders_7d or 0)} edits")
    else:
        add("req", "circle", "traffic log not mounted", "start")

    add("acc", "rect", f"{_fmt(s.accounts_7d)} new accounts")
    add("db", "cylinder", f"{_fmt(s.dicegrams)} dicegrams saved", "datastore")
    add("shared", "circle", f"{_fmt(s.shares)} shared links", "end")

    lines.append("")
    lines.extend(edges)

    # Totals hang off the side as a note rather than another rank, so the
    # funnel keeps reading as a single flow.
    lines.append(
        f'[note] totals "{_fmt(s.accounts)} accounts total, '
        f'{_fmt(s.dicegrams_7d)} dicegrams this week" target:db'
    )
    if s.log_available and (s.exports_7d or 0):
        lines.append(f'[note] exp "{_fmt(s.exports_7d or 0)} exports in 7d" target:shared')
    return "\n".join(lines) + "\n"


@router.get("/stats", response_model=Stats)
def stats(
    _admin: User = Depends(current_admin),
    session: Session = Depends(get_session),
) -> Stats:
    now = time.time()
    cutoff = now - 7 * 86400
    week_ago = __import__("datetime").datetime.fromtimestamp(
        cutoff, tz=__import__("datetime").timezone.utc
    )

    counts = Stats(
        accounts=session.exec(select(func.count()).select_from(User)).one(),
        dicegrams=session.exec(select(func.count()).select_from(Dicegram)).one(),
        shares=session.exec(select(func.count()).select_from(Share)).one(),
        accounts_7d=session.exec(
            select(func.count()).select_from(User).where(User.created_at >= week_ago)
        ).one(),
        dicegrams_7d=session.exec(
            select(func.count())
            .select_from(Dicegram)
            .where(Dicegram.created_at >= week_ago)
        ).one(),
    )

    rows = _read_log(cutoff)
    if rows is not None:
        counts.log_available = True
        counts.requests_7d = len(rows)
        counts.renders_7d = sum(1 for r in rows if r.get("request", {}).get("uri") == "/api/render")
        counts.exports_7d = sum(
            1 for r in rows if str(r.get("request", {}).get("uri", "")).startswith("/api/export")
        )
        counts.errors_7d = sum(1 for r in rows if int(r.get("status", 0)) >= 500)

        by_day: dict[str, int] = {}
        for r in rows:
            if r.get("request", {}).get("uri") != "/api/render":
                continue
            day = time.strftime("%Y-%m-%d", time.gmtime(float(r.get("ts", 0))))
            by_day[day] = by_day.get(day, 0) + 1
        counts.renders_by_day = sorted(by_day.items())

        paths: dict[str, int] = {}
        for r in rows:
            uri = str(r.get("request", {}).get("uri", "")).split("?")[0]
            if uri:
                paths[uri] = paths.get(uri, 0) + 1
        counts.top_paths = sorted(paths.items(), key=lambda kv: -kv[1])[:12]

    counts.dsl = _build_dsl(counts)
    return counts
