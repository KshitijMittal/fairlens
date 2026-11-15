"""Password and token primitives.

argon2id with time_cost=3, memory_cost=65536, parallelism=1.
bcrypt fallback chosen at import and logged.
session token: secrets.token_urlsafe(32), SHA-256 hex stored, raw token never persisted.
"""
import hashlib
import logging
import secrets
from typing import Final

logger = logging.getLogger(__name__)

ARGON2_TIME_COST: Final = 3
ARGON2_MEMORY_COST: Final = 65536
ARGON2_PARALLELISM: Final = 1

_PWD_CONTEXT = None
_HASHER_NAME = "argon2id"

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerificationError as Argon2VerificationError

    _PWD_CONTEXT = PasswordHasher(
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=32,
        salt_len=16,
    )
    logger.info("argon2id hasher initialised (time_cost=%d, memory_cost=%d, parallelism=%d)",
                ARGON2_TIME_COST, ARGON2_MEMORY_COST, ARGON2_PARALLELISM)
except Exception as exc:
    import bcrypt
    _PWD_CONTEXT = bcrypt
    _HASHER_NAME = "bcrypt"
    logger.warning("argon2-cffi unavailable (%s); falling back to bcrypt(cost=12)", exc)


def hash_password(password: str) -> str:
    """Hash a password with argon2id (or bcrypt fallback)."""
    if _HASHER_NAME == "argon2id":
        return _PWD_CONTEXT.hash(password)
    return _PWD_CONTEXT.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash. Constant-time for unknown accounts."""
    if _HASHER_NAME == "argon2id":
        try:
            _PWD_CONTEXT.verify(password_hash, password)
            return True
        except Argon2VerificationError:
            return False
    return _PWD_CONTEXT.checkpw(password.encode(), password_hash.encode())


def hash_token(token: str) -> str:
    """SHA-256 hex digest of a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def new_session_token() -> str:
    """Generate a new session token (raw, for the cookie)."""
    return secrets.token_urlsafe(32)


def new_auth_token() -> str:
    """Generate a new auth token (raw, for email links)."""
    return secrets.token_urlsafe(32)


_DUMMY_HASH: str | None = None


def dummy_hash() -> str:
    """A dummy hash for timing-safe verification of unknown accounts."""
    global _DUMMY_HASH
    if _DUMMY_HASH is None:
        if _HASHER_NAME == "argon2id":
            _DUMMY_HASH = _PWD_CONTEXT.hash(secrets.token_urlsafe(32))
        else:
            _DUMMY_HASH = _PWD_CONTEXT.hashpw(secrets.token_urlsafe(32).encode(),
                                              bcrypt.gensalt(rounds=12)).decode()
    return _DUMMY_HASH


def get_hasher_name() -> str:
    """Return the active hasher name for logging/debugging."""
    return _HASHER_NAME