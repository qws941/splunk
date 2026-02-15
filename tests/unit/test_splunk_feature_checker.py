#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for splunk_feature_checker.py"""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

import splunk_feature_checker as sfc_module
from splunk_feature_checker import SplunkFeatureChecker


@pytest.fixture
def splunk_home(tmp_path):
    """Create minimal Splunk home directory structure."""
    # System dirs
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "splunk").write_text("#!/bin/sh")
    (tmp_path / "bin" / "splunk").chmod(0o755)
    (tmp_path / "etc" / "system" / "local").mkdir(parents=True)
    (tmp_path / "etc" / "apps" / "security_alert" / "default").mkdir(parents=True)
    (tmp_path / "etc" / "apps" / "security_alert" / "lookups").mkdir(parents=True)
    (tmp_path / "var" / "lib" / "splunk").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def checker(splunk_home):
    return SplunkFeatureChecker(splunk_home=str(splunk_home))


class TestSplunkFeatureCheckerInit:
    def test_default_splunk_home(self):
        c = SplunkFeatureChecker()
        assert c.splunk_home == Path("/opt/splunk")

    def test_custom_splunk_home(self, splunk_home):
        c = SplunkFeatureChecker(splunk_home=str(splunk_home))
        assert c.splunk_home == splunk_home

    def test_initial_results_structure(self, checker):
        assert "timestamp" in checker.results
        assert isinstance(checker.results["checks"], dict)
        assert isinstance(checker.results["recommendations"], list)


class TestCheckSystemInfo:
    def test_successful_checks(self, checker):
        with patch.object(
            checker, "run_splunk_command", return_value="Splunk 9.0.0"
        ):
            checker.check_system_info()
        assert checker.results["checks"]["system"]["splunk_version"]["status"] == "OK"

    def test_version_check_failure(self, checker):
        with patch.object(
            checker, "run_splunk_command", side_effect=Exception("not found")
        ):
            checker.check_system_info()
        assert checker.results["checks"]["system"]["splunk_version"]["status"] == "ERROR"


class TestCheckStorageConfiguration:
    def test_no_indexes_conf(self, checker):
        checker.check_storage_configuration()
        storage = checker.results["storage"]
        assert storage["indexes_conf"]["exists"] is False

    def test_with_indexes_conf(self, checker, splunk_home):
        conf = splunk_home / "etc" / "system" / "local" / "indexes.con"
        conf.write_text("[default]\nhomePath = /data/splunk\ncoldPath = /data/cold\n")
        checker.check_storage_configuration()
        storage = checker.results["storage"]
        assert storage["indexes_conf"]["exists"] is True
        assert storage["custom_homePath"] is True
        assert storage["custom_coldPath"] is True


class TestCheckInputs:
    def test_no_inputs_conf(self, checker):
        checker.check_inputs()
        assert checker.results["checks"]["inputs"] == {}

    def test_with_tcp_and_udp(self, checker, splunk_home):
        conf = splunk_home / "etc" / "system" / "local" / "inputs.conf"
        conf.write_text(
            "[tcp://514]\nindex=fw\n[udp://514]\nindex=fw\n[http://hec]\ntoken=abc\n[monitor:///var/log]\nindex=os\n"
        )
        checker.check_inputs()
        inputs = checker.results["checks"]["inputs"]
        assert inputs["tcp"]["configured"] is True
        assert inputs["udp"]["configured"] is True
        assert inputs["hec"]["configured"] is True
        assert inputs["monitor"]["configured"] is True


class TestCheckAlertSystem:
    def test_with_savedsearches(self, checker, splunk_home):
        app_dir = splunk_home / "etc" / "apps" / "security_alert" / "default"
        (app_dir / "savedsearches.con").write_text(
            "[default]\n[001_Alert]\nenableSched = 1\n[002_Alert]\nenableSched = 0\n"
        )
        (app_dir / "alert_actions.con").write_text("[slack]\nparam.webhook = x\n")
        checker.check_alert_system()
        alerts = checker.results["checks"]["alerts"]
        assert alerts["savedsearches"]["status"] == "OK"
        assert alerts["alert_actions"]["slack"] is True

    def test_no_conf_files(self, checker):
        checker.check_alert_system()
        alerts = checker.results["checks"]["alerts"]
        assert alerts["savedsearches"]["exists"] is False


class TestCheckLookups:
    def test_with_csv_files(self, checker, splunk_home):
        lookups_dir = (
            splunk_home / "etc" / "apps" / "security_alert" / "lookups"
        )
        (lookups_dir / "test.csv").write_text("a,b\n1,2\n")
        (lookups_dir / "state_tracker_vpn.csv").write_text("device,state\n")
        checker.check_lookups()
        lookups = checker.results["checks"]["lookups"]
        assert lookups["csv_count"] == 2

    def test_no_lookups_dir(self, tmp_path):
        (tmp_path / "bin" / "splunk").parent.mkdir(parents=True)
        (tmp_path / "bin" / "splunk").write_text("#!/bin/sh")
        (tmp_path / "bin" / "splunk").chmod(0o755)
        c = SplunkFeatureChecker(splunk_home=str(tmp_path))
        c.check_lookups()
        assert c.results["checks"]["lookups"].get("status") == "WARNING"


class TestSuggestAutomation:
    def test_returns_8_suggestions(self, checker):
        checker.suggest_automation()
        assert checker.results["automation"]["count"] == 8
        assert len(checker.results["automation"]["suggestions"]) == 8

    def test_suggestion_structure(self, checker):
        checker.suggest_automation()
        for s in checker.results["automation"]["suggestions"]:
            assert "type" in s
            assert "title" in s
            assert "description" in s
            assert "example" in s
            assert "benefit" in s


class TestRunSplunkCommand:
    def test_success(self, checker, splunk_home):
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Splunk 9.0.0"
        mock_result.stderr = ""
        with patch("splunk_feature_checker.subprocess.run", return_value=mock_result):
            output = checker.run_splunk_command("version")
        assert output == "Splunk 9.0.0"

    def test_command_failure(self, checker, splunk_home):
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"
        with patch("splunk_feature_checker.subprocess.run", return_value=mock_result):
            with pytest.raises(Exception, match="Command failed"):
                checker.run_splunk_command("bad command")

    def test_binary_not_found(self, tmp_path):
        c = SplunkFeatureChecker(splunk_home=str(tmp_path))
        with pytest.raises(Exception, match="not found"):
            c.run_splunk_command("version")


class TestSaveResults:
    def test_saves_json(self, checker, splunk_home):
        checker.results["checks"]["test"] = {"status": "OK"}
        checker.save_results()
        output_file = (
            splunk_home
            / "etc"
            / "apps"
            / "security_alert"
            / "splunk_feature_check_results.json"
        )
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["checks"]["test"]["status"] == "OK"

    def test_handles_write_error(self, tmp_path):
        c = SplunkFeatureChecker(splunk_home=str(tmp_path))
        # No app_dir exists, so save should fail gracefully
        c.save_results()  # Should not raise
