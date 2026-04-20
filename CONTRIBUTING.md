# Contributing to Dicegram

Thanks for thinking about contributing. This is a small, opinionated codebase —
PRs are welcome, but please read this page first so we're aligned.

## Ground rules

- **DSL is the source of truth.** Every persistent visual property lives in
  the source file. UI interactions translate into DSL mutations, not parallel
  state. If your change drifts from that, we'll push back.
- **Orthogonal connectors only.** No bezier curves, no diagonals on the
  canvas. The backend SVG exporter and the frontend `SmartEdge` component
  agree on this.
- **Keep the two editors in sync.** If you touch shape rendering on the
  canvas (`frontend/src/routes/editor/ShapeNode.svelte`), update the
  `ShapePreview` component and the backend SVG exporter
  (`backend/app/dsl/export_svg.py`) so all three surfaces look identical.
- **No new dependencies without a justification.** Especially on the frontend —
  we're adapter-static, bundle size matters.

## Development workflow

1. Fork the repo, branch off `master`.
2. Run locally:
   ```bash
   cd backend && python -m venv .venv && . .venv/Scripts/activate
   pip install -r requirements.txt
   cp .env.example .env
   uvicorn app.main:app --reload --port 8000

   # in another terminal
   cd frontend && npm install && npm run dev
   ```
3. Open http://localhost:5173.
4. Tests and type-checks:
   ```bash
   cd frontend && npm run check && npm run lint && npm test
   ```
5. Open a PR using the [pull request template](.github/pull_request_template.md).
   Small, focused PRs are much easier to review than mega-branches.

## What we'd love help with

- **Bug fixes** — check open issues labeled `bug`.
- **DSL examples** — add real-world `.dgm` files to `examples/`.
- **Documentation** — `GUIDE.md` (DSL reference) can always use more worked
  examples.
- **Export formats** — the SVG/PNG/PDF/HTML/Visio matrix is a natural
  extension point. Mermaid output would be welcome.
- **Tests** — anything in `backend/app/dsl/` is well-structured for unit
  tests; we don't have enough of them.

## Licensing

By submitting a PR you agree that your contribution is licensed under the
same terms as the project: **GNU AGPL-3.0-or-later**. You retain your own
copyright.

We may, at our discretion, offer the same code under a commercial license to
third parties who can't comply with AGPL (this is standard dual-licensing;
it only works because we keep the copyright history clean via the
Contributor-License assumption above).

## Questions

Open a GitHub Discussion or ping the maintainer at
[desastregerstudio.com](https://desastregerstudio.com).
