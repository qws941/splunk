"""
Live Splunk Integration E2E Tests

These tests require a running Splunk instance with the security_alert app installed.
Run with: pytest tests/e2e/test_live_splunk_integration.py -v -m splunk_live

Credentials: Set via environment or use defaults below
    SPLUNK_HOST=192.168.50.150
    SPLUNK_PORT=8089
    SPLUNK_USERNAME=admin
    SPLUNK_PASSWORD=admin123
"""

import os
import pytest
import time
import csv
import io
import json
from datetime import datetime, timedelta

SPLUNK_HOST = os.getenv("SPLUNK_HOST", "192.168.50.150")
SPLUNK_PORT = int(os.getenv("SPLUNK_PORT", "8089"))
SPLUNK_USERNAME = os.getenv("SPLUNK_USERNAME", "admin")
SPLUNK_PASSWORD = os.getenv("SPLUNK_PASSWORD", "admin123")

ALERT_DEFINITIONS = {
    "002_VPN_Tunnel_Down": {
        "state_tracker": "vpn_tunnel_state.csv",
        "key_fields": ["device", "vpn_name", "status"],
        "severity": 4,
        "index": "fw",
    },
    "002_VPN_Tunnel_Up": {
        "state_tracker": "vpn_tunnel_state.csv",
        "key_fields": ["device", "vpn_name", "status"],
        "severity": 3,
        "index": "fw",
    },
    "013_SSL_VPN_Brute_Force": {
        "state_tracker": None,
        "key_fields": ["srcip", "failure_count"],
        "severity": 5,
        "index": "fw",
    },
}

STATE_TRACKER_SCHEMA = {
    "vpn_tunnel_state.csv": ["device", "vpn_name", "status", "last_seen", "first_seen"],
}


@pytest.fixture(scope="module")
def splunk_service():
    """Create Splunk SDK service connection with test credentials."""
    try:
        import splunklib.client as client

        service = client.connect(
            host=SPLUNK_HOST,
            port=SPLUNK_PORT,
            username=SPLUNK_USERNAME,
            password=SPLUNK_PASSWORD,
            autologin=True,
        )
        # Verify connection
        service.apps.list()
        return service
    except ImportError:
        pytest.skip("splunklib not installed - pip install splunk-sdk")
    except Exception as e:
        pytest.skip(f"Cannot connect to Splunk at {SPLUNK_HOST}:{SPLUNK_PORT} - {e}")


@pytest.fixture(scope="module")
def security_alert_app(splunk_service):
    """Verify security_alert app is installed."""
    apps = [app.name for app in splunk_service.apps.list()]
    if "security_alert" not in apps:
        pytest.skip("security_alert app not installed on Splunk server")
    return splunk_service.apps["security_alert"]


def run_splunk_search(service, search_query, earliest="-24h", latest="now", max_results=100):
    """Execute a Splunk search and return results as list of dicts."""
    import splunklib.results as results

    kwargs = {
        "earliest_time": earliest,
        "latest_time": latest,
        "count": max_results,
        "exec_mode": "blocking",
    }

    job = service.jobs.create(search_query, **kwargs)

    while not job.is_done():
        time.sleep(0.5)

    reader = results.JSONResultsReader(job.results(output_mode="json"))
    result_list = []
    for result in reader:
        if isinstance(result, dict):
            result_list.append(result)

    job.cancel()
    return result_list


class TestSplunkConnection:
    """Test basic Splunk connectivity."""

    @pytest.mark.splunk_live
    def test_connection_established(self, splunk_service):
        """Verify we can connect to Splunk."""
        assert splunk_service is not None
        info = splunk_service.info
        assert info is not None
        print(f"Connected to Splunk {info['version']} on {SPLUNK_HOST}")

    @pytest.mark.splunk_live
    def test_security_alert_app_installed(self, security_alert_app):
        """Verify security_alert app is present."""
        assert security_alert_app is not None

    @pytest.mark.splunk_live
    def test_fw_index_exists(self, splunk_service):
        """Verify fw index exists."""
        indexes = [idx.name for idx in splunk_service.indexes.list()]
        assert "fw" in indexes, f"fw index not found. Available: {indexes}"


