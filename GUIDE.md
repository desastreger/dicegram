# Dicegram — Complete Guide

> **Note.** The product is now **Dicegram**, a web app (SvelteKit + FastAPI).
> The DSL grammar documented here is shared between the current web app and the
> archived desktop PySide6 version (preserved on tag `v3.0-desktop-final` /
> branch `archive/pyside-desktop`). Where the two diverge the web app is
> authoritative — see [README.md](README.md) for web-app usage, dev runner,
> keybindings, and feature list; see [CHANGELOG.md](CHANGELOG.md) for history.
>
> Sections below that mention specific UI ("Select mode", "Draw palette",
> "`DiagramEditor.bat`", PyInstaller builds) are desktop-only and kept for
> reference until the desktop app is removed.

## Overview

Dicegram turns plain-text DSL into live architecture diagrams. You write code
in the editor and see the diagram update; you can also drag shapes on the
canvas and the DSL rewrites surgically to match. Code, canvas, inspector, and
dicetree are four windows into the same source file — edits on one surface
propagate to the others. Think of it as Mermaid meets Visio — the precision of
code with the interactivity of a visual editor.

**Web stack:** FastAPI + SQLModel + SQLite; SvelteKit 2 + Svelte 5 + Tailwind
v4 + Svelte Flow + CodeMirror 6.  
**Desktop stack (archived):** Python 3.10+, PySide6 (Qt), fpdf2 — single file
`diagram_app.py`.

---

## Quick Start

### Web app (current)

Double-click `reset-dev.bat` at the repo root — it hard-resets any running
dev servers, starts the FastAPI backend on `:8000` and the SvelteKit frontend
on `:5173`, then opens http://localhost:5173 in your browser. First time
through, run `start-dev.bat` once instead to create the Python venv and
`npm install` the frontend deps. See [README.md](README.md) for a manual
two-terminal setup and the full feature list.

### Desktop app (archived)

The sections below document the desktop version preserved on tag
`v3.0-desktop-final` / branch `archive/pyside-desktop`:

### From Source
```bash
pip install pyside6 fpdf2
python run.py
```

### Windows Launcher (no terminal needed)
Double-click `DiagramEditor.bat` — it finds Python, installs dependencies if needed, and launches.

### Standalone Executable (no Python needed)
Build with `python build_exe.py`, then run `dist/DiagramEditor/DiagramEditor.exe`.

### Build Your Own Executable
```bash
python build_exe.py
```
Output: `dist/DiagramEditor/DiagramEditor.exe`

### Troubleshooting Installation

**`pip install pyside6` fails or PySide6 won't import:**
- PySide6 requires Python 3.10 or newer. Check with `python --version`.
- On Linux, you may need system packages: `sudo apt install libgl1-mesa-glx libegl1` (Ubuntu/Debian) or equivalent for your distro.
- If you have multiple Python versions, ensure you're using the right one: `python3.10 -m pip install pyside6 fpdf2`.

**Application launches but the window is blank or crashes immediately:**
- Make sure your graphics drivers are up to date. PySide6 uses OpenGL by default.
- Try setting the environment variable `QT_QUICK_BACKEND=software` before launching to force software rendering.

**`ModuleNotFoundError: No module named 'fpdf'`:**
- Install with `pip install fpdf2` (note: the package is `fpdf2`, not `fpdf`).

**Windows: `python` is not recognized:**
- Ensure Python is added to your PATH during installation, or use the full path (e.g., `C:\Python312\python.exe run.py`).
- Alternatively, use `DiagramEditor.bat` which auto-detects common Python install locations.

**macOS/Linux: untested platform issues:**
- The application is developed and tested on Windows. PySide6 is cross-platform, but minor rendering or font differences may occur on macOS/Linux.
- On macOS, you may need to allow the app in System Preferences > Security & Privacy if Gatekeeper blocks it.

**Build executable fails (`python build_exe.py`):**
- PyInstaller must be installed: `pip install pyinstaller`.
- Some antivirus software flags PyInstaller output as suspicious — add an exclusion for the `dist/` directory.

---

## Project Files

| File | Purpose |
|------|---------|
| `run.py` | Entry point — never changes |
| `diagram_app.py` | All application code (single file) |
| `requirements.txt` | Python dependencies |
| `DiagramEditor.bat` | Windows launcher with auto-install |
| `build_exe.py` | PyInstaller build script |
| `examples/` | Sample diagram files (.dgm and .txt) |
| `README.md` | Quick readme |
| `GUIDE.md` | This document |

---

