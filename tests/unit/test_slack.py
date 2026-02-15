#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for slack.py (slack_blockkit_alert)"""

import csv
import gzip
import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

import slack as slack_module
from slack import (
    build_block_kit_message,
    format_field_value,
    get_alert_state_path,
    get_recent_alert_thread_ts,
    get_severity_emoji,
    parse_splunk_results,
    save_alert_state,
    send_to_slack,
)


# ── parse_splunk_results ─────────────────────────────────────────────
class TestParseSplunkResults:
    def test_parses_gzipped_csv(self, tmp_path):
        csv_path = tmp_path / "results.csv.gz"
        with gzip.open(str(csv_path), "wt", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["device", "logid", "msg"])
            writer.writeheader()
            writer.writerow({"device": "FG100", "logid": "001", "msg": "test"})
            writer.writerow({"device": "FG200", "logid": "002", "msg": "test2"})
        results = parse_splunk_results(str(csv_path))
        assert len(results) == 2
        assert results[0]["device"] == "FG100"
        assert results[1]["logid"] == "002"

    def test_returns_empty_on_missing_file(self):
        results = parse_splunk_results("/nonexistent/file.csv.gz")
        assert results == []

    def test_returns_empty_on_invalid_gzip(self, tmp_path):
        bad_file = tmp_path / "bad.csv.gz"
        bad_file.write_text("not gzip data")
        results = parse_splunk_results(str(bad_file))
        assert results == []

    def test_handles_empty_csv(self, tmp_path):
        csv_path = tmp_path / "empty.csv.gz"
        with gzip.open(str(csv_path), "wt", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["device"])
            writer.writeheader()
        results = parse_splunk_results(str(csv_path))
        assert results == []


# ── get_severity_emoji ───────────────────────────────────────────────
class TestGetSeverityEmoji:
    @pytest.mark.parametrize(
        "alert_name,expected",
        [
            ("Hardware Failure", "\U0001f534"),  # red circle
            ("VPN Tunnel Down", "\U0001f534"),
            ("HA State Change", "\U0001f7e0"),  # orange circle
            ("Interface Down", "\U0001f7e0"),
            ("Config Change", "\U0001f7e1"),  # yellow circle
            ("CPU High Usage", "\U0001f7e1"),
            ("Admin Login", "\U0001f535"),  # blue circle
            ("Unknown Alert", "\U0001f535"),
        ],
    )
    def test_severity_mapping(self, alert_name, expected):
        assert get_severity_emoji(alert_name) == expected


# ── format_field_value ───────────────────────────────────────────────
class TestFormatFieldValue:
    def test_basic_formatting(self):
        result = format_field_value("source_ip", "10.0.0.1")
        assert "Source Ip" in result
        assert "10.0.0.1" in result

    def test_emoji_prefix_for_known_key(self):
        result = format_field_value("device", "FG100")
        assert "\U0001f5a5\ufe0f" in result  # computer emoji

    def test_no_emoji_for_unknown_key(self):
        result = format_field_value("random_field", "value")
        assert result.startswith(" *Random Field:*") or result.startswith("*Random Field:*")

    def test_truncates_long_values(self):
        long_val = "x" * 200
        result = format_field_value("field", long_val)
        assert "..." in result
        # The value portion should be truncated to 100 chars
        assert len(long_val) > 100  # original is long

    def test_underscore_to_title_case(self):
        result = format_field_value("vpn_name", "tunnel1")
        assert "Vpn Name" in result


