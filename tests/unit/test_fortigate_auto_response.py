#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for fortigate_auto_response.py

This module has module-level side effects:
- logging.basicConfig writes to /opt/splunk/var/log/splunk/auto_response.log
- Module-level env vars: FORTIMANAGER_URL, FORTIMANAGER_TOKEN, SLACK_WEBHOOK_URL

We must mock the logging.FileHandler before importing.
"""

import json
import logging
import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests


@pytest.fixture(autouse=True)
def mock_logging_and_env(monkeypatch, tmp_path):
    """Patch FileHandler to avoid /opt/splunk path and set env vars."""
    log_file = str(tmp_path / "auto_response.log")
    monkeypatch.setenv("FORTIMANAGER_URL", "https://fmg.test.local")
    monkeypatch.setenv("FORTIMANAGER_TOKEN", "test-token-123")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/T/B/X")

    # Patch FileHandler before import
    original_file_handler = logging.FileHandler
    with patch(
        "logging.FileHandler",
        side_effect=lambda f, *a, **kw: original_file_handler(log_file, *a, **kw),
    ):
        # Force re-import to pick up new env vars and patched handler
        for mod_name in list(sys.modules):
            if "fortigate_auto_response" in mod_name:
                del sys.modules[mod_name]
        yield

    # Cleanup
    sys.modules.pop("fortigate_auto_response", None)


def _import_module():
    """Import fortigate_auto_response fresh."""
    if "fortigate_auto_response" in sys.modules:
        del sys.modules["fortigate_auto_response"]
    import fortigate_auto_response

    return fortigate_auto_response


# ── FortiManagerAPI ──────────────────────────────────────────────────
class TestFortiManagerAPI:
    def test_init_sets_headers(self):
        mod = _import_module()
        api = mod.FortiManagerAPI("https://fmg.local", "mytoken")
        assert api.url == "https://fmg.local"
        assert api.session.headers["Authorization"] == "Bearer mytoken"

    def test_url_trailing_slash_stripped(self):
        mod = _import_module()
        api = mod.FortiManagerAPI("https://fmg.local/", "token")
        assert api.url == "https://fmg.local"

    def test_add_address_blacklist_success(self):
        mod = _import_module()
        api = mod.FortiManagerAPI("https://fmg.local", "token")
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        with patch.object(api.session, "post", return_value=mock_resp):
            result = api.add_address_blacklist("1.2.3.4", "test block")
        assert result["status"] == "success"
        assert result["ip"] == "1.2.3.4"

    def test_add_address_blacklist_failure(self):
        mod = _import_module()
        api = mod.FortiManagerAPI("https://fmg.local", "token")
        with patch.object(
            api.session, "post", side_effect=requests.exceptions.ConnectionError("fail")
        ):
            result = api.add_address_blacklist("1.2.3.4", "test")
        assert result["status"] == "error"

    def test_apply_bandwidth_limit_success(self):
        mod = _import_module()
        api = mod.FortiManagerAPI("https://fmg.local", "token")
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        with patch.object(api.session, "post", return_value=mock_resp):
            result = api.apply_bandwidth_limit("10.0.0.1", 10)
        assert result["status"] == "success"
        assert result["limit"] == 10

    def test_disable_admin_account_success(self):
        mod = _import_module()
        api = mod.FortiManagerAPI("https://fmg.local", "token")
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        with patch.object(api.session, "put", return_value=mock_resp):
            result = api.disable_admin_account("rogue_admin")
        assert result["status"] == "success"
        assert result["user"] == "rogue_admin"

    def test_disable_admin_account_failure(self):
        mod = _import_module()
        api = mod.FortiManagerAPI("https://fmg.local", "token")
        with patch.object(
            api.session, "put", side_effect=Exception("auth failed")
        ):
            result = api.disable_admin_account("admin")
        assert result["status"] == "error"


# ── SlackNotifier ───────────────────────────────────────────────────
class TestSlackNotifier:
    def test_send_notification_success(self):
        mod = _import_module()
        notifier = mod.SlackNotifier("https://hooks.slack.com/test")
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        with patch("fortigate_auto_response.requests.post", return_value=mock_resp):
            result = notifier.send_notification("test_alert", "blocked", {"ip": "1.2.3.4"})
        assert result is True

    def test_send_notification_failure(self):
        mod = _import_module()
        notifier = mod.SlackNotifier("https://hooks.slack.com/test")
        with patch(
            "fortigate_auto_response.requests.post",
            side_effect=requests.exceptions.Timeout,
        ):
            result = notifier.send_notification("test", "action", {})
        assert result is False


# ── AutoResponseEngine ─────────────────────────────────────────────
class TestAutoResponseEngine:
    def test_brute_force_blocks_ip(self):
        mod = _import_module()
        engine = mod.AutoResponseEngine()
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        with patch.object(engine.fmg_api.session, "post", return_value=mock_resp):
            with patch.object(engine.slack, "send_notification", return_value=True):
                result = engine.execute_action(
                    {
                        "search_name": "013_SSL_VPN_Brute_Force",
                        "source_ip": "45.33.32.1",
                        "fail_count": 15,
                    }
                )
        assert result["status"] == "success"

    def test_brute_force_monitors_low_count(self):
        mod = _import_module()
        engine = mod.AutoResponseEngine()
        with patch.object(engine.slack, "send_notification", return_value=True):
            result = engine.execute_action(
                {
                    "search_name": "013_SSL_VPN_Brute_Force",
                    "source_ip": "10.0.0.1",
                    "fail_count": 3,
                }
            )
        assert result["status"] == "monitoring"

    def test_traffic_spike_applies_limit(self):
        mod = _import_module()
        engine = mod.AutoResponseEngine()
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        with patch.object(engine.fmg_api.session, "post", return_value=mock_resp):
            with patch.object(engine.slack, "send_notification", return_value=True):
                result = engine.execute_action(
                    {
                        "search_name": "015_Abnormal_Traffic_Spike",
                        "source_ip": "10.0.0.1",
                        "spike_multiplier": 10,
                    }
                )
        assert result["status"] == "success"

    def test_admin_login_disables_account(self):
        mod = _import_module()
        engine = mod.AutoResponseEngine()
        mock_resp = Mock()
        mock_resp.raise_for_status = Mock()
        with patch.object(engine.fmg_api.session, "put", return_value=mock_resp):
            with patch.object(engine.slack, "send_notification", return_value=True):
                result = engine.execute_action(
                    {
                        "search_name": "011_Admin_Login_Failed",
                        "source_ip": "10.0.0.1",
                        "fail_count": 5,
                        "user": "hacker",
                    }
                )
        assert result["status"] == "success"

    def test_unknown_alert_notification_only(self):
        mod = _import_module()
        engine = mod.AutoResponseEngine()
        with patch.object(engine.slack, "send_notification", return_value=True):
            result = engine.execute_action(
                {"search_name": "999_Unknown_Alert"}
            )
        assert result["status"] == "notified"
        assert result["action"] == "none"

    def test_action_logged(self):
        mod = _import_module()
        engine = mod.AutoResponseEngine()
        with patch.object(engine.slack, "send_notification", return_value=True):
            engine.execute_action({"search_name": "Unknown"})
        assert len(engine.action_log) == 1
        assert "timestamp" in engine.action_log[0]
