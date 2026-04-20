# Third-Party Licenses

Dicegram links to the following open-source libraries at runtime and at build
time. This file lists the direct dependencies you'll find in
`backend/requirements.txt` and `frontend/package.json`; transitive
dependencies inherit their own licenses (inspect `node_modules` and `pip show`
for the full tree).

Dicegram itself is licensed under **GNU AGPL-3.0-or-later** — see the
[`LICENSE`](./LICENSE) file.

---

## Backend (Python)

| Package | Version range | License | Role |
|---|---|---|---|
| [FastAPI](https://github.com/fastapi/fastapi) | ≥ 0.115 | MIT | HTTP framework |
| [Uvicorn](https://www.uvicorn.org/) (`uvicorn[standard]`) | ≥ 0.32 | BSD-3-Clause | ASGI server |
| [SQLModel](https://sqlmodel.tiangolo.com/) | ≥ 0.0.22 | MIT | ORM layer |
| [argon2-cffi](https://github.com/hynek/argon2-cffi) | ≥ 23.1 | MIT | Password hashing |
| [itsdangerous](https://github.com/pallets/itsdangerous) | ≥ 2.2 | BSD-3-Clause | Signed session cookies |
| [pydantic-settings](https://github.com/pydantic/pydantic-settings) | ≥ 2.6 | MIT | Typed config loader |
| [email-validator](https://github.com/JoshData/python-email-validator) | ≥ 2.2 | CC0-1.0 | Email validation |
| [python-multipart](https://github.com/Kludex/python-multipart) | ≥ 0.0.12 | Apache-2.0 | Multipart form parser |

## Frontend (Node)

### Runtime dependencies

| Package | Version range | License | Role |
|---|---|---|---|
| [@codemirror/\*](https://codemirror.net/) (commands, language, state, view) | ≥ 6 | MIT | Code editor core |
| [codemirror](https://codemirror.net/) | ≥ 6 | MIT | CodeMirror 6 meta package |
| [@xyflow/svelte](https://svelteflow.dev/) | ≥ 1.5 | MIT | Canvas graph / flow |
| [jsPDF](https://github.com/parallax/jsPDF) | ≥ 4.2 | MIT | Client-side PDF export |

### Build / toolchain dependencies

| Package | License | Role |
|---|---|---|
| [Svelte](https://svelte.dev/) ≥ 5 | MIT | UI framework |
| [SvelteKit](https://kit.svelte.dev/) + `@sveltejs/adapter-static` + `@sveltejs/vite-plugin-svelte` | MIT | Meta-framework, static adapter, Vite plugin |
| [Vite](https://vitejs.dev/) | MIT | Dev server / bundler |
| [TailwindCSS](https://tailwindcss.com/) + `@tailwindcss/forms` + `@tailwindcss/vite` | MIT | Styling |
| [TypeScript](https://www.typescriptlang.org/) | Apache-2.0 | Typed JS |
| [ESLint](https://eslint.org/) + `typescript-eslint` + `eslint-plugin-svelte` + `@eslint/js` + `@eslint/compat` | MIT | Linter |
| [Prettier](https://prettier.io/) + `prettier-plugin-svelte` + `prettier-plugin-tailwindcss` + `eslint-config-prettier` | MIT | Formatter |
| [Vitest](https://vitest.dev/) + `svelte-check` | MIT | Tests, type-check |
| [globals](https://github.com/sindresorhus/globals) / [@types/node](https://github.com/DefinitelyTyped/DefinitelyTyped) | MIT | Lint/type globals |

## Runtime infrastructure

Dicegram ships with optional infrastructure files that reference but do not
bundle third-party software:

- **[Caddy 2](https://caddyserver.com/)** — Apache-2.0. Pulled as
  `caddy:2-alpine` when you run with `--profile caddy`.
- **[Docker Engine](https://www.docker.com/)** / **[Docker Compose](https://docs.docker.com/compose/)**
  — Apache-2.0. Required on the host; not redistributed by this project.
- **[Python 3.12](https://www.python.org/)** base image (`python:3.12-slim-bookworm`)
  and **[Node.js 20](https://nodejs.org/)** builder (`node:20-alpine`) — both
  are licensed under their respective upstreams (PSF and MIT); images are
  pulled at build time, not redistributed.
- **[gosu](https://github.com/tianon/gosu)** — Apache-2.0. Used in the
  entrypoint to drop privileges.

---

### Regenerating this file

To produce a fully-enumerated list (including transitive dependencies):

```bash
# Backend
pip install pip-licenses
pip-licenses --from=mixed --format=markdown

# Frontend
npx license-checker --production --summary
```

If you notice a license mismatch or a missing dependency, please open a PR.
