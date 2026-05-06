from __future__ import annotations

from .parser import Node, Parsed

DEFAULTS = {
    "node_width": 160,
    "node_height": 70,
    "h_gap": 60,
    "v_gap": 80,
    "swimlane_gap": 40,
    "container_padding": 40,   # 2×grid — swimlane inner margin, symmetrical
    "box_padding": 40,          # 2×grid — box margin on all 4 sides; top clearance covers ~20px header pill
    "group_padding": 20,        # 1×grid
    "note_offset": 40,          # 2×grid
    "note_width": 160,
    "note_height": 60,          # 3×grid
    "margin": 60,               # 3×grid
    "snap_grid": 20,            # base grid unit; all positions/sizes snap to this
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


def _round_to_even_grid(value: int, grid: int) -> int:
    """Round UP to the nearest even multiple of `grid`. The "even" part is
    why ports stay grid-aligned: a node centred on `(x, y)` exposes its
    `left` port at `(x, y + h/2)`. If `h` is `n * grid`, that midpoint
    only lands on a grid line when `n` is even — otherwise it falls
    halfway between, and the connector running into that port snaps to
    the wrong row. Using `2*grid` as the quantum guarantees every face
    midpoint is a grid intersection."""
    if grid <= 0:
        return value
    quantum = grid * 2
    return ((value + quantum - 1) // quantum) * quantum


def _measure(node: Node, base_w: int, base_h: int, grid: int = 10) -> tuple[int, int]:
    lines = node.label.count("\n") + 1
    h = max(base_h, 36 + 18 * lines)
    longest = max((len(ln) for ln in node.label.split("\n")), default=4)
    w = max(base_w, 24 + int(longest * 8.2))
    pad_w, pad_h = SHAPE_PADDING_MULT.get(node.shape, (1.0, 1.0))
    w = int(w * pad_w)
    h = int(h * pad_h)
    w_override = _as_positive_int(node.attrs.get("width"))
    h_override = _as_positive_int(node.attrs.get("height"))
    final_w = w_override or w
    final_h = h_override or h
    # Snap to an even grid quantum so every port (centre of a face)
    # lands exactly on a grid intersection. Dimensions can grow but
    # never shrink — preserves the user's `width:` / `height:` lower
    # bounds while keeping the routing aligned.
    return _round_to_even_grid(final_w, grid), _round_to_even_grid(final_h, grid)


def _snap(value: float, grid: int) -> float:
    if grid <= 0:
        return value
    return round(value / grid) * grid


def _snap_up(value: float, grid: int) -> float:
    """Round UP to the next multiple of `grid`. Used to make centre
    positions land on grid lines (paired with `_round_to_even_grid` for
    sizes, every port is then a grid intersection)."""
    if grid <= 0:
        return value
    return ((int(value) + grid - 1) // grid) * grid


def _label_run_px(label: str) -> int:
    """Approximate visual width (px) needed for a connector label rendered
    by SmartEdge.svelte. Mirrors the frontend formula
    `max(30, longest * 6 + 12)`: ~6px per glyph at the 11px sans body
    font, plus a small horizontal pad for the label background. Returns
    0 for empty labels so callers can skip widening when nothing's drawn."""
    if not label:
        return 0
    longest = max((len(ln) for ln in label.split("\n")), default=0)
    if longest == 0:
        return 0
    return max(30, longest * 6 + 12)


def _container_pad(label: str, base_pad: int, snap: int) -> int:
    """Symmetrical padding for any container whose title label sits at the
    top edge. Each side gets the same clearance so the layout stays balanced.
    Accounts for multi-line labels: 3 lines ≈ 3×20px + insets.
    Result is always a multiple of `snap`."""
    lines = max(1, label.count("\n") + 1)
    # 20 px per line (covers 10–11 px font + leading + inset), plus an 8 px
    # top inset (the CSS `top: 4–6px` offset on the pill).
    header_h = lines * 20 + 8
    needed = header_h + snap   # header + one grid unit of breathing room
    g = max(snap, 1)
    return ((max(base_pad, needed) + g - 1) // g) * g


def compute_layout(parsed: Parsed) -> dict:
    cfg = {
        **DEFAULTS,
        **{k: v for k, v in parsed.settings.items() if isinstance(v, (int, float))},
    }
    direction = parsed.direction
    nodes = parsed.nodes
    # Resolve snap grid early — used by _container_pad and step_gap.
    snap: int = int(cfg["snap_grid"]) if int(cfg.get("snap_grid", 1)) > 0 else 1

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

    sizes = {
        n.name: _measure(n, cfg["node_width"], cfg["node_height"], cfg["snap_grid"])
        for n in nodes
    }

    all_steps = sorted({n.step for n in nodes}) if nodes else []

    # Per-step adaptive gap. The base `h_gap` (or `v_gap`, depending on
    # direction) is enough for unlabelled connectors, but a connector with
    # a label like "no" / "yes" / "approved" needs a horizontal/vertical
    # run long enough for the label's background rect to sit on it without
    # crowding either node face. Walk all forward edges (source.step <
    # target.step) and find the widest label that crosses each step
    # boundary, then bump that gap so the label has room.
    #
    # Backward / self-loop edges are skipped — they route over a long
    # detour where the label can settle on one of the long legs regardless
    # of the inter-step gap.
    step_index = {s: i for i, s in enumerate(all_steps)}
    node_step = {n.name: n.step for n in nodes}
    forward_label_max: dict[int, int] = {}
    # Parallel-corridor count: every edge that crosses a given boundary
    # demands its own ~OFFSET_STEP-px lane in the gap. Counting these per
    # boundary lets the layout open the gap proportionally — three
    # parallel back-edges between two rows ends up with 3 * lane_px of
    # extra clearance, so they never stack in the same corridor.
    edges_crossing: dict[int, int] = {}
    if parsed.edges and len(all_steps) >= 2:
        for ed in parsed.edges:
            ss = node_step.get(ed.source)
            ts = node_step.get(ed.target)
            if ss is None or ts is None:
                continue
            if ss == ts:
                continue  # same-step edge; routes around the cell, not across
            # Edge crosses every step boundary between min and max. Label
            # rides the longest segment, which runs along the gap; widen
            # every boundary it crosses so the label has room. Forward and
            # back edges both qualify — for a back-edge, the U-detour's
            # long horizontal still sits inside this gap.
            lo = min(ss, ts)
            hi = max(ss, ts)
            si = step_index.get(lo)
            ti = step_index.get(hi)
            if si is None or ti is None:
                continue
            px = _label_run_px(ed.label) if ed.label else 0
            for k in range(si, ti):
                if px > 0:
                    forward_label_max[k] = max(forward_label_max.get(k, 0), px)
                edges_crossing[k] = edges_crossing.get(k, 0) + 1

    # Per-lane dynamic container padding: a swimlane titled "My Multi-Line\nHeader"
    # needs more inset clearance than a single-word lane name.
    lane_pad: dict[str, int] = {}
    for sl in parsed.swimlanes:
        lane_pad[sl.name] = _container_pad(sl.name, cfg["container_padding"], snap)
    if "" not in lane_pad:
        lane_pad[""] = int(cfg["container_padding"])

    lane_breadth: dict[str, int] = {}
    for lane in lane_order:
        lp = lane_pad.get(lane, int(cfg["container_padding"]))
        widest = cfg["node_width"]
        for s in all_steps:
            cell = by_lane_step.get((lane, s), [])
            if cell:
                total = sum(sizes[cn.name][0] for cn in cell) + cfg["h_gap"] * (len(cell) - 1)
                widest = max(widest, total)
        lane_breadth[lane] = widest + 2 * lp

    step_depth: dict[int, int] = {}
    for s in all_steps:
        tallest = cfg["node_height"]
        for lane in lane_order:
            for cn in by_lane_step.get((lane, s), []):
                tallest = max(tallest, sizes[cn.name][1])
        step_depth[s] = tallest

    horizontal = direction in ("left-to-right", "right-to-left")
    reverse_steps = direction in ("bottom-to-top", "right-to-left")
    # Pin the page margin to the grid so the very first cursor position
    # (margin) lands on a grid line. Otherwise everything downstream
    # carries the offset.
    margin = int(_snap_up(cfg["margin"], snap))
    steps_ordered = list(reversed(all_steps)) if reverse_steps else all_steps

    # Map "boundary k between steps_ordered[k] and steps_ordered[k+1]" to
    # the extra pixels we need beyond the configured base gap. The
    # `forward_label_max` index was built against the natural step order;
    # if we're rendering reversed, mirror the indices so boundary 0 is
    # still "the first gap we walk past".
    base_gap = cfg["h_gap"] if horizontal else cfg["v_gap"]
    # Per-edge corridor — every connector crossing a boundary needs its
    # own lane in the gap. Picked to leave a clear visual band between
    # adjacent corridors at typical zoom levels.
    corridor_px = 18
    label_pad = 18

    def step_gap(boundary_idx_in_ordered: int) -> int:
        """How much space to leave AFTER the step at this position,
        before the next step. `boundary_idx_in_ordered` is 0-based against
        `steps_ordered`."""
        if reverse_steps:
            # If reversed, boundary i in ordered corresponds to boundary
            # (len-2-i) in natural order.
            natural_i = len(all_steps) - 2 - boundary_idx_in_ordered
        else:
            natural_i = boundary_idx_in_ordered
        # Two demands stack: label width and parallel-edge corridors.
        # Take the bigger of the two — they don't compound (the label
        # rides one of the corridors). The +1 on edge count gives a
        # symmetric margin around the corridor stack.
        label_need = forward_label_max.get(natural_i, 0)
        edge_count = edges_crossing.get(natural_i, 0)
        edge_need = (edge_count + 1) * corridor_px if edge_count > 0 else 0
        needed = max(label_need + label_pad, edge_need)
        if needed <= 0:
            return base_gap
        gap = max(base_gap, needed)
        # Snap up to a grid multiple so the cumulative cursor stays
        # aligned and ports between steps land on grid lines.
        return _snap_up(gap, snap)

    positions: dict[str, dict] = {}
    lane_rects: dict[str, dict] = {}

    if not horizontal:
        # Snap each lane's breadth UP to an even grid quantum so its
        # midpoint (where shapes centre) lands on a grid line. Same
        # rationale as `_round_to_even_grid` for nodes.
        lane_quantum = snap * 2
        for lane in lane_order:
            lane_breadth[lane] = (
                (lane_breadth[lane] + lane_quantum - 1) // lane_quantum
            ) * lane_quantum
        lane_center: dict[str, float] = {}
        cursor = margin
        swimlane_gap = int(_snap_up(cfg["swimlane_gap"], snap))
        for lane in lane_order:
            lane_center[lane] = cursor + lane_breadth[lane] / 2
            cursor += lane_breadth[lane] + swimlane_gap
        total_w = cursor - swimlane_gap + margin

        step_center: dict[int, float] = {}
        cursor = margin
        last_gap = base_gap
        for i, s in enumerate(steps_ordered):
            step_center[s] = cursor + step_depth[s] / 2
            # Use the adaptive gap between this step and the next; the
            # final step doesn't need a trailing gap (we subtract it
            # below to compute total_h).
            gap = step_gap(i) if i < len(steps_ordered) - 1 else base_gap
            cursor += step_depth[s] + gap
            last_gap = gap
        total_h = cursor - last_gap + margin

        for (lane, step), cell in by_lane_step.items():
            cx = lane_center[lane]
            cy = step_center[step]
            widths = [sizes[cn.name][0] for cn in cell]
            cell_w = sum(widths) + cfg["h_gap"] * (len(cell) - 1)
            x_cursor = cx - cell_w / 2
            for cn, w in zip(cell, widths):
                _, h = sizes[cn.name]
                pinned = cn.position is not None
                if pinned:
                    x, y = cn.position[0], cn.position[1]
                else:
                    x, y = x_cursor, cy - h / 2
                positions[cn.name] = {
                    # Snap pinned positions to the grid; never snap auto-placed
                    # ones — snapping drifts center-x per node width, which
                    # breaks vertical alignment between shapes on the same lane.
                    "x": _snap(x, snap) if pinned else x,
                    "y": _snap(y, snap) if pinned else y,
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
        lane_quantum = snap * 2
        for lane in lane_order:
            lane_breadth[lane] = (
                (lane_breadth[lane] + lane_quantum - 1) // lane_quantum
            ) * lane_quantum
        lane_center: dict[str, float] = {}
        cursor = margin
        swimlane_gap = int(_snap_up(cfg["swimlane_gap"], snap))
        for lane in lane_order:
            lane_center[lane] = cursor + lane_breadth[lane] / 2
            cursor += lane_breadth[lane] + swimlane_gap
        total_h = cursor - swimlane_gap + margin

        step_center: dict[int, float] = {}
        cursor = margin
        step_w_lookup: dict[int, int] = {}
        last_gap = base_gap
        for i, s in enumerate(steps_ordered):
            widest = cfg["node_width"]
            for lane in lane_order:
                for cn in by_lane_step.get((lane, s), []):
                    widest = max(widest, sizes[cn.name][0])
            step_w_lookup[s] = widest
            step_center[s] = cursor + widest / 2
            gap = step_gap(i) if i < len(steps_ordered) - 1 else base_gap
            cursor += widest + gap
            last_gap = gap
        total_w = cursor - last_gap + margin

        for (lane, step), cell in by_lane_step.items():
            cx = step_center[step]
            cy = lane_center[lane]
            heights = [sizes[cn.name][1] for cn in cell]
            cell_h = sum(heights) + cfg["v_gap"] * (len(cell) - 1)
            y_cursor = cy - cell_h / 2
            for cn, h in zip(cell, heights):
                w, _ = sizes[cn.name]
                pinned = cn.position is not None
                if pinned:
                    x, y = cn.position[0], cn.position[1]
                else:
                    x, y = cx - w / 2, y_cursor
                positions[cn.name] = {
                    # Only snap pinned positions — see the TB branch for the why.
                    "x": _snap(x, snap) if pinned else x,
                    "y": _snap(y, snap) if pinned else y,
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

    # Grow each swimlane rect to contain ALL its descendants: nodes, boxes
    # that live inside the lane, and notes attached to nodes in the lane.
    # A pinned @(x,y) position or a large child can push content outside
    # the step-derived bounds; the lane rectangle must always enclose every
    # descendant with symmetric clearance.
    lane_children: dict[str, list[str]] = {lane: [] for lane in lane_rects}
    for n in nodes:
        lane = n.swimlane or ""
        if lane in lane_rects:
            lane_children[lane].append(n.name)
    # Use per-lane dynamic padding for the grow pass so that lanes with
    # longer title labels keep the correct minimum inset.
    _grow_pad = lane_pad  # dict built earlier: {lane_name -> int}
    for lane, rect in lane_rects.items():
        gp = _grow_pad.get(lane, int(cfg["container_padding"]))
        children = [positions[nm] for nm in lane_children.get(lane, []) if nm in positions]
        if not children:
            continue
        cx0 = min(r["x"] for r in children) - gp
        cy0 = min(r["y"] for r in children) - gp
        cx1 = max(r["x"] + r["w"] for r in children) + gp
        cy1 = max(r["y"] + r["h"] for r in children) + gp
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
        pad = _container_pad(b.label, cfg["box_padding"], snap)
        rect = _bbox(b.members, pad)
        if rect:
            box_rects[b.label] = rect

    group_rects: dict[str, dict] = {}
    for g in parsed.groups:
        rect = _bbox(g.members, cfg["group_padding"])
        if rect:
            group_rects[g.name] = rect

    note_positions: list[dict] = []
    node_lane = {n.name: (n.swimlane or "") for n in nodes}
    for note in parsed.notes:
        target = positions.get(note.target)
        if not target:
            continue
        nw, nh = cfg["note_width"], cfg["note_height"]
        nx = target["x"] + target["w"] + cfg["note_offset"]
        ny = target["y"] + (target["h"] - nh) / 2
        np_ = {
            "text": note.text,
            "target": note.target,
            "x": _snap(nx, snap),
            "y": _snap(ny, snap),
            "w": nw,
            "h": nh,
        }
        note_positions.append(np_)

        # Expand the note target's swimlane rect to enclose the note.
        lane = node_lane.get(note.target, "")
        if lane in lane_rects:
            r = lane_rects[lane]
            gp = _grow_pad.get(lane, int(cfg["container_padding"]))
            r["x"] = min(r["x"], np_["x"] - gp)
            r["y"] = min(r["y"], np_["y"] - gp)
            nx1 = np_["x"] + np_["w"] + gp
            ny1 = np_["y"] + np_["h"] + gp
            r["w"] = max(r["x"] + r["w"], nx1) - r["x"]
            r["h"] = max(r["y"] + r["h"], ny1) - r["y"]

    # Expand each lane rect to also contain any box rects that sit inside it.
    box_lane: dict[str, str] = {}
    for b in parsed.boxes:
        if b.members:
            first_member = b.members[0]
            box_lane[b.label] = node_lane.get(first_member, "")
    for b_label, b_rect in box_rects.items():
        lane = box_lane.get(b_label, "")
        if lane in lane_rects:
            r = lane_rects[lane]
            gp = _grow_pad.get(lane, int(cfg["container_padding"]))
            r["x"] = min(r["x"], b_rect["x"] - gp)
            r["y"] = min(r["y"], b_rect["y"] - gp)
            bx1 = b_rect["x"] + b_rect["w"] + gp
            by1 = b_rect["y"] + b_rect["h"] + gp
            r["w"] = max(r["x"] + r["w"], bx1) - r["x"]
            r["h"] = max(r["y"] + r["h"], by1) - r["y"]

    return {
        "positions": positions,
        "lane_rects": lane_rects,
        "box_rects": box_rects,
        "group_rects": group_rects,
        "note_positions": note_positions,
        "direction": direction,
    }
