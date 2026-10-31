import pytest


def test_login_success_returns_bearer_token(client, valid_user):
    resp = client.login(**valid_user)

    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) >= 32


def test_each_login_issues_a_different_token(client, valid_user):
    first = client.login(**valid_user).json()["access_token"]
    second = client.login(**valid_user).json()["access_token"]

    assert first != second


@pytest.mark.parametrize(
    "email, password",
    [
        ("alice@example.com", "wrong-password"),
        ("nobody@example.com", "Passw0rd!"),
        ("ALICE@EXAMPLE.COM", "Passw0rd!"),
    ],
    ids=["wrong_password", "unknown_user", "email_case_mismatch"],
)
def test_login_rejects_bad_credentials(client, email, password):
    resp = client.login(email, password)

    assert resp.status_code == 401
    assert "access_token" not in resp.json()


def test_error_message_does_not_reveal_whether_user_exists(client):
    wrong_pw = client.login("alice@example.com", "wrong").json()
    unknown = client.login("nobody@example.com", "wrong").json()

    assert wrong_pw == unknown


@pytest.mark.parametrize(
    "email, password",
    [("", "Passw0rd!"), ("alice@example.com", ""), ("", ""), ("   ", "Passw0rd!")],
    ids=["empty_email", "empty_password", "both_empty", "blank_email"],
)
def test_login_rejects_empty_fields(client, email, password):
    assert client.login(email, password).status_code == 400


@pytest.mark.parametrize(
    "payload",
    [{}, {"email": "alice@example.com"}, {"password": "Passw0rd!"}],
    ids=["no_fields", "missing_password", "missing_email"],
)
def test_login_rejects_missing_fields(client, payload):
    assert client.post_raw("/login", json=payload).status_code == 422


def test_me_returns_user_for_valid_token(client, valid_user):
    token = client.login(**valid_user).json()["access_token"]

    resp = client.me(token)

    assert resp.status_code == 200
    assert resp.json() == {"email": valid_user["email"]}


def test_me_rejects_request_without_token(client):
    assert client.me().status_code == 401


def test_me_rejects_made_up_token(client):
    assert client.me("not-a-real-token").status_code == 401
