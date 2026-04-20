from __future__ import annotations

from html import escape

from .layout import compute_layout
from .parser import Node, Parsed

DARK_THEME = {
    "bg": "#0a0a0a",
    "lane_bg": "rgba(56,70,95,0.18)",
    "lane_border": "#334155",
    "lane_label": "#94a3b8",
    "box_bg": "rgba(56,70,95,0.30)",
    "box_border": "#475569",
    "box_label": "#cbd5e1",
    "group_border": "#f59e0b",
    "group_label": "#f59e0b",
    "note_bg": "#fde68a",
    "note_border": "#b45309",
    "note_text": "#422006",
    "note_leader": "#b45309",
    "node_fill": "#1f2937",
    "node_stroke": "#64748b",
    "node_text": "#e5e7eb",
    "edge": "#94a3b8",
    "edge_label": "#e5e7eb",
    "edge_label_bg": "#0f172a",
    "type_fill": {
        "start": "#064e3b",
        "end": "#3f1d1d",
        "decision": "#3a2f0b",
        "datastore": "#0c3a5c",
    },
    "priority_stroke": {"critical": "#ef4444", "high": "#f59e0b"},
    "status_stroke": {"blocked": "#ef4444", "complete": "#10b981"},
    "status_text": {"deprecated": "#71717a"},
}


def _style_num(node: Node, key: str) -> float | None:
    raw = node.style.get(key)
    if raw in (None, ""):
        return None
    try:
        return float(str(raw).rstrip("px"))
    except (TypeError, ValueError):
        return None


def _shape_path(node: Node, x: float, y: float, w: float, h: float) -> str:
    """Return an SVG element string for the shape outline."""
    cx = x + w / 2
    cy = y + h / 2
    rx_override = _style_num(node, "rx")
    if node.shape == "rect":
        rx = rx_override if rx_override is not None else 4
        return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" />'
    if node.shape == "rounded":
        rx = rx_override if rx_override is not None else 14
        return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" />'
    if node.shape == "stadium":
        return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h/2:.1f}" />'
    if node.shape == "circle":
        return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{w/2:.1f}" ry="{h/2:.1f}" />'
    if node.shape == "diamond":
        pts = f"{cx:.1f},{y:.1f} {x+w:.1f},{cy:.1f} {cx:.1f},{y+h:.1f} {x:.1f},{cy:.1f}"
        return f'<polygon points="{pts}" />'
    if node.shape == "parallelogram":
        skew = w * 0.15
        pts = f"{x+skew:.1f},{y:.1f} {x+w:.1f},{y:.1f} {x+w-skew:.1f},{y+h:.1f} {x:.1f},{y+h:.1f}"
        return f'<polygon points="{pts}" />'
    if node.shape == "hexagon":
        side = w * 0.12
        pts = (
            f"{x+side:.1f},{y:.1f} {x+w-side:.1f},{y:.1f} {x+w:.1f},{cy:.1f} "
            f"{x+w-side:.1f},{y+h:.1f} {x+side:.1f},{y+h:.1f} {x:.1f},{cy:.1f}"
        )
        return f'<polygon points="{pts}" />'
    if node.shape == "cylinder":
        cap = h * 0.15
        body_top = y + cap
        body_bot = y + h - cap
        return (
            f'<g><ellipse cx="{cx:.1f}" cy="{body_top:.1f}" rx="{w/2:.1f}" ry="{cap:.1f}" />'
            f'<rect x="{x:.1f}" y="{body_top:.1f}" width="{w:.1f}" height="{body_bot-body_top:.1f}" />'
            f'<path d="M {x:.1f} {body_top:.1f} L {x:.1f} {body_bot:.1f} '
            f'A {w/2:.1f} {cap:.1f} 0 0 0 {x+w:.1f} {body_bot:.1f} '
            f'L {x+w:.1f} {body_top:.1f}" /></g>'
        )
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" />'


def _text_lines(
    label: str,
    cx: float,
    cy: float,
    fill: str,
    font_size: float = 13,
    font_family: str = "-apple-system, Segoe UI, sans-serif",
) -> str:
    line_height = max(12, int(font_size * 1.25))
    lines = label.split("\n")
    n = len(lines)
    total = (n - 1) * line_height
    start_y = cy - total / 2 + font_size * 0.38
    out = []
    for i, line in enumerate(lines):
        out.append(
            f'<text x="{cx:.1f}" y="{start_y + i * line_height:.1f}" '
            f'text-anchor="middle" fill="{fill}" '
            f'font-family="{escape(font_family)}" font-size="{font_size:.1f}">'
            f"{escape(line)}</text>"
        )
    return "".join(out)


