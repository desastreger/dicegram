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

    # Comma-separated usernames allowed to read /api/admin/*. Deliberately
    # an env var rather than a DB column: a compromised database write
    # cannot mint an admin, and there is no UI that could accidentally
    # grant it. Empty (the default) means NOBODY is an admin, so a
    # self-hosted instance exposes nothing until it opts in.
    admin_usernames: str = ""

    # Where the Caddy access log is mounted read-only (docker-compose.yml).
    # Read through Settings, not os.environ, so a value in .env works in dev
    # too — pydantic-settings loads .env into Settings, never into the
    # process environment.
    access_log_glob: str = "/var/log/caddy/access*.log"

    @property
    def admin_username_set(self) -> set[str]:
        return {
            u.strip().casefold()
            for u in self.admin_usernames.split(",")
            if u.strip()
        }

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
