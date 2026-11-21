import os
import secrets
import time
import json


from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


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
LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"


def _load_messages() -> dict[str, dict[str, str]]:
    """Load one JSON file per language from locales/; English is the fallback."""
    messages = {}
    for path in sorted(LOCALES_DIR.glob("*.json")):
        messages[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    assert "en" in messages, "locales/en.json is required as the fallback language"
    return messages


MESSAGES = _load_messages()


def _messages_for(accept_language: str | None) -> dict[str, str]:
    """Messages for the requested language; fall back to English."""
    lang = (accept_language or "").split(",")[0].strip().split(";")[0].strip()
    return MESSAGES.get(lang, MESSAGES["en"])


def _t(key: str, accept_language: str | None) -> str:
    """Pick the message for the requested language; fall back to English."""
    return _messages_for(accept_language)[key]


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
def login(body: LoginRequest, accept_language: str | None = Header(default=None)):
    if not body.email.strip() or not body.password:
        raise HTTPException(
            status_code=400, detail=_t("email_and_password_required", accept_language)
        )

    locked_until = LOCKED_UNTIL.get(body.email)
    if locked_until and time.time() < locked_until:
        raise HTTPException(status_code=423, detail=_t("account_locked", accept_language))
    if locked_until:
        LOCKED_UNTIL.pop(body.email, None)
        FAILED_ATTEMPTS[body.email] = 0

    # Same message for unknown user and wrong password: do not leak which emails exist.
    if USERS.get(body.email) != body.password:
        count = FAILED_ATTEMPTS.get(body.email, 0) + 1
        FAILED_ATTEMPTS[body.email] = count
        if count >= MAX_FAILED_ATTEMPTS:
            LOCKED_UNTIL[body.email] = time.time() + LOCKOUT_SECONDS
        raise HTTPException(status_code=401, detail=_t("invalid_credentials", accept_language))

    if body.email in TWO_FA_USERS:
        temp_token = secrets.token_urlsafe(32)
        PENDING_2FA[temp_token] = body.email
        return {"requires_2fa": True, "temp_token": temp_token}

    FAILED_ATTEMPTS.pop(body.email, None)
    LOCKED_UNTIL.pop(body.email, None)

    return _issue_tokens(body.email)


@app.post("/verify-2fa")
def verify_2fa(body: Verify2FARequest, accept_language: str | None = Header(default=None)):
    email = PENDING_2FA.get(body.temp_token)
    if email is None:
        raise HTTPException(status_code=401, detail=_t("invalid_temp_token", accept_language))
    if body.code != TWO_FA_CODE:
        raise HTTPException(status_code=401, detail=_t("invalid_2fa_code", accept_language))
    PENDING_2FA.pop(body.temp_token, None)
    return _issue_tokens(email)


@app.post("/refresh")
def refresh(body: RefreshRequest, accept_language: str | None = Header(default=None)):
    record = REFRESH_TOKENS.get(body.refresh_token)
    if record is None:
        raise HTTPException(status_code=401, detail=_t("invalid_refresh_token", accept_language))
    if time.time() > record["expires_at"]:
        REFRESH_TOKENS.pop(body.refresh_token, None)
        raise HTTPException(status_code=401, detail=_t("refresh_token_expired", accept_language))
    email = record["email"]
    REFRESH_TOKENS.pop(body.refresh_token, None)
    return _issue_tokens(email)


@app.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    accept_language: str | None = Header(default=None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail=_t("missing_token", accept_language))
    token = authorization.removeprefix("Bearer ").strip()
    record = TOKENS.get(token)
    if record is None:
        raise HTTPException(status_code=401, detail=_t("invalid_token", accept_language))
    if time.time() > record["expires_at"]:
        TOKENS.pop(token, None)
        raise HTTPException(status_code=401, detail=_t("token_expired", accept_language))
    REFRESH_TOKENS.pop(record.get("refresh_token"), None)
    TOKENS.pop(token, None)
    return {"status": "logged out"}


@app.get("/me")
def me(
    authorization: str | None = Header(default=None),
    accept_language: str | None = Header(default=None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail=_t("missing_token", accept_language))
    token = authorization.removeprefix("Bearer ").strip()
    record = TOKENS.get(token)
    if record is None:
        raise HTTPException(status_code=401, detail=_t("invalid_token", accept_language))
    if time.time() > record["expires_at"]:
        TOKENS.pop(token, None)
        raise HTTPException(status_code=401, detail=_t("token_expired", accept_language))
    return {"email": record["email"]}


TIMEZONE_COUNTRIES = {
    "Asia/Bangkok": "country_bangkok",
    "Asia/Singapore": "country_singapore",
    "Asia/Seoul": "country_seoul",
}


@app.get("/time")
def get_time(
    tz: str,
    at: int | None = None,
    accept_language: str | None = Header(default=None),
):
    if tz not in TIMEZONE_COUNTRIES:
        raise HTTPException(status_code=400, detail=_t("unknown_timezone", accept_language))

    instant = at if at is not None else int(time.time())
    local = datetime.fromtimestamp(instant, tz=ZoneInfo(tz))
    messages = _messages_for(accept_language)
    country = messages[TIMEZONE_COUNTRIES[tz]]
    message = messages["time_message"].format(
        country=country,
        month=local.month,
        day=local.day,
        hour=local.hour,
        minute=local.minute,
    )
    return {"timezone": tz, "country": country, "message": message}
