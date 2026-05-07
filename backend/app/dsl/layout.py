from __future__ import annotations

from .parser import Node, Parsed

# ── Grid system ─────────────────────────────────────────────────────────
# G is the single visual unit.  Every spacing constant below is expressed
# as a multiple of G so the whole layout scales uniformly if G changes.
G = 20  # px

DEFAULTS = {
    "node_width":          8 * G,       # 160
    "node_height":         4 * G - 10,  # 70  (slightly under 4G keeps text tight)
    "h_gap":               3 * G,       # 60  space between sibling nodes in same cell
    "v_gap":               4 * G,       # 80  vertical gap between nodes in LR lane
    "swimlane_gap":        2 * G,       # 40  base horizontal gap between lanes (TB)
    "container_padding":   3 * G,       # 60  lane inset — 3G gives 1G lane-to-box margin
    "box_padding":         2 * G,       # 40  box inset — capped at container_padding-G
    "group_padding":       1 * G,       # 20
    "note_offset":         1 * G,       # 20  gap from node right edge to note left edge
    "note_width":          4 * G,       # 80  narrower than default node — encourages wrap
    "note_height":         2 * G,       # 40  base — grows to target_h + 2G clearance
    "margin":              3 * G,       # 60  canvas margin around entire diagram
    "snap_grid":           G // 2,      # 10  position/size snap quantum
}

SHAPE_PADDING_MULT = {
    "diamond":  (1.45, 1.4),
    "circle":   (1.3, 1.3),
    "hexagon":  (1.15, 1.05),
    "cylinder": (1.05, 1.15),
}


def _as_positive_int(value: object) -> int | None:
    try:
        n = int(float(str(value)))
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _round_to_even_grid(value: int, grid: int) -> int:
    """Round UP to the nearest even multiple of `grid`.  The "even" part is
    why ports stay grid-aligned: a node centred on (x, y) exposes its left
    port at (x, y + h/2).  If h is n*grid that midpoint only lands on a
    grid line when n is even — otherwise it falls halfway between."""
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
    return _round_to_even_grid(final_w, grid), _round_to_even_grid(final_h, grid)


def _snap(value: float, grid: int) -> float:
    if grid <= 0:
        return value
    return round(value / grid) * grid


