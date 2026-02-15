#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for auto_validator.py"""

import csv
import os
import sys
from pathlib import Path

import pytest

import auto_validator
from auto_validator import AutoValidator


@pytest.fixture
def app_dir(tmp_path):
    """Create a minimal Splunk app directory structure."""
    (tmp_path / "default").mkdir()
    (tmp_path / "lookups").mkdir()
    (tmp_path / "local").mkdir()
    (tmp_path / "bin").mkdir()
    (tmp_path / "metadata").mkdir()
    return tmp_path


@pytest.fixture
def validator(app_dir):
    return AutoValidator(app_dir=str(app_dir))


def write_conf_file(path, content):
    """Helper to write a .conf file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_csv(path, fieldnames, rows=None):
    """Helper to write a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)


class TestAutoValidatorInit:
    def test_default_app_dir(self):
        v = AutoValidator()
        assert v.app_dir == Path("/opt/splunk/etc/apps/security_alert")

    def test_custom_app_dir(self, app_dir):
        v = AutoValidator(app_dir=str(app_dir))
        assert v.app_dir == app_dir

    def test_initial_state(self, validator):
        assert validator.errors == []
        assert validator.warnings == []
        assert validator.info == []


class TestValidateLookups:
    def test_missing_lookups_dir_adds_error(self, tmp_path):
        v = AutoValidator(app_dir=str(tmp_path))
        # No lookups dir
        v.validate_lookups()
        assert any("lookups" in e.lower() for e in v.errors)

    def test_missing_required_lookup_adds_error(self, validator, app_dir):
        # No required CSV files
        validator.validate_lookups()
        assert any("fortigate_logid_notification_map" in e for e in validator.errors)

    def test_valid_required_lookups_no_error(self, validator, app_dir):
        # Create required lookups
        for name in [
            "fortigate_logid_notification_map.csv",
            "severity_priority.csv",
            "auto_response_actions.csv",
        ]:
            write_csv(
                app_dir / "lookups" / name,
                ["col1", "col2"],
                [{"col1": "a", "col2": "b"}],
            )
        validator.validate_lookups()
        # Should have no errors about required lookups
        required_errors = [
            e
            for e in validator.errors
            if "fortigate_logid_notification_map" in e
            or "severity_priority" in e
            or "auto_response_actions" in e
        ]
        assert len(required_errors) == 0

    def test_auto_creates_missing_state_trackers(self, validator, app_dir):
        # Create required lookups so we don't fail early
        for name in [
            "fortigate_logid_notification_map.csv",
            "severity_priority.csv",
            "auto_response_actions.csv",
        ]:
            write_csv(
                app_dir / "lookups" / name,
                ["col1", "col2"],
                [{"col1": "a", "col2": "b"}],
            )
        validator.validate_lookups()
        # State tracker auto-creation should show in info
        created_msgs = [i for i in validator.info if "생성" in i]
        assert len(created_msgs) > 0


class TestValidateCsvFile:
    def test_valid_csv(self, validator, app_dir):
        csv_path = app_dir / "lookups" / "test.csv"
        write_csv(csv_path, ["a", "b"], [{"a": "1", "b": "2"}])
        validator.validate_csv_file(csv_path)
        assert len(validator.errors) == 0

    def test_empty_csv_warns(self, validator, app_dir):
        csv_path = app_dir / "lookups" / "empty.csv"
        write_csv(csv_path, ["a", "b"])  # headers only, no data rows
        validator.validate_csv_file(csv_path)
        assert any("0 data row" in w or "empty" in w.lower() for w in validator.warnings)

    def test_nonexistent_csv_errors(self, validator, app_dir):
        csv_path = app_dir / "lookups" / "nope.csv"
        validator.validate_csv_file(csv_path)
        assert any("nope" in e for e in validator.errors)


class TestCreateStateTracker:
    def test_creates_csv_with_headers(self, validator, app_dir):
        tracker_path = app_dir / "lookups" / "new_tracker.csv"
        validator.create_state_tracker(tracker_path)
        assert tracker_path.exists()
        with open(tracker_path) as f:
            reader = csv.reader(f)
            headers = next(reader)
        assert "device" in headers
        assert "_key" in headers

    def test_created_file_has_correct_permissions(self, validator, app_dir):
        tracker_path = app_dir / "lookups" / "perm_test.csv"
        validator.create_state_tracker(tracker_path)
        mode = oct(os.stat(tracker_path).st_mode & 0o777)
        assert mode == "0o644"


