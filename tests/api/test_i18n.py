import json
import time
from pathlib import Path

import pytest

LOCALES_DIR = Path(__file__).resolve().parents[2] / "locales"


def _load_expected() -> dict[str, dict[str, str]]:
    """Expected messages, read from the same JSON files the server loads."""
    expected = {}
    for path in sorted(LOCALES_DIR.glob("*.json")):
        expected[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    return expected


EXPECTED = _load_expected()

LANGS = sorted(EXPECTED)


def test_all_languages_have_the_same_keys():
    en_keys = set(EXPECTED["en"])
    for lang, messages in EXPECTED.items():
        assert set(messages) == en_keys, lang
        assert all(isinstance(value, str) for value in messages.values()), lang


@pytest.mark.parametrize("lang", LANGS)
def test_login_wrong_password_message_is_localized(client, valid_user, lang):
    resp = client.login(email=valid_user["email"], password="wrong-password", lang=lang)
    assert resp.status_code == 401
    assert resp.json()["detail"] == EXPECTED[lang]["invalid_credentials"]


@pytest.mark.parametrize("lang", LANGS)
def test_login_missing_fields_message_is_localized(client, lang):
    resp = client.login(email="", password="Passw0rd!", lang=lang)
    assert resp.status_code == 400
    assert resp.json()["detail"] == EXPECTED[lang]["email_and_password_required"]


@pytest.mark.parametrize("lang", LANGS)
def test_locked_message_is_localized(client, valid_user, lang):
    for _ in range(5):
        resp = client.login(email=valid_user["email"], password="wrong-password", lang=lang)
        assert resp.status_code == 401

    resp = client.login(**valid_user, lang=lang)
    assert resp.status_code == 423
    assert resp.json()["detail"] == EXPECTED[lang]["account_locked"]


def test_expired_token_message_is_localized(client, valid_user):
    me_tokens = [client.login(**valid_user).json()["access_token"] for _ in LANGS]
    logout_tokens = [client.login(**valid_user).json()["access_token"] for _ in LANGS]

    time.sleep(3)

    for token, lang in zip(me_tokens, LANGS):
        resp = client.me(token, lang=lang)
        assert resp.status_code == 401
        assert resp.json()["detail"] == EXPECTED[lang]["token_expired"]

    for token, lang in zip(logout_tokens, LANGS):
        resp = client.logout(token, lang=lang)
        assert resp.status_code == 401
        assert resp.json()["detail"] == EXPECTED[lang]["token_expired"]


def test_refresh_expired_message_is_localized(client, valid_user):
    refresh_tokens = [client.login(**valid_user).json()["refresh_token"] for _ in LANGS]

    time.sleep(6)

    for refresh_token, lang in zip(refresh_tokens, LANGS):
        resp = client.refresh(refresh_token=refresh_token, lang=lang)
        assert resp.status_code == 401
        assert resp.json()["detail"] == EXPECTED[lang]["refresh_token_expired"]


@pytest.mark.parametrize("lang", LANGS)
def test_verify_2fa_wrong_code_message_is_localized(client, lang):
    login_resp = client.login(email="bob@example.com", password="BobPass123!")
    temp_token = login_resp.json()["temp_token"]

    resp = client.verify_2fa(temp_token=temp_token, code="000000", lang=lang)
    assert resp.status_code == 401
    assert resp.json()["detail"] == EXPECTED[lang]["invalid_2fa_code"]


@pytest.mark.parametrize("lang", LANGS)
def test_verify_2fa_invalid_temp_token_message_is_localized(client, lang):
    resp = client.verify_2fa(temp_token="not-a-real-temp-token", code="123456", lang=lang)
    assert resp.status_code == 401
    assert resp.json()["detail"] == EXPECTED[lang]["invalid_temp_token"]


@pytest.mark.parametrize("lang", LANGS)
def test_me_missing_and_invalid_token_messages_are_localized(client, lang):
    resp = client.me(lang=lang)
    assert resp.status_code == 401
    assert resp.json()["detail"] == EXPECTED[lang]["missing_token"]

    resp = client.me("not-a-real-token", lang=lang)
    assert resp.status_code == 401
    assert resp.json()["detail"] == EXPECTED[lang]["invalid_token"]


def test_missing_language_defaults_to_english(client, valid_user):
    resp = client.login(email=valid_user["email"], password="wrong-password")
    assert resp.status_code == 401
    assert resp.json()["detail"] == EXPECTED["en"]["invalid_credentials"]


def test_unsupported_language_falls_back_to_english(client, valid_user):
    resp = client.login(email=valid_user["email"], password="wrong-password", lang="fr")
    assert resp.status_code == 401
    assert resp.json()["detail"] == EXPECTED["en"]["invalid_credentials"]


def test_language_header_with_quality_values(client, valid_user):
    resp = client.login(
        email=valid_user["email"],
        password="wrong-password",
        lang="zh-CN,zh;q=0.9,en;q=0.8",
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == EXPECTED["zh-CN"]["invalid_credentials"]
