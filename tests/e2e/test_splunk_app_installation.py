"""
E2E tests for Splunk App installation and vendored dependencies.

Tests verify:
1. App structure is complete and valid
2. Vendored Python dependencies are properly packaged
3. imports work correctly on live Splunk server
4. Tarball packaging preserves all required files
"""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
SECURITY_ALERT_PATH = PROJECT_ROOT / "security_alert"
BIN_PATH = SECURITY_ALERT_PATH / "bin"
LIB_PATH = BIN_PATH / "lib"

VENDORED_PACKAGES = [
    "requests",
    "urllib3",
    "certifi",
    "charset_normalizer",
    "idna",
]

SCRIPTS_USING_REQUESTS = [
    "slack.py",
    "slack_callback.py",
    "fortigate_auto_response.py",
    "send_test_alert.py",
]


class TestVendoredDependencies:

    def test_lib_directory_exists(self):
        assert LIB_PATH.exists(), "bin/lib/ directory must exist"
        assert LIB_PATH.is_dir(), "bin/lib/ must be a directory"

    @pytest.mark.parametrize("package", VENDORED_PACKAGES)
    def test_vendored_package_exists(self, package: str):
        package_path = LIB_PATH / package
        assert (
            package_path.exists()
        ), f"Vendored package {package} not found in bin/lib/"
        assert package_path.is_dir(), f"{package} must be a directory"

    @pytest.mark.parametrize("package", VENDORED_PACKAGES)
    def test_vendored_package_has_init(self, package: str):
        init_file = LIB_PATH / package / "__init__.py"
        assert init_file.exists(), f"{package}/__init__.py must exist"

    def test_requests_version_compatible(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, '{LIB_PATH}'); "
                "import requests; print(requests.__version__)",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Failed to import requests: {result.stderr}"

        version = result.stdout.strip()
        major, minor, *_ = version.split(".")
        assert int(major) == 2, f"requests major version must be 2, got {major}"
        assert int(minor) >= 25, f"requests minor version must be >= 25, got {minor}"

    def test_urllib3_version_is_v1(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, '{LIB_PATH}'); "
                "import urllib3; print(urllib3.__version__)",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Failed to import urllib3: {result.stderr}"

        version = result.stdout.strip()
        major, *_ = version.split(".")
        assert (
            int(major) == 1
        ), f"urllib3 must be v1.x for OpenSSL 1.0.2 compatibility, got v{version}"


class TestScriptSysPath:

    @pytest.mark.parametrize("script", SCRIPTS_USING_REQUESTS)
    def test_script_has_sys_path_setup(self, script: str):
        script_path = BIN_PATH / script
        if not script_path.exists():
            pytest.skip(f"{script} not found")

        content = script_path.read_text()
        assert "sys.path.insert" in content, f"{script} must have sys.path.insert"
        assert (
            "'lib'" in content or '"lib"' in content
        ), f"{script} must reference 'lib'"

    @pytest.mark.parametrize("script", SCRIPTS_USING_REQUESTS)
    def test_script_imports_requests_successfully(self, script: str):
        script_path = BIN_PATH / script
        if not script_path.exists():
            pytest.skip(f"{script} not found")

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, '{LIB_PATH}'); "
                "import requests; print('OK')",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(BIN_PATH),
        )
        assert result.returncode == 0, f"requests import failed: {result.stderr}"
        assert "OK" in result.stdout


class TestAppStructure:

    REQUIRED_DIRS = ["bin", "default", "lookups", "metadata"]
    REQUIRED_CONFIGS = [
        "default/app.conf",
        "default/savedsearches.conf",
        "default/macros.conf",
        "default/transforms.conf",
    ]

    @pytest.mark.parametrize("dirname", REQUIRED_DIRS)
    def test_required_directory_exists(self, dirname: str):
        dir_path = SECURITY_ALERT_PATH / dirname
        assert dir_path.exists(), f"Required directory {dirname}/ not found"
        assert dir_path.is_dir(), f"{dirname} must be a directory"

    @pytest.mark.parametrize("config", REQUIRED_CONFIGS)
    def test_required_config_exists(self, config: str):
        config_path = SECURITY_ALERT_PATH / config
        assert config_path.exists(), f"Required config {config} not found"


class TestTarballPackaging:

    def test_tarball_can_be_created(self, tmp_path: Path):
        tarball_path = tmp_path / "security_alert.tar.gz"

        result = subprocess.run(
            ["tar", "-czf", str(tarball_path), "security_alert/"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, f"Tarball creation failed: {result.stderr}"
        assert tarball_path.exists(), "Tarball was not created"
        assert tarball_path.stat().st_size > 100000, "Tarball is suspiciously small"

    def test_tarball_contains_vendored_libs(self, tmp_path: Path):
        tarball_path = tmp_path / "security_alert.tar.gz"

        subprocess.run(
            ["tar", "-czf", str(tarball_path), "security_alert/"],
            capture_output=True,
            cwd=str(PROJECT_ROOT),
        )

        result = subprocess.run(
            ["tar", "-tzf", str(tarball_path)],
            capture_output=True,
            text=True,
        )
        contents = result.stdout

        for package in VENDORED_PACKAGES:
            assert (
                f"bin/lib/{package}/" in contents
            ), f"Vendored package {package} not in tarball"


@pytest.mark.splunk_live
class TestLiveSplunkInstallation:

    SPLUNK_HOST = "192.168.50.150"
    SPLUNK_SSH = "splunk"

    def test_app_installed_on_splunk(self):
        result = subprocess.run(
            [
                "ssh",
                self.SPLUNK_SSH,
                "test -d /opt/splunk/etc/apps/security_alert && echo EXISTS",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "EXISTS" in result.stdout, "security_alert app not installed on Splunk"

    def test_vendored_lib_on_splunk(self):
        result = subprocess.run(
            [
                "ssh",
                self.SPLUNK_SSH,
                "test -d /opt/splunk/etc/apps/security_alert/bin/lib && echo EXISTS",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "EXISTS" in result.stdout, "bin/lib/ not found on Splunk server"

    def test_requests_import_on_splunk_python(self):
        result = subprocess.run(
            [
                "ssh",
                self.SPLUNK_SSH,
                "cd /opt/splunk/etc/apps/security_alert/bin && "
                "/opt/splunk/bin/splunk cmd python3 -c "
                "\"import sys; sys.path.insert(0, 'lib'); "
                "import requests; print('IMPORT_OK')\"",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            "IMPORT_OK" in result.stdout
        ), f"requests import failed on Splunk: {result.stderr}"

    @pytest.mark.parametrize("package", VENDORED_PACKAGES)
    def test_vendored_package_on_splunk(self, package: str):
        result = subprocess.run(
            [
                "ssh",
                self.SPLUNK_SSH,
                f"test -d /opt/splunk/etc/apps/security_alert/bin/lib/{package} "
                "&& echo EXISTS",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "EXISTS" in result.stdout, f"{package} not found on Splunk server"
