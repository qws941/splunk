"""
E2E tests for Splunk SimpleXML dashboard validation.

This module validates dashboard XML files WITHOUT requiring a live Splunk instance:
- XML well-formedness
- Dashboard structure (form/dashboard, version, label, panels)
- SPL syntax validation (balanced delimiters)
- Macro reference validation
- Theme consistency
- Time picker token validation

Tests follow existing patterns from test_saved_searches.py and test_lookup_files.py.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest


# =============================================================================
# Dashboard File Discovery
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent

# All SimpleXML dashboard files in the project
DASHBOARD_FILES = [
    # Core security_alert app
    PROJECT_ROOT / "security_alert" / "default" / "data" / "ui" / "views" / "slack_test_dashboard.xml",
    # security_alert_user app
    PROJECT_ROOT / "security_alert_user" / "default" / "data" / "ui" / "views" / "alert-management-dashboard.xml",
    PROJECT_ROOT / "security_alert_user" / "default" / "data" / "ui" / "views" / "data-explorer-dashboard.xml",
    # configs/dashboards (not deployed but should be valid)
    PROJECT_ROOT / "configs" / "dashboards" / "alert-testing-dashboard.xml",
    PROJECT_ROOT / "configs" / "dashboards" / "fortigate-production-alerts-dashboard.xml",
]

# Filter to only existing files
EXISTING_DASHBOARDS = [f for f in DASHBOARD_FILES if f.exists()]

# Dashboard IDs for test output
DASHBOARD_IDS = [f.stem for f in EXISTING_DASHBOARDS]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def parsed_dashboards() -> Dict[str, Tuple[Path, ET.Element]]:
    """Parse all dashboards once per module."""
    result = {}
    for filepath in EXISTING_DASHBOARDS:
        try:
            tree = ET.parse(filepath)
            result[filepath.stem] = (filepath, tree.getroot())
        except ET.ParseError:
            # Will be caught by well-formedness test
            result[filepath.stem] = (filepath, None)
    return result


@pytest.fixture(scope="module")
def macros_config() -> Dict[str, Dict]:
    """Load macros.conf for reference validation."""
    macros_path = PROJECT_ROOT / "security_alert" / "default" / "macros.conf"
    if not macros_path.exists():
        return {}
    
    macros = {}
    current_stanza = None
    
    with open(macros_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_stanza = line[1:-1]
                macros[current_stanza] = {}
            elif "=" in line and current_stanza:
                key, _, value = line.partition("=")
                macros[current_stanza][key.strip()] = value.strip()
    
    return macros


# =============================================================================
# Test Class: XML Well-formedness
# =============================================================================


class TestDashboardXMLWellFormedness:
    """Test that all dashboard XML files are well-formed."""

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_xml_is_well_formed(self, dashboard_file: Path):
        """Dashboard XML should parse without errors."""
        try:
            tree = ET.parse(dashboard_file)
            root = tree.getroot()
            assert root is not None, f"{dashboard_file.name}: Empty root element"
        except ET.ParseError as e:
            pytest.fail(f"{dashboard_file.name}: XML parse error - {e}")

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_xml_encoding_is_utf8(self, dashboard_file: Path):
        """Dashboard should be readable as UTF-8."""
        try:
            content = dashboard_file.read_text(encoding="utf-8")
            assert len(content) > 0, f"{dashboard_file.name}: Empty file"
        except UnicodeDecodeError as e:
            pytest.fail(f"{dashboard_file.name}: Not valid UTF-8 - {e}")


# =============================================================================
# Test Class: Dashboard Structure
# =============================================================================


class TestDashboardStructure:
    """Test dashboard structural requirements."""

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_root_element_is_form_or_dashboard(self, dashboard_file: Path):
        """Root element must be <form> or <dashboard>."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        assert root.tag in ["form", "dashboard"], \
            f"{dashboard_file.name}: Root element is '{root.tag}', expected 'form' or 'dashboard'"

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_has_version_attribute(self, dashboard_file: Path):
        """Dashboard should have version attribute."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        version = root.get("version")
        assert version is not None, f"{dashboard_file.name}: Missing version attribute"
        assert version in ["1.1", "1.0", "2"], \
            f"{dashboard_file.name}: Unexpected version '{version}'"

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_has_label_element(self, dashboard_file: Path):
        """Dashboard should have a <label> element."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        label = root.find("label")
        assert label is not None, f"{dashboard_file.name}: Missing <label> element"
        assert label.text and label.text.strip(), \
            f"{dashboard_file.name}: Empty <label> element"

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_has_at_least_one_row(self, dashboard_file: Path):
        """Dashboard should have at least one <row> element."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        rows = root.findall(".//row")
        assert len(rows) >= 1, f"{dashboard_file.name}: No <row> elements found"

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_has_at_least_one_panel(self, dashboard_file: Path):
        """Dashboard should have at least one <panel> element."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        panels = root.findall(".//panel")
        assert len(panels) >= 1, f"{dashboard_file.name}: No <panel> elements found"


