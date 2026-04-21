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

# Labels may be a single quoted string OR a sequence joined by the
# `[linebreak]` token — e.g. `"First" [linebreak] "Second"`. The label
# portion is captured greedily and parsed apart later.
_LABEL_PART_RE = re.compile(r'("(?:[^"\\]|\\.)*"|\[linebreak\])')
_LABEL_SEQ_RE = re.compile(
    r'(?P<label>"(?:[^"\\]|\\.)*"(?:\s*\[linebreak\]\s*"(?:[^"\\]|\\.)*")*)'
)
OBJECT_RE = re.compile(
    r'^\[(\w+)\]\s+(\w+)\s+'
    r'("(?:[^"\\]|\\.)*"(?:\s*\[linebreak\]\s*"(?:[^"\\]|\\.)*")*)'
    r'\s*(.*?)\s*$'
)
ATTR_RE = re.compile(r'(\w+):((?:"[^"]*"|\S+))')
CONNECTOR_RE = re.compile(r'^\[connector\]\s+(?:(\w+)\s+)?(.*?)\s*$')
# Kind-keyword bracket forms — the bracket names the LINE STYLE. Tip is
# always a separate visible field, so `[solid_line] … tip:none` gives a
# plain solid stroke with no arrowhead, same line style, different
# terminator. Legacy `[arrow]` / `[dashed_arrow]` / etc. still parse for
# back-compat with files normalized under the old scheme.
#
#   [solid_line]   → kind=solid       default tip=arrow
#   [dashed_line]  → kind=dashed      default tip=arrow
#   [thick_line]   → kind=thick       default tip=arrow
#   [dotted_line]  → kind=dotted_line default tip=none
#   [connector]    → generic (kind from the `kind:` field)
#
# Legacy aliases (accepted for read; R8 emits the new keywords):
#   [arrow] / [solid_arrow]    → kind=solid,  tip=arrow
#   [dashed_arrow]             → kind=dashed, tip=arrow
#   [thick_arrow]              → kind=thick,  tip=arrow
#   [line]                     → kind=solid,  tip=none
_KIND_KEYWORD_PRESETS: dict[str, tuple[str, str]] = {
    "solid_line": ("solid", "arrow"),
    "dashed_line": ("dashed", "arrow"),
    "thick_line": ("thick", "arrow"),
    "dotted_line": ("dotted_line", "none"),
    # legacy aliases
    "arrow": ("solid", "arrow"),
    "solid_arrow": ("solid", "arrow"),
    "dashed_arrow": ("dashed", "arrow"),
    "thick_arrow": ("thick", "arrow"),
    "line": ("solid", "none"),
}
KIND_KEYWORD_RE = re.compile(
    r'^\[(' + "|".join(_KIND_KEYWORD_PRESETS) + r')\]\s+(?:(\w+)\s+)?(.*?)\s*$'
)
STYLE_BLOCK_RE = re.compile(r"\{([^{}]*)\}")
POSITION_RE = re.compile(r"@\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)")
SETTING_RE = re.compile(r"^setting\s+(\w+)\s+(.+)$")
DIRECTION_RE = re.compile(r"^direction\s+(\S+)$")
SWIMLANE_OPEN_RE = re.compile(r'^swimlane\s+"([^"]+)"\s*\{$')
BOX_OPEN_RE = re.compile(r'^box\s+"([^"]+)"\s*(?:\{([^{}]*)\})?\s*\{$')
GROUP_OPEN_RE = re.compile(r'^group\s+"([^"]+)"\s*\{(.*)$')
NOTE_RE = re.compile(
    r'^note\s+'
    r'("(?:[^"\\]|\\.)*"(?:\s*\[linebreak\]\s*"(?:[^"\\]|\\.)*")*)'
    r'\s+\[(\w+)\]$'
)
# Bracket-form note: `[note] name? "text" target:other_node`. Same shape
# as `[solid_line] name? from:A to:B …` so notes surface as first-class
# objects in the inspector alongside shapes and connectors.
NOTE_BRACKET_RE = re.compile(
    r'^\[note\]\s+(?:(\w+)\s+)?'
    r'("(?:[^"\\]|\\.)*"(?:\s*\[linebreak\]\s*"(?:[^"\\]|\\.)*")*)'
    r'\s*(.*?)\s*$'
)
IDENT_RE = re.compile(r"\w+")

