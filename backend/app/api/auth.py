"""Auth routes: signup, login, logout, /v1/me, password reset, Google sign-in."""
import base64
import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from app.auth.security import (
    dummy_hash,
    hash_password,
    hash_token,
    new_auth_token,
    verify_password,
)
from app.auth.sessions import (
    SESSION_COOKIE_NAME,
    clear_session_cookie,
    create_session,
    require_user,
    set_session_cookie,
    sweep_expired,
)
from app.core.config import settings
from app.db import Repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/auth", tags=["auth"])
me_router = APIRouter(tags=["auth"])

SIGNUP_MIN_PASSWORD = 12
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_SCOPES = ("openid", "email", "profile")
# F8-AC1: if a sensitive scope ever appears above, production refuses to start.
SENSITIVE_GOOGLE_SCOPES = {
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/cloud-platform",
}


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=SIGNUP_MIN_PASSWORD, max_length=128)
    display_name: str | None = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MeResponse(BaseModel):
    id: str
    email: str
    display_name: str | None


class ResetRequest(BaseModel):
    email: EmailStr


class ResetConfirmRequest(BaseModel):
    token: str
    password: str = Field(min_length=SIGNUP_MIN_PASSWORD, max_length=128)


def _hit_rate_limit(repo: Repository, bucket: str, identifier: str, limit: int) -> None:
    """Count one attempt; the identifier is hashed so no address is stored."""
    key = hashlib.sha256(identifier.lower().encode()).hexdigest()
    if repo.hit_rate_limit(bucket, key) > limit:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.",
                            headers={"Retry-After": "3600"})


def _me(user: dict) -> MeResponse:
    return MeResponse(id=str(user["id"]), email=user["email"],
                      display_name=user["display_name"])


def _login(request: Request, response: Response, repo: Repository, user: dict) -> MeResponse:
    sweep_expired()
    set_session_cookie(response, create_session(repo, user["id"]))
    return _me(user)


@router.post("/signup", status_code=201)
def signup(request: Request, response: Response, data: SignupRequest) -> MeResponse:
    repo: Repository = request.app.state.repo
    _hit_rate_limit(repo, "signup", data.email, 5)

    try:
        user = repo.create_user(data.email.lower(), hash_password(data.password), None,
                                data.display_name)
    except Exception as exc:
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise HTTPException(status_code=409,
                                detail="An account with this email already exists.")
        raise
    return _login(request, response, repo, user)


@router.post("/login")
def login(request: Request, response: Response, data: LoginRequest) -> MeResponse:
    repo: Repository = request.app.state.repo
    _hit_rate_limit(repo, "login", data.email, 10)

    user = repo.get_user_by_email(data.email.lower())
    if user and user["password_hash"]:
        valid = verify_password(data.password, user["password_hash"])
    else:
        verify_password(data.password, dummy_hash())
        valid = False

    if not valid:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return _login(request, response, repo, user)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response,
           token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME)) -> None:
    if token:
        repo: Repository = request.app.state.repo
        repo.delete_session(hash_token(token))
    clear_session_cookie(response)


@me_router.get("/v1/me")
def me(request: Request, user_id: uuid.UUID = Depends(require_user)) -> MeResponse:
    user = request.app.state.repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _me(user)


@router.post("/reset/request", status_code=202)
def reset_request(request: Request, data: ResetRequest) -> dict:
    """Always the same 202 and body, whether or not the address exists (F8-AC3)."""
    repo: Repository = request.app.state.repo
    _hit_rate_limit(repo, "reset", data.email, 3)

    user = repo.get_user_by_email(data.email.lower())
    if user:
        token = new_auth_token()
        repo.create_auth_token(hash_token(token), user["id"], "password_reset",
                               datetime.now(timezone.utc) + timedelta(minutes=30))
        if settings.BREVO_API_KEY and settings.BREVO_SENDER:
            try:
                _send_reset_email(user["email"], token)
            except Exception as exc:
                logger.warning("Reset email failed: %s", type(exc).__name__)

    return {"message": "If an account with that email exists, a reset link has been sent."}


