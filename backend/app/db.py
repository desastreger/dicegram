import logging
from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlmodel import Session, SQLModel, create_engine

from .config import settings

logger = logging.getLogger(__name__)

_is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if _is_sqlite else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA busy_timeout=5000")
        cur.close()


@contextmanager
def _tolerant_ddl():
    """Run a schema-migration step, swallowing "duplicate column" /
    "table already exists" / equivalent errors from a losing race against
    another uvicorn worker performing the SAME migration at boot. Every
    call site here is already gated by an `inspect()` check beforehand,
    so this only catches the narrow concurrent-worker window (both
    workers see "missing" before either commits its DDL) — a genuine
    schema problem still surfaces the next time the gating check runs.
    Covers both SQLite (OperationalError: duplicate column name / table
    ... already exists) and Postgres (ProgrammingError: column/relation
    already exists)."""
    try:
        yield
    except (OperationalError, ProgrammingError) as exc:
        logger.debug("schema migration step skipped (concurrent worker race?): %s", exc)


def _ensure_schema() -> None:
    """Schema migrations for already-deployed instances that predate new
    columns. `SQLModel.metadata.create_all` adds tables but never ALTERs
    existing ones, so we hand-patch the couple of known drifts. Safe to
    run repeatedly — each statement is conditional on the column missing,
    and `_tolerant_ddl` absorbs the case where a sibling worker won the
    same ALTER first.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "user" not in inspector.get_table_names():
        return
    user_cols = {c["name"] for c in inspector.get_columns("user")}
    if "branding_palette" not in user_cols:
        with _tolerant_ddl():
            with engine.begin() as conn:
                # SQLite accepts JSON as TEXT; SQLAlchemy JSON type stores JSON-
                # encoded strings either way. Default to an empty JSON object.
                conn.execute(text("ALTER TABLE user ADD COLUMN branding_palette JSON"))
                conn.execute(text("UPDATE user SET branding_palette = '{}' WHERE branding_palette IS NULL"))
    if "palette_presets" not in user_cols:
        with _tolerant_ddl():
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE user ADD COLUMN palette_presets JSON"))
                conn.execute(text("UPDATE user SET palette_presets = '{}' WHERE palette_presets IS NULL"))
    if "palette_locked" not in user_cols:
        with _tolerant_ddl():
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE user ADD COLUMN palette_locked BOOLEAN DEFAULT 0"))
                conn.execute(text("UPDATE user SET palette_locked = 0 WHERE palette_locked IS NULL"))
    # Username + password_hint added when SMTP-driven recovery was disabled
    # (see PR notes); both NULLABLE because pre-existing rows don't have
    # them and we never want a forced backfill.
    if "username" not in user_cols:
        with _tolerant_ddl():
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE user ADD COLUMN username VARCHAR"))
    if "password_hint" not in user_cols:
        with _tolerant_ddl():
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE user ADD COLUMN password_hint VARCHAR"))

    if "share" in inspector.get_table_names():
        with _tolerant_ddl():
            with engine.begin() as conn:
                # One-time dedup: earlier versions let concurrent
                # share-create requests race past a check-then-insert with
                # no DB constraint (routers/shares.py), producing more
                # than one Share row per dicegram_id — which also meant
                # "revoke" (delete .first()) could leave stale rows live.
                # Keep the oldest row (lowest id) per dicegram_id and drop
                # the rest; must run BEFORE the unique index below or its
                # creation would fail outright on any existing duplicates.
                conn.execute(text(
                    "DELETE FROM share WHERE id NOT IN ("
                    "SELECT MIN(id) FROM share GROUP BY dicegram_id"
                    ")"
                ))
                # Belt-and-suspenders: enforce one Share per Dicegram at
                # the DB level too (models.Share also declares
                # unique=True, which only takes effect for brand-new
                # tables via create_all — this covers upgrades).
                conn.execute(text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_share_dicegram_id_unique "
                    "ON share (dicegram_id)"
                ))


def init_db() -> None:
    with _tolerant_ddl():
        SQLModel.metadata.create_all(engine)
    _ensure_schema()


def get_session():
    with Session(engine) as session:
        yield session
