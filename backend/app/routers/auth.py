from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select

from ..db import get_session
from ..deps import current_user
from ..models import User
from ..palette import ALLOWED_KEYS, merge_palette
from ..rate_limit import limiter
from ..security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class SignupCredentials(BaseModel):
    """Signup payload. Adds `username` (display handle) and `password_hint`
    (a user-chosen reminder string we display back if they forget the
    password). The hint is *not* a security token — there's no SMTP-based
    recovery while we're offline, so the hint exists purely so the user
    can refresh their own memory."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    username: str = Field(min_length=1, max_length=60)
    password_hint: str = Field(min_length=1, max_length=140)


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    username: str | None = None
    password_hint: str | None = None


class HintLookupIn(BaseModel):
    email: EmailStr


class HintLookupOut(BaseModel):
    # Empty string when no account matches — keeps the response shape
    # consistent and avoids a 404-vs-200 enumeration vector.
    password_hint: str = ""


class HintUpdateIn(BaseModel):
    password_hint: str = Field(min_length=1, max_length=140)


class UsernameUpdateIn(BaseModel):
    username: str = Field(min_length=1, max_length=60)


class PaletteOut(BaseModel):
    palette: dict[str, str]
    locked: bool = False


class PaletteIn(BaseModel):
    palette: dict[str, str] = Field(default_factory=dict)
    locked: bool | None = None


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


def _user_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        username=user.username,
        password_hint=user.password_hint,
    )


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def signup(
    request: Request,
    response: Response,
    creds: SignupCredentials,
    session: Session = Depends(get_session),
):
    exists = session.exec(select(User).where(User.email == creds.email)).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email already registered"
        )
    user = User(
        email=creds.email,
        password_hash=hash_password(creds.password),
        username=creds.username.strip(),
        password_hint=creds.password_hint.strip(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    request.session["user_id"] = user.id
    return _user_public(user)


@router.post("/login", response_model=UserPublic)
@limiter.limit("10/minute")
def login(
    request: Request,
    response: Response,
    creds: Credentials,
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == creds.email)).first()
    if not user or not verify_password(user.password_hash, creds.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials"
        )
    request.session["user_id"] = user.id
    return _user_public(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request):
    request.session.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(current_user)):
    return _user_public(user)


# ─── Password hint (replacement for SMTP-driven reset) ──────────────────

@router.post("/hint-lookup", response_model=HintLookupOut)
@limiter.limit("10/minute")
def hint_lookup(
    request: Request,
    response: Response,
    body: HintLookupIn,
    session: Session = Depends(get_session),
):
    """Return the password hint stored for the given email, or an empty
    string if no account matches. Rate-limited so the endpoint can't be
    used as a free email enumeration oracle. The hint is user-chosen and
    intentionally not secret — it's the bridge while SMTP recovery is
    offline."""
    user = session.exec(select(User).where(User.email == body.email)).first()
    if user is None or not user.password_hint:
        return HintLookupOut(password_hint="")
    return HintLookupOut(password_hint=user.password_hint)


@router.put("/me/hint", response_model=UserPublic)
def update_hint(
    body: HintUpdateIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    user.password_hint = body.password_hint.strip()
    session.add(user)
    session.commit()
    session.refresh(user)
    return _user_public(user)


@router.put("/me/username", response_model=UserPublic)
def update_username(
    body: UsernameUpdateIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
):
    user.username = body.username.strip()
    session.add(user)
    session.commit()
    session.refresh(user)
    return _user_public(user)


@router.get("/me/palette", response_model=PaletteOut)
def get_palette(user: User = Depends(current_user)):
    """Return the effective palette (defaults merged with user overrides)."""
    return PaletteOut(
        palette=merge_palette(user.branding_palette),
        locked=bool(user.palette_locked),
    )


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
    if body.locked is not None:
        user.palette_locked = bool(body.locked)
    session.add(user)
    session.commit()
    session.refresh(user)
    return PaletteOut(
        palette=merge_palette(user.branding_palette),
        locked=bool(user.palette_locked),
    )


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
    return PaletteOut(
        palette=merge_palette(user.branding_palette),
        locked=bool(user.palette_locked),
    )


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
