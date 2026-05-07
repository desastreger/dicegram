"""Edge route planner.

THE CONTRACT
============

`plan_edges()` is the single deterministic source of truth for connector
geometry. It runs after `compute_layout()` and produces one `EdgePlan`
per edge — a fully-resolved record containing:

  · attachment points (x, y) on each node face, including any offset
    slot needed for port exclusivity;
  · the polyline waypoints between them, never overlapping with another
    edge in the same corridor;
  · a label anchor on the visually-dominant segment;
  · the corner radius the renderer should soften bends with.

The frontend consumes this directly. It does NO routing decisions of
its own — no obstacle avoidance, no lane assignment, no port-collision
detection. Anything the frontend wanted to recompute belongs in here.

Why this exists
---------------

The previous pipeline scattered routing across three places: the backend
allocator (port choice), Canvas pre-pass (lane index), SmartEdge (elbow
bias). Each pass had partial information and slightly different inputs
(approximate vs. xyflow-real handle pixels), which produced "hanging in
air" lines, lane drift between passes, and stack-on-the-same-port bugs
nobody could fix without breaking another case. Centralising every
geometric decision here makes the whole pipeline reproducible: same
parsed input + layout → identical plans, every time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .parser import Edge, Node, Parsed


# ─── Tunables ─────────────────────────────────────────────────────────

# How far past a node face the line stops bending. Long enough that the
# elbow is clear of the shape's halo, short enough that adjacent shapes
# don't crowd each other.
STUB = 20

# Distance between two adjacent ports on the SAME face — applies to both
# offset slots (`r+1` is one step past the cardinal mid-face) and to the
# spread of multi-edge fan-outs from a single node.
PORT_PITCH = 24

# Distance between adjacent corridor lanes inside a step gap. Each
# parallel arrow that crosses the same gap and exits the same face gets
# its own lane spaced by this much from neighbours.
LANE_PITCH = 18

# Soft corner radius applied at every bend in the rendered polyline.
# Reads humane/handcrafted rather than mechanical CAD-line.
CORNER_RADIUS = 6


# ─── Plan data structures ─────────────────────────────────────────────

@dataclass
class Point:
    x: float
    y: float


@dataclass
class EdgePlan:
    edge_id: str
    source_id: str
    target_id: str
    kind: str
    label: str = ""
    attrs: dict[str, str] = field(default_factory=dict)
    # Where the line attaches on each shape — already includes any
    # port-offset adjustment, so the renderer doesn't need to compute it.
    source_x: float = 0.0
    source_y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    # Polyline corners between attachment points (NOT including the
    # attachment points themselves; the renderer prepends/appends them).
    waypoints: list[Point] = field(default_factory=list)
    # Where to position the connector label, plus the angle of the
    # segment the label rides (so the renderer can keep the rect
    # axis-aligned to that segment).
    label_x: float | None = None
    label_y: float | None = None
    label_axis: str = "horizontal"  # 'horizontal' or 'vertical'
    # Visual hints — these survive serialisation as plain strings/numbers.
    source_port: str = "b"  # cardinal letter, with `+N`/`-N` offset
    target_port: str = "t"
    corner_radius: float = CORNER_RADIUS


# ─── Internal types ──────────────────────────────────────────────────

@dataclass
class _Face:
    """One face (cardinal direction) of a node. Tracks which slots are
    already used by claimed edges. Slot 0 is the cardinal centre; ±1, ±2
    spill outward in alternating direction one PORT_PITCH at a time."""

    side: str  # 't' / 'b' / 'l' / 'r'
    used: set[int] = field(default_factory=set)


@dataclass
class _NodeBox:
    """Layout-resolved geometry for a single node."""

    name: str
    x: float
    y: float
    w: float
    h: float
    swimlane: str = ""
    step: int = 0
    # Distance between adjacent ports on the same face. Defaults to the
    # module constant for callers that don't yet thread G in; plan_edges
    # always overrides with G so ports stay grid-aligned.
    port_pitch: int = PORT_PITCH
    faces: dict[str, _Face] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.faces:
            self.faces = {s: _Face(side=s) for s in ("t", "b", "l", "r")}

    def cx(self) -> float:
        return self.x + self.w / 2

    def cy(self) -> float:
        return self.y + self.h / 2

    def claim(self, side: str, slot: int) -> None:
        self.faces[side].used.add(slot)

    def is_free(self, side: str, slot: int) -> bool:
        return slot not in self.faces[side].used

    def next_slot(self, side: str) -> int:
        """Smallest-magnitude free slot on this face. Tries 0, +1, -1,
        +2, -2, …"""
        if self.is_free(side, 0):
            return 0
        for n in range(1, 32):
            if self.is_free(side, n):
                return n
            if self.is_free(side, -n):
                return -n
        return 0  # caller's problem if every slot is taken

    def port_xy(self, side: str, slot: int) -> tuple[float, float]:
        """World coords of the named port on this node, including the
        slot offset along the face's parallel axis."""
        d = slot * self.port_pitch
        if side == "t":
            return self.cx() + d, self.y
        if side == "b":
            return self.cx() + d, self.y + self.h
        if side == "l":
            return self.x, self.cy() + d
        # 'r'
        return self.x + self.w, self.cy() + d

    def outward(self, side: str) -> tuple[float, float]:
        """Outward unit normal of the named face. Used by the renderer
        to know which way the stub points before the first corner."""
        return {
            "t": (0.0, -1.0),
            "b": (0.0, 1.0),
            "l": (-1.0, 0.0),
            "r": (1.0, 0.0),
        }[side]


