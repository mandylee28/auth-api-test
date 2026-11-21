import time


def test_logout_revokes_access_token(client, valid_user):
    token = client.login(**valid_user).json()["access_token"]
    assert client.me(token).status_code == 200

    resp = client.logout(token)
    assert resp.status_code == 200
    assert resp.json()["status"] == "logged out"

    assert client.me(token).status_code == 401


def test_logout_revokes_paired_refresh_token(client, valid_user):
    login_data = client.login(**valid_user).json()
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    resp = client.logout(access_token)
    assert resp.status_code == 200

    assert client.refresh(refresh_token=refresh_token).status_code == 401


def test_logout_without_token_returns_401(client):
    assert client.logout().status_code == 401


def test_logout_with_invalid_token_returns_401(client):
    assert client.logout("not-a-real-token").status_code == 401


def test_logout_twice_returns_401_second_time(client, valid_user):
    token = client.login(**valid_user).json()["access_token"]

    first = client.logout(token)
    assert first.status_code == 200

    second = client.logout(token)
    assert second.status_code == 401


def test_logout_one_session_does_not_affect_other(client, valid_user):
    first = client.login(**valid_user).json()
    second = client.login(**valid_user).json()
    assert first["access_token"] != second["access_token"]

    resp = client.logout(first["access_token"])
    assert resp.status_code == 200

    assert client.me(first["access_token"]).status_code == 401
    assert client.me(second["access_token"]).status_code == 200


def test_logout_with_expired_token_returns_401(client, valid_user):
    token = client.login(**valid_user).json()["access_token"]

    time.sleep(3)

    resp = client.logout(token)
    assert resp.status_code == 401
    assert resp.json()["detail"] == "token expired"
