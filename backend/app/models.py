from datetime import datetime, timezone

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def fold_username(name: str) -> str:
    """Case-folded lookup key for a username.

    `casefold()` rather than `lower()` so non-ASCII handles compare the way a
    user expects (German ß folds to ss, for instance). Every read and write of
    `User.username_key` must go through this, or two accounts could differ only
    by case and both claim to be the same login.
    """
    return name.strip().casefold()


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # Login identifier. Unique and case-insensitively matched — see
    # `username_key`, which is what queries actually compare against.
    #
    # This replaced email as the identifier: Dicegram has no SMTP subsystem
    # at all, so an email address could never be used to contact anyone or
    # recover an account. Collecting one was a field of friction storing
    # personal data with no purpose.
    username: str = Field(index=True)
    # Case-folded copy of `username`, carrying the uniqueness constraint.
    # SQLite has no case-insensitive unique index without a collation or an
    # expression index, and an expression index cannot be expressed through
    # SQLModel — so the folded form is materialised instead. Always write it
    # via `fold_username()`; never set it by hand.
    username_key: str = Field(index=True, unique=True)
    password_hash: str
    # Legacy identifier, retained only so existing accounts can still sign in
    # during the transition. Nullable: signup no longer collects it, and it
    # is scheduled for removal once every active account has moved across.
    email: str | None = Field(default=None, index=True)
    # User-supplied "password reminder" string. There is no password reset —
    # no email means no reset link — so this is the only prompt a user gets.
    # Shown after a FAILED LOGIN for that username, never via a bulk lookup:
    # keying a public endpoint on username would make it trivially
    # scrapeable, since usernames are far more guessable than emails.
    password_hint: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utcnow)
    # Currently applied per-user branding palette (see app/palette.py).
    # Stored as JSON; only keys in ALLOWED_KEYS survive a PUT. Empty-string
    # values mean "inherit the shipped default".
    branding_palette: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Named palette presets. `{name: overrides}` — the name the user
    # chose for the preset mapped to the same override shape as
    # branding_palette. Empty by default; "Activating" a preset copies its
    # overrides into branding_palette.
    palette_presets: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Hard lock: when True, the editor's Inspector refuses to commit inline
    # colour overrides for nodes that inherit their colour from the
    # palette. Useful for enforcing brand consistency across a team.
    palette_locked: bool = Field(default=False)


class Dicegram(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    name: str
    source: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Share(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True)
    # unique=True: one Share row per Dicegram. Enforced at the DB level as
    # belt-and-suspenders alongside the get-or-create logic in
    # routers/shares.py (which otherwise raced under concurrent create
    # requests and produced duplicate rows that `revoke` couldn't fully
    # clean up). Only takes effect for freshly-created tables via
    # create_all; `db._ensure_schema` runs an idempotent dedup + adds the
    # equivalent unique index for pre-existing databases on upgrade.
    dicegram_id: int = Field(foreign_key="dicegram.id", index=True, unique=True)
    created_at: datetime = Field(default_factory=utcnow)
