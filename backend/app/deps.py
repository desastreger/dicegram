from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from .config import settings
from .db import get_session
from .models import User, fold_username


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
    """Gate for /api/admin/*. Admins are named in the ADMIN_USERNAMES env
    var; see Settings.admin_usernames for why it lives there and not in the
    database.

    Returns 404 rather than 403 for a signed-in non-admin, so the existence
    of an admin surface is not confirmed to an ordinary account."""
    allowed = settings.admin_username_set
    if not allowed or fold_username(user.username) not in allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return user
