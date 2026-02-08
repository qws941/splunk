# TESTS KNOWLEDGE BASE

**Scope:** E2E test suite (pytest)

## OVERVIEW

End-to-end tests covering Splunk app configs, backend API, domains, and frontend. Pytest with shared fixtures in `conftest.py`. Runs without live Splunk by default (`splunk_live` marker gates Splunk-dependent tests).

## STRUCTURE

```
tests/
├── conftest.py            # Shared fixtures (716 LOC)
├── pytest.ini             # Pytest configuration
└── e2e/                   # E2E test modules (13 files)
    ├── test_config_validation.py
    ├── test_saved_searches.py
    ├── test_slack_alert_action.py
    ├── test_bin_scripts.py
    ├── test_backend_api.py
    ├── test_domains.py
    ├── test_dashboard_xml.py
    ├── test_health_metrics.py
    ├── test_splunk_feature_checker.py
    ├── test_splunk_dashboard.py
    ├── test_fortigate_auto_response.py
    ├── test_splunk_app_installation.py
    └── test_live_splunk_integration.py
```

## HOW TO RUN

```bash
# All E2E tests (no Splunk required)
pytest tests/e2e -v -m "not splunk_live"

# With live Splunk connection
pytest tests/e2e -v

# Single test file
pytest tests/e2e/test_config_validation.py -v
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add shared fixture | `conftest.py` |
| Add E2E test | `e2e/test_{module}.py` |
| Skip without Splunk | `@pytest.mark.splunk_live` |
| Mock Slack webhook | `conftest.py` → `mock_slack_server` fixture |

## CONVENTIONS

| Rule | Convention |
|------|------------|
| Fixture scope | `session` for expensive setup |
| Splunk dependency | Gate with `@pytest.mark.splunk_live` |
| Splunk target | `192.168.50.150:8089` (default) |
| Mock Slack | `HTTPServer` in background thread |
| Test naming | `test_{module}.py` matching source module |

## ANTI-PATTERNS

| NEVER | Why |
|-------|-----|
| Require live Splunk by default | Tests must run in CI without Splunk |
| Inline test data | Use fixtures from `conftest.py` |
| Skip `conftest.py` fixtures | Shared setup prevents duplication |
| Import Splunk SDK unconditionally | Gate with `SPLUNK_SDK_AVAILABLE` flag |
