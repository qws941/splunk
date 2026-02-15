#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for generate_test_events.py"""

import os
import random
import re
import sys
from datetime import datetime
from unittest.mock import patch

import pytest

import generate_test_events as gte


class TestGetTimestamp:
    def test_returns_iso_format(self):
        ts = gte.get_timestamp()
        # Should match YYYY-MM-DDTHH:MM:SS
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", ts)

    def test_returns_current_time(self):
        before = datetime.now().strftime("%Y-%m-%dT%H:%M")
        ts = gte.get_timestamp()
        assert ts.startswith(before)


class TestRandomIp:
    def test_returns_valid_ip_format(self):
        ip = gte.random_ip()
        parts = ip.split(".")
        assert len(parts) == 4
        for part in parts:
            assert 0 <= int(part) <= 255

    def test_first_octet_range(self):
        random.seed(42)
        for _ in range(100):
            ip = gte.random_ip()
            first = int(ip.split(".")[0])
            assert 1 <= first <= 223

    def test_last_octet_range(self):
        random.seed(42)
        for _ in range(100):
            ip = gte.random_ip()
            last = int(ip.split(".")[-1])
            assert 1 <= last <= 254

    def test_different_ips_generated(self):
        random.seed(42)
        ips = {gte.random_ip() for _ in range(50)}
        assert len(ips) > 1


class TestGenerateEvent:
    def test_known_alert_returns_events(self):
        events = gte.generate_event("001_config_change", count=1)
        assert len(events) == 1
        assert isinstance(events[0], str)

    def test_known_alert_multiple_count(self):
        events = gte.generate_event("001_config_change", count=5)
        assert len(events) == 5

    def test_unknown_alert_returns_empty(self):
        events = gte.generate_event("999_nonexistent", count=1)
        assert events == []

    def test_event_contains_syslog_fields(self):
        events = gte.generate_event("002_vpn_tunnel_down", count=1)
        assert len(events) == 1
        event = events[0]
        # Syslog events should contain logid= and type= fields
        assert "logid=" in event or "type=" in event

    def test_all_alert_types_generate(self):
        for alert_name in gte.ALERTS:
            events = gte.generate_event(alert_name, count=1)
            assert len(events) == 1, f"Alert {alert_name} failed to generate"
            assert isinstance(events[0], str)

    def test_default_count_is_one(self):
        events = gte.generate_event("001_config_change")
        assert len(events) == 1


class TestInjectToSplunk:
    def test_writes_events_to_file(self, tmp_path):
        test_dir = str(tmp_path / "test_logs")
        with patch.object(gte, "TEST_LOG_DIR", test_dir):
            events = ["event1 logid=001", "event2 logid=002"]
            result = gte.inject_to_splunk(events, source="test")
            assert result is True
            # Check file was created
            files = os.listdir(test_dir)
            assert len(files) == 1
            assert files[0].endswith(".log")
            # Check content
            with open(os.path.join(test_dir, files[0])) as f:
                content = f.read()
            assert "event1 logid=001" in content
            assert "event2 logid=002" in content

    def test_creates_directory_if_missing(self, tmp_path):
        test_dir = str(tmp_path / "new" / "nested" / "dir")
        with patch.object(gte, "TEST_LOG_DIR", test_dir):
            events = ["test event"]
            result = gte.inject_to_splunk(events, source="test")
            assert result is True
            assert os.path.isdir(test_dir)

    def test_empty_events_creates_empty_file(self, tmp_path):
        test_dir = str(tmp_path / "empty")
        with patch.object(gte, "TEST_LOG_DIR", test_dir):
            result = gte.inject_to_splunk([], source="test")
            assert result is True

    def test_handles_write_permission_error(self, tmp_path):
        """os.makedirs is outside try/except so PermissionError propagates."""
        test_dir = str(tmp_path / "no_perms")
        with patch.object(gte, "TEST_LOG_DIR", test_dir), \
             patch("os.makedirs", side_effect=PermissionError("Permission denied")):
            events = ["test event"]
            with pytest.raises(PermissionError):
                gte.inject_to_splunk(events, source="test")


class TestAlertsDict:
    def test_alerts_not_empty(self):
        assert len(gte.ALERTS) > 0

    def test_all_alerts_have_description_and_event(self):
        for name, alert in gte.ALERTS.items():
            assert "description" in alert, f"{name} missing description"
            assert "event" in alert, f"{name} missing event"
            assert callable(alert["event"]), f"{name} event not callable"

    def test_alert_descriptions_are_strings(self):
        for name, alert in gte.ALERTS.items():
            assert isinstance(alert["description"], str)
            assert len(alert["description"]) > 0


class TestModuleLevelConstants:
    def test_devices_list_exists(self):
        assert hasattr(gte, "DEVICES")
        assert len(gte.DEVICES) > 0

    def test_users_list_exists(self):
        assert hasattr(gte, "USERS")
        assert len(gte.USERS) > 0
