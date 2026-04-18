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
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"></svg>'

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
    parts.append(
        f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{th["edge"]}" /></marker></defs>'
    )

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

    for i, edge in enumerate(parsed.edges):
        sp = positions.get(edge.source)
        tp = positions.get(edge.target)
        if not sp or not tp:
            continue
        sx = sp["x"] + sp["w"] / 2
        sy = sp["y"] + sp["h"] / 2
        tx = tp["x"] + tp["w"] / 2
        ty = tp["y"] + tp["h"] / 2
        sw = {"thick": 3, "dashed": 1.5, "solid_line": 1.5, "dotted_line": 1.5, "solid": 1.5}.get(edge.kind, 1.5)
        dash = {"dashed": "6 4", "dotted_line": "2 4"}.get(edge.kind, "")
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        marker = ' marker-end="url(#arrow)"' if edge.kind in {"solid", "dashed", "thick"} else ""
        parts.append(
            f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" '
            f'stroke="{th["edge"]}" stroke-width="{sw}"{dash_attr}{marker} />'
        )
        if edge.label:
            mx, my = (sx + tx) / 2, (sy + ty) / 2
            parts.append(
                f'<rect x="{mx-30:.1f}" y="{my-9:.1f}" width="60" height="14" rx="3" fill="{th["edge_label_bg"]}" />'
                f'<text x="{mx:.1f}" y="{my+3:.1f}" text-anchor="middle" font-size="11" '
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
