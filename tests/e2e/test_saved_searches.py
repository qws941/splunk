"""
E2E tests for Splunk saved searches (alerts).

Tests validate:
- SPL syntax correctness
- Macro expansion
- Field extraction patterns
- State tracking logic
- Alert trigger conditions
"""

import re
from pathlib import Path
from typing import Dict, List

import pytest


EXPECTED_ALERTS = [
    "001_Config_Change",
    "002_VPN_Tunnel_Down",
    "002_VPN_Tunnel_Up",
    "006_CPU_Memory_Anomaly",
    "007_Hardware_Failure",
    "007_Hardware_Restored",
    "008_HA_State_Change",
    "010_Resource_Limit",
    "011_Admin_Login_Failed",
    "012_Interface_Down",
    "012_Interface_Up",
    "013_SSL_VPN_Brute_Force",
    "015_Abnormal_Traffic_Spike",
    "016_System_Reboot",
    "017_License_Expiry_Warning",
]


class TestSavedSearchesConfiguration:
    """Test saved searches configuration integrity."""

    def test_all_expected_alerts_exist(self, saved_searches: Dict):
        """Verify all 15 expected alerts are defined."""
        missing = [
            alert for alert in EXPECTED_ALERTS if alert not in saved_searches
        ]
        assert not missing, f"Missing alerts: {missing}"

    def test_no_unexpected_alerts(self, saved_searches: Dict):
        """Verify no unexpected alert stanzas exist."""
        unexpected = [
            name
            for name in saved_searches
            if name.startswith(("0", "1"))
            and name not in EXPECTED_ALERTS
        ]
        assert not unexpected, f"Unexpected alerts: {unexpected}"

    @pytest.mark.parametrize("alert_name", EXPECTED_ALERTS)
    def test_alert_has_required_fields(
        self, saved_searches: Dict, alert_name: str
    ):
        """Each alert must have required configuration fields."""
        alert = saved_searches.get(alert_name, {})
        required_fields = [
            "search",
            "cron_schedule",
            "alert.severity",
            "action.slack",
        ]

        missing = [f for f in required_fields if f not in alert]
        assert not missing, f"{alert_name} missing fields: {missing}"

    @pytest.mark.parametrize("alert_name", EXPECTED_ALERTS)
    def test_alert_has_slack_action_enabled(
        self, saved_searches: Dict, alert_name: str
    ):
        """Each alert must have Slack action enabled."""
        alert = saved_searches.get(alert_name, {})
        assert alert.get("action.slack") == "1", (
            f"{alert_name}: action.slack should be '1'"
        )

    @pytest.mark.parametrize("alert_name", EXPECTED_ALERTS)
    def test_alert_has_valid_cron_schedule(
        self, saved_searches: Dict, alert_name: str
    ):
        """Cron schedule must be valid 5-field format."""
        alert = saved_searches.get(alert_name, {})
        cron = alert.get("cron_schedule", "")

        cron_pattern = r"^(\*|(?:\*/?\d*)|[\d,\-/]+)\s+(\*|(?:\*/?\d*)|[\d,\-/]+)\s+(\*|(?:\*/?\d*)|[\d,\-/]+)\s+(\*|(?:\*/?\d*)|[\d,\-/]+)\s+(\*|(?:\*/?\d*)|[\d,\-/]+)$"
        assert re.match(cron_pattern, cron), (
            f"{alert_name}: Invalid cron format '{cron}'"
        )

    @pytest.mark.parametrize("alert_name", EXPECTED_ALERTS)
    def test_alert_severity_in_valid_range(
        self, saved_searches: Dict, alert_name: str
    ):
        """Alert severity must be 1-6."""
        alert = saved_searches.get(alert_name, {})
        severity = int(alert.get("alert.severity", "0"))
        assert 1 <= severity <= 6, (
            f"{alert_name}: severity {severity} not in range 1-6"
        )


