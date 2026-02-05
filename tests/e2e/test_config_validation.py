"""E2E tests for Splunk configuration files validation."""

import configparser
import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent.parent
SECURITY_ALERT_PATH = PROJECT_ROOT / "security_alert"
DEFAULT_PATH = SECURITY_ALERT_PATH / "default"

CONFIG_FILES = [
    "alert_actions.conf",
    "app.conf",
    "commands.conf",
    "eventgen.conf",
    "macros.conf",
    "props.conf",
    "restmap.conf",
    "savedsearches.conf",
    "transforms.conf",
]


class TestConfigFilesExist:

    @pytest.mark.parametrize("config_file", CONFIG_FILES)
    def test_config_file_exists(self, config_file: str):
        config_path = DEFAULT_PATH / config_file
        assert config_path.exists(), f"{config_file} not found in default/"


class TestConfigSyntax:

    @pytest.mark.parametrize("config_file", CONFIG_FILES)
    def test_config_is_valid_ini(self, config_file: str):
        config_path = DEFAULT_PATH / config_file
        if not config_path.exists():
            pytest.skip(f"{config_file} not found")

        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(config_path))
        assert len(parser.sections()) >= 0


class TestAppConf:

    def test_app_conf_has_required_stanzas(self):
        config_path = DEFAULT_PATH / "app.conf"
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(config_path))

        assert "launcher" in parser.sections() or "install" in parser.sections()

    def test_app_conf_has_version(self):
        config_path = DEFAULT_PATH / "app.conf"
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(config_path))

        version_found = False
        for section in parser.sections():
            if parser.has_option(section, "version"):
                version_found = True
                version = parser.get(section, "version")
                assert re.match(r"^\d+\.\d+\.\d+", version), f"Invalid version: {version}"
        assert version_found, "No version found in app.conf"

    def test_app_conf_has_label(self):
        config_path = DEFAULT_PATH / "app.conf"
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(config_path))

        label_found = False
        for section in parser.sections():
            if parser.has_option(section, "label"):
                label_found = True
                label = parser.get(section, "label")
                assert len(label) > 0, "Label is empty"
        assert label_found, "No label found in app.conf"


class TestAlertActionsConf:

    def test_alert_actions_conf_exists(self):
        config_path = DEFAULT_PATH / "alert_actions.conf"
        assert config_path.exists()

    def test_alert_actions_has_slack_stanza(self):
        config_path = DEFAULT_PATH / "alert_actions.conf"
        if not config_path.exists():
            pytest.skip("alert_actions.conf not found")

        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(config_path))

        slack_stanzas = [s for s in parser.sections() if "slack" in s.lower()]
        assert len(slack_stanzas) > 0, "No Slack-related stanza found"


class TestSavedSearchesConf:

    def test_savedsearches_conf_exists(self):
        config_path = DEFAULT_PATH / "savedsearches.conf"
        assert config_path.exists()

    def test_savedsearches_has_alerts(self):
        config_path = DEFAULT_PATH / "savedsearches.conf"
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(config_path))

        assert len(parser.sections()) > 0, "No saved searches found"

    def test_saved_searches_have_search_query(self):
        config_path = DEFAULT_PATH / "savedsearches.conf"
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(config_path))

        for section in parser.sections():
            if section == "default":
                continue
            assert parser.has_option(section, "search"), f"Search {section} has no 'search' field"

    def test_saved_searches_have_valid_cron(self):
        config_path = DEFAULT_PATH / "savedsearches.conf"
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(config_path))

        cron_pattern = re.compile(r"^[\d\*\-\/,]+\s+[\d\*\-\/,]+\s+[\d\*\-\/,]+\s+[\d\*\-\/,]+\s+[\d\*\-\/,]+$")

        for section in parser.sections():
            if section == "default":
                continue
            if parser.has_option(section, "cron_schedule"):
                cron = parser.get(section, "cron_schedule")
                assert cron_pattern.match(cron), f"Invalid cron in {section}: {cron}"


class TestMacrosConf:

    def test_macros_conf_exists(self):
        config_path = DEFAULT_PATH / "macros.conf"
        assert config_path.exists()

    def test_macros_have_definition(self):
        config_path = DEFAULT_PATH / "macros.conf"
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(config_path))

        for section in parser.sections():
            if section == "default":
                continue
            assert parser.has_option(section, "definition"), f"Macro {section} has no 'definition'"


class TestTransformsConf:

    def test_transforms_conf_exists(self):
        config_path = DEFAULT_PATH / "transforms.conf"
        assert config_path.exists()

    def test_transforms_have_valid_type(self):
        config_path = DEFAULT_PATH / "transforms.conf"
        if not config_path.exists():
            pytest.skip("transforms.conf not found")

        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(config_path))

        valid_fields = ["REGEX", "FORMAT", "filename", "external_cmd", "fields_list"]

        for section in parser.sections():
            if section == "default":
                continue
            has_valid_field = any(parser.has_option(section, f) for f in valid_fields)
            assert has_valid_field, f"Transform {section} has no valid type field"


class TestRestmapConf:

    def test_restmap_conf_exists(self):
        config_path = DEFAULT_PATH / "restmap.conf"
        assert config_path.exists()

    def test_restmap_has_admin_stanzas(self):
        config_path = DEFAULT_PATH / "restmap.conf"
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(str(config_path))

        admin_stanzas = [s for s in parser.sections() if s.startswith("admin:")]
        assert len(admin_stanzas) > 0, "No admin stanzas found in restmap.conf"


class TestPropsConf:

    def test_props_conf_exists(self):
        config_path = DEFAULT_PATH / "props.conf"
        assert config_path.exists()


class TestNoHardcodedCredentials:

    SENSITIVE_PATTERNS = [
        r"password\s*=\s*['\"][^'\"]+['\"]",
        r"api_key\s*=\s*['\"][^'\"]+['\"]",
        r"secret\s*=\s*['\"][^'\"]+['\"]",
    ]

    EXCLUDED_FILES = ["eventgen.conf"]

    @pytest.mark.parametrize("config_file", CONFIG_FILES)
    def test_no_hardcoded_credentials(self, config_file: str):
        if config_file in self.EXCLUDED_FILES:
            pytest.skip(f"{config_file} uses token placeholders")

        config_path = DEFAULT_PATH / config_file
        if not config_path.exists():
            pytest.skip(f"{config_file} not found")

        content = config_path.read_text()

        for pattern in self.SENSITIVE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            filtered = [m for m in matches if "$" not in m and "{{" not in m and "##" not in m]
            assert len(filtered) == 0, f"Hardcoded credential in {config_file}: {filtered}"
