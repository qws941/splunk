"""
Pytest configuration and shared fixtures for Splunk security_alert E2E tests.

This module provides:
- Splunk SDK connection fixtures
- Test data generators
- Lookup file management
- Mock Slack server for alert action testing
"""

import csv
import gzip
import json
import os
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch  # noqa: F401

import pytest

# Add security_alert/bin to path for importing modules
SECURITY_ALERT_BIN = Path(__file__).parent.parent / "security_alert" / "bin"
sys.path.insert(0, str(SECURITY_ALERT_BIN))

# Try to import splunklib (optional - for live Splunk tests)
try:
    import splunklib.client as splunk_client
    import splunklib.results as splunk_results

    SPLUNK_SDK_AVAILABLE = True
except ImportError:
    SPLUNK_SDK_AVAILABLE = False
    splunk_client = None
    splunk_results = None


# =============================================================================
# Configuration
# =============================================================================


@pytest.fixture(scope="session")
def splunk_config() -> Dict[str, Any]:
    """Splunk connection configuration from environment variables."""
    return {
        "host": os.getenv("SPLUNK_HOST", "192.168.50.150"),
        "port": int(os.getenv("SPLUNK_PORT", "8089")),
        "username": os.getenv("SPLUNK_USERNAME", "admin"),
        "password": os.getenv("SPLUNK_PASSWORD", ""),
        "app": os.getenv("SPLUNK_APP", "security_alert"),
        "owner": os.getenv("SPLUNK_OWNER", "admin"),
    }


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def security_alert_path(project_root: Path) -> Path:
    """Return security_alert app directory."""
    return project_root / "security_alert"


# =============================================================================
# Splunk Connection Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def splunk_service(splunk_config: Dict[str, Any]) -> Optional[Any]:
    """
    Create Splunk SDK service connection.
    Returns None if SDK not available or connection fails.
    """
    if not SPLUNK_SDK_AVAILABLE:
        pytest.skip("splunklib not installed")
        return None

    try:
        service = splunk_client.connect(
            host=splunk_config["host"],
            port=splunk_config["port"],
            username=splunk_config["username"],
            password=splunk_config["password"],
            app=splunk_config["app"],
            owner=splunk_config["owner"],
        )
        # Verify connection
        service.apps.list()
        return service
    except Exception as e:
        pytest.skip(f"Cannot connect to Splunk: {e}")
        return None


