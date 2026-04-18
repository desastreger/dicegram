from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select

from ..db import get_session
from ..deps import current_user
from ..models import User
from ..security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    id: int
    email: EmailStr


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def signup(
    creds: Credentials,
    request: Request,
    session: Session = Depends(get_session),
):
    exists = session.exec(select(User).where(User.email == creds.email)).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email already registered"
        )
    user = User(email=creds.email, password_hash=hash_password(creds.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    request.session["user_id"] = user.id
    return UserPublic(id=user.id, email=user.email)


@router.post("/login", response_model=UserPublic)
def login(
    creds: Credentials,
    request: Request,
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == creds.email)).first()
    if not user or not verify_password(user.password_hash, creds.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials"
        )
    request.session["user_id"] = user.id
    return UserPublic(id=user.id, email=user.email)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request):
    request.session.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(current_user)):
    return UserPublic(id=user.id, email=user.email)
