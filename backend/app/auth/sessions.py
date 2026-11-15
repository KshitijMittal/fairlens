"""Session plumbing: cookie-backed sessions, one row per login.

Cookie `fl_session`, HttpOnly, Secure in production, SameSite=Lax, Path=/, 30 days.
Only the SHA-256 digest of the token is stored. Expired rows are swept at startup
and on every login (TRD 5.1) instead of by a cron.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, HTTPException, Request, Response

from app.auth.security import hash_token, new_session_token
from app.core.config import settings
from app.db import Repository

SESSION_COOKIE_NAME = "fl_session"
SESSION_MAX_AGE = 30 * 24 * 60 * 60


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=SESSION_MAX_AGE,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def create_session(repo: Repository, user_id: uuid.UUID) -> str:
    """Create a session row and return the raw token for the cookie."""
    token = new_session_token()
    repo.create_session(hash_token(token), user_id,
                        datetime.now(timezone.utc) + timedelta(days=30))
    return token


def get_session_user_id(request: Request, token: str | None = Cookie(
        default=None, alias=SESSION_COOKIE_NAME)) -> uuid.UUID | None:
    if not token:
        return None
    repo: Repository = request.app.state.repo
    token_hash = hash_token(token)
    session = repo.get_session(token_hash)
    if not session:
        return None
    if session["expires_at"] < datetime.now(timezone.utc):
        repo.delete_session(token_hash)
        return None
    return session["user_id"]


def require_user(request: Request, token: str | None = Cookie(
        default=None, alias=SESSION_COOKIE_NAME)) -> uuid.UUID:
    user_id = get_session_user_id(request, token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


def optional_user(request: Request, token: str | None = Cookie(
        default=None, alias=SESSION_COOKIE_NAME)) -> uuid.UUID | None:
    return get_session_user_id(request, token)


def sweep_expired() -> None:
    """Delete expired sessions and stale rate-limit windows."""
    from app.db import get_pool
    with get_pool().connection() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < now()")
        conn.execute("DELETE FROM rate_limits WHERE window_start < date_trunc('hour', now())")
