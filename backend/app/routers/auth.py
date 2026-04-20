from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select

from ..db import get_session
from ..deps import current_user
from ..models import User
from ..palette import ALLOWED_KEYS, DEFAULT_PALETTE, merge_palette
from ..rate_limit import limiter
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


class PresetOut(BaseModel):
    name: str
    overrides: dict[str, str]
    active: bool


class PresetsOut(BaseModel):
    presets: list[PresetOut]


class PresetSaveIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    # If omitted, save the user's current active overrides under this name.
    overrides: dict[str, str] | None = None


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
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
@limiter.limit("10/minute")
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


def _sanitize_overrides(raw: dict[str, str]) -> dict[str, str]:
    clean: dict[str, str] = {}
    for k, v in raw.items():
        if k not in ALLOWED_KEYS or not isinstance(v, str):
            continue
        v = v.strip()
        if v == "" or v.startswith("#") or v.startswith("rgb") or v.startswith("hsl"):
            clean[k] = v
    return clean


def _active_preset_name(user: User) -> str:
    """Return the preset name whose overrides exactly match the current
    branding_palette, or '' if none does (i.e. the user is mid-edit)."""
    cur = user.branding_palette or {}
    for name, ov in (user.palette_presets or {}).items():
        if (ov or {}) == cur:
            return name
    return ""


@router.get("/me/palettes", response_model=PresetsOut)
def list_presets(user: User = Depends(current_user)):
    active = _active_preset_name(user)
    presets = user.palette_presets or {}
    return PresetsOut(
        presets=[
            PresetOut(name=n, overrides=dict(ov or {}), active=(n == active))
            for n, ov in sorted(presets.items(), key=lambda kv: kv[0].lower())
        ]
    )


@router.post("/me/palettes", response_model=PresetsOut)
def save_preset(
    body: PresetSaveIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    """Create or overwrite a named preset. If `overrides` is omitted, save
    the user's current active overrides under the given name."""
    overrides = _sanitize_overrides(
        body.overrides if body.overrides is not None else (user.branding_palette or {})
    )
    presets = dict(user.palette_presets or {})
    presets[body.name] = overrides
    user.palette_presets = presets
    session.add(user)
    session.commit()
    session.refresh(user)
    return list_presets(user)


@router.patch("/me/palettes/{name}/activate", response_model=PaletteOut)
def activate_preset(
    name: str,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    presets = user.palette_presets or {}
    if name not in presets:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown preset")
    user.branding_palette = _sanitize_overrides(dict(presets[name] or {}))
    session.add(user)
    session.commit()
    session.refresh(user)
    return PaletteOut(palette=merge_palette(user.branding_palette))


@router.delete("/me/palettes/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preset(
    name: str,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    presets = dict(user.palette_presets or {})
    if name not in presets:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown preset")
    del presets[name]
    user.palette_presets = presets
    session.add(user)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