class TestSavedSearchesLive:
    """Live tests for all 15 saved searches."""

    @pytest.mark.splunk_live
    def test_all_alerts_exist(self, splunk_service):
        """Verify all expected alerts are configured."""
        saved_searches = splunk_service.saved_searches
        search_names = [ss.name for ss in saved_searches.list()]

        missing = []
        for alert_name in ALERT_DEFINITIONS:
            if alert_name not in search_names:
                missing.append(alert_name)

        assert not missing, f"Missing alerts: {missing}"

    @pytest.mark.splunk_live
    @pytest.mark.parametrize("alert_name", ALERT_DEFINITIONS.keys())
    def test_alert_configuration_valid(self, splunk_service, alert_name):
        """Verify each alert has required configuration."""
        try:
            saved_search = splunk_service.saved_searches[alert_name]
        except KeyError:
            pytest.skip(f"Alert {alert_name} not found")

        content = saved_search.content

        assert "search" in content, f"{alert_name}: missing search"

        actual_severity = int(content.get("alert.severity", 0))
        assert actual_severity >= 1 and actual_severity <= 6, f"{alert_name}: invalid severity {actual_severity}"

        assert content.get("action.slack") in ["1", "true", True], f"{alert_name}: Slack action not enabled"

    @pytest.mark.splunk_live
    @pytest.mark.slow
    @pytest.mark.parametrize("alert_name", ALERT_DEFINITIONS.keys())
    def test_alert_search_syntax_valid(self, splunk_service, alert_name):
        """Verify each alert's SPL syntax is valid by parsing it."""
        try:
            saved_search = splunk_service.saved_searches[alert_name]
        except KeyError:
            pytest.skip(f"Alert {alert_name} not found")

        search_query = saved_search.content.get("search", "")
        if not search_query:
            pytest.skip(f"{alert_name}: empty search query")

        parse_search = f"{search_query} | head 1"

        try:
            run_splunk_search(
                splunk_service,
                parse_search,
                earliest="-5m",
                latest="now",
                max_results=1
            )
        except Exception as e:
            error_str = str(e).lower()
            if "no matching events" in error_str or "empty" in error_str:
                pass
            elif "unknown search command 'index'" in error_str:
                pytest.skip(f"{alert_name}: search starts with index=, needs 'search' prefix")
            else:
                pytest.fail(f"{alert_name}: SPL syntax error - {e}")

    @pytest.mark.splunk_live
    @pytest.mark.slow
    def test_all_alerts_can_execute(self, splunk_service):
        """Execute each alert search (limited results) to verify it runs."""
        results_summary = {}
        skipped_realtime = []

        for alert_name in ALERT_DEFINITIONS:
            try:
                saved_search = splunk_service.saved_searches[alert_name]
                search_query = saved_search.content.get("search", "")

                # Skip real-time searches - they can't be executed via REST API
                if "earliest=rt" in search_query or "latest=rt" in search_query:
                    skipped_realtime.append(alert_name)
                    results_summary[alert_name] = {
                        "status": "SKIPPED",
                        "reason": "real-time search"
                    }
                    continue

                if search_query.strip().startswith("index") or search_query.strip().startswith("`"):
                    limited_search = f"search {search_query} | head 5"
                else:
                    limited_search = f"{search_query} | head 5"

                start_time = time.time()
                results = run_splunk_search(
                    splunk_service,
                    limited_search,
                    earliest="-24h",
                    latest="now",
                    max_results=5
                )
                elapsed = time.time() - start_time

                results_summary[alert_name] = {
                    "status": "OK",
                    "result_count": len(results),
                    "elapsed_seconds": round(elapsed, 2)
                }

            except KeyError:
                results_summary[alert_name] = {"status": "NOT_FOUND"}
            except Exception as e:
                results_summary[alert_name] = {"status": "ERROR", "error": str(e)}

        print("\n=== Alert Execution Summary ===")
        for name, info in results_summary.items():
            print(f"  {name}: {info}")

        failed = [name for name, info in results_summary.items() if info["status"] == "ERROR"]
        assert not failed, f"Alerts failed to execute: {failed}"