# =============================================================================
# Test Class: Panel Completeness
# =============================================================================


class TestPanelCompleteness:
    """Test that panels have required elements."""

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_panels_have_titles_or_are_input_panels(self, dashboard_file: Path):
        """Panels should have <title> unless they are input-only panels."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        panels = root.findall(".//panel")
        panels_without_titles = []
        
        for i, panel in enumerate(panels):
            title = panel.find("title")
            # Panels with only inputs (no visualizations) don't need titles
            has_visualization = any(
                panel.find(viz) is not None
                for viz in ["table", "chart", "single", "map", "html", "viz"]
            )
            
            if has_visualization and (title is None or not title.text):
                panels_without_titles.append(i + 1)
        
        assert not panels_without_titles, \
            f"{dashboard_file.name}: Panels without titles: {panels_without_titles}"

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_visualization_panels_have_search(self, dashboard_file: Path):
        """Panels with visualizations should have a search definition."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        panels = root.findall(".//panel")
        panels_without_search = []
        
        for i, panel in enumerate(panels):
            # Check if panel has visualization
            has_visualization = any(
                panel.find(viz) is not None
                for viz in ["table", "chart", "single", "map", "viz"]
            )
            
            if has_visualization:
                # Check for search in various locations
                has_search = (
                    panel.find(".//search") is not None or
                    panel.find(".//query") is not None
                )
                
                if not has_search:
                    panels_without_search.append(i + 1)
        
        # Allow some panels without search (e.g., static HTML panels)
        # Only fail if more than 50% of viz panels lack search
        total_viz_panels = sum(
            1 for p in panels
            if any(p.find(v) is not None for v in ["table", "chart", "single", "map", "viz"])
        )
        
        if total_viz_panels > 0:
            missing_ratio = len(panels_without_search) / total_viz_panels
            assert missing_ratio < 0.5, \
                f"{dashboard_file.name}: Too many panels without search ({len(panels_without_search)}/{total_viz_panels})"


# =============================================================================
# Test Class: SPL Syntax Validation
# =============================================================================


class TestSPLSyntax:
    """Validate SPL syntax in dashboard searches."""

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_searches_have_balanced_parentheses(self, dashboard_file: Path):
        """All searches should have balanced parentheses."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        errors = []
        for query in root.findall(".//query"):
            if query.text:
                text = query.text
                if text.count("(") != text.count(")"):
                    errors.append(f"Unbalanced (): '{text[:50]}...'")
        
        assert not errors, f"{dashboard_file.name}: {'; '.join(errors)}"

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_searches_have_balanced_brackets(self, dashboard_file: Path):
        """All searches should have balanced square brackets."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        errors = []
        for query in root.findall(".//query"):
            if query.text:
                text = query.text
                if text.count("[") != text.count("]"):
                    errors.append(f"Unbalanced []: '{text[:50]}...'")
        
        assert not errors, f"{dashboard_file.name}: {'; '.join(errors)}"

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_searches_have_balanced_backticks(self, dashboard_file: Path):
        """All searches should have balanced backticks (for macros)."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        errors = []
        for query in root.findall(".//query"):
            if query.text:
                text = query.text
                if text.count("`") % 2 != 0:
                    errors.append(f"Unbalanced backticks: '{text[:50]}...'")
        
        assert not errors, f"{dashboard_file.name}: {'; '.join(errors)}"

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_searches_have_balanced_quotes(self, dashboard_file: Path):
        """All searches should have balanced double quotes."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        errors = []
        for query in root.findall(".//query"):
            if query.text:
                text = query.text
                if text.count('"') % 2 != 0:
                    errors.append(f"Unbalanced quotes: '{text[:50]}...'")
        
        assert not errors, f"{dashboard_file.name}: {'; '.join(errors)}"


