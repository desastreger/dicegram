from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlmodel import Session

from ..config import settings
from ..db import get_session
from ..dsl.export_svg import render_svg
from ..dsl.parser import parse
from ..models import User
from ..palette import build_theme
from ..rate_limit import limiter

router = APIRouter(prefix="/api/export", tags=["export"])


class ExportIn(BaseModel):
    source: str = Field(max_length=settings.max_source_bytes)


@router.post("/svg")
@limiter.limit("30/minute")
def export_svg(
    request: Request,
    body: ExportIn,
    session: Session = Depends(get_session),
) -> Response:
    # Apply the signed-in user's branding palette when available; anonymous
    # (demo-mode) exports use the shipped default palette.
    user_id = request.session.get("user_id") if request else None
    user = session.get(User, user_id) if user_id else None
    parsed = parse(body.source)
    theme_id = parsed.settings.get("color_scheme") if isinstance(parsed.settings, dict) else None
    dicegram_overrides = _palette_overrides_from_settings(parsed.settings)
    user_palette = user.branding_palette if user else None
    theme = build_theme(user_palette, theme_id=theme_id, dicegram_overrides=dicegram_overrides)
    svg = render_svg(parsed, theme=theme)
    return Response(content=svg, media_type="image/svg+xml")


def _palette_overrides_from_settings(parsed_settings: dict) -> dict[str, str]:
    """Pluck `setting palette_<key> <color>` entries from a Parsed.settings
    dict. Per-Dicegram palette overrides ride alongside the rest of the
    layout / direction settings so the entire theme (chrome + palette tweaks)
    travels with the source on share or export."""
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
