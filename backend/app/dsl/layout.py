from __future__ import annotations

from .parser import Node, Parsed

DEFAULTS = {
    "node_width": 160,
    "node_height": 70,
    "h_gap": 60,
    "v_gap": 80,
    "swimlane_gap": 40,
    "container_padding": 32,
    "box_padding": 18,
    "group_padding": 14,
    "note_offset": 28,
    "note_width": 160,
    "note_height": 56,
    "margin": 60,
    "snap_grid": 10,
}

SHAPE_PADDING_MULT = {
    "diamond": (1.45, 1.4),
    "circle": (1.3, 1.3),
    "hexagon": (1.15, 1.05),
    "cylinder": (1.05, 1.15),
}


def _as_positive_int(value: object) -> int | None:
    try:
        n = int(float(str(value)))
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _measure(node: Node, base_w: int, base_h: int) -> tuple[int, int]:
    lines = node.label.count("\n") + 1
    h = max(base_h, 36 + 18 * lines)
    longest = max((len(ln) for ln in node.label.split("\n")), default=4)
    w = max(base_w, 24 + int(longest * 8.2))
    pad_w, pad_h = SHAPE_PADDING_MULT.get(node.shape, (1.0, 1.0))
    w = int(w * pad_w)
    h = int(h * pad_h)
    w_override = _as_positive_int(node.attrs.get("width"))
    h_override = _as_positive_int(node.attrs.get("height"))
    return w_override or w, h_override or h


def _snap(value: float, grid: int) -> float:
    if grid <= 0:
        return value
    return round(value / grid) * grid


