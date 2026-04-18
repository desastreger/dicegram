from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..dsl.layout import compute_layout
from ..dsl.parser import parse

router = APIRouter(prefix="/api/render", tags=["render"])


class RenderIn(BaseModel):
    source: str


class NodeOut(BaseModel):
    id: str
    shape: str
    label: str
    x: float
    y: float
    width: float
    height: float
    swimlane: str | None = None
    box: str | None = None
    attrs: dict = Field(default_factory=dict)
    style: dict = Field(default_factory=dict)


class EdgeOut(BaseModel):
    id: str
    source: str
    target: str
    kind: str
    label: str = ""
    attrs: dict = Field(default_factory=dict)


class LaneOut(BaseModel):
    name: str
    x: float
    y: float
    width: float
    height: float


class BoxOut(BaseModel):
    label: str
    swimlane: str | None = None
    style: dict = Field(default_factory=dict)
    members: list[str] = Field(default_factory=list)
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None


class GroupOut(BaseModel):
    name: str
    members: list[str] = Field(default_factory=list)
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None


class NoteOut(BaseModel):
    text: str
    target: str
    x: float = 0
    y: float = 0
    width: float = 160
    height: float = 56


class ErrorOut(BaseModel):
    line: int
    column: int
    message: str


class RenderOut(BaseModel):
    direction: str
    settings: dict = Field(default_factory=dict)
    nodes: list[NodeOut]
    edges: list[EdgeOut]
    lanes: list[LaneOut]
    boxes: list[BoxOut]
    groups: list[GroupOut]
    notes: list[NoteOut]
    errors: list[ErrorOut]


@router.post("", response_model=RenderOut)
def render(body: RenderIn) -> RenderOut:
    parsed = parse(body.source)
    layout = compute_layout(parsed)
    positions = layout["positions"]

    nodes_out: list[NodeOut] = []
    for n in parsed.nodes:
        p = positions.get(n.name)
        if not p:
            continue
        nodes_out.append(
            NodeOut(
                id=n.name,
                shape=n.shape,
                label=n.label,
                x=p["x"],
                y=p["y"],
                width=p["w"],
                height=p["h"],
                swimlane=n.swimlane,
                box=n.box,
                attrs=n.attrs,
                style=n.style,
            )
        )

    edges_out = [
        EdgeOut(
            id=f"e{i}",
            source=e.source,
            target=e.target,
            kind=e.kind,
            label=e.label,
            attrs=e.attrs,
        )
        for i, e in enumerate(parsed.edges)
    ]

    lanes_out = [
        LaneOut(name=name, x=r["x"], y=r["y"], width=r["w"], height=r["h"])
        for name, r in layout["lane_rects"].items()
    ]

    box_rects = layout["box_rects"]
    boxes_out = []
    for b in parsed.boxes:
        rect = box_rects.get(b.label) or {}
        boxes_out.append(
            BoxOut(
                label=b.label,
                swimlane=b.swimlane,
                style=b.style,
                members=b.members,
                x=rect.get("x"),
                y=rect.get("y"),
                width=rect.get("w"),
                height=rect.get("h"),
            )
        )

    group_rects = layout["group_rects"]
    groups_out = []
    for g in parsed.groups:
        rect = group_rects.get(g.name) or {}
        groups_out.append(
            GroupOut(
                name=g.name,
                members=g.members,
                x=rect.get("x"),
                y=rect.get("y"),
                width=rect.get("w"),
                height=rect.get("h"),
            )
        )

    notes_out = [
        NoteOut(
            text=np["text"],
            target=np["target"],
            x=np["x"],
            y=np["y"],
            width=np["w"],
            height=np["h"],
        )
        for np in layout["note_positions"]
    ]

    return RenderOut(
        direction=layout["direction"],
        settings=parsed.settings,
        nodes=nodes_out,
        edges=edges_out,
        lanes=lanes_out,
        boxes=boxes_out,
        groups=groups_out,
        notes=notes_out,
        errors=[
            ErrorOut(line=pe.line, column=pe.column, message=pe.message)
            for pe in parsed.errors
        ],
    )
