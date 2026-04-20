from __future__ import annotations

import re
from dataclasses import dataclass, field

SHAPE_KEYWORDS = {
    "rect",
    "rounded",
    "diamond",
    "circle",
    "parallelogram",
    "hexagon",
    "cylinder",
    "stadium",
}

CONNECTION_PATTERNS = [
    ("==>", "thick"),
    ("-->", "dashed"),
    ("-.-", "dotted_line"),
    ("---", "solid_line"),
    ("->", "solid"),
]

OBJECT_RE = re.compile(r'^\[(\w+)\]\s+(\w+)\s+"((?:[^"\\]|\\.)*)"\s*(.*?)\s*$')
ATTR_RE = re.compile(r'(\w+):((?:"[^"]*"|\S+))')
STYLE_BLOCK_RE = re.compile(r"\{([^{}]*)\}")
POSITION_RE = re.compile(r"@\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)")
SETTING_RE = re.compile(r"^setting\s+(\w+)\s+(.+)$")
DIRECTION_RE = re.compile(r"^direction\s+(\S+)$")
SWIMLANE_OPEN_RE = re.compile(r'^swimlane\s+"([^"]+)"\s*\{$')
BOX_OPEN_RE = re.compile(r'^box\s+"([^"]+)"\s*(?:\{([^{}]*)\})?\s*\{$')
GROUP_OPEN_RE = re.compile(r'^group\s+"([^"]+)"\s*\{(.*)$')
NOTE_RE = re.compile(r'^note\s+"((?:[^"\\]|\\.)*)"\s+\[(\w+)\]$')
IDENT_RE = re.compile(r"\w+")


@dataclass
class Node:
    name: str
    shape: str
    label: str
    step: int = 0
    swimlane: str | None = None
    box: str | None = None
    attrs: dict = field(default_factory=dict)
    style: dict = field(default_factory=dict)
    position: tuple[float, float] | None = None
    step_explicit: bool = True


@dataclass
class Edge:
    source: str
    target: str
    kind: str
    label: str = ""
    attrs: dict = field(default_factory=dict)
    # Explicit port on the source side (one of 't','b','l','r'). None = let
    # the renderer pick a port from geometry. Authored as `A@r -> B@l`.
    source_port: str | None = None
    target_port: str | None = None


@dataclass
class Swimlane:
    name: str
    members: list[str] = field(default_factory=list)


@dataclass
class Box:
    label: str
    swimlane: str | None = None
    style: dict = field(default_factory=dict)
    members: list[str] = field(default_factory=list)


@dataclass
class Group:
    name: str
    members: list[str] = field(default_factory=list)


@dataclass
class Note:
    text: str
    target: str


@dataclass
class ParseError:
    line: int
    column: int
    message: str


@dataclass
class Parsed:
    direction: str = "top-to-bottom"
    settings: dict = field(default_factory=dict)
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    swimlanes: list[Swimlane] = field(default_factory=list)
    boxes: list[Box] = field(default_factory=list)
    groups: list[Group] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    errors: list[ParseError] = field(default_factory=list)


def _strip_inline_comment(line: str) -> str:
    in_str = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line):
            i += 2
            continue
        if ch == '"':
            in_str = not in_str
        elif not in_str and line[i : i + 2] == "//":
            return line[:i].rstrip()
        i += 1
    return line


def _parse_style_pairs(text: str) -> dict:
    style: dict = {}
    for pair in text.split(","):
        if ":" in pair:
            k, v = pair.split(":", 1)
            style[k.strip()] = v.strip()
    return style


def _split_attrs(rest: str) -> tuple[dict, dict, tuple[float, float] | None]:
    style: dict = {}
    position: tuple[float, float] | None = None

    m = STYLE_BLOCK_RE.search(rest)
    if m:
        style = _parse_style_pairs(m.group(1))
        rest = rest[: m.start()] + rest[m.end() :]

    m = POSITION_RE.search(rest)
    if m:
        position = (float(m.group(1)), float(m.group(2)))
        rest = rest[: m.start()] + rest[m.end() :]

    attrs: dict = {}
    for am in ATTR_RE.finditer(rest):
        k = am.group(1)
        v = am.group(2)
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        attrs[k] = v
    return attrs, style, position


def _parse_object(line: str, swimlane: str | None, box: str | None) -> Node | None:
    m = OBJECT_RE.match(line)
    if not m:
        return None
    shape = m.group(1)
    if shape not in SHAPE_KEYWORDS:
        return None
    name = m.group(2)
    label = m.group(3).replace("\\n", "\n")
    attrs, style, position = _split_attrs(m.group(4))
    step_explicit = "step" in attrs
    step_raw = attrs.pop("step", "0")
    try:
        step = int(step_raw)
    except (TypeError, ValueError):
        step = 0
    return Node(
        name=name,
        shape=shape,
        label=label,
        step=step,
        swimlane=swimlane,
        box=box,
        attrs=attrs,
        style=style,
        position=position,
        step_explicit=step_explicit,
    )


_PORT_ALIASES = {
    "t": "t", "top": "t", "n": "t", "north": "t",
    "b": "b", "bottom": "b", "s": "b", "south": "b",
    "l": "l", "left": "l", "w": "l", "west": "l",
    "r": "r", "right": "r", "e": "r", "east": "r",
}


def _split_node_port(token: str) -> tuple[str, str | None]:
    """`decide@r` → ("decide", "r"). Unknown ports pass through as-is so
    downstream error reporting sees them.
    """
    if "@" not in token:
        return token, None
    name, _, port = token.partition("@")
    port = port.strip().lower()
    return name.strip(), _PORT_ALIASES.get(port, port) or None


