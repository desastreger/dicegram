# Diagram Editor — Project Memory

## Architecture
- **Single-file app**: All code in `diagram_app.py` (~4030 lines). This is intentional — do NOT split into packages.
- **Stack**: Python 3.10+, PySide6 (Qt), fpdf2 for PDF export.
- **Entry point**: `python run.py` (imports `diagram_app.main()`).
- **License**: Proprietary, closed-source, sole commercialization rights. See `LICENSE`.
- **Dependencies are LGPL-3.0** (PySide6, fpdf2) — dynamically linked, compliant. See `THIRD_PARTY_LICENSES.md`.

## Key Classes
- `DiagramEditor(QMainWindow)` — main window, menus, toolbar, settings dock, all wiring
- `DiagramScene(QGraphicsScene)` — renders diagram, handles mouse events for connect mode
- `DiagramView(QGraphicsView)` — zoom, pan, mode management (select/pan/connect)
- `DiagramNode(QGraphicsItem)` — single shape node with paint, ports, tooltip, drag
- `DiagramEdge(QGraphicsItem)` — live connection tethered to source/target nodes, caches path
- `CodeEditor(QPlainTextEdit)` — editor with line numbers, error gutter, syntax highlighting
- `PDFExporter` — fpdf2-based PDF export with per-node sizes and color schemes

## Key Functions
- `parse_diagram(code)` — parses DSL → structured dict
- `compute_layout(parsed, settings)` — grid layout with positions, swimlane rects, step bands
- `_measure_node(label, shape, w, h)` — auto-sizes nodes to fit text

## Bidirectional Editing Flow
```
CODE CHANGED → parse → layout → render scene
                                    ↑ suppress flags prevent loops
NODE DRAGGED → surgical QTextCursor edit on release → re-parse (no re-render)
PORT DRAG    → append connection line to code → re-parse + re-render
DIRECTION    → settings combo writes to code / code updates combo
```
- Uses `_suppress_code_update` and `_suppress_scene_update` flags to prevent infinite loops.
- `setPlainText()` destroys undo — always use `QTextCursor` for surgical edits.

## DSL Features
- 8 shapes: rect, rounded, diamond, circle, parallelogram, hexagon, cylinder, stadium
- 5 connection types: `->`, `-->`, `==>`, `---`, `-.-`
- Swimlanes, boxes, groups, notes, direction, settings, position pins `@(x,y)`
- Rich attributes: step (required), type, owner, status, tags, priority, id

## Build & Run
```bash
pip install pyside6 fpdf2
python run.py
# Standalone exe:
python build_exe.py  # → dist/DiagramEditor/DiagramEditor.exe
```

## File Formats
- `.dgm` — JSON: `{ "version": 3, "code": "...", "settings": {...} }`
- `.txt` — raw DSL code

## Recent Changes (newest first)
- Removed step band background fills (were bleeding around components)
- Fixed 8 bugs: back-edge styling for all directions, group/note per-node sizing, PDF self-loops, undo-preserving edits, dead code removal, swimlane reparent wiring, hex color error handling, edge path caching
- Added: CHANGELOG.md, LICENSE, THIRD_PARTY_LICENSES.md, examples/, .github/ templates, GUIDE.md troubleshooting section, fixed GUIDE.md inaccuracies

## Style Notes
- App uses Catppuccin Mocha dark theme (hardcoded STYLESHEET)
- 7 color schemes for diagrams: Default, Blueprint, Warm, Monochrome, Dark, Synthwave, Forest
- Font: "Segoe UI" for diagram rendering, system monospace for code editor
- The toolbar has a custom ASCII art logo (blackjack card + hook)

## Things to Watch
- Single-file constraint: all changes go in `diagram_app.py`
- Undo preservation: never use `setPlainText()` for incremental edits
- Suppress flags: always set/unset `_suppress_code_update` and `_suppress_scene_update` in try/finally
- Node sizes: always use `node_sizes.get(name, (base_w, base_h))` — never assume base sizes
