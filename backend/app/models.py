from datetime import datetime, timezone

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=utcnow)
    # Set the first time the user confirms their email via the verification
    # link. Until then, email_verified_at is None and we surface a banner
    # in the frontend; no feature is gated on verification yet.
    email_verified_at: datetime | None = Field(default=None)
    # Currently applied per-user branding palette (see app/palette.py).
    # Stored as JSON; only keys in ALLOWED_KEYS survive a PUT. Empty-string
    # values mean "inherit the shipped default".
    branding_palette: dict = Field(default_factory=dict, sa_column=Column(JSON))
    # Named palette presets. `{name: overrides}` — the name the user
    # chose for the preset mapped to the same override shape as
    # branding_palette. Empty by default; "Activating" a preset copies its
    # overrides into branding_palette.
    palette_presets: dict = Field(default_factory=dict, sa_column=Column(JSON))


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