def _parse_connection(line: str) -> Edge | None:
    for pattern, kind in CONNECTION_PATTERNS:
        idx = line.find(pattern)
        if idx == -1:
            continue
        left = line[:idx].strip()
        right = line[idx + len(pattern) :].strip()
        if not left or not right:
            continue

        label = ""
        attrs: dict = {}
        target = right
        colon = right.find(":")
        if colon != -1:
            target = right[:colon].strip()
            tail = right[colon + 1 :].strip()
            lm = re.match(r'^"((?:[^"\\]|\\.)*)"', tail)
            if lm:
                label = lm.group(1).replace("\\n", "\n")
                tail = tail[lm.end() :]
            for am in ATTR_RE.finditer(tail):
                k = am.group(1)
                v = am.group(2)
                if v.startswith('"') and v.endswith('"'):
                    v = v[1:-1]
                attrs[k] = v
        target = target.split()[0] if target else target
        if not target:
            continue
        source = left.split()[0]

        source_name, source_port = _split_node_port(source)
        target_name, target_port = _split_node_port(target)

        if not IDENT_RE.fullmatch(source_name) or not IDENT_RE.fullmatch(target_name):
            continue

        # Normalize arrow / decoration attrs to short forms so renderers
        # don't have to guess. Accepted values:
        #   arrow  circle  diamond  square  tee  open_arrow  none
        for key in ("start", "end"):
            v = attrs.get(key)
            if isinstance(v, str):
                attrs[key] = v.strip().lower()

        return Edge(
            source=source_name,
            target=target_name,
            kind=kind,
            label=label,
            attrs=attrs,
            source_port=source_port,
            target_port=target_port,
        )
    return None


def _topmost(stack: list[tuple[str, object]], kind: str) -> object | None:
    for k, ref in reversed(stack):
        if k == kind:
            return ref
    return None


def parse(source: str) -> Parsed:
    parsed = Parsed()
    stack: list[tuple[str, object]] = []  # (kind, container_object)
    group_collecting: Group | None = None

    for lineno, raw in enumerate(source.split("\n"), 1):
        line = _strip_inline_comment(raw).rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        # Group body: collect identifiers until '}'
        if group_collecting is not None:
            if stripped == "}":
                group_collecting = None
                if stack and stack[-1][0] == "group":
                    stack.pop()
                continue
            for tok in IDENT_RE.findall(stripped):
                group_collecting.members.append(tok)
            continue

        # Closing brace for non-group containers
        if stripped == "}":
            if stack:
                stack.pop()
            continue

        # direction
        m = DIRECTION_RE.match(stripped)
        if m:
            parsed.direction = m.group(1)
            continue

        # setting
        m = SETTING_RE.match(stripped)
        if m:
            k, v = m.group(1), m.group(2).strip()
            try:
                parsed.settings[k] = int(v)
            except ValueError:
                try:
                    parsed.settings[k] = float(v)
                except ValueError:
                    parsed.settings[k] = v
            continue

        # swimlane open
        m = SWIMLANE_OPEN_RE.match(stripped)
        if m:
            sl = Swimlane(name=m.group(1))
            parsed.swimlanes.append(sl)
            stack.append(("swimlane", sl))
            continue

        # box open (may have inline style block before final '{')
        m = BOX_OPEN_RE.match(stripped)
        if m:
            current_sl_obj = _topmost(stack, "swimlane")
            current_sl = current_sl_obj.name if isinstance(current_sl_obj, Swimlane) else None
            style = _parse_style_pairs(m.group(2)) if m.group(2) else {}
            bx = Box(label=m.group(1), swimlane=current_sl, style=style)
            parsed.boxes.append(bx)
            stack.append(("box", bx))
            continue

        # group open (one-line or multi-line)
        m = GROUP_OPEN_RE.match(stripped)
        if m:
            grp = Group(name=m.group(1))
            parsed.groups.append(grp)
            inline_rest = m.group(2).strip()
            if inline_rest.endswith("}"):
                body = inline_rest[:-1]
                for tok in IDENT_RE.findall(body):
                    grp.members.append(tok)
                # not pushed onto stack; closed inline
            else:
                if inline_rest:
                    for tok in IDENT_RE.findall(inline_rest):
                        grp.members.append(tok)
                stack.append(("group", grp))
                group_collecting = grp
            continue

        # note
        m = NOTE_RE.match(stripped)
        if m:
            parsed.notes.append(Note(text=m.group(1).replace("\\n", "\n"), target=m.group(2)))
            continue

        # object
        sl_obj = _topmost(stack, "swimlane")
        bx_obj = _topmost(stack, "box")
        sl_name = sl_obj.name if isinstance(sl_obj, Swimlane) else None
        bx_label = bx_obj.label if isinstance(bx_obj, Box) else None
        node = _parse_object(stripped, sl_name, bx_label)
        if node:
            parsed.nodes.append(node)
            if isinstance(sl_obj, Swimlane):
                sl_obj.members.append(node.name)
            if isinstance(bx_obj, Box):
                bx_obj.members.append(node.name)
            continue

        # connection
        edge = _parse_connection(stripped)
        if edge:
            parsed.edges.append(edge)
            continue

        col = len(raw) - len(raw.lstrip()) + 1
        parsed.errors.append(
            ParseError(line=lineno, column=col, message=f"unrecognized: {stripped[:80]}")
        )

    return parsed
