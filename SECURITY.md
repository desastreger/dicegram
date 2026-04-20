# Security Policy

## Reporting a vulnerability

If you find a security issue in Dicegram, please **do not open a public
issue**. Instead, email **security@desastregerstudio.com** (or
**nacho@desastregerstudio.com** if the security alias bounces).

Please include:

- A clear description of the issue and its impact.
- Minimal steps to reproduce, including the exact DSL input, HTTP request,
  or UI action.
- The commit hash or deploy you tested against.
- Whether you'd like credit in the fix announcement.

We'll acknowledge receipt within **3 business days** and aim to ship a fix
or a documented mitigation within **30 days** for anything rated high or
critical. Informational / low-severity reports may take longer.

## Supported versions

Only the `master` branch is supported. We don't backport fixes to older
tagged releases.

| Version | Supported |
|---|---|
| `master` | ✅ |
| Tagged `v4.x` releases | Best effort, no guarantees |
| `v3.x-desktop-final` (archived desktop app) | ❌ |

## Hosted instance

The hosted instance at **https://dicegram.desastreger.cloud** is patched from
`master` on the same day a fix lands. If you report an issue that affects the
hosted service, we'll note the patch time in our response.

## Scope

In scope:

- The FastAPI backend (`backend/`), including auth, shares, render, export.
- The SvelteKit frontend (`frontend/`), especially anywhere user-supplied DSL
  is parsed, rendered, or serialized.
- The deploy scripts (`deploy.sh`, `Dockerfile`, `docker-compose.yml`, `Caddyfile`).
- The DSL parser / compiler (`backend/app/dsl/`), especially regex-driven
  paths that could be triggered remotely.

Out of scope (still reports welcome, but lower priority):

- Missing rate limits (we know — slowapi is on the roadmap).
- Denial-of-service via extremely large DSL inputs (we cap at ~1 MiB).
- Social engineering of maintainers.
- Attacks on third-party infrastructure (Hostinger, Let's Encrypt, DNS providers).
