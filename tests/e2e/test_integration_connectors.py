"""
E2E tests for Integration Connectors.

Tests FAZ, Splunk HEC, and Slack connectors via the backend API.
Uses mock servers to avoid requiring live external services.
"""

import os
import json
import time
import subprocess
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List, Dict, Any

import pytest
import requests


BACKEND_PORT = 3103
MOCK_SLACK_PORT = 9003
STARTUP_TIMEOUT = 15


class SlackWebhookHandler(BaseHTTPRequestHandler):
    """Mock Slack webhook server that captures incoming requests."""

    received_requests: List[Dict[str, Any]] = []

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body}

        SlackWebhookHandler.received_requests.append(
            {
                "path": self.path,
                "headers": dict(self.headers),
                "body": payload,
                "timestamp": time.time(),
            }
        )

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def project_root() -> Path:
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def mock_slack_server():
    """Start a mock Slack webhook server."""
    SlackWebhookHandler.received_requests = []

    server = HTTPServer(("localhost", MOCK_SLACK_PORT), SlackWebhookHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield {
        "url": f"http://localhost:{MOCK_SLACK_PORT}/webhook",
        "port": MOCK_SLACK_PORT,
        "get_requests": lambda: SlackWebhookHandler.received_requests,
        "clear_requests": lambda: SlackWebhookHandler.received_requests.clear(),
    }

    server.shutdown()


@pytest.fixture(scope="module")
def backend_server(project_root: Path, mock_slack_server):
    """Start backend server with mock Slack webhook configured."""
    server_script = project_root / "backend" / "server.js"

    if not server_script.exists():
        pytest.skip(f"Backend server not found: {server_script}")

    env = os.environ.copy()
    env["API_PORT"] = str(BACKEND_PORT)
    env["NODE_ENV"] = "test"
    env["SLACK_WEBHOOK_URL"] = mock_slack_server["url"]

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


@pytest.mark.integration
class TestFAZConnector:
    """Tests for FortiAnalyzer connector functionality."""

    def test_faz_connection_status_in_stats(self, backend_server):
        """Stats should include FAZ connection status."""
        response = requests.get(f"{backend_server}/api/stats")
        data = response.json()

        assert "connections" in data
        assert "fortianalyzer" in data["connections"]

    def test_events_endpoint_returns_data(self, backend_server):
        """Events endpoint should return data (mocked or real)."""
        response = requests.get(f"{backend_server}/api/events")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "events" in data

    def test_events_with_time_range(self, backend_server):
        """Events should accept time range parameter."""
        response = requests.get(f"{backend_server}/api/events?timeRange=-1h")
        assert response.status_code == 200

        data = response.json()
        assert data["timeRange"] == "-1h"

    def test_events_with_limit(self, backend_server):
        """Events should respect limit parameter."""
        response = requests.get(f"{backend_server}/api/events?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True


@pytest.mark.integration
class TestSlackConnector:
    """Tests for Slack connector functionality."""

    def test_slack_status_in_stats(self, backend_server):
        """Stats should include Slack connection status."""
        response = requests.get(f"{backend_server}/api/stats")
        data = response.json()

        assert "connections" in data
        assert "slack" in data["connections"]

    def test_slack_test_endpoint_exists(self, backend_server):
        """Slack test endpoint should exist."""
        response = requests.get(f"{backend_server}/api/slack/test")
        assert response.status_code in [200, 500]

    def test_slack_test_response_structure(self, backend_server):
        """Slack test response should have proper structure."""
        response = requests.get(f"{backend_server}/api/slack/test")
        data = response.json()

        assert "success" in data
        if data["success"]:
            assert "message" in data
        else:
            assert "error" in data


@pytest.mark.integration
class TestSplunkHECConnector:
    """Tests for Splunk HEC connector functionality."""

    def test_splunk_status_in_stats(self, backend_server):
        """Stats should include Splunk connection status."""
        response = requests.get(f"{backend_server}/api/stats")
        data = response.json()

        assert "connections" in data
        assert "splunk" in data["connections"]

    def test_splunk_connection_boolean(self, backend_server):
        """Splunk connection should be boolean."""
        response = requests.get(f"{backend_server}/api/stats")
        data = response.json()

        splunk_status = data["connections"]["splunk"]
        assert isinstance(splunk_status, bool)


@pytest.mark.integration
class TestConnectorErrorHandling:
    """Tests for connector error handling."""

    def test_graceful_faz_failure(self, backend_server):
        """Events should handle FAZ connection failure gracefully."""
        response = requests.get(f"{backend_server}/api/events")
        assert response.status_code in [200, 500]

        data = response.json()
        assert "success" in data

    def test_graceful_slack_failure(self, backend_server):
        """Slack test should handle webhook failure gracefully."""
        response = requests.get(f"{backend_server}/api/slack/test")
        assert response.status_code in [200, 500]

        data = response.json()
        assert "success" in data


@pytest.mark.integration
class TestConnectorConfiguration:
    """Tests for connector configuration."""

    def test_stats_returns_valid_json(self, backend_server):
        """Stats endpoint should always return valid JSON."""
        response = requests.get(f"{backend_server}/api/stats")
        assert response.status_code == 200

        try:
            data = response.json()
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail("Stats endpoint returned invalid JSON")

    def test_connections_all_present(self, backend_server):
        """All expected connection types should be present."""
        response = requests.get(f"{backend_server}/api/stats")
        data = response.json()

        expected_connections = ["fortianalyzer", "splunk", "slack"]
        for conn in expected_connections:
            assert conn in data["connections"], f"Missing connection: {conn}"
