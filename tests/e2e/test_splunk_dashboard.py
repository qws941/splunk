"""
E2E tests for Splunk Web Dashboard using Playwright.

Tests the slack_test_dashboard.xml against Splunk Web.
Requires: Splunk running at SPLUNK_URL (default: http://192.168.50.150:8000)
"""

import os
import pytest

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

SPLUNK_URL = os.getenv("SPLUNK_URL", "http://192.168.50.150:8000")
SPLUNK_USER = os.getenv("SPLUNK_USER", "admin")
SPLUNK_PASS = os.getenv("SPLUNK_PASS", "")


pytestmark = pytest.mark.skipif(
    not PLAYWRIGHT_AVAILABLE,
    reason="pytest-playwright not installed"
)


@pytest.fixture
def authenticated_page():
    """Create authenticated Splunk browser session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        page.goto(f"{SPLUNK_URL}/en-US/account/login")

        if page.query_selector('input[name="username"]'):
            page.fill('input[name="username"]', SPLUNK_USER)
            page.fill('input[name="password"]', SPLUNK_PASS)
            page.click('input[type="submit"]')

            page.wait_for_url("**/app/**", timeout=10000)

        yield page

        context.close()
        browser.close()


@pytest.mark.splunk_live
class TestSplunkLogin:

    def test_login_page_accessible(self, playwright):
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        page.goto(f"{SPLUNK_URL}/en-US/account/login")

        assert page.query_selector('input[name="username"]') is not None
        context.close()
        browser.close()

    def test_can_authenticate(self, authenticated_page):
        if not SPLUNK_PASS:
            pytest.skip("SPLUNK_PASS not set")

        assert "/account/login" not in authenticated_page.url


@pytest.mark.splunk_live
class TestSlackTestDashboard:

    DASHBOARD_PATH = "/en-US/app/security_alert/slack_test_dashboard"

    def test_dashboard_loads(self, authenticated_page):
        if not SPLUNK_PASS:
            pytest.skip("SPLUNK_PASS not set")

        authenticated_page.goto(f"{SPLUNK_URL}{self.DASHBOARD_PATH}")
        authenticated_page.wait_for_load_state("networkidle", timeout=30000)

        title = authenticated_page.query_selector(".dashboard-title")
        assert title is not None

    def test_dashboard_has_alert_dropdown(self, authenticated_page):
        if not SPLUNK_PASS:
            pytest.skip("SPLUNK_PASS not set")

        authenticated_page.goto(f"{SPLUNK_URL}{self.DASHBOARD_PATH}")
        authenticated_page.wait_for_load_state("networkidle")

        dropdown = authenticated_page.query_selector('select, [data-component="Dropdown"]')
        assert dropdown is not None

    def test_dashboard_has_panels(self, authenticated_page):
        if not SPLUNK_PASS:
            pytest.skip("SPLUNK_PASS not set")

        authenticated_page.goto(f"{SPLUNK_URL}{self.DASHBOARD_PATH}")
        authenticated_page.wait_for_load_state("networkidle")

        panels = authenticated_page.query_selector_all(".dashboard-panel, .panel")
        assert len(panels) >= 2


@pytest.mark.splunk_live
class TestSplunkAppNavigation:

    def test_security_alert_app_accessible(self, authenticated_page):
        if not SPLUNK_PASS:
            pytest.skip("SPLUNK_PASS not set")

        authenticated_page.goto(f"{SPLUNK_URL}/en-US/app/security_alert")
        authenticated_page.wait_for_load_state("networkidle")

        assert "security_alert" in authenticated_page.url

    def test_saved_searches_page(self, authenticated_page):
        if not SPLUNK_PASS:
            pytest.skip("SPLUNK_PASS not set")

        authenticated_page.goto(
            f"{SPLUNK_URL}/en-US/manager/security_alert/saved/searches"
        )
        authenticated_page.wait_for_load_state("networkidle")

        table = authenticated_page.query_selector("table, .listing-table")
        assert table is not None


@pytest.mark.splunk_live
class TestSplunkSearch:

    def test_search_page_loads(self, authenticated_page):
        if not SPLUNK_PASS:
            pytest.skip("SPLUNK_PASS not set")

        authenticated_page.goto(f"{SPLUNK_URL}/en-US/app/security_alert/search")
        authenticated_page.wait_for_load_state("networkidle")

        search_bar = authenticated_page.query_selector(
            'textarea, input[type="text"], .search-bar'
        )
        assert search_bar is not None


@pytest.mark.splunk_live
class TestSplunkAlertActions:

    def test_alert_actions_page(self, authenticated_page):
        if not SPLUNK_PASS:
            pytest.skip("SPLUNK_PASS not set")

        authenticated_page.goto(
            f"{SPLUNK_URL}/en-US/manager/security_alert/alert_actions"
        )
        authenticated_page.wait_for_load_state("networkidle")

        authenticated_page.wait_for_timeout(2000)
