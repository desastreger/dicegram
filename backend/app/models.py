from datetime import datetime, timezone

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    # Display handle the user picks at signup. Optional today (older rows
    # predate the column) — the email is still the canonical identifier.
    username: str | None = Field(default=None)
    # User-supplied "password reminder" string. Captured at signup so the
    # user can recover their own memory of the password while SMTP-driven
    # forgot-password is disabled. Visible only to the signed-in user
    # (Settings page) plus the lookup-by-email helper on /login.
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
    dicegram_id: int = Field(foreign_key="dicegram.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)
