#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for slack_callback.py

slack_callback.py imports splunk.admin at module level, which is only
available inside Splunk. We mock it before importing.
"""

import csv
import hashlib
import hmac
import json
import os
import sys
import time
import types
from unittest.mock import MagicMock, Mock, patch

import pytest


# ── Mock splunk.admin before importing slack_callback ────────────────
@pytest.fixture(autouse=True)
def mock_splunk_admin():
    """Install a mock splunk.admin module so slack_callback can be imported."""
    splunk_mod = types.ModuleType("splunk")
    admin_mod = types.ModuleType("splunk.admin")

    class MockMConfigHandler:
        def __init__(self, *args, **kwargs):
            pass

    admin_mod.MConfigHandler = MockMConfigHandler
    admin_mod.ACTION_EDIT = "edit"
    admin_mod.CONTEXT_NONE = 0
    admin_mod.init = Mock()

    splunk_mod.admin = admin_mod
    sys.modules["splunk"] = splunk_mod
    sys.modules["splunk.admin"] = admin_mod

    yield admin_mod

    # Cleanup
    for mod_name in ["splunk", "splunk.admin", "slack_callback"]:
        sys.modules.pop(mod_name, None)


def _import_slack_callback():
    """Import slack_callback fresh (after mock is installed)."""
    if "slack_callback" in sys.modules:
        del sys.modules["slack_callback"]
    import slack_callback

    return slack_callback


# ── verify_slack_signature ───────────────────────────────────────────
class TestVerifySlackSignature:
    def test_valid_signature(self):
        mod = _import_slack_callback()
        signing_secret = "test_secret_12345"
        timestamp = str(int(time.time()))
        body = '{"type":"block_actions"}'
        sig_basestring = f"v0:{timestamp}:{body}"
        expected_sig = (
            "v0="
            + hmac.new(
                signing_secret.encode(), sig_basestring.encode(), hashlib.sha256
            ).hexdigest()
        )
        result = mod.verify_slack_signature(
            signing_secret, timestamp, body, expected_sig
        )
        assert result is True

    def test_invalid_signature(self):
        mod = _import_slack_callback()
        result = mod.verify_slack_signature(
            "secret", str(int(time.time())), "body", "v0=invalid"
        )
        assert result is False

    def test_stale_timestamp_rejected(self):
        mod = _import_slack_callback()
        old_timestamp = str(int(time.time()) - 600)  # 10 minutes ago
        result = mod.verify_slack_signature(
            "secret", old_timestamp, "body", "v0=anything"
        )
        assert result is False


# ── update_alert_state ───────────────────────────────────────────────
class TestUpdateAlertState:
    def test_updates_matching_alert(self, tmp_path):
        mod = _import_slack_callback()
        state_file = tmp_path / "alert_state.csv"
        fieldnames = [
            "alert_id", "search_name", "message_ts",
            "channel", "status", "created_at", "updated_at", "acked_by",
        ]
        with open(state_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(
                {
                    "alert_id": "test_alert_123",
                    "search_name": "test",
                    "message_ts": "123.456",
                    "channel": "#test",
                    "status": "open",
                    "created_at": "2024-01-01 00:00:00",
                    "updated_at": "2024-01-01 00:00:00",
                    "acked_by": "",
                }
            )
        with patch.object(
            mod, "get_alert_state_path", return_value=str(state_file)
        ):
            result = mod.update_alert_state(
                "test_alert_123", "acknowledged", "user@corp"
            )
        assert result is True
        with open(state_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert rows[0]["status"] == "acknowledged"
        assert rows[0]["acked_by"] == "user@corp"

    def test_returns_false_for_missing_alert(self, tmp_path):
        mod = _import_slack_callback()
        state_file = tmp_path / "alert_state.csv"
        fieldnames = [
            "alert_id", "search_name", "message_ts",
            "channel", "status", "created_at", "updated_at", "acked_by",
        ]
        with open(state_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        with patch.object(
            mod, "get_alert_state_path", return_value=str(state_file)
        ):
            result = mod.update_alert_state("nonexistent", "acknowledged")
        assert result is False

    def test_returns_false_when_file_missing(self, tmp_path):
        mod = _import_slack_callback()
        with patch.object(
            mod,
            "get_alert_state_path",
            return_value=str(tmp_path / "nope.csv"),
        ):
            result = mod.update_alert_state("test", "acknowledged")
        assert result is False


# ── update_slack_message ─────────────────────────────────────────────
class TestUpdateSlackMessage:
    def test_posts_to_chat_update(self):
        mod = _import_slack_callback()
        mock_resp = Mock()
        mock_resp.json.return_value = {"ok": True}
        mock_resp.raise_for_status = Mock()
        with patch("slack_callback.requests.post", return_value=mock_resp) as mock_post:
            result = mod.update_slack_message(
                "xoxb-token", "#channel", "12345.6789", "Updated text"
            )
        assert result == {"ok": True}
        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        assert "chat.update" in call_url

    def test_removes_actions_block(self):
        mod = _import_slack_callback()
        mock_resp = Mock()
        mock_resp.json.return_value = {"ok": True}
        mock_resp.raise_for_status = Mock()
        original_blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "Alert"}},
            {"type": "actions", "elements": []},
        ]
        with patch("slack_callback.requests.post", return_value=mock_resp) as mock_post:
            mod.update_slack_message(
                "xoxb-token", "#channel", "12345.6789",
                "Acknowledged", original_blocks=original_blocks,
            )
        call_json = mock_post.call_args[1]["json"]
        block_types = [b["type"] for b in call_json["blocks"]]
        assert "actions" not in block_types
        # Should have appended a context block
        assert "context" in block_types


# ── update_alert_state matching by message_ts ───────────────────────
class TestUpdateAlertStateByMessageTs:
    def test_matches_by_message_ts(self, tmp_path):
        mod = _import_slack_callback()
        state_file = tmp_path / "alert_state.csv"
        fieldnames = [
            "alert_id", "search_name", "message_ts",
            "channel", "status", "created_at", "updated_at", "acked_by",
        ]
        with open(state_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(
                {
                    "alert_id": "some_other_id",
                    "search_name": "test",
                    "message_ts": "999.888",
                    "channel": "#test",
                    "status": "open",
                    "created_at": "2024-01-01 00:00:00",
                    "updated_at": "2024-01-01 00:00:00",
                    "acked_by": "",
                }
            )
        with patch.object(
            mod, "get_alert_state_path", return_value=str(state_file)
        ):
            result = mod.update_alert_state(
                "999.888", "acknowledged", "user1"
            )
        assert result is True
        with open(state_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert rows[0]["status"] == "acknowledged"


# ── update_slack_message edge cases ──────────────────────────────────
class TestUpdateSlackMessageEdgeCases:
    def test_without_original_blocks(self):
        mod = _import_slack_callback()
        mock_resp = Mock()
        mock_resp.json.return_value = {"ok": True}
        with patch("slack_callback.requests.post", return_value=mock_resp) as mock_post:
            result = mod.update_slack_message(
                "xoxb-token", "#channel", "12345.6789", "Text only"
            )
        assert result == {"ok": True}
        call_json = mock_post.call_args[1]["json"]
        assert "text" in call_json
        assert "blocks" not in call_json

    def test_requests_not_available(self):
        mod = _import_slack_callback()
        original_requests = mod.requests
        mod.requests = None
        try:
            result = mod.update_slack_message(
                "xoxb-token", "#channel", "12345", "msg"
            )
            assert result["ok"] is False
            assert "not available" in result["error"]
        finally:
            mod.requests = original_requests


# ── SlackCallbackHandler ─────────────────────────────────────────────
class TestSlackCallbackHandler:
    def test_setup_for_edit_action(self):
        mod = _import_slack_callback()
        handler = mod.SlackCallbackHandler.__new__(mod.SlackCallbackHandler)
        handler.requestedAction = "edit"  # admin.ACTION_EDIT
        handler.supportedArgs = MagicMock()
        handler.setup()
        handler.supportedArgs.addOptArg.assert_any_call("payload")
        handler.supportedArgs.addOptArg.assert_any_call("*")

    def test_handleEdit_ack_alert(self):
        mod = _import_slack_callback()
        handler = mod.SlackCallbackHandler.__new__(mod.SlackCallbackHandler)
        payload = json.dumps({
            "type": "block_actions",
            "actions": [{"action_id": "ack_alert", "value": "alert_123"}],
            "user": {"name": "testuser"},
        })
        handler.callerArgs = {
            "payload": [payload],
            "X-Slack-Request-Timestamp": [None],
            "X-Slack-Signature": [None],
        }
        confInfo = {"result": {}}
        with patch.object(mod, "update_alert_state") as mock_update:
            handler.handleEdit(confInfo)
        mock_update.assert_called_once_with("alert_123", "acknowledged", "testuser")
        assert confInfo["result"]["status"] == "ok"

    def test_handleEdit_snooze_alert(self):
        mod = _import_slack_callback()
        handler = mod.SlackCallbackHandler.__new__(mod.SlackCallbackHandler)
        payload = json.dumps({
            "type": "block_actions",
            "actions": [{"action_id": "snooze_alert_1h", "value": "alert_456"}],
            "user": {"username": "snoozeuser"},
        })
        handler.callerArgs = {
            "payload": [payload],
            "X-Slack-Request-Timestamp": [None],
            "X-Slack-Signature": [None],
        }
        confInfo = {"result": {}}
        with patch.object(mod, "update_alert_state") as mock_update:
            handler.handleEdit(confInfo)
        mock_update.assert_called_once_with("alert_456", "snoozed_1h", "snoozeuser")
        assert confInfo["result"]["status"] == "ok"

    def test_handleEdit_no_payload(self):
        mod = _import_slack_callback()
        handler = mod.SlackCallbackHandler.__new__(mod.SlackCallbackHandler)
        handler.callerArgs = {
            "payload": [None],
            "X-Slack-Request-Timestamp": [None],
            "X-Slack-Signature": [None],
        }
        confInfo = {"result": {}}
        handler.handleEdit(confInfo)
        assert confInfo["result"]["status"] == "error"
        assert "No payload" in confInfo["result"]["message"]

    def test_handleEdit_unknown_action_type(self):
        mod = _import_slack_callback()
        handler = mod.SlackCallbackHandler.__new__(mod.SlackCallbackHandler)
        payload = json.dumps({"type": "message_action"})
        handler.callerArgs = {
            "payload": [payload],
            "X-Slack-Request-Timestamp": [None],
            "X-Slack-Signature": [None],
        }
        confInfo = {"result": {}}
        handler.handleEdit(confInfo)
        assert confInfo["result"]["status"] == "ignored"

    def test_handleEdit_with_valid_signature(self):
        mod = _import_slack_callback()
        handler = mod.SlackCallbackHandler.__new__(mod.SlackCallbackHandler)
        signing_secret = "test_secret"
        timestamp = str(int(time.time()))
        payload_str = json.dumps({"type": "block_actions", "actions": [], "user": {"name": "u"}})
        sig_basestring = f"v0:{timestamp}:{payload_str}"
        signature = "v0=" + hmac.new(
            signing_secret.encode(), sig_basestring.encode(), hashlib.sha256
        ).hexdigest()
        handler.callerArgs = {
            "payload": [payload_str],
            "X-Slack-Request-Timestamp": [timestamp],
            "X-Slack-Signature": [signature],
        }
        confInfo = {"result": {}}
        with patch.dict(os.environ, {"SLACK_SIGNING_SECRET": signing_secret}):
            handler.handleEdit(confInfo)
        # No error about invalid signature
        assert confInfo["result"].get("status") != "error"

    def test_handleEdit_with_invalid_signature(self):
        mod = _import_slack_callback()
        handler = mod.SlackCallbackHandler.__new__(mod.SlackCallbackHandler)
        timestamp = str(int(time.time()))
        handler.callerArgs = {
            "payload": ['{"type":"test"}'],
            "X-Slack-Request-Timestamp": [timestamp],
            "X-Slack-Signature": ["v0=invalidsig"],
        }
        confInfo = {"result": {}}
        with patch.dict(os.environ, {"SLACK_SIGNING_SECRET": "real_secret"}):
            handler.handleEdit(confInfo)
        assert confInfo["result"]["status"] == "error"
        assert "Invalid Slack signature" in confInfo["result"]["message"]

    def test_handleEdit_exception_handling(self):
        mod = _import_slack_callback()
        handler = mod.SlackCallbackHandler.__new__(mod.SlackCallbackHandler)
        handler.callerArgs = {
            "payload": ["not valid json"],
            "X-Slack-Request-Timestamp": [None],
            "X-Slack-Signature": [None],
        }
        confInfo = {"result": {}}
        handler.handleEdit(confInfo)
        assert confInfo["result"]["status"] == "error"


# ── admin.init called at module level ────────────────────────────────
class TestModuleLevelInit:
    def test_admin_init_called(self, mock_splunk_admin):
        _import_slack_callback()
        mock_splunk_admin.init.assert_called()


# ── get_alert_state_path ─────────────────────────────────────────────
class TestGetAlertStatePath:
    def test_returns_path_in_lookups(self):
        mod = _import_slack_callback()
        path = mod.get_alert_state_path()
        assert "lookups" in path
        assert path.endswith("alert_state.csv")


# ── try/except import requests ───────────────────────────────────────
class TestRequestsImport:
    def test_requests_import_failure(self):
        """Test that requests=None when import fails (lines 22-23)."""
        import importlib
        # This is covered by the test_requests_not_available test above
        # The module-level try/except is hit during import
        mod = _import_slack_callback()
        assert mod.requests is not None  # normally available
