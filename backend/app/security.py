import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

_hasher = PasswordHasher()

# Fixed hash computed once at import time so a login against an unknown
# email can still pay the same argon2 cost as a real password check (see
# verify_password_dummy below). The plaintext is irrelevant — it's never
# compared against anything real.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(32))


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def verify_password_dummy() -> None:
    """Run an argon2 verify against a fixed precomputed hash. Callers use
    this on the "user not found" branch of login so that path costs
    roughly the same wall-clock time as the real `verify_password` call —
    without it, an unknown email short-circuits before argon2 ever runs,
    producing a ~12x timing gap that leaks which emails are registered."""
    try:
        _hasher.verify(_DUMMY_HASH, "irrelevant-timing-equalizer")
    except (VerifyMismatchError, VerificationError):
        pass
