"""Branding palette — Dicegram-tunable default colors for diagram elements.

Every Dicegram declares a *theme* (via `setting color_scheme <id>`). The theme
ships its own baseline palette. The user's personal brand palette (stored on
the user row) overlays the theme baseline. Inline DSL styles
(e.g. `{fill:#abc123}`) and per-Dicegram setting overrides (e.g.
`setting palette_node_fill #fff`) win above that, so a single Dicegram can
deviate without touching the user's brand defaults.

Tokens cover:
  - type fills: one per `type:<value>` the parser understands
  - node defaults: fill / stroke / text when no type matches
  - edges: stroke, label colour
  - priority / status strokes: accents applied via attrs
"""

from __future__ import annotations

import re
from typing import Any

# Strict CSS-color shape — refuses anything that could land in an SVG
# attribute as raw HTML. The previous prefix-only check ("starts with #
# / rgb / hsl") let a payload like `#"><script>` through, which then
# rendered literal `<script>` in every export. Any colour the user can
# legitimately set passes; everything else is dropped silently.
_COLOR_RE = re.compile(
    r"^("
    r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})"  # #rgb / #rgba / #rrggbb / #rrggbbaa
    r"|rgb\(\s*[^)<>\"']+\)"
    r"|rgba\(\s*[^)<>\"']+\)"
    r"|hsl\(\s*[^)<>\"']+\)"
    r"|hsla\(\s*[^)<>\"']+\)"
    r"|oklch\(\s*[^)<>\"']+\)"
    r"|color\(\s*[^)<>\"']+\)"
    r"|color-mix\(\s*[^)<>\"']+\)"
    r"|[a-zA-Z]{3,30}"  # named colors (red, transparent, currentColor, …)
    r")$"
)


def _is_safe_color(value: str) -> bool:
    """Reject any colour string that contains characters that could
    break out of an SVG attribute. Whitelist common functional colour
    forms; everything else is dropped at the boundary."""
    if not value or len(value) > 80:
        return False
    if any(c in value for c in "<>\"'`"):
        return False
    return _COLOR_RE.match(value) is not None