@router.post("/reset/confirm")
def reset_confirm(request: Request, data: ResetConfirmRequest) -> dict:
    repo: Repository = request.app.state.repo
    token_row = repo.consume_auth_token(hash_token(data.token))
    if not token_row:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    repo.set_password(token_row["user_id"], hash_password(data.password))
    repo.delete_all_sessions_for_user(token_row["user_id"])
    return {"message": "Password has been reset. You can now sign in."}


def _send_reset_email(email: str, token: str) -> None:
    reset_url = f"{settings.APP_ORIGIN}/reset?token={token}"
    text = (f"You requested a password reset. Visit {reset_url} to set a new password. "
            "The link expires in 30 minutes.")
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": settings.BREVO_API_KEY, "Content-Type": "application/json"},
            json={
                "sender": {"email": settings.BREVO_SENDER, "name": "FairLens"},
                "to": [{"email": email}],
                "subject": "Reset your FairLens password",
                "textContent": text,
                "htmlContent": f'<p>{text}</p><p><a href="{reset_url}">Set a new password</a></p>',
            },
        )
        resp.raise_for_status()


def _google_redirect_uri() -> str:
    return f"{settings.APP_ORIGIN}/api/v1/auth/google/callback"


@router.get("/google/start")
def google_start() -> RedirectResponse:
    if not settings.google_enabled:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")

    verifier = secrets.token_urlsafe(32)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": _google_redirect_uri(),
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    resp = RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{urlencode(params)}", status_code=302)
    for key, value in (("fl_g_state", state), ("fl_g_verifier", verifier)):
        resp.set_cookie(key=key, value=value, httponly=True, secure=settings.cookie_secure,
                        samesite="lax", path="/", max_age=600)
    return resp


@router.get("/google/callback")
def google_callback(
    request: Request,
    code: str = Query(default=""),
    state: str = Query(default=""),
    error: str | None = Query(default=None),
) -> RedirectResponse:
    def fail(reason: str) -> RedirectResponse:
        resp = RedirectResponse(url=f"{settings.APP_ORIGIN}/login?error={reason}", status_code=302)
        for key in ("fl_g_state", "fl_g_verifier"):
            resp.delete_cookie(key, path="/")
        return resp

    if error:
        logger.warning("Google OAuth error: %s", error)
        return fail("google_denied")

    cookie_state = request.cookies.get("fl_g_state")
    verifier = request.cookies.get("fl_g_verifier")
    if not cookie_state or not secrets.compare_digest(cookie_state, state):
        return fail("invalid_state")
    if not verifier or not code:
        return fail("invalid_verifier")

    with httpx.Client(timeout=20.0) as client:
        token_resp = client.post(GOOGLE_TOKEN_URL, data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": _google_redirect_uri(),
            "grant_type": "authorization_code",
            "code_verifier": verifier,
        })
        token_resp.raise_for_status()
        userinfo_resp = client.get(GOOGLE_USERINFO_URL, headers={
            "Authorization": f"Bearer {token_resp.json()['access_token']}"})
        userinfo_resp.raise_for_status()
        info = userinfo_resp.json()

    if not info.get("email_verified"):
        return fail("email_not_verified")

    google_sub, email = info["sub"], info["email"].lower()
    repo: Repository = request.app.state.repo
    user = repo.get_user_by_google_sub(google_sub) or repo.get_user_by_email(email)
    if user and not user["google_sub"]:
        user = repo.link_google_sub(user["id"], google_sub)
    if not user:
        user = repo.create_user(email, None, google_sub, info.get("name"))

    sweep_expired()
    resp = RedirectResponse(url=f"{settings.APP_ORIGIN}/", status_code=302)
    set_session_cookie(resp, create_session(repo, user["id"]))
    for key in ("fl_g_state", "fl_g_verifier"):
        resp.delete_cookie(key, path="/")
    return resp