@pytest.fixture
def splunk_search(splunk_service: Any):
    """
    Factory fixture to execute Splunk searches.

    Usage:
        results = splunk_search("search index=fw | head 10")
    """
    if splunk_service is None:
        pytest.skip("Splunk service not available")

    def _search(
        query: str,
        earliest_time: str = "-1h",
        latest_time: str = "now",
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """Execute a Splunk search and return results as list of dicts."""
        kwargs = {
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "count": max_results,
        }

        job = splunk_service.jobs.create(query, **kwargs)

        while not job.is_done():
            time.sleep(0.5)

        results = []
        for result in splunk_results.JSONResultsReader(job.results(output_mode="json")):
            if isinstance(result, dict):
                results.append(result)

        return results

    return _search


# =============================================================================
# Test Data Fixtures
# =============================================================================


# Alert event templates based on generate_test_events.py
ALERT_TEMPLATES = {
    "001_Config_Change": {
        "logid": "0100044546",
        "type": "event",
        "subtype": "system",
        "level": "notice",
        "devname": "FG-TEST-01",
        "user": "admin",
        "ui": "ssh(192.168.1.100)",
        "cfgpath": "firewall policy",
        "cfgattr": "set status enable",
        "msg": "Configuration changed from 'disable' to 'enable'",
    },
    "002_VPN_Tunnel_Down": {
        "logid": "0101037124",
        "type": "event",
        "subtype": "vpn",
        "level": "warning",
        "devname": "FG-TEST-01",
        "tunnelid": "VPN-TO-BRANCH",
        "remip": "203.0.113.50",
        "srcip": "192.168.1.1",
        "msg": "IPsec tunnel down reason: peer unreachable",
    },
    "002_VPN_Tunnel_Up": {
        "logid": "0101037125",
        "type": "event",
        "subtype": "vpn",
        "level": "notice",
        "devname": "FG-TEST-01",
        "tunnelid": "VPN-TO-BRANCH",
        "remip": "203.0.113.50",
        "srcip": "192.168.1.1",
        "msg": "IPsec tunnel established",
    },
    "006_CPU_Memory_Anomaly": {
        "logid": "0100032001",
        "type": "event",
        "subtype": "system",
        "level": "warning",
        "devname": "FG-TEST-01",
        "msg": "System CPU usage high: 95%",
    },
    "007_Hardware_Failure": {
        "logid": "0103040013",
        "type": "event",
        "subtype": "system",
        "level": "alert",
        "devname": "FG-TEST-01",
        "msg": "Hardware sensor alarm: Fan 1 failure detected",
    },
    "007_Hardware_Restored": {
        "logid": "0103040014",
        "type": "event",
        "subtype": "system",
        "level": "notice",
        "devname": "FG-TEST-01",
        "msg": "Hardware sensor restored: Fan 1 operating normally",
    },
    "008_HA_State_Change": {
        "logid": "0104032006",
        "type": "event",
        "subtype": "ha",
        "level": "warning",
        "devname": "FG-TEST-01",
        "ha_state": "master",
        "from_state": "slave",
        "member": "FG-PEER-01",
        "msg": "HA state changed from slave to master",
    },
    "010_Resource_Limit": {
        "logid": "0100032010",
        "type": "event",
        "subtype": "system",
        "level": "alert",
        "devname": "FG-TEST-01",
        "msg": "Resource limit exceeded: Disk usage 95%, limit 90%",
    },
    "011_Admin_Login_Failed": {
        "logid": "0100032101",
        "type": "event",
        "subtype": "system",
        "level": "warning",
        "devname": "FG-TEST-01",
        "user": "admin",
        "srcip": "10.0.0.99",
        "authproto": "ssh",
        "msg": "Administrator login failed from 10.0.0.99",
    },
    "012_Interface_Down": {
        "logid": "0100032201",
        "type": "event",
        "subtype": "system",
        "level": "warning",
        "devname": "FG-TEST-01",
        "interface": "port1",
        "msg": "Interface port1 link down",
    },
    "012_Interface_Up": {
        "logid": "0100032202",
        "type": "event",
        "subtype": "system",
        "level": "notice",
        "devname": "FG-TEST-01",
        "interface": "port1",
        "msg": "Interface port1 link up speed: 1000Mbps duplex: full",
    },
    "013_SSL_VPN_Brute_Force": {
        "logid": "0101039426",
        "type": "event",
        "subtype": "vpn",
        "level": "warning",
        "devname": "FG-TEST-01",
        "srcip": "10.0.0.99",
        "user": "testuser",
        "reason": "invalid credentials",
        "msg": "SSL VPN login failed for testuser from 10.0.0.99",
    },
    "015_Abnormal_Traffic_Spike": {
        "logid": "0000000013",
        "type": "traffic",
        "subtype": "forward",
        "level": "notice",
        "devname": "FG-TEST-01",
        "srcip": "192.168.1.100",
        "dstip": "8.8.8.8",
        "proto": 6,
        "sentbyte": "10000000",
        "rcvdbyte": "5000000",
        "msg": "Traffic session",
    },
    "016_System_Reboot": {
        "logid": "0100032002",
        "type": "event",
        "subtype": "system",
        "level": "alert",
        "devname": "FG-TEST-01",
        "msg": "System reboot initiated by admin",
    },
    "017_License_Expiry_Warning": {
        "logid": "0100032501",
        "type": "event",
        "subtype": "system",
        "level": "warning",
        "devname": "FG-TEST-01",
        "license": "FortiCare",
        "msg": "License FortiCare expires in 7 days",
    },
}


@pytest.fixture
def alert_event_generator():
    """
    Factory fixture to generate test alert events.

    Usage:
        event = alert_event_generator("001_Config_Change")
        events = alert_event_generator("011_Admin_Login_Failed", count=5)
    """

    def _generate(alert_name: str, count: int = 1, **overrides) -> List[Dict[str, Any]]:
        """Generate test events for a specific alert."""
        if alert_name not in ALERT_TEMPLATES:
            raise ValueError(f"Unknown alert: {alert_name}")

        template = ALERT_TEMPLATES[alert_name].copy()
        events = []

        for i in range(count):
            event = template.copy()
            event["_time"] = (datetime.now() - timedelta(seconds=i * 10)).isoformat()
            event.update(overrides)
            events.append(event)

        return events if count > 1 else events[0]

    return _generate


@pytest.fixture
def syslog_formatter():
    """
    Convert event dict to FortiGate syslog format.

    Usage:
        syslog_line = syslog_formatter(event)
    """

    def _format(event: Dict[str, Any]) -> str:
        """Format event as FortiGate syslog line."""
        timestamp = datetime.now().strftime("%b %d %H:%M:%S")
        devname = event.get("devname", "FortiGate")

        # Build key=value pairs
        pairs = []
        for key, value in event.items():
            if key.startswith("_"):
                continue
            if isinstance(value, str) and " " in value:
                pairs.append(f'{key}="{value}"')
            else:
                pairs.append(f"{key}={value}")

        return f"{timestamp} {devname} {' '.join(pairs)}"

    return _format


# =============================================================================
# Lookup File Fixtures
# =============================================================================


@pytest.fixture
def lookup_path(security_alert_path: Path) -> Path:
    """Return lookups directory path."""
    return security_alert_path / "lookups"


@pytest.fixture
def state_tracker_files() -> List[str]:
    """List of state tracker CSV files."""
    return [
        "vpn_state_tracker.csv",
        "hardware_state_tracker.csv",
        "ha_state_tracker.csv",
        "interface_state_tracker.csv",
        "cpu_memory_state_tracker.csv",
        "resource_state_tracker.csv",
        "admin_login_state_tracker.csv",
        "vpn_brute_force_state_tracker.csv",
        "traffic_spike_state_tracker.csv",
        "license_state_tracker.csv",
    ]


@pytest.fixture
def backup_lookup(lookup_path: Path):
    """
    Context manager to backup and restore lookup files during tests.

    Usage:
        with backup_lookup("vpn_state_tracker.csv"):
            # Test modifies the file
            ...
        # File is restored after test
    """
    import shutil
    from contextlib import contextmanager

    @contextmanager
    def _backup(filename: str):
        filepath = lookup_path / filename
        backup_path = filepath.with_suffix(".csv.bak")

        # Backup if exists
        if filepath.exists():
            shutil.copy2(filepath, backup_path)

        try:
            yield filepath
        finally:
            # Restore from backup
            if backup_path.exists():
                shutil.move(backup_path, filepath)
            elif filepath.exists():
                # Remove if it was created during test
                filepath.unlink()

    return _backup


@pytest.fixture
def create_lookup_entry(lookup_path: Path):
    """
    Factory to create entries in lookup files.

    Usage:
        create_lookup_entry("vpn_state_tracker.csv", {
            "device": "FG-TEST-01",
            "vpn_name": "VPN-TO-BRANCH",
            "state": "DOWN"
        })
    """

    def _create(filename: str, entry: Dict[str, str]):
        filepath = lookup_path / filename

        # Read existing or create new
        existing_rows = []
        fieldnames = list(entry.keys())

        if filepath.exists():
            with open(filepath, "r", newline="") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or fieldnames
                existing_rows = list(reader)

        # Add new entry
        existing_rows.append(entry)

        # Write back
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_rows)

    return _create


