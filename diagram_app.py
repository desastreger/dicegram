"""
Diagram Editor — PySide6 Desktop Application
Step-based code-to-diagram tool with bidirectional editing, rich attributes,
QGraphicsScene rendering, and PDF/SVG/PNG export.

Requires: Python 3.10+, PySide6>=6.6, fpdf2>=2.7
Run via: python run.py
"""

import sys
import re
import math
import json
import os
from collections import defaultdict, deque
from pathlib import Path
from fpdf import FPDF

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QDockWidget,
    QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QPlainTextEdit, QGraphicsScene, QGraphicsView,
    QGraphicsItem, QGraphicsRectItem, QGraphicsLineItem,
    QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsPolygonItem,
    QGraphicsDropShadowEffect, QGraphicsPathItem,
    QMenuBar, QMenu, QToolBar, QStatusBar,
    QLabel, QSlider, QComboBox, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QDialog, QDialogButtonBox,
    QTextEdit, QScrollArea, QCompleter,
    QToolButton,
)
from PySide6.QtCore import (
    Qt, QTimer, QSettings, QRectF, QPointF, QSizeF, QLineF,
    Signal, Slot, QStringListModel,
)
from PySide6.QtGui import (
    QFont, QFontDatabase, QColor, QPen, QBrush, QPainter,
    QPainterPath, QPolygonF, QAction, QTextCharFormat,
    QSyntaxHighlighter, QTextCursor, QKeySequence,
    QImage, QPixmap, QTextDocument,
)
from PySide6.QtSvg import QSvgGenerator


# ═══════════════════════════════════════════════
#  Utility
# ═══════════════════════════════════════════════

def hex_to_rgb(h):
    try:
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return (128, 128, 128)


def hex_to_qcolor(h):
    try:
        r, g, b = hex_to_rgb(h)
        return QColor(r, g, b)
    except Exception:
        return QColor(128, 128, 128)


# ═══════════════════════════════════════════════
#  Color Schemes
# ═══════════════════════════════════════════════

COLOR_SCHEMES = {
    "Default": {
        "node_fill": "#ffffff", "node_stroke": "#333333",
        "node_text": "#222222", "edge_stroke": "#555555",
        "edge_label": "#444444", "swimlane_fill": "#e8edf2",
        "swimlane_stroke": "#90a4ae", "swimlane_header": "#455a64",
        "swimlane_header_text": "#ffffff", "canvas_bg": "#f5f5f5",
        "phase_line": "#b0bec5", "phase_text": "#607d8b",
        "note_fill": "#fff9c4", "note_stroke": "#fbc02d",
        "note_text": "#5d4037", "shadow": "#c0c0c0",
        "step_band_even": "#f5f5f5", "step_band_odd": "#eeeeee",
        "port_color": "#455a64", "port_hover": "#1976d2",
        "box_fill": "#e0e7ee", "box_stroke": "#90a4ae",
    },
    "Blueprint": {
        "node_fill": "#e3f2fd", "node_stroke": "#1565c0",
        "node_text": "#0d47a1", "edge_stroke": "#1976d2",
        "edge_label": "#1565c0", "swimlane_fill": "#bbdefb",
        "swimlane_stroke": "#64b5f6", "swimlane_header": "#1565c0",
        "swimlane_header_text": "#ffffff", "canvas_bg": "#e8eaf6",
        "phase_line": "#90caf9", "phase_text": "#1565c0",
        "note_fill": "#e1f5fe", "note_stroke": "#0288d1",
        "note_text": "#01579b", "shadow": "#9fa8da",
        "step_band_even": "#e8eaf6", "step_band_odd": "#c5cae9",
        "port_color": "#1565c0", "port_hover": "#42a5f5",
        "box_fill": "#bbdefb", "box_stroke": "#64b5f6",
    },
    "Warm": {
        "node_fill": "#fff8e1", "node_stroke": "#e65100",
        "node_text": "#bf360c", "edge_stroke": "#d84315",
        "edge_label": "#bf360c", "swimlane_fill": "#ffe0b2",
        "swimlane_stroke": "#ffb74d", "swimlane_header": "#e65100",
        "swimlane_header_text": "#ffffff", "canvas_bg": "#fff3e0",
        "phase_line": "#ffcc80", "phase_text": "#e65100",
        "note_fill": "#fff8e1", "note_stroke": "#ff8f00",
        "note_text": "#e65100", "shadow": "#ffcc80",
        "step_band_even": "#fff3e0", "step_band_odd": "#ffe0b2",
        "port_color": "#e65100", "port_hover": "#ff9800",
        "box_fill": "#ffe0b2", "box_stroke": "#ffb74d",
    },
    "Monochrome": {
        "node_fill": "#fafafa", "node_stroke": "#424242",
        "node_text": "#212121", "edge_stroke": "#616161",
        "edge_label": "#616161", "swimlane_fill": "#eeeeee",
        "swimlane_stroke": "#bdbdbd", "swimlane_header": "#424242",
        "swimlane_header_text": "#ffffff", "canvas_bg": "#f5f5f5",
        "phase_line": "#9e9e9e", "phase_text": "#616161",
        "note_fill": "#f5f5f5", "note_stroke": "#9e9e9e",
        "note_text": "#424242", "shadow": "#bdbdbd",
        "step_band_even": "#f5f5f5", "step_band_odd": "#eeeeee",
        "port_color": "#424242", "port_hover": "#757575",
        "box_fill": "#e0e0e0", "box_stroke": "#bdbdbd",
    },
    "Dark": {
        "node_fill": "#313244", "node_stroke": "#89b4fa",
        "node_text": "#cdd6f4", "edge_stroke": "#a6adc8",
        "edge_label": "#bac2de", "swimlane_fill": "#1e1e2e",
        "swimlane_stroke": "#45475a", "swimlane_header": "#89b4fa",
        "swimlane_header_text": "#1e1e2e", "canvas_bg": "#181825",
        "phase_line": "#45475a", "phase_text": "#6c7086",
        "note_fill": "#45475a", "note_stroke": "#89b4fa",
        "note_text": "#cdd6f4", "shadow": "#11111b",
        "step_band_even": "#1e1e2e", "step_band_odd": "#232336",
        "port_color": "#89b4fa", "port_hover": "#74c7ec",
        "box_fill": "#313244", "box_stroke": "#45475a",
    },
    "Synthwave": {
        "node_fill": "#241b35", "node_stroke": "#ff6ac1",
        "node_text": "#f3e6ff", "edge_stroke": "#00d9ff",
        "edge_label": "#72f1b8", "swimlane_fill": "#1a1128",
        "swimlane_stroke": "#ff6ac1", "swimlane_header": "#ff6ac1",
        "swimlane_header_text": "#1a1128", "canvas_bg": "#120d1a",
        "phase_line": "#7b5ea7", "phase_text": "#ff6ac1",
        "note_fill": "#2d1f42", "note_stroke": "#00d9ff",
        "note_text": "#72f1b8", "shadow": "#0a0710",
        "step_band_even": "#120d1a", "step_band_odd": "#1a1128",
        "port_color": "#ff6ac1", "port_hover": "#ff8ad8",
        "box_fill": "#241b35", "box_stroke": "#ff6ac1",
    },
    "Forest": {
        "node_fill": "#f0f7f0", "node_stroke": "#2d6a2d",
        "node_text": "#1a3d1a", "edge_stroke": "#4a8c4a",
        "edge_label": "#2d6a2d", "swimlane_fill": "#e0f0e0",
        "swimlane_stroke": "#7ab97a", "swimlane_header": "#2d6a2d",
        "swimlane_header_text": "#ffffff", "canvas_bg": "#f5faf5",
        "phase_line": "#a0cfa0", "phase_text": "#2d6a2d",
        "note_fill": "#e8f5e9", "note_stroke": "#4caf50",
        "note_text": "#1b5e20", "shadow": "#a5d6a7",
        "step_band_even": "#f5faf5", "step_band_odd": "#eaf5ea",
        "port_color": "#2d6a2d", "port_hover": "#4a8c4a",
        "box_fill": "#e0f0e0", "box_stroke": "#7ab97a",
    },
}

DEFAULT_COLORS = COLOR_SCHEMES["Default"]

SHAPE_TYPES = [
    "rect", "rounded", "diamond", "circle",
    "parallelogram", "hexagon", "cylinder", "stadium",
]

KEYWORDS = [
    "swimlane", "group", "note", "direction", "box",
]

ATTRIBUTE_KEYS = [
    "step", "type", "owner", "status", "tags", "priority", "id",
]

TYPE_VALUES = [
    "process", "decision", "input", "output", "datastore",
    "start", "end", "manual", "automated", "approval", "external",
]

STATUS_VALUES = ["draft", "active", "deprecated", "blocked", "complete"]
PRIORITY_VALUES = ["low", "medium", "high", "critical"]


# ═══════════════════════════════════════════════
#  DSL Parser
# ═══════════════════════════════════════════════

# Connection patterns — order matters (most specific first).
CONNECTION_PATTERNS = [
    (re.compile(r"^(\w+)\s*==>\s*(\w+)(.*)$"), "thick", True),
    (re.compile(r"^(\w+)\s*-->\s*(\w+)(.*)$"), "dashed", True),
    (re.compile(r"^(\w+)\s*->\s*(\w+)(.*)$"), "solid", True),
    (re.compile(r"^(\w+)\s*---\s*(\w+)(.*)$"), "solid_line", False),
    (re.compile(r"^(\w+)\s*-\.-\s*(\w+)(.*)$"), "dotted_line", False),
]

OBJECT_RE = re.compile(
    r'^\[(\w+)\]\s+(\w+)\s+"((?:[^"\\]|\\.)*)"\s*(.*?)\s*$'
)
SWIMLANE_OPEN_RE = re.compile(r'^swimlane\s+"([^"]+)"\s*\{')
BOX_OPEN_RE = re.compile(r'^box\s+"([^"]+)"(?:\s*\{([^}]*)\})?\s*\{')
GROUP_OPEN_RE = re.compile(r'^group\s+"([^"]+)"\s*\{')
NOTE_RE = re.compile(r'^note\s+"([^"]+)"\s*\[(\w+)\]')
DIRECTION_NAMES = {
    "top-to-bottom": "top-to-bottom", "tb": "top-to-bottom",
    "left-to-right": "left-to-right", "lr": "left-to-right",
    "bottom-to-top": "bottom-to-top", "bt": "bottom-to-top",
    "right-to-left": "right-to-left", "rl": "right-to-left",
}
DIRECTION_RE = re.compile(
    r'^direction\s+(top-to-bottom|left-to-right|bottom-to-top|right-to-left|LR|TB|RL|BT)\s*$',
    re.IGNORECASE,
)
COMMENT_RE = re.compile(r'^\s*//')
STEP_RE = re.compile(r'step:(\d+)')
STYLE_RE = re.compile(r'\{([^}]*)\}')
POS_RE = re.compile(r'@\((\d+),\s*(\d+)\)')
ATTR_RE = re.compile(r'(\w+):((?:"[^"]*"|\S+))')
GROUP_MEMBER_RE = re.compile(r'^\s*(\w+)\s*$')

CONN_LABEL_RE = re.compile(r':\s*"((?:[^"\\]|\\.)*)"')
CONN_HINT_RE = re.compile(r'\[(above|below|center)\]')


def _parse_inline_style(raw):
    style = {}
    if not raw:
        return style
    for part in raw.split(","):
        part = part.strip()
        if ":" in part:
            k, v = part.split(":", 1)
            style[k.strip()] = v.strip()
    return style


def _parse_attrs(rest):
    """Parse key:value attribute pairs from the remainder of an object line."""
    attrs = {}
    for m in ATTR_RE.finditer(rest):
        key = m.group(1)
        val = m.group(2).strip('"')
        attrs[key] = val
    return attrs


def _parse_connection_rest(rest):
    """Parse label, hint, and attributes from the rest of a connection line."""
    label = ""
    hint = ""
    condition = None
    weight = None

    lm = CONN_LABEL_RE.search(rest)
    if lm:
        label = lm.group(1).replace("\\n", "\n")
    hm = CONN_HINT_RE.search(rest)
    if hm:
        hint = hm.group(1)

    attrs = _parse_attrs(rest)
    condition = attrs.get("condition")
    try:
        weight = int(attrs.get("weight", "0")) or None
    except (ValueError, TypeError):
        weight = None

    return label, hint, condition, weight


SETTING_RE = re.compile(r'^setting\s+(\w+)\s+(.+)$')

SETTING_KEYS = {
    "node_width", "node_height", "h_gap", "v_gap",
    "font_size", "container_padding", "swimlane_gap",
    "color_scheme",
}


def parse_diagram(code):
    result = {
        "direction": "top-to-bottom",
        "objects": [],
        "connections": [],
        "swimlanes": [],
        "boxes": [],
        "groups": [],
        "notes": [],
        "errors": [],
        "_object_lines": {},
        "_settings": {},  # settings declared in code
    }
    name_map = {}
    current_swimlane = None
    current_box = None
    # Stack of open blocks: ("swimlane", name) | ("box", label) | ("group", label)
    block_stack = []

    lines = code.split("\n")
    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line or COMMENT_RE.match(line):
            continue

        # Direction
        m = DIRECTION_RE.match(line)
        if m:
            raw_dir = m.group(1).lower()
            result["direction"] = DIRECTION_NAMES.get(raw_dir, "top-to-bottom")
            continue

        # Setting (e.g. "setting node_width 160")
        m = SETTING_RE.match(line)
        if m:
            key = m.group(1)
            val = m.group(2).strip().strip('"')
            if key in SETTING_KEYS:
                result["_settings"][key] = val
            continue

        # Note
        m = NOTE_RE.match(line)
        if m:
            result["notes"].append({"text": m.group(1), "attached_to": m.group(2)})
            continue

        # Swimlane open
        m = SWIMLANE_OPEN_RE.match(line)
        if m:
            sl_name = m.group(1)
            current_swimlane = {"name": sl_name, "object_names": [], "line_number": line_num}
            result["swimlanes"].append(current_swimlane)
            block_stack.append(("swimlane", sl_name))
            continue

        # Box open
        m = BOX_OPEN_RE.match(line)
        if m:
            box_label = m.group(1)
            box_style = _parse_inline_style(m.group(2)) if m.group(2) else None
            current_box = {
                "label": box_label, "style": box_style,
                "object_names": [],
                "swimlane": current_swimlane["name"] if current_swimlane else None,
            }
            result["boxes"].append(current_box)
            block_stack.append(("box", box_label))
            continue

        # Group open
        m = GROUP_OPEN_RE.match(line)
        if m:
            grp = {"label": m.group(1), "object_names": []}
            result["groups"].append(grp)
            block_stack.append(("group", grp["label"]))
            continue

        # Closing brace
        if line == "}":
            if block_stack:
                btype, _ = block_stack.pop()
                if btype == "swimlane":
                    current_swimlane = None
                elif btype == "box":
                    current_box = None
                elif btype == "group":
                    pass
            continue

        # Inside a group block — just names
        if block_stack and block_stack[-1][0] == "group":
            gm = GROUP_MEMBER_RE.match(line)
            if gm:
                grp_label = block_stack[-1][1]
                for g in result["groups"]:
                    if g["label"] == grp_label:
                        g["object_names"].append(gm.group(1))
                        break
                continue

        # Object definition
        m = OBJECT_RE.match(line)
        if m:
            shape, name, label_raw, rest = m.group(1), m.group(2), m.group(3), m.group(4)
            if shape not in SHAPE_TYPES:
                result["errors"].append({
                    "line": line_num,
                    "message": f"Unknown shape '{shape}'. Valid: {', '.join(SHAPE_TYPES)}",
                })
                continue
            if name in name_map:
                result["errors"].append({
                    "line": line_num, "message": f"Duplicate name '{name}'",
                })
                continue

            # Multi-line support + auto-capitalize each word
            label = label_raw.replace("\\n", "\n")
            label = "\n".join(
                " ".join(w.capitalize() if w[0:1].islower() else w
                         for w in line.split())
                for line in label.split("\n")
            )

            # Parse step
            step_m = STEP_RE.search(rest)
            if not step_m:
                result["errors"].append({
                    "line": line_num, "message": f"Missing step:N on '{name}'",
                })
                continue
            step = int(step_m.group(1))

            # Parse optional style override
            style = None
            # Find style block that is NOT the box style
            style_matches = list(STYLE_RE.finditer(rest))
            if style_matches:
                style = _parse_inline_style(style_matches[-1].group(1))

            # Parse position pin
            pos = None
            pos_m = POS_RE.search(rest)
            if pos_m:
                pos = (int(pos_m.group(1)), int(pos_m.group(2)))

            # Parse all attributes
            all_attrs = _parse_attrs(rest)
            obj_type = all_attrs.get("type")
            owner = all_attrs.get("owner")
            status = all_attrs.get("status")
            tags_raw = all_attrs.get("tags", "")
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
            priority = all_attrs.get("priority")
            obj_id = None
            if "id" in all_attrs:
                try:
                    obj_id = int(all_attrs["id"])
                except ValueError:
                    obj_id = None

            # Extra attrs (unknown keys)
            known_keys = {"step", "type", "owner", "status", "tags", "priority", "id"}
            extra = {k: v for k, v in all_attrs.items() if k not in known_keys}

            obj = {
                "name": name, "label": label, "shape": shape, "step": step,
                "swimlane": current_swimlane["name"] if current_swimlane else None,
                "box": current_box["label"] if current_box else None,
                "style": style, "pos": pos, "line_number": line_num,
                "type": obj_type, "owner": owner, "status": status,
                "tags": tags, "priority": priority, "id": obj_id,
                "extra_attrs": extra,
            }
            name_map[name] = obj
            result["objects"].append(obj)
            result["_object_lines"][name] = line_num

            if current_swimlane:
                current_swimlane["object_names"].append(name)
            if current_box:
                current_box["object_names"].append(name)
            continue

        # Connection
        matched = False
        for regex, etype, has_arrow in CONNECTION_PATTERNS:
            cm = regex.match(line)
            if cm:
                from_name, to_name = cm.group(1), cm.group(2)
                rest = cm.group(3)
                label, hint, condition, weight = _parse_connection_rest(rest)
                result["connections"].append({
                    "from_name": from_name, "to_name": to_name,
                    "label": label, "type": etype, "arrow": has_arrow,
                    "label_hint": hint or None,
                    "condition": condition, "weight": weight,
                    "line_number": line_num,
                })
                matched = True
                break
        if matched:
            continue

        result["errors"].append({"line": line_num, "message": f'Unrecognized: "{line}"'})

    # Validate references
    all_names = set(name_map.keys())
    for conn in result["connections"]:
        for ref in (conn["from_name"], conn["to_name"]):
            if ref not in all_names:
                result["errors"].append({
                    "line": conn["line_number"],
                    "message": f"Unknown object '{ref}' in connection",
                })
    for note in result["notes"]:
        if note["attached_to"] not in all_names:
            result["errors"].append({
                "line": 0, "message": f"Note target '{note['attached_to']}' not found",
            })
    for grp in result["groups"]:
        for gn in grp["object_names"]:
            if gn not in all_names:
                result["errors"].append({
                    "line": 0, "message": f"Group member '{gn}' not found",
                })

    if block_stack:
        result["errors"].append({"line": len(lines), "message": "Unclosed block — missing }"})

    return result


