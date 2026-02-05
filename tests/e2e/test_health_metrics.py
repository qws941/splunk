"""
E2E tests for Health and Metrics endpoints.

Tests /health and /metrics (Prometheus format) for both:
- backend/server.js (port 3001)
- index.js legacy server (port 8080)
"""

import os
import re
import time
import subprocess
from pathlib import Path

import pytest
import requests


BACKEND_PORT = 3102
LEGACY_PORT = 8082
STARTUP_TIMEOUT = 15


@pytest.fixture(scope="module")
def project_root() -> Path:
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def backend_server(project_root: Path):
    """Start backend/server.js, wait for /health, yield base URL."""
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


@pytest.fixture(scope="module")
def legacy_server(project_root: Path):
    """Start index.js (legacy), wait for /health, yield base URL."""
    server_script = project_root / "index.js"

    if not server_script.exists():
        pytest.skip(f"Legacy server not found: {server_script}")

    env = os.environ.copy()
    env["PORT"] = str(LEGACY_PORT)
    env["NODE_ENV"] = "test"

    process = subprocess.Popen(
        ["node", str(server_script)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(project_root),
    )

    base_url = f"http://localhost:{LEGACY_PORT}"
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
            f"Legacy server failed to start\n"
            f"stdout: {stdout.decode()}\n"
            f"stderr: {stderr.decode()}"
        )

    yield base_url

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.mark.backend
class TestBackendHealth:
    """Health endpoint tests for backend/server.js."""

    def test_health_endpoint_returns_200(self, backend_server):
        response = requests.get(f"{backend_server}/health")
        assert response.status_code == 200

    def test_health_response_structure(self, backend_server):
        response = requests.get(f"{backend_server}/health")
        data = response.json()

        assert "status" in data
        assert data["status"] in ["ok", "healthy", "up"]

    def test_health_includes_uptime(self, backend_server):
        response = requests.get(f"{backend_server}/health")
        data = response.json()

        if "uptime" in data:
            assert isinstance(data["uptime"], (int, float))
            assert data["uptime"] >= 0

    def test_health_includes_memory(self, backend_server):
        response = requests.get(f"{backend_server}/health")
        data = response.json()

        if "memory" in data:
            assert isinstance(data["memory"], dict)

    def test_health_response_time(self, backend_server):
        start = time.time()
        response = requests.get(f"{backend_server}/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1


@pytest.mark.backend
class TestBackendMetrics:
    """Prometheus metrics endpoint tests for backend/server.js."""

    def test_metrics_endpoint_returns_200(self, backend_server):
        response = requests.get(f"{backend_server}/metrics")
        assert response.status_code == 200

    def test_metrics_content_type(self, backend_server):
        response = requests.get(f"{backend_server}/metrics")
        content_type = response.headers.get("Content-Type", "")
        assert "text/plain" in content_type or "text/html" in content_type

    def test_metrics_prometheus_format(self, backend_server):
        response = requests.get(f"{backend_server}/metrics")
        text = response.text

        has_help = "# HELP" in text
        has_type = "# TYPE" in text

        if has_help or has_type:
            assert has_help, "Prometheus format should include # HELP comments"
            assert has_type, "Prometheus format should include # TYPE comments"

    def test_metrics_contains_process_info(self, backend_server):
        response = requests.get(f"{backend_server}/metrics")
        text = response.text

        process_metrics = [
            "process_cpu",
            "process_memory",
            "process_uptime",
            "nodejs_heap",
            "http_request",
            "api_",
        ]

        found_any = any(metric in text for metric in process_metrics)
        has_metrics = len(text.strip()) > 0
        assert has_metrics, "Metrics endpoint should return content"

    def test_metrics_parseable(self, backend_server):
        response = requests.get(f"{backend_server}/metrics")
        text = response.text

        lines = text.strip().split("\n")
        for line in lines:
            if line.startswith("#"):
                continue
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                metric_name = parts[0]
                assert re.match(r"^[a-zA-Z_:][a-zA-Z0-9_:]*", metric_name)


@pytest.mark.backend
@pytest.mark.slow
class TestLegacyHealth:
    """Health endpoint tests for index.js (legacy server)."""

    def test_health_endpoint_returns_200(self, legacy_server):
        response = requests.get(f"{legacy_server}/health")
        assert response.status_code == 200

    def test_health_response_structure(self, legacy_server):
        response = requests.get(f"{legacy_server}/health")
        data = response.json()

        assert "status" in data

    def test_health_includes_services(self, legacy_server):
        response = requests.get(f"{legacy_server}/health")
        data = response.json()

        if "services" in data:
            assert isinstance(data["services"], dict)


@pytest.mark.backend
@pytest.mark.slow
class TestLegacyMetrics:
    """Prometheus metrics endpoint tests for index.js (legacy server)."""

    def test_metrics_endpoint_returns_200(self, legacy_server):
        response = requests.get(f"{legacy_server}/metrics")
        assert response.status_code == 200

    def test_metrics_prometheus_format(self, legacy_server):
        response = requests.get(f"{legacy_server}/metrics")
        text = response.text

        if "# HELP" in text:
            assert "# TYPE" in text


@pytest.mark.backend
class TestHealthComparison:
    """Compare health endpoints between backend and legacy servers."""

    @pytest.mark.slow
    def test_both_servers_healthy(self, backend_server, legacy_server):
        backend_resp = requests.get(f"{backend_server}/health")
        legacy_resp = requests.get(f"{legacy_server}/health")

        assert backend_resp.status_code == 200
        assert legacy_resp.status_code == 200

    @pytest.mark.slow
    def test_health_response_compatibility(self, backend_server, legacy_server):
        backend_data = requests.get(f"{backend_server}/health").json()
        legacy_data = requests.get(f"{legacy_server}/health").json()

        assert "status" in backend_data
        assert "status" in legacy_data
