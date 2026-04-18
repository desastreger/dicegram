from __future__ import annotations

import re
from dataclasses import dataclass, field

from .parser import SHAPE_KEYWORDS

POSITION_RE = re.compile(r"@\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)")
NODE_LINE_RE = re.compile(r'^(\s*)\[(\w+)\]\s+(\w+)\s+"((?:[^"\\]|\\.)*)"(.*)$')
EDGE_LINE_RE = re.compile(r"^(\s*)(\w+)\s*(==>|-->|-\.-|---|->)\s*(\w+)(.*)$")
SNAP_SETTING_RE = re.compile(r"^\s*setting\s+snap_grid\s+(\d+)", re.MULTILINE)
FREE_PLACEMENT_RE = re.compile(
    r"^\s*setting\s+free_placement\s+(on|off|true|false|1|0)", re.MULTILINE
)


@dataclass
class Notice:
    severity: str
    message: str
    line: int | None = None


@dataclass
class NormalizeResult:
    source: str
    notices: list[Notice] = field(default_factory=list)
    changed: bool = False


def _snap(value: float, grid: int) -> int:
    if grid <= 0:
        return int(value)
    return int(round(value / grid) * grid)


def _free_placement(source: str) -> bool:
    m = FREE_PLACEMENT_RE.search(source)
    if not m:
        return False
    return m.group(1).lower() in ("on", "true", "1")


def _snap_grid(source: str) -> int:
    m = SNAP_SETTING_RE.search(source)
    if not m:
        return 10
    try:
        g = int(m.group(1))
        return g if g > 0 else 10
    except ValueError:
        return 10