# ═══════════════════════════════════════════════
#  Step-Based Layout Engine
# ═══════════════════════════════════════════════

def _snap_to_grid(val, grid_size=10):
    """Snap a value to the nearest grid increment."""
    return round(val / grid_size) * grid_size


def _measure_node(label, shape, base_w, base_h):
    """Return (w, h) for a node that fits its label text, snapped to grid.

    Shapes like diamond and cylinder need extra space so text doesn't
    get clipped by the shape boundary.
    """
    lines = label.split("\n") if label else [""]
    max_line_len = max(len(ln) for ln in lines)
    num_lines = len(lines)
    text_w = max_line_len * 8 + 24
    text_h = num_lines * 18 + 14

    w = max(base_w, text_w)
    h = max(base_h, text_h)

    # Inflate for shapes where text-safe area < bounding box.
    # Keep inflation modest so diamonds don't balloon.
    if shape == "diamond":
        w = max(w + 30, base_w)   # add fixed padding, not 1.5x multiplier
        h = max(h + 16, base_h)
    elif shape == "circle":
        d = max(w, h, 56)
        w = h = d
    elif shape == "parallelogram":
        w = max(w + 30, base_w)
    elif shape == "hexagon":
        w = max(w + 34, base_w)
    elif shape == "cylinder":
        h = max(h + 16, base_h)

    # Snap to 10px grid so nodes align cleanly
    return (_snap_to_grid(w), _snap_to_grid(h))


def compute_layout(parsed, settings=None):
    """Step-based grid layout.  Natively supports all four directions.

    TB/BT: swimlanes = vertical columns, steps = horizontal rows.
    LR/RL: swimlanes = horizontal rows,  steps = vertical columns.
    """
    settings = settings or {}
    direction = settings.get("direction", "top-to-bottom")
    base_w = settings.get("node_width", 140)
    base_h = settings.get("node_height", 50)
    h_gap = settings.get("h_gap", 60)
    v_gap = settings.get("v_gap", 70)
    pad = settings.get("container_padding", 20)
    sl_gap = settings.get("swimlane_gap", 10)
    sl_hdr = 36
    box_hdr = 26
    margin = 50
    step_label_sz = 30
    GRID = 10

    is_horizontal = direction in ("left-to-right", "right-to-left")
    is_reversed = direction in ("bottom-to-top", "right-to-left")

    objects = parsed["objects"]
    swimlanes = parsed["swimlanes"]

    empty = {"positions": {}, "swimlane_rects": {}, "box_rects": {},
             "step_bands": [], "column_widths": {}, "row_heights": {},
             "node_sizes": {}, "direction": direction}
    if not objects:
        return empty

    # ── Per-node sizes ──
    node_sizes = {}
    for obj in objects:
        w, h = _measure_node(obj["label"], obj["shape"], base_w, base_h)
        node_sizes[obj["name"]] = (w, h)

    # ── Lanes & steps ──
    sl_names = [sl["name"] for sl in swimlanes]
    has_free = any(o["swimlane"] is None for o in objects)
    lanes = list(sl_names)
    if has_free:
        lanes.append("__free__")

    all_steps = sorted(set(o["step"] for o in objects))
    if is_reversed:
        all_steps = list(reversed(all_steps))
    if not all_steps:
        all_steps = [0]

    # Grid: (step, lane) → [names]
    grid = defaultdict(list)
    for obj in objects:
        lane = obj["swimlane"] or "__free__"
        grid[(obj["step"], lane)].append(obj["name"])

    # In TB: lanes are columns (x-axis), steps are rows (y-axis).
    # In LR: lanes are rows (y-axis), steps are columns (x-axis).

    # ── Lane sizes (cross-axis extent per lane) ──
    lane_sizes = {}
    for lane in lanes:
        max_cross = base_w if not is_horizontal else base_h
        for step in all_steps:
            for name in grid.get((step, lane), []):
                nw, nh = node_sizes.get(name, (base_w, base_h))
                cross = nw if not is_horizontal else nh
                max_cross = max(max_cross, cross)
        lane_sizes[lane] = max_cross + 2 * pad

    # ── Step sizes (flow-axis extent per step) ──
    step_sizes = {}
    for step in all_steps:
        max_flow = (base_h if not is_horizontal else base_w) + v_gap
        for lane in lanes:
            names = grid.get((step, lane), [])
            n = len(names)
            if n == 0:
                continue
            if not is_horizontal:
                # TB/BT: nodes stack vertically in a cell
                stack = sum(node_sizes.get(nm, (base_w, base_h))[1] for nm in names)
                stack += max(0, n - 1) * (v_gap * 0.5) + v_gap
            else:
                # LR/RL: nodes stack vertically in a cell (within a row-lane)
                stack = sum(node_sizes.get(nm, (base_w, base_h))[1] for nm in names)
                stack += max(0, n - 1) * (v_gap * 0.5) + v_gap
                # But the flow-axis is width
                flow_max = max(node_sizes.get(nm, (base_w, base_h))[0] for nm in names)
                max_flow = max(max_flow, flow_max + h_gap)
            max_flow = max(max_flow, stack if not is_horizontal else max_flow)
        step_sizes[step] = max_flow

    # ── Cross-axis positions (lane positions) ──
    lane_pos = {}  # lane → cross-axis start coordinate
    cross_cursor = margin + step_label_sz
    for lane in lanes:
        lane_pos[lane] = cross_cursor
        cross_cursor += lane_sizes[lane] + sl_gap

    # ── Flow-axis positions (step positions) ──
    step_pos = {}  # step → flow-axis start coordinate
    flow_cursor = margin + sl_hdr
    for step in all_steps:
        step_pos[step] = flow_cursor
        flow_cursor += step_sizes[step]

    total_cross = cross_cursor + margin
    total_flow = flow_cursor + margin

    # ── Place objects ──
    positions = {}
    for (step, lane), names in grid.items():
        if not is_horizontal:
            # TB/BT: x = lane center, y = stacked in step row
            cx = _snap_to_grid(lane_pos[lane] + lane_sizes[lane] / 2, GRID)
            n = len(names)
            stack_h = sum(node_sizes.get(nm, (base_w, base_h))[1] for nm in names)
            stack_h += max(0, n - 1) * (v_gap * 0.5)
            flow_mid = step_pos[step] + step_sizes[step] / 2
            y_cur = _snap_to_grid(flow_mid - stack_h / 2, GRID)
            for name in names:
                nw, nh = node_sizes.get(name, (base_w, base_h))
                obj = next((o for o in objects if o["name"] == name), None)
                if obj and obj.get("pos"):
                    positions[name] = obj["pos"]
                else:
                    positions[name] = (cx, _snap_to_grid(y_cur + nh / 2, GRID))
                y_cur += nh + v_gap * 0.5
        else:
            # LR/RL: y = lane center, x = step column center
            cy = _snap_to_grid(lane_pos[lane] + lane_sizes[lane] / 2, GRID)
            flow_mid = step_pos[step] + step_sizes[step] / 2
            # Stack multiple parallel nodes vertically within the lane
            n = len(names)
            stack_h = sum(node_sizes.get(nm, (base_w, base_h))[1] for nm in names)
            stack_h += max(0, n - 1) * (v_gap * 0.5)
            y_start = _snap_to_grid(cy - stack_h / 2, GRID)
            for name in names:
                nw, nh = node_sizes.get(name, (base_w, base_h))
                obj = next((o for o in objects if o["name"] == name), None)
                if obj and obj.get("pos"):
                    positions[name] = obj["pos"]
                else:
                    px = _snap_to_grid(flow_mid, GRID)
                    py = _snap_to_grid(y_start + nh / 2, GRID)
                    positions[name] = (px, py)
                y_start += nh + v_gap * 0.5

    # ── Swimlane rects (must fully contain ALL children using actual sizes) ──
    swimlane_rects = {}
    for sl in swimlanes:
        lane = sl["name"]
        if lane not in lane_pos:
            continue
        child_names = [n for n in sl["object_names"] if n in positions]
        if not child_names:
            continue

        # Compute tight bounding box from actual child positions + sizes
        child_lefts, child_rights, child_tops, child_bottoms = [], [], [], []
        for cn in child_names:
            cx, cy = positions[cn]
            cnw, cnh = node_sizes.get(cn, (base_w, base_h))
            child_lefts.append(cx - cnw / 2)
            child_rights.append(cx + cnw / 2)
            child_tops.append(cy - cnh / 2)
            child_bottoms.append(cy + cnh / 2)

        if not is_horizontal:
            # TB/BT: swimlane is a vertical column
            sx = min(child_lefts) - pad
            sw = max(child_rights) - min(child_lefts) + 2 * pad
            # Ensure column is at least as wide as lane_sizes
            sx = min(sx, lane_pos[lane] - pad / 2)
            sw = max(sw, lane_sizes[lane] + pad)
            sy = margin
            sh = max(child_bottoms) + pad - sy
            sh = max(sh, total_flow - 2 * margin)
        else:
            # LR/RL: swimlane is a horizontal row
            sy = min(child_tops) - pad
            sh = max(child_bottoms) - min(child_tops) + 2 * pad
            # Ensure row is at least as tall as lane_sizes
            sy = min(sy, lane_pos[lane] - pad / 2)
            sh = max(sh, lane_sizes[lane] + pad)
            sx = margin
            sw = max(child_rights) + pad - sx
            sw = max(sw, total_flow - 2 * margin)

        swimlane_rects[lane] = (sx, sy, sw, sh)

    # ── Box rects (must fully contain ALL children using actual sizes) ──
    box_rects = {}
    for box in parsed["boxes"]:
        child_names = [n for n in box["object_names"] if n in positions]
        if not child_names:
            continue
        x1 = min(positions[n][0] - node_sizes.get(n, (base_w, base_h))[0] / 2
                 for n in child_names) - pad
        y1 = min(positions[n][1] - node_sizes.get(n, (base_w, base_h))[1] / 2
                 for n in child_names) - pad - box_hdr
        x2 = max(positions[n][0] + node_sizes.get(n, (base_w, base_h))[0] / 2
                 for n in child_names) + pad
        y2 = max(positions[n][1] + node_sizes.get(n, (base_w, base_h))[1] / 2
                 for n in child_names) + pad
        box_rects[box["label"]] = (x1, y1, x2 - x1, y2 - y1)

    # ── Step bands ──
    step_bands = []
    if not is_horizontal:
        # Horizontal bands (full width)
        all_x = [lane_pos[c] - pad for c in lanes]
        all_xr = [lane_pos[c] + lane_sizes[c] + pad for c in lanes]
        bx = min(all_x) if all_x else margin
        bw = (max(all_xr) if all_xr else total_cross) - bx
        for step in all_steps:
            y0 = step_pos[step]
            y1 = y0 + step_sizes[step]
            step_bands.append((step, y0, y1, bx, bw))
    else:
        # Vertical bands (full height)
        all_y = [lane_pos[c] - pad for c in lanes]
        all_yr = [lane_pos[c] + lane_sizes[c] + pad for c in lanes]
        by = min(all_y) if all_y else margin
        bh = (max(all_yr) if all_yr else total_cross) - by
        for step in all_steps:
            x0 = step_pos[step]
            x1 = x0 + step_sizes[step]
            # For horizontal: step_bands store (step, x0, x1, by, bh)
            step_bands.append((step, x0, x1, by, bh))

    return {
        "positions": positions,
        "swimlane_rects": swimlane_rects,
        "box_rects": box_rects,
        "step_bands": step_bands,
        "column_widths": lane_sizes,
        "row_heights": step_sizes,
        "node_sizes": node_sizes,
        "direction": direction,
    }


# ═══════════════════════════════════════════════
#  Shape Drawing Helpers (for QPainterPath)
# ═══════════════════════════════════════════════

def shape_path(shape, w, h):
    """Return a QPainterPath for the given shape centered at (0,0)."""
    p = QPainterPath()
    hw, hh = w / 2, h / 2
    if shape == "rect":
        p.addRect(-hw, -hh, w, h)
    elif shape == "rounded":
        p.addRoundedRect(-hw, -hh, w, h, 12, 12)
    elif shape == "diamond":
        poly = QPolygonF([QPointF(0, -hh), QPointF(hw, 0),
                          QPointF(0, hh), QPointF(-hw, 0)])
        p.addPolygon(poly)
        p.closeSubpath()
    elif shape == "circle":
        r = max(hw, hh)
        p.addEllipse(QPointF(0, 0), r, r)
    elif shape == "parallelogram":
        sk = 18
        poly = QPolygonF([QPointF(-hw + sk, -hh), QPointF(hw, -hh),
                          QPointF(hw - sk, hh), QPointF(-hw, hh)])
        p.addPolygon(poly)
        p.closeSubpath()
    elif shape == "hexagon":
        hx = 20
        poly = QPolygonF([QPointF(-hw + hx, -hh), QPointF(hw - hx, -hh),
                          QPointF(hw, 0), QPointF(hw - hx, hh),
                          QPointF(-hw + hx, hh), QPointF(-hw, 0)])
        p.addPolygon(poly)
        p.closeSubpath()
    elif shape == "cylinder":
        ry = 10
        p.addRect(-hw, -hh + ry, w, h - 2 * ry)
        p.addEllipse(QPointF(0, -hh + ry), hw, ry)
        p.addEllipse(QPointF(0, hh - ry), hw, ry)
    elif shape == "stadium":
        p.addRoundedRect(-hw, -hh, w, h, hh, hh)
    else:
        p.addRect(-hw, -hh, w, h)
    return p


# ═══════════════════════════════════════════════
#  DiagramNode (QGraphicsItem)
# ═══════════════════════════════════════════════

