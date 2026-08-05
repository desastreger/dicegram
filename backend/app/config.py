from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_BAD_SECRETS = {"", "dev-secret-change-me", "replace-me-with-a-long-random-string"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "dev-secret-change-me"
    database_url: str = "sqlite:///./dicegram.db"
    session_cookie_secure: bool = False
    session_max_age_seconds: int = 60 * 60 * 24 * 14

    # Max payload size for DSL-accepting endpoints. 1 MiB is plenty for any
    # real diagram; keeps parser/regex cost bounded.
    max_source_bytes: int = 1 * 1024 * 1024

    # Public base URL — kept for downstream URL builders that may want
    # an absolute reference (e.g. share links). Defaults to localhost so
    # dev runs without env config.
    app_base_url: str = "http://localhost:5173"

    # Comma-separated USER IDS allowed to read /api/admin/*.
    #
    # IDS, NOT USERNAMES. A username is not a claim on anything: naming an
    # account that does not exist yet means the first person to register
    # that name becomes an administrator. With a public repository an
    # attacker can read this setting's purpose and guess the likely name
    # from the commit history. An id refers to an account that already
    # exists and cannot be obtained by signing up.
    #
    # Still an env var rather than a DB column: a database write cannot
    # mint an admin and no UI can grant it. Empty (the default) means
    # NOBODY is an admin, so a fresh instance exposes no admin surface.
    #
    # Find yours while signed in:  GET /api/auth/me  ->  {"id": N, ...}
    admin_user_ids: str = ""

    # Comma-separated USERNAMES to grant admin, resolved to ids ONCE at
    # startup (see admin_grants.resolve_admin_ids). A name that does not
    # resolve to an existing account is ignored and logged loudly.
    #
    # This is a convenience over ADMIN_USER_IDS, not a replacement, and it
    # carries a caveat worth understanding: a username is only safe to name
    # once that account EXISTS. Naming an unclaimed handle is a land-grab —
    # whoever registers it first would become an administrator at the next
    # restart. Resolving at boot means an unclaimed name grants nothing
    # until someone restarts the process, and the warning tells you why.
    #
    # Prefer pinning ADMIN_USER_IDS; the startup log prints the resolved id.
    admin_usernames: str = ""

    @property
    def admin_username_list(self) -> list[str]:
        return [u.strip() for u in self.admin_usernames.split(",") if u.strip()]

    # Where the Caddy access log is mounted read-only (docker-compose.yml).
    # Read through Settings, not os.environ, so a value in .env works in dev
    # too — pydantic-settings loads .env into Settings, never into the
    # process environment.
    access_log_glob: str = "/var/log/caddy/access*.log"

    @property
    def admin_id_set(self) -> set[int]:
        out: set[int] = set()
        for part in self.admin_user_ids.split(","):
            part = part.strip()
            if part.isdigit():
                out.add(int(part))
        return out

    @model_validator(mode="after")
    def _reject_default_in_prod(self) -> "Settings":
        # Only enforce when NOT in dev — detection is crude: if the cookie is
        # marked secure (i.e. SESSION_COOKIE_SECURE=true), we're not running
        # locally, so refuse to boot with a dev secret. This runs on the
        # RESOLVED settings (post env-file / env-var loading), unlike a
        # plain field_validator reading os.getenv directly, which never saw
        # values that came from `.env` rather than the real environment.
        if self.session_cookie_secure:
            if self.secret_key in _BAD_SECRETS or len(self.secret_key) < 32:
                raise ValueError(
                    "SECRET_KEY is missing, too short, or still the default. "
                    "Generate one with: "
                    "python3 -c 'import secrets; print(secrets.token_urlsafe(48))'"
                )
        return self


settings = Settings()
