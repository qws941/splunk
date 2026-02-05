"""
E2E tests for DDD Domain Layer.

Tests the domains/ module structure and behavior via API endpoints.
- defense/: Circuit breaker, retry logic
- integration/: FAZ, Splunk, Slack connectors
- security/: Event processor
"""

import os
import time
import subprocess
from pathlib import Path

import pytest
import requests


BACKEND_PORT = 3104
STARTUP_TIMEOUT = 15


@pytest.fixture(scope="module")
def project_root() -> Path:
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def domains_path(project_root: Path) -> Path:
    return project_root / "domains"


@pytest.fixture(scope="module")
def backend_server(project_root: Path):
    """Start backend server for testing domain behavior via API."""
    server_script = project_root / "backend" / "server.js"

    if not server_script.exists():
        pytest.skip(f"Backend server not found: {server_script}")

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

    base_url = f"http://localhost:{BACKEND_PORT}"
    start_time = time.time()
    while time.time() - start_time < STARTUP_TIMEOUT:
        try:
            response = requests.get(f"{base_url}/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)
    else:
        process.kill()
        stdout, stderr = process.communicate()
        pytest.fail(
            f"Backend server failed to start\n"
            f"stdout: {stdout.decode()}\n"
            f"stderr: {stderr.decode()}"
        )

    yield base_url

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.mark.domain
class TestDomainStructure:
    """Verify domain module structure exists."""

    def test_defense_module_exists(self, domains_path):
        defense_dir = domains_path / "defense"
        assert defense_dir.exists(), "defense/ domain should exist"
        assert defense_dir.is_dir()

    def test_integration_module_exists(self, domains_path):
        integration_dir = domains_path / "integration"
        assert integration_dir.exists(), "integration/ domain should exist"
        assert integration_dir.is_dir()

    def test_security_module_exists(self, domains_path):
        security_dir = domains_path / "security"
        assert security_dir.exists(), "security/ domain should exist"
        assert security_dir.is_dir()

    def test_circuit_breaker_file_exists(self, domains_path):
        circuit_breaker = domains_path / "defense" / "circuit-breaker.js"
        assert circuit_breaker.exists(), "circuit-breaker.js should exist"

    def test_faz_connector_file_exists(self, domains_path):
        faz_connector = domains_path / "integration" / "fortianalyzer-direct-connector.js"
        assert faz_connector.exists(), "fortianalyzer-direct-connector.js should exist"

    def test_slack_connector_file_exists(self, domains_path):
        slack_connector = domains_path / "integration" / "slack-connector.js"
        assert slack_connector.exists(), "slack-connector.js should exist"

    def test_splunk_connector_file_exists(self, domains_path):
        splunk_connector = domains_path / "integration" / "splunk-api-connector.js"
        assert splunk_connector.exists(), "splunk-api-connector.js should exist"

    def test_event_processor_file_exists(self, domains_path):
        processor = domains_path / "security" / "security-event-processor.js"
        assert processor.exists(), "security-event-processor.js should exist"


@pytest.mark.domain
class TestDefenseDomain:
    """Test defense domain (circuit breaker) via API."""

    def test_stats_includes_processor_info(self, backend_server):
        """Stats should include processor information."""
        response = requests.get(f"{backend_server}/api/stats")
        data = response.json()

        assert data["success"] is True
        assert "processor" in data

    def test_connections_reflect_circuit_state(self, backend_server):
        """Connection status should reflect circuit breaker state."""
        response = requests.get(f"{backend_server}/api/stats")
        data = response.json()

        connections = data.get("connections", {})
        assert isinstance(connections, dict)
        assert len(connections) > 0


@pytest.mark.domain
class TestSecurityDomain:
    """Test security domain (event processor) via API."""

    def test_processor_stats_available(self, backend_server):
        """Processor stats should be available in stats endpoint."""
        response = requests.get(f"{backend_server}/api/stats")
        data = response.json()

        assert "processor" in data
        processor = data["processor"]
        assert isinstance(processor, dict)

    def test_events_processed_through_security_domain(self, backend_server):
        """Events endpoint should work (uses security domain)."""
        response = requests.get(f"{backend_server}/api/events")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True


@pytest.mark.domain
class TestIntegrationDomain:
    """Test integration domain (connectors) via API."""

    def test_all_connectors_status_available(self, backend_server):
        """All connector statuses should be in stats."""
        response = requests.get(f"{backend_server}/api/stats")
        data = response.json()

        connections = data.get("connections", {})

        expected = ["fortianalyzer", "splunk", "slack"]
        for conn_name in expected:
            assert conn_name in connections, f"Missing connector status: {conn_name}"

    def test_faz_connector_provides_events(self, backend_server):
        """FAZ connector should provide events data."""
        response = requests.get(f"{backend_server}/api/events?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert "events" in data

    def test_slack_connector_testable(self, backend_server):
        """Slack connector should be testable via API."""
        response = requests.get(f"{backend_server}/api/slack/test")
        assert response.status_code in [200, 500]

        data = response.json()
        assert "success" in data


@pytest.mark.domain
class TestDomainBoundaries:
    """Test that domain boundaries are respected."""

    def test_stats_aggregates_all_domains(self, backend_server):
        """Stats should aggregate info from all domains."""
        response = requests.get(f"{backend_server}/api/stats")
        data = response.json()

        assert "processor" in data
        assert "connections" in data
        assert "timestamp" in data

    def test_events_flow_through_domains(self, backend_server):
        """Events should flow: FAZ -> Security -> Response."""
        response = requests.get(f"{backend_server}/api/events")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "events" in data

    def test_correlation_uses_security_domain(self, backend_server):
        """Correlation should use security domain processing."""
        response = requests.get(f"{backend_server}/api/correlation")
        assert response.status_code == 200

        data = response.json()
        assert "rules" in data
        assert "summary" in data