## User Interface

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Menu Bar (File, Edit, Insert, View, Help)                   │
├─────────────────────────────────────────────────────────────┤
│  Toolbar (file ops, export, modes, undo/redo, filter)        │
├──────────┬────────────────────┬──────────────────────────────┤
│ Settings │    Code Editor     │        Preview               │
│ (dock)   │                    │     (QGraphicsScene)         │
│          │  Syntax-highlighted│                              │
│ Direction│  code with line    │   Live-rendered diagram      │
│ Sliders  │  numbers and error │   with nodes, edges,         │
│ Scheme   │  gutter            │   swimlanes, step bands     │
│ Grid     │                    │                              │
│ Steps    │  ┌──────────────┐  │   Zoom/pan/select/connect   │
│          │  │ Error Panel  │  │                              │
│          │  └──────────────┘  ├──────────────────────────────┤
│          │                    │  Drawing Palette (3 rows)    │
├──────────┴────────────────────┴──────────────────────────────┤
│  Status Bar (objects, connections, swimlanes, steps, zoom)   │
└─────────────────────────────────────────────────────────────┘
```

### Panels

- **Settings Dock** (left) — resizable, dockable, floatable. Direction, sizing sliders, color scheme, grid/step toggles.
- **Code Editor** (center) — syntax-highlighted, line numbers, red error gutter, find bar, autocomplete.
- **Preview** (right) — QGraphicsScene with zoom (Ctrl+wheel), pan (H mode), node selection, drag-to-move, drag-to-connect.
- **Drawing Palette** (bottom of preview) — 3 rows of insert buttons: Containers, Shapes, Connectors.
- **Error Panel** (bottom of editor) — clickable list of parse errors, collapsible.

---

## DSL Syntax

### Objects (Nodes)

```
[shape] unique_name "Display Label" step:N [attributes...] [{style}] [@(x,y)]
```

**Shapes** (with conventional meanings):

| Shape | Syntax | Meaning (Visio/BPMN) |
|-------|--------|---------------------|
| Rectangle | `[rect]` | Process / activity / task |
| Rounded | `[rounded]` | Sub-process / alternate task |
| Diamond | `[diamond]` | Decision / gateway |
| Circle | `[circle]` | Start or end event |
| Parallelogram | `[parallelogram]` | Data input / output |
| Hexagon | `[hexagon]` | Preparation / setup |
| Cylinder | `[cylinder]` | Database / data store |
| Stadium | `[stadium]` | Terminal / boundary |

**Step** (`step:N`) is required. Objects sharing the same step number are placed in the same row/column (parallel). Lower step numbers are placed earlier in the flow direction.

**Labels** are auto-capitalized. Use `\n` for multi-line: `"First Line\nSecond Line"`.

### Attributes (All Optional)

| Attribute | Values | Effect |
|-----------|--------|--------|
| `type:` | process, decision, input, output, datastore, start, end, manual, automated, approval, external | Semantic category, shown in tooltip |
| `owner:"name"` | any string | Responsibility assignment |
| `status:` | draft, active, deprecated, blocked, complete | Visual: draft=dashed, blocked=red, deprecated=strikethrough, complete=checkmark |
| `tags:"a, b"` | comma-separated | Freeform labels, searchable via filter |
| `priority:` | low, medium, high, critical | Visual: critical=thick red border, low=thin muted |
| `id:N` | integer | External reference number |

Unknown attribute keys are accepted and stored (extensible).

### Style Overrides

```
[rect] node "Label" step:1 {fill: #a6e3a1, stroke: #2d6a2d, text: #000000}
```

### Connections

| Syntax | Type | Meaning (BPMN) |
|--------|------|----------------|
| `A -> B` | Solid arrow | Sequence flow |
| `A --> B` | Dashed arrow | Message / conditional flow |
| `A ==> B` | Thick arrow | Critical path |
| `A --- B` | Solid line | Association |
| `A -.- B` | Dotted line | Dependency |

**Labels:** `A -> B : "label text"`  
**Placement:** `A -> B : "label" [above]` / `[below]` / `[center]`  
**Attributes:** `A -> B condition:"expr" weight:5`  
**Self-loops:** `A -> A : "retry"`

Connections are written outside swimlane blocks and reference objects by name across any swimlane.

### Swimlanes

```
swimlane "Department Name" {
    [rect] task1 "Task One" step:1 type:process
    [rect] task2 "Task Two" step:2 type:process
}
```

- In **top-to-bottom**: swimlanes are vertical columns, arranged left to right
- In **left-to-right**: swimlanes are horizontal rows, arranged top to bottom
- Objects outside any swimlane go in a "free" area

### Boxes (Sub-Containers)

```
box "Automated Tests" {fill: #313244, stroke: #89b4fa} {
    [rect] unit "Unit Tests" step:5
    [rect] integration "Integration" step:5
}
```

Boxes live inside swimlanes for color-coded sub-grouping.

### Groups (Visual Overlay)

```
group "Sprint 1" {
    task1
    task2
}
```

Groups draw a dashed border around referenced objects. They don't own or contain — they're a visual annotation that can span swimlanes.

### Notes

```
note "Important info" [object_name]
```

Draws a sticky note attached to the target object.

### Direction

```
direction top-to-bottom
```

Values: `top-to-bottom` (default), `left-to-right`, `bottom-to-top`, `right-to-left`  
Shorthand also accepted: `TB`, `LR`, `BT`, `RL`

Changing direction in the code updates the settings panel, and vice versa.

### Position Pins

```
[rect] node "Label" step:1 @(350, 200)
```

Written automatically when you drag a node. Overrides auto-layout for that node.

### Comments

```
// This is a comment
```

---

## Interaction Modes

Three mutually exclusive modes, toggled via toolbar buttons or keyboard:

| Mode | Key | Cursor | Behavior |
|------|-----|--------|----------|
| **Select** | V | Arrow | Click to select nodes, drag to move them, rubber-band selection on empty space |
| **Pan** | H | Hand | Drag anywhere to scroll the canvas |
| **Connect** | C | Crosshair | Click a node, drag to another to create a `->` connection |

### Zoom & Navigation

- **Ctrl + Mouse Wheel** — zoom in/out (0.1x to 5.0x)
- **Mouse Wheel** — vertical scroll
- **Double-click empty space** — fit diagram to view
- **Ctrl+0** — zoom to fit
- **Ctrl+1** — actual size (100%)
- **Ctrl+=** / **Ctrl+-** — zoom in / out

### Bidirectional Editing

- **Drag a node** → writes `@(x,y)` to the code, only on mouse release, using a surgical single-line edit
- **Drag from port to port** (Connect mode) → writes `name1 -> name2` to the code
- **Change direction in settings** → writes `direction left-to-right` to the code
- **Change direction in code** → updates the settings combo
- **All edges auto-follow** when nodes move (DiagramEdge is a live tethered object)
- Snap-to-grid (10px) on all drag operations

---

## Filter / Search System

The filter field in the toolbar accepts queries:

| Query | Matches |
|-------|---------|
| `type:decision` | All decision nodes |
| `owner:alice` | Objects owned by alice |
| `tags:mvp` | Objects tagged "mvp" |
| `status:blocked` | All blocked nodes |
| `step:5` | All objects at step 5 |
| `alice` | Free text across name, label, owner, tags |
| `type:decision,process` | OR: decision or process |
| `type:decision owner:alice` | AND: both must match |

Filtering dims non-matching objects to 15% opacity. Layout doesn't change. Clear with Escape.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New file |
| Ctrl+O | Open file |
| Ctrl+S | Save file |
| Ctrl+Shift+S | Save as |
| Ctrl+P | Export PDF |
| Ctrl+E | Export SVG |
| Ctrl+Shift+E | Export PNG |
| Ctrl+Shift+C | Copy diagram to clipboard |
| Ctrl+Z | Undo |
| Ctrl+Shift+Z | Redo |
| Ctrl+F | Find |
| Ctrl+H | Find & Replace |
| Ctrl+/ | Focus filter field |
| Ctrl+0 | Zoom to fit |
| Ctrl+1 | Actual size |
| Ctrl+Shift+L | Copy LLM prompt to clipboard |
| V | Select mode |
| H | Pan mode |
| C | Connect mode |
| F1 | Syntax reference |
| Escape | Close find bar / clear filter |

---

## Color Schemes

Seven built-in schemes: **Default**, **Blueprint**, **Warm**, **Monochrome**, **Dark**, **Synthwave**, **Forest**.

Each scheme defines colors for: node fill/stroke/text, edge stroke/label, swimlane fill/stroke/header, canvas background, step band even/odd, note fill/stroke/text, port color, box fill/stroke, shadow.

Change via Settings dock or View > Color Scheme menu.

---

## Export Formats

| Format | Method | Details |
|--------|--------|---------|
| **PDF** | Ctrl+P / File > Export PDF | fpdf2-based, per-node sizes, proper shapes, color-scheme aware |
| **SVG** | Ctrl+E / File > Export SVG | QSvgGenerator, vector output |
| **PNG** | Ctrl+Shift+E / File > Export PNG | QImage at 2x resolution |
| **Clipboard** | Ctrl+Shift+C | Copies diagram as image to system clipboard |

---

## LLM Prompt

**Help > Copy LLM Prompt** (or Ctrl+Shift+L) copies a complete instruction set to the clipboard. Paste it into any LLM (ChatGPT, Claude, etc.) and ask it to generate a diagram — the output can be pasted directly into the code editor.

---

## Save File Format

`.dgm` files are JSON:

```json
{
  "version": 3,
  "code": "direction top-to-bottom\n...",
  "settings": {
    "node_width": 140,
    "node_height": 50,
    "h_gap": 60,
    "v_gap": 70,
    "font_size": 11,
    "container_padding": 20,
    "swimlane_gap": 10,
    "color_scheme": "Default"
  }
}
```

Plain text files (`.txt`) are also supported — treated as raw DSL code without settings.

---

## Architecture Notes

### Single File
All code lives in `diagram_app.py`. This is intentional — the user explicitly wants no package splitting.

### Key Classes

| Class | Purpose |
|-------|---------|
| `DiagramEditor(QMainWindow)` | Main window, menus, toolbar, settings dock, wiring |
| `DiagramScene(QGraphicsScene)` | Renders the diagram, handles mouse events for connect mode |
| `DiagramView(QGraphicsView)` | Zoom, pan, mode management |
| `DiagramNode(QGraphicsItem)` | A single shape node with paint, ports, tooltip, drag |
| `DiagramEdge(QGraphicsItem)` | A live connection tethered to source/target nodes |
| `CodeEditor(QPlainTextEdit)` | Editor with line numbers, error gutter, syntax highlighting |
| `DiagramHighlighter(QSyntaxHighlighter)` | Syntax coloring for the DSL |
| `AutocompletePopup` | Not yet a QCompleter, built via the old approach (to be upgraded) |
| `PDFExporter` | fpdf2-based PDF export with per-node sizes and color schemes |

### Key Functions

| Function | Purpose |
|----------|---------|
| `parse_diagram(code)` | Parses DSL → structured dict with objects, connections, swimlanes, etc. |
| `compute_layout(parsed, settings)` | Computes grid layout with positions, swimlane rects, step bands |
| `_measure_node(label, shape, w, h)` | Auto-sizes a node to fit its text content |
| `_snap_to_grid(val, grid_size)` | Snaps a coordinate to the nearest grid increment |
| `parse_filter_query(query)` | Parses filter field text into structured terms |
| `object_matches_filter(obj, terms)` | Tests if an object matches filter criteria |
| `hex_to_rgb(h)` / `hex_to_qcolor(h)` | Color conversion helpers |

### Bidirectional Sync Flow

```
CODE CHANGED → parse → layout → render scene
                                    ↑ suppress flags prevent loops
NODE DRAGGED → surgical QTextCursor edit on release only → re-parse (no re-render)
PORT DRAG    → append connection line to code → re-parse + re-render
DIRECTION    → settings combo writes to code / code updates combo
```

---

## Development History (April 13, 2026)

1. **Started as HTML/JS** with CodeMirror + dagre + jsPDF. User wanted desktop instead.
2. **Rebuilt as Python/tkinter** with custom canvas renderer, fpdf2 PDF export.
3. **User requests accumulated**: timeline phases, symbol toolbar, autocomplete, save/load, syntax highlighting, color schemes, drag-to-move, connection ports.
4. **Massive spec received**: complete DSL redesign with step-based tree structure, rich attributes, swimlane hierarchy, bidirectional editing, QGraphicsScene rendering.
5. **Rebuilt as PySide6** — new parser, layout engine, QGraphicsScene, DiagramNode/DiagramEdge classes, all menus and toolbars.
6. **Visual fixes**: layout engine overhauled multiple times (upside-down swimlanes, node overlap, edge routing through nodes, text overflow in shapes).
7. **Bidirectional editing**: drag-to-move writes @(x,y) to code, drag-to-connect writes connection lines, direction sync between code and settings.
8. **Interaction modes**: Select (V), Pan (H), Connect (C) with toolbar toggles.
9. **Node auto-sizing**: shapes inflate to fit their text content with shape-specific adjustments.
10. **Connection hit-testing**: area search with expanding radius to reliably find target nodes.
11. **Direction support**: native LR/RL layout (not rotated TB) with horizontal swimlane rows and vertical step bands.
12. **Auto-capitalize**: all label words start with capitals.
13. **Grid system**: visible 20px grid, 10px snap on drag.
14. **PDF exporter**: rewritten to use per-node sizes, proper shapes, edge clipping, centered text.
15. **LLM prompt**: complete DSL instruction set with working example, copyable to clipboard.
16. **Standalone exe**: PyInstaller build with fontTools/fpdf2 data included.