# ─── Port-pair candidates ─────────────────────────────────────────────

_FORWARD = {
    "top-to-bottom": ("b", "t"),
    "left-to-right": ("r", "l"),
    "bottom-to-top": ("t", "b"),
    "right-to-left": ("l", "r"),
}

_PERP_PAIR = {
    "top-to-bottom": ("l", "r"),
    "left-to-right": ("t", "b"),
    "bottom-to-top": ("l", "r"),
    "right-to-left": ("t", "b"),
}


def _candidates_for(
    direction: str,
    rel_step: int,           # +1 forward adjacent, +N skip, 0 same step, -N back
    same_lane: bool,
    target_to_right: bool,   # in TB charts, target's lane index > source's
) -> list[tuple[str, str]]:
    """Ranked port-pair candidates for an edge. Higher rank = more
    natural visually. The allocator walks this list and picks the first
    pair where both ends still have a slot 0 free; if none does it
    falls through to offsets on the highest-rank pair."""
    fwd = _FORWARD.get(direction, ("b", "t"))
    fwd_src, fwd_dst = fwd
    rev_src, rev_dst = fwd_dst, fwd_src
    perp_a, perp_b = _PERP_PAIR.get(direction, ("l", "r"))

    if direction in ("top-to-bottom", "bottom-to-top"):
        # TB: cross-lane sits side-to-side, target_to_right means r→l
        face_pair = ("r", "l") if target_to_right else ("l", "r")
    else:
        # LR: cross-lane sits top-to-bottom
        face_pair = ("b", "t") if target_to_right else ("t", "b")

    same_side_a = (perp_a, perp_a)
    same_side_b = (perp_b, perp_b)

    if rel_step == 0:
        if same_lane:
            return [same_side_a, same_side_b]
        # Cross-lane same-step: face pair ONLY. Pass 2 will spill to offset
        # slots if the primary slot is taken. Same-side pairs are excluded —
        # they produce U-loops that wrap entirely around one node, which
        # looks like the connector doubled back through the shape.
        return [face_pair]

    if rel_step == 1:  # adjacent forward
        if same_lane:
            return [
                (fwd_src, fwd_dst),
                same_side_b,
                same_side_a,
                (perp_a, fwd_dst),
                (perp_b, fwd_dst),
                (fwd_src, perp_a),
                (fwd_src, perp_b),
            ]
        if target_to_right:
            # Target is to the right: exit source's leading face, enter target's
            # trailing face — the natural horizontal crossing.
            return [face_pair, (fwd_src, fwd_dst), same_side_a, same_side_b]
        else:
            # Target is to the LEFT: prefer routing through the step gap
            # (fwd ports b→t / r→l) so the connector passes below/beside
            # the current step's shapes rather than running horizontally
            # through them and colliding with same-step cross-lane connectors.
            return [(fwd_src, fwd_dst), face_pair, same_side_a, same_side_b]

    if rel_step > 1:  # skip-forward
        if same_lane:
            return [same_side_b, same_side_a, (fwd_src, fwd_dst)]
        if target_to_right:
            return [face_pair, same_side_a, same_side_b, (fwd_src, fwd_dst)]
        else:
            return [(fwd_src, fwd_dst), face_pair, same_side_a, same_side_b]

    # rel_step < 0  → back-edge
    if same_lane:
        return [same_side_a, same_side_b, (rev_src, rev_dst)]
    # Cross-lane back-edge: same-side U-loops FIRST. Face pairs produce
    # S-shapes (exit source in one direction, enter target from the same
    # direction), which is visually confusing for back-edges. The U-loop
    # wraps cleanly around the outside of the diagram — the conventional
    # flowchart look for "retry" and "loop-back" arcs.
    return [same_side_a, same_side_b, (rev_src, rev_dst)]