# ── build_block_kit_message ──────────────────────────────────────────
class TestBuildBlockKitMessage:
    def test_returns_blocks_list(self):
        blocks = build_block_kit_message(
            "Test Alert", "test_search", [{"device": "FG100"}]
        )
        assert isinstance(blocks, list)
        assert len(blocks) > 0

    def test_header_block_present(self):
        blocks = build_block_kit_message(
            "Test Alert", "test_search", [{"device": "FG100"}]
        )
        header = blocks[0]
        assert header["type"] == "header"
        assert "Test Alert" in header["text"]["text"]

    def test_actions_block_with_ack_and_snooze(self):
        blocks = build_block_kit_message(
            "Test Alert", "test_search", [{"device": "FG100"}]
        )
        actions = [b for b in blocks if b["type"] == "actions"]
        assert len(actions) == 1
        action_ids = [e.get("action_id") for e in actions[0]["elements"]]
        assert "ack_alert" in action_ids
        assert "snooze_alert_1h" in action_ids

    def test_view_link_adds_button(self):
        blocks = build_block_kit_message(
            "Test Alert",
            "test_search",
            [{"device": "FG100"}],
            view_link="https://splunk.example.com/search",
        )
        actions = [b for b in blocks if b["type"] == "actions"]
        urls = [e.get("url") for e in actions[0]["elements"] if e.get("url")]
        assert "https://splunk.example.com/search" in urls

    def test_max_5_results_shown(self):
        results = [{"device": f"FG{i}"} for i in range(10)]
        blocks = build_block_kit_message("Test", "search", results)
        # Should have context block about showing 5 of 10
        context_blocks = [b for b in blocks if b["type"] == "context"]
        assert any("5 of 10" in str(b) for b in context_blocks)

    def test_custom_alert_id(self):
        blocks = build_block_kit_message(
            "Test", "search", [{"device": "FG100"}], alert_id="custom_123"
        )
        actions = [b for b in blocks if b["type"] == "actions"]
        values = [e.get("value") for e in actions[0]["elements"]]
        assert "custom_123" in values

    def test_empty_results(self):
        blocks = build_block_kit_message("Test", "search", [])
        assert isinstance(blocks, list)

    def test_fields_limited_to_10(self):
        # Result with many fields
        result = {f"field_{i}": f"value_{i}" for i in range(20)}
        blocks = build_block_kit_message("Test", "search", [result])
        section_blocks = [b for b in blocks if b["type"] == "section" and "fields" in b]
        for sb in section_blocks:
            if sb.get("fields"):
                assert len(sb["fields"]) <= 10


# ── get_alert_state_path ─────────────────────────────────────────────
class TestGetAlertStatePath:
    def test_returns_path_with_lookups_dir(self):
        path = get_alert_state_path()
        assert path.endswith("alert_state.csv")
        assert "lookups" in path


# ── get_recent_alert_thread_ts ───────────────────────────────────────
class TestGetRecentAlertThreadTs:
    def test_returns_none_when_no_state_file(self, tmp_path):
        with patch.object(slack_module, "get_alert_state_path", return_value=str(tmp_path / "nope.csv")):
            result = get_recent_alert_thread_ts("test", "#channel")
        assert result is None

    def test_returns_thread_ts_for_matching_open_alert(self, tmp_path):
        state_file = tmp_path / "alert_state.csv"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(state_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "alert_id", "search_name", "message_ts",
                    "channel", "status", "created_at", "updated_at", "acked_by",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "alert_id": "test_123",
                    "search_name": "test_search",
                    "message_ts": "1234567890.123456",
                    "channel": "#alerts",
                    "status": "open",
                    "created_at": now,
                    "updated_at": now,
                    "acked_by": "",
                }
            )
        with patch.object(slack_module, "get_alert_state_path", return_value=str(state_file)):
            result = get_recent_alert_thread_ts("test_search", "#alerts")
        assert result == "1234567890.123456"

    def test_returns_none_for_old_alert(self, tmp_path):
        state_file = tmp_path / "alert_state.csv"
        old_time = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        with open(state_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "alert_id", "search_name", "message_ts",
                    "channel", "status", "created_at", "updated_at", "acked_by",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "alert_id": "test_123",
                    "search_name": "test_search",
                    "message_ts": "1234567890.123456",
                    "channel": "#alerts",
                    "status": "open",
                    "created_at": old_time,
                    "updated_at": old_time,
                    "acked_by": "",
                }
            )
        with patch.object(slack_module, "get_alert_state_path", return_value=str(state_file)):
            result = get_recent_alert_thread_ts("test_search", "#alerts")
        assert result is None

    def test_returns_none_for_acked_alert(self, tmp_path):
        state_file = tmp_path / "alert_state.csv"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(state_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "alert_id", "search_name", "message_ts",
                    "channel", "status", "created_at", "updated_at", "acked_by",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "alert_id": "test_123",
                    "search_name": "test_search",
                    "message_ts": "1234567890.123456",
                    "channel": "#alerts",
                    "status": "acknowledged",
                    "created_at": now,
                    "updated_at": now,
                    "acked_by": "user1",
                }
            )
        with patch.object(slack_module, "get_alert_state_path", return_value=str(state_file)):
            result = get_recent_alert_thread_ts("test_search", "#alerts")
        assert result is None


