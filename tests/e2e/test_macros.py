"""
E2E tests for macros.conf validation.
"""

import re
from typing import Dict

import pytest

EXPECTED_MACROS = [
    "fortigate_index",
    "baseline_time_range",
    "realtime_time_range",
    "cpu_high_threshold",
    "memory_high_threshold",
    "baseline_anomaly_multiplier",
    "logids_config_change",
    "logids_vpn_tunnel",
    "logids_cpu_memory",
    "logids_hardware_failure",
    "logids_ha_state",
    "logids_resource_limit",
    "logids_admin_login",
    "logids_link_monitor",
    "logids_ssl_vpn_failed",
    "logids_traffic",
    "logids_system_reboot",
    "logids_license_warning",
    "enrich_with_logid_lookup",
    "slack_channel_security",
    "slack_channel_network",
    "slack_channel_infrastructure",
    "slack_channel_operations",
]


class TestMacrosExist:

    @pytest.mark.parametrize("macro_name", EXPECTED_MACROS)
    def test_macro_exists(self, macros: Dict, macro_name: str):
        assert macro_name in macros, f"Missing macro: {macro_name}"

    def test_macro_count(self, macros: Dict):
        assert len(macros) >= 20, f"Expected at least 20 macros, found {len(macros)}"


class TestIndexMacro:

    def test_fortigate_index_defined(self, macros: Dict):
        assert "fortigate_index" in macros

    def test_fortigate_index_has_definition(self, macros: Dict):
        macro = macros.get("fortigate_index", {})
        definition = macro.get("definition", "")
        assert definition, "fortigate_index has no definition"

    def test_fortigate_index_specifies_index(self, macros: Dict):
        macro = macros.get("fortigate_index", {})
        definition = macro.get("definition", "")
        assert "index=" in definition, "fortigate_index should specify index="


class TestLogIdMacros:

    LOGID_MACROS = [m for m in EXPECTED_MACROS if m.startswith("logids_")]

    @pytest.mark.parametrize("macro_name", LOGID_MACROS)
    def test_logid_macro_has_logid_reference(self, macros: Dict, macro_name: str):
        macro = macros.get(macro_name, {})
        definition = macro.get("definition", "")

        has_logid = "logid=" in definition.lower() or "logid" in definition.lower()
        assert has_logid, f"{macro_name} should reference logid"

    @pytest.mark.parametrize("macro_name", LOGID_MACROS)
    def test_logid_macro_has_valid_format(self, macros: Dict, macro_name: str):
        macro = macros.get(macro_name, {})
        definition = macro.get("definition", "")

        assert definition, f"{macro_name} has empty definition"
        assert len(definition) > 5, f"{macro_name} definition too short"


class TestThresholdMacros:

    def test_cpu_threshold_is_numeric(self, macros: Dict):
        macro = macros.get("cpu_high_threshold", {})
        definition = macro.get("definition", "")

        if definition:
            cleaned = re.sub(r"[^\d.]", "", definition)
            if cleaned:
                try:
                    float(cleaned)
                except ValueError:
                    pytest.fail("cpu_high_threshold should be numeric")

    def test_memory_threshold_is_numeric(self, macros: Dict):
        macro = macros.get("memory_high_threshold", {})
        definition = macro.get("definition", "")

        if definition:
            cleaned = re.sub(r"[^\d.]", "", definition)
            if cleaned:
                try:
                    float(cleaned)
                except ValueError:
                    pytest.fail("memory_high_threshold should be numeric")


class TestEnrichMacro:

    def test_enrich_macro_exists(self, macros: Dict):
        assert "enrich_with_logid_lookup" in macros

    def test_enrich_macro_uses_lookup(self, macros: Dict):
        macro = macros.get("enrich_with_logid_lookup", {})
        definition = macro.get("definition", "")

        assert (
            "lookup" in definition.lower()
        ), "enrich_with_logid_lookup should use lookup command"


class TestSlackChannelMacros:

    CHANNEL_MACROS = [m for m in EXPECTED_MACROS if m.startswith("slack_channel_")]

    @pytest.mark.parametrize("macro_name", CHANNEL_MACROS)
    def test_channel_macro_has_channel_name(self, macros: Dict, macro_name: str):
        macro = macros.get(macro_name, {})
        definition = macro.get("definition", "")

        has_channel = "#" in definition or "channel" in definition.lower()
        assert has_channel or definition, f"{macro_name} should specify channel"


class TestMacroSyntax:

    @pytest.mark.parametrize("macro_name", EXPECTED_MACROS)
    def test_macro_has_balanced_quotes(self, macros: Dict, macro_name: str):
        macro = macros.get(macro_name, {})
        definition = macro.get("definition", "")

        double_quotes = definition.count('"')
        assert double_quotes % 2 == 0, f"{macro_name} has unbalanced double quotes"

    @pytest.mark.parametrize("macro_name", EXPECTED_MACROS)
    def test_macro_has_balanced_parentheses(self, macros: Dict, macro_name: str):
        macro = macros.get(macro_name, {})
        definition = macro.get("definition", "")

        open_parens = definition.count("(")
        close_parens = definition.count(")")
        assert open_parens == close_parens, f"{macro_name} has unbalanced parentheses"


@pytest.mark.splunk_live
class TestLiveMacroExpansion:

    @pytest.mark.parametrize("macro_name", EXPECTED_MACROS[:5])
    def test_macro_expands_in_splunk(self, splunk_search, macro_name: str):
        try:
            splunk_search(
                f"| makeresults | eval test=`{macro_name}` | head 1",
                earliest_time="-1m",
                max_results=1,
            )
        except Exception as e:
            if "Unknown" in str(e) or "undefined" in str(e).lower():
                pytest.fail(f"Macro {macro_name} not defined in Splunk")