# ─── Reciprocal-pair collapse ─────────────────────────────────────────

def _collapse_reciprocals(
    edges: list[Edge], steps: dict[str, int]
) -> tuple[list[Edge], int]:
    """Merge `A -> B` + `B -> A` (same kind) into one bidirectional edge,
    but ONLY when both legs travel in the same step-direction (i.e. both
    forward or both backward). A forward edge paired with a backward edge
    represents a loop construct (e.g. a "retry" arc) — collapsing those
    into a single `<->` arrow destroys the loop-back routing and misleads
    readers into thinking the relationship is symmetric."""
    seen: dict[tuple[str, str, str], int] = {}
    drop: set[int] = set()
    for i, ed in enumerate(edges):
        if ed.source == ed.target:
            continue
        partner = (ed.target, ed.source, ed.kind)
        if partner in seen:
            j = seen[partner]
            keeper = edges[j]
            # If one leg is a forward edge (source.step ≤ target.step) and
            # the other is a back-edge, they form a loop — preserve both.
            ed_back = steps.get(ed.source, 0) > steps.get(ed.target, 0)
            keeper_back = steps.get(keeper.source, 0) > steps.get(keeper.target, 0)
            if ed_back != keeper_back:
                seen[(ed.source, ed.target, ed.kind)] = i
                continue
            keeper.attrs = dict(keeper.attrs or {})
            keeper.attrs["start"] = "arrow"
            keeper.attrs["end"] = keeper.attrs.get("end", "arrow")
            if ed.label and keeper.label and ed.label != keeper.label:
                keeper.label = f"{keeper.label} / {ed.label}"
            elif ed.label and not keeper.label:
                keeper.label = ed.label
            drop.add(i)
        else:
            seen[(ed.source, ed.target, ed.kind)] = i
    if not drop:
        return edges, 0
    return [e for i, e in enumerate(edges) if i not in drop], len(drop)


# ─── Allocation pass ──────────────────────────────────────────────────

