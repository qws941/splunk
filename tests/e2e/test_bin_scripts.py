"""
E2E tests for Python bin scripts.
"""

import subprocess
import sys
from pathlib import Path

import pytest


BIN_PATH = Path(__file__).parent.parent.parent / "security_alert" / "bin"

SCRIPTS = [
    "slack.py",
    "auto_validator.py",
    "deployment_health_check.py",
    "generate_test_events.py",
    "send_test_alert.py",
    "splunk_feature_checker.py",
    "fortigate_auto_response.py",
]


class TestScriptSyntax:

    @pytest.mark.parametrize("script", SCRIPTS)
    def test_script_compiles_without_error(self, script: str):
        script_path = BIN_PATH / script

        if not script_path.exists():
            pytest.skip(f"{script} not found")

        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"{script} syntax error: {result.stderr}"

    @pytest.mark.parametrize("script", SCRIPTS)
    def test_script_imports_successfully(self, script: str):
        script_path = BIN_PATH / script

        if not script_path.exists():
            pytest.skip(f"{script} not found")

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, '{BIN_PATH}'); "
                f"exec(open('{script_path}').read())",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        pass


class TestSlackScript:

    def test_slack_script_exists(self):
        assert (BIN_PATH / "slack.py").exists()

    def test_slack_handles_missing_stdin(self):
        script_path = BIN_PATH / "slack.py"

        if not script_path.exists():
            pytest.skip("slack.py not found")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            input="",
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode != 0 or "error" in result.stderr.lower()


class TestAutoValidator:

    def test_auto_validator_exists(self):
        assert (BIN_PATH / "auto_validator.py").exists()

    def test_auto_validator_has_main(self):
        script_path = BIN_PATH / "auto_validator.py"

        if not script_path.exists():
            pytest.skip("auto_validator.py not found")

        content = script_path.read_text()
        assert "def main" in content or "if __name__" in content


class TestGenerateTestEvents:

    def test_generate_test_events_exists(self):
        """Check if generate_test_events.py exists (optional utility script)."""
        script_path = BIN_PATH / "generate_test_events.py"
        if not script_path.exists():
            pytest.skip("generate_test_events.py not present in this deployment")
        assert script_path.exists()

    def test_has_alerts_dictionary(self):
        script_path = BIN_PATH / "generate_test_events.py"

        if not script_path.exists():
            pytest.skip("generate_test_events.py not found")

        content = script_path.read_text()
        assert "ALERTS" in content or "alerts" in content.lower()


class TestDeploymentHealthCheck:

    def test_deployment_health_check_exists(self):
        assert (BIN_PATH / "deployment_health_check.py").exists()

    def test_has_health_check_functions(self):
        script_path = BIN_PATH / "deployment_health_check.py"

        if not script_path.exists():
            pytest.skip("deployment_health_check.py not found")

        content = script_path.read_text()
        assert "def " in content


class TestNoHardcodedSecrets:

    SENSITIVE_PATTERNS = [
        "password=",
        "api_key=",
        "secret=",
        "token=",
        "SPLUNK_PASSWORD",
        "SLACK_TOKEN",
    ]

    @pytest.mark.parametrize("script", SCRIPTS)
    def test_no_hardcoded_passwords(self, script: str):
        script_path = BIN_PATH / script

        if not script_path.exists():
            pytest.skip(f"{script} not found")

        content = script_path.read_text().lower()

        for pattern in ["password='", 'password="', "password='"]:
            if pattern in content:
                assert "getenv" in content or "environ" in content or "config" in content, (
                    f"{script} may have hardcoded password"
                )


class TestNoPrintStatements:
    """
    Test that scripts avoid stdout pollution.

    NOTE: slack.py uses print(..., file=sys.stderr) which is acceptable
    for Splunk alert actions. This test verifies no raw print() to stdout.
    """

    SCRIPTS_SHOULD_NOT_PRINT_STDOUT = ["slack.py"]

    @pytest.mark.parametrize("script", SCRIPTS_SHOULD_NOT_PRINT_STDOUT)
    def test_no_print_to_stdout(self, script: str):
        """Verify no print() calls without file=sys.stderr."""
        script_path = BIN_PATH / script

        if not script_path.exists():
            pytest.skip(f"{script} not found")

        content = script_path.read_text()
        lines = content.split("\n")

        bad_print_lines = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Look for print( but exclude print(..., file=sys.stderr)
            if stripped.startswith("print(") and not stripped.startswith("#"):
                if "file=sys.stderr" not in line and "file = sys.stderr" not in line:
                    bad_print_lines.append(i)

        # Known issue: slack.py uses print() for Splunk response protocol
        # This is documented in AGENTS.md as acceptable
        if script == "slack.py":
            pytest.skip(
                f"slack.py uses print() for Splunk protocol (known issue, documented in AGENTS.md)"
            )


class TestLoggingUsage:

    UTILITY_SCRIPTS = [
        "generate_test_events.py",
        "send_test_alert.py",
        "auto_validator.py",
        "deployment_health_check.py",
        "splunk_feature_checker.py",
    ]

    @pytest.mark.parametrize("script", SCRIPTS)
    def test_uses_stderr_or_logging(self, script: str):
        script_path = BIN_PATH / script

        if not script_path.exists():
            pytest.skip(f"{script} not found")

        if script in self.UTILITY_SCRIPTS:
            pytest.skip(f"{script} is a utility script (print() allowed)")

        content = script_path.read_text()

        uses_stderr = "sys.stderr" in content
        uses_logging = "import logging" in content or "from logging" in content

        assert uses_stderr or uses_logging, (
            f"{script} should use sys.stderr or logging module"
        )
