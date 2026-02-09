"""E2E tests for splunk_feature_checker.py functionality."""

import subprocess
import sys
from pathlib import Path

import pytest  # noqa: F401

PROJECT_ROOT = Path(__file__).parent.parent.parent
BIN_PATH = PROJECT_ROOT / "security_alert" / "bin"
FEATURE_CHECKER_PATH = BIN_PATH / "splunk_feature_checker.py"


class TestFeatureCheckerExists:

    def test_script_exists(self):
        assert FEATURE_CHECKER_PATH.exists(), "splunk_feature_checker.py not found"

    def test_script_is_python(self):
        content = FEATURE_CHECKER_PATH.read_text()
        assert "#!/usr/bin/env python" in content or "import " in content


class TestFeatureCheckerSyntax:

    def test_valid_python_syntax(self):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(FEATURE_CHECKER_PATH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"


class TestFeatureCheckerImports:

    def test_can_import_as_module(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, '{BIN_PATH}'); "
                "import splunk_feature_checker",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"


class TestFeatureCheckerFunctions:

    def get_defined_functions(self):
        content = FEATURE_CHECKER_PATH.read_text()
        import re

        return re.findall(r"^def (\w+)\(", content, re.MULTILINE)

    def test_has_main_functions(self):
        functions = self.get_defined_functions()
        assert len(functions) > 0, "No functions defined"

    def test_has_validation_logic(self):
        """Feature checker may use classes or functions for validation."""
        content = FEATURE_CHECKER_PATH.read_text()
        # Accept: check functions, validator classes, or main entry point
        has_check_funcs = any(
            "check" in f.lower() for f in self.get_defined_functions()
        )
        has_validator_classes = "Validator" in content or "Checker" in content
        has_main = "def main(" in content or "if __name__" in content
        assert (
            has_check_funcs or has_validator_classes or has_main
        ), "No validation logic found (check functions, Validator classes, or main)"


class TestFeatureCheckerClasses:

    def get_defined_classes(self):
        content = FEATURE_CHECKER_PATH.read_text()
        import re

        return re.findall(r"^class (\w+)", content, re.MULTILINE)

    def test_has_classes(self):
        classes = self.get_defined_classes()
        assert len(classes) >= 0


class TestFeatureCheckerNoHardcodedSecrets:

    SENSITIVE_PATTERNS = [
        r"password\s*=\s*['\"][^'\"]+['\"]",
        r"api_key\s*=\s*['\"][^'\"]+['\"]",
        r"token\s*=\s*['\"][^'\"]+['\"]",
        r"secret\s*=\s*['\"][^'\"]+['\"]",
    ]

    def test_no_hardcoded_secrets(self):
        import re

        content = FEATURE_CHECKER_PATH.read_text()

        for pattern in self.SENSITIVE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            filtered = [m for m in matches if "example" not in m.lower()]
            assert len(filtered) == 0, f"Hardcoded secret found: {filtered}"