def _allocate(
    edges: list[Edge],
    boxes: dict[str, _NodeBox],
    direction: str,
    lane_index: dict[str, int],
) -> list[tuple[Edge, str, int, str, int]]:
    """Walk every edge and claim a (side, slot) on both endpoints. Honours
    user-pinned anchors (anything that doesn't match the chart's forward
    default). Returns a list of (edge, src_side, src_slot, dst_side,
    dst_slot) parallel to `edges`."""
    fwd_src, fwd_dst = _FORWARD.get(direction, ("b", "t"))
    out: list[tuple[Edge, str, int, str, int]] = []

    # Order: edges most likely to land on the chart's natural ports go
    # first. That preserves the clean look of straightforward chains.
    def priority(item: tuple[int, Edge]) -> tuple[int, int, int]:
        i, ed = item
        if ed.source not in boxes or ed.target not in boxes:
            return (5, 0, i)
        ss = boxes[ed.source].step
        ts = boxes[ed.target].step
        rel = ts - ss
        if rel == 1:
            return (0, 0, i)
        if rel > 1:
            return (1, rel, i)
        if rel == 0:
            return (2, 0, i)
        if rel < 0:
            return (3, -rel, i)
        return (4, 0, i)

    indexed = sorted(enumerate(edges), key=priority)

    for _, ed in indexed:
        if ed.source not in boxes or ed.target not in boxes:
            continue
        sb = boxes[ed.source]
        tb = boxes[ed.target]
        rel = tb.step - sb.step
        same_lane = sb.swimlane == tb.swimlane
        target_to_right = lane_index.get(tb.swimlane, 0) > lane_index.get(sb.swimlane, 0)

        # Decode any user-supplied port (offset suffix included).
        def decode(p: str | None) -> tuple[str, int] | None:
            if not p:
                return None
            v = p.lower().strip()
            v = {"top": "t", "bottom": "b", "left": "l", "right": "r"}.get(v, v)
            if v in ("t", "b", "l", "r"):
                return (v, 0)
            for letter in ("t", "b", "l", "r"):
                if v.startswith(letter) and len(v) > 1:
                    rest = v[1:]
                    try:
                        return (letter, int(rest))
                    except ValueError:
                        continue
            return None

        ds = decode(ed.source_port)
        dt = decode(ed.target_port)
        user_pinned = (ds and ds[0] != fwd_src) or (dt and dt[0] != fwd_dst)

        if user_pinned:
            s_side, s_off = ds or (fwd_src, 0)
            t_side, t_off = dt or (fwd_dst, 0)
            # Spill to next slot if cardinal is taken — they pinned the
            # SIDE, not the exact slot.
            if s_off == 0 and not sb.is_free(s_side, 0):
                s_off = sb.next_slot(s_side)
            if t_off == 0 and not tb.is_free(t_side, 0):
                t_off = tb.next_slot(t_side)
            sb.claim(s_side, s_off)
            tb.claim(t_side, t_off)
            out.append((ed, s_side, s_off, t_side, t_off))
            continue

        candidates = _candidates_for(direction, rel, same_lane, target_to_right)

        chosen: tuple[str, int, str, int] | None = None
        # Pass 1: both sides free at slot 0.
        for s_side, t_side in candidates:
            if sb.is_free(s_side, 0) and tb.is_free(t_side, 0):
                chosen = (s_side, 0, t_side, 0)
                break
        # Pass 2: spill to offsets, preferring the FIRST candidate so
        # related edges cluster on the same face.
        if chosen is None:
            for s_side, t_side in candidates:
                s_off = 0 if sb.is_free(s_side, 0) else sb.next_slot(s_side)
                t_off = 0 if tb.is_free(t_side, 0) else tb.next_slot(t_side)
                chosen = (s_side, s_off, t_side, t_off)
                break
        if chosen is None:
            # Edge case (no candidates) — should never trigger.
            chosen = (fwd_src, sb.next_slot(fwd_src), fwd_dst, tb.next_slot(fwd_dst))

        s_side, s_off, t_side, t_off = chosen
        sb.claim(s_side, s_off)
        tb.claim(t_side, t_off)
        out.append((ed, s_side, s_off, t_side, t_off))

    # Re-sort back into original-index order so plans align with the
    # caller's edge list.
    by_id = {id(e): i for i, e in enumerate(edges)}
    out.sort(key=lambda t: by_id[id(t[0])])
    return out


# ─── Lane assignment ──────────────────────────────────────────────────

def _assign_lanes(
    allocations: list[tuple[Edge, str, int, str, int]],
    boxes: dict[str, _NodeBox],
    direction: str,
) -> dict[int, int]:
    """For every edge, decide which lane (signed integer) it occupies in
    the corridor between its source and target. Lanes are unique per
    (corridor, source-port-side) so parallel arrows from the same face
    don't share an elbow. Returns {edge_index: lane}.

    A "corridor" is identified by the pair of step indices the edge
    crosses. Lane 0 is the centre, ±1, ±2 fan symmetrically — gives a
    visually balanced spread regardless of edge count."""
    # Group edges by (corridor_key, source_port_side).
    groups: dict[tuple[str, str], list[int]] = {}
    for i, (ed, s_side, _, _, _) in enumerate(allocations):
        if ed.source not in boxes or ed.target not in boxes:
            continue
        ss = boxes[ed.source].step
        ts = boxes[ed.target].step
        if ss == ts:
            continue
        lo, hi = min(ss, ts), max(ss, ts)
        key = (f"{lo}|{hi}", s_side)
        groups.setdefault(key, []).append(i)

    lanes: dict[int, int] = {}
    for members in groups.values():
        n = len(members)
        if n == 1:
            lanes[members[0]] = 0
            continue
        # Each unit of offset_steps produces a drift of (lane_pitch / 2).
        # For drift to land on the G-grid (lane_pitch=G), every offset
        # MUST be even. Odd n: symmetric around 0 (n=3 → -2, 0, +2).
        # Even n: slightly asymmetric to keep all offsets even (n=2 →
        # -2, 0; n=4 → -4, -2, 0, +2).
        for k, idx in enumerate(members):
            if n % 2 == 1:
                offset_steps = 2 * k - (n - 1)
            else:
                offset_steps = 2 * k - n
            lanes[idx] = offset_steps
    return lanes


# ─── Waypoint generation ──────────────────────────────────────────────

