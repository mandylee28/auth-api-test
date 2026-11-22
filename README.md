# auth-api-tests


API test framework (Python, pytest, requests) for a mock authentication service.

Built to practise test design for identity flows: login, token handling, error behaviour.


## Run locally


```bash

python3 -m venv .venv && source .venv/bin/activate

pip install -r requirements.txt

pytest

```


The test session starts the mock service on a free port automatically.

To test an already running server instead: `AUTH_BASE_URL=http://host:port pytest`


## Test reports


```

pytest --html=report.html --self-contained-html # HTML report

pytest --junitxml=report.xml # JUnit XML for the summary tool

python tools/summarize_failures.py report.xml # failure summary

coverage combine # merge server coverage data

coverage report -m # coverage report (CI enforces 100%)


```


## Design


- `app/` mock service (FastAPI), the system under test
- `app/db.py` SQLite storage for users (stdlib `sqlite3`); tests use a separate database file
- `locales/` one JSON file per language; messages are picked by `Accept-Language`, English fallback; translations are managed in Crowdin and synced back as pull requests (see `crowdin.yml`)
- `lib/client.py` API client; tests never call `requests` directly
- `tests/conftest.py` session-scoped server fixture, per-test state reset for isolation
- `tests/api/` test cases, using `parametrize` for data-driven checks


## Covered so far

118 tests, 100% coverage of `app/` (CI enforces `--fail-under=100`).

Week 1: login success, bad credentials (without leaking which emails exist), empty and missing fields, token validation on a protected endpoint.

Week 2: account lockout (5 failed logins, 5-minute lock, 423), 2FA (temp token + code, bob only), token expiry (1 hour) and refresh token rotation (7 days),
logout revokes the access token and its paired refresh token.

Week 3: GitHub Actions CI runs pytest on push and PR to main, HTML test report (pytest-html,
uploaded as a CI artifact), failure summary tool (`tools/summarize_failures.py` reads a JUnit XML report).

Week 4: ruff lint and format check in CI, and 100% coverage enforced in CI. Multilingual messages (English, Simplified Chinese, Traditional Chinese, Malay) for auth errors and the time message; adding a language is one new JSON file, covered by tests automatically. Cross-timezone time (`GET /time` for Bangkok, Singapore, Seoul, Tokyo, London and New York; the same instant shown in each local time, 400 for an unsupported timezone). SQLite storage for users with `POST /register` (email format and password length checks, duplicate email returns 409, success returns 201; registered users survive a server restart).

Translations: managed in Crowdin (free plan) — the GitHub integration syncs `locales/en.json` as the source and returns translations as pull requests, which CI validates. `crowdin.yml` sets a custom commit message without `[ci skip]`, so Crowdin pull requests trigger CI.


## Roadmap


Week 2: account lockout, 2FA, token expiry and refresh, logout. (done)

Week 3: GitHub Actions CI, HTML report, failure summary tool. (done)

Week 4: lint and coverage gates, multilingual messages, cross-timezone time, SQLite storage, user registration. (done)

Week 5: more `/time` timezones (Tokyo, London, New York), Crowdin translation management. (done)