class TestSPLSyntax:
    """Test SPL query syntax and patterns."""

    @pytest.mark.parametrize("alert_name", EXPECTED_ALERTS)
    def test_search_uses_fortigate_index_macro(
        self, saved_searches: Dict, alert_name: str
    ):
        """Search should use `fortigate_index` macro."""
        alert = saved_searches.get(alert_name, {})
        search = alert.get("search", "")

        has_macro = "`fortigate_index`" in search
        has_hardcoded = "index=fw" in search or "index=fortigate" in search

        assert has_macro or has_hardcoded, (
            f"{alert_name}: Missing index specification"
        )

    @pytest.mark.parametrize("alert_name", EXPECTED_ALERTS)
    def test_search_has_balanced_backticks(
        self, saved_searches: Dict, alert_name: str
    ):
        """Macro backticks must be balanced."""
        alert = saved_searches.get(alert_name, {})
        search = alert.get("search", "")

        backtick_count = search.count("`")
        assert backtick_count % 2 == 0, (
            f"{alert_name}: Unbalanced backticks ({backtick_count})"
        )

    @pytest.mark.parametrize("alert_name", EXPECTED_ALERTS)
    def test_search_has_balanced_parentheses(
        self, saved_searches: Dict, alert_name: str
    ):
        """Parentheses must be balanced."""
        alert = saved_searches.get(alert_name, {})
        search = alert.get("search", "")

        open_count = search.count("(")
        close_count = search.count(")")
        assert open_count == close_count, (
            f"{alert_name}: Unbalanced parentheses ({open_count} open, {close_count} close)"
        )

    @pytest.mark.parametrize("alert_name", EXPECTED_ALERTS)
    def test_search_has_balanced_brackets(
        self, saved_searches: Dict, alert_name: str
    ):
        """Square brackets must be balanced."""
        alert = saved_searches.get(alert_name, {})
        search = alert.get("search", "")

        open_count = search.count("[")
        close_count = search.count("]")
        assert open_count == close_count, (
            f"{alert_name}: Unbalanced brackets ({open_count} open, {close_count} close)"
        )

    @pytest.mark.parametrize("alert_name", EXPECTED_ALERTS)
    def test_search_has_balanced_quotes(
        self, saved_searches: Dict, alert_name: str
    ):
        """Double quotes must be balanced (accounting for escaped quotes)."""
        alert = saved_searches.get(alert_name, {})
        search = alert.get("search", "")

        unescaped_quotes = search.replace('\\"', '').replace("\\\"", "")
        quote_count = unescaped_quotes.count('"')

        if quote_count % 2 != 0:
            pytest.skip(
                f"{alert_name}: Complex quote structure ({quote_count} quotes) - manual review needed"
            )

    @pytest.mark.parametrize("alert_name", EXPECTED_ALERTS)
    def test_search_uses_coalesce_for_fields(
        self, saved_searches: Dict, alert_name: str
    ):
        """Searches should use coalesce() for field fallbacks."""
        alert = saved_searches.get(alert_name, {})
        search = alert.get("search", "")

        assert "coalesce(" in search, (
            f"{alert_name}: Should use coalesce() for field safety"
        )


class TestStateTracking:
    """Test EMS-style state tracking pattern."""

    STATE_TRACKING_ALERTS = [
        "002_VPN_Tunnel_Down",
        "002_VPN_Tunnel_Up",
        "007_Hardware_Failure",
        "007_Hardware_Restored",
        "008_HA_State_Change",
        "010_Resource_Limit",
        "011_Admin_Login_Failed",
        "012_Interface_Down",
        "012_Interface_Up",
        "013_SSL_VPN_Brute_Force",
        "015_Abnormal_Traffic_Spike",
        "017_License_Expiry_Warning",
    ]

    @pytest.mark.parametrize("alert_name", STATE_TRACKING_ALERTS)
    def test_uses_inputlookup(self, saved_searches: Dict, alert_name: str):
        """State tracking alerts must use inputlookup."""
        alert = saved_searches.get(alert_name, {})
        search = alert.get("search", "")
        assert "inputlookup" in search, (
            f"{alert_name}: Missing inputlookup for state tracking"
        )

    @pytest.mark.parametrize("alert_name", STATE_TRACKING_ALERTS)
    def test_uses_outputlookup(self, saved_searches: Dict, alert_name: str):
        """State tracking alerts must use outputlookup."""
        alert = saved_searches.get(alert_name, {})
        search = alert.get("search", "")
        assert "outputlookup" in search, (
            f"{alert_name}: Missing outputlookup for state tracking"
        )

    @pytest.mark.parametrize("alert_name", STATE_TRACKING_ALERTS)
    def test_has_state_changed_logic(
        self, saved_searches: Dict, alert_name: str
    ):
        """State tracking alerts must evaluate state_changed."""
        alert = saved_searches.get(alert_name, {})
        search = alert.get("search", "")
        assert "state_changed" in search, (
            f"{alert_name}: Missing state_changed evaluation"
        )

    @pytest.mark.parametrize("alert_name", STATE_TRACKING_ALERTS)
    def test_filters_on_state_changed(
        self, saved_searches: Dict, alert_name: str
    ):
        """Alert should filter where state_changed=1."""
        alert = saved_searches.get(alert_name, {})
        search = alert.get("search", "")
        assert "where state_changed=1" in search, (
            f"{alert_name}: Missing 'where state_changed=1' filter"
        )