# Verbose block-form edge:  A@r -> B@l {
#                               label: "yes"
#                               end: arrow
#                           }
# Header matches whether or not the optional `edge` keyword prefixes it.
_EDGE_BLOCK_SYMS = r"->|-->|==>|---|-\.-"
EDGE_BLOCK_OPEN_RE = re.compile(
    r"^(?:edge\s+)?(\w+)(?:@(\w+))?\s*(" + _EDGE_BLOCK_SYMS + r")\s*(\w+)(?:@(\w+))?\s*\{\s*(.*)$"
)
EDGE_BLOCK_ATTR_RE = re.compile(
    r'(\w+)\s*:\s*('
    r'"(?:[^"\\]|\\.)*"(?:\s*\[linebreak\]\s*"(?:[^"\\]|\\.)*")*'
    r'|\S+'
    r')'
)


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


def _join_label_parts(raw: str) -> str:
    """Collapse `"A" [linebreak] "B"` → `A\\nB`. Also honours the legacy
    `\\n` escape inside a single quoted string so pre-existing files keep
    working; new files should prefer the `[linebreak]` token which is
    discoverable in autocomplete."""
    parts: list[str] = []
    for m in _LABEL_PART_RE.finditer(raw):
        tok = m.group(1)
        if tok == "[linebreak]":
            parts.append("\n")
        else:
            inner = tok[1:-1].replace("\\n", "\n").replace('\\"', '"')
            parts.append(inner)
    return "".join(parts)


def _parse_object(line: str, swimlane: str | None, box: str | None) -> Node | None:
    m = OBJECT_RE.match(line)
    if not m:
        return None
    shape = m.group(1)
    if shape not in SHAPE_KEYWORDS:
        return None
    name = m.group(2)
    label = _join_label_parts(m.group(3))
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


_KIND_SYM_TO_KIND = {
    "->": "solid",
    "-->": "dashed",
    "==>": "thick",
    "---": "solid_line",
    "-.-": "dotted_line",
}
_KIND_ALIAS = {
    "solid": "solid",
    "dashed": "dashed",
    "thick": "thick",
    "solid_line": "solid_line",
    "line": "solid_line",
    "solid-line": "solid_line",
    "dotted_line": "dotted_line",
    "dotted": "dotted_line",
    "dotted-line": "dotted_line",
}


def _apply_edge_block_attr(edge: Edge, key: str, value: str) -> None:
    """Mutate `edge` with a single `key: value` pair from a block body.

    In `[connector]` / block form, `from:` and `to:` can carry a node ref
    (with optional `@port`) OR a bare port word. A bare port word (e.g.
    `from: right`) keeps the current port-only semantics from the pre-
    connector block grammar. A node ref (e.g. `from: decide` or
    `from: decide@r`) sets the source name and optional port.

    `from_anchor:` / `to_anchor:` are anchor-only — they only ever set the
    port, never the source/target name. Preferred in `[connector]` form so
    authors can keep anchors visible and separable from node refs (the
    compiler then has a structured signal to work with).

    Everything else lands in `attrs` (so `tip:` → stored under `end`,
    `back:` → stored under `start`, custom keys pass through).
    """
    key = key.strip().lower()
    v = value.strip()
    # Label sequences: `"First" [linebreak] "Second"` collapse to multi-line.
    if v.startswith('"') and "[linebreak]" in v:
        v = _join_label_parts(v)
    elif v.startswith('"') and v.endswith('"') and len(v) >= 2:
        v = v[1:-1].replace("\\n", "\n").replace('\\"', '"')

    if key in ("from", "source", "origin"):
        vl = v.lower()
        # Bare port word (`from: right`) only when source is already set
        # from the block header — otherwise a single-letter node name like
        # `b` would silently become a port. In `[connector]` form, source
        # starts empty, so this branch never fires and everything is a ref.
        if "@" not in v and vl in _PORT_ALIASES and edge.source:
            edge.source_port = _PORT_ALIASES[vl]
        else:
            name, port = _split_node_port(v)
            if name:
                edge.source = name
            if port:
                edge.source_port = port
        return
    if key in ("to", "target", "destination"):
        vl = v.lower()
        if "@" not in v and vl in _PORT_ALIASES and edge.target:
            edge.target_port = _PORT_ALIASES[vl]
        else:
            name, port = _split_node_port(v)
            if name:
                edge.target = name
            if port:
                edge.target_port = port
        return
    if key in ("from_port", "from_anchor", "source_port", "source_anchor", "origin_anchor"):
        edge.source_port = _PORT_ALIASES.get(v.lower(), v.lower()) or None
        return
    if key in ("to_port", "to_anchor", "target_port", "target_anchor", "destination_anchor"):
        edge.target_port = _PORT_ALIASES.get(v.lower(), v.lower()) or None
        return
    if key == "label":
        edge.label = v
        return
    if key == "kind":
        canonical = _KIND_ALIAS.get(v.lower())
        if canonical:
            edge.kind = canonical
        return
    if key == "tip":
        edge.attrs["end"] = v.lower()
        return
    if key == "back":
        edge.attrs["start"] = v.lower()
        return
    if key in ("start", "end"):
        edge.attrs[key] = v.lower()
        return
    edge.attrs[key] = v