# ── save_alert_state ─────────────────────────────────────────────────
class TestSaveAlertState:
    def test_creates_new_file_if_not_exists(self, tmp_path):
        state_file = tmp_path / "lookups" / "alert_state.csv"
        with patch.object(slack_module, "get_alert_state_path", return_value=str(state_file)):
            save_alert_state("test_search", "12345.6789", "#alerts")
        assert state_file.exists()
        with open(state_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["search_name"] == "test_search"
        assert rows[0]["message_ts"] == "12345.6789"
        assert rows[0]["status"] == "open"

    def test_appends_to_existing_file(self, tmp_path):
        state_file = tmp_path / "lookups" / "alert_state.csv"
        state_file.parent.mkdir(parents=True)
        # Create initial file
        with open(state_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "alert_id", "search_name", "message_ts",
                    "channel", "status", "created_at", "updated_at", "acked_by",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "alert_id": "existing",
                    "search_name": "old_search",
                    "message_ts": "111.222",
                    "channel": "#old",
                    "status": "open",
                    "created_at": "2024-01-01 00:00:00",
                    "updated_at": "2024-01-01 00:00:00",
                    "acked_by": "",
                }
            )
        with patch.object(slack_module, "get_alert_state_path", return_value=str(state_file)):
            save_alert_state("new_search", "333.444", "#new")
        with open(state_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2


# ── send_to_slack ────────────────────────────────────────────────────
class TestSendToSlack:
    def test_bot_token_sends_to_api(self):
        mock_resp = Mock()
        mock_resp.json.return_value = {"ok": True, "ts": "12345.6789"}
        mock_resp.raise_for_status = Mock()
        with patch("slack.requests.post", return_value=mock_resp) as mock_post:
            success, ts = send_to_slack(
                None, "xoxb-test-token", "#channel", [{"type": "section"}]
            )
        assert success is True
        assert ts == "12345.6789"
        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        assert "chat.postMessage" in call_url

    def test_webhook_sends_to_hooks_url(self):
        mock_resp = Mock()
        mock_resp.text = "ok"
        mock_resp.raise_for_status = Mock()
        with patch("slack.requests.post", return_value=mock_resp) as mock_post:
            success, ts = send_to_slack(
                "https://hooks.slack.com/services/T/B/X",
                None,
                "#channel",
                [{"type": "section"}],
            )
        assert success is True
        assert ts is None
        mock_post.assert_called_once()

    def test_no_credentials_returns_false(self):
        success, ts = send_to_slack(None, None, "#channel", [{"type": "section"}])
        assert success is False
        assert ts is None

    def test_invalid_bot_token_returns_false(self):
        success, ts = send_to_slack(None, "not-a-bot-token", "#channel", [])
        assert success is False

    def test_invalid_webhook_url_returns_false(self):
        success, ts = send_to_slack(
            "https://not-slack.com/hook", None, "#channel", []
        )
        assert success is False

    def test_api_error_returns_false(self):
        mock_resp = Mock()
        mock_resp.json.return_value = {"ok": False, "error": "invalid_auth"}
        mock_resp.raise_for_status = Mock()
        with patch("slack.requests.post", return_value=mock_resp):
            success, ts = send_to_slack(
                None, "xoxb-test-token", "#channel", []
            )
        assert success is False

    def test_timeout_returns_false(self):
        import requests

        with patch("slack.requests.post", side_effect=requests.exceptions.Timeout):
            success, ts = send_to_slack(
                None, "xoxb-test-token", "#channel", []
            )
        assert success is False

    def test_request_exception_returns_false(self):
        import requests

        with patch(
            "slack.requests.post",
            side_effect=requests.exceptions.ConnectionError("fail"),
        ):
            success, ts = send_to_slack(
                None, "xoxb-test-token", "#channel", []
            )
        assert success is False

    def test_proxy_passed_through(self):
        mock_resp = Mock()
        mock_resp.json.return_value = {"ok": True, "ts": "1"}
        mock_resp.raise_for_status = Mock()
        proxies = {"http": "http://proxy:8080"}
        with patch("slack.requests.post", return_value=mock_resp) as mock_post:
            send_to_slack(
                None, "xoxb-test-token", "#channel", [], proxies=proxies
            )
        assert mock_post.call_args[1]["proxies"] == proxies
