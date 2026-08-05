from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from ..config import settings
from ..db import get_session
from ..deps import current_user
from ..models import User, fold_username
from ..palette import ALLOWED_KEYS, merge_palette
from ..rate_limit import limiter
from ..security import hash_password, verify_password, verify_password_dummy

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Credentials(BaseModel):
    """Login payload. `identifier` is a username, but during the transition
    it also accepts a legacy email so accounts created before the switch can
    still sign in. Once the email column is dropped this becomes username-only."""

    identifier: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class SignupCredentials(BaseModel):
    """Signup payload — username and password, nothing else required.

    No email: Dicegram has no SMTP subsystem, so an address could never be
    used to contact anyone or recover an account. Collecting one was a field
    of friction that stored personal data with no purpose.

    That makes `password_hint` the ONLY prompt a user will ever get, which is
    why it stays — but it is optional, and it is not a security token. The
    signup UI is explicit that there is no reset of any kind."""

    username: str = Field(min_length=2, max_length=60, pattern=r"^[A-Za-z0-9_.\- ]+$")
    password: str = Field(min_length=8, max_length=128)
    password_hint: str = Field(default="", max_length=140)


class UserPublic(BaseModel):
    id: int
    username: str
    # Retained only while legacy accounts still carry one; never collected.
    email: str | None = None
    password_hint: str | None = None


class LoginFailure(BaseModel):
    """401 body for a failed login. Carries the account's own hint when one
    is set, so the user gets their reminder at the moment they need it —
    replacing the old bulk /hint-lookup endpoint, which any caller could
    scrape without ever attempting a login."""

    detail: str = "invalid credentials"
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


# How many failed attempts, from the same browser session, before the hint
# is shown at all.
HINT_AFTER_FAILURES = 3


def _hint_after_repeated_failure(request: Request, user: User) -> str:
    """The account's hint, but only once this browser has failed repeatedly.

    Returning it on the FIRST failure made every hint harvestable with a
    single unauthenticated request — you only needed the username. That is
    fine for an email address, which is semi-private, and not fine for a
    username, which is a public handle. This project's own admin username
    appears in every git commit in a public repository.

    The counter lives in the signed session cookie rather than in server
    memory, for two reasons: it survives across uvicorn workers (an
    in-process dict would not, and a real user round-robining across three
    workers might never reach the threshold), and a scripted harvester that
    keeps no cookie jar never accumulates a count at all — so it never sees
    a hint, however many requests it makes.

    Admin accounts never get a hint disclosed, at any count. Their username
    is the most guessable one on the instance and their compromise matters
    most; if an admin forgets their password, the recovery path is server
    access, which they have by definition.
    """
    if not user.password_hint:
        return ""
    if fold_username(user.username) in settings.admin_username_set:
        return ""
    key = fold_username(user.username)
    count = request.session.get("lf_n", 0) if request.session.get("lf_user") == key else 0
    count += 1
    request.session["lf_user"] = key
    request.session["lf_n"] = count
    return user.password_hint if count >= HINT_AFTER_FAILURES else ""


def _user_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        username=user.username,
        email=user.email,
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
    key = fold_username(creds.username)
    exists = session.exec(select(User).where(User.username_key == key)).first()
    if exists:
        # A username is a public handle, so saying it is taken discloses
        # nothing an attacker could not learn by trying to register it.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="username already taken"
        )
    user = User(
        username=creds.username.strip(),
        username_key=key,
        password_hash=hash_password(creds.password),
        password_hint=(creds.password_hint or "").strip() or None,
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
    ident = creds.identifier.strip()
    user = session.exec(
        select(User).where(User.username_key == fold_username(ident))
    ).first()
    if user is None and "@" in ident:
        # Transition path: accounts created before the switch signed up with
        # an email and may not know their generated username yet. Dropped
        # once the email column goes.
        user = session.exec(select(User).where(User.email == ident)).first()
    if not user:
        # Run a dummy argon2 verify so this branch costs the same
        # wall-clock time as a real password check below — otherwise an
        # unknown identifier short-circuits before argon2 runs, and the ~12x
        # timing gap reveals which accounts exist.
        verify_password_dummy()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "invalid credentials", "password_hint": ""},
        )
    if not verify_password(user.password_hash, creds.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "detail": "invalid credentials",
                "password_hint": _hint_after_repeated_failure(request, user),
            },
        )
    # Successful sign-in clears the failure counter below.
    request.session.pop("lf_user", None)
    request.session.pop("lf_n", None)
    request.session["user_id"] = user.id
    return _user_public(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request):
    request.session.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(current_user)):
    return _user_public(user)


# ─── Password hint ─────────────────────────────────────────────────────
#
# The public POST /api/auth/hint-lookup endpoint used to live here. It took
# an email and returned that account's hint to any caller, which made every
# stored hint harvestable in bulk without a single login attempt. Moving to
# username-based login would have made it strictly worse — usernames are
# public handles and far more guessable than email addresses.
#
# The hint is now returned by the /login 401 body when the username exists
# but the password is wrong, so a caller must actually attempt a login (and
# wear that route's rate limit) to see one.

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