def _line_crosses_box(
    axis_value: float,
    axis: str,
    range_min: float,
    range_max: float,
    box: tuple[float, float, float, float],
    pad: float = 0.0,
) -> bool:
    """True when an axis-aligned line intersects the interior of `box`.

    `axis='x'` is a vertical line at x=axis_value spanning y ∈ [range_min,
    range_max]; `axis='y'` is a horizontal line. `pad` extends the box
    outward to keep the connector clear of the shape's halo (default 0
    for tight fits)."""
    bx, by, bw, bh = box
    if axis == "x":
        if not (bx - pad < axis_value < bx + bw + pad):
            return False
        return not (range_max <= by - pad or range_min >= by + bh + pad)
    if not (by - pad < axis_value < by + bh + pad):
        return False
    return not (range_max <= bx - pad or range_min >= bx + bw + pad)


def _find_clear_axis(
    natural: float,
    range_min: float,
    range_max: float,
    axis: str,
    obstacles: list[tuple[float, float, float, float]],
    grid: int,
    pad: float = 0.0,
    direction_bias: int = 0,
) -> float:
    """Return the closest grid-aligned position to `natural` such that an
    axis-aligned line on `axis` between `range_min` and `range_max` does
    not cross any obstacle. Falls back to `natural` if no clear slot is
    found within ~60G of scanning.

    `direction_bias`: 0 = symmetric search (closest cleared position on
    either side); +1 = positive direction only (used when the U-loop
    elbow must move further from the lane); -1 = negative only."""
    if grid <= 0:
        return natural
    if not any(_line_crosses_box(natural, axis, range_min, range_max, b, pad) for b in obstacles):
        return natural
    for step in range(1, 80):
        if direction_bias >= 0:
            candidate = natural + step * grid
            if not any(_line_crosses_box(candidate, axis, range_min, range_max, b, pad) for b in obstacles):
                return candidate
        if direction_bias <= 0:
            candidate = natural - step * grid
            if not any(_line_crosses_box(candidate, axis, range_min, range_max, b, pad) for b in obstacles):
                return candidate
    return natural


def _dogleg_if_crossing(
    pts: list[Point],
    seg_idx: int,
    obstacles: list[tuple[float, float, float, float]],
    grid: int,
    pad: float,
) -> list[Point]:
    """If `pts[seg_idx]`→`pts[seg_idx+1]` is an axis-aligned segment that
    crosses any obstacle, replace it with a 3-segment dogleg routed via
    a clear y (for horizontal segments) or x (for vertical) close to
    the original. Returns the (possibly extended) point list."""
    if grid <= 0 or seg_idx < 0 or seg_idx + 1 >= len(pts):
        return pts
    p1, p2 = pts[seg_idx], pts[seg_idx + 1]
    is_horizontal = abs(p1.y - p2.y) < 0.5
    is_vertical = abs(p1.x - p2.x) < 0.5
    if is_horizontal == is_vertical:
        return pts  # degenerate or diagonal — skip
    if is_horizontal:
        x_min, x_max = (p1.x, p2.x) if p1.x <= p2.x else (p2.x, p1.x)
        if x_max - x_min < grid:
            return pts
        if not any(_line_crosses_box(p1.y, "y", x_min, x_max, b, pad) for b in obstacles):
            return pts
        clear_y = _find_clear_axis(p1.y, x_min, x_max, "y", obstacles, grid, pad)
        if abs(clear_y - p1.y) < grid / 2:
            return pts
        return (
            pts[: seg_idx + 1]
            + [Point(p1.x, clear_y), Point(p2.x, clear_y)]
            + pts[seg_idx + 1 :]
        )
    # vertical
    y_min, y_max = (p1.y, p2.y) if p1.y <= p2.y else (p2.y, p1.y)
    if y_max - y_min < grid:
        return pts
    if not any(_line_crosses_box(p1.x, "x", y_min, y_max, b, pad) for b in obstacles):
        return pts
    clear_x = _find_clear_axis(p1.x, y_min, y_max, "x", obstacles, grid, pad)
    if abs(clear_x - p1.x) < grid / 2:
        return pts
    return (
        pts[: seg_idx + 1]
        + [Point(clear_x, p1.y), Point(clear_x, p2.y)]
        + pts[seg_idx + 1 :]
    )


