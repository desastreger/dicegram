from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..config import settings
from ..dsl.compiler import normalize
from ..dsl.layout import compute_layout
from ..dsl.parser import parse
from ..dsl.tree import build_tree

router = APIRouter(prefix="/api/render", tags=["render"])


class RenderIn(BaseModel):
    source: str = Field(max_length=settings.max_source_bytes)
    normalize_source: bool = True


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
    parent_id: str = "__root__"
    attrs: dict = Field(default_factory=dict)
    style: dict = Field(default_factory=dict)


class EdgeOut(BaseModel):
    id: str
    source: str
    target: str
    kind: str
    label: str = ""
    attrs: dict = Field(default_factory=dict)
    source_port: str | None = None
    target_port: str | None = None


class LaneOut(BaseModel):
    id: str
    name: str
    x: float
    y: float
    width: float
    height: float


class BoxOut(BaseModel):
    id: str
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


class NoticeOut(BaseModel):
    severity: str
    message: str
    line: int | None = None


class TreeNodeOut(BaseModel):
    id: str
    kind: str
    label: str
    parent: str | None = None
    children: list[str] = Field(default_factory=list)
    shape: str | None = None


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
    notices: list[NoticeOut] = Field(default_factory=list)
    tree: list[TreeNodeOut] = Field(default_factory=list)
    normalized_source: str = ""
    source_changed: bool = False


def _swimlane_id(name: str) -> str:
    return f"swimlane:{name}"


def _box_id(label: str, swimlane: str | None) -> str:
    return f"box:{swimlane or ''}::{label}"


@router.post("", response_model=RenderOut)
def render(body: RenderIn) -> RenderOut:
    original = body.source
    notices_out: list[NoticeOut] = []
    normalized_source = original
    source_changed = False

    if body.normalize_source:
        res = normalize(original)
        normalized_source = res.source
        source_changed = res.changed
        notices_out = [
            NoticeOut(severity=n.severity, message=n.message, line=n.line)
            for n in res.notices
        ]

    parsed = parse(normalized_source)
    layout = compute_layout(parsed)
    positions = layout["positions"]
    tree = build_tree(parsed)

    nodes_out: list[NodeOut] = []
    for n in parsed.nodes:
        p = positions.get(n.name)
        if not p:
            continue
        tn = tree.nodes.get(n.name)
        parent_id = tn.parent if tn else "__root__"
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
                parent_id=parent_id or "__root__",
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
            source_port=e.source_port,
            target_port=e.target_port,
        )
        for i, e in enumerate(parsed.edges)
    ]

    lanes_out = [
        LaneOut(
            id=_swimlane_id(name),
            name=name,
            x=r["x"],
            y=r["y"],
            width=r["w"],
            height=r["h"],
        )
        for name, r in layout["lane_rects"].items()
    ]

    box_rects = layout["box_rects"]
    boxes_out = []
    for b in parsed.boxes:
        rect = box_rects.get(b.label) or {}
        boxes_out.append(
            BoxOut(
                id=_box_id(b.label, b.swimlane),
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

    tree_out = [
        TreeNodeOut(
            id=tn.id,
            kind=tn.kind,
            label=tn.label,
            parent=tn.parent,
            children=list(tn.children),
            shape=tn.props.get("shape") if tn.kind == "shape" else None,
        )
        for tn in tree.nodes.values()
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
        notices=notices_out,
        tree=tree_out,
        normalized_source=normalized_source,
        source_changed=source_changed,
    )