class DiagramNode(QGraphicsItem):
    PORT_OFFSETS = {
        "top": (0, -0.5), "bottom": (0, 0.5),
        "left": (-0.5, 0), "right": (0.5, 0),
    }

    def __init__(self, obj_data, node_w, node_h, colors, font_size=11):
        super().__init__()
        self.obj = obj_data
        self.node_w = node_w
        self.node_h = node_h
        self.colors = colors
        self.font_size = font_size
        self.is_filtered_out = False
        self._hovered = False
        self.edges = []  # DiagramEdge instances connected to this node

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setOffset(3, 3)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        self._build_tooltip()

    def _build_tooltip(self):
        o = self.obj
        lines = [f"{o['name']} — \"{o['label'].replace(chr(10), ' ')}\"", "━" * 30]
        lines.append(f"Shape:    {o['shape']}")
        lines.append(f"Step:     {o['step']}")
        if o.get("swimlane"):
            lines.append(f"Swimlane: {o['swimlane']}")
        for k in ("type", "owner", "status", "priority"):
            if o.get(k):
                lines.append(f"{k.title():<10}{o[k]}")
        if o.get("tags"):
            lines.append(f"Tags:     {', '.join(o['tags'])}")
        if o.get("id") is not None:
            lines.append(f"ID:       {o['id']}")
        for k, v in o.get("extra_attrs", {}).items():
            lines.append(f"{k}:     {v}")
        self.setToolTip("\n".join(lines))

    def boundingRect(self):
        m = 4  # margin for selection border
        return QRectF(-self.node_w / 2 - m, -self.node_h / 2 - m,
                      self.node_w + 2 * m, self.node_h + 2 * m)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        o = self.obj
        ns = o.get("style") or {}
        fill_color = hex_to_qcolor(ns.get("fill", self.colors["node_fill"]))
        stroke_color = hex_to_qcolor(ns.get("stroke", self.colors["node_stroke"]))
        text_color = hex_to_qcolor(ns.get("text", self.colors["node_text"]))
        stroke_w = float(ns.get("stroke_width", "2"))

        # Priority adjustments
        priority = o.get("priority")
        if priority == "critical":
            stroke_w = 3
            stroke_color = QColor(
                min(255, stroke_color.red() + 40),
                max(0, stroke_color.green() - 20),
                max(0, stroke_color.blue() - 20),
            )
        elif priority == "high":
            stroke_w = 2.5
        elif priority == "low":
            stroke_w = 1
            fill_color.setAlpha(220)

        # Status adjustments
        status = o.get("status")
        pen = QPen(stroke_color, stroke_w)
        if status == "draft":
            pen.setStyle(Qt.DashLine)
        elif status == "blocked":
            pen.setColor(QColor("#f38ba8"))
        elif status == "deprecated":
            fill_color.setAlpha(100)

        # Filter dimming
        if self.is_filtered_out:
            painter.setOpacity(0.15)

        # Draw shape
        path = shape_path(o["shape"], self.node_w, self.node_h)
        painter.setPen(pen)
        painter.setBrush(QBrush(fill_color))
        painter.drawPath(path)

        # Status decorations
        if status == "deprecated":
            painter.setPen(QPen(QColor("#f38ba8"), 1.5))
            painter.drawLine(QPointF(-self.node_w / 2, -self.node_h / 2),
                             QPointF(self.node_w / 2, self.node_h / 2))
        elif status == "complete":
            painter.setPen(QPen(QColor("#a6e3a1"), 2))
            cx, cy = self.node_w / 2 - 10, -self.node_h / 2 + 10
            painter.drawLine(QPointF(cx - 4, cy), QPointF(cx - 1, cy + 3))
            painter.drawLine(QPointF(cx - 1, cy + 3), QPointF(cx + 5, cy - 4))

        # Label — draw inside the text-safe area of the shape
        painter.setPen(text_color)
        font = QFont("Segoe UI", self.font_size)
        painter.setFont(font)

        # Compute text-safe rectangle (inscribed area where text won't be
        # clipped by the shape boundary)
        hw, hh = self.node_w / 2, self.node_h / 2
        shape = o["shape"]
        if shape == "diamond":
            # Inscribed rect of a diamond is ~50% of each dimension
            inset_x, inset_y = hw * 0.35, hh * 0.35
        elif shape == "circle":
            # Inscribed rect of a circle: side = r*sqrt(2) ≈ 0.7*diameter
            inset_x = inset_y = max(hw, hh) * 0.3
        elif shape == "parallelogram":
            inset_x, inset_y = 22, 6
        elif shape == "hexagon":
            inset_x, inset_y = 24, 6
        elif shape == "cylinder":
            inset_x, inset_y = 8, 14  # avoid top/bottom ellipses
        else:
            inset_x, inset_y = 8, 6

        text_rect = QRectF(-hw + inset_x, -hh + inset_y,
                           self.node_w - 2 * inset_x, self.node_h - 2 * inset_y)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, o["label"])

        # Pin indicator
        if o.get("pos"):
            painter.setBrush(QBrush(QColor("#89b4fa")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(self.node_w / 2 - 6, -self.node_h / 2 + 6), 3, 3)

        # Selection highlight
        if self.isSelected():
            painter.setPen(QPen(QColor("#89b4fa"), 2.5, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect().adjusted(2, 2, -2, -2))

        # Ports on hover
        if self._hovered or self.isSelected():
            port_color = hex_to_qcolor(self.colors.get("port_color", "#455a64"))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(port_color))
            for name, (dx, dy) in self.PORT_OFFSETS.items():
                px = dx * self.node_w
                py = dy * self.node_h
                painter.drawEllipse(QPointF(px, py), 4, 4)

        painter.setOpacity(1.0)

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()

    def port_pos(self, port_name):
        dx, dy = self.PORT_OFFSETS.get(port_name, (0, 0))
        return self.mapToScene(QPointF(dx * self.node_w, dy * self.node_h))

    def best_port_to(self, target_pos):
        best = None
        best_dist = float("inf")
        for name, (dx, dy) in self.PORT_OFFSETS.items():
            p = self.mapToScene(QPointF(dx * self.node_w, dy * self.node_h))
            d = (p.x() - target_pos.x()) ** 2 + (p.y() - target_pos.y()) ** 2
            if d < best_dist:
                best_dist = d
                best = name
        return best

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Snap to 10px grid during drag
            grid = 10
            x = round(value.x() / grid) * grid
            y = round(value.y() / grid) * grid
            return QPointF(x, y)
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Update connected edges visually
            for edge in self.edges:
                edge.prepareGeometryChange()
                edge.update()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self._drag_start_pos = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # Only emit node_moved ONCE on release, and only if it actually moved
        if hasattr(self, '_drag_start_pos') and self.pos() != self._drag_start_pos:
            if self.scene():
                self.scene().node_moved.emit(
                    self.obj["name"], int(self.pos().x()), int(self.pos().y())
                )


# ═══════════════════════════════════════════════
#  DiagramEdge — dynamic tether between two nodes
# ═══════════════════════════════════════════════

class DiagramEdge(QGraphicsItem):
    """A connection line that stays tethered to its source and target
    DiagramNode objects.  Whenever either node moves, the edge
    recalculates its path automatically.
    """

    def __init__(self, conn_data, source_node, target_node, colors, font_size=11, direction="top-to-bottom"):
        super().__init__()
        self.conn = conn_data
        self.source = source_node
        self.target = target_node
        self.colors = colors
        self.font_size = font_size
        self.direction = direction
        self.setZValue(0)
        self.setAcceptHoverEvents(True)
        self._hovered = False
        self._cached_path = None

        # Build tooltip
        tip = [f"{conn_data['from_name']} \u2192 {conn_data['to_name']}"]
        if conn_data.get("label"):
            tip.append(f'Label: "{conn_data["label"]}"')
        if conn_data.get("condition"):
            tip.append(f'Condition: {conn_data["condition"]}')
        if conn_data.get("weight"):
            tip.append(f'Weight: {conn_data["weight"]}')
        self.setToolTip("\n".join(tip))

    def _clip(self, cx, cy, tx, ty, hw, hh):
        dx, dy = tx - cx, ty - cy
        if abs(dx) < 0.001 and abs(dy) < 0.001:
            return QPointF(cx, cy - hh)
        if abs(dx) < 0.001:
            return QPointF(cx, cy + (hh if dy > 0 else -hh))
        if abs(dy) < 0.001:
            return QPointF(cx + (hw if dx > 0 else -hw), cy)
        s = min(hw / abs(dx), hh / abs(dy))
        return QPointF(cx + dx * s, cy + dy * s)

    def _port(self, node, port_name):
        """Get the scene-coordinate position of a named port on a node."""
        dx, dy = DiagramNode.PORT_OFFSETS[port_name]
        p = node.scenePos()
        return QPointF(p.x() + dx * node.node_w, p.y() + dy * node.node_h)

    def _flow_ports(self):
        """Return (source_port, target_port) names based on flow direction.
        In TB: source exits bottom, target enters top.
        In LR: source exits right, target enters left.
        """
        d = self.direction
        if d == "top-to-bottom":
            return "bottom", "top"
        elif d == "bottom-to-top":
            return "top", "bottom"
        elif d == "left-to-right":
            return "right", "left"
        elif d == "right-to-left":
            return "left", "right"
        return "bottom", "top"

    def _build_path(self):
        """Compute the edge path using explicit ports based on direction.
        Edges exit the source from the flow-direction port and enter
        the target from the opposite port. Cross-lane edges use
        orthogonal bends.
        """
        sp = self.source.scenePos()
        tp = self.target.scenePos()
        x1, y1 = sp.x(), sp.y()
        x2, y2 = tp.x(), tp.y()
        hw = self.source.node_w / 2
        hh = self.source.node_h / 2
        hw2 = self.target.node_w / 2
        hh2 = self.target.node_h / 2

        path = QPainterPath()
        d = self.direction
        is_horizontal = d in ("left-to-right", "right-to-left")

        # Self-loop
        if self.source is self.target:
            loop_r = 28
            path.moveTo(x1 + hw, y1 - 8)
            path.cubicTo(x1 + hw + loop_r * 1.4, y1 - loop_r - 8,
                         x1 + hw + loop_r * 1.4, y1 + loop_r + 8,
                         x1 + hw, y1 + 8)
            self._arrow_tip = QPointF(x1 + hw, y1 + 8)
            self._arrow_dir = (-0.3, 0.95)
            self._label_pos = QPointF(x1 + hw + loop_r + 4, y1 - 8)
            return path

        # Determine flow direction and detect back-edges
        src_port, tgt_port = self._flow_ports()

        is_back = False
        if d == "top-to-bottom" and y2 < y1 - self.source.node_h:
            is_back = True
        elif d == "bottom-to-top" and y2 > y1 + self.source.node_h:
            is_back = True
        elif d == "left-to-right" and x2 < x1 - self.source.node_w:
            is_back = True
        elif d == "right-to-left" and x2 > x1 + self.source.node_w:
            is_back = True

        if is_back:
            # Swap ports for back-edges (exit from opposite side)
            src_port, tgt_port = tgt_port, src_port

        s = self._port(self.source, src_port)
        e = self._port(self.target, tgt_port)

        # Check if nodes are roughly aligned on the cross-axis
        if is_horizontal:
            aligned = abs(y2 - y1) < 8
        else:
            aligned = abs(x2 - x1) < 8

        if is_back:
            # Route around with detour
            offset = 40
            if is_horizontal:
                mid_y = max(y1 + hh, y2 + hh2) + offset
                path.moveTo(s)
                path.lineTo(s.x(), mid_y)
                path.lineTo(e.x(), mid_y)
                path.lineTo(e)
                self._arrow_dir = (0, -1 if e.y() < mid_y else 1)
            else:
                mid_x = max(x1 + hw, x2 + hw2) + offset
                path.moveTo(s)
                path.lineTo(mid_x, s.y())
                path.lineTo(mid_x, e.y())
                path.lineTo(e)
                self._arrow_dir = (-1 if e.x() < mid_x else 1, 0)
            self._arrow_tip = e
            self._label_pos = QPointF((s.x() + e.x()) / 2, (s.y() + e.y()) / 2)
        elif aligned:
            # Straight line between ports
            path.moveTo(s)
            path.lineTo(e)
            angle = math.atan2(e.y() - s.y(), e.x() - s.x())
            self._arrow_tip = e
            self._arrow_dir = (math.cos(angle), math.sin(angle))
            self._label_pos = QPointF((s.x() + e.x()) / 2, (s.y() + e.y()) / 2)
        else:
            # Orthogonal bend — exit from port, bend, enter port
            if is_horizontal:
                mid_x = (s.x() + e.x()) / 2
                path.moveTo(s)
                path.lineTo(mid_x, s.y())
                path.lineTo(mid_x, e.y())
                path.lineTo(e)
                self._arrow_dir = (1 if e.x() > mid_x else -1, 0)
            else:
                mid_y = (s.y() + e.y()) / 2
                path.moveTo(s)
                path.lineTo(s.x(), mid_y)
                path.lineTo(e.x(), mid_y)
                path.lineTo(e)
                self._arrow_dir = (0, 1 if e.y() > mid_y else -1)
            self._arrow_tip = e
            self._label_pos = QPointF((s.x() + e.x()) / 2, (s.y() + e.y()) / 2)

        return path

    def _get_path(self):
        """Return the cached path, rebuilding only if invalidated."""
        if self._cached_path is None:
            self._cached_path = self._build_path()
        return self._cached_path

    def _invalidate_path(self):
        self._cached_path = None

    def boundingRect(self):
        # Use a generous bounding rect that covers both nodes + margin
        sp = self.source.scenePos()
        tp = self.target.scenePos()
        r = QRectF(sp, tp).normalized()
        m = 60
        return r.adjusted(-m, -m, m, m)

    def shape(self):
        return self._get_path()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        conn = self.conn
        pen = QPen(hex_to_qcolor(self.colors["edge_stroke"]))
        etype = conn["type"]
        weight = conn.get("weight") or 0
        w = 1.8 + min(weight, 5) * 0.4
        if etype == "thick":
            w = max(w, 3.5)
        elif etype == "dashed":
            pen.setStyle(Qt.DashLine)
        elif etype in ("dotted_line", "dotted_arrow"):
            pen.setStyle(Qt.DotLine)
        pen.setWidthF(w)

        is_back = False
        sp = self.source.scenePos()
        tp = self.target.scenePos()
        if self.source is not self.target:
            d = self.direction
            if d == "top-to-bottom" and tp.y() < sp.y() - self.source.node_h:
                is_back = True
            elif d == "bottom-to-top" and tp.y() > sp.y() + self.source.node_h:
                is_back = True
            elif d == "left-to-right" and tp.x() < sp.x() - self.source.node_w:
                is_back = True
            elif d == "right-to-left" and tp.x() > sp.x() + self.source.node_w:
                is_back = True
        if is_back:
            pen.setStyle(Qt.DashDotLine)

        if self._hovered:
            pen.setColor(hex_to_qcolor(self.colors.get("port_hover", "#1976d2")))
            pen.setWidthF(w + 1)

        # Invalidate cache since node positions may have changed
        self._invalidate_path()
        path = self._get_path()
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Arrowhead
        if conn["arrow"]:
            tip = self._arrow_tip
            dx, dy = self._arrow_dir
            size = 10
            angle = math.atan2(dy, dx)
            a1 = angle + math.pi * 0.82
            a2 = angle - math.pi * 0.82
            poly = QPolygonF([
                tip,
                QPointF(tip.x() + size * math.cos(a1), tip.y() + size * math.sin(a1)),
                QPointF(tip.x() + size * math.cos(a2), tip.y() + size * math.sin(a2)),
            ])
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(pen.color()))
            painter.drawPolygon(poly)

        # Edge label — centered on midpoint by default
        if conn["label"]:
            lp = self._label_pos
            hint = conn.get("label_hint") or ""
            if hint == "above":
                lp = QPointF(lp.x(), lp.y() - 16)
            elif hint == "below":
                lp = QPointF(lp.x(), lp.y() + 16)
            # "center" and default: no offset, label sits on midpoint

            font = QFont("Segoe UI", self.font_size - 1)
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(conn["label"])
            th = fm.height()
            bg_rect = QRectF(lp.x() - tw / 2 - 4, lp.y() - th / 2 - 2,
                             tw + 8, th + 4)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(hex_to_qcolor(self.colors["canvas_bg"])))
            painter.drawRoundedRect(bg_rect, 3, 3)
            painter.setPen(hex_to_qcolor(self.colors["edge_label"]))
            painter.setFont(font)
            painter.drawText(bg_rect, Qt.AlignCenter, conn["label"])

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()


# ═══════════════════════════════════════════════
#  DiagramScene
# ═══════════════════════════════════════════════

class DiagramScene(QGraphicsScene):
    node_moved = Signal(str, int, int)  # name, x, y
    connection_created = Signal(str, str)  # from_name, to_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_nodes = {}
        self._colors = dict(DEFAULT_COLORS)
        self._settings = {}
        self._parsed = None
        self._rubber_line = None
        self._drag_source_node = None

    def render_diagram(self, parsed, layout, settings):
        self.clear()
        self.scene_nodes.clear()
        self._parsed = parsed
        self._settings = settings

        scheme = settings.get("color_scheme", "Default")
        self._colors = dict(COLOR_SCHEMES.get(scheme, DEFAULT_COLORS))
        colors = self._colors

        self.setBackgroundBrush(QBrush(hex_to_qcolor(colors["canvas_bg"])))

        node_w = settings.get("node_width", 140)
        node_h = settings.get("node_height", 50)
        font_size = settings.get("font_size", 11)

        positions = layout.get("positions", {})
        if not positions:
            t = self.addText("Enter diagram code to see a preview.",
                             QFont("Segoe UI", 14))
            t.setDefaultTextColor(QColor("#999999"))
            t.setPos(50, 50)
            return

        # ── Background grid ──
        if settings.get("show_grid", True):
            grid_size = 20
            bg_color = hex_to_qcolor(colors["canvas_bg"])
            # Slightly visible grid dots
            grid_color = QColor(bg_color)
            grid_color.setRed(min(255, max(0, grid_color.red() + (15 if grid_color.lightness() > 128 else -15))))
            grid_color.setGreen(min(255, max(0, grid_color.green() + (15 if grid_color.lightness() > 128 else -15))))
            grid_color.setBlue(min(255, max(0, grid_color.blue() + (15 if grid_color.lightness() > 128 else -15))))
            grid_pen = QPen(grid_color, 0.5)

            # Determine extent from positions
            all_x = [p[0] for p in positions.values()]
            all_y = [p[1] for p in positions.values()]
            gx1 = int(min(all_x) - 200) // grid_size * grid_size
            gx2 = int(max(all_x) + 400) // grid_size * grid_size
            gy1 = int(min(all_y) - 200) // grid_size * grid_size
            gy2 = int(max(all_y) + 400) // grid_size * grid_size

            for gx in range(gx1, gx2 + 1, grid_size):
                line = self.addLine(QLineF(gx, gy1, gx, gy2), grid_pen)
                line.setZValue(-5)
            for gy in range(gy1, gy2 + 1, grid_size):
                line = self.addLine(QLineF(gx1, gy, gx2, gy), grid_pen)
                line.setZValue(-5)

        # Step bands — direction-aware
        direction = settings.get("direction", "top-to-bottom")
        is_horizontal = direction in ("left-to-right", "right-to-left")
        show_steps = settings.get("show_step_numbers", True)

        for entry in layout.get("step_bands", []):
            step = entry[0]
            band_color = colors["step_band_odd"] if step % 2 else colors["step_band_even"]
            if not is_horizontal:
                # TB/BT: horizontal bands — (step, y0, y1, bx, bw)
                _, y0, y1, bx, bw = entry
                rect = self.addRect(QRectF(bx, y0, bw, y1 - y0),
                                    QPen(Qt.NoPen), QBrush(hex_to_qcolor(band_color)))
                rect.setZValue(-4)
                if show_steps:
                    lbl = self.addText(str(step), QFont("Segoe UI", 9, QFont.Bold))
                    lbl.setDefaultTextColor(hex_to_qcolor(colors["phase_text"]))
                    lbl.setPos(bx + 4, y0 + 2)
                    lbl.setZValue(-3)
            else:
                # LR/RL: vertical bands — (step, x0, x1, by, bh)
                _, x0, x1, by, bh = entry
                rect = self.addRect(QRectF(x0, by, x1 - x0, bh),
                                    QPen(Qt.NoPen), QBrush(hex_to_qcolor(band_color)))
                rect.setZValue(-4)
                if show_steps:
                    lbl = self.addText(str(step), QFont("Segoe UI", 9, QFont.Bold))
                    lbl.setDefaultTextColor(hex_to_qcolor(colors["phase_text"]))
                    lbl.setPos(x0 + 2, by + 2)
                    lbl.setZValue(-3)

        # Swimlane backgrounds — direction-aware headers
        sl_hdr_size = 30
        for sl_name, (sx, sy, sw, sh) in layout.get("swimlane_rects", {}).items():
            rect = self.addRect(QRectF(sx, sy, sw, sh),
                                QPen(hex_to_qcolor(colors["swimlane_stroke"]), 1.5),
                                QBrush(hex_to_qcolor(colors["swimlane_fill"])))
            rect.setZValue(-3)

            if not is_horizontal:
                # TB/BT: header bar at top, full width
                hdr = self.addRect(QRectF(sx, sy, sw, sl_hdr_size),
                                   QPen(Qt.NoPen),
                                   QBrush(hex_to_qcolor(colors["swimlane_header"])))
                hdr.setZValue(-2.5)
                txt = self.addText(sl_name, QFont("Segoe UI", font_size, QFont.Bold))
                txt.setDefaultTextColor(hex_to_qcolor(colors["swimlane_header_text"]))
                txt.setPos(sx + sw / 2 - txt.boundingRect().width() / 2, sy + 4)
                txt.setZValue(-2.5)
            else:
                # LR/RL: header bar on the left side, full height
                hdr = self.addRect(QRectF(sx, sy, sl_hdr_size, sh),
                                   QPen(Qt.NoPen),
                                   QBrush(hex_to_qcolor(colors["swimlane_header"])))
                hdr.setZValue(-2.5)
                txt = self.addText(sl_name, QFont("Segoe UI", font_size, QFont.Bold))
                txt.setDefaultTextColor(hex_to_qcolor(colors["swimlane_header_text"]))
                txt.setRotation(90)
                txt.setPos(sx + sl_hdr_size - 4,
                           sy + sh / 2 - txt.boundingRect().width() / 2)
                txt.setZValue(-2.5)

        # Box containers
        for box_label, (bx, by, bw, bh) in layout.get("box_rects", {}).items():
            box_data = next((b for b in parsed["boxes"] if b["label"] == box_label), None)
            bstyle = (box_data.get("style") or {}) if box_data else {}
            bf = hex_to_qcolor(bstyle.get("fill", colors["box_fill"]))
            bs = hex_to_qcolor(bstyle.get("stroke", colors["box_stroke"]))
            rect = self.addRect(QRectF(bx, by, bw, bh),
                                QPen(bs, 1.5), QBrush(bf))
            rect.setZValue(-2)
            txt = self.addText(box_label, QFont("Segoe UI", font_size - 1, QFont.Bold))
            txt.setDefaultTextColor(bs)
            txt.setPos(bx + 6, by + 3)
            txt.setZValue(-2)

        # Groups (dashed overlay)
        for grp in parsed["groups"]:
            gnames = [n for n in grp["object_names"] if n in positions]
            if not gnames:
                continue
            pad = 20
            gx1 = min(positions[n][0] - node_sizes.get(n, (node_w, node_h))[0] / 2 for n in gnames) - pad
            gy1 = min(positions[n][1] - node_sizes.get(n, (node_w, node_h))[1] / 2 for n in gnames) - pad - 16
            gx2 = max(positions[n][0] + node_sizes.get(n, (node_w, node_h))[0] / 2 for n in gnames) + pad
            gy2 = max(positions[n][1] + node_sizes.get(n, (node_w, node_h))[1] / 2 for n in gnames) + pad
            pen = QPen(hex_to_qcolor(colors["phase_line"]), 1.5, Qt.DashLine)
            rect = self.addRect(QRectF(gx1, gy1, gx2 - gx1, gy2 - gy1), pen, QBrush(Qt.NoBrush))
            rect.setZValue(-1)
            txt = self.addText(grp["label"], QFont("Segoe UI", font_size - 2, italic=True))
            txt.setDefaultTextColor(hex_to_qcolor(colors["phase_text"]))
            txt.setPos(gx1 + 4, gy1 + 2)
            txt.setZValue(-1)

        # ── Nodes (created BEFORE edges so edges can reference them) ──
        node_sizes = layout.get("node_sizes", {})
        for obj in parsed["objects"]:
            name = obj["name"]
            if name not in positions:
                continue
            cx, cy = positions[name]
            nw, nh = node_sizes.get(name, (node_w, node_h))
            node = DiagramNode(obj, nw, nh, colors, font_size)
            node.setPos(cx, cy)
            node.setZValue(1)
            self.addItem(node)
            self.scene_nodes[name] = node

        # ── Edges (dynamic DiagramEdge objects tethered to nodes) ──
        self.scene_edges = []
        for conn in parsed["connections"]:
            fn, tn = conn["from_name"], conn["to_name"]
            src_node = self.scene_nodes.get(fn)
            tgt_node = self.scene_nodes.get(tn)
            if not src_node or not tgt_node:
                continue
            edge = DiagramEdge(conn, src_node, tgt_node, colors, font_size,
                               direction=settings.get("direction", "top-to-bottom"))
            self.addItem(edge)
            self.scene_edges.append(edge)
            # Register edge on both nodes so they can trigger updates
            src_node.edges.append(edge)
            tgt_node.edges.append(edge)

        # Notes
        for note in parsed["notes"]:
            target = note["attached_to"]
            if target not in positions:
                continue
            tx, ty = positions[target]
            t_nw, t_nh = node_sizes.get(target, (node_w, node_h))
            nx = tx + t_nw / 2 + 15
            ny = ty - t_nh / 2 - 20
            # Line
            line = self.addLine(QLineF(tx + t_nw / 2, ty - t_nh / 2, nx + 2, ny + 18),
                                QPen(hex_to_qcolor(colors["note_stroke"]), 1, Qt.DashLine))
            line.setZValue(2)
            # Note rect
            note_text = note["text"]
            nw = max(len(note_text) * 7 + 12, 50)
            nh = 24
            nrect = self.addRect(QRectF(nx, ny, nw, nh),
                                 QPen(hex_to_qcolor(colors["note_stroke"]), 1),
                                 QBrush(hex_to_qcolor(colors["note_fill"])))
            nrect.setZValue(2)
            ntxt = self.addText(note_text, QFont("Segoe UI", font_size - 2))
            ntxt.setDefaultTextColor(hex_to_qcolor(colors["note_text"]))
            ntxt.setPos(nx + 4, ny + 2)
            ntxt.setZValue(2)

    # ── Mouse events — behaviour depends on view mode ──
    def _get_transform(self):
        if self.views():
            return self.views()[0].transform()
        from PySide6.QtGui import QTransform
        return QTransform()

    def _current_mode(self):
        if self.views():
            return self.views()[0].mode
        return DiagramView.MODE_SELECT

    def _find_node_at(self, scene_pos, exclude=None):
        """Find a DiagramNode at or near scene_pos.

        Uses a generous search area and walks parent chains so that
        clicking on a label, shadow, or edge still finds the node.
        """
        # First try exact hit
        item = self.itemAt(scene_pos, self._get_transform())
        while item:
            if isinstance(item, DiagramNode) and item is not exclude:
                return item
            item = item.parentItem()

        # Try area search with increasing radius
        for radius in (15, 30, 50):
            area = QRectF(scene_pos.x() - radius, scene_pos.y() - radius,
                          radius * 2, radius * 2)
            for item in self.items(area):
                if isinstance(item, DiagramNode) and item is not exclude:
                    return item
        return None

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        mode = self._current_mode()

        if mode == DiagramView.MODE_CONNECT:
            node = self._find_node_at(event.scenePos())
            if node:
                self._drag_source_node = node
                best_port = node.best_port_to(event.scenePos())
                port_scene = node.port_pos(best_port) if best_port else event.scenePos()
                pen = QPen(QColor("#89b4fa"), 2.5, Qt.DashLine)
                self._rubber_line = self.addLine(
                    QLineF(port_scene, event.scenePos()), pen)
                self._rubber_line.setZValue(10)
                event.accept()
                return
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._rubber_line and self._drag_source_node:
            line = self._rubber_line.line()
            self._rubber_line.setLine(QLineF(line.p1(), event.scenePos()))

            # Highlight the target node if hovering over one
            target = self._find_node_at(event.scenePos(), exclude=self._drag_source_node)
            for node in self.scene_nodes.values():
                if node is target:
                    node._hovered = True
                elif node is not self._drag_source_node:
                    node._hovered = False
                node.update()

            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._rubber_line and self._drag_source_node:
            target = self._find_node_at(event.scenePos(), exclude=self._drag_source_node)
            if target:
                self.connection_created.emit(
                    self._drag_source_node.obj["name"],
                    target.obj["name"],
                )
            # Clean up rubber band and hover state
            self.removeItem(self._rubber_line)
            self._rubber_line = None
            self._drag_source_node = None
            for node in self.scene_nodes.values():
                node._hovered = False
                node.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)


