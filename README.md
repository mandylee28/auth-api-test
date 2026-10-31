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

## Design

- `app/` mock service (FastAPI), the system under test
- `lib/client.py` API client; tests never call `requests` directly
- `tests/conftest.py` session-scoped server fixture, per-test state reset for isolation
- `tests/api/` test cases, using `parametrize` for data-driven checks

## Covered so far

Login success, bad credentials (without leaking which emails exist), empty and missing fields,
token validation on a protected endpoint.

## Roadmap

Week 2: account lockout, 2FA, token expiry and refresh, logout.
Week 3: GitHub Actions CI, HTML report, failure summary tool.
