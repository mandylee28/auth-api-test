TWO_FA_USER = {"email": "bob@example.com", "password": "BobPass123!"}


def test_bob_login_returns_temp_token_not_access_token(client):
    resp = client.login(**TWO_FA_USER)
    assert resp.status_code == 200
    data = resp.json()
    assert data["requires_2fa"] is True
    assert data["temp_token"]
    assert "access_token" not in data


def test_bob_verify_with_correct_code_returns_access_token(client):
    login_resp = client.login(**TWO_FA_USER)
    temp_token = login_resp.json()["temp_token"]

    resp = client.verify_2fa(temp_token=temp_token, code="123456")
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    assert token

    me_resp = client.me(token)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "bob@example.com"


def test_bob_verify_with_wrong_code_returns_401(client):
    login_resp = client.login(**TWO_FA_USER)
    temp_token = login_resp.json()["temp_token"]

    resp = client.verify_2fa(temp_token=temp_token, code="000000")
    assert resp.status_code == 401
    assert "access_token" not in resp.json()


def test_temp_token_cannot_be_used_for_me(client):
    login_resp = client.login(**TWO_FA_USER)
    temp_token = login_resp.json()["temp_token"]

    resp = client.me(temp_token)
    assert resp.status_code == 401


def test_verify_with_invalid_temp_token_returns_401(client):
    resp = client.verify_2fa(temp_token="not-a-real-temp-token", code="123456")
    assert resp.status_code == 401


def test_temp_token_can_only_be_used_once(client):
    login_resp = client.login(**TWO_FA_USER)
    temp_token = login_resp.json()["temp_token"]

    first = client.verify_2fa(temp_token=temp_token, code="123456")
    assert first.status_code == 200

    second = client.verify_2fa(temp_token=temp_token, code="123456")
    assert second.status_code == 401