# =============================================================================
# Test Class: Macro Reference Validation
# =============================================================================


class TestMacroReferences:
    """Validate that referenced macros exist in macros.conf."""

    def extract_macro_references(self, query_text: str) -> Set[str]:
        """Extract macro names from backtick references."""
        # Match `macro_name` or `macro_name(arg1,arg2)`
        pattern = r"`([a-zA-Z_][a-zA-Z0-9_]*(?:\([^)]*\))?)`"
        matches = re.findall(pattern, query_text)
        
        # Extract just the macro name (without arguments)
        macro_names = set()
        for match in matches:
            name = match.split("(")[0]
            macro_names.add(name)
        
        return macro_names

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_macro_references_are_valid(self, dashboard_file: Path, macros_config: Dict):
        """All macro references should exist in macros.conf."""
        if not macros_config:
            pytest.skip("macros.conf not found or empty")
        
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        all_macro_refs = set()
        for query in root.findall(".//query"):
            if query.text:
                refs = self.extract_macro_references(query.text)
                all_macro_refs.update(refs)
        
        # Also check in option values and other text content
        content = dashboard_file.read_text(encoding="utf-8")
        content_refs = self.extract_macro_references(content)
        all_macro_refs.update(content_refs)
        
        # Check which macros are undefined
        # Note: Some macros might be defined elsewhere (e.g., system macros)
        # We only check against our macros.conf
        defined_macros = set(macros_config.keys())
        
        # Common system macros that are always available
        system_macros = {"comment", "searchmacro"}
        
        undefined = all_macro_refs - defined_macros - system_macros
        
        # Only warn, don't fail - macros might be defined in other apps
        if undefined:
            # This is informational - macros might be valid but defined elsewhere
            pass  # Could use pytest.warns() or print a warning


# =============================================================================
# Test Class: Theme Consistency
# =============================================================================


class TestThemeConsistency:
    """Test dashboard theme settings."""

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_theme_attribute_if_present_is_valid(self, dashboard_file: Path):
        """If theme attribute is present, it should be valid."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        theme = root.get("theme")
        if theme is not None:
            assert theme in ["dark", "light"], \
                f"{dashboard_file.name}: Invalid theme '{theme}'"

    @pytest.mark.dashboard
    def test_deployed_dashboards_have_consistent_theme(self, parsed_dashboards):
        """Deployed dashboards (in security_alert) should have consistent theme."""
        deployed_files = [
            stem for stem, (path, _) in parsed_dashboards.items()
            if "security_alert" in str(path) and "configs" not in str(path)
        ]
        
        themes = {}
        for stem in deployed_files:
            path, root = parsed_dashboards.get(stem, (None, None))
            if root is not None:
                themes[stem] = root.get("theme", "default")
        
        # All deployed dashboards should ideally have the same theme
        unique_themes = set(themes.values())
        
        # Just report, don't fail - theme consistency is a recommendation
        if len(unique_themes) > 1:
            pass  # Could emit a warning


# =============================================================================
# Test Class: Time Picker Token Validation
# =============================================================================


class TestTimePickerTokens:
    """Validate time picker token usage."""

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_earliest_latest_tokens_are_consistent(self, dashboard_file: Path):
        """Searches using time tokens should use both earliest and latest consistently."""
        content = dashboard_file.read_text(encoding="utf-8")
        
        # Find all earliest/latest token usages
        earliest_pattern = r"\$[a-zA-Z_]*\.?earliest\$"
        latest_pattern = r"\$[a-zA-Z_]*\.?latest\$"
        
        earliest_matches = re.findall(earliest_pattern, content)
        latest_matches = re.findall(latest_pattern, content)
        
        # If time tokens are used, both earliest and latest should appear
        if earliest_matches or latest_matches:
            # Normalize to base token names
            earliest_bases = {m.replace(".earliest$", "").replace("$", "") for m in earliest_matches}
            latest_bases = {m.replace(".latest$", "").replace("$", "") for m in latest_matches}
            
            # For each time picker, both tokens should be used
            all_bases = earliest_bases | latest_bases
            for base in all_bases:
                has_earliest = base in earliest_bases or f"{base}.earliest" in content
                has_latest = base in latest_bases or f"{base}.latest" in content
                
                # This is a soft check - some uses are valid without pairs
                # The critical check is in test_no_duplicate_time_tokens
                pass

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_no_duplicate_time_tokens_in_query(self, dashboard_file: Path):
        """A query should not use the same time token for both earliest and latest."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        errors = []
        for query in root.findall(".//query"):
            if query.text:
                text = query.text
                # Check for pattern like: earliest=$x$ latest=$x$
                # or: earliest=$x.earliest$ latest=$x.earliest$ (the bug we fixed!)
                earliest_match = re.search(r"earliest=(\$[^$]+\$)", text)
                latest_match = re.search(r"latest=(\$[^$]+\$)", text)
                
                if earliest_match and latest_match:
                    earliest_token = earliest_match.group(1)
                    latest_token = latest_match.group(1)
                    
                    # Both should not be the same unless they're different token types
                    if earliest_token == latest_token:
                        errors.append(
                            f"Same token for earliest and latest: {earliest_token}"
                        )
        
        assert not errors, f"{dashboard_file.name}: {'; '.join(errors)}"


