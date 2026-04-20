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
    body: ExportIn,
    request: Request,
    session: Session = Depends(get_session),
) -> Response:
    # Apply the signed-in user's branding palette when available; anonymous
    # (demo-mode) exports use the shipped default palette.
    user_id = request.session.get("user_id") if request else None
    user = session.get(User, user_id) if user_id else None
    theme = build_theme(user.branding_palette) if user else build_theme(None)

    parsed = parse(body.source)
    svg = render_svg(parsed, theme=theme)
    return Response(content=svg, media_type="image/svg+xml")