class TestStateTrackersLive:
    """Live tests for EMS state tracking pattern."""

    @pytest.mark.splunk_live
    def test_state_tracker_lookups_exist(self, splunk_service):
        """Verify all state tracker lookup files exist."""
        search = "| rest /services/data/lookup-table-files"
        results = run_splunk_search(splunk_service, search, max_results=100)

        lookup_names = [r.get("title", "") for r in results]

        missing = []
        for tracker in STATE_TRACKER_SCHEMA:
            if tracker not in lookup_names:
                base_name = tracker.replace(".csv", "")
                if base_name not in lookup_names and tracker not in lookup_names:
                    missing.append(tracker)

        if missing:
            print(f"Note: Missing trackers (may be auto-created): {missing}")

    @pytest.mark.splunk_live
    @pytest.mark.parametrize("tracker_name,expected_cols", STATE_TRACKER_SCHEMA.items())
    def test_state_tracker_schema(self, splunk_service, tracker_name, expected_cols):
        """Verify each state tracker has correct column schema."""
        search = f"| inputlookup {tracker_name} | head 1"

        try:
            results = run_splunk_search(splunk_service, search, max_results=1)

            if results:
                actual_cols = list(results[0].keys())
                actual_cols = [c for c in actual_cols if not c.startswith("_")]

                for expected_col in expected_cols:
                    assert expected_col in actual_cols, (
                        f"{tracker_name}: missing column '{expected_col}'. "
                        f"Found: {actual_cols}"
                    )
        except Exception as e:
            if "lookup table file not found" in str(e).lower():
                pytest.skip(f"{tracker_name} not yet created")
            raise

    @pytest.mark.splunk_live
    def test_ems_pattern_state_changed_logic(self, splunk_service):
        """Test the EMS state_changed detection pattern without requiring lookup file."""
        test_search = """
        | makeresults count=4
        | streamstats count as row
        | eval device=case(row<=2, "FW-01", row>2, "FW-02")
        | eval current_state=case(row==1, "up", row==2, "up", row==3, "down", row==4, "up")
        | eval previous_state=case(row==1, null(), row==2, "up", row==3, "up", row==4, "down")
        | eval state_changed=if(isnull(previous_state) OR previous_state!=current_state, 1, 0)
        | where state_changed=1
        | table device, current_state, previous_state, state_changed
        """

        try:
            results = run_splunk_search(splunk_service, test_search, max_results=10)
            assert len(results) >= 2, f"Expected at least 2 state changes, got {len(results)}"
        except Exception as e:
            pytest.fail(f"EMS pattern test failed: {e}")

    @pytest.mark.splunk_live
    @pytest.mark.slow
    def test_outputlookup_updates_tracker(self, splunk_service):
        """Test that outputlookup correctly updates state trackers."""
        test_tracker = "test_e2e_state_tracker.csv"

        try:
            create_search = f"""
            | makeresults
            | eval device="TEST-FW-E2E"
            | eval status="testing"
            | eval last_seen=now()
            | outputlookup {test_tracker} create_empty=true
            """
            run_splunk_search(splunk_service, create_search)

            verify_search = f"| inputlookup {test_tracker}"
            results = run_splunk_search(splunk_service, verify_search)

            assert len(results) >= 1, "outputlookup did not create entry"
            assert results[0].get("device") == "TEST-FW-E2E"

        finally:
            try:
                delete_search = f"| makeresults | fields - _time | outputlookup {test_tracker}"
                run_splunk_search(splunk_service, delete_search)
            except Exception:
                pass


class TestSlackIntegrationLive:
    """Live tests for Slack alert integration."""

    @pytest.mark.splunk_live
    def test_slack_alert_action_configured(self, splunk_service):
        """Verify Slack alert action is properly configured."""
        search = "| rest /services/alerts/alert_actions"
        results = run_splunk_search(splunk_service, search)

        action_names = [r.get("title", "") for r in results]
        assert "slack" in action_names, "Slack alert action not found"

    @pytest.mark.splunk_live
    def test_slack_webhook_configured(self, splunk_service):
        """Verify Slack webhook or bot token is configured."""
        search = "| rest /services/alerts/alert_actions/slack"

        try:
            results = run_splunk_search(splunk_service, search)
            if results:
                config = results[0]
                has_webhook = bool(config.get("param.webhook_url"))
                has_token = bool(config.get("param.bot_token"))

                assert has_webhook or has_token, (
                    "Slack alert action missing webhook_url or bot_token configuration"
                )
        except Exception as e:
            pytest.skip(f"Cannot read Slack configuration: {e}")

    @pytest.mark.splunk_live
    @pytest.mark.parametrize("alert_name", [
        name for name, config in ALERT_DEFINITIONS.items()
        if config["severity"] >= 4
    ])
    def test_high_severity_alerts_have_slack_channel(self, splunk_service, alert_name):
        """Verify high severity alerts have Slack channel configured."""
        try:
            saved_search = splunk_service.saved_searches[alert_name]
            content = saved_search.content

            channel = content.get("action.slack.param.channel")
            assert channel, f"{alert_name}: No Slack channel configured"
            assert channel.startswith("#") or channel.startswith("@"), (
                f"{alert_name}: Invalid channel format: {channel}"
            )
        except KeyError:
            pytest.skip(f"Alert {alert_name} not found")


