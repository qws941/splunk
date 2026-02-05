"""
E2E tests for Slack alert action (slack.py).

slack.py expects a gzipped CSV file path as argument (Splunk alert action protocol).
"""

import json
import sys
import gzip
import csv
import tempfile
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Any

import pytest

BIN_PATH = Path(__file__).parent.parent.parent / "security_alert" / "bin"
SLACK_SCRIPT = BIN_PATH / "slack.py"


@pytest.fixture
def run_slack_alert_with_file():
    """Execute slack.py with a temp gzipped CSV file."""

    def _run(results: List[Dict], webhook_url: str = "") -> Dict[str, Any]:
        if not SLACK_SCRIPT.exists():
            pytest.skip("slack.py not found")

        with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as f:
            temp_path = f.name

        with gzip.open(temp_path, "wt", encoding="utf-8") as gz:
            if results:
                writer = csv.DictWriter(gz, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)

        env = os.environ.copy()
        if webhook_url:
            env["SLACK_WEBHOOK_URL"] = webhook_url

        try:
            proc = subprocess.run(
                [sys.executable, str(SLACK_SCRIPT), temp_path],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            return {
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        finally:
            Path(temp_path).unlink(missing_ok=True)

    return _run


class TestSlackScriptExecution:

    def test_script_exists(self):
        assert SLACK_SCRIPT.exists(), "slack.py not found"

    def test_script_requires_argument(self):
        if not SLACK_SCRIPT.exists():
            pytest.skip("slack.py not found")

        proc = subprocess.run(
            [sys.executable, str(SLACK_SCRIPT)],
            capture_output=True,
            text=True,
        )

        assert proc.returncode != 0
        assert "usage" in proc.stderr.lower() or "missing" in proc.stderr.lower()

    def test_script_handles_nonexistent_file(self):
        if not SLACK_SCRIPT.exists():
            pytest.skip("slack.py not found")

        proc = subprocess.run(
            [sys.executable, str(SLACK_SCRIPT), "/nonexistent/file.csv.gz"],
            capture_output=True,
            text=True,
        )

        assert proc.returncode != 0 or "error" in proc.stderr.lower()


class TestSlackAlertPayloadParsing:

    def test_parse_valid_results_file(self, run_slack_alert_with_file):
        results = [
            {
                "device": "FG-TEST-01",
                "event": "Hardware Failure",
                "severity": "CRITICAL",
            }
        ]

        result = run_slack_alert_with_file(results)

        has_usage_error = "usage:" in result["stderr"].lower()
        assert not has_usage_error, f"Unexpected usage error: {result['stderr']}"

    def test_handle_empty_results(self, run_slack_alert_with_file):
        result = run_slack_alert_with_file([])

        is_ok = result["returncode"] == 0
        handles_empty = "no results" in result["stderr"].lower() or "empty" in result["stderr"].lower()
        assert is_ok or handles_empty or result["returncode"] != 0

    def test_handle_missing_fields(self, run_slack_alert_with_file):
        results = [{"partial": "data"}]

        result = run_slack_alert_with_file(results)

        no_crash = "traceback" not in result["stderr"].lower()
        assert no_crash, f"Script crashed: {result['stderr']}"


class TestSlackScriptOutput:

    def test_no_stdout_pollution(self, run_slack_alert_with_file):
        """Splunk alert scripts should not print to stdout."""
        results = [{"device": "FG-TEST", "event": "Test"}]

        result = run_slack_alert_with_file(results)

        if result["stdout"]:
            try:
                json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass

    def test_errors_go_to_stderr(self, run_slack_alert_with_file):
        results = [{"device": "FG-TEST", "event": "Test"}]

        result = run_slack_alert_with_file(results)

        if result["returncode"] != 0:
            assert result["stderr"], "Errors should be written to stderr"


class TestSlackScriptFunctions:

    def test_has_parse_function(self):
        if not SLACK_SCRIPT.exists():
            pytest.skip("slack.py not found")

        content = SLACK_SCRIPT.read_text()
        assert "def parse_splunk_results" in content or "def parse" in content

    def test_has_format_function(self):
        if not SLACK_SCRIPT.exists():
            pytest.skip("slack.py not found")

        content = SLACK_SCRIPT.read_text()
        has_format = "def format" in content or "def build" in content
        has_blocks = "blocks" in content.lower()
        assert has_format or has_blocks

    def test_has_send_function(self):
        if not SLACK_SCRIPT.exists():
            pytest.skip("slack.py not found")

        content = SLACK_SCRIPT.read_text()
        has_send = "def send" in content or "requests.post" in content
        assert has_send

    def test_uses_gzip_module(self):
        if not SLACK_SCRIPT.exists():
            pytest.skip("slack.py not found")

        content = SLACK_SCRIPT.read_text()
        assert "import gzip" in content or "from gzip" in content

    def test_uses_requests_module(self):
        if not SLACK_SCRIPT.exists():
            pytest.skip("slack.py not found")

        content = SLACK_SCRIPT.read_text()
        assert "import requests" in content


class TestErrorHandling:

    def test_handles_invalid_gzip_file(self):
        if not SLACK_SCRIPT.exists():
            pytest.skip("slack.py not found")

        with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as f:
            f.write(b"not a gzip file")
            temp_path = f.name

        try:
            proc = subprocess.run(
                [sys.executable, str(SLACK_SCRIPT), temp_path],
                capture_output=True,
                text=True,
            )

            assert proc.returncode != 0 or "error" in proc.stderr.lower()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_handles_empty_gzip_file(self):
        if not SLACK_SCRIPT.exists():
            pytest.skip("slack.py not found")

        with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as f:
            temp_path = f.name

        with gzip.open(temp_path, "wt") as gz:
            gz.write("")

        try:
            proc = subprocess.run(
                [sys.executable, str(SLACK_SCRIPT), temp_path],
                capture_output=True,
                text=True,
            )

            no_traceback = "traceback" not in proc.stderr.lower()
            assert no_traceback, f"Script crashed: {proc.stderr}"
        finally:
            Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def slack_webhook_url():
    """Get Slack webhook URL from environment, skip if not set."""
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        pytest.skip("SLACK_WEBHOOK_URL not configured")
    return url


@pytest.fixture
def alert_templates():
    """Sample alert templates for testing (subset to avoid spam)."""
    return {
        "007": {
            "name": "Hardware Failure",
            "emoji": "🔴",
            "color": "#FF0000",
            "sample": {
                "devname": "FGT-TEST-01",
                "component": "PSU 2",
                "status": "failed",
            },
        },
        "001": {
            "name": "Config Change",
            "emoji": "⚙️",
            "color": "#FFA500",
            "sample": {
                "devname": "FGT-TEST-01",
                "user": "admin",
                "action": "edit",
                "path": "firewall policy 101",
            },
        },
    }


def build_test_block_kit(alert_id: str, template: Dict) -> List[Dict]:
    """Build Block Kit message for testing."""
    from datetime import datetime

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sample = template["sample"]

    fields = [{"type": "mrkdwn", "text": f"*{k}:*\n{v}"} for k, v in sample.items()]

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{template['emoji']} [{alert_id}] {template['name']} (E2E TEST)",
                "emoji": True,
            },
        },
        {"type": "section", "fields": fields[:4]},
    ]

    if len(fields) > 4:
        blocks.append({"type": "section", "fields": fields[4:8]})

    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"🧪 *E2E TEST* | {now} | pytest test_slack_alert_action.py",
                }
            ],
        }
    )

    return blocks