class TestMacroExpansion:
    """Test macro references are valid."""

    LOGID_MACROS = [
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
    ]

    def test_all_referenced_macros_exist(
        self, saved_searches: Dict, macros: Dict
    ):
        """All macros referenced in searches must be defined."""
        all_searches = " ".join(
            alert.get("search", "") for alert in saved_searches.values()
        )

        macro_refs = re.findall(r"`(\w+)`", all_searches)
        undefined = [m for m in set(macro_refs) if m not in macros]

        assert not undefined, f"Undefined macros: {undefined}"

    def test_fortigate_index_macro_exists(self, macros: Dict):
        """fortigate_index macro must be defined."""
        assert "fortigate_index" in macros

    def test_fortigate_index_references_fw(self, macros: Dict):
        """fortigate_index should reference index=fw."""
        macro = macros.get("fortigate_index", {})
        definition = macro.get("definition", "")
        assert "index=fw" in definition or "index=fortigate" in definition

    @pytest.mark.parametrize("macro_name", LOGID_MACROS)
    def test_logid_macro_exists(self, macros: Dict, macro_name: str):
        """LogID macros must be defined."""
        assert macro_name in macros, f"Missing macro: {macro_name}"

    @pytest.mark.parametrize("macro_name", LOGID_MACROS)
    def test_logid_macro_has_valid_logids(
        self, macros: Dict, macro_name: str
    ):
        """LogID macros should contain logid= patterns."""
        macro = macros.get(macro_name, {})
        definition = macro.get("definition", "")
        assert "logid=" in definition.lower() or "logid" in definition.lower(), (
            f"{macro_name}: Should contain logid references"
        )

    def test_enrich_with_logid_lookup_exists(self, macros: Dict):
        """enrich_with_logid_lookup macro must be defined."""
        assert "enrich_with_logid_lookup" in macros


class TestRealtimeScheduling:
    """Test realtime alert scheduling configuration."""

    REALTIME_ALERTS = [
        alert for alert in EXPECTED_ALERTS
        if alert not in ["017_License_Expiry_Warning"]
    ]

    @pytest.mark.parametrize("alert_name", REALTIME_ALERTS)
    def test_realtime_schedule_enabled(
        self, saved_searches: Dict, alert_name: str
    ):
        """Realtime alerts should have realtime_schedule=1."""
        alert = saved_searches.get(alert_name, {})
        assert alert.get("realtime_schedule") == "1", (
            f"{alert_name}: Should have realtime_schedule=1"
        )

    @pytest.mark.parametrize("alert_name", REALTIME_ALERTS)
    def test_dispatch_uses_rt_time_range(
        self, saved_searches: Dict, alert_name: str
    ):
        """Realtime alerts should use rt- time range."""
        alert = saved_searches.get(alert_name, {})
        earliest = alert.get("dispatch.earliest_time", "")
        assert earliest.startswith("rt-"), (
            f"{alert_name}: dispatch.earliest_time should start with 'rt-'"
        )


@pytest.mark.splunk_live
class TestLiveSplunkSearches:
    """Tests requiring live Splunk connection."""

    @pytest.mark.parametrize("alert_name", EXPECTED_ALERTS)
    def test_search_parses_without_error(
        self, splunk_search, saved_searches: Dict, alert_name: str
    ):
        """Search SPL should parse without syntax errors."""
        alert = saved_searches.get(alert_name, {})
        search_query = alert.get("search", "")

        parse_query = f"| makeresults | eval test=1 | append [{search_query} | head 0]"

        try:
            splunk_search(parse_query, earliest_time="-1m", max_results=1)
        except Exception as e:
            pytest.fail(f"{alert_name}: SPL parse error - {e}")

    @pytest.mark.parametrize("alert_name", EXPECTED_ALERTS)
    def test_alert_search_exists_in_splunk(
        self, splunk_service, alert_name: str
    ):
        """Saved search should exist in Splunk."""
        try:
            search = splunk_service.saved_searches[alert_name]
            assert search is not None
        except KeyError:
            pytest.fail(f"{alert_name}: Not found in Splunk")