def compute_layout(parsed: Parsed) -> dict:
    cfg = {
        **DEFAULTS,
        **{k: v for k, v in parsed.settings.items() if isinstance(v, (int, float))},
    }
    direction = parsed.direction
    nodes = parsed.nodes

    # Nodes marked type:end without an explicit step land alongside type:start
    # at step 0. Shift them past the last explicit step so they render as the
    # final row / column.
    explicit_steps = [n.step for n in nodes if n.step_explicit]
    if explicit_steps:
        end_step = max(explicit_steps) + 1
        for n in nodes:
            if not n.step_explicit and n.attrs.get("type") == "end":
                n.step = end_step

    lane_order: list[str] = [sl.name for sl in parsed.swimlanes]
    if not lane_order:
        lane_order = [""]
    declared = set(lane_order)
    for n in nodes:
        lane = n.swimlane or ""
        if lane not in declared:
            lane_order.append(lane)
            declared.add(lane)

    by_lane_step: dict[tuple[str, int], list[Node]] = {}
    for n in nodes:
        by_lane_step.setdefault((n.swimlane or "", n.step), []).append(n)

    sizes = {n.name: _measure(n, cfg["node_width"], cfg["node_height"]) for n in nodes}

    all_steps = sorted({n.step for n in nodes}) if nodes else []

    lane_breadth: dict[str, int] = {}
    for lane in lane_order:
        widest = cfg["node_width"]
        for s in all_steps:
            cell = by_lane_step.get((lane, s), [])
            if cell:
                total = sum(sizes[cn.name][0] for cn in cell) + cfg["h_gap"] * (len(cell) - 1)
                widest = max(widest, total)
        lane_breadth[lane] = widest + 2 * cfg["container_padding"]

    step_depth: dict[int, int] = {}
    for s in all_steps:
        tallest = cfg["node_height"]
        for lane in lane_order:
            for cn in by_lane_step.get((lane, s), []):
                tallest = max(tallest, sizes[cn.name][1])
        step_depth[s] = tallest

    horizontal = direction in ("left-to-right", "right-to-left")
    reverse_steps = direction in ("bottom-to-top", "right-to-left")
    margin = cfg["margin"]
    steps_ordered = list(reversed(all_steps)) if reverse_steps else all_steps
    snap = cfg["snap_grid"]

    positions: dict[str, dict] = {}
    lane_rects: dict[str, dict] = {}

    if not horizontal:
        lane_center: dict[str, float] = {}
        cursor = margin
        for lane in lane_order:
            lane_center[lane] = cursor + lane_breadth[lane] / 2
            cursor += lane_breadth[lane] + cfg["swimlane_gap"]
        total_w = cursor - cfg["swimlane_gap"] + margin

        step_center: dict[int, float] = {}
        cursor = margin
        for s in steps_ordered:
            step_center[s] = cursor + step_depth[s] / 2
            cursor += step_depth[s] + cfg["v_gap"]
        total_h = cursor - cfg["v_gap"] + margin

        for (lane, step), cell in by_lane_step.items():
            cx = lane_center[lane]
            cy = step_center[step]
            widths = [sizes[cn.name][0] for cn in cell]
            cell_w = sum(widths) + cfg["h_gap"] * (len(cell) - 1)
            x_cursor = cx - cell_w / 2
            for cn, w in zip(cell, widths):
                _, h = sizes[cn.name]
                if cn.position:
                    x, y = cn.position[0], cn.position[1]
                else:
                    x, y = x_cursor, cy - h / 2
                positions[cn.name] = {
                    "x": _snap(x, snap),
                    "y": _snap(y, snap),
                    "w": w,
                    "h": h,
                }
                x_cursor += w + cfg["h_gap"]

        cursor = margin
        for lane in lane_order:
            if lane:
                lane_rects[lane] = {
                    "x": cursor,
                    "y": margin - cfg["container_padding"],
                    "w": lane_breadth[lane],
                    "h": total_h - 2 * margin + 2 * cfg["container_padding"],
                }
            cursor += lane_breadth[lane] + cfg["swimlane_gap"]
    else:
        lane_center: dict[str, float] = {}
        cursor = margin
        for lane in lane_order:
            lane_center[lane] = cursor + lane_breadth[lane] / 2
            cursor += lane_breadth[lane] + cfg["swimlane_gap"]
        total_h = cursor - cfg["swimlane_gap"] + margin

        step_center: dict[int, float] = {}
        cursor = margin
        step_w_lookup: dict[int, int] = {}
        for s in steps_ordered:
            widest = cfg["node_width"]
            for lane in lane_order:
                for cn in by_lane_step.get((lane, s), []):
                    widest = max(widest, sizes[cn.name][0])
            step_w_lookup[s] = widest
            step_center[s] = cursor + widest / 2
            cursor += widest + cfg["h_gap"]
        total_w = cursor - cfg["h_gap"] + margin

        for (lane, step), cell in by_lane_step.items():
            cx = step_center[step]
            cy = lane_center[lane]
            heights = [sizes[cn.name][1] for cn in cell]
            cell_h = sum(heights) + cfg["v_gap"] * (len(cell) - 1)
            y_cursor = cy - cell_h / 2
            for cn, h in zip(cell, heights):
                w, _ = sizes[cn.name]
                if cn.position:
                    x, y = cn.position[0], cn.position[1]
                else:
                    x, y = cx - w / 2, y_cursor
                positions[cn.name] = {
                    "x": _snap(x, snap),
                    "y": _snap(y, snap),
                    "w": w,
                    "h": h,
                }
                y_cursor += h + cfg["v_gap"]

        cursor = margin
        for lane in lane_order:
            if lane:
                lane_rects[lane] = {
                    "x": margin - cfg["container_padding"],
                    "y": cursor,
                    "w": total_w - 2 * margin + 2 * cfg["container_padding"],
                    "h": lane_breadth[lane],
                }
            cursor += lane_breadth[lane] + cfg["swimlane_gap"]

    # Grow each swimlane rect to contain all its children. A pinned @(x,y)
    # position can push a node outside the step-derived bounds; the lane
    # rectangle must always enclose every child of the swimlane.
    lane_children: dict[str, list[str]] = {lane: [] for lane in lane_rects}
    for n in nodes:
        lane = n.swimlane or ""
        if lane in lane_rects:
            lane_children[lane].append(n.name)
    lane_pad = cfg["container_padding"]
    for lane, rect in lane_rects.items():
        children = [positions[nm] for nm in lane_children.get(lane, []) if nm in positions]
        if not children:
            continue
        cx0 = min(r["x"] for r in children) - lane_pad
        cy0 = min(r["y"] for r in children) - lane_pad
        cx1 = max(r["x"] + r["w"] for r in children) + lane_pad
        cy1 = max(r["y"] + r["h"] for r in children) + lane_pad
        x0 = min(rect["x"], cx0)
        y0 = min(rect["y"], cy0)
        x1 = max(rect["x"] + rect["w"], cx1)
        y1 = max(rect["y"] + rect["h"], cy1)
        lane_rects[lane] = {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}

    def _bbox(names: list[str], pad: int) -> dict | None:
        rects = [positions[n] for n in names if n in positions]
        if not rects:
            return None
        x0 = min(r["x"] for r in rects) - pad
        y0 = min(r["y"] for r in rects) - pad
        x1 = max(r["x"] + r["w"] for r in rects) + pad
        y1 = max(r["y"] + r["h"] for r in rects) + pad
        return {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}

    box_rects: dict[str, dict] = {}
    for b in parsed.boxes:
        rect = _bbox(b.members, cfg["box_padding"])
        if rect:
            box_rects[b.label] = rect

    group_rects: dict[str, dict] = {}
    for g in parsed.groups:
        rect = _bbox(g.members, cfg["group_padding"])
        if rect:
            group_rects[g.name] = rect

    note_positions: list[dict] = []
    for note in parsed.notes:
        target = positions.get(note.target)
        if not target:
            continue
        nw, nh = cfg["note_width"], cfg["note_height"]
        nx = target["x"] + target["w"] + cfg["note_offset"]
        ny = target["y"] + (target["h"] - nh) / 2
        note_positions.append(
            {
                "text": note.text,
                "target": note.target,
                "x": _snap(nx, snap),
                "y": _snap(ny, snap),
                "w": nw,
                "h": nh,
            }
        )

    return {
        "positions": positions,
        "lane_rects": lane_rects,
        "box_rects": box_rects,
        "group_rects": group_rects,
        "note_positions": note_positions,
        "direction": direction,
    }
