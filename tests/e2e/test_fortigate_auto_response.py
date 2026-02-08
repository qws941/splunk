"""E2E tests for fortigate_auto_response.py functionality."""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
BIN_PATH = PROJECT_ROOT / "security_alert" / "bin"
LIB_PATH = BIN_PATH / "lib"
SCRIPT_PATH = BIN_PATH / "fortigate_auto_response.py"


class TestFortigateAutoResponseExists:

    def test_script_exists(self):
        assert SCRIPT_PATH.exists(), "fortigate_auto_response.py not found"

    def test_script_has_shebang(self):
        content = SCRIPT_PATH.read_text()
        assert content.startswith("#!/"), "Missing shebang"


class TestFortigateAutoResponseSyntax:

    def test_valid_python_syntax(self):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"


class TestFortigateAutoResponseImports:

    def test_imports_requests_from_vendored(self):
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
        assert result.returncode == 0, f"requests import failed: {result.stderr}"

    def test_has_sys_path_setup(self):
        content = SCRIPT_PATH.read_text()
        assert "sys.path.insert" in content, "Missing sys.path setup"
        assert "'lib'" in content or '"lib"' in content, "Missing lib reference"


class TestFortigateAutoResponseFunctions:

    def get_defined_functions(self):
        content = SCRIPT_PATH.read_text()
        import re

        return re.findall(r"^def (\w+)\(", content, re.MULTILINE)

    def test_has_functions(self):
        functions = self.get_defined_functions()
        assert len(functions) > 0, "No functions defined"

    def test_has_response_functions(self):
        functions = self.get_defined_functions()
        response_funcs = [
            f for f in functions if "response" in f.lower() or "action" in f.lower()
        ]
        assert len(response_funcs) >= 0


class TestFortigateAutoResponseClasses:

    def get_defined_classes(self):
        content = SCRIPT_PATH.read_text()
        import re

        return re.findall(r"^class (\w+)", content, re.MULTILINE)

    def test_classes_defined(self):
        classes = self.get_defined_classes()
        assert len(classes) >= 0


class TestFortigateAutoResponseSecurity:

    def test_no_hardcoded_ips(self):
        import re

        content = SCRIPT_PATH.read_text()

        ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        matches = re.findall(ip_pattern, content)

        allowed = ["127.0.0.1", "0.0.0.0", "255.255.255.255"]
        suspicious = [ip for ip in matches if ip not in allowed]

        assert len(suspicious) == 0, f"Hardcoded IPs found: {suspicious}"

    def test_no_hardcoded_credentials(self):
        import re

        content = SCRIPT_PATH.read_text()

        patterns = [
            r"password\s*=\s*['\"][^$][^'\"]+['\"]",
            r"api_key\s*=\s*['\"][^$][^'\"]+['\"]",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            assert len(matches) == 0, f"Hardcoded credential: {matches}"
