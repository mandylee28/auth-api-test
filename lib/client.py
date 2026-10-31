"""Thin API client. Tests talk to this, never to requests directly,
so a change in the API only needs fixing in one place (same idea as Page Object Model)."""
import requests


class AuthClient:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def health(self) -> requests.Response:
        return self.session.get(self._url("/health"), timeout=self.timeout)

    def reset(self) -> requests.Response:
        return self.session.post(self._url("/reset"), timeout=self.timeout)

    def login(self, email: str, password: str) -> requests.Response:
        return self.session.post(
            self._url("/login"),
            json={"email": email, "password": password},
            timeout=self.timeout,
        )

    def post_raw(self, path: str, **kwargs) -> requests.Response:
        """For malformed-request tests that the typed helpers cannot express."""
        return self.session.post(self._url(path), timeout=self.timeout, **kwargs)

    def me(self, token: str | None = None) -> requests.Response:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.session.get(self._url("/me"), headers=headers, timeout=self.timeout)