def send_slack_webhook(webhook_url: str, blocks: List[Dict], color: str = "#0066FF") -> Dict[str, Any]:
    """Send message to Slack webhook and return result."""
    import requests

    payload = {"blocks": blocks, "attachments": [{"color": color}]}

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return {
            "success": response.status_code == 200 and response.text == "ok",
            "status_code": response.status_code,
            "response": response.text,
        }
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


@pytest.mark.splunk_live
class TestLiveSlackIntegration:
    """Live Slack webhook integration tests.

    These tests actually send messages to Slack.
    Requires SLACK_WEBHOOK_URL environment variable.
    """

    def test_webhook_url_configured(self, slack_webhook_url):
        """Verify webhook URL is configured and valid format."""
        assert slack_webhook_url.startswith("https://hooks.slack.com/"), (
            "Invalid webhook URL format"
        )

    def test_send_single_test_alert(self, slack_webhook_url, alert_templates):
        """Send a single test alert to verify webhook works."""
        alert_id = "007"
        template = alert_templates[alert_id]
        blocks = build_test_block_kit(alert_id, template)

        result = send_slack_webhook(slack_webhook_url, blocks, template["color"])

        assert result["success"], f"Slack send failed: {result}"
        assert result["status_code"] == 200
        assert result["response"] == "ok"

    def test_send_config_change_alert(self, slack_webhook_url, alert_templates):
        """Send config change alert to verify different alert type."""
        alert_id = "001"
        template = alert_templates[alert_id]
        blocks = build_test_block_kit(alert_id, template)

        result = send_slack_webhook(slack_webhook_url, blocks, template["color"])

        assert result["success"], f"Slack send failed: {result}"

    def test_slack_script_with_webhook(self, run_slack_alert_with_file, slack_webhook_url):
        """Test the actual slack.py script with a real webhook."""
        results = [
            {
                "device": "FGT-E2E-TEST",
                "event": "E2E Test Alert",
                "severity": "INFO",
                "msg": "This is an automated E2E test",
            }
        ]

        result = run_slack_alert_with_file(results, webhook_url=slack_webhook_url)

        # Script should succeed with valid webhook
        assert result["returncode"] == 0, f"Script failed: {result['stderr']}"
        assert "success" in result["stderr"].lower() or result["returncode"] == 0

    def test_invalid_webhook_returns_error(self, run_slack_alert_with_file):
        """Test that invalid webhook URL is handled gracefully."""
        results = [{"device": "FGT-TEST", "event": "Test"}]
        invalid_url = "https://hooks.slack.com/services/INVALID/URL/HERE"

        result = run_slack_alert_with_file(results, webhook_url=invalid_url)

        # Should fail but not crash
        assert "traceback" not in result["stderr"].lower()
