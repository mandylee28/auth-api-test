import time


def test_login_returns_refresh_token_and_expires_in(client, valid_user):
    resp = client.login(**valid_user)
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["expires_in"] == 2
    assert data["refresh_token"] != data["access_token"]


def test_refresh_with_valid_token_returns_new_tokens(client, valid_user):
    login_data = client.login(**valid_user).json()
    old_access = login_data["access_token"]
    old_refresh = login_data["refresh_token"]

    resp = client.refresh(refresh_token=old_refresh)
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["access_token"] != old_access
    assert data["refresh_token"]
    assert data["refresh_token"] != old_refresh
    assert data["expires_in"] == 2

    me_resp = client.me(data["access_token"])
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == valid_user["email"]


def test_refresh_with_invalid_token_returns_401(client):
    resp = client.refresh(refresh_token="not-a-real-refresh-token")
    assert resp.status_code == 401


def test_old_refresh_token_cannot_be_reused(client, valid_user):
    login_data = client.login(**valid_user).json()
    old_refresh = login_data["refresh_token"]

    first = client.refresh(refresh_token=old_refresh)
    assert first.status_code == 200

    second = client.refresh(refresh_token=old_refresh)
    assert second.status_code == 401


def test_bob_verify_2fa_returns_refresh_token(client):
    login_resp = client.login(email="bob@example.com", password="BobPass123!")
    temp_token = login_resp.json()["temp_token"]

    resp = client.verify_2fa(temp_token=temp_token, code="123456")
    assert resp.status_code == 200
    assert resp.json()["refresh_token"]
    assert resp.json()["expires_in"] == 2


def test_access_token_expires_after_ttl(client, valid_user):
    token = client.login(**valid_user).json()["access_token"]
    assert client.me(token).status_code == 200
    time.sleep(3)
    assert client.me(token).status_code == 401


def test_refresh_still_works_after_access_token_expires(client, valid_user):
    login_data = client.login(**valid_user).json()
    old_access = login_data["access_token"]
    refresh_token = login_data["refresh_token"]
    time.sleep(3)
    assert client.me(old_access).status_code == 401

    resp = client.refresh(refresh_token=refresh_token)
    assert resp.status_code == 200
    new_access = resp.json()["access_token"]
    assert client.me(new_access).status_code == 200


def test_refresh_token_expires_after_ttl(client, valid_user):
    refresh_token = client.login(**valid_user).json()["refresh_token"]

    time.sleep(6)

    resp = client.refresh(refresh_token=refresh_token)
    assert resp.status_code == 401
    assert resp.json()["detail"] == "refresh token expired"


def test_default_ttls_are_production_values():
    import app.main as main

    assert main.ACCESS_TOKEN_TTL_SECONDS == 3600
    assert main.REFRESH_TOKEN_TTL_SECONDS == 7 * 24 * 3600
    assert main.LOCKOUT_SECONDS == 300
