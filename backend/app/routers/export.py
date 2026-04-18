from fastapi import APIRouter, Response
from pydantic import BaseModel

from ..dsl.export_svg import render_svg
from ..dsl.parser import parse

router = APIRouter(prefix="/api/export", tags=["export"])


class ExportIn(BaseModel):
    source: str


@router.post("/svg")
def export_svg(body: ExportIn) -> Response:
    parsed = parse(body.source)
    svg = render_svg(parsed)
    return Response(content=svg, media_type="image/svg+xml")