def _make_waypoints(
    sb: _NodeBox,
    s_side: str,
    s_off: int,
    tb: _NodeBox,
    t_side: str,
    t_off: int,
    lane: int,
    stub: int = STUB,
    lane_pitch: int = LANE_PITCH,
    grid: int = 0,
    obstacles: list[tuple[float, float, float, float]] | None = None,
) -> tuple[list[Point], tuple[float, float], tuple[float, float]]:
    """Produce the polyline corners between the source and target
    attachment points. Handles three shapes:

      · straight   — collinear stubs, no bend
      · L          — one bend; perpendicular-port pair
      · U          — two bends; same-side port pair (loopback)
      · Z (S)      — two bends; opposite-side port pair across a corridor

    The lane offset (in half-grid units) shifts the elbow off the
    midpoint so parallel routes don't share a segment.

    `grid` snaps the Z-shape elbow position so it lands on the visual
    grid even when the two stubs are an odd-G apart (their midpoint
    is otherwise half-G off). 0 disables snapping.

    `obstacles` is a list of node bboxes (excluding source/target) to
    avoid: when the natural Z-shape elbow would land in a populated
    column or row, the elbow is shifted in G-steps until it clears."""
    sx, sy = sb.port_xy(s_side, s_off)
    tx, ty = tb.port_xy(t_side, t_off)
    sn = sb.outward(s_side)
    tn = tb.outward(t_side)
    obs = obstacles or []
    obstacle_pad = grid // 2 if grid > 0 else 0

    def _snap_to_grid(v: float) -> float:
        if grid <= 0:
            return v
        return round(v / grid) * grid

    # Stubs — every route exits and enters perpendicular to its face.
    sStub = (sx + sn[0] * stub, sy + sn[1] * stub)
    tStub = (tx + tn[0] * stub, ty + tn[1] * stub)

    pts: list[Point] = [Point(sStub[0], sStub[1])]

    # Lane drift: half a lane_pitch per integer step (half-grid units
    # come from `_assign_lanes`).
    drift = lane * (lane_pitch / 2)

    # Same-side ports → U-loop. Both stubs already point in the same
    # outward direction; align them along the dominant axis to a shared
    # extreme so the route between is a single perpendicular segment.
    # The elbow extends beyond every stub plus any obstacle nodes that
    # sit between the stubs along the lane axis (e.g. a U-loop on the
    # right side of a swimlane must clear all nodes to the right of the
    # widest stub, not just the stub itself).
    if s_side == t_side:
        if s_side in ("l", "r"):
            range_y_min = min(sStub[1], tStub[1])
            range_y_max = max(sStub[1], tStub[1])
        else:
            range_x_min = min(sStub[0], tStub[0])
            range_x_max = max(sStub[0], tStub[0])
        if s_side == "l":
            base = min(sStub[0], tStub[0])
            base = _find_clear_axis(base, range_y_min, range_y_max, "x",
                                    obs, grid, obstacle_pad, direction_bias=-1)
            x = base - max(0, drift)
            pts.append(Point(x, sStub[1]))
            pts.append(Point(x, tStub[1]))
        elif s_side == "r":
            base = max(sStub[0], tStub[0])
            base = _find_clear_axis(base, range_y_min, range_y_max, "x",
                                    obs, grid, obstacle_pad, direction_bias=1)
            x = base + max(0, drift)
            pts.append(Point(x, sStub[1]))
            pts.append(Point(x, tStub[1]))
        elif s_side == "t":
            base = min(sStub[1], tStub[1])
            base = _find_clear_axis(base, range_x_min, range_x_max, "y",
                                    obs, grid, obstacle_pad, direction_bias=-1)
            y = base - max(0, drift)
            pts.append(Point(sStub[0], y))
            pts.append(Point(tStub[0], y))
        else:  # 'b'
            base = max(sStub[1], tStub[1])
            base = _find_clear_axis(base, range_x_min, range_x_max, "y",
                                    obs, grid, obstacle_pad, direction_bias=1)
            y = base + max(0, drift)
            pts.append(Point(sStub[0], y))
            pts.append(Point(tStub[0], y))
        pts.append(Point(tStub[0], tStub[1]))
        return pts, sn, tn

    # Opposite-axis ports (b↔t or l↔r) → Z-shape.
    s_horizontal = s_side in ("l", "r")
    t_horizontal = t_side in ("l", "r")
    if s_horizontal == t_horizontal:
        # Both horizontal (l/r ↔ l/r) or both vertical (t/b ↔ t/b);
        # midpoint between stubs as the elbow corridor. Snap the
        # midpoint to the grid BEFORE adding drift so all parallel
        # lanes (drift = int × G) stay grid-aligned.
        if s_horizontal:
            base_mx = _snap_to_grid((sStub[0] + tStub[0]) / 2)
            run_y_min = min(sStub[1], tStub[1])
            run_y_max = max(sStub[1], tStub[1])
            base_mx = _find_clear_axis(
                base_mx, run_y_min, run_y_max, "x", obs, grid, obstacle_pad
            )
            mx = base_mx + drift
            pts.append(Point(mx, sStub[1]))
            pts.append(Point(mx, tStub[1]))
        else:
            base_my = _snap_to_grid((sStub[1] + tStub[1]) / 2)
            run_x_min = min(sStub[0], tStub[0])
            run_x_max = max(sStub[0], tStub[0])
            base_my = _find_clear_axis(
                base_my, run_x_min, run_x_max, "y", obs, grid, obstacle_pad
            )
            my = base_my + drift
            pts.append(Point(sStub[0], my))
            pts.append(Point(tStub[0], my))
        pts.append(Point(tStub[0], tStub[1]))
        return pts, sn, tn

    # Perpendicular axes (e.g., source@b → target@l) → L-shape, single
    # bend at the corner sStub.x / tStub.y combination that keeps both
    # the source-stub direction and the target-stub direction true.
    if s_horizontal:
        # source exits horizontally; target enters vertically →
        # corner at (target_x_stub, source_y_stub)
        pts.append(Point(tStub[0], sStub[1]))
    else:
        pts.append(Point(sStub[0], tStub[1]))
    pts.append(Point(tStub[0], tStub[1]))
    return pts, sn, tn


