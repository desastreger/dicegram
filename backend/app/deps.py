from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from .admin_grants import RESOLVED_ADMIN_IDS
from .config import settings
from .db import get_session
from .models import User


def current_user(
    request: Request, session: Session = Depends(get_session)
) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated"
        )
    user = session.get(User, user_id)
    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated"
        )
    return user


def current_admin(user: User = Depends(current_user)) -> User:
    """Gate for /api/admin/*. Admins are listed by USER ID in the
    ADMIN_USER_IDS env var; see Settings.admin_user_ids for why it is ids
    rather than usernames, and why it is an env var rather than a column.

    Returns 404 rather than 403 for a signed-in non-admin, so the existence
    of an admin surface is not confirmed to an ordinary account."""
    allowed = settings.admin_id_set | RESOLVED_ADMIN_IDS
    if not allowed or user.id not in allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return user
