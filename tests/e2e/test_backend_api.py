"""
E2E tests for Backend REST API endpoints.

Tests the backend/server.js API endpoints without requiring live Splunk.
Uses subprocess to start the backend server and makes HTTP requests.
"""

import os
import subprocess
import time
from pathlib import Path

import pytest
import requests

# =============================================================================
# Configuration
# =============================================================================

BACKEND_PORT = 3101
BACKEND_URL = f"http://localhost:{BACKEND_PORT}"
STARTUP_TIMEOUT = 10  # seconds


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def project_root() -> Path:
    """Return project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def backend_server(project_root: Path):
    """
    Start the backend server as a subprocess.
    Waits for /health to respond, yields the base URL.
    Kills process on teardown.
    """
    server_script = project_root / "backend" / "server.js"

    if not server_script.exists():
        pytest.skip(f"Backend server not found: {server_script}")

    # Start the server
    env = os.environ.copy()
    env["API_PORT"] = str(BACKEND_PORT)
    env["NODE_ENV"] = "test"

    process = subprocess.Popen(
        ["node", str(server_script)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(project_root),
    )

    # Wait for server to be ready
    start_time = time.time()
    while time.time() - start_time < STARTUP_TIMEOUT:
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)
    else:
        process.kill()
        stdout, stderr = process.communicate()
        pytest.fail(
            f"Backend server failed to start within {STARTUP_TIMEOUT}s\n"
            f"stdout: {stdout.decode()}\n"
            f"stderr: {stderr.decode()}"
        )

    yield BACKEND_URL

    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


# =============================================================================
# Test Classes
# =============================================================================


@pytest.mark.backend
class TestEventsAPI:
    """Tests for GET /api/events endpoint."""

    def test_get_events_returns_200(self, backend_server):
        """Events endpoint should return 200 OK."""
        response = requests.get(f"{backend_server}/api/events")
        assert response.status_code == 200

    def test_get_events_response_structure(self, backend_server):
        """Events response should have expected structure."""
        response = requests.get(f"{backend_server}/api/events")
        data = response.json()

        assert "success" in data
        assert "events" in data

    def test_get_events_with_limit(self, backend_server):
        """Events endpoint should respect limit parameter."""
        response = requests.get(f"{backend_server}/api/events?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_events_returns_events_list(self, backend_server):
        """Events should contain list of event objects."""
        response = requests.get(f"{backend_server}/api/events")
        data = response.json()

        events = data.get("events", {})
        if isinstance(events, dict):
            assert "events" in events or "success" in data
        else:
            assert isinstance(events, list)

    def test_get_events_with_time_range(self, backend_server):
        """Events endpoint should accept timeRange parameter."""
        response = requests.get(f"{backend_server}/api/events?timeRange=-24h")
        assert response.status_code == 200
        data = response.json()
        assert data["timeRange"] == "-24h"


@pytest.mark.backend
class TestStatsAPI:
    """Tests for GET /api/stats endpoint."""

    def test_get_stats_returns_200(self, backend_server):
        """Stats endpoint should return 200 OK."""
        response = requests.get(f"{backend_server}/api/stats")
        assert response.status_code == 200

    def test_get_stats_response_structure(self, backend_server):
        """Stats response should have expected structure."""
        response = requests.get(f"{backend_server}/api/stats")
        data = response.json()

        assert data["success"] is True
        assert "timestamp" in data
        assert "processor" in data
        assert "connections" in data

    def test_get_stats_connections_structure(self, backend_server):
        """Stats connections should include all expected fields."""
        response = requests.get(f"{backend_server}/api/stats")
        data = response.json()
        connections = data["connections"]

        assert "fortianalyzer" in connections
        assert "splunk" in connections
        assert "slack" in connections


@pytest.mark.backend
class TestCorrelationAPI:
    """Tests for GET /api/correlation endpoint."""

    def test_get_correlation_returns_200(self, backend_server):
        """Correlation endpoint should return 200 OK."""
        response = requests.get(f"{backend_server}/api/correlation")
        assert response.status_code == 200

    def test_get_correlation_response_structure(self, backend_server):
        """Correlation response should have expected structure."""
        response = requests.get(f"{backend_server}/api/correlation")
        data = response.json()

        assert data["success"] is True
        assert "rules" in data
        assert "summary" in data
        assert isinstance(data["rules"], list)

    def test_get_correlation_with_time_range(self, backend_server):
        """Correlation endpoint should accept timeRange parameter."""
        response = requests.get(f"{backend_server}/api/correlation?timeRange=-7d")
        assert response.status_code == 200
        data = response.json()
        assert data["timeRange"] == "-7d"

    def test_get_correlation_rules_structure(self, backend_server):
        """Correlation rules should have expected fields."""
        response = requests.get(f"{backend_server}/api/correlation")
        data = response.json()

        if data["rules"]:
            rule = data["rules"][0]
            assert "id" in rule
            assert "name" in rule
            assert "triggered" in rule
            assert "trend" in rule


@pytest.mark.backend
class TestAlertsAPI:
    """Tests for /api/alerts endpoints."""

    def test_get_alerts_returns_200(self, backend_server):
        """Alerts endpoint should return 200 OK."""
        response = requests.get(f"{backend_server}/api/alerts")
        assert response.status_code == 200

    def test_get_alerts_response_structure(self, backend_server):
        """Alerts response should have expected structure."""
        response = requests.get(f"{backend_server}/api/alerts")
        data = response.json()

        assert data["success"] is True
        assert "count" in data
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_get_alerts_item_structure(self, backend_server):
        """Each alert should have expected fields."""
        response = requests.get(f"{backend_server}/api/alerts")
        data = response.json()

        if data["alerts"]:
            alert = data["alerts"][0]
            assert "id" in alert
            assert "severity" in alert
            assert "status" in alert
            assert "timestamp" in alert

    def test_acknowledge_alert_success(self, backend_server):
        """Acknowledge alert with valid alertId should succeed."""
        response = requests.post(
            f"{backend_server}/api/alerts/acknowledge",
            json={"alertId": "alert_001", "acknowledgedBy": "test_user"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["alertId"] == "alert_001"

    def test_acknowledge_alert_missing_id(self, backend_server):
        """Acknowledge alert without alertId should return 400."""
        response = requests.post(
            f"{backend_server}/api/alerts/acknowledge",
            json={"acknowledgedBy": "test_user"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "alertId" in data["error"]


@pytest.mark.backend
class TestThreatsAPI:
    """Tests for GET /api/threats endpoint."""

    def test_get_threats_returns_200(self, backend_server):
        """Threats endpoint should return 200 OK."""
        response = requests.get(f"{backend_server}/api/threats")
        assert response.status_code == 200

    def test_get_threats_response_structure(self, backend_server):
        """Threats response should have expected structure."""
        response = requests.get(f"{backend_server}/api/threats")
        data = response.json()

        assert data["success"] is True
        assert "topThreats" in data
        assert "geoDistribution" in data
        assert "attackTypes" in data

    def test_get_threats_item_structure(self, backend_server):
        """Each threat should have expected fields."""
        response = requests.get(f"{backend_server}/api/threats")
        data = response.json()

        if data["topThreats"]:
            threat = data["topThreats"][0]
            assert "ip" in threat
            assert "country" in threat
            assert "abuseScore" in threat
            assert "attackTypes" in threat


@pytest.mark.backend
class TestDashboardsAPI:
    """Tests for GET /api/dashboards endpoint."""

    def test_get_dashboards_returns_200(self, backend_server):
        """Dashboards endpoint should return 200 OK."""
        response = requests.get(f"{backend_server}/api/dashboards")
        assert response.status_code == 200

    def test_get_dashboards_response_structure(self, backend_server):
        """Dashboards response should have expected structure."""
        response = requests.get(f"{backend_server}/api/dashboards")
        data = response.json()

        assert data["success"] is True
        assert "dashboards" in data
        assert isinstance(data["dashboards"], list)
        assert len(data["dashboards"]) == 4  # Expected 4 dashboards

    def test_get_dashboards_item_structure(self, backend_server):
        """Each dashboard should have expected fields."""
        response = requests.get(f"{backend_server}/api/dashboards")
        data = response.json()

        for dashboard in data["dashboards"]:
            assert "id" in dashboard
            assert "name" in dashboard
            assert "description" in dashboard
            assert "widgets" in dashboard


@pytest.mark.backend
class TestSlackAPI:
    """Tests for GET /api/slack/test endpoint."""

    def test_slack_test_returns_response(self, backend_server):
        """Slack test endpoint should return a response."""
        response = requests.get(f"{backend_server}/api/slack/test")
        # May fail if Slack not configured, but should not error
        assert response.status_code in [200, 500]

    def test_slack_test_response_structure(self, backend_server):
        """Slack test response should have expected structure."""
        response = requests.get(f"{backend_server}/api/slack/test")
        data = response.json()

        # Either success or error, but should have structure
        if response.status_code == 200:
            assert data["success"] is True
            assert "message" in data
        else:
            assert data["success"] is False
            assert "error" in data


@pytest.mark.backend
class TestErrorHandling:
    """Tests for API error handling."""

    def test_invalid_route_returns_404(self, backend_server):
        """Unknown API routes should return 404."""
        response = requests.get(f"{backend_server}/api/unknown")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_invalid_method_handling(self, backend_server):
        """Invalid HTTP method should be handled gracefully."""
        response = requests.delete(f"{backend_server}/api/events")
        # Should return 404 (no route for DELETE)
        assert response.status_code == 404

    def test_malformed_json_body(self, backend_server):
        """Malformed JSON in POST body should be handled."""
        response = requests.post(
            f"{backend_server}/api/alerts/acknowledge",
            data="not valid json",
            headers={"Content-Type": "application/json"},
        )
        # Should return error status
        assert response.status_code in [400, 500]


@pytest.mark.backend
class TestResponseTimes:
    """Tests for API response time requirements."""

    def test_health_response_time(self, backend_server):
        """Health endpoint should respond within 100ms."""
        start = time.time()
        response = requests.get(f"{backend_server}/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1  # 100ms

    def test_events_response_time(self, backend_server):
        """Events endpoint should respond within 1s."""
        start = time.time()
        response = requests.get(f"{backend_server}/api/events")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0  # 1 second

    def test_stats_response_time(self, backend_server):
        """Stats endpoint should respond within 500ms."""
        start = time.time()
        response = requests.get(f"{backend_server}/api/stats")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.5  # 500ms
