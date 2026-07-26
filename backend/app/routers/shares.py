import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, field_serializer
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ..db import get_session
from ..deps import current_user
from ..dsl.export_svg import render_svg
from ..dsl.parser import MAX_GRAPH_ELEMENTS, graph_too_large, parse
from ..models import Dicegram, Share, User
from ..palette import build_theme
from ..rate_limit import limiter

# Restrictive headers on raw SVG responses — defense-in-depth alongside
# the colour sanitization in dsl/export_svg.py. If a future bug ever let
# an unsafe value slip through, the browser still won't execute it: no
# script/style/external resource is allowed to load from inside the SVG.
_SVG_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
    "Content-Disposition": 'inline; filename="dicegram.svg"',
    "X-Content-Type-Options": "nosniff",
}

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
    try:
        session.commit()
    except IntegrityError:
        # Lost a create race against a concurrent request for the same
        # Dicegram — the unique index on dicegram_id rejected our insert.
        # Re-query and return the winner's row instead of erroring, so
        # "create share" is effectively get-or-create even under races.
        session.rollback()
        existing = session.exec(
            select(Share).where(Share.dicegram_id == dicegram.id)
        ).first()
        if existing:
            return ShareOut(slug=existing.slug, created_at=existing.created_at)
        raise
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
    # Delete ALL Share rows for this dicegram, not just the first — older
    # code left orphaned duplicates (from the create race above) live
    # after a "revoke", which is a fail-open bug: the link kept working.
    existing = session.exec(select(Share).where(Share.dicegram_id == dicegram.id)).all()
    for row in existing:
        session.delete(row)
    if existing:
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
@limiter.limit("30/minute")
def get_shared_svg(
    request: Request, slug: str, session: Session = Depends(get_session)
) -> Response:
    share = session.exec(select(Share).where(Share.slug == slug)).first()
    if not share:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    dicegram = session.get(Dicegram, share.dicegram_id)
    if not dicegram:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    # Shared views use the share owner's palette so the brand travels with the Dicegram.
    owner = session.get(User, dicegram.owner_id)
    parsed = parse(dicegram.source)
    if graph_too_large(parsed):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"diagram too large to render (max {MAX_GRAPH_ELEMENTS} nodes/edges)",
        )
    theme_id = parsed.settings.get("color_scheme") if isinstance(parsed.settings, dict) else None
    overrides = _palette_overrides_from_settings(parsed.settings)
    owner_palette = owner.branding_palette if owner else None
    theme = build_theme(owner_palette, theme_id=theme_id, dicegram_overrides=overrides)
    return Response(
        content=render_svg(parsed, theme=theme),
        media_type="image/svg+xml",
        headers=_SVG_HEADERS,
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
    if graph_too_large(parsed):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"diagram too large to render (max {MAX_GRAPH_ELEMENTS} nodes/edges)",
        )
    theme_id = parsed.settings.get("color_scheme") if isinstance(parsed.settings, dict) else None
    overrides = _palette_overrides_from_settings(parsed.settings)
    theme = build_theme(user.branding_palette, theme_id=theme_id, dicegram_overrides=overrides)
    return Response(
        content=render_svg(parsed, theme=theme),
        media_type="image/svg+xml",
        headers=_SVG_HEADERS,
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
