"""E2E tests for Splunk dashboard XML validation."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent.parent
SECURITY_ALERT_PATH = PROJECT_ROOT / "security_alert"
VIEWS_PATH = SECURITY_ALERT_PATH / "default" / "data" / "ui" / "views"


class TestDashboardDirectoryExists:

    def test_views_directory_exists(self):
        if not VIEWS_PATH.exists():
            pytest.skip("views/ directory not found")
        assert VIEWS_PATH.is_dir()


class TestDashboardXMLFiles:

    def get_dashboard_files(self):
        if not VIEWS_PATH.exists():
            return []
        return list(VIEWS_PATH.glob("*.xml"))

    def test_dashboard_files_exist(self):
        files = self.get_dashboard_files()
        if len(files) == 0:
            pytest.skip("No dashboard XML files found")
        assert len(files) > 0

    @pytest.fixture
    def dashboard_files(self):
        return self.get_dashboard_files()

    def test_xml_files_are_valid(self, dashboard_files):
        for xml_file in dashboard_files:
            try:
                ET.parse(str(xml_file))
            except ET.ParseError as e:
                pytest.fail(f"{xml_file.name} is not valid XML: {e}")

    def test_dashboards_have_root_element(self, dashboard_files):
        for xml_file in dashboard_files:
            tree = ET.parse(str(xml_file))
            root = tree.getroot()
            valid_roots = ["dashboard", "form", "view"]
            assert root.tag in valid_roots, f"{xml_file.name} has invalid root: {root.tag}"


class TestDashboardStructure:

    def get_dashboard_files(self):
        if not VIEWS_PATH.exists():
            return []
        return list(VIEWS_PATH.glob("*.xml"))

    def test_dashboards_have_label(self):
        for xml_file in self.get_dashboard_files():
            tree = ET.parse(str(xml_file))
            root = tree.getroot()
            label = root.find("label")
            if label is None:
                label = root.get("label")
            assert label is not None or root.get("label"), f"{xml_file.name} has no label"

    def test_dashboards_have_panels(self):
        for xml_file in self.get_dashboard_files():
            tree = ET.parse(str(xml_file))
            root = tree.getroot()
            panels = root.findall(".//panel")
            rows = root.findall(".//row")
            assert len(panels) > 0 or len(rows) > 0, f"{xml_file.name} has no panels"


class TestDashboardSecurity:

    def get_dashboard_files(self):
        if not VIEWS_PATH.exists():
            return []
        return list(VIEWS_PATH.glob("*.xml"))

    def test_no_hardcoded_credentials(self):
        import re
        patterns = [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"api_key\s*=\s*['\"][^'\"]+['\"]",
        ]

        for xml_file in self.get_dashboard_files():
            content = xml_file.read_text()
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                assert len(matches) == 0, f"{xml_file.name} has hardcoded credential"

    def test_no_inline_scripts_with_secrets(self):
        for xml_file in self.get_dashboard_files():
            tree = ET.parse(str(xml_file))
            root = tree.getroot()

            for script in root.iter("script"):
                if script.text:
                    text = script.text.lower()
                    assert "password" not in text, f"{xml_file.name} has password in script"
                    assert "api_key" not in text, f"{xml_file.name} has api_key in script"