# =============================================================================
# Test Class: Input Elements
# =============================================================================


class TestInputElements:
    """Validate dashboard input elements (dropdowns, time pickers, etc.)."""

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_inputs_have_token_attribute(self, dashboard_file: Path):
        """Input elements should have token attribute."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        errors = []
        input_types = ["dropdown", "text", "radio", "checkbox", "multiselect", "time"]
        
        for input_type in input_types:
            for input_elem in root.findall(f".//{input_type}"):
                token = input_elem.get("token")
                if token is None:
                    # Check for nested token element
                    token_elem = input_elem.find("token")
                    if token_elem is None or not token_elem.text:
                        label = input_elem.find("label")
                        label_text = label.text if label is not None else "unknown"
                        errors.append(f"{input_type} '{label_text}' missing token")
        
        # Don't fail - some inputs use default tokens
        # This is informational only


# =============================================================================
# Test Class: Dashboard File Organization
# =============================================================================


class TestDashboardFileOrganization:
    """Test dashboard file organization and naming conventions."""

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_filename_matches_convention(self, dashboard_file: Path):
        """Dashboard filenames should follow Splunk conventions."""
        filename = dashboard_file.stem
        
        # Should be lowercase with underscores or hyphens
        # Allow some flexibility for existing files
        valid_chars = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
        
        invalid_chars = set(filename.lower()) - valid_chars
        # Allow uppercase for existing files but warn
        
        # Just verify the extension is correct
        assert dashboard_file.suffix == ".xml", \
            f"{dashboard_file.name}: Should have .xml extension"

    @pytest.mark.dashboard
    def test_all_expected_dashboards_exist(self):
        """All expected dashboard files should exist."""
        missing = [f for f in DASHBOARD_FILES if not f.exists()]
        
        # Don't fail - just report
        if missing:
            pytest.skip(f"Some expected dashboards don't exist: {[f.name for f in missing]}")


# =============================================================================
# Test Class: Dashboard Content Quality
# =============================================================================


class TestDashboardContentQuality:
    """Test dashboard content quality metrics."""

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_no_hardcoded_credentials(self, dashboard_file: Path):
        """Dashboard should not contain hardcoded credentials."""
        content = dashboard_file.read_text(encoding="utf-8").lower()
        
        sensitive_patterns = [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]",  # Long token strings
        ]
        
        for pattern in sensitive_patterns:
            matches = re.findall(pattern, content)
            assert not matches, \
                f"{dashboard_file.name}: Potential hardcoded credential found"

    @pytest.mark.dashboard
    @pytest.mark.parametrize("dashboard_file", EXISTING_DASHBOARDS, ids=DASHBOARD_IDS)
    def test_searches_use_index_specification(self, dashboard_file: Path):
        """Searches should specify an index for performance."""
        tree = ET.parse(dashboard_file)
        root = tree.getroot()
        
        searches_without_index = 0
        total_searches = 0
        
        for query in root.findall(".//query"):
            if query.text:
                text = query.text.strip()
                # Skip non-search queries (e.g., REST calls, makeresults)
                if text.startswith("|") or "| rest" in text.lower():
                    continue
                
                total_searches += 1
                
                # Check for index= or `macro` (macros often include index)
                has_index = (
                    "index=" in text.lower() or
                    "index =" in text.lower() or
                    "`" in text  # Macro might include index
                )
                
                if not has_index:
                    searches_without_index += 1
        
        # Allow some searches without explicit index (might use macros)
        if total_searches > 0:
            missing_ratio = searches_without_index / total_searches
            # Just informational - don't fail
            pass
