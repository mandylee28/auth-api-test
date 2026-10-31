import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

from lib.client import AuthClient

ROOT = Path(__file__).resolve().parent.parent
VALID_USER = {"email": "alice@example.com", "password": "Passw0rd!"}


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def base_url():
    """Use AUTH_BASE_URL if set (test any deployed server); otherwise start the mock locally."""
    external = os.environ.get("AUTH_BASE_URL")
    if external:
        yield external
        return

    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                if requests.get(f"{url}/health", timeout=1).ok:
                    break
            except requests.ConnectionError:
                time.sleep(0.2)
        else:
            raise RuntimeError("mock server did not start in 15s")
        yield url
    finally:
        proc.terminate()
        proc.wait(timeout=5)


@pytest.fixture
def client(base_url):
    """Fresh client and clean server state for every test (test isolation)."""
    c = AuthClient(base_url)
    c.reset()
    return c


@pytest.fixture
def valid_user():
    return dict(VALID_USER)
