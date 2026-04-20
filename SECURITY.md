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

## Credential and data storage

- **Passwords**: hashed with [argon2-cffi](https://github.com/hynek/argon2-cffi)
  using the library's default parameters. Plain-text passwords are never
  written to disk, and login requests compare hashes in constant time.
- **Session cookies**: `httpOnly`, `sameSite=lax`, `secure` (in production —
  toggled by `SESSION_COOKIE_SECURE=true`), signed with `SECRET_KEY` via
  `itsdangerous`. Sessions last 14 days by default.
- **Verification / reset tokens**: signed with `SECRET_KEY` + a purpose salt
  (distinct salts for verification and reset so tokens can't be swapped
  between flows). Verification expires after 48 h, reset after 1 h. Tokens
  are stateless — the server only checks the signature + expiry, so there's
  nothing to leak from a compromised DB except the `SECRET_KEY` itself.
- **`SECRET_KEY`**: read from `.env`, which `deploy.sh` `chmod 0600`s on
  creation. Never logged, never sent in responses. Rotate by editing `.env`
  and restarting the container — all existing sessions and unused tokens
  become invalid instantly.
- **Database**: SQLite on a named Docker volume by default — not encrypted
  at rest. For regulated-data deployments, point `DATABASE_URL` at a
  Postgres instance with TDE / encrypted storage; the app code is agnostic.
- **Email outbound**: SMTP over TLS (STARTTLS on 587 or SMTPS on 465). No
  email content is stored server-side beyond the audit line in the logs
  when the "console" transport is active.

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
