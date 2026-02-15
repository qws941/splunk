#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for deployment_health_check.py"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

import deployment_health_check as dhc_module
from deployment_health_check import DeploymentHealthCheck


@pytest.fixture
def app_dir(tmp_path):
    """Create minimal Splunk app directory."""
    for d in ["bin", "default", "local", "lookups", "metadata"]:
        (tmp_path / d).mkdir()
    return tmp_path


@pytest.fixture
def checker(app_dir):
    return DeploymentHealthCheck(app_dir=str(app_dir))


class TestDeploymentHealthCheckInit:
    def test_default_app_dir(self):
        c = DeploymentHealthCheck()
        assert c.app_dir == Path("/opt/splunk/etc/apps/security_alert")

    def test_custom_app_dir(self, app_dir):
        c = DeploymentHealthCheck(app_dir=str(app_dir))
        assert c.app_dir == app_dir

    def test_initial_results_structure(self, checker):
        assert "timestamp" in checker.results
        assert checker.results["checks"] == []
        assert checker.results["errors"] == []
        assert checker.results["warnings"] == []


class TestCheckFileStructure:
    def test_all_dirs_and_files_present(self, checker, app_dir):
        # Create required files
        (app_dir / "default" / "app.conf").write_text("[launcher]")
        (app_dir / "default" / "alert_actions.conf").write_text("[slack]")
        (app_dir / "default" / "setup.xml").write_text("<setup/>")
        (app_dir / "bin" / "slack_blockkit_alert.py").write_text("# test")
        (app_dir / "bin" / "auto_validator.py").write_text("# test")
        (app_dir / "bin" / "splunk_feature_checker.py").write_text("# test")

        checker.check_file_structure()
        assert len(checker.results["errors"]) == 0
        assert checker.results["checks"][0]["status"] == "OK"

    def test_missing_dirs_add_errors(self, tmp_path):
        c = DeploymentHealthCheck(app_dir=str(tmp_path))
        c.check_file_structure()
        # Should have errors for missing dirs
        assert len(c.results["errors"]) > 0
        assert c.results["checks"][0]["status"] == "ERROR"

    def test_missing_files_add_errors(self, checker, app_dir):
        # Dirs exist but no required files
        checker.check_file_structure()
        file_errors = [e for e in checker.results["errors"] if "\ud544\uc218 \ud30c\uc77c" in e]
        assert len(file_errors) > 0


class TestCheckSplunkService:
    def test_running_service(self, checker):
        mock_result = Mock()
        mock_result.stdout = "splunkd is running (PID: 12345)"
        mock_result.returncode = 0
        with patch("deployment_health_check.subprocess.run", return_value=mock_result):
            checker.check_splunk_service()
        assert checker.results["checks"][0]["status"] == "OK"
        assert len(checker.results["errors"]) == 0

    def test_stopped_service(self, checker):
        mock_result = Mock()
        mock_result.stdout = "splunkd is not running"
        mock_result.returncode = 1
        with patch("deployment_health_check.subprocess.run", return_value=mock_result):
            checker.check_splunk_service()
        assert checker.results["checks"][0]["status"] == "ERROR"

    def test_timeout(self, checker):
        with patch(
            "deployment_health_check.subprocess.run",
            side_effect=subprocess.TimeoutExpired("splunk", 10),
        ):
            checker.check_splunk_service()
        assert checker.results["checks"][0]["status"] == "WARNING"

    def test_exception(self, checker):
        with patch(
            "deployment_health_check.subprocess.run",
            side_effect=FileNotFoundError("splunk not found"),
        ):
            checker.check_splunk_service()
        assert checker.results["checks"][0]["status"] == "ERROR"


class TestCheckAppStatus:
    def test_enabled_app(self, checker):
        mock_result = Mock()
        mock_result.stdout = "security_alert  ENABLED"
        with patch("deployment_health_check.subprocess.run", return_value=mock_result):
            checker.check_app_status()
        assert checker.results["checks"][0]["status"] == "OK"

    def test_disabled_app(self, checker):
        mock_result = Mock()
        mock_result.stdout = "security_alert  DISABLED"
        with patch("deployment_health_check.subprocess.run", return_value=mock_result):
            checker.check_app_status()
        assert checker.results["checks"][0]["status"] == "WARNING"

    def test_unknown_status(self, checker):
        mock_result = Mock()
        mock_result.stdout = "something unexpected"
        with patch("deployment_health_check.subprocess.run", return_value=mock_result):
            checker.check_app_status()
        assert checker.results["checks"][0]["status"] == "ERROR"


class TestCheckSchedulerStatus:
    def test_with_active_alerts(self, checker, app_dir):
        content = """[001_Config_Change_Alert]
enableSched = 1
[002_VPN_Alert]
enableSched = 1
[003_Disabled_Alert]
enableSched = 0
"""
        (app_dir / "local" / "savedsearches.conf").write_text(content)
        checker.check_scheduler_status()
        assert checker.results["checks"][0]["status"] == "OK"

    def test_no_savedsearches_file(self, checker, app_dir):
        checker.check_scheduler_status()
        assert checker.results["checks"][0]["status"] == "WARNING"

    def test_all_alerts_disabled(self, checker, app_dir):
        content = """[001_Config_Change_Alert]
enableSched = 0
"""
        (app_dir / "local" / "savedsearches.conf").write_text(content)
        checker.check_scheduler_status()
        assert checker.results["checks"][0]["status"] == "WARNING"


