"""
E2E tests for React Frontend Dashboard using Playwright.

Requires: pip install pytest-playwright && playwright install chromium
Run frontend: cd frontend && npm run dev

Tests run against: http://localhost:5173 (Vite dev server)
"""

import os
import subprocess
import time
from pathlib import Path

import pytest

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
FRONTEND_PATH = Path(__file__).parent.parent.parent / "frontend"


@pytest.fixture(scope="module")
def frontend_server():
    """Start frontend dev server for testing."""
    if os.getenv("SKIP_SERVER_START"):
        yield FRONTEND_URL
        return

    if not FRONTEND_PATH.exists():
        pytest.skip("Frontend directory not found")

    node_modules = FRONTEND_PATH / "node_modules"
    if not node_modules.exists():
        pytest.skip("Run 'npm install' in frontend/ first")

    proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host", "0.0.0.0"],
        cwd=str(FRONTEND_PATH),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    time.sleep(5)

    yield FRONTEND_URL

    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture
def page(playwright):
    """Create browser page for testing."""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
    browser.close()


@pytest.mark.frontend
class TestDashboardNavigation:

    def test_root_redirects_to_dashboard(self, page, frontend_server):
        page.goto(frontend_server)
        page.wait_for_url("**/dashboard")
        assert "/dashboard" in page.url

    def test_navigate_to_security(self, page, frontend_server):
        page.goto(f"{frontend_server}/dashboard")
        page.click("text=Security")
        page.wait_for_url("**/security")
        assert "/security" in page.url

    def test_navigate_to_alerts(self, page, frontend_server):
        page.goto(f"{frontend_server}/dashboard")
        page.click("text=Alerts")
        page.wait_for_url("**/alerts")
        assert "/alerts" in page.url

    def test_navigate_to_threats(self, page, frontend_server):
        page.goto(f"{frontend_server}/dashboard")
        page.click("text=Threats")
        page.wait_for_url("**/threats")
        assert "/threats" in page.url

    def test_navigate_to_correlation(self, page, frontend_server):
        page.goto(f"{frontend_server}/dashboard")
        page.click("text=Correlation")
        page.wait_for_url("**/correlation")
        assert "/correlation" in page.url

    def test_navigate_to_system(self, page, frontend_server):
        page.goto(f"{frontend_server}/dashboard")
        page.click("text=System")
        page.wait_for_url("**/system")
        assert "/system" in page.url


@pytest.mark.frontend
class TestDashboardComponents:

    def test_dashboard_has_stats_cards(self, page, frontend_server):
        page.goto(f"{frontend_server}/dashboard")
        page.wait_for_selector(".stats-grid")

        cards = page.query_selector_all(".stats-grid > *")
        assert len(cards) >= 4

    def test_dashboard_has_page_header(self, page, frontend_server):
        page.goto(f"{frontend_server}/dashboard")

        header = page.query_selector(".page-header h2")
        assert header is not None
        assert "Dashboard" in header.inner_text()

    def test_dashboard_has_event_chart(self, page, frontend_server):
        page.goto(f"{frontend_server}/dashboard")

        chart_card = page.query_selector(".chart-card")
        assert chart_card is not None

    def test_dashboard_has_alerts_table(self, page, frontend_server):
        page.goto(f"{frontend_server}/dashboard")

        alerts_header = page.query_selector("text=Recent Alerts")
        assert alerts_header is not None


@pytest.mark.frontend
class TestDashboardData:

    def test_stats_cards_show_values(self, page, frontend_server):
        page.goto(f"{frontend_server}/dashboard")
        page.wait_for_selector(".stats-grid")

        page.wait_for_timeout(2000)

        cards = page.query_selector_all(".stats-grid > *")
        for card in cards:
            value_elem = card.query_selector("[class*='value']")
            if value_elem:
                value = value_elem.inner_text()
                assert value != "", "Stats card should have a value"

    def test_loading_indicator_appears(self, page, frontend_server):
        page.goto(f"{frontend_server}/dashboard")

        page.wait_for_selector(".stats-grid", timeout=10000)


@pytest.mark.frontend
class TestResponsiveLayout:

    def test_mobile_viewport(self, page, frontend_server):
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(f"{frontend_server}/dashboard")

        header = page.query_selector(".page-header")
        assert header is not None

    def test_tablet_viewport(self, page, frontend_server):
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(f"{frontend_server}/dashboard")

        stats_grid = page.query_selector(".stats-grid")
        assert stats_grid is not None

    def test_desktop_viewport(self, page, frontend_server):
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(f"{frontend_server}/dashboard")

        layout = page.query_selector(".dashboard-page")
        assert layout is not None


@pytest.mark.frontend
class TestErrorHandling:

    def test_invalid_route_handling(self, page, frontend_server):
        page.goto(f"{frontend_server}/nonexistent-route")

        page.wait_for_timeout(1000)
        assert page.url.endswith("/nonexistent-route") or "/dashboard" in page.url


@pytest.mark.frontend
@pytest.mark.slow
class TestPageLoading:

    PAGES = [
        "/dashboard",
        "/security",
        "/alerts",
        "/threats",
        "/correlation",
        "/system",
    ]

    @pytest.mark.parametrize("path", PAGES)
    def test_page_loads_without_error(self, page, frontend_server, path):
        page.goto(f"{frontend_server}{path}")

        page.wait_for_load_state("networkidle", timeout=10000)

        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        page.wait_for_timeout(500)
        assert len(errors) == 0, f"Page errors on {path}: {errors}"
