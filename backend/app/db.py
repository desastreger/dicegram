from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from .config import settings

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


def _ensure_schema() -> None:
    """Schema migrations for already-deployed instances that predate new
    columns. `SQLModel.metadata.create_all` adds tables but never ALTERs
    existing ones, so we hand-patch the couple of known drifts. Safe to
    run repeatedly — each statement is conditional on the column missing.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "user" not in inspector.get_table_names():
        return
    user_cols = {c["name"] for c in inspector.get_columns("user")}
    if "branding_palette" not in user_cols:
        with engine.begin() as conn:
            # SQLite accepts JSON as TEXT; SQLAlchemy JSON type stores JSON-
            # encoded strings either way. Default to an empty JSON object.
            conn.execute(text("ALTER TABLE user ADD COLUMN branding_palette JSON"))
            conn.execute(text("UPDATE user SET branding_palette = '{}' WHERE branding_palette IS NULL"))
    if "palette_presets" not in user_cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE user ADD COLUMN palette_presets JSON"))
            conn.execute(text("UPDATE user SET palette_presets = '{}' WHERE palette_presets IS NULL"))


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_schema()


def get_session():
    with Session(engine) as session:
        yield session