# ═══════════════════════════════════════════════
#  DiagramView (QGraphicsView)
# ═══════════════════════════════════════════════

class DiagramView(QGraphicsView):
    zoom_changed = Signal(float)
    # Interaction modes
    MODE_SELECT = "select"    # Click to select, drag to move nodes
    MODE_PAN = "pan"          # Drag to pan the canvas
    MODE_CONNECT = "connect"  # Click source port, drag to target port

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.zoom_level = 1.0
        self._mode = self.MODE_SELECT
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)  # default: select
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    def set_mode(self, mode):
        self._mode = mode
        if mode == self.MODE_PAN:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.OpenHandCursor)
        elif mode == self.MODE_SELECT:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setCursor(Qt.ArrowCursor)
        elif mode == self.MODE_CONNECT:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)

    @property
    def mode(self):
        return self._mode

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            new_zoom = self.zoom_level * factor
            new_zoom = max(0.1, min(5.0, new_zoom))
            scale_factor = new_zoom / self.zoom_level
            self.scale(scale_factor, scale_factor)
            self.zoom_level = new_zoom
            self.zoom_changed.emit(self.zoom_level)
        else:
            super().wheelEvent(event)

    def mouseDoubleClickEvent(self, event):
        if not self.scene().itemAt(self.mapToScene(event.pos()), self.transform()):
            self.fit_to_content()
        else:
            super().mouseDoubleClickEvent(event)

    def fit_to_content(self):
        rect = self.scene().itemsBoundingRect().adjusted(-40, -40, 40, 40)
        if rect.isEmpty():
            return
        self.fitInView(rect, Qt.KeepAspectRatio)
        # Calculate actual zoom from the transform
        t = self.transform()
        self.zoom_level = t.m11()
        self.zoom_changed.emit(self.zoom_level)

    def reset_zoom(self):
        self.resetTransform()
        self.zoom_level = 1.0
        self.zoom_changed.emit(1.0)


# ═══════════════════════════════════════════════
#  Syntax Highlighter
# ═══════════════════════════════════════════════

class DiagramHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []

        # Build formats
        def fmt(color, bold=False, italic=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Bold)
            if italic:
                f.setFontItalic(True)
            return f

        comment_fmt = fmt("#6c7086", italic=True)
        keyword_fmt = fmt("#cba6f7", bold=True)
        shape_fmt = fmt("#89b4fa", bold=True)
        string_fmt = fmt("#a6e3a1")
        operator_fmt = fmt("#fab387")
        step_fmt = fmt("#94e2d5", bold=True)
        attr_key_fmt = fmt("#94e2d5")
        attr_val_fmt = fmt("#94e2d5", italic=True)
        style_fmt = fmt("#94e2d5")
        hint_fmt = fmt("#94e2d5")
        name_fmt = fmt("#f9e2af")

        self._rules = [
            (re.compile(r'//.*$'), comment_fmt),
            (re.compile(r'\b(swimlane|group|note|direction|box|setting)\b'), keyword_fmt),
            (re.compile(r'\b(top-to-bottom|left-to-right|bottom-to-top|right-to-left)\b'), step_fmt),
            (re.compile(r'\[(rect|rounded|diamond|circle|parallelogram|hexagon|cylinder|stadium)\]'), shape_fmt),
            (re.compile(r'"[^"]*"'), string_fmt),
            (re.compile(r'(==>|-->|->|---|-\.-)'), operator_fmt),
            (re.compile(r'step:\d+'), step_fmt),
            (re.compile(r'\b(type|owner|status|tags|priority|id|condition|weight):'), attr_key_fmt),
            (re.compile(r'\{[^}]*\}'), style_fmt),
            (re.compile(r'@\(\d+,\s*\d+\)'), style_fmt),
            (re.compile(r'\[(above|below|center)\]'), hint_fmt),
        ]

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ═══════════════════════════════════════════════
#  Code Editor with Line Numbers
# ═══════════════════════════════════════════════

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSizeF(self.editor.line_number_width(), 0).toSize()

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_area = LineNumberArea(self)
        self._error_lines = set()

        mono = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono.setPointSize(11)
        self.setFont(mono)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 2)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.blockCountChanged.connect(self._update_line_area_width)
        self.updateRequest.connect(self._update_line_area)
        self._update_line_area_width()

    def set_error_lines(self, lines):
        self._error_lines = set(lines)
        self._line_area.update()

    def line_number_width(self):
        digits = max(1, len(str(self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_area_width(self):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def _update_line_area(self, rect, dy):
        if dy:
            self._line_area.scroll(0, dy)
        else:
            self._line_area.update(0, rect.y(), self._line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_area_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_area.setGeometry(cr.left(), cr.top(),
                                     self.line_number_width(), cr.height())

    def paint_line_numbers(self, event):
        painter = QPainter(self._line_area)
        painter.fillRect(event.rect(), QColor("#181825"))

        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = block_num + 1
                if number in self._error_lines:
                    painter.fillRect(0, top, self._line_area.width(),
                                     int(self.blockBoundingRect(block).height()),
                                     QColor("#e64553"))
                    painter.setPen(QColor("#ffffff"))
                else:
                    painter.setPen(QColor("#585b70"))
                painter.drawText(0, top, self._line_area.width() - 4,
                                 int(self.blockBoundingRect(block).height()),
                                 Qt.AlignRight | Qt.AlignVCenter, str(number))

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_num += 1

        painter.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            self.insertPlainText("  ")
            return
        super().keyPressEvent(event)


# ═══════════════════════════════════════════════
#  Filter Engine
# ═══════════════════════════════════════════════

def parse_filter_query(query):
    """Parse 'type:decision owner:alice free_text' into filter terms."""
    terms = []
    # Match key:value or key:"value" pairs
    for m in re.finditer(r'(\w+):((?:"[^"]*"|\S+))', query):
        key = m.group(1)
        val = m.group(2).strip('"')
        terms.append(("attr", key, val))

    # Remaining free text (after removing key:value pairs)
    remaining = re.sub(r'\w+:(?:"[^"]*"|\S+)', '', query).strip()
    if remaining:
        for word in remaining.split():
            terms.append(("freetext", None, word))
    return terms


def object_matches_filter(obj, terms):
    """Return True if the object matches ALL filter terms."""
    for ttype, key, val in terms:
        if ttype == "attr":
            vals = [v.strip() for v in val.split(",")]
            if key == "tags":
                if not any(v in obj.get("tags", []) for v in vals):
                    return False
            elif key == "step":
                if str(obj.get("step")) not in vals:
                    return False
            elif key == "swimlane":
                if (obj.get("swimlane") or "") not in vals:
                    return False
            else:
                obj_val = str(obj.get(key, obj.get("extra_attrs", {}).get(key, "")))
                if not any(v.lower() in obj_val.lower() for v in vals):
                    return False
        elif ttype == "freetext":
            # Search across name, label, owner, tags, type, all attrs
            searchable = " ".join([
                obj.get("name", ""), obj.get("label", ""),
                obj.get("owner", "") or "", obj.get("type", "") or "",
                " ".join(obj.get("tags", [])),
                obj.get("status", "") or "", obj.get("priority", "") or "",
            ] + list(obj.get("extra_attrs", {}).values()))
            if val.lower() not in searchable.lower():
                return False
    return True


# ═══════════════════════════════════════════════
#  PDF Exporter
# ═══════════════════════════════════════════════

class PDFExporter:
    @staticmethod
    def export(parsed, filepath, settings=None):
        """Export the diagram to PDF using the same layout engine as the
        scene renderer.  Uses per-node sizes so shapes match the screen.
        """
        settings = settings or {}
        base_w = settings.get("node_width", 140)
        base_h = settings.get("node_height", 50)
        font_size = settings.get("font_size", 11)
        scheme = settings.get("color_scheme", "Default")
        colors = COLOR_SCHEMES.get(scheme, DEFAULT_COLORS)

        layout = compute_layout(parsed, settings)
        positions = layout.get("positions", {})
        node_sizes = layout.get("node_sizes", {})
        if not positions:
            return False

        # Compute diagram bounds from ALL positioned objects with their
        # actual sizes, plus swimlane rects, plus margin.
        margin = 50
        xs, ys = [], []
        for name, (px, py) in positions.items():
            nw, nh = node_sizes.get(name, (base_w, base_h))
            xs += [px - nw / 2, px + nw / 2]
            ys += [py - nh / 2, py + nh / 2]
        for _, (sx, sy, sw_r, sh_r) in layout.get("swimlane_rects", {}).items():
            xs += [sx, sx + sw_r]
            ys += [sy, sy + sh_r]
        mn_x = min(xs) - margin
        mn_y = min(ys) - margin
        mx_x = max(xs) + margin
        mx_y = max(ys) + margin

        dw = max(mx_x - mn_x, 1)
        dh = max(mx_y - mn_y, 1)
        landscape = dw > dh
        pdf = FPDF(orientation="L" if landscape else "P", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_auto_page_break(auto=False)

        pw, ph = pdf.w - 20, pdf.h - 20
        sc = min(pw / dw, ph / dh)

        def tx(x): return 10 + (x - mn_x) * sc
        def ty(y): return 10 + (y - mn_y) * sc
        def s(v): return v * sc

        def set_fill(h):
            r, g, b = hex_to_rgb(h)
            pdf.set_fill_color(r, g, b)
        def set_draw(h):
            r, g, b = hex_to_rgb(h)
            pdf.set_draw_color(r, g, b)
        def set_text_c(h):
            r, g, b = hex_to_rgb(h)
            pdf.set_text_color(r, g, b)

        def centered_text(cx_mm, cy_mm, text, w_mm):
            """Draw text centered at (cx_mm, cy_mm) within w_mm width."""
            lbl = text.replace("\n", " ")
            tw = pdf.get_string_width(lbl)
            fh = pdf.font_size * 1.2
            pdf.set_xy(cx_mm - tw / 2, cy_mm - fh / 2)
            pdf.cell(tw, fh, lbl)

        sl_hdr = 36

        # ── Step bands ──
        for entry in layout.get("step_bands", []):
            step, y0, y1 = entry[0], entry[1], entry[2]
            band_color = colors["step_band_odd"] if step % 2 else colors["step_band_even"]
            set_fill(band_color)
            pdf.rect(tx(mn_x), ty(y0), s(dw), s(y1 - y0), "F")
            set_text_c(colors["phase_text"])
            pdf.set_font("Helvetica", "B", max(5, font_size * sc * 0.5))
            pdf.set_xy(tx(mn_x) + 1, ty(y0) + 0.5)
            pdf.cell(8, s(12), str(step))

        # ── Swimlanes ──
        for sl_name, (sx, sy, sw_r, sh_r) in layout.get("swimlane_rects", {}).items():
            set_fill(colors["swimlane_fill"])
            set_draw(colors["swimlane_stroke"])
            pdf.set_line_width(0.3 * sc)
            pdf.rect(tx(sx), ty(sy), s(sw_r), s(sh_r), "DF")
            # Header
            set_fill(colors["swimlane_header"])
            pdf.rect(tx(sx), ty(sy), s(sw_r), s(sl_hdr), "F")
            set_text_c(colors["swimlane_header_text"])
            pdf.set_font("Helvetica", "B", max(6, font_size * sc * 0.85))
            pdf.set_xy(tx(sx), ty(sy))
            pdf.cell(s(sw_r), s(sl_hdr), sl_name, align="C")

        # ── Boxes ──
        for blabel, (bx, by, bw, bh) in layout.get("box_rects", {}).items():
            bdata = next((b for b in parsed["boxes"] if b["label"] == blabel), None)
            bst = (bdata.get("style") or {}) if bdata else {}
            set_fill(bst.get("fill", colors["box_fill"]))
            set_draw(bst.get("stroke", colors["box_stroke"]))
            pdf.set_line_width(0.3 * sc)
            pdf.rect(tx(bx), ty(by), s(bw), s(bh), "DF")
            set_text_c(bst.get("stroke", colors["box_stroke"]))
            pdf.set_font("Helvetica", "B", max(5, font_size * sc * 0.6))
            pdf.set_xy(tx(bx) + 1, ty(by) + 0.5)
            pdf.cell(s(bw) - 2, s(20), blabel)

        # ── Groups ──
        for grp in parsed["groups"]:
            gnames = [n for n in grp["object_names"] if n in positions]
            if not gnames:
                continue
            pad = 25
            gx1 = min(positions[n][0] - node_sizes.get(n, (base_w, base_h))[0] / 2 for n in gnames) - pad
            gy1 = min(positions[n][1] - node_sizes.get(n, (base_w, base_h))[1] / 2 for n in gnames) - pad - 16
            gx2 = max(positions[n][0] + node_sizes.get(n, (base_w, base_h))[0] / 2 for n in gnames) + pad
            gy2 = max(positions[n][1] + node_sizes.get(n, (base_w, base_h))[1] / 2 for n in gnames) + pad
            set_draw(colors["phase_line"])
            pdf.set_line_width(0.2 * sc)
            for ax, ay, bxx, byy in [
                (gx1, gy1, gx2, gy1), (gx2, gy1, gx2, gy2),
                (gx2, gy2, gx1, gy2), (gx1, gy2, gx1, gy1),
            ]:
                pdf.dashed_line(tx(ax), ty(ay), tx(bxx), ty(byy), 1.5 * sc, 0.8 * sc)
            set_text_c(colors["phase_text"])
            pdf.set_font("Helvetica", "I", max(5, font_size * sc * 0.55))
            pdf.set_xy(tx(gx1) + 1, ty(gy1) + 0.5)
            pdf.cell(s(gx2 - gx1) - 2, s(12), grp["label"])

        # ── Edges (with per-node clipping) ──
        def clip(cx, cy, ttx, tty, hw, hh):
            dx, dy = ttx - cx, tty - cy
            if abs(dx) < 0.01 and abs(dy) < 0.01:
                return cx, cy - hh
            if abs(dx) < 0.01:
                return cx, cy + (hh if dy > 0 else -hh)
            if abs(dy) < 0.01:
                return cx + (hw if dx > 0 else -hw), cy
            return cx + dx * min(hw / abs(dx), hh / abs(dy)), \
                   cy + dy * min(hw / abs(dx), hh / abs(dy))

        for conn in parsed["connections"]:
            fn, tn = conn["from_name"], conn["to_name"]
            if fn not in positions or tn not in positions:
                continue

            set_draw(colors["edge_stroke"])
            etype = conn["type"]
            weight = conn.get("weight") or 0
            lw = (0.4 + min(weight, 5) * 0.12) * sc
            if etype == "thick":
                lw = max(lw, 0.8 * sc)
            pdf.set_line_width(lw)

            x1, y1 = positions[fn]
            x2, y2 = positions[tn]
            nw1, nh1 = node_sizes.get(fn, (base_w, base_h))

            # Self-loop
            if fn == tn:
                loop_r = 28
                # Draw a small arc to the right of the node
                arc_cx = tx(x1 + nw1 / 2 + loop_r * 0.7)
                arc_cy = ty(y1)
                arc_r = s(loop_r * 0.8)
                pdf.ellipse(arc_cx - arc_r, arc_cy - arc_r, arc_r * 2, arc_r * 2, "D")
                if conn["label"]:
                    set_text_c(colors["edge_label"])
                    pdf.set_font("Helvetica", "", max(5, font_size * sc * 0.65))
                    pdf.set_xy(arc_cx + arc_r + 1, arc_cy - pdf.font_size * 0.6)
                    pdf.cell(0, pdf.font_size * 1.2, conn["label"])
                continue

            nw2, nh2 = node_sizes.get(tn, (base_w, base_h))
            sx_e, sy_e = clip(x1, y1, x2, y2, nw1 / 2, nh1 / 2)
            ex_e, ey_e = clip(x2, y2, x1, y1, nw2 / 2, nh2 / 2)

            if etype == "dashed":
                pdf.dashed_line(tx(sx_e), ty(sy_e), tx(ex_e), ty(ey_e), 2 * sc, 1 * sc)
            elif etype in ("dotted_line", "dotted_arrow"):
                pdf.dashed_line(tx(sx_e), ty(sy_e), tx(ex_e), ty(ey_e), 0.8 * sc, 0.8 * sc)
            else:
                pdf.line(tx(sx_e), ty(sy_e), tx(ex_e), ty(ey_e))

            if conn["arrow"]:
                angle = math.atan2(ey_e - sy_e, ex_e - sx_e)
                ah = 2.5 * sc
                a1 = angle + math.pi * 0.83
                a2 = angle - math.pi * 0.83
                pts = [{"x": tx(ex_e), "y": ty(ey_e)},
                       {"x": tx(ex_e) + ah * math.cos(a1), "y": ty(ey_e) + ah * math.sin(a1)},
                       {"x": tx(ex_e) + ah * math.cos(a2), "y": ty(ey_e) + ah * math.sin(a2)}]
                set_fill(colors["edge_stroke"])
                try:
                    pdf.polygon(pts, style="F")
                except Exception:
                    pass

            # Edge label — centered on midpoint
            if conn["label"]:
                emx = (tx(sx_e) + tx(ex_e)) / 2
                emy = (ty(sy_e) + ty(ey_e)) / 2
                set_text_c(colors["edge_label"])
                pdf.set_font("Helvetica", "", max(5, font_size * sc * 0.65))
                etw = pdf.get_string_width(conn["label"])
                fh = pdf.font_size * 1.2
                set_fill(colors["canvas_bg"])
                pdf.rect(emx - etw / 2 - 1, emy - fh / 2 - 0.5, etw + 2, fh + 1, "F")
                set_text_c(colors["edge_label"])
                pdf.set_xy(emx - etw / 2, emy - fh / 2)
                pdf.cell(etw, fh, conn["label"])

        # ── Nodes (per-node sizes, proper shapes) ──
        for obj in parsed["objects"]:
            name = obj["name"]
            if name not in positions:
                continue
            cx, cy = positions[name]
            nw, nh = node_sizes.get(name, (base_w, base_h))
            x, y = tx(cx), ty(cy)
            w, h = s(nw), s(nh)
            ns = obj.get("style") or {}
            set_fill(ns.get("fill", colors["node_fill"]))
            set_draw(ns.get("stroke", colors["node_stroke"]))
            pdf.set_line_width(0.3 * sc)

            shape = obj["shape"]
            if shape in ("rounded", "stadium"):
                pdf.rect(x - w / 2, y - h / 2, w, h, "DF")
            elif shape == "diamond":
                pts = [{"x": x, "y": y - h / 2}, {"x": x + w / 2, "y": y},
                       {"x": x, "y": y + h / 2}, {"x": x - w / 2, "y": y}]
                try:
                    pdf.polygon(pts, style="DF")
                except Exception:
                    pdf.rect(x - w / 2, y - h / 2, w, h, "DF")
            elif shape == "circle":
                r = max(w, h) / 2
                pdf.ellipse(x - r, y - r, r * 2, r * 2, "DF")
            elif shape == "parallelogram":
                sk = 5 * sc
                pts = [{"x": x - w / 2 + sk, "y": y - h / 2},
                       {"x": x + w / 2, "y": y - h / 2},
                       {"x": x + w / 2 - sk, "y": y + h / 2},
                       {"x": x - w / 2, "y": y + h / 2}]
                try:
                    pdf.polygon(pts, style="DF")
                except Exception:
                    pdf.rect(x - w / 2, y - h / 2, w, h, "DF")
            elif shape == "hexagon":
                hx_s = 6 * sc
                pts = [{"x": x - w / 2 + hx_s, "y": y - h / 2},
                       {"x": x + w / 2 - hx_s, "y": y - h / 2},
                       {"x": x + w / 2, "y": y},
                       {"x": x + w / 2 - hx_s, "y": y + h / 2},
                       {"x": x - w / 2 + hx_s, "y": y + h / 2},
                       {"x": x - w / 2, "y": y}]
                try:
                    pdf.polygon(pts, style="DF")
                except Exception:
                    pdf.rect(x - w / 2, y - h / 2, w, h, "DF")
            elif shape == "cylinder":
                ry_p = 2.5 * sc
                pdf.rect(x - w / 2, y - h / 2 + ry_p, w, h - 2 * ry_p, "DF")
                pdf.ellipse(x - w / 2, y - h / 2, w, ry_p * 2, "DF")
                pdf.ellipse(x - w / 2, y + h / 2 - ry_p * 2, w, ry_p * 2, "DF")
            else:
                pdf.rect(x - w / 2, y - h / 2, w, h, "DF")

            # Label — centered in shape
            set_text_c(ns.get("text", colors["node_text"]))
            pdf.set_font("Helvetica", "", max(5, font_size * sc * 0.8))
            lbl = obj["label"].replace("\n", " ")
            centered_text(x, y, lbl, w)

        # ── Notes ──
        for note in parsed["notes"]:
            target = note["attached_to"]
            if target not in positions:
                continue
            ttx, tty = positions[target]
            tnw, tnh = node_sizes.get(target, (base_w, base_h))
            nx = tx(ttx + tnw / 2 + 15)
            ny = ty(tty - tnh / 2 - 15)
            set_fill(colors["note_fill"])
            set_draw(colors["note_stroke"])
            pdf.set_line_width(0.15 * sc)
            pdf.set_font("Helvetica", "", max(4, font_size * sc * 0.55))
            nw_mm = max(pdf.get_string_width(note["text"]) + 3, 12)
            nh_mm = 4 * sc
            pdf.rect(nx, ny, nw_mm, nh_mm, "DF")
            set_text_c(colors["note_text"])
            pdf.set_xy(nx + 0.5, ny + 0.5 * sc)
            pdf.cell(nw_mm - 1, 2.5 * sc, note["text"])
            set_draw(colors["note_stroke"])
            pdf.set_line_width(0.1 * sc)
            pdf.line(tx(ttx + tnw / 2), ty(tty - tnh / 2), nx + 1, ny + nh_mm)

        pdf.output(filepath)
        return True


# ═══════════════════════════════════════════════
#  Example Code & Help
# ═══════════════════════════════════════════════

EXAMPLE_CODE = r"""// Settings (these sync with the settings panel)
direction top-to-bottom
setting node_width 140
setting node_height 50
setting h_gap 60
setting v_gap 70

// === Swimlanes contain objects ===
swimlane "Product Team" {
    [rounded] gather_reqs "Gather\nRequirements" step:1 type:process owner:"alice" status:active tags:"mvp, sprint-1"
    [diamond] feasibility "Feasibility Review" step:2 type:decision owner:"bob" priority:high
    [rounded] revise "Revise Scope" step:2 type:process owner:"alice" status:draft
}

swimlane "Engineering" {
    [rect] sys_design "System Design" step:3 type:process owner:"charlie" tags:"architecture" {fill: #e3f2fd, stroke: #1565c0}
    [rect] implement "Implementation" step:4 type:automated owner:"dev-team" priority:high
    [hexagon] testing "Run Tests" step:5 type:automated owner:"qa-team" status:active tags:"ci, blocking"
}

swimlane "Operations" {
    [parallelogram] staging "Deploy to Staging" step:6 type:process owner:"devops"
    [diamond] qa_check "QA Approval?" step:7 type:approval owner:"qa-lead" priority:critical
    [stadium] release "Release to Prod" step:8 type:process status:active
    [cylinder] update_db "Update Database" step:8 type:datastore owner:"dba-team"
}

// Standalone objects
[circle] start "Start" step:0 type:start
[circle] done "Done" step:9 type:end

// === Connections ===
start -> gather_reqs : "kick off"
gather_reqs -> feasibility
feasibility -> sys_design : "approved" [center] condition:"feasible == true"
feasibility --> revise : "needs work"
revise -> feasibility
sys_design -> implement
implement ==> testing : "critical path" weight:10
testing -> staging
staging -> qa_check
qa_check -> release : "pass"
qa_check -.- implement : "fail: rework"
release -> update_db
update_db -> done
implement -> implement : "iterate"

// === Group ===
group "Sprint 1" {
    gather_reqs
    feasibility
    revise
}

// === Notes ===
note "Critical bottleneck here" [testing]
"""

HELP_TEXT = """\
═══════════════════════════════════════════════
         DIAGRAM EDITOR — SYNTAX REFERENCE
═══════════════════════════════════════════════

OBJECTS
───────
  [shape] name "Label" step:N [attributes...] [{style}] [@(x,y)]

  Shapes: rect, rounded, diamond, circle,
          parallelogram, hexagon, cylinder, stadium

  Example:
    [rect] my_task "Do Something" step:3 type:process owner:"alice"
    [diamond] decision "OK?" step:4 type:decision priority:high
    [rect] styled "Custom" step:5 {fill: #ff0000, stroke: #000}

ATTRIBUTES (all optional, on objects)
─────────────────────────────────────
  step:N          Timeline position (required, N >= 0)
  type:           process|decision|input|output|datastore|start|end|
                  manual|automated|approval|external (or custom)
  owner:"name"    Responsibility
  status:         draft|active|deprecated|blocked|complete
  tags:"a, b"     Comma-separated labels
  priority:       low|medium|high|critical
  id:N            External reference number

  Unknown keys are stored without error (extensible).

CONNECTIONS
───────────
  A -> B               Solid arrow
  A --> B              Dashed arrow
  A ==> B              Thick arrow
  A --- B              Solid line
  A -.- B              Dotted line
  A -> B : "label"     With label
  A -> B : "lbl" [center]   Label placement: above|below|center
  A -> B condition:"expr"   Condition (shown in tooltip)
  A -> B weight:5            Visual emphasis

SWIMLANES
─────────
  swimlane "Name" {
      [rect] child "Child" step:1
  }

BOXES (inside swimlanes, sub-grouping)
──────────────────────────────────────
  box "Label" {fill: #hex, stroke: #hex} {
      [rect] a "A" step:1
  }

GROUPS (visual overlay, reference names)
────────────────────────────────────────
  group "Label" {
      name1
      name2
  }

DIRECTION
─────────
  direction top-to-bottom    (default)
  direction left-to-right
  direction bottom-to-top
  direction right-to-left

  Shorthand also accepted: TB, LR, BT, RL

NOTES
─────
  note "Text" [object_name]

SETTINGS (in code — syncs with settings panel)
───────────────────────────────────────────────
  setting node_width 160
  setting node_height 60
  setting h_gap 80
  setting v_gap 90
  setting font_size 12
  setting container_padding 25
  setting swimlane_gap 15
  setting color_scheme Dark

  Changing a setting in code updates the panel.
  Changing the panel updates the code.

FILTER (toolbar field)
──────────────────────
  type:decision          Match by attribute
  owner:alice            Match owner
  tags:mvp               Match tag
  status:blocked         Match status
  step:5                 Match step number
  alice                  Free text search
  type:decision,process  OR within attribute
  type:decision owner:x  AND across attributes

KEYBOARD SHORTCUTS
──────────────────
  Ctrl+N          New
  Ctrl+O          Open
  Ctrl+S          Save
  Ctrl+Shift+S    Save As
  Ctrl+P          Export PDF
  Ctrl+E          Export SVG
  Ctrl+Shift+E    Export PNG
  Ctrl+Shift+C    Copy diagram to clipboard
  Ctrl+F          Find
  Ctrl+H          Find & Replace
  Ctrl+/          Focus filter
  Ctrl+=          Zoom in
  Ctrl+-          Zoom out
  Ctrl+0          Zoom to fit
  Ctrl+1          Actual size
  Ctrl+Z          Undo
  Ctrl+Shift+Z    Redo
  F1              Syntax help
  Escape          Close find/clear filter
  Ctrl+Q          Quit
"""

LLM_PROMPT = """\
You are generating diagram code for a step-based visual diagram editor. Follow these rules exactly.

═══════════════════════════════════════════════
 OUTPUT FORMAT
═══════════════════════════════════════════════

Output ONLY the diagram code. No markdown fences, no explanation, no commentary before or after. The output is pasted directly into the editor.

═══════════════════════════════════════════════
 OBJECTS (nodes in the diagram)
═══════════════════════════════════════════════

Syntax:
  [shape] unique_name "Display Label" step:N key:value key:"value with spaces"

Rules:
- shape is one of: rect, rounded, diamond, circle, parallelogram, hexagon, cylinder, stadium
- unique_name must be a valid identifier: letters, digits, underscores. Must be unique across the entire diagram.
- "Display Label" is the text shown inside the shape. Use \\n for line breaks.
- step:N is REQUIRED. N is a non-negative integer. Objects with the same step number are placed in the same horizontal row (parallel). Lower steps are higher on the diagram.
- Steps do not need to be contiguous (you can use step:0, step:5, step:10).

Standard shape meanings (follow these conventions):
  rect           Process / activity / task (general-purpose)
  rounded        Sub-process / alternate task
  diamond        Decision / gateway (yes/no branch point)
  circle         Start or end event (terminator)
  parallelogram  Data input or output
  hexagon        Preparation / setup step
  cylinder       Database / data store
  stadium        Terminal / external process boundary

═══════════════════════════════════════════════
 ATTRIBUTES (optional, on objects)
═══════════════════════════════════════════════

All attributes are optional key:value pairs after step:N. Order does not matter. Quote values that contain spaces or commas.

  type:process        Semantic type. Values: process, decision, input, output, datastore, start, end, manual, automated, approval, external (or any custom string)
  owner:"person"      Who is responsible for this step
  status:active       Lifecycle state: draft, active, deprecated, blocked, complete
  tags:"mvp, v2"      Comma-separated freeform labels
  priority:high       Importance: low, medium, high, critical
  id:42               External reference number

Status affects rendering:
  draft       → dashed border
  blocked     → red border
  deprecated  → transparent with strikethrough
  complete    → checkmark indicator

Priority affects rendering:
  critical    → thick red-tinted border
  high        → slightly thicker border
  low         → thinner border, muted fill

Unknown attribute keys are accepted and stored (the system is extensible). You can add any key:value pair.

═══════════════════════════════════════════════
 STYLE OVERRIDES (optional, on objects)
═══════════════════════════════════════════════

After all attributes, you can add {fill: #hex, stroke: #hex, text: #hex} to override colors:

  [rect] my_node "Highlighted" step:3 type:process {fill: #a6e3a1, stroke: #2d6a2d}

═══════════════════════════════════════════════
 SWIMLANES (containers for objects)
═══════════════════════════════════════════════

Syntax:
  swimlane "Lane Name" {
      [shape] name "Label" step:N ...
      [shape] name2 "Label2" step:M ...
  }

- Swimlanes are vertical columns. Objects inside a swimlane are placed in that column.
- Swimlanes are laid out left to right in declaration order.
- Objects outside any swimlane go in a separate "free" column.
- Connections between objects in different swimlanes work normally — just reference the names.
- Indent children by 4 spaces (convention, not required).

═══════════════════════════════════════════════
 BOXES (sub-containers inside swimlanes)
═══════════════════════════════════════════════

Syntax:
  box "Box Label" {fill: #hex, stroke: #hex} {
      [shape] name "Label" step:N ...
  }

- Boxes live inside swimlanes or at the top level.
- They visually group children with a colored rounded rectangle and a header.
- Use them for sub-grouping (e.g. "Automated Tests", "Manual Review").

═══════════════════════════════════════════════
 CONNECTIONS (edges between objects)
═══════════════════════════════════════════════

Syntax:
  source_name -> target_name                    Solid arrow (sequence flow)
  source_name --> target_name                   Dashed arrow (message/conditional flow)
  source_name ==> target_name                   Thick arrow (critical path)
  source_name --- target_name                   Solid line, no arrow (association)
  source_name -.- target_name                   Dotted line, no arrow (dependency)

Optional label:
  source -> target : "label text"

Optional label placement hint:
  source -> target : "label" [above]
  source -> target : "label" [below]
  source -> target : "label" [center]

Optional connection attributes (after label):
  source -> target : "approved" condition:"status == ok"
  source -> target : "critical" weight:10

- weight:N makes the line thicker (visual emphasis).
- condition:"expr" stores metadata shown in tooltip on hover.
- Self-loops are supported: name -> name : "retry"
- Connections are written OUTSIDE swimlane blocks, at the top level.

═══════════════════════════════════════════════
 GROUPS (visual overlay, not a container)
═══════════════════════════════════════════════

Syntax:
  group "Group Label" {
      object_name_1
      object_name_2
  }

- Groups draw a dashed border around the referenced objects.
- They do NOT own or contain objects — they are a visual annotation.
- Group members are referenced by name (must already be defined).
- Groups can span multiple swimlanes.

═══════════════════════════════════════════════
 NOTES (annotations attached to objects)
═══════════════════════════════════════════════

Syntax:
  note "Annotation text" [object_name]

- Draws a small yellow note box connected to the target object.
- The object must exist (referenced by name).

═══════════════════════════════════════════════
 DIRECTION
═══════════════════════════════════════════════

Syntax:
  direction top-to-bottom

Values: top-to-bottom (default), left-to-right, bottom-to-top, right-to-left
Shorthand also accepted: TB, LR, BT, RL

═══════════════════════════════════════════════
 COMMENTS
═══════════════════════════════════════════════

  // This is a comment (ignored by the parser)

Use comments to organize sections of the diagram.

═══════════════════════════════════════════════
 POSITION PINS (optional)
═══════════════════════════════════════════════

  [rect] name "Label" step:N @(350, 200)

- Pins an object to an exact pixel position (overrides auto-layout).
- Written automatically when a user drags a node. You rarely need to write these manually.

═══════════════════════════════════════════════
 COMPLETE EXAMPLE
═══════════════════════════════════════════════

direction top-to-bottom

// Swimlanes define organizational columns
swimlane "Customer" {
    [circle] request "Submit\\nRequest" step:0 type:start
    [diamond] satisfied "Satisfied?" step:4 type:decision
    [circle] done "Done" step:5 type:end
}

swimlane "Support Team" {
    [rect] triage "Triage Issue" step:1 type:process owner:"support-lead" priority:high
    [diamond] escalate "Needs\\nEscalation?" step:2 type:decision
    [rect] resolve "Resolve Issue" step:3 type:process owner:"support-agent" status:active
}

swimlane "Engineering" {
    [rect] investigate "Investigate Bug" step:2 type:process owner:"dev-team" tags:"bugs"
    [hexagon] fix "Develop Fix" step:3 type:process owner:"dev-team"
    [cylinder] deploy "Deploy Patch" step:4 type:process owner:"devops" {fill: #a6e3a1, stroke: #2d6a2d}
}

// Connections (at top level, reference names freely across swimlanes)
request -> triage : "new ticket"
triage -> escalate
escalate -> resolve : "no"
escalate -> investigate : "yes"
investigate -> fix
fix -> deploy
deploy -> satisfied
resolve -> satisfied
satisfied -> done : "yes"
satisfied --> triage : "no, reopen"

// Group for visual emphasis
group "Engineering Pipeline" {
    investigate
    fix
    deploy
}

// Annotation
note "SLA: 24h response" [triage]

═══════════════════════════════════════════════
 STRUCTURAL RULES
═══════════════════════════════════════════════

1. Every object MUST have a unique name and a step:N.
2. Connections reference objects by name. Both endpoints must exist.
3. Objects inside swimlane { } blocks belong to that swimlane.
4. Connections are written OUTSIDE swimlane blocks.
5. Groups reference existing names — they don't create objects.
6. Notes reference an existing object name in [brackets].
7. Same step number = same row = parallel placement.
8. Lower step numbers are placed higher (top of diagram).
9. Use shapes that match their conventional meaning (diamond for decisions, cylinder for databases, etc.).
10. Keep names short, lowercase, with underscores: gather_reqs, qa_check, update_db.
"""

STYLESHEET = """
QMainWindow, QWidget { background: #1e1e2e; color: #cdd6f4;
    font-family: 'Segoe UI','SF Pro Display','Ubuntu',sans-serif; font-size: 10pt; }
QMenuBar { background: #181825; color: #cdd6f4; border-bottom: 1px solid #313244; }
QMenuBar::item:selected { background: #313244; }
QMenu { background: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; }
QMenu::item:selected { background: #45475a; }
QMenu::separator { height: 1px; background: #313244; margin: 4px 8px; }
QToolBar { background: #181825; border-bottom: 1px solid #313244; spacing: 4px; padding: 4px; }
QToolButton { background: #313244; color: #cdd6f4; border: none;
    border-radius: 4px; padding: 6px 12px; font-weight: bold; }
QToolButton:hover { background: #45475a; }
QToolButton:pressed { background: #585b70; }
QSplitter::handle { background: #313244; }
QSplitter::handle:horizontal { width: 4px; }
QSplitter::handle:vertical { height: 4px; }
QSplitter::handle:hover { background: #89b4fa; }
QPlainTextEdit { background: #1e1e2e; color: #cdd6f4;
    selection-background-color: #45475a; border: none; }
QDockWidget { color: #89b4fa; font-weight: bold; }
QDockWidget::title { background: #181825; padding: 6px; border-bottom: 1px solid #313244; }
QSlider::groove:horizontal { height: 4px; background: #313244; border-radius: 2px; }
QSlider::handle:horizontal { background: #89b4fa; width: 14px; height: 14px;
    margin: -5px 0; border-radius: 7px; }
QSlider::handle:horizontal:hover { background: #74c7ec; }
QComboBox { background: #313244; color: #cdd6f4; border: 1px solid #45475a;
    border-radius: 4px; padding: 4px 8px; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background: #1e1e2e; color: #cdd6f4;
    selection-background-color: #45475a; }
QStatusBar { background: #181825; color: #a6adc8; border-top: 1px solid #313244; }
QScrollBar:vertical { background: #1e1e2e; width: 10px; border: none; }
QScrollBar::handle:vertical { background: #45475a; border-radius: 5px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #1e1e2e; height: 10px; border: none; }
QScrollBar::handle:horizontal { background: #45475a; border-radius: 5px; min-width: 20px; }
QScrollBar::handle:horizontal:hover { background: #585b70; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QGroupBox { border: 1px solid #313244; border-radius: 6px; margin-top: 8px;
    padding-top: 16px; font-weight: bold; color: #89b4fa; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
QLineEdit { background: #313244; color: #cdd6f4; border: 1px solid #45475a;
    border-radius: 4px; padding: 4px 8px; }
QLineEdit:focus { border-color: #89b4fa; }
QPushButton { background: #313244; color: #cdd6f4; border: none;
    border-radius: 4px; padding: 6px 14px; }
QPushButton:hover { background: #45475a; }
QPushButton:pressed { background: #585b70; }
QDialog { background: #1e1e2e; }
QListWidget { background: #181825; color: #f38ba8; border: none;
    font-family: 'Consolas','Monospace',monospace; font-size: 9pt; }
QListWidget::item:hover { background: #313244; }
QLabel { color: #cdd6f4; }
"""


# ═══════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════

class DiagramEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagram Editor \u2014 Untitled")
        self.setMinimumSize(1100, 700)
        self.resize(1400, 850)

        self.current_file = None
        self.has_unsaved_changes = False
        self._suppress_code_update = False
        self._suppress_scene_update = False
        self._last_parsed = None
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)
        self._debounce_timer.timeout.connect(self._update_preview)

        self._filter_debounce = QTimer(self)
        self._filter_debounce.setSingleShot(True)
        self._filter_debounce.setInterval(150)
        self._filter_debounce.timeout.connect(self._apply_filter)

        self.settings = QSettings("DiagramEditor", "DiagramEditor")

        self._diagram_settings = {
            "node_width": 140, "node_height": 50,
            "h_gap": 60, "v_gap": 70,
            "font_size": 11, "color_scheme": "Default",
            "container_padding": 20, "container_gap": 15,
            "swimlane_gap": 10, "direction": "top-to-bottom",
        }

        self._setup_actions()
        self._setup_central_widget()
        self._setup_settings_dock()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_status_bar()
        self.setStyleSheet(STYLESHEET)

        self._load_persisted_state()

        self.code_editor.setPlainText(EXAMPLE_CODE)
        self._schedule_update()

    # ─── Actions ─────────────────────────────
    def _setup_actions(self):
        self.act_new = QAction("New", self, shortcut=QKeySequence.New, triggered=self._new_file)
        self.act_open = QAction("Open", self, shortcut=QKeySequence.Open, triggered=self._open_file)
        self.act_save = QAction("Save", self, shortcut=QKeySequence.Save, triggered=self._save_file)
        self.act_save_as = QAction("Save As", self, shortcut="Ctrl+Shift+S", triggered=self._save_file_as)
        self.act_export_pdf = QAction("Export PDF", self, shortcut="Ctrl+P", triggered=self._export_pdf)
        self.act_export_svg = QAction("Export SVG", self, shortcut="Ctrl+E", triggered=self._export_svg)
        self.act_export_png = QAction("Export PNG", self, shortcut="Ctrl+Shift+E", triggered=self._export_png)
        self.act_quit = QAction("Quit", self, shortcut=QKeySequence.Quit, triggered=self.close)
        self.act_undo = QAction("Undo", self, shortcut=QKeySequence.Undo, triggered=lambda: self.code_editor.undo())
        self.act_redo = QAction("Redo", self, shortcut="Ctrl+Shift+Z", triggered=lambda: self.code_editor.redo())
        self.act_find = QAction("Find", self, shortcut=QKeySequence.Find, triggered=lambda: self._show_find(False))
        self.act_replace = QAction("Find && Replace", self, shortcut="Ctrl+H", triggered=lambda: self._show_find(True))
        self.act_copy_diagram = QAction("Copy Diagram", self, shortcut="Ctrl+Shift+C", triggered=self._copy_diagram)
        self.act_zoom_in = QAction("Zoom In", self, shortcut="Ctrl+=", triggered=lambda: self._zoom(1.15))
        self.act_zoom_out = QAction("Zoom Out", self, shortcut="Ctrl+-", triggered=lambda: self._zoom(1 / 1.15))
        self.act_zoom_fit = QAction("Zoom to Fit", self, shortcut="Ctrl+0", triggered=lambda: self.diagram_view.fit_to_content())
        self.act_zoom_actual = QAction("Actual Size", self, shortcut="Ctrl+1", triggered=lambda: self.diagram_view.reset_zoom())
        self.act_focus_filter = QAction("Focus Filter", self, shortcut="Ctrl+/", triggered=self._focus_filter)
        self.act_clear_filter = QAction("Clear Filter", self, shortcut="Ctrl+Shift+/", triggered=self._clear_filter)
        self.act_help = QAction("Syntax Reference", self, shortcut="F1", triggered=self._show_help)
        self.act_example = QAction("Load Example", self, triggered=self._load_example)
        self.act_about = QAction("About", self, triggered=self._show_about)
        self.act_llm_prompt = QAction("Copy LLM Prompt", self, shortcut="Ctrl+Shift+L",
                                       triggered=self._show_llm_prompt)
        self.act_llm_prompt.setToolTip("Show and copy to clipboard a complete instruction set for an LLM to generate diagrams in this tool's DSL")

        # ── Mode actions ──
        self.act_mode_select = QAction("\u25e8 Select (V)", self, checkable=True, checked=True)
        self.act_mode_select.setShortcut("V")
        self.act_mode_select.setToolTip("Select mode \u2014 Click to select objects, drag to move them. (V)")
        self.act_mode_select.triggered.connect(lambda: self._set_mode("select"))

        self.act_mode_pan = QAction("\u270b Pan (H)", self, checkable=True)
        self.act_mode_pan.setShortcut("H")
        self.act_mode_pan.setToolTip("Pan mode \u2014 Drag anywhere to scroll the canvas. (H)")
        self.act_mode_pan.triggered.connect(lambda: self._set_mode("pan"))

        self.act_mode_connect = QAction("\u2197 Connect (C)", self, checkable=True)
        self.act_mode_connect.setShortcut("C")
        self.act_mode_connect.setToolTip("Connect mode \u2014 Click a node and drag to another to create a connection. (C)")
        self.act_mode_connect.triggered.connect(lambda: self._set_mode("connect"))

        from PySide6.QtGui import QActionGroup
        self._mode_group = QActionGroup(self)
        self._mode_group.setExclusive(True)
        self._mode_group.addAction(self.act_mode_select)
        self._mode_group.addAction(self.act_mode_pan)
        self._mode_group.addAction(self.act_mode_connect)

        # ── Insert actions ──
        # Containers
        self.act_ins_swimlane = QAction("\u2261 Swimlane", self, triggered=lambda: self._insert_template('swimlane'))
        self.act_ins_swimlane.setToolTip("Swimlane \u2014 Cross-functional lane (Visio). Groups objects by department, role, or system.")
        self.act_ins_box = QAction("\u25a3 Box", self, triggered=lambda: self._insert_template('box'))
        self.act_ins_box.setToolTip("Box \u2014 Sub-container inside a swimlane for color-coded grouping (e.g. \"Automated Tests\").")
        self.act_ins_group = QAction("\u2500\u2500 Group", self, triggered=lambda: self._insert_template('group'))
        self.act_ins_group.setToolTip("Group \u2014 Visual overlay (dashed border) referencing existing objects. Like Visio's group selection.")

        # Shapes — Visio/BPMN/Mermaid standard meanings
        self.act_ins_rect = QAction("\u25ad Process", self, triggered=lambda: self._insert_template('rect'))
        self.act_ins_rect.setToolTip("Rectangle \u2014 Process / Activity / Task. Standard flowchart action step. (Visio: Process, Mermaid: node)")
        self.act_ins_rounded = QAction("\u25ad Rounded", self, triggered=lambda: self._insert_template('rounded'))
        self.act_ins_rounded.setToolTip("Rounded Rectangle \u2014 Alternate process or sub-process. (BPMN: Task, Mermaid: rounded node)")
        self.act_ins_diamond = QAction("\u25c7 Decision", self, triggered=lambda: self._insert_template('diamond'))
        self.act_ins_diamond.setToolTip("Diamond \u2014 Decision / Gateway. Branch point with Yes/No or conditional paths. (Visio: Decision, BPMN: Gateway)")
        self.act_ins_circle = QAction("\u25cb Start/End", self, triggered=lambda: self._insert_template('circle'))
        self.act_ins_circle.setToolTip("Circle \u2014 Terminator / Event. Start or end of a flow. (Visio: Terminator, BPMN: Start/End Event, Mermaid: circle)")
        self.act_ins_para = QAction("\u25b1 Input/Output", self, triggered=lambda: self._insert_template('parallelogram'))
        self.act_ins_para.setToolTip("Parallelogram \u2014 Data / Input / Output. Represents data entering or leaving the process. (Visio: Data, ISO 5807)")
        self.act_ins_hex = QAction("\u2b21 Preparation", self, triggered=lambda: self._insert_template('hexagon'))
        self.act_ins_hex.setToolTip("Hexagon \u2014 Preparation / Setup. Initialization or configuration step before a process. (Visio: Preparation, Mermaid: hexagon)")
        self.act_ins_cyl = QAction("\u2395 Database", self, triggered=lambda: self._insert_template('cylinder'))
        self.act_ins_cyl.setToolTip("Cylinder \u2014 Data Store / Database. Persistent storage: database, disk, repository. (Visio: Data Store, Mermaid: cylindrical)")
        self.act_ins_stadium = QAction("\u2b2d Terminal", self, triggered=lambda: self._insert_template('stadium'))
        self.act_ins_stadium.setToolTip("Stadium \u2014 Terminal / Pill. Start/stop point or external process boundary. (Mermaid: stadium-shaped)")

        # Connections — standard flowchart/BPMN meaning
        self.act_ins_arrow = QAction("\u2192 Sequence Flow", self, triggered=lambda: self._insert_template('arrow'))
        self.act_ins_arrow.setToolTip("Solid Arrow (\u2192) \u2014 Sequence Flow. Normal flow of control from one step to the next. (BPMN: Sequence Flow)")
        self.act_ins_dashed = QAction("\u21e2 Message Flow", self, triggered=lambda: self._insert_template('dashed_arrow'))
        self.act_ins_dashed.setToolTip("Dashed Arrow (\u21e2) \u2014 Message / Conditional Flow. Communication between pools, or optional/alternate path. (BPMN: Message Flow)")
        self.act_ins_thick = QAction("\u21d2 Critical Path", self, triggered=lambda: self._insert_template('thick_arrow'))
        self.act_ins_thick.setToolTip("Thick Arrow (\u21d2) \u2014 Critical Path / Emphasis. Highlights the primary or time-critical route through the diagram.")
        self.act_ins_line = QAction("\u2500 Association", self, triggered=lambda: self._insert_template('solid_line'))
        self.act_ins_line.setToolTip("Solid Line (\u2500) \u2014 Association / Undirected relationship. Links related elements without implying sequence. (BPMN: Association)")
        self.act_ins_dotted = QAction("\u2504 Dependency", self, triggered=lambda: self._insert_template('dotted_line'))
        self.act_ins_dotted.setToolTip("Dotted Line (\u2504) \u2014 Dependency / Weak link. Indicates a dependency, fallback path, or error recovery route.")

        # Other
        self.act_ins_note = QAction("\u2709 Note", self, triggered=lambda: self._insert_template('note'))
        self.act_ins_note.setToolTip("Note / Annotation \u2014 Attach explanatory text to any object. (BPMN: Text Annotation, Visio: Callout)")

    # ─── Menu Bar ────────────────────────────
    def _setup_menu_bar(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        file_menu.addAction(self.act_new)
        file_menu.addAction(self.act_open)
        self.recent_menu = file_menu.addMenu("Open Recent")
        self._update_recent_menu()
        file_menu.addAction(self.act_save)
        file_menu.addAction(self.act_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.act_export_pdf)
        file_menu.addAction(self.act_export_svg)
        file_menu.addAction(self.act_export_png)
        file_menu.addSeparator()
        file_menu.addAction(self.act_quit)

        edit_menu = mb.addMenu("Edit")
        edit_menu.addAction(self.act_undo)
        edit_menu.addAction(self.act_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_find)
        edit_menu.addAction(self.act_replace)
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_copy_diagram)

        # ── Insert menu ──
        insert_menu = mb.addMenu("Insert")

        cont_menu = insert_menu.addMenu("Containers")
        cont_menu.addAction(self.act_ins_swimlane)
        cont_menu.addAction(self.act_ins_box)
        cont_menu.addAction(self.act_ins_group)

        shape_menu = insert_menu.addMenu("Shapes")
        shape_menu.addAction(self.act_ins_rect)
        shape_menu.addAction(self.act_ins_rounded)
        shape_menu.addAction(self.act_ins_diamond)
        shape_menu.addAction(self.act_ins_circle)
        shape_menu.addSeparator()
        shape_menu.addAction(self.act_ins_para)
        shape_menu.addAction(self.act_ins_hex)
        shape_menu.addAction(self.act_ins_cyl)
        shape_menu.addAction(self.act_ins_stadium)

        conn_menu = insert_menu.addMenu("Connections")
        conn_menu.addAction(self.act_ins_arrow)
        conn_menu.addAction(self.act_ins_dashed)
        conn_menu.addAction(self.act_ins_thick)
        conn_menu.addSeparator()
        conn_menu.addAction(self.act_ins_line)
        conn_menu.addAction(self.act_ins_dotted)

        insert_menu.addSeparator()
        insert_menu.addAction(self.act_ins_note)

        view_menu = mb.addMenu("View")
        view_menu.addAction(self.act_zoom_in)
        view_menu.addAction(self.act_zoom_out)
        view_menu.addAction(self.act_zoom_fit)
        view_menu.addAction(self.act_zoom_actual)
        view_menu.addSeparator()
        view_menu.addAction(self.act_focus_filter)
        view_menu.addAction(self.act_clear_filter)
        view_menu.addSeparator()
        self.act_toggle_settings = self.settings_dock.toggleViewAction()
        self.act_toggle_settings.setText("Settings Panel")
        view_menu.addAction(self.act_toggle_settings)

        # Color scheme submenu
        scheme_menu = view_menu.addMenu("Color Scheme")
        for name in COLOR_SCHEMES:
            act = QAction(name, self, checkable=True)
            act.setChecked(name == self._diagram_settings["color_scheme"])
            act.triggered.connect(lambda checked, n=name: self._set_scheme(n))
            scheme_menu.addAction(act)

        help_menu = mb.addMenu("Help")
        help_menu.addAction(self.act_help)
        help_menu.addAction(self.act_example)
        help_menu.addSeparator()
        help_menu.addAction(self.act_llm_prompt)
        help_menu.addSeparator()
        help_menu.addAction(self.act_about)

    # ─── Toolbar ─────────────────────────────
    def _setup_toolbar(self):
        tb = self.addToolBar("Main")
        tb.setMovable(True)

        # ASCII logo: Blackjack card + hook
        logo = QLabel(
            "\u250c\u2500\u2500\u2510 \u256d\u2510\n"
            "\u2502A\u2660\u2502 \u2502\u2502\n"
            "\u2502\u2660A\u2502 \u2570\u256f\n"
            "\u2514\u2500\u2500\u2518   "
        )
        logo.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 7pt; "
            "color: #f5e0dc; background: #313244; "
            "border: 1px solid #45475a; border-radius: 3px; "
            "padding: 1px 3px; margin-right: 6px;"
        )
        logo.setToolTip("Diagram Editor \u2014 With blackjack and a hooker!")
        tb.addWidget(logo)

        tb.addAction(self.act_new)
        tb.addAction(self.act_open)
        tb.addAction(self.act_save)
        tb.addSeparator()
        tb.addAction(self.act_export_pdf)
        tb.addAction(self.act_export_svg)
        tb.addSeparator()
        tb.addAction(self.act_copy_diagram)
        tb.addSeparator()
        tb.addAction(self.act_zoom_fit)
        tb.addSeparator()
        tb.addAction(self.act_undo)
        tb.addAction(self.act_redo)
        tb.addSeparator()

        # Mode buttons (mutually exclusive)
        tb.addAction(self.act_mode_select)
        tb.addAction(self.act_mode_pan)
        tb.addAction(self.act_mode_connect)
        tb.addSeparator()

        # Filter field
        self.filter_field = QLineEdit()
        self.filter_field.setPlaceholderText("Filter: type:decision owner:alice tags:mvp ...")
        self.filter_field.setMinimumWidth(250)
        self.filter_field.setMaximumWidth(400)
        self.filter_field.textChanged.connect(lambda: self._filter_debounce.start())
        self.filter_field.installEventFilter(self)
        tb.addWidget(self.filter_field)

    # ─── Central Widget ─────────────────────
    def _setup_central_widget(self):
        # Scene + View
        self.diagram_scene = DiagramScene(self)
        self.diagram_view = DiagramView(self.diagram_scene)
        self.diagram_view.zoom_changed.connect(self._on_zoom_changed)

        # Bidirectional: scene → code
        self.diagram_scene.node_moved.connect(self._on_node_moved)
        self.diagram_scene.connection_created.connect(self._on_connection_created)
        self.diagram_scene.selectionChanged.connect(self._on_scene_selection_changed)

        # Code editor
        self.code_editor = CodeEditor()
        self.highlighter = DiagramHighlighter(self.code_editor.document())
        self.code_editor.textChanged.connect(self._on_code_changed)
        self.code_editor.cursorPositionChanged.connect(self._on_cursor_moved)

        # Error list
        self.error_list = QListWidget()
        self.error_list.itemDoubleClicked.connect(self._on_error_clicked)

        # Find bar
        self.find_bar = QWidget()
        self.find_bar.setVisible(False)
        fb_layout = QHBoxLayout(self.find_bar)
        fb_layout.setContentsMargins(4, 2, 4, 2)
        fb_layout.addWidget(QLabel("Find:"))
        self.find_input = QLineEdit()
        self.find_input.returnPressed.connect(self._find_next)
        fb_layout.addWidget(self.find_input)
        btn_next = QPushButton("Next")
        btn_next.clicked.connect(self._find_next)
        fb_layout.addWidget(btn_next)
        btn_prev = QPushButton("Prev")
        btn_prev.clicked.connect(self._find_prev)
        fb_layout.addWidget(btn_prev)

        self.replace_label = QLabel("Replace:")
        fb_layout.addWidget(self.replace_label)
        self.replace_input = QLineEdit()
        fb_layout.addWidget(self.replace_input)
        self.btn_replace = QPushButton("Replace")
        self.btn_replace.clicked.connect(self._replace_one)
        fb_layout.addWidget(self.btn_replace)
        self.btn_replace_all = QPushButton("All")
        self.btn_replace_all.clicked.connect(self._replace_all)
        fb_layout.addWidget(self.btn_replace_all)

        btn_close = QPushButton("\u2715")
        btn_close.setFixedWidth(30)
        btn_close.clicked.connect(lambda: self.find_bar.hide())
        fb_layout.addWidget(btn_close)
        self.replace_label.hide()
        self.replace_input.hide()
        self.btn_replace.hide()
        self.btn_replace_all.hide()

        # Editor vertical splitter
        editor_splitter = QSplitter(Qt.Vertical)
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        editor_layout.addWidget(self.find_bar)
        editor_layout.addWidget(self.code_editor)
        editor_splitter.addWidget(editor_widget)
        editor_splitter.addWidget(self.error_list)
        editor_splitter.setStretchFactor(0, 4)
        editor_splitter.setStretchFactor(1, 1)
        editor_splitter.setChildrenCollapsible(True)
        self.editor_splitter = editor_splitter

        # ── Drawing palette (multi-row, bottom of preview) ──
        palette_style = """
            QWidget#palette { background: #181825; border-top: 1px solid #313244; }
            QPushButton { background: #313244; color: #cdd6f4; border: none;
                border-radius: 3px; padding: 3px 8px; font-size: 9pt; }
            QPushButton:hover { background: #45475a; }
            QPushButton:pressed { background: #585b70; }
        """
        palette_widget = QWidget()
        palette_widget.setObjectName("palette")
        palette_widget.setStyleSheet(palette_style)
        palette_grid = QVBoxLayout(palette_widget)
        palette_grid.setContentsMargins(6, 4, 6, 4)
        palette_grid.setSpacing(3)

        def _make_row(label_text, actions):
            row = QHBoxLayout()
            row.setSpacing(3)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #6c7086; font-size: 8pt; font-weight: bold; min-width: 75px;")
            row.addWidget(lbl)
            for act in actions:
                btn = QPushButton(act.text())
                btn.setToolTip(act.toolTip())
                btn.clicked.connect(act.trigger)
                row.addWidget(btn)
            row.addStretch()
            return row

        palette_grid.addLayout(_make_row("Containers", [
            self.act_ins_swimlane, self.act_ins_box, self.act_ins_group,
        ]))
        palette_grid.addLayout(_make_row("Shapes", [
            self.act_ins_rect, self.act_ins_rounded, self.act_ins_diamond,
            self.act_ins_circle, self.act_ins_para, self.act_ins_hex,
            self.act_ins_cyl, self.act_ins_stadium,
        ]))
        palette_grid.addLayout(_make_row("Connectors", [
            self.act_ins_arrow, self.act_ins_dashed, self.act_ins_thick,
            self.act_ins_line, self.act_ins_dotted, self.act_ins_note,
        ]))

        # Preview pane = diagram view on top + palette at bottom
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)
        preview_layout.addWidget(self.diagram_view, 1)
        preview_layout.addWidget(palette_widget)

        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(editor_splitter)
        main_splitter.addWidget(preview_widget)
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 3)
        main_splitter.setChildrenCollapsible(False)
        self.main_splitter = main_splitter

        self.setCentralWidget(main_splitter)

    # ─── Settings Dock ───────────────────────
    def _setup_settings_dock(self):
        dock = QDockWidget("Settings", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(8)

        # Direction
        grp_layout = QGroupBox("Layout")
        gl = QFormLayout(grp_layout)
        self.direction_combo = QComboBox()
        self.direction_combo.addItems([
            "top-to-bottom", "left-to-right", "bottom-to-top", "right-to-left",
        ])
        self.direction_combo.currentTextChanged.connect(self._on_direction_changed)
        gl.addRow("Direction:", self.direction_combo)
        layout.addWidget(grp_layout)

        # Sizing sliders
        grp_size = QGroupBox("Sizing")
        sl = QFormLayout(grp_size)
        self._slider_widgets = {}
        for label, key, lo, hi, default in [
            ("Node Width", "node_width", 80, 250, 140),
            ("Node Height", "node_height", 30, 120, 50),
            ("H Gap", "h_gap", 20, 150, 60),
            ("V Gap", "v_gap", 20, 150, 70),
            ("Font Size", "font_size", 8, 18, 11),
            ("Padding", "container_padding", 10, 40, 20),
        ]:
            slider = QSlider(Qt.Horizontal)
            slider.setRange(lo, hi)
            slider.setValue(default)
            val_label = QLabel(str(default))
            slider.valueChanged.connect(lambda v, vl=val_label: vl.setText(str(v)))
            slider.valueChanged.connect(self._schedule_update)
            self._slider_widgets[key] = slider
            row = QHBoxLayout()
            row.addWidget(slider)
            row.addWidget(val_label)
            w = QWidget()
            w.setLayout(row)
            sl.addRow(f"{label}:", w)
        layout.addWidget(grp_size)

        # Color scheme + toggles
        grp_color = QGroupBox("Appearance")
        cl = QFormLayout(grp_color)
        self.scheme_combo = QComboBox()
        self.scheme_combo.addItems(list(COLOR_SCHEMES.keys()))
        self.scheme_combo.currentTextChanged.connect(self._schedule_update)
        cl.addRow("Scheme:", self.scheme_combo)

        from PySide6.QtWidgets import QCheckBox
        self.show_grid_cb = QCheckBox("Show grid")
        self.show_grid_cb.setChecked(True)
        self.show_grid_cb.setStyleSheet("color: #cdd6f4;")
        self.show_grid_cb.toggled.connect(self._schedule_update)
        cl.addRow(self.show_grid_cb)

        self.show_steps_cb = QCheckBox("Show step numbers")
        self.show_steps_cb.setChecked(True)
        self.show_steps_cb.setStyleSheet("color: #cdd6f4;")
        self.show_steps_cb.toggled.connect(self._schedule_update)
        cl.addRow(self.show_steps_cb)

        layout.addWidget(grp_color)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        dock.setWidget(scroll)

        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.settings_dock = dock

    # ─── Status Bar ──────────────────────────
    def _setup_status_bar(self):
        self.status_label = QLabel("Ready")
        self.zoom_label = QLabel("Zoom: 100%")
        self.filter_status = QLabel("")
        sb = self.statusBar()
        sb.addWidget(self.status_label, 1)
        sb.addPermanentWidget(self.filter_status)
        sb.addPermanentWidget(self.zoom_label)

    # ─── Core Logic ──────────────────────────
    def _schedule_update(self, *args):
        self._debounce_timer.start()

    def _on_code_changed(self):
        if not self._suppress_code_update:
            self.has_unsaved_changes = True
            self._update_title()
            self._schedule_update()

    def _update_preview(self):
        if self._suppress_scene_update:
            return

        code = self.code_editor.toPlainText().strip()
        if not code:
            self.diagram_scene.clear()
            self.error_list.clear()
            self.status_label.setText("Ready")
            return

        parsed = parse_diagram(code)
        self._last_parsed = parsed

        # Bidirectional direction sync: code ↔ settings combo
        code_dir = parsed.get("direction", "top-to-bottom")
        self.direction_combo.blockSignals(True)
        idx = self.direction_combo.findText(code_dir)
        if idx >= 0:
            self.direction_combo.setCurrentIndex(idx)
        self.direction_combo.blockSignals(False)

        self._apply_diagram_settings()

        # Apply code-declared settings (override panel values)
        code_settings = parsed.get("_settings", {})
        for key, val in code_settings.items():
            if key == "color_scheme":
                self._diagram_settings[key] = val
                idx_s = self.scheme_combo.findText(val)
                if idx_s >= 0:
                    self.scheme_combo.blockSignals(True)
                    self.scheme_combo.setCurrentIndex(idx_s)
                    self.scheme_combo.blockSignals(False)
            elif key in self._slider_widgets:
                try:
                    int_val = int(val)
                    self._diagram_settings[key] = int_val
                    self._slider_widgets[key].blockSignals(True)
                    self._slider_widgets[key].setValue(int_val)
                    self._slider_widgets[key].blockSignals(False)
                except ValueError:
                    pass

        layout = compute_layout(parsed, self._diagram_settings)

        self._suppress_scene_update = True
        self.diagram_scene.render_diagram(parsed, layout, self._diagram_settings)
        self._suppress_scene_update = False

        # Update errors
        self.error_list.clear()
        error_lines = set()
        for err in parsed["errors"]:
            ln = err.get("line", 0)
            error_lines.add(ln)
            self.error_list.addItem(f"Line {ln}: {err['message']}")
        self.code_editor.set_error_lines(error_lines)

        # Status
        objs = len(parsed["objects"])
        conns = len(parsed["connections"])
        sls = len(parsed["swimlanes"])
        steps = len(set(o["step"] for o in parsed["objects"])) if parsed["objects"] else 0
        parts = [f"{objs} objects", f"{conns} connections"]
        if sls:
            parts.append(f"{sls} swimlanes")
        if steps:
            parts.append(f"{steps} steps")
        rect = self.diagram_scene.itemsBoundingRect()
        if not rect.isEmpty():
            parts.append(f"{int(rect.width())}\u00d7{int(rect.height())}px")
        self.status_label.setText(", ".join(parts))

        # Apply active filter
        self._apply_filter()

    def _apply_diagram_settings(self):
        for key, slider in self._slider_widgets.items():
            self._diagram_settings[key] = slider.value()
        self._diagram_settings["color_scheme"] = self.scheme_combo.currentText()
        self._diagram_settings["show_step_numbers"] = self.show_steps_cb.isChecked()
        self._diagram_settings["show_grid"] = self.show_grid_cb.isChecked()
        self._diagram_settings["direction"] = self.direction_combo.currentText()

    def _on_direction_changed(self, new_direction):
        """Direction combo changed — write it to the code editor."""
        if self._suppress_code_update:
            return
        self._suppress_code_update = True
        try:
            doc = self.code_editor.document()
            dir_re = re.compile(
                r'^(\s*)direction\s+'
                r'(top-to-bottom|left-to-right|bottom-to-top|right-to-left'
                r'|TB|LR|BT|RL)\s*$',
                re.IGNORECASE,
            )
            # Find the direction line and replace it surgically
            found = False
            block = doc.begin()
            while block.isValid():
                if dir_re.match(block.text()):
                    cursor = QTextCursor(block)
                    cursor.movePosition(QTextCursor.StartOfBlock)
                    cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                    self._suppress_scene_update = True
                    cursor.insertText(f"direction {new_direction}")
                    self._suppress_scene_update = False
                    found = True
                    break
                block = block.next()

            if not found:
                # Insert at top, after any leading comments
                block = doc.begin()
                insert_block = doc.begin()
                while block.isValid():
                    text = block.text().strip()
                    if text and not text.startswith("//"):
                        insert_block = block
                        break
                    block = block.next()
                cursor = QTextCursor(insert_block)
                cursor.movePosition(QTextCursor.StartOfBlock)
                self._suppress_scene_update = True
                cursor.insertText(f"direction {new_direction}\n")
                self._suppress_scene_update = False
        finally:
            self._suppress_code_update = False
        self._schedule_update()

    # ─── Filter ──────────────────────────────
    def _apply_filter(self):
        query = self.filter_field.text().strip()
        if not query or not self._last_parsed:
            # Clear filter
            for node in self.diagram_scene.scene_nodes.values():
                node.is_filtered_out = False
                node.update()
            self.filter_status.setText("")
            return

        terms = parse_filter_query(query)
        match_count = 0
        total = len(self._last_parsed["objects"])
        for obj in self._last_parsed["objects"]:
            matches = object_matches_filter(obj, terms)
            if matches:
                match_count += 1
            node = self.diagram_scene.scene_nodes.get(obj["name"])
            if node:
                node.is_filtered_out = not matches
                node.update()

        self.filter_status.setText(f"Filter: {match_count} of {total} objects match")

    def _focus_filter(self):
        self.filter_field.setFocus()
        self.filter_field.selectAll()

    def _clear_filter(self):
        self.filter_field.clear()
        self._apply_filter()

    # ─── Selection Sync ──────────────────────
    def _on_cursor_moved(self):
        if self._suppress_scene_update or not self._last_parsed:
            return
        cursor = self.code_editor.textCursor()
        line = cursor.blockNumber() + 1
        obj_lines = self._last_parsed.get("_object_lines", {})
        for name, ln in obj_lines.items():
            if ln == line:
                node = self.diagram_scene.scene_nodes.get(name)
                if node:
                    self.diagram_scene.clearSelection()
                    node.setSelected(True)
                return
        self.diagram_scene.clearSelection()

    # ─── Bidirectional: Scene → Code ────────
    def _on_node_moved(self, name, x, y):
        """Node was dragged in the scene — write @(x,y) to code.

        This fires ONCE on mouse release, not during drag.
        Uses a surgical QTextCursor edit on just the one line so it
        does NOT trigger a full scene rebuild.
        """
        if self._suppress_code_update:
            return
        self._suppress_code_update = True
        self._suppress_scene_update = True
        try:
            self._write_position_pin(name, x, y)
        finally:
            self._suppress_code_update = False
            self._suppress_scene_update = False
        self.has_unsaved_changes = True
        self._update_title()
        # Re-parse in the background so _last_parsed stays fresh,
        # but do NOT re-render the scene (the node is already where
        # the user put it, and the edges followed).
        code = self.code_editor.toPlainText()
        self._last_parsed = parse_diagram(code)
        # Check if the node was dragged into a different swimlane
        self._check_swimlane_reparent(name, x, y)

    def _write_position_pin(self, name, x, y):
        """Insert or update @(x,y) on the object's code line.

        Uses QTextCursor to edit only the affected line so it does NOT
        trigger a full document replace (which would rebuild the scene
        and destroy the drag operation).
        """
        obj_lines = (self._last_parsed or {}).get("_object_lines", {})
        line_num = obj_lines.get(name)
        if line_num is None:
            return
        block_idx = line_num - 1  # 0-based

        doc = self.code_editor.document()
        block = doc.findBlockByNumber(block_idx)
        if not block.isValid():
            return

        old_text = block.text()
        pin_str = f"@({x}, {y})"

        # Build new line
        pin_re = re.compile(r'@\(\s*-?\d+\s*,\s*-?\d+\s*\)')
        if pin_re.search(old_text):
            new_text = pin_re.sub(pin_str, old_text)
        else:
            style_m = re.search(r'\{[^}]*\}\s*$', old_text)
            if style_m:
                new_text = old_text[:style_m.start()].rstrip() + " " + pin_str + " " + style_m.group()
            else:
                new_text = old_text.rstrip() + " " + pin_str

        if new_text == old_text:
            return

        # Surgical replace: select just this block's text, replace it
        cursor = QTextCursor(block)
        cursor.movePosition(QTextCursor.StartOfBlock)
        cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        cursor.insertText(new_text)

    def _check_swimlane_reparent(self, name, x, y):
        """If a node was dragged into a different swimlane column, update
        the code to move it."""
        if not self._last_parsed:
            return
        layout_data = compute_layout(self._last_parsed, self._diagram_settings)
        sl_rects = layout_data.get("swimlane_rects", {})

        # Which swimlane is the node now inside?
        new_swimlane = None
        for sl_name, (sx, sy, sw, sh) in sl_rects.items():
            if sx <= x <= sx + sw and sy <= y <= sy + sh:
                new_swimlane = sl_name
                break

        # What swimlane was it in before?
        obj = next((o for o in self._last_parsed["objects"]
                     if o["name"] == name), None)
        if not obj:
            return
        old_swimlane = obj.get("swimlane")

        if new_swimlane == old_swimlane:
            return  # No change

        # Reparent: remove from old swimlane block, add to new one
        # This is complex code manipulation — we move the line from one
        # block to another. For now, just re-parse after pin update;
        # the next render will pick up the new position.
        # Full reparent would require cutting and pasting lines between
        # swimlane blocks, which we'll do here:
        code = self.code_editor.toPlainText()
        lines = code.split("\n")
        obj_lines = self._last_parsed.get("_object_lines", {})
        src_line_idx = obj_lines.get(name)
        if src_line_idx is None:
            return
        idx = src_line_idx - 1
        if idx < 0 or idx >= len(lines):
            return

        obj_line = lines[idx]
        # Remove the line from its current position
        lines.pop(idx)

        if new_swimlane:
            # Find the closing brace of the target swimlane and insert before it
            target_close = None
            depth = 0
            in_target = False
            for i, ln in enumerate(lines):
                stripped = ln.strip()
                if re.match(rf'^swimlane\s+"{re.escape(new_swimlane)}"\s*\{{', stripped):
                    in_target = True
                    depth = 1
                    continue
                if in_target:
                    if "{" in stripped:
                        depth += stripped.count("{")
                    if "}" in stripped:
                        depth -= stripped.count("}")
                    if depth <= 0:
                        target_close = i
                        break
            if target_close is not None:
                # Indent and insert
                lines.insert(target_close, "    " + obj_line.strip())
        else:
            # Move to top level — insert after the last swimlane block
            insert_at = len(lines)
            for i, ln in enumerate(lines):
                if ln.strip().startswith("swimlane") or ln.strip() == "}":
                    insert_at = i + 1
            lines.insert(insert_at, obj_line.strip())

        cursor = self.code_editor.textCursor()
        pos = cursor.position()
        self.code_editor.setPlainText("\n".join(lines))
        cursor = self.code_editor.textCursor()
        cursor.setPosition(min(pos, len(self.code_editor.toPlainText())))
        self.code_editor.setTextCursor(cursor)

    def _on_connection_created(self, from_name, to_name):
        """User dragged a connection between two ports — add it to code."""
        if self._suppress_code_update:
            return
        self._suppress_code_update = True
        try:
            new_line = f"{from_name} -> {to_name}"
            # Append at end of document using QTextCursor
            cursor = QTextCursor(self.code_editor.document())
            cursor.movePosition(QTextCursor.End)
            cursor.insertText("\n" + new_line)
        finally:
            self._suppress_code_update = False
        self.has_unsaved_changes = True
        self._update_title()
        self._schedule_update()

    def _on_scene_selection_changed(self):
        """Scene selection changed — scroll editor to matching line."""
        if self._suppress_scene_update:
            return
        selected = self.diagram_scene.selectedItems()
        if not selected:
            return
        item = selected[0]
        if not isinstance(item, DiagramNode):
            return
        name = item.obj["name"]
        if not self._last_parsed:
            return
        obj_lines = self._last_parsed.get("_object_lines", {})
        ln = obj_lines.get(name)
        if ln is None:
            return
        self._suppress_scene_update = True
        cursor = self.code_editor.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, ln - 1)
        cursor.select(QTextCursor.LineUnderCursor)
        self.code_editor.setTextCursor(cursor)
        self.code_editor.centerCursor()
        self._suppress_scene_update = False

    # ─── Modes ───────────────────────────────
    def _set_mode(self, mode):
        self.diagram_view.set_mode(mode)
        self.act_mode_select.setChecked(mode == "select")
        self.act_mode_pan.setChecked(mode == "pan")
        self.act_mode_connect.setChecked(mode == "connect")
        self.statusBar().showMessage(
            {"select": "Select mode: click to select, drag to move",
             "pan": "Pan mode: drag to scroll the canvas",
             "connect": "Connect mode: click a node, drag to another to connect",
            }.get(mode, ""), 3000
        )

    # ─── Zoom ────────────────────────────────
    def _zoom(self, factor):
        view = self.diagram_view
        new_zoom = view.zoom_level * factor
        new_zoom = max(0.1, min(5.0, new_zoom))
        sf = new_zoom / view.zoom_level
        view.scale(sf, sf)
        view.zoom_level = new_zoom
        view.zoom_changed.emit(new_zoom)

    def _on_zoom_changed(self, level):
        self.zoom_label.setText(f"Zoom: {int(level * 100)}%")

    # ─── Find & Replace ──────────────────────
    def _show_find(self, with_replace):
        self.find_bar.show()
        self.find_input.setFocus()
        vis = with_replace
        self.replace_label.setVisible(vis)
        self.replace_input.setVisible(vis)
        self.btn_replace.setVisible(vis)
        self.btn_replace_all.setVisible(vis)

    def _find_next(self):
        query = self.find_input.text()
        if not query:
            return
        cursor = self.code_editor.textCursor()
        found = self.code_editor.document().find(query, cursor)
        if found.isNull():
            found = self.code_editor.document().find(query, 0)
        if not found.isNull():
            self.code_editor.setTextCursor(found)

    def _find_prev(self):
        query = self.find_input.text()
        if not query:
            return
        cursor = self.code_editor.textCursor()
        found = self.code_editor.document().find(query, cursor, QTextDocument.FindBackward)
        if found.isNull():
            end_cursor = QTextCursor(self.code_editor.document())
            end_cursor.movePosition(QTextCursor.End)
            found = self.code_editor.document().find(query, end_cursor, QTextDocument.FindBackward)
        if not found.isNull():
            self.code_editor.setTextCursor(found)

    def _replace_one(self):
        cursor = self.code_editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText().lower() == self.find_input.text().lower():
            cursor.insertText(self.replace_input.text())
        self._find_next()

    def _replace_all(self):
        query = self.find_input.text()
        replacement = self.replace_input.text()
        if not query:
            return
        # Use QTextCursor to preserve undo history
        cursor = QTextCursor(self.code_editor.document())
        cursor.beginEditBlock()
        while True:
            found = self.code_editor.document().find(query, cursor)
            if found.isNull():
                break
            found.insertText(replacement)
            cursor = found
        cursor.endEditBlock()

    # ─── File I/O ────────────────────────────
    def _new_file(self):
        if not self._check_unsaved():
            return
        self.code_editor.clear()
        self.current_file = None
        self.has_unsaved_changes = False
        self._update_title()

    def _open_file(self):
        if not self._check_unsaved():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Diagram", "",
            "Diagram files (*.dgm);;Text files (*.txt);;All files (*)",
        )
        if path:
            self._load_file(path)

    def _load_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            try:
                data = json.loads(content)
                code = data.get("code", "")
                ss = data.get("settings", {})
                for key, slider in self._slider_widgets.items():
                    if key in ss:
                        slider.setValue(ss[key])
                if "color_scheme" in ss:
                    idx = self.scheme_combo.findText(ss["color_scheme"])
                    if idx >= 0:
                        self.scheme_combo.setCurrentIndex(idx)
            except json.JSONDecodeError:
                code = content
            self.code_editor.setPlainText(code)
            self.current_file = path
            self.has_unsaved_changes = False
            self._add_recent(path)
            self._update_title()
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def _save_file(self):
        if self.current_file:
            self._do_save(self.current_file)
        else:
            self._save_file_as()

    def _save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Diagram", "diagram.dgm",
            "Diagram files (*.dgm);;All files (*)",
        )
        if path:
            self._do_save(path)

    def _do_save(self, path):
        code = self.code_editor.toPlainText()
        self._apply_diagram_settings()
        data = {"version": 3, "code": code, "settings": dict(self._diagram_settings)}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.current_file = path
            self.has_unsaved_changes = False
            self._add_recent(path)
            self._update_title()
            self.status_label.setText(f"Saved: {path}")
        except Exception as ex:
            QMessageBox.critical(self, "Save Error", str(ex))

    def _check_unsaved(self):
        if not self.has_unsaved_changes:
            return True
        r = QMessageBox.question(
            self, "Unsaved Changes",
            "You have unsaved changes. Save before continuing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
        )
        if r == QMessageBox.Save:
            self._save_file()
            return not self.has_unsaved_changes
        return r == QMessageBox.Discard

    # ─── Recent Files ────────────────────────
    def _add_recent(self, path):
        recent = self.settings.value("recent_files", [], type=list)
        path = os.path.abspath(path)
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self.settings.setValue("recent_files", recent[:5])
        self._update_recent_menu()

    def _update_recent_menu(self):
        self.recent_menu.clear()
        recent = self.settings.value("recent_files", [], type=list)
        for p in recent:
            if os.path.isfile(p):
                act = QAction(os.path.basename(p), self)
                act.triggered.connect(lambda checked, fp=p: self._load_file(fp))
                self.recent_menu.addAction(act)
        if not recent:
            self.recent_menu.addAction("(empty)").setEnabled(False)

    # ─── Export ───────────────────────────────
    def _export_pdf(self):
        if not self._last_parsed or not self._last_parsed["objects"]:
            QMessageBox.warning(self, "Export", "No diagram to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "diagram.pdf", "PDF (*.pdf)")
        if path:
            self._apply_diagram_settings()
            PDFExporter.export(self._last_parsed, path, self._diagram_settings)
            self.status_label.setText(f"PDF: {path}")

    def _export_svg(self):
        rect = self.diagram_scene.itemsBoundingRect().adjusted(-40, -40, 40, 40)
        if rect.isEmpty():
            QMessageBox.warning(self, "Export", "No diagram to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export SVG", "diagram.svg", "SVG (*.svg)")
        if path:
            gen = QSvgGenerator()
            gen.setFileName(path)
            gen.setSize(rect.size().toSize())
            gen.setViewBox(rect)
            painter = QPainter(gen)
            painter.setRenderHint(QPainter.Antialiasing)
            self.diagram_scene.render(painter, QRectF(), rect)
            painter.end()
            self.status_label.setText(f"SVG: {path}")

    def _export_png(self):
        rect = self.diagram_scene.itemsBoundingRect().adjusted(-40, -40, 40, 40)
        if rect.isEmpty():
            QMessageBox.warning(self, "Export", "No diagram to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export PNG", "diagram.png", "PNG (*.png)")
        if path:
            img = QImage(rect.size().toSize() * 2, QImage.Format_ARGB32)
            img.fill(Qt.white)
            painter = QPainter(img)
            painter.setRenderHint(QPainter.Antialiasing)
            self.diagram_scene.render(painter, QRectF(), rect)
            painter.end()
            img.save(path, "PNG")
            self.status_label.setText(f"PNG: {path}")

    def _copy_diagram(self):
        rect = self.diagram_scene.itemsBoundingRect().adjusted(-40, -40, 40, 40)
        if rect.isEmpty():
            return
        img = QImage(rect.size().toSize() * 2, QImage.Format_ARGB32)
        img.fill(Qt.white)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        self.diagram_scene.render(painter, QRectF(), rect)
        painter.end()
        QApplication.clipboard().setImage(img)
        self.status_label.setText("Copied diagram to clipboard!")
        QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))

    # ─── Helpers ─────────────────────────────
    def _update_title(self):
        name = os.path.basename(self.current_file) if self.current_file else "Untitled"
        prefix = "\u2022 " if self.has_unsaved_changes else ""
        self.setWindowTitle(f"{prefix}Diagram Editor \u2014 {name}")

    def _set_scheme(self, name):
        idx = self.scheme_combo.findText(name)
        if idx >= 0:
            self.scheme_combo.setCurrentIndex(idx)

    # ─── Insert templates ────────────────────
    _insert_counter = 0

    def _next_name(self, prefix="obj"):
        DiagramEditor._insert_counter += 1
        return f"{prefix}_{DiagramEditor._insert_counter}"

    def _next_step(self):
        """Find the highest step in current code + 1."""
        if self._last_parsed and self._last_parsed["objects"]:
            return max(o["step"] for o in self._last_parsed["objects"]) + 1
        return 1

    def _insert_template(self, kind):
        """Insert a fully functional code template at the editor cursor.

        Every inserted object gets a unique name and a valid step so it
        renders immediately.  Containers come pre-populated with a child
        object.  Connectors reference the two most recently defined
        objects so the edge is visible right away.
        """
        step = self._next_step()

        # Find two most recent object names for connectors
        src, tgt = "source", "target"
        if self._last_parsed and len(self._last_parsed["objects"]) >= 2:
            names = [o["name"] for o in self._last_parsed["objects"]]
            src, tgt = names[-2], names[-1]
        elif self._last_parsed and len(self._last_parsed["objects"]) == 1:
            src = tgt = self._last_parsed["objects"][0]["name"]

        # First existing object name (for notes)
        first_obj = src

        templates = {
            # Containers — pre-populated with a child so they render
            'swimlane': lambda: (
                f'swimlane "{self._next_name("Lane")}" {{\n'
                f'    [rect] {self._next_name("task")} "New Task" step:{step} type:process\n'
                f'}}'
            ),
            'box': lambda: (
                f'box "{self._next_name("Box")}" {{fill: #313244, stroke: #89b4fa}} {{\n'
                f'    [rect] {self._next_name("item")} "New Item" step:{step} type:process\n'
                f'}}'
            ),
            'group': lambda: (
                f'group "{self._next_name("Group")}" {{\n'
                f'    {src}\n'
                f'    {tgt}\n'
                f'}}'
            ),
            # Shapes — all fully defined with step + type
            'rect': lambda: f'[rect] {self._next_name("process")} "New Process" step:{step} type:process',
            'rounded': lambda: f'[rounded] {self._next_name("task")} "New Task" step:{step} type:process',
            'diamond': lambda: f'[diamond] {self._next_name("decision")} "Yes or No?" step:{step} type:decision',
            'circle': lambda: f'[circle] {self._next_name("event")} "Start" step:{step} type:start',
            'parallelogram': lambda: f'[parallelogram] {self._next_name("data")} "Input Data" step:{step} type:input',
            'hexagon': lambda: f'[hexagon] {self._next_name("prep")} "Setup" step:{step} type:process',
            'cylinder': lambda: f'[cylinder] {self._next_name("db")} "Data Store" step:{step} type:datastore',
            'stadium': lambda: f'[stadium] {self._next_name("terminal")} "End" step:{step} type:end',
            # Connections — reference real objects
            'arrow': lambda: f'{src} -> {tgt} : "flow"',
            'dashed_arrow': lambda: f'{src} --> {tgt} : "optional"',
            'thick_arrow': lambda: f'{src} ==> {tgt} : "critical"',
            'solid_line': lambda: f'{src} --- {tgt}',
            'dotted_line': lambda: f'{src} -.- {tgt}',
            # Note — references a real object
            'note': lambda: f'note "Annotation" [{first_obj}]',
        }
        gen = templates.get(kind)
        if not gen:
            return
        snippet = gen()
        cursor = self.code_editor.textCursor()
        if cursor.positionInBlock() > 0:
            cursor.movePosition(QTextCursor.EndOfBlock)
            cursor.insertText("\n")
        cursor.insertText(snippet + "\n")
        self.code_editor.setTextCursor(cursor)
        self.code_editor.setFocus()
        self._schedule_update()

    def _load_example(self):
        self.code_editor.setPlainText(EXAMPLE_CODE)
        self.current_file = None
        self.has_unsaved_changes = False
        self._update_title()

    def _show_help(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Syntax Reference")
        dlg.resize(700, 700)
        layout = QVBoxLayout(dlg)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 11))
        text.setPlainText(HELP_TEXT)
        layout.addWidget(text)
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.close)
        layout.addWidget(btn)
        dlg.exec()

    def _show_llm_prompt(self):
        """Show the LLM instruction set and copy it to clipboard."""
        QApplication.clipboard().setText(LLM_PROMPT)

        dlg = QDialog(self)
        dlg.setWindowTitle("LLM Diagram Prompt \u2014 Copied to clipboard!")
        dlg.resize(800, 750)
        layout = QVBoxLayout(dlg)

        header = QLabel("\u2705  Copied to clipboard. Paste this into any LLM to generate diagrams.")
        header.setStyleSheet("color: #a6e3a1; font-size: 12pt; font-weight: bold; padding: 8px;")
        layout.addWidget(header)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 10))
        text.setPlainText(LLM_PROMPT)
        layout.addWidget(text)

        btn_row = QHBoxLayout()
        btn_copy = QPushButton("Copy Again")
        btn_copy.clicked.connect(lambda: (
            QApplication.clipboard().setText(LLM_PROMPT),
            self.statusBar().showMessage("LLM prompt copied to clipboard!", 2000),
        ))
        btn_row.addWidget(btn_copy)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.close)
        btn_row.addWidget(btn_close)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        dlg.exec()

    def _show_about(self):
        QMessageBox.about(self, "About Diagram Editor",
                          "Diagram Editor v3.0\n\n"
                          "Step-based code-to-diagram tool\n"
                          "with bidirectional editing.\n\n"
                          "Built with PySide6 + fpdf2")

    def _on_error_clicked(self, item):
        text = item.text()
        m = re.match(r"Line (\d+):", text)
        if m:
            ln = int(m.group(1))
            cursor = self.code_editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, ln - 1)
            self.code_editor.setTextCursor(cursor)
            self.code_editor.centerCursor()
            self.code_editor.setFocus()

    # ─── State Persistence ───────────────────
    def _load_persisted_state(self):
        geo = self.settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
        scheme = self.settings.value("color_scheme", "Default")
        idx = self.scheme_combo.findText(scheme)
        if idx >= 0:
            self.scheme_combo.setCurrentIndex(idx)
        for key, slider in self._slider_widgets.items():
            val = self.settings.value(f"setting_{key}")
            if val is not None:
                slider.setValue(int(val))

    def closeEvent(self, event):
        if not self._check_unsaved():
            event.ignore()
            return
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("color_scheme", self.scheme_combo.currentText())
        for key, slider in self._slider_widgets.items():
            self.settings.setValue(f"setting_{key}", slider.value())
        event.accept()

    # ─── Event Filter (Escape in filter) ─────
    def eventFilter(self, obj, event):
        if obj is self.filter_field and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_Escape:
                self._clear_filter()
                self.code_editor.setFocus()
                return True
        return super().eventFilter(obj, event)


# ═══════════════════════════════════════════════
#  Entry Point
# ═══════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DiagramEditor")
    app.setOrganizationName("DiagramEditor")
    window = DiagramEditor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
