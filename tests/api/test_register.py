import pytest


def test_register_success_returns_201_and_user_can_log_in(client):
    resp = client.register("carol@example.com", "StrongPass1")
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "carol@example.com"
    assert body["status"] == "registered"

    resp = client.login("carol@example.com", "StrongPass1")
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.parametrize(
    "lang,detail",
    [
        ("en", "email already registered"),
        ("zh-CN", "该邮箱已注册"),
        ("zh-TW", "此電子郵件已註冊"),
        ("ms", "e-mel sudah didaftarkan"),
    ],
)
def test_register_duplicate_email_returns_409(client, lang, detail):
    resp = client.register("carol@example.com", "StrongPass1")
    assert resp.status_code == 201

    resp = client.register("carol@example.com", "StrongPass1", lang=lang)
    assert resp.status_code == 409
    assert resp.json()["detail"] == detail


@pytest.mark.parametrize(
    "bad_email",
    ["not-an-email", "carol@", "@example.com", "carol@example"],
)
def test_register_invalid_email_returns_400(client, bad_email):
    resp = client.register(bad_email, "StrongPass1")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "invalid email address"


@pytest.mark.parametrize("bad_password", ["short", "1234567"])
def test_register_weak_password_returns_400(client, bad_password):
    resp = client.register("carol@example.com", bad_password)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "password is too weak"


@pytest.mark.parametrize(
    "payload",
    [{}, {"email": "carol@example.com"}, {"password": "StrongPass1"}],
)
def test_register_missing_fields_returns_422(client, payload):
    resp = client.post_raw("/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "", "password": "StrongPass1"},
        {"email": "   ", "password": "StrongPass1"},
        {"email": "carol@example.com", "password": ""},
    ],
)
def test_register_empty_fields_returns_400(client, payload):
    resp = client.post_raw("/register", json=payload)
    assert resp.status_code == 400
    assert resp.json()["detail"] == "email and password are required"