class TestCheckSlackIntegration:
    def test_valid_slack_config(self, checker, app_dir):
        content = """[slack]
param.bot_token = xoxb-test
param.channel = #alerts
"""
        (app_dir / "local" / "alert_actions.conf").write_text(content)
        checker.check_slack_integration()
        assert checker.results["checks"][0]["status"] == "OK"

    def test_no_config_file(self, checker, tmp_path):
        c = DeploymentHealthCheck(app_dir=str(tmp_path))
        c.check_slack_integration()
        assert c.results["checks"][0]["status"] == "ERROR"

    def test_missing_credentials(self, checker, app_dir):
        content = """[slack]
param.channel = #alerts
"""
        # Write to default dir (fallback path)
        (app_dir / "default" / "alert_actions.conf").write_text(content)
        checker.check_slack_integration()
        assert any("\uc778\uc99d" in w for w in checker.results["warnings"])


class TestCheckLookupHealth:
    def test_with_lookup_files(self, checker, app_dir):
        (app_dir / "lookups" / "test.csv").write_text("col_a,col_b\nvalue1,value2\n")
        (app_dir / "lookups" / "test2.csv").write_text("col_x,col_y\nvalue3,value4\n")
        checker.check_lookup_health()
        assert checker.results["checks"][0]["status"] == "OK"

    def test_empty_lookup_files(self, checker, app_dir):
        (app_dir / "lookups" / "empty.csv").write_text("")  # < 10 bytes
        checker.check_lookup_health()
        assert checker.results["checks"][0]["status"] == "WARNING"

    def test_no_lookups_dir(self, tmp_path):
        c = DeploymentHealthCheck(app_dir=str(tmp_path))
        c.check_lookup_health()
        assert c.results["checks"][0]["status"] == "ERROR"


class TestCheckRestApi:
    def test_with_restmap(self, checker, app_dir):
        content = """[admin:security_alert/alerts]
match=/security_alert/alerts
"""
        (app_dir / "local" / "restmap.conf").write_text(content)
        checker.check_rest_api()
        assert checker.results["checks"][0]["status"] == "OK"

    def test_no_restmap(self, checker, app_dir):
        checker.check_rest_api()
        assert checker.results["checks"][0]["status"] == "WARNING"


class TestCheckDashboards:
    def test_with_dashboards(self, checker, app_dir):
        views_dir = app_dir / "local" / "data" / "ui" / "views"
        views_dir.mkdir(parents=True)
        (views_dir / "test.xml").write_text("<dashboard/>")
        checker.check_dashboards()
        assert checker.results["checks"][0]["status"] == "OK"

    def test_no_dashboards(self, checker, app_dir):
        checker.check_dashboards()
        assert checker.results["checks"][0]["status"] == "WARNING"


class TestCheckScriptPermissions:
    def test_executable_scripts(self, checker, app_dir):
        script = app_dir / "bin" / "test.py"
        script.write_text("#!/usr/bin/env python3")
        script.chmod(0o755)
        checker.check_script_permissions()
        assert checker.results["checks"][0]["status"] == "OK"

    def test_non_executable_scripts(self, checker, app_dir):
        script = app_dir / "bin" / "test.py"
        script.write_text("#!/usr/bin/env python3")
        script.chmod(0o644)
        checker.check_script_permissions()
        assert checker.results["checks"][0]["status"] == "WARNING"

    def test_no_bin_dir(self, tmp_path):
        c = DeploymentHealthCheck(app_dir=str(tmp_path))
        c.check_script_permissions()
        assert c.results["checks"][0]["status"] == "ERROR"


class TestPrintResults:
    def test_summary_populated(self, checker, app_dir):
        checker.results["checks"].append({"name": "test", "status": "OK"})
        checker.results["checks"].append({"name": "test2", "status": "ERROR"})
        checker.results["errors"].append("test error")
        checker.print_results()
        assert checker.results["summary"]["total_checks"] == 2
        assert checker.results["summary"]["ok"] == 1
        assert checker.results["summary"]["errors"] == 1
        assert checker.results["summary"]["overall_status"] == "ERROR"

    def test_all_ok_summary(self, checker):
        checker.results["checks"].append({"name": "test", "status": "OK"})
        checker.print_results()
        assert checker.results["summary"]["overall_status"] == "OK"


class TestRunAllChecks:
    def test_returns_results_dict(self, checker, app_dir):
        # Mock subprocess calls
        mock_result = Mock()
        mock_result.stdout = "splunkd is running"
        mock_result.returncode = 0
        with patch("deployment_health_check.subprocess.run", return_value=mock_result):
            results = checker.run_all_checks()
        assert isinstance(results, dict)
        assert "summary" in results
        assert len(results["checks"]) == 10
