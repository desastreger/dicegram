"""Branding palette — user-tunable default colors for diagram elements.

The palette is stored per-user as JSON on the `user` row. DSL-inline styles
(e.g. `{fill:#abc123}`) always win; the palette only fills in defaults that
the DSL didn't specify. This keeps diagrams portable — exporting a diagram
authored against one palette and re-importing it under another produces a
re-coloured but structurally identical diagram.

Tokens cover:
  - type fills: one per `type:<value>` the parser understands
  - node defaults: fill / stroke / text when no type matches
  - edges: stroke, label colour
  - priority / status strokes: accents applied via attrs
"""

from __future__ import annotations

from typing import Any


# Shipped default palette. The canvas-side hardcoded colours in
# ShapeNode.svelte and the backend DARK_THEME in dsl/export_svg.py are
# derived from these values (and must be kept in sync).
DEFAULT_PALETTE: dict[str, str] = {
    # Type fills (maps directly to `type:<value>` attr).
    "type_start": "#064e3b",
    "type_end": "#3f1d1d",
    "type_decision": "#3a2f0b",
    "type_datastore": "#0c3a5c",
    "type_process": "",  # empty = fall through to node_fill
    "type_input": "",
    "type_output": "",
    "type_manual": "",
    "type_automated": "",
    "type_approval": "",
    "type_external": "",
    # Node default fill / stroke / text (used when DSL is silent and type has
    # no explicit colour).
    "node_fill": "#1f2937",
    "node_stroke": "#64748b",
    "node_text": "#e5e7eb",
    # Priority strokes.
    "priority_critical": "#ef4444",
    "priority_high": "#f59e0b",
    # Status strokes / text.
    "status_blocked": "#ef4444",
    "status_complete": "#10b981",
    "status_deprecated_text": "#71717a",
    # Edges.
    "edge": "#94a3b8",
    "edge_label": "#e5e7eb",
}


# All keys clients are allowed to PUT. Anything else is silently dropped.
ALLOWED_KEYS: frozenset[str] = frozenset(DEFAULT_PALETTE.keys())


def merge_palette(user_palette: dict[str, Any] | None) -> dict[str, str]:
    """Overlay the user palette on top of the default palette.

    Empty-string values from the user palette mean "inherit the default";
    anything else (including None) is ignored. Unknown keys are dropped.
    """
    out = dict(DEFAULT_PALETTE)
    if not user_palette:
        return out
    for k, v in user_palette.items():
        if k not in ALLOWED_KEYS:
            continue
        if not isinstance(v, str):
            continue
        v = v.strip()
        if v == "":
            continue
        # Very light validation: must look vaguely like a CSS colour.
        if not (v.startswith("#") or v.startswith("rgb") or v.startswith("hsl")):
            continue
        out[k] = v
    return out


def resolve_fill_for_type(palette: dict[str, str], type_attr: str | None) -> str | None:
    """Return the palette-provided fill for a `type:` attr, or None if the
    palette says "fall through to node_fill" (empty string)."""
    if not type_attr:
        return None
    key = f"type_{type_attr}"
    val = palette.get(key, "")
    return val if val else None


def build_theme(user_palette: dict[str, Any] | None) -> dict[str, Any]:
    """Produce a theme dict in the shape the SVG renderer expects, seeded
    from DARK_THEME-equivalent defaults and overlaid with the user palette.
    """
    p = merge_palette(user_palette)
    type_fill: dict[str, str] = {}
    # Only emit type fills that are non-empty — empty string = inherit node_fill.
    for type_attr in (
        "start", "end", "decision", "datastore",
        "process", "input", "output", "manual", "automated", "approval", "external",
    ):
        v = p.get(f"type_{type_attr}", "")
        if v:
            type_fill[type_attr] = v
    return {
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
        "node_fill": p["node_fill"],
        "node_stroke": p["node_stroke"],
        "node_text": p["node_text"],
        "edge": p["edge"],
        "edge_label": p["edge_label"],
        "edge_label_bg": "#0f172a",
        "type_fill": type_fill,
        "priority_stroke": {
            "critical": p["priority_critical"],
            "high": p["priority_high"],
        },
        "status_stroke": {
            "blocked": p["status_blocked"],
            "complete": p["status_complete"],
        },
        "status_text": {"deprecated": p["status_deprecated_text"]},
    }
