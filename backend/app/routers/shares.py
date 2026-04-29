import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, field_serializer
from sqlmodel import Session, select

from ..db import get_session
from ..deps import current_user
from ..dsl.export_svg import render_svg
from ..dsl.parser import parse
from ..models import Dicegram, Share, User
from ..palette import build_theme

router = APIRouter(tags=["shares"])


def _as_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class ShareOut(BaseModel):
    slug: str
    created_at: datetime

    @field_serializer("created_at")
    def _ser_dt(self, v: datetime) -> str:
        return _as_utc_iso(v)


class PublicDicegram(BaseModel):
    name: str
    source: str
    updated_at: datetime

    @field_serializer("updated_at")
    def _ser_dt(self, v: datetime) -> str:
        return _as_utc_iso(v)


def _new_slug(session: Session) -> str:
    for _ in range(8):
        candidate = secrets.token_urlsafe(8).replace("_", "").replace("-", "")[:10]
        existing = session.exec(select(Share).where(Share.slug == candidate)).first()
        if not existing:
            return candidate
    raise HTTPException(status_code=500, detail="could not allocate slug")


@router.post("/api/dicegrams/{dicegram_id}/share", response_model=ShareOut)
def create_share(
    dicegram_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    dicegram = session.get(Dicegram, dicegram_id)
    if not dicegram or dicegram.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    existing = session.exec(select(Share).where(Share.dicegram_id == dicegram.id)).first()
    if existing:
        return ShareOut(slug=existing.slug, created_at=existing.created_at)
    slug = _new_slug(session)
    share = Share(slug=slug, dicegram_id=dicegram.id)
    session.add(share)
    session.commit()
    session.refresh(share)
    return ShareOut(slug=share.slug, created_at=share.created_at)


@router.delete(
    "/api/dicegrams/{dicegram_id}/share", status_code=status.HTTP_204_NO_CONTENT
)
def revoke_share(
    dicegram_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    dicegram = session.get(Dicegram, dicegram_id)
    if not dicegram or dicegram.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    existing = session.exec(select(Share).where(Share.dicegram_id == dicegram.id)).first()
    if existing:
        session.delete(existing)
        session.commit()


@router.get("/api/shares/{slug}", response_model=PublicDicegram)
def get_shared(slug: str, session: Session = Depends(get_session)):
    share = session.exec(select(Share).where(Share.slug == slug)).first()
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    dicegram = session.get(Dicegram, share.dicegram_id)
    if not dicegram:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return PublicDicegram(
        name=dicegram.name, source=dicegram.source, updated_at=dicegram.updated_at
    )


@router.get("/api/shares/{slug}/svg")
def get_shared_svg(slug: str, session: Session = Depends(get_session)) -> Response:
    share = session.exec(select(Share).where(Share.slug == slug)).first()
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    dicegram = session.get(Dicegram, share.dicegram_id)
    if not dicegram:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    # Shared views use the share owner's palette so the brand travels with the Dicegram.
    owner = session.get(User, dicegram.owner_id)
    parsed = parse(dicegram.source)
    theme_id = parsed.settings.get("color_scheme") if isinstance(parsed.settings, dict) else None
    overrides = _palette_overrides_from_settings(parsed.settings)
    owner_palette = owner.branding_palette if owner else None
    theme = build_theme(owner_palette, theme_id=theme_id, dicegram_overrides=overrides)
    return Response(
        content=render_svg(parsed, theme=theme),
        media_type="image/svg+xml",
    )


@router.get("/api/dicegrams/{dicegram_id}/svg")
def get_dicegram_svg(
    dicegram_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> Response:
    dicegram = session.get(Dicegram, dicegram_id)
    if not dicegram or dicegram.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    parsed = parse(dicegram.source)
    theme_id = parsed.settings.get("color_scheme") if isinstance(parsed.settings, dict) else None
    overrides = _palette_overrides_from_settings(parsed.settings)
    theme = build_theme(user.branding_palette, theme_id=theme_id, dicegram_overrides=overrides)
    return Response(
        content=render_svg(parsed, theme=theme),
        media_type="image/svg+xml",
    )


def _palette_overrides_from_settings(parsed_settings: dict) -> dict[str, str]:
    """Pluck `setting palette_<key> <color>` entries from Parsed.settings.
    Mirrors the helper in routers/export.py — kept private here so the two
    SVG paths stay in lockstep without an explicit shared module."""
    if not isinstance(parsed_settings, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in parsed_settings.items():
        if not isinstance(k, str) or not k.startswith("palette_"):
            continue
        key = k[len("palette_"):]
        if isinstance(v, str):
            out[key] = v
    return out