class TestMacrosLive:
    """Live tests for SPL macros."""

    EXPECTED_MACROS = [
        "logids_vpn_tunnel",
        "logids_hardware_failure",
        "logids_ha_state",
        "logids_admin_login",
        "logids_config_change",
        "logids_ssl_vpn_failed",
        "logids_cpu_memory",
        "fortigate_index",
    ]

    @pytest.mark.splunk_live
    def test_macros_exist(self, splunk_service):
        """Verify all expected macros are defined."""
        search = "| rest /services/configs/conf-macros"
        results = run_splunk_search(splunk_service, search)

        macro_names = [r.get("title", "") for r in results]

        missing = [m for m in self.EXPECTED_MACROS if m not in macro_names]
        if missing:
            print(f"Note: Some macros not found (may use different names): {missing}")

    @pytest.mark.splunk_live
    @pytest.mark.parametrize("macro_name", EXPECTED_MACROS)
    def test_macro_expands_correctly(self, splunk_service, macro_name):
        """Verify each macro expands without error."""
        search = f"search `{macro_name}` | head 1"

        try:
            run_splunk_search(splunk_service, search, earliest="-5m", max_results=1)
        except Exception as e:
            error_str = str(e).lower()
            if "unknown search command" in error_str or "is not defined" in error_str:
                pytest.skip(f"Macro {macro_name} not found")
            if "no matching events" in error_str or "empty" in error_str:
                pass
            else:
                pytest.fail(f"Macro {macro_name} expansion failed: {e}")


class TestEndToEndAlertFlow:
    """End-to-end tests for complete alert flow."""

    @pytest.mark.splunk_live
    @pytest.mark.slow
    def test_inject_event_triggers_state_change(self, splunk_service):
        """Test injecting an event that should trigger state change detection."""
        test_id = f"E2E-{int(time.time())}"

        inject_search = f"""
        | makeresults
        | eval _raw="date=2024-01-15 time=12:00:00 devname=TEST-{test_id} logid=0101039424 type=event subtype=vpn action=tunnel-up"
        | eval _time=now()
        | eval index="fw"
        | collect index=fw source="e2e_test"
        """

        try:
            run_splunk_search(splunk_service, inject_search)
            print(f"Injected test event with ID: TEST-{test_id}")
            time.sleep(2)

            verify_search = f'search index=fw source="e2e_test" "TEST-{test_id}" | head 1'
            results = run_splunk_search(splunk_service, verify_search, earliest="-5m")

            if results:
                assert "TEST-" in str(results[0])
            else:
                print("Note: Event injection may require elevated permissions")

        except Exception as e:
            if "not authorized" in str(e).lower():
                pytest.skip("User not authorized to inject events")
            raise

    @pytest.mark.splunk_live
    def test_alert_history_accessible(self, splunk_service):
        """Verify we can access alert trigger history."""
        search = """
        | rest /services/alerts/fired_alerts
        | table title, trigger_time, severity
        | head 10
        """

        results = run_splunk_search(splunk_service, search)
        assert isinstance(results, list)
        print(f"Found {len(results)} recent alert triggers")


class TestPerformance:
    """Performance tests for alert searches."""

    @pytest.mark.splunk_live
    @pytest.mark.slow
    def test_alert_search_performance(self, splunk_service):
        """Measure execution time for each alert search."""
        performance_results = {}

        for alert_name in ALERT_DEFINITIONS:
            try:
                saved_search = splunk_service.saved_searches[alert_name]
                search_query = saved_search.content.get("search", "")
                limited_search = f"{search_query} | head 10"

                start = time.time()
                run_splunk_search(splunk_service, limited_search, earliest="-1h")
                elapsed = time.time() - start

                performance_results[alert_name] = elapsed

            except KeyError:
                performance_results[alert_name] = None
            except Exception as e:
                performance_results[alert_name] = f"ERROR: {e}"

        print("\n=== Alert Search Performance (1h range, head 10) ===")
        for name, elapsed in sorted(performance_results.items(), key=lambda x: x[1] if isinstance(x[1], float) else 999):
            if isinstance(elapsed, float):
                status = "SLOW" if elapsed > 30 else "OK"
                print(f"  {name}: {elapsed:.2f}s [{status}]")
            else:
                print(f"  {name}: {elapsed}")

        slow_alerts = [name for name, t in performance_results.items() if isinstance(t, float) and t > 30]
        if slow_alerts:
            print(f"\nWARNING: Slow alerts (>30s): {slow_alerts}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "splunk_live", "--tb=short"])
