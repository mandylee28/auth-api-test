import os
import secrets
import time

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mock Auth Service")

USERS = {"alice@example.com": "Passw0rd!", "bob@example.com": "BobPass123!"}
TOKENS: dict[str, dict] = {}  # token -> {"email": ..., "expires_at": ...}
REFRESH_TOKENS: dict[str, dict] = {}  # refresh_token -> {"email": ..., "expires_at": ...}
ACCESS_TOKEN_TTL_SECONDS = int(os.environ.get("ACCESS_TOKEN_TTL_SECONDS", "3600"))
REFRESH_TOKEN_TTL_SECONDS = int(os.environ.get("REFRESH_TOKEN_TTL_SECONDS", str(7 * 24 * 3600)))
LOCKOUT_SECONDS = int(os.environ.get("LOCKOUT_SECONDS", "300"))

TWO_FA_USERS = {"bob@example.com"}
TWO_FA_CODE = "123456"
PENDING_2FA: dict[str, str] = {}  # temp_token -> email

MAX_FAILED_ATTEMPTS = 5
FAILED_ATTEMPTS = {}
LOCKED_UNTIL = {}


class LoginRequest(BaseModel):
    email: str
    password: str


class Verify2FARequest(BaseModel):
    code: str
    temp_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _issue_tokens(email: str):
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    TOKENS[access_token] = {
        "email": email,
        "expires_at": time.time() + ACCESS_TOKEN_TTL_SECONDS,
        "refresh_token": refresh_token,
    }
    REFRESH_TOKENS[refresh_token] = {
        "email": email,
        "expires_at": time.time() + REFRESH_TOKEN_TTL_SECONDS,
    }
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_TTL_SECONDS,
        "refresh_token": refresh_token,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reset")
def reset():
    """Test-only endpoint: clear all state so each test starts clean."""
    TOKENS.clear()
    FAILED_ATTEMPTS.clear()
    LOCKED_UNTIL.clear()
    PENDING_2FA.clear()
    REFRESH_TOKENS.clear()
    return {"status": "reset"}


@app.post("/login")
def login(body: LoginRequest):
    if not body.email.strip() or not body.password:
        raise HTTPException(status_code=400, detail="email and password are required")

    locked_until = LOCKED_UNTIL.get(body.email)
    if locked_until and time.time() < locked_until:
        raise HTTPException(status_code=423, detail="account locked")
    if locked_until:
        LOCKED_UNTIL.pop(body.email, None)
        FAILED_ATTEMPTS[body.email] = 0

    # Same message for unknown user and wrong password: do not leak which emails exist.
    if USERS.get(body.email) != body.password:
        count = FAILED_ATTEMPTS.get(body.email, 0) + 1
        FAILED_ATTEMPTS[body.email] = count
        if count >= MAX_FAILED_ATTEMPTS:
            LOCKED_UNTIL[body.email] = time.time() + LOCKOUT_SECONDS
        raise HTTPException(status_code=401, detail="invalid credentials")

    if body.email in TWO_FA_USERS:
        temp_token = secrets.token_urlsafe(32)
        PENDING_2FA[temp_token] = body.email
        return {"requires_2fa": True, "temp_token": temp_token}

    FAILED_ATTEMPTS.pop(body.email, None)
    LOCKED_UNTIL.pop(body.email, None)

    return _issue_tokens(body.email)


@app.post("/verify-2fa")
def verify_2fa(body: Verify2FARequest):
    email = PENDING_2FA.get(body.temp_token)
    if email is None:
        raise HTTPException(status_code=401, detail="invalid temp token")
    if body.code != TWO_FA_CODE:
        raise HTTPException(status_code=401, detail="invalid 2fa code")
    PENDING_2FA.pop(body.temp_token, None)
    return _issue_tokens(email)


@app.post("/refresh")
def refresh(body: RefreshRequest):
    record = REFRESH_TOKENS.get(body.refresh_token)
    if record is None:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    if time.time() > record["expires_at"]:
        REFRESH_TOKENS.pop(body.refresh_token, None)
        raise HTTPException(status_code=401, detail="refresh token expired")
    email = record["email"]
    REFRESH_TOKENS.pop(body.refresh_token, None)
    return _issue_tokens(email)


@app.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing token")
    token = authorization.removeprefix("Bearer ").strip()
    record = TOKENS.get(token)
    if record is None:
        raise HTTPException(status_code=401, detail="invalid token")
    if time.time() > record["expires_at"]:
        TOKENS.pop(token, None)
        raise HTTPException(status_code=401, detail="token expired")
    REFRESH_TOKENS.pop(record.get("refresh_token"), None)
    TOKENS.pop(token, None)
    return {"status": "logged out"}


@app.get("/me")
def me(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing token")
    token = authorization.removeprefix("Bearer ").strip()
    record = TOKENS.get(token)
    if record is None:
        raise HTTPException(status_code=401, detail="invalid token")
    if time.time() > record["expires_at"]:
        TOKENS.pop(token, None)
        raise HTTPException(status_code=401, detail="token expired")
    return {"email": record["email"]}
