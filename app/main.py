"""Mock authentication service used as the system under test.

Week 1 scope: /login, /me, /health, /reset.
Lockout and 2FA are added in week 2.
"""
import secrets
import time

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mock Auth Service")

USERS = {"alice@example.com": "Passw0rd!"}
TOKENS: dict[str, str] = {}  # token -> email
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 300
FAILED_ATTEMPTS = {}
LOCKED_UNTIL = {}


class LoginRequest(BaseModel):
    email: str
    password: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reset")
def reset():
    """Test-only endpoint: clear all state so each test starts clean."""
    TOKENS.clear()
    FAILED_ATTEMPTS.clear()
    LOCKED_UNTIL.clear()
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

    FAILED_ATTEMPTS.pop(body.email, None)
    LOCKED_UNTIL.pop(body.email, None)

    token = secrets.token_urlsafe(32)
    TOKENS[token] = body.email
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me")
def me(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing token")
    email = TOKENS.get(authorization.removeprefix("Bearer ").strip())
    if email is None:
        raise HTTPException(status_code=401, detail="invalid token")
    return {"email": email}
