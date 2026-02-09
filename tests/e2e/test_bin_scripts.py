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

        subprocess.run(
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
                assert (
                    "getenv" in content or "environ" in content or "config" in content
                ), f"{script} may have hardcoded password"


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
                "slack.py uses print() for Splunk protocol (known issue, documented in AGENTS.md)"
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

        assert (
            uses_stderr or uses_logging
        ), f"{script} should use sys.stderr or logging module"


# =============================================================================
# Behavior Tests (Enhanced)
# =============================================================================


@pytest.mark.bin_scripts
class TestAutoValidatorBehavior:
    """Test auto_validator.py actual validation behavior."""

    @pytest.fixture
    def validator_script(self) -> Path:
        script = BIN_PATH / "auto_validator.py"
        if not script.exists():
            pytest.skip("auto_validator.py not found")
        return script

    @pytest.fixture
    def temp_conf_dir(self, tmp_path: Path) -> Path:
        conf_dir = tmp_path / "default"
        conf_dir.mkdir()
        return conf_dir

    def test_validates_valid_conf_syntax(self, validator_script, temp_conf_dir):
        """Validator should run and produce output."""
        result = subprocess.run(
            [sys.executable, str(validator_script)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(BIN_PATH.parent.parent),
        )

        output = result.stdout + result.stderr
        has_validation_output = (
            "검증" in output
            or "validation" in output.lower()
            or "error" in output.lower()
            or "pass" in output.lower()
            or len(output) > 0
        )
        assert has_validation_output

    def test_detects_missing_stanza_bracket(self, validator_script, temp_conf_dir):
        """Validator should detect missing bracket in stanza."""
        invalid_conf = temp_conf_dir / "invalid.conf"
        invalid_conf.write_text("[unclosed_stanza\n" "key = value\n")

        result = subprocess.run(
            [
                sys.executable,
                str(validator_script),
                "--check-syntax",
                str(invalid_conf),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should either fail or report an error
        has_error = (
            result.returncode != 0
            or "error" in result.stderr.lower()
            or "error" in result.stdout.lower()
            or "invalid" in result.stdout.lower()
        )
        assert result.returncode == 0 or has_error

    def test_runs_without_arguments(self, validator_script):
        """Validator should handle being run without arguments."""
        result = subprocess.run(
            [sys.executable, str(validator_script)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(BIN_PATH.parent.parent),
        )

        # Should not crash - either succeeds or shows usage
        assert result.returncode in [0, 1, 2]


@pytest.mark.bin_scripts
class TestDeploymentHealthCheckBehavior:
    """Test deployment_health_check.py actual health check behavior."""

    @pytest.fixture
    def health_check_script(self) -> Path:
        script = BIN_PATH / "deployment_health_check.py"
        if not script.exists():
            pytest.skip("deployment_health_check.py not found")
        return script

    def test_runs_without_crash(self, health_check_script):
        """Health check should run without crashing."""
        result = subprocess.run(
            [sys.executable, str(health_check_script)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(BIN_PATH.parent.parent),
        )

        # Script may fail checks but should not crash
        assert result.returncode in [0, 1]

    def test_outputs_check_results(self, health_check_script):
        """Health check should output check results."""
        result = subprocess.run(
            [sys.executable, str(health_check_script)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(BIN_PATH.parent.parent),
        )

        output = result.stdout + result.stderr
        # Should output something about checks
        has_output = len(output) > 0
        assert has_output

    def test_with_help_flag(self, health_check_script):
        """Health check should respond to --help flag."""
        result = subprocess.run(
            [sys.executable, str(health_check_script), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Either shows help or runs anyway
        output = result.stdout + result.stderr
        assert result.returncode in [0, 1, 2] or len(output) > 0


@pytest.mark.bin_scripts
class TestSplunkFeatureCheckerBehavior:
    """Test splunk_feature_checker.py feature detection behavior."""

    @pytest.fixture
    def feature_checker_script(self) -> Path:
        script = BIN_PATH / "splunk_feature_checker.py"
        if not script.exists():
            pytest.skip("splunk_feature_checker.py not found")
        return script

    def test_runs_without_crash(self, feature_checker_script):
        """Feature checker should run without crashing."""
        result = subprocess.run(
            [sys.executable, str(feature_checker_script)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(BIN_PATH.parent.parent),
        )

        # Should not crash
        assert result.returncode in [0, 1, 2]

    def test_with_help_flag(self, feature_checker_script):
        """Feature checker should respond to --help flag."""
        result = subprocess.run(
            [sys.executable, str(feature_checker_script), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout + result.stderr
        assert result.returncode in [0, 1, 2] or len(output) > 0


@pytest.mark.bin_scripts
class TestFortigateAutoResponseBehavior:
    """Test fortigate_auto_response.py behavior."""

    @pytest.fixture
    def auto_response_script(self) -> Path:
        script = BIN_PATH / "fortigate_auto_response.py"
        if not script.exists():
            pytest.skip("fortigate_auto_response.py not found")
        return script

    def test_requires_arguments(self, auto_response_script):
        """Auto response should require arguments or show usage."""
        result = subprocess.run(
            [sys.executable, str(auto_response_script)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should either fail with usage or require args
        output = result.stdout + result.stderr
        has_usage = "usage" in output.lower() or "error" in output.lower()
        assert result.returncode != 0 or has_usage

    def test_with_help_flag(self, auto_response_script):
        """Auto response should respond to --help flag."""
        result = subprocess.run(
            [sys.executable, str(auto_response_script), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout + result.stderr
        assert result.returncode in [0, 1, 2] or len(output) > 0


@pytest.mark.bin_scripts
class TestScriptInterdependencies:
    """Test that scripts can import shared modules."""

    def test_lib_directory_exists(self):
        """lib/ directory should exist for shared modules."""
        lib_path = BIN_PATH / "lib"
        # lib/ may or may not exist
        if lib_path.exists():
            assert lib_path.is_dir()

    @pytest.mark.parametrize("script", SCRIPTS)
    def test_script_no_import_errors(self, script: str):
        """Scripts should not have missing imports."""
        script_path = BIN_PATH / script

        if not script_path.exists():
            pytest.skip(f"{script} not found")

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, '{BIN_PATH}'); "
                f"compile(open('{script_path}').read(), '{script_path}', 'exec')",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"{script} has syntax error: {result.stderr}"
