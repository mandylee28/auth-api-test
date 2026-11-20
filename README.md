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
```

## Design

- `app/` mock service (FastAPI), the system under test
- `lib/client.py` API client; tests never call `requests` directly
- `tests/conftest.py` session-scoped server fixture, per-test state reset for isolation
- `tests/api/` test cases, using `parametrize` for data-driven checks

## Covered so far

Week 1: login success, bad credentials (without leaking which emails exist), empty and missing fields, token validation on a protected endpoint.

Week 2: account lockout (5 failed logins, 5-minute lock, 423), 2FA (temp token + code, bob only), token expiry (1 hour) and refresh token rotation (7 days), logout revokes the access token and its paired refresh token.

Week 3: GitHub Actions CI runs pytest on push and PR to main, HTML test report (pytest-html,
uploaded as a CI artifact), failure summary tool (`tools/summarize_failures.py` reads a JUnit XML report).


## Roadmap

Week 2: account lockout, 2FA, token expiry and refresh, logout. (done)
Week 3: GitHub Actions CI, HTML report, failure summary tool. (done)