class TestValidateTransformsConf:
    def test_missing_file_adds_error(self, validator, app_dir):
        validator.validate_transforms_conf()
        assert any("transforms" in e.lower() for e in validator.errors)

    def test_valid_transforms_conf(self, validator, app_dir):
        content = """
[fortigate_logid_notification_map]
filename = fortigate_logid_notification_map.csv

[severity_priority]
filename = severity_priority.csv

[auto_response_actions]
filename = auto_response_actions.csv

[alert_state]
filename = alert_state.csv

[alert_tracking]
filename = alert_tracking.csv
"""
        write_conf_file(app_dir / "default" / "transforms.conf", content)
        validator.validate_transforms_conf()
        # No errors about missing required stanzas
        transforms_errors = [e for e in validator.errors if "transforms" in e.lower()]
        assert len(transforms_errors) == 0


class TestValidatePropsConf:
    def test_missing_file_adds_error(self, validator, app_dir):
        validator.validate_props_conf()
        assert any("props" in e.lower() for e in validator.errors)

    def test_valid_props_conf(self, validator, app_dir):
        content = """
[fortigate_syslog]
TRANSFORMS-lookup_logid = fortigate_logid_notification_map
TRANSFORMS-lookup_severity = severity_priority
TRANSFORMS-lookup_response = auto_response_actions
"""
        write_conf_file(app_dir / "default" / "props.conf", content)
        validator.validate_props_conf()
        props_errors = [e for e in validator.errors if "props" in e.lower()]
        assert len(props_errors) == 0


class TestValidateSavedSearchesConf:
    def test_missing_file_adds_error(self, validator, app_dir):
        validator.validate_savedsearches_conf()
        assert any("savedsearch" in w.lower() for w in validator.warnings)

    def test_valid_alert_stanza(self, validator, app_dir):
        content = """
[001_Config_Change_Alert]
search = index=fw logid=0100032001 | stats count by device
cron_schedule = */5 * * * *
alert.severity = 3
alert.suppress = 1
"""
        write_conf_file(app_dir / "default" / "savedsearches.conf", content)
        validator.validate_savedsearches_conf()
        # Should find and validate the alert
        spl_errors = [e for e in validator.errors if "SPL" in e or "search" in e.lower()]
        assert len(spl_errors) == 0


class TestValidateSpl:
    def test_valid_spl(self, validator):
        content = """
[001_Test]
search = index=fw logid=0100032001 | stats count by device
"""
        result = validator.validate_spl_in_alert(content, "001_Test")
        assert result is True

    def test_missing_search_field(self, validator):
        content = """
[001_Test]
cron_schedule = */5 * * * *
"""
        result = validator.validate_spl_in_alert(content, "001_Test")
        assert result is False


class TestValidateCronSchedule:
    def test_valid_cron(self, validator):
        content = """
[001_Test]
cron_schedule = */5 * * * *
"""
        result = validator.validate_cron_schedule(content, "001_Test")
        assert result is True

    def test_invalid_cron_too_many_fields(self, validator):
        content = """
[001_Test]
cron_schedule = */5 * * * * *
"""
        result = validator.validate_cron_schedule(content, "001_Test")
        assert result is False

    def test_missing_cron(self, validator):
        content = """
[001_Test]
search = index=fw
"""
        result = validator.validate_cron_schedule(content, "001_Test")
        assert result is False


class TestValidateAll:
    def test_returns_false_when_errors_exist(self, validator, app_dir):
        # With empty app dir, many validations will fail
        result = validator.validate_all()
        assert result is False
        assert len(validator.errors) > 0

    def test_returns_true_with_valid_config(self, validator, app_dir):
        # Setup minimal valid config
        for name in [
            "fortigate_logid_notification_map.csv",
            "severity_priority.csv",
            "auto_response_actions.csv",
        ]:
            write_csv(
                app_dir / "lookups" / name,
                ["col1", "col2"],
                [{"col1": "a", "col2": "b"}],
            )

        transforms_content = """
[fortigate_logid_lookup]
filename = fortigate_logid_notification_map.csv
[severity_priority_lookup]
filename = severity_priority.csv
[auto_response_lookup]
filename = auto_response_actions.csv
[vpn_state_tracker]
filename = vpn_state_tracker.csv
[hardware_state_tracker]
filename = hardware_state_tracker.csv
"""
        write_conf_file(app_dir / "default" / "transforms.conf", transforms_content)

        props_content = """
[fortigate_syslog]
LOOKUP-fortigate_logid = fortigate_logid_notification_map
LOOKUP-severity_priority = severity_priority
LOOKUP-auto_response = auto_response_actions
"""
        write_conf_file(app_dir / "default" / "props.conf", props_content)

        searches_content = """
[001_Config_Change_Alert]
search = index=fw logid=0100032001 | stats count by device
cron_schedule = */5 * * * *
"""
        write_conf_file(app_dir / "default" / "savedsearches.conf", searches_content)

        actions_content = """
[slack]
python.version = python3
param.webhook_url = https://hooks.slack.com/test
param.channel = #test
"""
        write_conf_file(app_dir / "default" / "alert_actions.conf", actions_content)

        result = validator.validate_all()
        assert result is True
