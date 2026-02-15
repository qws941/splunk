#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for slack_callback.py

slack_callback.py imports splunk.admin at module level, which is only
available inside Splunk. We mock it before importing.
"""

import csv
import hashlib
import hmac
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


# ── get_alert_state_path ─────────────────────────────────────────────
class TestGetAlertStatePath:
    def test_returns_path_in_lookups(self):
        mod = _import_slack_callback()
        path = mod.get_alert_state_path()
        assert "lookups" in path
        assert path.endswith("alert_state.csv")
