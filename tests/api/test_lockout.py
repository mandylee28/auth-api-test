import time


def test_account_locks_after_five_failed_logins(client, valid_user):
    for _ in range(5):
        resp = client.login(email=valid_user["email"], password="Wrong123!")
        assert resp.status_code == 401
    resp = client.login(**valid_user)
    assert resp.status_code == 423


def test_locked_account_rejects_wrong_password_too(client, valid_user):
    for _ in range(5):
        resp = client.login(email=valid_user["email"], password="Wrong123!")
        assert resp.status_code == 401
    resp = client.login(email=valid_user["email"], password="Wrong123!")
    assert resp.status_code == 423


def test_successful_login_resets_failure_count(client, valid_user):
    for _ in range(4):
        resp = client.login(email=valid_user["email"], password="Wrong123!")
        assert resp.status_code == 401
    resp = client.login(**valid_user)
    assert resp.status_code == 200
    resp = client.login(email=valid_user["email"], password="Wrong123!")
    assert resp.status_code == 401


def test_account_unlocks_after_lockout_expires(client, valid_user):
    for _ in range(5):
        resp = client.login(email=valid_user["email"], password="Wrong123!")
        assert resp.status_code == 401
    resp = client.login(**valid_user)
    assert resp.status_code == 423
    time.sleep(3)
    resp = client.login(**valid_user)
    assert resp.status_code == 200