def _repair_path(
    pts: list[Point],
    obstacles: list[tuple[float, float, float, float]],
    grid: int,
    pad: float,
) -> list[Point]:
    """Walk every segment in `pts`; if any axis-aligned segment crosses
    an obstacle, dogleg it to a clear y/x. Iterate until no segment
    crosses (cap at 3 passes — the segments multiply with each repair
    so unbounded iteration could blow up on adversarial inputs)."""
    if not obstacles or grid <= 0:
        return pts
    for _ in range(3):
        repaired = False
        i = len(pts) - 2
        while i >= 0:
            new_pts = _dogleg_if_crossing(pts, i, obstacles, grid, pad)
            if new_pts is not pts and len(new_pts) != len(pts):
                pts = new_pts
                repaired = True
            i -= 1
        if not repaired:
            break
    return pts


def _simplify_path(pts: list[Point]) -> list[Point]:
    """Remove duplicate and collinear points so `_label_anchor` sees
    only the true geometric segments, not stub intermediates."""
    if len(pts) < 2:
        return pts
    dedup: list[Point] = [pts[0]]
    for p in pts[1:]:
        last = dedup[-1]
        if abs(p.x - last.x) > 0.5 or abs(p.y - last.y) > 0.5:
            dedup.append(p)
    if len(dedup) < 3:
        return dedup
    out: list[Point] = [dedup[0]]
    for i in range(1, len(dedup) - 1):
        a = out[-1]
        b = dedup[i]
        c = dedup[i + 1]
        vert = abs(a.x - b.x) < 0.5 and abs(b.x - c.x) < 0.5
        horiz = abs(a.y - b.y) < 0.5 and abs(b.y - c.y) < 0.5
        if not (vert or horiz):
            out.append(b)
    out.append(dedup[-1])
    return out


_LABEL_GRID = 20  # snap label position to this grid so it lands on a crisp pixel row


def _label_anchor(
    waypoints: list[Point], label_grid: int = _LABEL_GRID
) -> tuple[Point, str]:
    """Find the LONGEST axis-aligned segment in the polyline and return
    its grid-snapped midpoint. Simplifies collinear/duplicate points first
    so stub intermediates don't win over the true long segment."""
    simplified = _simplify_path(waypoints)
    pts = simplified if len(simplified) >= 2 else waypoints
    best_idx = 0
    best_len = -1.0
    for i in range(len(pts) - 1):
        a = pts[i]
        b = pts[i + 1]
        length = abs(b.x - a.x) + abs(b.y - a.y)
        if length > best_len:
            best_len = length
            best_idx = i
    a = pts[best_idx]
    b = pts[best_idx + 1]
    raw_x = (a.x + b.x) / 2
    raw_y = (a.y + b.y) / 2
    g = max(1, label_grid)
    midpoint = Point(round(raw_x / g) * g, round(raw_y / g) * g)
    axis = "horizontal" if abs(a.y - b.y) < 0.5 else "vertical"
    return midpoint, axis


# ─── Public entry point ───────────────────────────────────────────────