def normalize(source: str) -> NormalizeResult:
    """Idempotently rewrite a DSL source to enforce structural invariants.

    R1: strip trailing whitespace on each line, drop a leading BOM.
    R2: round every @(x,y) position to the snap grid.
    R3: remove edges whose source or target is not a declared node.
    R4: rename duplicate node definitions (second occurrence gets _2 suffix,
        and all edges/notes referencing it are rewritten — but only if the
        duplicate is AFTER the original; the first wins).
    R5: when two pinned siblings land on the same grid cell, shift the
        second by one grid step along the minor axis.
    R6: strip @(x,y) pins from nodes inside a swimlane. The lane layout
        always centers children on the lane axis; letting pins fight that
        produces dissonant, ragged views. Root-level pins stay.
    R7: force the canonical shape for each semantic type. Visio convention:
        decision→diamond, start/end→circle, datastore→cylinder,
        input/output→parallelogram, approval→hexagon, manual→rounded.
        If the author wrote an inconsistent shape the compiler rewrites it
        so visuals always match meaning.
    """
    notices: list[Notice] = []
    if source.startswith("\ufeff"):
        source = source.lstrip("\ufeff")

    grid = _snap_grid(source)
    free_placement = _free_placement(source)
    lines = source.split("\n")
    changed = False

    # R1: trim trailing whitespace (preserve line count / empty lines).
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped != line:
            lines[i] = stripped
            changed = True

    # R2: snap every position literal.
    def snap_positions(line: str) -> str:
        nonlocal changed

        def sub(m: re.Match[str]) -> str:
            nonlocal changed
            x = float(m.group(1))
            y = float(m.group(2))
            nx = _snap(x, grid)
            ny = _snap(y, grid)
            if nx != x or ny != y:
                changed = True
            return f"@({nx}, {ny})"

        return POSITION_RE.sub(sub, line)

    for i, line in enumerate(lines):
        snapped = snap_positions(line)
        if snapped != line:
            lines[i] = snapped

    # R4: collect declared node names, rename later duplicates.
    declared: dict[str, int] = {}
    rename: dict[str, str] = {}
    for i, line in enumerate(lines):
        m = NODE_LINE_RE.match(line)
        if not m:
            continue
        _, shape, name, label, rest = m.groups()
        if shape not in SHAPE_KEYWORDS:
            continue
        if name in declared:
            suffix = 2
            while f"{name}_{suffix}" in declared or f"{name}_{suffix}" in rename.values():
                suffix += 1
            new_name = f"{name}_{suffix}"
            rename[f"{i}:{name}"] = new_name
            indent = m.group(1)
            lines[i] = f'{indent}[{shape}] {new_name} "{label}"{rest}'
            declared[new_name] = i
            notices.append(
                Notice("fix", f"duplicate '{name}' renamed to '{new_name}'", i + 1)
            )
            changed = True
        else:
            declared[name] = i

    # R3: drop edges referencing unknown nodes (and notes).
    pruned_lines: list[str] = []
    for i, line in enumerate(lines):
        em = EDGE_LINE_RE.match(line)
        if em:
            _, src, _, dst, _ = em.groups()
            if src not in declared or dst not in declared:
                missing = src if src not in declared else dst
                notices.append(
                    Notice("fix", f"dropped edge referencing unknown '{missing}'", i + 1)
                )
                changed = True
                continue
        note_m = re.match(r'^\s*note\s+"[^"]*"\s+\[(\w+)\]\s*$', line)
        if note_m:
            target = note_m.group(1)
            if target not in declared:
                notices.append(
                    Notice("fix", f"dropped note referencing unknown '{target}'", i + 1)
                )
                changed = True
                continue
        pruned_lines.append(line)
    if len(pruned_lines) != len(lines):
        lines = pruned_lines

    # R5: resolve identical pinned positions.
    #     We don't have full layout info here, but co-located *explicit* pins
    #     are unambiguous conflicts. Shift the later occurrence by one grid
    #     step along y (or x if the direction is horizontal).
    horizontal = _is_horizontal(source)
    pin_cells: dict[tuple[int, int], int] = {}  # (x, y) -> line index
    for i, line in enumerate(lines):
        if not NODE_LINE_RE.match(line):
            continue
        m = POSITION_RE.search(line)
        if not m:
            continue
        x = int(float(m.group(1)))
        y = int(float(m.group(2)))
        cell = (x, y)
        if cell in pin_cells:
            step = max(grid, 10)
            while cell in pin_cells:
                if horizontal:
                    cell = (cell[0] + step, cell[1])
                else:
                    cell = (cell[0], cell[1] + step)
            new_line = POSITION_RE.sub(f"@({cell[0]}, {cell[1]})", line, count=1)
            lines[i] = new_line
            pin_cells[cell] = i
            notices.append(
                Notice(
                    "fix",
                    f"shifted co-located pin to @({cell[0]}, {cell[1]})",
                    i + 1,
                )
            )
            changed = True
        else:
            pin_cells[cell] = i

    # R7: force canonical shape per type attribute. Visio convention — a
    #     reader seeing a diamond expects a decision; a circle expects a
    #     terminator. Keep author intent visible regardless of [shape].
    #     `setting free_placement on` opts out (for users who want full
    #     manual control over shapes and pins).
    if free_placement:
        new_source = "\n".join(lines)
        return NormalizeResult(source=new_source, notices=notices, changed=changed)

    TYPE_TO_SHAPE = {
        "start": "circle",
        "end": "circle",
        "decision": "diamond",
        "datastore": "cylinder",
        "input": "parallelogram",
        "output": "parallelogram",
        "approval": "hexagon",
        "manual": "rounded",
    }
    TYPE_ATTR_RE = re.compile(r"(?:^|\s)type:([A-Za-z_]+)")
    for i, line in enumerate(lines):
        m = NODE_LINE_RE.match(line)
        if not m:
            continue
        indent, shape, name, label, rest = m.groups()
        if shape not in SHAPE_KEYWORDS:
            continue
        tm = TYPE_ATTR_RE.search(rest)
        if not tm:
            continue
        semantic = tm.group(1).lower()
        required = TYPE_TO_SHAPE.get(semantic)
        if not required or shape == required:
            continue
        lines[i] = f'{indent}[{required}] {name} "{label}"{rest}'
        notices.append(
            Notice(
                "fix",
                f"'{name}' shape {shape} → {required} to match type:{semantic}",
                i + 1,
            )
        )
        changed = True

    # R6: pinned nodes inside a swimlane lose their pins so the lane
    #     auto-layout can place them on the lane axis.
    depth = 0
    kinds: list[str] = []  # stack of enclosing block kinds: "swimlane" or "box"
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("swimlane ") and stripped.endswith("{"):
            kinds.append("swimlane")
            depth += 1
            continue
        if stripped.startswith("box ") and stripped.endswith("{"):
            kinds.append("box")
            depth += 1
            continue
        if stripped == "}" and depth > 0:
            kinds.pop()
            depth -= 1
            continue
        # Inside any swimlane (directly or via a nested box)?
        in_lane = any(k == "swimlane" for k in kinds)
        if not in_lane:
            continue
        nm = NODE_LINE_RE.match(line)
        if not nm:
            continue
        if not POSITION_RE.search(line):
            continue
        cleaned = POSITION_RE.sub("", line)
        cleaned = re.sub(r"\s+$", "", cleaned)
        if cleaned != line:
            lines[i] = cleaned
            notices.append(
                Notice(
                    "fix",
                    f"dropped pin from '{nm.group(3)}' — swimlane auto-centers children",
                    i + 1,
                )
            )
            changed = True

    new_source = "\n".join(lines)
    return NormalizeResult(source=new_source, notices=notices, changed=changed)


def _is_horizontal(source: str) -> bool:
    m = re.search(r"^\s*direction\s+(\S+)", source, re.MULTILINE)
    if not m:
        return False
    return m.group(1) in ("left-to-right", "right-to-left")
