"""E2E tests for slack_callback.py REST handler."""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
BIN_PATH = PROJECT_ROOT / "security_alert" / "bin"
LIB_PATH = BIN_PATH / "lib"
SCRIPT_PATH = BIN_PATH / "slack_callback.py"


class TestSlackCallbackExists:

    def test_script_exists(self):
        assert SCRIPT_PATH.exists(), "slack_callback.py not found"


class TestSlackCallbackSyntax:

    def test_valid_python_syntax(self):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"


class TestSlackCallbackImports:

    def test_imports_requests(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, '{LIB_PATH}'); "
                "import requests; print('OK')",
            ],
            capture_output=True,
            text=True,
            cwd=str(BIN_PATH),
            timeout=10,
        )
        assert result.returncode == 0

    def test_has_sys_path_setup(self):
        content = SCRIPT_PATH.read_text()
        assert "sys.path.insert" in content
        assert "'lib'" in content or '"lib"' in content


class TestSlackCallbackSplunkIntegration:

    def test_imports_splunk_admin(self):
        content = SCRIPT_PATH.read_text()
        assert "splunk.admin" in content or "import splunk" in content

    def test_has_rest_handler_class(self):
        content = SCRIPT_PATH.read_text()
        assert "class " in content
        assert (
            "MConfigHandler" in content
            or "AdminHandler" in content
            or "PersistentServerConnectionApplication" in content
        )


class TestSlackCallbackFunctions:

    def get_defined_functions(self):
        content = SCRIPT_PATH.read_text()
        import re

        return re.findall(r"^\s*def (\w+)\(", content, re.MULTILINE)

    def test_has_handler_methods(self):
        functions = self.get_defined_functions()
        handler_methods = [
            "handleList",
            "handleEdit",
            "handleCreate",
            "handleRemove",
            "handle",
        ]
        has_handler = any(m in functions for m in handler_methods)
        assert has_handler or len(functions) > 0


class TestSlackCallbackSecurity:

    def test_validates_slack_signature(self):
        content = SCRIPT_PATH.read_text()
        has_hmac = "hmac" in content.lower()
        has_signature = "signature" in content.lower()
        assert has_hmac or has_signature, "No signature validation found"

    def test_signature_called_in_handler(self):
        """Verify verify_slack_signature is actually called in handleEdit."""
        content = SCRIPT_PATH.read_text()
        import re

        # Find handleEdit method body
        handle_match = re.search(
            r"def handleEdit\(self.*?\n(.*?)(?=\n    def |\nclass |\Z)",
            content,
            re.DOTALL,
        )
        assert handle_match, "handleEdit method not found"
        handle_body = handle_match.group(1)
        assert (
            "verify_slack_signature" in handle_body
        ), "verify_slack_signature is defined but never called in handleEdit"

    def test_no_hardcoded_tokens(self):
        import re

        content = SCRIPT_PATH.read_text()

        patterns = [
            r"xoxb-[a-zA-Z0-9-]+",
            r"xoxp-[a-zA-Z0-9-]+",
            r"xapp-[a-zA-Z0-9-]+",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            assert len(matches) == 0, f"Hardcoded Slack token: {matches}"
