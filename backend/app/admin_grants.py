"""Resolve ADMIN_USERNAMES to account ids, once, at startup.

Admin rights are ultimately held by an ACCOUNT ID. Ids cannot be claimed by
signing up, which is what makes them safe; a username can be, which is why
an earlier version that gated on names directly was a privilege-escalation
bug — anyone could register the configured name and become an administrator.

Naming an account is still the ergonomic way to configure this, so it is
supported, with two properties that make it safe enough:

  * Resolution happens ONCE at startup. A name that is unclaimed when the
    process boots grants nothing, so registering it later does not silently
    hand out admin while the server runs.
  * A name that does not resolve is logged at WARNING with the reason, so
    a typo or an unclaimed handle is visible rather than silent.

The residual risk, stated plainly: if the named account is deleted and the
process later restarts while the name is unclaimed, whoever holds it then
would resolve as admin. Pin ADMIN_USER_IDS to remove that entirely — the
startup log prints the id to use.
"""

from __future__ import annotations

import logging

from sqlmodel import Session, select

from .config import settings
from .db import engine
from .models import User, fold_username

logger = logging.getLogger(__name__)

# Ids resolved from ADMIN_USERNAMES at startup. Union'd with the explicit
# ADMIN_USER_IDS by deps.current_admin.
RESOLVED_ADMIN_IDS: set[int] = set()


def resolve_admin_ids() -> set[int]:
    """Look up each configured username and record its id. Idempotent."""
    RESOLVED_ADMIN_IDS.clear()
    names = settings.admin_username_list
    if not names:
        return RESOLVED_ADMIN_IDS
    try:
        with Session(engine) as session:
            for name in names:
                user = session.exec(
                    select(User).where(User.username_key == fold_username(name))
                ).first()
                if user is None:
                    logger.warning(
                        "ADMIN_USERNAMES: no account named %r — granting nothing. "
                        "Create the account, then restart. (An unclaimed name is "
                        "not a claim on anything.)",
                        name,
                    )
                    continue
                RESOLVED_ADMIN_IDS.add(user.id)
                logger.warning(
                    "ADMIN_USERNAMES: %r resolved to user id %s. "
                    "Pin ADMIN_USER_IDS=%s to make this independent of the name.",
                    name,
                    user.id,
                    user.id,
                )
    except Exception as exc:  # pragma: no cover - startup resilience
        # Never let admin resolution stop the app booting; failing closed
        # (no admin) is the safe outcome.
        logger.warning("ADMIN_USERNAMES could not be resolved: %s", exc)
    return RESOLVED_ADMIN_IDS
