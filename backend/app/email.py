"""Email sending + signed verification / reset tokens.

Two transports are supported:
  - "console": log the rendered email to stdout. Default for local dev and
    for any deployment that hasn't configured SMTP. Emails never leave the
    machine, so users won't receive verification / reset links, but the
    server won't crash and you can copy the link out of the logs while
    you're setting up SMTP.
  - "smtp": connect to an SMTP server using env-configured creds.

Tokens are signed with the app's SECRET_KEY via itsdangerous.URLSafeTimed
Serializer, so the server doesn't need to store any state — verifying a
token only checks the signature + expiry.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Literal

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .config import settings

log = logging.getLogger("dicegram.email")

# Token purposes — included in the payload so a verification link can't be
# repurposed as a password-reset link and vice versa.
PURPOSE_VERIFY = "email-verify"
PURPOSE_RESET = "password-reset"


def _serializer(purpose: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key, salt=purpose)


def make_token(user_id: int, purpose: str) -> str:
    return _serializer(purpose).dumps({"uid": user_id})


def read_token(token: str, purpose: str, max_age_seconds: int) -> int | None:
    try:
        payload = _serializer(purpose).loads(token, max_age=max_age_seconds)
    except SignatureExpired:
        return None
    except BadSignature:
        return None
    uid = payload.get("uid") if isinstance(payload, dict) else None
    return int(uid) if isinstance(uid, int) else None


def send_email(to: str, subject: str, text_body: str, html_body: str | None = None) -> None:
    """Send an email using the configured transport.

    Never raises. Failures are logged but swallowed so a flaky SMTP server
    doesn't poison signup / reset endpoints.
    """
    transport: Literal["console", "smtp"] = (
        "smtp" if settings.smtp_host else "console"
    )
    if transport == "console":
        log.warning(
            "[email:console] transport not configured; logging instead of sending.\n"
            "  To: %s\n  Subject: %s\n---\n%s\n---",
            to,
            subject,
            text_body,
        )
        return

    msg = EmailMessage()
    msg["From"] = (
        f"{settings.smtp_from_name} <{settings.smtp_from_address}>"
        if settings.smtp_from_name
        else settings.smtp_from_address
    )
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    try:
        if settings.smtp_use_tls:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if settings.smtp_username:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
        else:
            # Submission over TLS from the start (port 465 style).
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                if settings.smtp_username:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
    except Exception as exc:  # noqa: BLE001
        log.exception("failed to send email to %s: %s", to, exc)


def build_verify_email(verify_url: str) -> tuple[str, str, str]:
    """Return (subject, text_body, html_body) for a verification email."""
    subject = "Verify your Dicegram email"
    text = (
        "Welcome to Dicegram.\n\n"
        "Confirm your email address by visiting the link below (valid for 48 hours):\n"
        f"{verify_url}\n\n"
        "If you didn't sign up for Dicegram, you can ignore this message — "
        "no account was created for your address.\n"
    )
    html = (
        '<p>Welcome to <strong>Dicegram</strong>.</p>'
        '<p>Confirm your email address by clicking the link below '
        '(valid for 48 hours):</p>'
        f'<p><a href="{verify_url}">{verify_url}</a></p>'
        '<p>If you didn\'t sign up, you can ignore this message — no account '
        'was created for your address.</p>'
    )
    return subject, text, html


def build_reset_email(reset_url: str) -> tuple[str, str, str]:
    subject = "Reset your Dicegram password"
    text = (
        "Someone — hopefully you — requested a password reset for this email.\n\n"
        "If it was you, set a new password via the link below (valid for 1 hour):\n"
        f"{reset_url}\n\n"
        "If it wasn't you, you can ignore this message. Your existing password stays active.\n"
    )
    html = (
        '<p>Someone — hopefully you — requested a password reset for this email.</p>'
        '<p>If it was you, set a new password via the link below (valid for 1 hour):</p>'
        f'<p><a href="{reset_url}">{reset_url}</a></p>'
        '<p>If it wasn\'t you, you can ignore this message. Your existing password stays active.</p>'
    )
    return subject, text, html
