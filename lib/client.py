"""Thin API client. Tests talk to this, never to requests directly,
so a change in the API only needs fixing in one place (same idea as Page Object Model)."""

import requests


def _lang_headers(lang: str | None) -> dict[str, str]:
    """Accept-Language header for the requested language, or nothing."""
    return {"Accept-Language": lang} if lang else {}


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

    def login(self, email: str, password: str, lang: str | None = None) -> requests.Response:
        return self.session.post(
            self._url("/login"),
            json={"email": email, "password": password},
            headers=_lang_headers(lang),
            timeout=self.timeout,
        )

    def verify_2fa(self, temp_token: str, code: str, lang: str | None = None) -> requests.Response:
        return self.session.post(
            self._url("/verify-2fa"),
            json={"temp_token": temp_token, "code": code},
            headers=_lang_headers(lang),
            timeout=self.timeout,
        )

    def refresh(self, refresh_token: str, lang: str | None = None) -> requests.Response:
        return self.session.post(
            self._url("/refresh"),
            json={"refresh_token": refresh_token},
            headers=_lang_headers(lang),
            timeout=self.timeout,
        )

    def logout(self, token: str | None = None, lang: str | None = None) -> requests.Response:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        headers.update(_lang_headers(lang))
        return self.session.post(self._url("/logout"), headers=headers, timeout=self.timeout)

    def post_raw(self, path: str, **kwargs) -> requests.Response:
        """For malformed-request tests that the typed helpers cannot express."""
        return self.session.post(self._url(path), timeout=self.timeout, **kwargs)

    def me(self, token: str | None = None, lang: str | None = None) -> requests.Response:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        headers.update(_lang_headers(lang))
        return self.session.get(self._url("/me"), headers=headers, timeout=self.timeout)

    def get_time(
        self, tz: str, at: int | None = None, lang: str | None = None
    ) -> requests.Response:
        params = {"tz": tz, "at": at}
        return self.session.get(
            self._url("/time"),
            params=params,
            headers=_lang_headers(lang),
            timeout=self.timeout,
        )