def _node_color(node: Node, theme: dict) -> tuple[str, str, str, float, str]:
    style = node.style
    attrs = node.attrs
    type_attr = attrs.get("type", "")
    status = attrs.get("status", "")
    priority = attrs.get("priority", "")

    fill = style.get("fill") or theme["type_fill"].get(type_attr, theme["node_fill"])
    stroke = (
        style.get("stroke")
        or theme["priority_stroke"].get(priority)
        or theme["status_stroke"].get(status)
        or theme["node_stroke"]
    )
    sw_override = _style_num(node, "stroke_width")
    if sw_override is not None:
        sw = sw_override
    else:
        sw = 3.0 if priority == "critical" else 2.25 if priority == "high" else 1.5
    text = style.get("text") or theme["status_text"].get(status, theme["node_text"])
    dasharray = "6 4" if status == "draft" else ""
    return fill, stroke, text, sw, dasharray


def render_svg(parsed: Parsed, theme: dict | None = None) -> str:
    th = theme or DARK_THEME
    layout = compute_layout(parsed)
    positions = layout["positions"]

    if not positions:
        if parsed.errors:
            first = parsed.errors[0]
            msg = escape(f"line {first.line}: {first.message}")
            extra = (
                f" (+{len(parsed.errors) - 1} more)" if len(parsed.errors) > 1 else ""
            )
            return (
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 140" '
                f'width="520" height="140" style="background:{th["bg"]}; '
                'font-family: -apple-system, sans-serif">'
                f'<rect x="0" y="0" width="520" height="140" fill="{th["bg"]}" />'
                '<rect x="16" y="16" width="488" height="108" rx="8" '
                f'fill="{th["node_fill"]}" stroke="#b45309" stroke-width="1.5" />'
                f'<text x="32" y="52" fill="#f59e0b" font-size="14" font-weight="600">'
                'Dicegram could not be rendered</text>'
                f'<text x="32" y="80" fill="{th["node_text"]}" font-size="12">'
                f'{msg}{extra}</text>'
                f'<text x="32" y="104" fill="#94a3b8" font-size="11">'
                'Fix the DSL and re-share to update the preview.</text>'
                '</svg>'
            )
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"></svg>'

    pad = 20
    xs = [p["x"] for p in positions.values()]
    ys = [p["y"] for p in positions.values()]
    xs2 = [p["x"] + p["w"] for p in positions.values()]
    ys2 = [p["y"] + p["h"] for p in positions.values()]
    for r in layout["lane_rects"].values():
        xs.append(r["x"])
        ys.append(r["y"])
        xs2.append(r["x"] + r["w"])
        ys2.append(r["y"] + r["h"])
    for r in layout["box_rects"].values():
        xs.append(r["x"])
        ys.append(r["y"])
        xs2.append(r["x"] + r["w"])
        ys2.append(r["y"] + r["h"])
    for r in layout["group_rects"].values():
        xs.append(r["x"])
        ys.append(r["y"])
        xs2.append(r["x"] + r["w"])
        ys2.append(r["y"] + r["h"])
    for n in layout["note_positions"]:
        xs.append(n["x"])
        ys.append(n["y"])
        xs2.append(n["x"] + n["w"])
        ys2.append(n["y"] + n["h"])

    min_x = min(xs) - pad
    min_y = min(ys) - pad
    max_x = max(xs2) + pad
    max_y = max(ys2) + pad
    width = max_x - min_x
    height = max_y - min_y

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{min_x:.1f} {min_y:.1f} {width:.1f} {height:.1f}" '
        f'width="{width:.1f}" height="{height:.1f}" '
        f'style="background:{th["bg"]}; font-family: -apple-system, sans-serif">'
    )
    edge_fill = th["edge"]
    parts.append(
        '<defs>'
        # Classic filled triangle — the default at the target end.
        f'<marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" '
        f'markerWidth="10" markerHeight="10" orient="auto-start-reverse" markerUnits="userSpaceOnUse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{edge_fill}" /></marker>'
        # Reversed copy for arrow-at-source when the line direction is
        # start→end and we want a head pointing back INTO the source.
        f'<marker id="arrow_rev" viewBox="0 0 10 10" refX="0" refY="5" '
        f'markerWidth="10" markerHeight="10" orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M 10 0 L 0 5 L 10 10 z" fill="{edge_fill}" /></marker>'
        # Open / outlined arrow — "interface" or "implements" in UML dialect.
        f'<marker id="open_arrow" viewBox="0 0 10 10" refX="10" refY="5" '
        f'markerWidth="10" markerHeight="10" orient="auto-start-reverse" markerUnits="userSpaceOnUse">'
        f'<path d="M 0 0 L 10 5 L 0 10" fill="none" stroke="{edge_fill}" stroke-width="1.5" /></marker>'
        f'<marker id="open_arrow_rev" viewBox="0 0 10 10" refX="0" refY="5" '
        f'markerWidth="10" markerHeight="10" orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M 10 0 L 0 5 L 10 10" fill="none" stroke="{edge_fill}" stroke-width="1.5" /></marker>'
        # Filled circle — common "bulb" or "aggregation" terminator.
        f'<marker id="circle_end" viewBox="0 0 10 10" refX="5" refY="5" '
        f'markerWidth="8" markerHeight="8" orient="auto" markerUnits="userSpaceOnUse">'
        f'<circle cx="5" cy="5" r="3.5" fill="{edge_fill}" /></marker>'
        # Hollow diamond — "composition-lite". Solid diamond alternative is
        # available via explicit `end:diamond_solid` if we ever extend.
        f'<marker id="diamond_end" viewBox="0 0 12 10" refX="11" refY="5" '
        f'markerWidth="12" markerHeight="10" orient="auto-start-reverse" markerUnits="userSpaceOnUse">'
        f'<path d="M 0 5 L 6 0 L 12 5 L 6 10 z" fill="{edge_fill}" /></marker>'
        # Tee / bar — perpendicular stub, common "stop" or "must-not" semantic.
        f'<marker id="tee_end" viewBox="0 0 4 10" refX="2" refY="5" '
        f'markerWidth="4" markerHeight="10" orient="auto" markerUnits="userSpaceOnUse">'
        f'<rect x="0" y="0" width="4" height="10" fill="{edge_fill}" /></marker>'
        # Square terminator — deliberate "pinned"-looking end cap.
        f'<marker id="square_end" viewBox="0 0 8 8" refX="4" refY="4" '
        f'markerWidth="8" markerHeight="8" orient="auto" markerUnits="userSpaceOnUse">'
        f'<rect x="1" y="1" width="6" height="6" fill="{edge_fill}" /></marker>'
        '</defs>'
    )

    # Marker id lookup shared by both ends. `is_start=True` flips to the
    # reversed arrow variants so an arrow pointing back at the source is a
    # proper triangle, not an accidental outline.
    def marker_id(kind: str, is_start: bool) -> str | None:
        kind = (kind or "").lower()
        if kind in ("none", "", "off"):
            return None
        if kind == "arrow":
            return "arrow_rev" if is_start else "arrow"
        if kind == "open_arrow":
            return "open_arrow_rev" if is_start else "open_arrow"
        if kind == "circle":
            return "circle_end"
        if kind == "diamond":
            return "diamond_end"
        if kind == "tee":
            return "tee_end"
        if kind == "square":
            return "square_end"
        return None

    parts.append(f'<rect x="{min_x:.1f}" y="{min_y:.1f}" width="{width:.1f}" height="{height:.1f}" fill="{th["bg"]}" />')

    for name, r in layout["lane_rects"].items():
        parts.append(
            f'<rect x="{r["x"]:.1f}" y="{r["y"]:.1f}" width="{r["w"]:.1f}" height="{r["h"]:.1f}" '
            f'rx="10" fill="{th["lane_bg"]}" stroke="{th["lane_border"]}" stroke-dasharray="4 3" />'
            f'<text x="{r["x"]+12:.1f}" y="{r["y"]+18:.1f}" font-size="11" fill="{th["lane_label"]}" '
            f'style="text-transform:uppercase; letter-spacing: 0.08em">{escape(name)}</text>'
        )

    for label, r in layout["box_rects"].items():
        parts.append(
            f'<rect x="{r["x"]:.1f}" y="{r["y"]:.1f}" width="{r["w"]:.1f}" height="{r["h"]:.1f}" '
            f'rx="8" fill="{th["box_bg"]}" stroke="{th["box_border"]}" />'
            f'<text x="{r["x"]+10:.1f}" y="{r["y"]+14:.1f}" font-size="10" fill="{th["box_label"]}" '
            f'style="text-transform:uppercase; letter-spacing: 0.06em">{escape(label)}</text>'
        )

    for n in parsed.nodes:
        p = positions.get(n.name)
        if not p:
            continue
        x, y, w, h = p["x"], p["y"], p["w"], p["h"]
        cx, cy = x + w / 2, y + h / 2
        fill, stroke, text_color, sw, dash = _node_color(n, th)
        shape_el = _shape_path(n, x, y, w, h)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        opacity = _style_num(n, "opacity")
        opacity_attr = f' opacity="{opacity}"' if opacity is not None else ""
        parts.append(
            f'<g fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash_attr}{opacity_attr}>{shape_el}</g>'
        )
        font_size = _style_num(n, "font_size") or 13
        font_family = n.style.get("font_family") or "-apple-system, Segoe UI, sans-serif"
        parts.append(_text_lines(n.label, cx, cy, text_color, font_size, font_family))

    horizontal_dir = layout["direction"] in ("left-to-right", "right-to-left")

    def port_point(rect: dict, port: str) -> tuple[float, float]:
        cx = rect["x"] + rect["w"] / 2
        cy = rect["y"] + rect["h"] / 2
        if port == "t":
            return cx, rect["y"]
        if port == "b":
            return cx, rect["y"] + rect["h"]
        if port == "l":
            return rect["x"], cy
        if port == "r":
            return rect["x"] + rect["w"], cy
        return cx, cy

    def pick_ports(src: dict, tgt: dict) -> tuple[str, str]:
        """Geometry-based port picker — pick the *dominant axis* from the
        source→target vector rather than locking to the chart's flow axis.
        An edge with a mostly-vertical delta now enters the target from
        the top/bottom even under a left-to-right chart, which matches
        user expectation ("a connector coming from above should enter the
        top, not the left"). Tie-break toward the chart axis.
        """
        dx = (tgt["x"] + tgt["w"] / 2) - (src["x"] + src["w"] / 2)
        dy = (tgt["y"] + tgt["h"] / 2) - (src["y"] + src["h"] / 2)
        if abs(dx) > abs(dy) or (abs(dx) == abs(dy) and horizontal_dir):
            return ("r", "l") if dx >= 0 else ("l", "r")
        return ("b", "t") if dy >= 0 else ("t", "b")

    for i, edge in enumerate(parsed.edges):
        sp = positions.get(edge.source)
        tp = positions.get(edge.target)
        if not sp or not tp:
            continue

        auto_sport, auto_tport = pick_ports(sp, tp)
        sport = edge.source_port or auto_sport
        tport = edge.target_port or auto_tport
        sx, sy = port_point(sp, sport)
        tx, ty = port_point(tp, tport)
        # The middle-hop path honours the source exit axis so the
        # arrowhead's tangent matches the entry side. If the source port
        # is t/b, the first segment is vertical; if l/r, horizontal.
        source_vertical = sport in ("t", "b")

        sw = {"thick": 3, "dashed": 1.5, "solid_line": 1.5, "dotted_line": 1.5, "solid": 1.5}.get(edge.kind, 1.5)
        dash = {"dashed": "6 4", "dotted_line": "2 4"}.get(edge.kind, "")
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""

        # Kind-default decorations. An explicit `start:` / `end:` attr on
        # the edge always wins over these defaults.
        default_end = "arrow" if edge.kind in {"solid", "dashed", "thick"} else "none"
        default_start = "none"
        end_kind = str(edge.attrs.get("end", default_end)).lower()
        start_kind = str(edge.attrs.get("start", default_start)).lower()
        end_m = marker_id(end_kind, is_start=False)
        start_m = marker_id(start_kind, is_start=True)
        marker = ""
        if end_m:
            marker += f' marker-end="url(#{end_m})"'
        if start_m:
            marker += f' marker-start="url(#{start_m})"'

        opacity_attr = ""
        op_val = edge.attrs.get("opacity")
        try:
            if op_val is not None and 0 <= float(op_val) <= 1:
                opacity_attr = f' opacity="{float(op_val):.2f}"'
        except (TypeError, ValueError):
            pass
        # Orthogonal L-shape: first and last segment perpendicular to the
        # handle side (so the arrow head's tangent matches the entry axis).
        # Snap near-aligned endpoints together so sub-pixel drift doesn't
        # produce a visible zigzag.
        ALIGN_EPS = 4.0
        if abs(tx - sx) < ALIGN_EPS:
            tx = sx
        if abs(ty - sy) < ALIGN_EPS:
            ty = sy
        dx = tx - sx
        dy = ty - sy
        if dx == 0 or dy == 0:
            path_d = f"M {sx:.1f} {sy:.1f} L {tx:.1f} {ty:.1f}"
        elif source_vertical:
            # Source port is top or bottom: first segment vertical, then
            # horizontal middle, then vertical into target. Final stroke
            # is vertical, so the end-marker's tangent points up/down.
            my = sy + dy / 2
            path_d = (
                f"M {sx:.1f} {sy:.1f} L {sx:.1f} {my:.1f} "
                f"L {tx:.1f} {my:.1f} L {tx:.1f} {ty:.1f}"
            )
        else:
            # Source port is left or right: first segment horizontal, then
            # vertical middle, then horizontal into target.
            mx = sx + dx / 2
            path_d = (
                f"M {sx:.1f} {sy:.1f} L {mx:.1f} {sy:.1f} "
                f"L {mx:.1f} {ty:.1f} L {tx:.1f} {ty:.1f}"
            )
        parts.append(
            f'<path d="{path_d}" fill="none" '
            f'stroke="{th["edge"]}" stroke-width="{sw}"{dash_attr}{opacity_attr}{marker} />'
        )
        if edge.label:
            # Label sits on the middle (perpendicular) segment's midpoint.
            if dx == 0 or dy == 0:
                mx_lbl, my_lbl = (sx + tx) / 2, (sy + ty) / 2
            elif source_vertical:
                mx_lbl, my_lbl = (sx + tx) / 2, sy + dy / 2
            else:
                mx_lbl, my_lbl = sx + dx / 2, (sy + ty) / 2
            parts.append(
                f'<rect x="{mx_lbl-30:.1f}" y="{my_lbl-9:.1f}" width="60" height="14" rx="3" fill="{th["edge_label_bg"]}" />'
                f'<text x="{mx_lbl:.1f}" y="{my_lbl+3:.1f}" text-anchor="middle" font-size="11" '
                f'fill="{th["edge_label"]}">{escape(edge.label)}</text>'
            )

    for n in layout["note_positions"]:
        target = positions.get(n["target"])
        if target:
            tx = target["x"] + target["w"] / 2
            ty = target["y"] + target["h"] / 2
            nx_c = n["x"] + n["w"] / 2
            ny_c = n["y"] + n["h"] / 2
            parts.append(
                f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{nx_c:.1f}" y2="{ny_c:.1f}" '
                f'stroke="{th["note_leader"]}" stroke-width="1" stroke-dasharray="3 3" />'
            )
        parts.append(
            f'<rect x="{n["x"]:.1f}" y="{n["y"]:.1f}" width="{n["w"]:.1f}" height="{n["h"]:.1f}" '
            f'rx="4" fill="{th["note_bg"]}" stroke="{th["note_border"]}" />'
        )
        parts.append(
            f'<text x="{n["x"]+10:.1f}" y="{n["y"]+22:.1f}" font-size="12" fill="{th["note_text"]}">'
            f"{escape(n['text'].splitlines()[0] if n['text'] else '')}</text>"
        )

    for name, r in layout["group_rects"].items():
        parts.append(
            f'<rect x="{r["x"]:.1f}" y="{r["y"]:.1f}" width="{r["w"]:.1f}" height="{r["h"]:.1f}" '
            f'rx="12" fill="none" stroke="{th["group_border"]}" stroke-width="1.5" stroke-dasharray="6 4" />'
            f'<rect x="{r["x"]+12:.1f}" y="{r["y"]-8:.1f}" width="{len(name)*7+12:.1f}" height="14" rx="4" '
            f'fill="{th["bg"]}" />'
            f'<text x="{r["x"]+18:.1f}" y="{r["y"]+2:.1f}" font-size="10" fill="{th["group_label"]}" '
            f'style="text-transform:uppercase; letter-spacing: 0.05em">{escape(name)}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)
