from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select

from ..db import get_session
from ..deps import current_user
from ..models import User
from ..palette import ALLOWED_KEYS, DEFAULT_PALETTE, merge_palette
from ..security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    id: int
    email: EmailStr


class PaletteOut(BaseModel):
    palette: dict[str, str]


class PaletteIn(BaseModel):
    palette: dict[str, str] = Field(default_factory=dict)


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


@router.get("/me/palette", response_model=PaletteOut)
def get_palette(user: User = Depends(current_user)):
    """Return the effective palette (defaults merged with user overrides)."""
    return PaletteOut(palette=merge_palette(user.branding_palette))


@router.put("/me/palette", response_model=PaletteOut)
def put_palette(
    body: PaletteIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    """Replace the user palette with the given overrides. Keys outside the
    allowed set are silently dropped; invalid colours are dropped by
    `merge_palette`. Pass an empty dict to reset to defaults."""
    clean: dict[str, str] = {}
    for k, v in body.palette.items():
        if k not in ALLOWED_KEYS or not isinstance(v, str):
            continue
        v = v.strip()
        # Accept "" as "inherit default" so the UI can unset individual keys.
        if v == "" or v.startswith("#") or v.startswith("rgb") or v.startswith("hsl"):
            clean[k] = v
    user.branding_palette = clean
    session.add(user)
    session.commit()
    session.refresh(user)
    return PaletteOut(palette=merge_palette(user.branding_palette))
