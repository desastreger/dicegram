# Changelog

All notable changes to Diagram Editor are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [3.0.1] — 2026-04-13

### Fixed
- Containment logic for objects inside swimlanes and boxes
- Port-based edge routing — connections now attach to nearest port instead of node center
- Settings directives (`setting node_width 140`, etc.) now properly sync between code and settings panel

## [3.0.0] — 2026-04-13

### Added
- Complete rewrite using PySide6 (Qt) — replaces tkinter version
- QGraphicsScene-based rendering with DiagramNode and DiagramEdge items
- Bidirectional editing: drag nodes to move (writes `@(x,y)` to code), drag ports to connect (writes connection to code)
- 8 shape types: rect, rounded, diamond, circle, parallelogram, hexagon, cylinder, stadium
- 5 connection types: `->`, `-->`, `==>`, `---`, `-.-` with labels, hints, conditions, and weights
- Swimlanes, boxes (sub-containers), groups (visual overlays), and notes
- Step-based layout: same step number = same row/column (parallel placement)
- Rich attributes: type, owner, status, tags, priority, id — with visual effects (dashed for draft, red for blocked, strikethrough for deprecated, checkmark for complete)
- 7 color schemes: Default, Blueprint, Warm, Monochrome, Dark, Synthwave, Forest
- 4 layout directions: top-to-bottom, left-to-right, bottom-to-top, right-to-left
- Filter/search system with structured queries (type:, owner:, tags:, status:, step:, free text, AND/OR)
- 3 interaction modes: Select (V), Pan (H), Connect (C)
- Syntax-highlighted code editor with line numbers, error gutter, and find/replace
- Drawing palette for inserting shapes and connectors via click
- Export to PDF (fpdf2), SVG, PNG, and clipboard
- `.dgm` save format (JSON with version, code, settings) and `.txt` (raw DSL)
- LLM prompt generator (Help > Copy LLM Prompt) for AI-assisted diagram creation
- Node auto-sizing to fit text content
- Snap-to-grid (10px) on all drag operations
- Standalone executable build via PyInstaller

### Changed
- Architecture: single-file design (`diagram_app.py`) — all code in one place by design

### Previous Versions
Versions 1.x (HTML/JS with CodeMirror + dagre) and 2.x (Python/tkinter) were not formally tracked. Version 3.0 is a ground-up rewrite.