def plan_edges(
    parsed: Parsed,
    layout: dict,
) -> tuple[list[EdgePlan], int]:
    """Build an `EdgePlan` for every edge in `parsed`. Returns
    `(plans, num_collapsed)` so the caller can surface a notice when
    reciprocal arrow pairs were merged."""
    # Resolve the visual grid unit from layout. Every routing tunable
    # below is set to a multiple of G so ports, stubs, and lane drifts
    # all land on the grid — see plan: tidy-crunching-sparrow.md.
    G = int(layout.get("G", 20))
    stub       = G
    port_pitch = G
    lane_pitch = G
    corner_r   = max(4, G // 3)
    label_grid = G

    # Step 1: collapse `A -> B` + `B -> A` into one bidirectional edge,
    # but only when both legs travel in the same step direction.
    steps = {n.name: int(n.step) for n in parsed.nodes}
    edges, num_collapsed = _collapse_reciprocals(list(parsed.edges), steps)
    parsed.edges = edges

    # Step 2: build per-node geometry from the layout.
    positions = layout.get("positions", {})
    boxes: dict[str, _NodeBox] = {}
    for n in parsed.nodes:
        p = positions.get(n.name)
        if not p:
            continue
        boxes[n.name] = _NodeBox(
            name=n.name,
            x=float(p["x"]),
            y=float(p["y"]),
            w=float(p["w"]),
            h=float(p["h"]),
            swimlane=n.swimlane or "",
            step=int(n.step),
            port_pitch=port_pitch,
        )

    lane_index = {sl.name: i for i, sl in enumerate(parsed.swimlanes)}
    if "" not in lane_index:
        # Default lane appears AT THE END so a no-swimlane chart still
        # has a stable lane index.
        lane_index[""] = len(lane_index)

    # Step 3: allocate ports.
    allocations = _allocate(edges, boxes, parsed.direction, lane_index)

    # Step 4: assign lanes for parallel-corridor spread.
    lanes = _assign_lanes(allocations, boxes, parsed.direction)

    # Pre-compute every node's bbox so each edge can pull a list of
    # obstacles minus its own endpoints — used to keep the Z-shape
    # elbow out of populated columns/rows.
    node_bboxes = {
        name: (b.x, b.y, b.w, b.h) for name, b in boxes.items()
    }

    # Step 5: build the plans.
    plans: list[EdgePlan] = []
    for i, (ed, s_side, s_off, t_side, t_off) in enumerate(allocations):
        if ed.source not in boxes or ed.target not in boxes:
            continue
        sb = boxes[ed.source]
        tb = boxes[ed.target]
        sx, sy = sb.port_xy(s_side, s_off)
        tx, ty = tb.port_xy(t_side, t_off)
        lane = lanes.get(i, 0)
        obstacles = [
            bb for name, bb in node_bboxes.items()
            if name != ed.source and name != ed.target
        ]
        interior, _, _ = _make_waypoints(
            sb, s_side, s_off, tb, t_side, t_off, lane,
            stub=stub, lane_pitch=lane_pitch, grid=G,
            obstacles=obstacles,
        )
        # Full polyline: attachment points + interior corners. The renderer
        # receives the complete sequence and draws it verbatim — it does not
        # prepend/append endpoints itself.
        full = [Point(sx, sy)] + interior + [Point(tx, ty)]
        # Final pass — dogleg any segment that still crosses an obstacle.
        # The base shape generators avoid populated columns/rows for the
        # main elbow, but terminal segments at sStub.y / tStub.y can still
        # traverse a node that shares the source's or target's row.
        full = _repair_path(full, obstacles, G, max(2, G // 4))
        label_xy, label_axis = _label_anchor(full, label_grid=label_grid)
        plans.append(
            EdgePlan(
                edge_id=f"e{i}",
                source_id=ed.source,
                target_id=ed.target,
                kind=ed.kind,
                label=ed.label,
                attrs=dict(ed.attrs or {}),
                source_x=sx,
                source_y=sy,
                target_x=tx,
                target_y=ty,
                waypoints=full,
                label_x=label_xy.x,
                label_y=label_xy.y,
                label_axis=label_axis,
                source_port=_encode(s_side, s_off),
                target_port=_encode(t_side, t_off),
                corner_radius=corner_r,
            )
        )
    return plans, num_collapsed


def _encode(side: str, slot: int) -> str:
    if slot == 0:
        return side
    sign = "+" if slot > 0 else ""
    return f"{side}{sign}{slot}"