def _snap_up(value: float, grid: int) -> float:
    if grid <= 0:
        return value
    return ((int(value) + grid - 1) // grid) * grid


def _compute_G(cfg: dict, snap: int) -> int:
    """Resolve the visual grid unit G from the configured font size.
    Scales 1.8× the font size, snapped up to 2*snap so G stays an
    integer multiple of the snap quantum (and thus an integer)."""
    font_size = int(cfg.get("font_size", 11))
    line_height = font_size * 1.8
    quantum = max(1, snap * 2)
    return max(quantum, int(_snap_up(line_height, quantum)))


def _label_run_px(label: str) -> int:
    """Approximate rendered width of a connector label: ~6 px/glyph + 12 px
    horizontal padding.  Returns 0 for empty labels."""
    if not label:
        return 0
    longest = max((len(ln) for ln in label.split("\n")), default=0)
    if longest == 0:
        return 0
    return max(30, longest * 6 + 12)


def _container_pad(label: str, base_pad: int, snap: int, max_pad: int | None = None) -> int:
    """Symmetrical clearance for any container whose title pill sits at the
    top edge.  Grows for multi-line labels; always a multiple of `snap`;
    never exceeds `max_pad` (used to keep boxes inside their enclosing lane).

    Formula: each label line needs ~20 px (11 px font + leading + inset),
    plus 8 px of top-pill inset, plus one snap unit of breathing room."""
    lines = max(1, label.count("\n") + 1)
    header_h = lines * 20 + 8
    needed = header_h + snap
    g = max(snap, 1)
    result = ((max(base_pad, needed) + g - 1) // g) * g
    if max_pad is not None:
        result = min(result, max_pad)
    return result


def compute_layout(parsed: Parsed) -> dict:
    cfg = {
        **DEFAULTS,
        **{k: v for k, v in parsed.settings.items() if isinstance(v, (int, float))},
    }
    direction = parsed.direction
    nodes = parsed.nodes
    snap: int = int(cfg["snap_grid"]) if int(cfg.get("snap_grid", 1)) > 0 else 1
    G = _compute_G(cfg, snap)

    # Shift type:end nodes without an explicit step past the last explicit step.
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
        n.name: _measure(n, cfg["node_width"], cfg["node_height"], G)
        for n in nodes
    }

    all_steps = sorted({n.step for n in nodes}) if nodes else []

    # ── Gap analysis ────────────────────────────────────────────────────
    # Walk all edges to find:
    # (a) widest label that crosses each STEP boundary   → forward_label_max
    # (b) edge count per step boundary                   → edges_crossing
    # (c) widest cross-lane connector label              → cross_lane_label_max
    #
    # (a)+(b) drive per-step vertical gap; (c) drives the swimlane gap so
    # labels on connectors that cross between lanes have room to breathe.
    step_index   = {s: i for i, s in enumerate(all_steps)}
    node_step    = {n.name: n.step    for n in nodes}
    node_lane    = {n.name: (n.swimlane or "") for n in nodes}

    forward_label_max: dict[int, int] = {}
    edges_crossing:    dict[int, int] = {}
    cross_lane_label_max = 0

    if parsed.edges and len(all_steps) >= 2:
        for ed in parsed.edges:
            ss = node_step.get(ed.source)
            ts = node_step.get(ed.target)
            if ss is None or ts is None:
                continue
            sl = node_lane.get(ed.source, "")
            tl = node_lane.get(ed.target, "")
            label_px = _label_run_px(ed.label) if ed.label else 0
            if sl != tl and label_px > 0:
                cross_lane_label_max = max(cross_lane_label_max, label_px)
            if ss == ts:
                continue
            lo, hi = min(ss, ts), max(ss, ts)
            si = step_index.get(lo)
            ti = step_index.get(hi)
            if si is None or ti is None:
                continue
            for k in range(si, ti):
                if label_px > 0:
                    forward_label_max[k] = max(forward_label_max.get(k, 0), label_px)
                edges_crossing[k] = edges_crossing.get(k, 0) + 1

    # Dynamic swimlane gap: wide enough for the widest cross-lane connector
    # label to sit centered in the corridor with G px of padding on each side.
    #   needed = label_width + 2*G
    # Snap up to the grid so lane positions stay aligned.
    base_swimlane_gap = int(cfg["swimlane_gap"])
    if cross_lane_label_max > 0:
        needed_gap = cross_lane_label_max + 2 * G
        base_swimlane_gap = max(base_swimlane_gap, needed_gap)
    swimlane_gap_px: int = int(_snap_up(base_swimlane_gap, G))

    # ── Per-lane padding ─────────────────────────────────────────────────
    # container_padding is the minimum; multi-line lane names need more.
    # Box padding is capped at container_padding - G so there is always at
    # least one grid unit of visible margin between box border and lane border.
    container_pad_int = int(cfg["container_padding"])
    box_pad_cap = container_pad_int - G  # max box padding inside a lane

    lane_pad: dict[str, int] = {}
    for sl in parsed.swimlanes:
        lane_pad[sl.name] = _container_pad(sl.name, container_pad_int, G)
    if "" not in lane_pad:
        lane_pad[""] = container_pad_int

    lane_breadth: dict[str, int] = {}
    for lane in lane_order:
        lp = lane_pad.get(lane, container_pad_int)
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

    horizontal    = direction in ("left-to-right", "right-to-left")
    reverse_steps = direction in ("bottom-to-top", "right-to-left")
    margin        = int(_snap_up(cfg["margin"], G))
    steps_ordered = list(reversed(all_steps)) if reverse_steps else all_steps
    base_gap      = cfg["h_gap"] if horizontal else cfg["v_gap"]

    # Per-edge corridor uses G/2 so three parallel connectors occupy 3G of gap.
    corridor_px = G // 2      # 10 px per corridor slot
    label_pad_px = G          # padding around the label rect

    # Box-edge detection — when adjacent steps belong to different boxes, the
    # default step gap leaves zero pixels between the two box borders (each
    # box extends `box_padding` past its members). Track which steps each
    # box covers so step_gap() can bump the gap to clear both paddings + G.
    box_pad_value = int(cfg["box_padding"])
    box_steps: dict[str, set[int]] = {}
    for n in nodes:
        if n.box:
            box_steps.setdefault(n.box, set()).add(n.step)
    boxes_at: dict[int, frozenset[str]] = {}
    for s in all_steps:
        boxes_at[s] = frozenset(b for b, ss in box_steps.items() if s in ss)

    def step_gap(boundary_idx: int) -> int:
        if reverse_steps:
            natural_i = len(all_steps) - 2 - boundary_idx
        else:
            natural_i = boundary_idx
        label_need = forward_label_max.get(natural_i, 0)
        edge_count = edges_crossing.get(natural_i, 0)
        edge_need  = (edge_count + 1) * corridor_px if edge_count > 0 else 0
        needed     = max(label_need + label_pad_px, edge_need)
        # If this boundary crosses different box memberships (e.g. one box
        # ends and another begins), reserve enough for both boxes' inner
        # padding plus a G of visible separation between their borders.
        if natural_i + 1 < len(all_steps):
            s_lo = all_steps[natural_i]
            s_hi = all_steps[natural_i + 1]
            boxes_lo = boxes_at.get(s_lo, frozenset())
            boxes_hi = boxes_at.get(s_hi, frozenset())
            # Different non-empty box sets that don't share a box → adjacent
            # boxes meet here. (Same-set means we're staying in the same
            # box; one-side-empty means a box meeting unboxed nodes, which
            # the default step gap already handles.)
            both_boxed = bool(boxes_lo) and bool(boxes_hi)
            if both_boxed and boxes_lo.isdisjoint(boxes_hi):
                needed = max(needed, 2 * box_pad_value + G)
        gap = max(base_gap, needed) if needed > 0 else base_gap
        return int(_snap_up(gap, G))

    positions:  dict[str, dict] = {}
    lane_rects: dict[str, dict] = {}

    if not horizontal:
        lane_quantum = G * 2
        for lane in lane_order:
            lane_breadth[lane] = (
                (lane_breadth[lane] + lane_quantum - 1) // lane_quantum
            ) * lane_quantum
        lane_center: dict[str, float] = {}
        cursor = margin
        for lane in lane_order:
            lane_center[lane] = cursor + lane_breadth[lane] / 2
            cursor += lane_breadth[lane] + swimlane_gap_px
        total_w = cursor - swimlane_gap_px + margin

        step_center: dict[int, float] = {}
        cursor   = margin
        last_gap = base_gap
        for i, s in enumerate(steps_ordered):
            step_center[s] = cursor + step_depth[s] / 2
            gap = step_gap(i) if i < len(steps_ordered) - 1 else base_gap
            cursor  += step_depth[s] + gap
            last_gap = gap
        total_h = cursor - last_gap + margin

        for (lane, step), cell in by_lane_step.items():
            cx = lane_center[lane]
            cy = step_center[step]
            widths  = [sizes[cn.name][0] for cn in cell]
            cell_w  = sum(widths) + cfg["h_gap"] * (len(cell) - 1)
            # Snap the leading edge to G so multi-node cells whose total
            # width is an odd-G multiple (e.g. two 2G-wide nodes + 3G gap
            # = 7G) don't shift the cell off-grid. Subsequent nodes inherit
            # G alignment because widths are 2G-multiples and h_gap snaps
            # to G in the inner update.
            x_cursor = _snap(cx - cell_w / 2, G)
            for cn, w in zip(cell, widths):
                _, h = sizes[cn.name]
                pinned = cn.position is not None
                x, y   = (cn.position[0], cn.position[1]) if pinned else (x_cursor, cy - h / 2)
                positions[cn.name] = {
                    "x": _snap(x, snap) if pinned else x,
                    "y": _snap(y, snap) if pinned else y,
                    "w": w, "h": h,
                }
                x_cursor += w + cfg["h_gap"]

        cursor = margin
        for lane in lane_order:
            if lane:
                lp = lane_pad.get(lane, container_pad_int)
                lane_rects[lane] = {
                    "x": cursor,
                    "y": margin - lp,
                    "w": lane_breadth[lane],
                    "h": total_h - 2 * margin + 2 * lp,
                }
            cursor += lane_breadth[lane] + swimlane_gap_px
    else:
        lane_quantum = G * 2
        for lane in lane_order:
            lane_breadth[lane] = (
                (lane_breadth[lane] + lane_quantum - 1) // lane_quantum
            ) * lane_quantum
        lane_center: dict[str, float] = {}
        cursor = margin
        for lane in lane_order:
            lane_center[lane] = cursor + lane_breadth[lane] / 2
            cursor += lane_breadth[lane] + swimlane_gap_px
        total_h = cursor - swimlane_gap_px + margin

        step_center: dict[int, float] = {}
        cursor   = margin
        last_gap = base_gap
        for i, s in enumerate(steps_ordered):
            widest = max((sizes[cn.name][0] for lane in lane_order
                          for cn in by_lane_step.get((lane, s), [])),
                         default=cfg["node_width"])
            step_center[s] = cursor + widest / 2
            gap = step_gap(i) if i < len(steps_ordered) - 1 else base_gap
            cursor  += widest + gap
            last_gap = gap
        total_w = cursor - last_gap + margin

        for (lane, step), cell in by_lane_step.items():
            cx = step_center[step]
            cy = lane_center[lane]
            heights  = [sizes[cn.name][1] for cn in cell]
            cell_h   = sum(heights) + cfg["v_gap"] * (len(cell) - 1)
            # Snap leading edge to G — same reasoning as the TB branch.
            y_cursor = _snap(cy - cell_h / 2, G)
            for cn, h in zip(cell, heights):
                w, _ = sizes[cn.name]
                pinned = cn.position is not None
                x, y   = (cn.position[0], cn.position[1]) if pinned else (cx - w / 2, y_cursor)
                positions[cn.name] = {
                    "x": _snap(x, snap) if pinned else x,
                    "y": _snap(y, snap) if pinned else y,
                    "w": w, "h": h,
                }
                y_cursor += h + cfg["v_gap"]

        cursor = margin
        for lane in lane_order:
            if lane:
                lp = lane_pad.get(lane, container_pad_int)
                lane_rects[lane] = {
                    "x": margin - lp,
                    "y": cursor,
                    "w": total_w - 2 * margin + 2 * lp,
                    "h": lane_breadth[lane],
                }
            cursor += lane_breadth[lane] + swimlane_gap_px

    # ── Grow lane rects to contain any pinned nodes outside auto bounds ──
    lane_children: dict[str, list[str]] = {lane: [] for lane in lane_rects}
    for n in nodes:
        lane = n.swimlane or ""
        if lane in lane_rects:
            lane_children[lane].append(n.name)
    for lane, rect in lane_rects.items():
        gp = lane_pad.get(lane, container_pad_int)
        children = [positions[nm] for nm in lane_children.get(lane, []) if nm in positions]
        if not children:
            continue
        cx0 = min(r["x"] for r in children) - gp
        cy0 = min(r["y"] for r in children) - gp
        cx1 = max(r["x"] + r["w"] for r in children) + gp
        cy1 = max(r["y"] + r["h"] for r in children) + gp
        x0, y0 = min(rect["x"], cx0), min(rect["y"], cy0)
        x1, y1 = max(rect["x"] + rect["w"], cx1), max(rect["y"] + rect["h"], cy1)
        lane_rects[lane] = {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}

    # ── Boxes and groups ─────────────────────────────────────────────────
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
        pad = _container_pad(b.label, cfg["box_padding"], G, max_pad=box_pad_cap)
        rect = _bbox(b.members, pad)
        if rect:
            box_rects[b.label] = rect

    group_rects: dict[str, dict] = {}
    for g in parsed.groups:
        rect = _bbox(g.members, cfg["group_padding"])
        if rect:
            group_rects[g.name] = rect

    # ── Notes ────────────────────────────────────────────────────────────
    # Notes are compact sticky-note pills. They are PARENTED to the target
    # node's swimlane: the pill sits inside the lane (forcing the lane to
    # grow if it was tighter than the note), one G to the right of the
    # target with one G of clearance above and below so the note reads as
    # a child annotation rather than a floater bumping into adjacent shapes.
    #
    # Width is narrower than the default node to signal supplementary
    # content; height grows to target_h + 2G to seat the clearance.
    def _bbox_overlaps(a: tuple[float, float, float, float],
                       b: tuple[float, float, float, float]) -> bool:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)

    other_node_bboxes = [
        (p["x"], p["y"], p["w"], p["h"]) for p in positions.values()
    ]
    note_target_lane: dict[int, str] = {}

    note_positions: list[dict] = []
    for note in parsed.notes:
        target = positions.get(note.target)
        if not target:
            continue
        nw = cfg["note_width"]
        # Taller than target by 1G top + 1G bottom — visible breathing
        # room within the lane.
        nh = max(cfg["note_height"], int(target["h"]) + 2 * G)
        nx = target["x"] + target["w"] + cfg["note_offset"]
        ny = target["y"] - G  # 1G clearance above target's top edge
        # Skip overlap with the target itself; only worry about other nodes.
        target_bbox = (target["x"], target["y"], target["w"], target["h"])
        candidates_to_clear = [b for b in other_node_bboxes if b != target_bbox]
        for _ in range(80):  # cap shift at 80*G to avoid runaway
            note_bbox = (nx, ny, nw, nh)
            if not any(_bbox_overlaps(note_bbox, b) for b in candidates_to_clear):
                break
            nx += G
        note_idx = len(note_positions)
        target_lane = next(
            (n.swimlane or "" for n in nodes if n.name == note.target),
            "",
        )
        note_target_lane[note_idx] = target_lane
        note_positions.append(
            {
                "text":   note.text,
                "target": note.target,
                "x": _snap(nx, snap),
                "y": _snap(ny, snap),
                "w": nw, "h": nh,
            }
        )

    # Lane grow-pass #2 — fold each note into its target's swimlane so the
    # lane wraps the note as a child container. The first grow-pass earlier
    # only saw the nodes; notes are placed after that, so we re-run for them.
    if note_positions:
        for idx, npos in enumerate(note_positions):
            lane = note_target_lane.get(idx, "")
            rect = lane_rects.get(lane)
            if not rect:
                continue
            gp = lane_pad.get(lane, container_pad_int)
            nx, ny = npos["x"], npos["y"]
            nx2, ny2 = nx + npos["w"], ny + npos["h"]
            x0 = min(rect["x"], nx - gp)
            y0 = min(rect["y"], ny - gp)
            x1 = max(rect["x"] + rect["w"], nx2 + gp)
            y1 = max(rect["y"] + rect["h"], ny2 + gp)
            lane_rects[lane] = {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}

    return {
        "positions":      positions,
        "lane_rects":     lane_rects,
        "box_rects":      box_rects,
        "group_rects":    group_rects,
        "note_positions": note_positions,
        "direction":      direction,
        "G":              G,
    }