# Default-Dark — the "no theme picked" baseline. Mirrors the chrome's
# default-dark theme. Frontend `palette.svelte.ts` and `themes.ts`
# (chrome) and `dsl/export_svg.py` (SVG export) must stay in sync.
DEFAULT_DARK_PALETTE: dict[str, str] = {
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
    # Node default fill / stroke / text.
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


# Warm palette — cream canvas, salmon terminals, sage green for
# processes/automated, lavender for decisions/gates, soft warm grays
# for edges and chrome. Intentionally light/airy.

WARM_PALETTE: dict[str, str] = {
    # Type fills.
    "type_start": "#fce4d6",         # salmon pill
    "type_end": "#fce4d6",
    "type_decision": "#e6e3f7",      # lavender for gates / decisions
    "type_datastore": "#dde6f0",     # soft blue-gray
    "type_process": "#dceadb",       # sage green
    "type_input": "#fce4d6",         # input == terminal-ish, salmon pill
    "type_output": "#fce4d6",
    "type_manual": "#dceadb",
    "type_automated": "#dceadb",
    "type_approval": "#e6e3f7",
    "type_external": "#fce4d6",
    # Node default fill / stroke / text.
    "node_fill": "#dceadb",          # sage green default — most boxes are LLM/process
    "node_stroke": "#a8c2a3",        # muted sage outline
    "node_text": "#3d5c3a",          # deep sage text
    # Priority strokes.
    "priority_critical": "#c44536",
    "priority_high": "#d4863b",
    # Status strokes / text.
    "status_blocked": "#c44536",
    "status_complete": "#5b8060",
    "status_deprecated_text": "#8a8780",
    # Edges.
    "edge": "#8a8a82",               # warm gray, like the screenshots
    "edge_label": "#3d3d35",
}

# `auto` — the palette an unpinned dicegram gets.
#
# On canvas these are `color-mix(in srgb, var(--app-ok) 24%, var(--app-bg))`
# style expressions that track the chrome (see AUTO_PALETTE in
# frontend/src/lib/palette.svelte.ts). A static SVG cannot evaluate those, so
# the export used to fall back to WARM — which assigns *different* colours per
# type. Same document, two looks: on canvas a start node was sage green and an
# end node rose (go/stop); in the export both came out the same salmon, losing
# the distinction entirely.
#
# These values are those canvas expressions RESOLVED against the light chrome,
# sampled from the running app rather than eyeballed. Layered over WARM so the
# surface chrome `auto` leaves to CSS (lane / box / note backgrounds) keeps the
# warm look that already matched. Re-sample if the --app-* tokens change.
AUTO_PALETTE: dict[str, str] = {
    **WARM_PALETTE,
    # Type fills — canvas colour-mix() expressions resolved on light chrome.
    "type_start": "#d1d7c9",         # sage  (--app-ok 24%)   "go"
    "type_end": "#ecccc3",           # rose  (--app-danger 22%) "stop"
    "type_decision": "#edd6bb",      # amber (--app-warn 26%)
    "type_datastore": "#eed6ca",     # accent 18%
    "type_process": "#e3d6bd",       # --app-surface-2
    "type_input": "#f0ddd2",
    "type_output": "#f0ddd2",
    "type_manual": "#e3d6bd",
    "type_automated": "#dfe1d5",
    "type_approval": "#f1e0cb",
    "type_external": "#f2e1d6",
    # Node default fill / stroke / text.
    "node_fill": "#e3d6bd",
    "node_stroke": "#9a8771",
    "node_text": "#1f1a16",
    # Priority strokes.
    "priority_critical": "#b8392a",
    "priority_high": "#c47a2a",
    # Status strokes / text.
    "status_blocked": "#b8392a",
    "status_complete": "#4d7553",
    "status_deprecated_text": "#6b5f53",
    # Edges.
    "edge": "#5a5048",
    "edge_label": "#1f1a16",
}


# Light — clean light theme baseline (existing behavior, just centralized).
LIGHT_PALETTE: dict[str, str] = {
    "type_start": "#bbf7d0",
    "type_end": "#fecaca",
    "type_decision": "#fde68a",
    "type_datastore": "#bfdbfe",
    "type_process": "",
    "type_input": "",
    "type_output": "",
    "type_manual": "",
    "type_automated": "",
    "type_approval": "",
    "type_external": "",
    "node_fill": "#f8fafc",
    "node_stroke": "#475569",
    "node_text": "#0f172a",
    "priority_critical": "#dc2626",
    "priority_high": "#d97706",
    "status_blocked": "#dc2626",
    "status_complete": "#059669",
    "status_deprecated_text": "#9ca3af",
    "edge": "#475569",
    "edge_label": "#0f172a",
}


# Theme id -> baseline palette. The id matches the chrome theme id in
# frontend/src/lib/themes.ts so a single `setting color_scheme <id>`
# directive picks both chrome and palette together.
THEME_PRESETS: dict[str, dict[str, str]] = {
    "warm": WARM_PALETTE,
    "warm_dark": DEFAULT_DARK_PALETTE,
    "warm-dark": DEFAULT_DARK_PALETTE,
    "default-dark": DEFAULT_DARK_PALETTE,
    "default_dark": DEFAULT_DARK_PALETTE,
    "dark": DEFAULT_DARK_PALETTE,
    "dracula": DEFAULT_DARK_PALETTE,
    "gruvbox": DEFAULT_DARK_PALETTE,
    "gruvbox_dark": DEFAULT_DARK_PALETTE,
    "gruvbox-dark": DEFAULT_DARK_PALETTE,
    "high_contrast": DEFAULT_DARK_PALETTE,
    "high-contrast": DEFAULT_DARK_PALETTE,
    "solarized_dark": DEFAULT_DARK_PALETTE,
    "solarized-dark": DEFAULT_DARK_PALETTE,
    "solarized_light": LIGHT_PALETTE,
    "solarized-light": LIGHT_PALETTE,
    "light": LIGHT_PALETTE,
    # `auto` on the canvas tracks chrome via CSS variables, but a static
    # SVG export has to commit to one palette. See AUTO_PALETTE above —
    # these are the canvas's own colour-mix() expressions resolved against
    # the light chrome, so screen and export finally agree.
    "auto": AUTO_PALETTE,
}

# Default-Dark remains the palette *shape* reference (ALLOWED_KEYS below is
# derived from its keys), but it is no longer the default theme.
DEFAULT_PALETTE = DEFAULT_DARK_PALETTE

# Unconfigured dicegrams resolve to `auto` → warm-light, matching both the
# note above ("unconfigured dicegrams ship as the warm-on-cream look") and
# the frontend's own DEFAULT_THEME_ID in src/lib/themes.ts.
#
# This used to be "default-dark", which defeated that intent: the `auto`
# mapping only applied to documents that explicitly wrote
# `setting color_scheme auto`, so a document with no color_scheme line at
# all — the landing-page example, and anything an LLM writes — exported as a
# black diagram while the editor showed it light.
DEFAULT_THEME_ID = "auto"

# All keys clients are allowed to PUT. Anything else is silently dropped.
ALLOWED_KEYS: frozenset[str] = frozenset(DEFAULT_PALETTE.keys())


def theme_palette(theme_id: str | None) -> dict[str, str]:
    """Return the baseline palette for a theme id (case-insensitive). Falls
    back to DEFAULT_THEME_ID when the id is unknown or empty.

    This must resolve the empty id the SAME way `merge_palette` resolves the
    surface chrome below — both go through DEFAULT_THEME_ID. They used to
    disagree: this function fell back to DEFAULT_PALETTE (dark) while the
    chrome fell back to DEFAULT_THEME_ID, so an unthemed document rendered a
    light page with dark node fills — a half-applied theme that looked worse
    than either one applied consistently.
    """
    key = (theme_id or DEFAULT_THEME_ID).strip().lower()
    return dict(
        THEME_PRESETS.get(key)
        or THEME_PRESETS.get(DEFAULT_THEME_ID)
        or DEFAULT_PALETTE
    )


def merge_palette(
    user_palette: dict[str, Any] | None,
    theme_id: str | None = None,
    dicegram_overrides: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Overlay user palette and per-Dicegram overrides on top of the theme
    baseline.

    Layering (lowest to highest precedence):
      1. theme baseline (`theme_palette(theme_id)`)
      2. user_palette  — the user's stored brand overrides
      3. dicegram_overrides — palette tweaks declared in a single Dicegram

    Empty-string values mean "inherit the lower layer"; non-string values
    and unknown keys are silently dropped. CSS-color shape is checked very
    lightly so the worst case is a refused override, never a broken render.
    """
    out = theme_palette(theme_id)
    for layer in (user_palette, dicegram_overrides):
        if not layer:
            continue
        for k, v in layer.items():
            if k not in ALLOWED_KEYS:
                continue
            if not isinstance(v, str):
                continue
            v = v.strip()
            if v == "":
                continue
            if not _is_safe_color(v):
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


def build_theme(
    user_palette: dict[str, Any] | None,
    theme_id: str | None = None,
    dicegram_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce a theme dict in the shape the SVG renderer expects, seeded
    from the named theme baseline and overlaid with user + Dicegram layers.
    """
    p = merge_palette(user_palette, theme_id=theme_id, dicegram_overrides=dicegram_overrides)
    type_fill: dict[str, str] = {}
    # Only emit type fills that are non-empty — empty string = inherit node_fill.
    for type_attr in (
        "start", "end", "decision", "datastore",
        "process", "input", "output", "manual", "automated", "approval", "external",
    ):
        v = p.get(f"type_{type_attr}", "")
        if v:
            type_fill[type_attr] = v

    # Surface chrome (lane / box / note backgrounds) varies by theme. The
    # warm / light themes want a paper-white surface; default-dark keeps
    # the existing slate look. Treat `auto` as warm for export — there's
    # no chrome to follow when the SVG is rendered server-side.
    norm_id = (theme_id or DEFAULT_THEME_ID).lower()
    is_dark = norm_id in {"default-dark", "default_dark", "dark", "dracula", "gruvbox", "gruvbox-dark", "gruvbox_dark", "high-contrast", "high_contrast", "solarized-dark", "solarized_dark", "warm-dark", "warm_dark"}
    if is_dark:
        bg = "#0a0a0a"
        lane_bg = "rgba(56,70,95,0.18)"
        lane_border = "#334155"
        lane_label = "#94a3b8"
        box_bg = "rgba(56,70,95,0.30)"
        box_border = "#475569"
        box_label = "#cbd5e1"
        edge_label_bg = "#0f172a"
        note_bg = "#fde68a"
        note_border = "#b45309"
        note_text = "#422006"
        note_leader = "#b45309"
        group_border = "#f59e0b"
        group_label = "#f59e0b"
        edge_label_text = p["edge_label"]
    else:
        # Warm light surface for the `warm` / `auto` themes; clean white
        # for `light` / `solarized-light`.
        warm_like = norm_id in {"warm", "auto"}
        bg = "#fbf7f2" if warm_like else "#ffffff"
        lane_bg = "rgba(217,119,87,0.06)"
        lane_border = "#e3d9cf"
        lane_label = "#6b6259"
        box_bg = "rgba(217,119,87,0.04)"
        box_border = "#d6cbc0"
        box_label = "#5a5048"
        edge_label_bg = bg
        note_bg = "#fef3c7"
        note_border = "#d4863b"
        note_text = "#5a3d0a"
        note_leader = "#d4863b"
        group_border = "#b8a48f"
        group_label = "#8a7a6a"
        # Force a dark edge-label text colour on light surfaces; the
        # palette's `edge_label` may be the dark-mode pale-grey value
        # (when a user mixed-and-matched), which would render unreadable
        # on the paper bg. Pick the brand text colour for warm/auto, the
        # light theme's deep-slate for everything else.
        edge_label_text = "#3d3d35" if warm_like else "#0f172a"

    return {
        "bg": bg,
        "lane_bg": lane_bg,
        "lane_border": lane_border,
        "lane_label": lane_label,
        "box_bg": box_bg,
        "box_border": box_border,
        "box_label": box_label,
        "group_border": group_border,
        "group_label": group_label,
        "note_bg": note_bg,
        "note_border": note_border,
        "note_text": note_text,
        "note_leader": note_leader,
        "node_fill": p["node_fill"],
        "node_stroke": p["node_stroke"],
        "node_text": p["node_text"],
        "edge": p["edge"],
        "edge_label": edge_label_text,
        "edge_label_bg": edge_label_bg,
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