def _finalize_block_edge_body(edge: Edge, body: str) -> None:
    """Parse a block body — single-line `{ a:1 b:"hello world" }` or
    multi-line — into edge attrs. Accepts `key: value` with whitespace
    around the colon (block form convention) and quoted string values."""
    for am in EDGE_BLOCK_ATTR_RE.finditer(body):
        _apply_edge_block_attr(edge, am.group(1), am.group(2))


def _parse_connector(line: str) -> Edge | None:
    """`[connector] c1 from:decide@r to:issue@l kind:dashed tip:arrow`
    OR the kind-keyword form `[arrow] c1 from:… to:…` where the bracket
    names the line style (and implies a sensible default tip).

    A single-line object-style connector. `from:`/`to:` carry the node
    reference (with optional `@port` shorthand); `from_anchor:` /
    `to_anchor:` are the separable anchor fields that surface in the
    inspector and give the self-healer a structured signal to fix layout
    drift. `tip:` / `back:` are user-friendly aliases for `end:` / `start:`.
    """
    m = CONNECTOR_RE.match(line)
    preset_kind: str | None = None
    preset_tip: str | None = None
    if not m:
        m = KIND_KEYWORD_RE.match(line)
        if not m:
            return None
        keyword = m.group(1).lower()
        preset_kind, preset_tip = _KIND_KEYWORD_PRESETS[keyword]
        connector_name = m.group(2)
        body = m.group(3) or ""
    else:
        connector_name = m.group(1)
        body = m.group(2) or ""

    edge = Edge(source="", target="", kind=preset_kind or "solid")
    if preset_tip:
        edge.attrs["end"] = preset_tip
    if connector_name:
        edge.attrs["name"] = connector_name
    _finalize_block_edge_body(edge, body)
    if not edge.source or not edge.target:
        return None
    return edge


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
            lm = _LABEL_SEQ_RE.match(tail)
            if lm:
                label = _join_label_parts(lm.group("label"))
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
    edge_collecting: Edge | None = None

    for lineno, raw in enumerate(source.split("\n"), 1):
        line = _strip_inline_comment(raw).rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        # Block-form edge body: collect `key: value` until '}'.
        if edge_collecting is not None:
            if stripped == "}":
                parsed.edges.append(edge_collecting)
                edge_collecting = None
                continue
            _finalize_block_edge_body(edge_collecting, stripped)
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
            parsed.notes.append(Note(text=_join_label_parts(m.group(1)), target=m.group(2)))
            continue

        # Bracket-form note.
        m = NOTE_BRACKET_RE.match(stripped)
        if m:
            text = _join_label_parts(m.group(2))
            rest = m.group(3) or ""
            target = ""
            for am in ATTR_RE.finditer(rest):
                k = am.group(1).lower()
                v = am.group(2)
                if v.startswith('"') and v.endswith('"'):
                    v = v[1:-1]
                if k in ("target", "to", "for"):
                    target = v
            if target:
                parsed.notes.append(Note(text=text, target=target))
                continue
            # Missing target → let this fall through to the error branch.

        # bracket-form connector:  [connector] name? from:A to:B kind:… tip:…
        connector = _parse_connector(stripped)
        if connector:
            parsed.edges.append(connector)
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

        # block-form connection:  A@r -> B@l { … }
        m = EDGE_BLOCK_OPEN_RE.match(stripped)
        if m:
            src_port = _PORT_ALIASES.get((m.group(2) or "").lower()) if m.group(2) else None
            tgt_port = _PORT_ALIASES.get((m.group(5) or "").lower()) if m.group(5) else None
            kind = _KIND_SYM_TO_KIND.get(m.group(3), "solid")
            block_edge = Edge(
                source=m.group(1),
                target=m.group(4),
                kind=kind,
                source_port=src_port,
                target_port=tgt_port,
            )
            rest = (m.group(6) or "").strip()
            if rest.endswith("}"):
                # Single-line block:  A -> B { label:"x" end:circle }
                _finalize_block_edge_body(block_edge, rest[:-1])
                parsed.edges.append(block_edge)
            else:
                if rest:
                    _finalize_block_edge_body(block_edge, rest)
                edge_collecting = block_edge
            continue

        # inline connection
        edge = _parse_connection(stripped)
        if edge:
            parsed.edges.append(edge)
            continue

        col = len(raw) - len(raw.lstrip()) + 1
        parsed.errors.append(
            ParseError(line=lineno, column=col, message=f"unrecognized: {stripped[:80]}")
        )

    return parsed
