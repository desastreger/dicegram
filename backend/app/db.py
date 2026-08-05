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

    _migrate_username_identity(inspector)

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


def _slug_from_email(email: str) -> str:
    """Derive a candidate username from an email local-part."""
    import re as _re

    local = (email or "").split("@")[0]
    slug = _re.sub(r"[^A-Za-z0-9_.-]", "", local).strip("._-")
    return slug or "user"


def _migrate_username_identity(inspector) -> None:
    """Move the login identifier from email to username.

    Runs once, and only on tables that still carry the old shape. The work:

      1. Backfill `username` for rows that never set one, derived from the
         email local-part and de-duplicated case-insensitively.
      2. Materialise `username_key` (case-folded) and put the uniqueness
         constraint on it.
      3. Make `email` nullable, so signup can stop collecting it.

    Existing accounts are NOT locked out — login accepts either identifier
    (routers/auth.py). Dropping `email` entirely is a separate, later change.

    SQLite cannot drop a NOT NULL constraint in place, so step 3 needs a
    table rebuild there. Two traps that cost a rollback to find:

      * `PRAGMA foreign_keys` is a NO-OP inside a transaction, so it has to
        be set on a raw connection before BEGIN. `dicegram.owner_id`
        references `user.id`, and this engine turns foreign keys ON for every
        connection (see the connect listener above), so DROP TABLE user
        fails outright without it.
      * The row count is asserted before the swap; a mismatch raises and the
        transaction rolls back, leaving the original table untouched.

    Postgres needs none of that — it can ALTER the constraints directly.
    """
    from sqlalchemy import text

    if "user" not in inspector.get_table_names():
        return
    cols = {c["name"] for c in inspector.get_columns("user")}
    if "username_key" in cols:
        return  # already migrated

    # ── Shared step 1: derive the usernames, in Python for readability.
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, email, username FROM \"user\"")).all()
    taken: set[str] = set()
    updates: list[tuple[str, str, int]] = []
    for uid, email, username in rows:
        base = (username or "").strip() or _slug_from_email(email or "")
        candidate, n = base, 2
        while candidate.casefold() in taken:
            candidate, n = f"{base}{n}", n + 1
        taken.add(candidate.casefold())
        updates.append((candidate, candidate.casefold(), uid))

    if not _is_sqlite:
        # Postgres: alter in place, no rebuild required.
        with _tolerant_ddl():
            with engine.begin() as conn:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN username_key VARCHAR'))
                for uname, ukey, uid in updates:
                    conn.execute(
                        text('UPDATE "user" SET username = :u, username_key = :k WHERE id = :i'),
                        {"u": uname, "k": ukey, "i": uid},
                    )
                conn.execute(text('ALTER TABLE "user" ALTER COLUMN email DROP NOT NULL'))
                conn.execute(text('ALTER TABLE "user" ALTER COLUMN username SET NOT NULL'))
                conn.execute(text('ALTER TABLE "user" ALTER COLUMN username_key SET NOT NULL'))
                conn.execute(text(
                    'CREATE UNIQUE INDEX IF NOT EXISTS ix_user_username_key ON "user" (username_key)'
                ))
        return

    # ── SQLite: rebuild the table.
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute("PRAGMA foreign_keys=OFF")   # must precede BEGIN to take effect
        cur.execute("BEGIN")
        try:
            before = cur.execute("SELECT COUNT(*) FROM user").fetchone()[0]

            if "username_key" not in cols:
                cur.execute("ALTER TABLE user ADD COLUMN username_key VARCHAR")
            for uname, ukey, uid in updates:
                cur.execute(
                    "UPDATE user SET username = ?, username_key = ? WHERE id = ?",
                    (uname, ukey, uid),
                )

            cur.execute("""
                CREATE TABLE user_migrated (
                    id INTEGER NOT NULL PRIMARY KEY,
                    username VARCHAR NOT NULL,
                    username_key VARCHAR NOT NULL,
                    password_hash VARCHAR NOT NULL,
                    email VARCHAR,
                    password_hint VARCHAR,
                    created_at DATETIME,
                    branding_palette JSON,
                    palette_presets JSON,
                    palette_locked BOOLEAN DEFAULT 0
                )
            """)
            cur.execute("""
                INSERT INTO user_migrated
                    (id, username, username_key, password_hash, email, password_hint,
                     created_at, branding_palette, palette_presets, palette_locked)
                SELECT id, username, username_key, password_hash, email, password_hint,
                       created_at,
                       COALESCE(branding_palette, '{}'),
                       COALESCE(palette_presets, '{}'),
                       COALESCE(palette_locked, 0)
                FROM user
            """)
            after = cur.execute("SELECT COUNT(*) FROM user_migrated").fetchone()[0]
            if after != before:
                raise RuntimeError(
                    f"username migration would lose rows ({before} -> {after}); rolled back"
                )

            cur.execute("DROP TABLE user")
            cur.execute("ALTER TABLE user_migrated RENAME TO user")
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_user_username_key ON user (username_key)"
            )
            cur.execute("CREATE INDEX IF NOT EXISTS ix_user_username ON user (username)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_user_email ON user (email)")
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise
    finally:
        try:
            raw.cursor().execute("PRAGMA foreign_keys=ON")
        finally:
            raw.close()


def init_db() -> None:
    with _tolerant_ddl():
        SQLModel.metadata.create_all(engine)
    _ensure_schema()


def get_session():
    with Session(engine) as session:
        yield session
