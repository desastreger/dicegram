# Diagram Editor

Step-based code-to-diagram desktop application with bidirectional editing, rich attributes, and live preview.

## Quick Start

```bash
pip install pyside6 fpdf2
python run.py
```

Or on Windows, double-click `DiagramEditor.bat`.

Or unzip `DiagramEditor-standalone.zip` and run `DiagramEditor.exe` (no Python needed).

## Documentation

See **[GUIDE.md](GUIDE.md)** for the complete reference:
- Full DSL syntax with all shapes, connections, attributes
- Keyboard shortcuts
- Interaction modes (Select, Pan, Connect)
- Filter/search system
- Export formats (PDF, SVG, PNG, clipboard)
- Bidirectional editing behavior
- Color schemes
- Architecture notes
- LLM prompt for AI-generated diagrams

## Requirements

- Python 3.10+
- PySide6 >= 6.6
- fpdf2 >= 2.7

## Features at a Glance

- 8 shape types following Visio/BPMN conventions
- 5 connection types with labels, hints, and attributes
- Swimlanes, boxes, groups, notes
- Step-based parallel placement (same step = same row)
- Rich attributes: type, owner, status, tags, priority (with visual effects)
- 7 color schemes
- 4 layout directions (top-to-bottom, left-to-right, bottom-to-top, right-to-left)
- Drag nodes to move (writes position to code)
- Drag between ports to connect (writes connection to code)
- Filter by any attribute
- Auto-capitalize labels
- Alignment grid with snap
- PDF/SVG/PNG export
- LLM prompt generator for AI diagram creation
