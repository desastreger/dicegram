from pydantic import field_validator
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

    # Public base URL — used to build verification / password-reset links
    # in outbound emails. e.g. "https://dicegram.desastreger.cloud".
    # Defaults to empty in dev so the links point at localhost:5173 when
    # your frontend is on vite.
    app_base_url: str = "http://localhost:5173"

    # Email / SMTP. If smtp_host is empty we fall back to a "console" email
    # transport that logs the body of the email instead of sending it —
    # useful for dev and for setups that haven't configured SMTP yet.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True  # True = STARTTLS on 587; False = SSL on 465.
    smtp_from_address: str = "noreply@dicegram.local"
    smtp_from_name: str = "Dicegram"

    # Token lifetimes (seconds).
    verify_token_max_age: int = 60 * 60 * 48   # 48h
    reset_token_max_age: int = 60 * 60         # 1h

    @field_validator("secret_key")
    @classmethod
    def _reject_default_in_prod(cls, v: str) -> str:
        # Only enforce when NOT in dev — detection is crude: if the cookie is
        # marked secure (i.e. someone set SESSION_COOKIE_SECURE=true), we're
        # not running locally, so refuse to boot with a dev secret.
        import os
        if os.getenv("SESSION_COOKIE_SECURE", "").lower() in {"1", "true", "yes"}:
            if v in _BAD_SECRETS or len(v) < 32:
                raise ValueError(
                    "SECRET_KEY is missing, too short, or still the default. "
                    "Generate one with: "
                    "python3 -c 'import secrets; print(secrets.token_urlsafe(48))'"
                )
        return v


settings = Settings()