# =============================================================================
# Mock Slack Server Fixtures
# =============================================================================


class MockSlackHandler(BaseHTTPRequestHandler):
    """HTTP handler for mock Slack webhook server."""

    received_messages: List[Dict[str, Any]] = []

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            message = json.loads(body.decode("utf-8"))
            MockSlackHandler.received_messages.append(
                {
                    "path": self.path,
                    "headers": dict(self.headers),
                    "body": message,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def log_message(self, format, *args):
        """Suppress logging."""
        pass


@pytest.fixture
def mock_slack_server():
    """
    Start a mock Slack webhook server for testing alert actions.

    Usage:
        def test_slack_alert(mock_slack_server):
            webhook_url = mock_slack_server["url"]
            # Trigger alert...
            messages = mock_slack_server["messages"]()
    """
    # Clear previous messages
    MockSlackHandler.received_messages = []

    # Find available port
    server = HTTPServer(("127.0.0.1", 0), MockSlackHandler)
    port = server.server_address[1]

    # Start server in background thread
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield {
        "url": f"http://127.0.0.1:{port}/webhook",
        "port": port,
        "messages": lambda: MockSlackHandler.received_messages.copy(),
        "clear": lambda: MockSlackHandler.received_messages.clear(),
    }

    server.shutdown()


# =============================================================================
# Slack Alert Action Fixtures
# =============================================================================


@pytest.fixture
def mock_splunk_alert_payload():
    """
    Create mock Splunk alert action payload (stdin JSON).

    Usage:
        payload = mock_splunk_alert_payload(
            results=[{"device": "FG-TEST", "event": "test"}],
            alert_name="007_Hardware_Failure"
        )
    """

    def _create(
        results: List[Dict[str, Any]],
        alert_name: str = "Test_Alert",
        channel: str = "#test-channel",
        webhook_url: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        """Create mock alert payload."""
        # Create gzipped CSV for results
        csv_content = ""
        if results:
            fieldnames = list(results[0].keys())
            import io

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
            csv_content = output.getvalue()

        # Create temp gzipped file
        temp_file = tempfile.NamedTemporaryFile(
            mode="wb", suffix=".csv.gz", delete=False
        )
        with gzip.open(temp_file.name, "wt") as f:
            f.write(csv_content)

        return {
            "result": results[0] if results else {},
            "results_file": temp_file.name,
            "search_name": alert_name,
            "configuration": {
                "channel": channel,
                "webhook_url": webhook_url,
                **kwargs,
            },
            "session_key": "test_session_key",
            "search_uri": f"/services/saved/searches/{alert_name}",
            "server_uri": "https://localhost:8089",
            "owner": "admin",
            "app": "security_alert",
        }

    return _create


@pytest.fixture
def run_slack_alert(mock_splunk_alert_payload):
    """
    Execute slack.py alert action with mock payload.

    Usage:
        result = run_slack_alert(
            results=[{"device": "FG-TEST", "msg": "Test"}],
            webhook_url="http://localhost:8080/webhook"
        )
    """
    import subprocess

    def _run(results: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        payload = mock_splunk_alert_payload(results, **kwargs)

        # Run slack.py with payload as stdin
        slack_script = SECURITY_ALERT_BIN / "slack.py"

        proc = subprocess.run(
            [sys.executable, str(slack_script)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
        )

        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "payload": payload,
        }

    return _run


# =============================================================================
# Configuration File Fixtures
# =============================================================================


@pytest.fixture
def parse_conf_file():
    """
    Parse Splunk .conf file into dictionary.

    Usage:
        config = parse_conf_file("savedsearches.conf")
    """

    def _parse(filepath: Path) -> Dict[str, Dict[str, str]]:
        """Parse conf file into nested dict."""
        result = {}
        current_stanza = None

        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Stanza header
                if line.startswith("[") and line.endswith("]"):
                    current_stanza = line[1:-1]
                    result[current_stanza] = {}
                    continue

                # Key-value pair
                if "=" in line and current_stanza:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()

                    # Handle line continuation
                    while value.endswith("\\"):
                        value = value[:-1]
                        next_line = next(f, "").strip()
                        value += next_line

                    result[current_stanza][key] = value

        return result

    return _parse


@pytest.fixture
def saved_searches(security_alert_path: Path, parse_conf_file) -> Dict[str, Dict]:
    """Load and parse savedsearches.conf."""
    conf_path = security_alert_path / "default" / "savedsearches.conf"
    return parse_conf_file(conf_path)


@pytest.fixture
def macros(security_alert_path: Path, parse_conf_file) -> Dict[str, Dict]:
    """Load and parse macros.conf."""
    conf_path = security_alert_path / "default" / "macros.conf"
    return parse_conf_file(conf_path)


# =============================================================================
# Markers
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "splunk_live: mark test as requiring live Splunk connection"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line(
        "markers", "alert: mark test as alert-specific (parametrize with alert name)"
    )
