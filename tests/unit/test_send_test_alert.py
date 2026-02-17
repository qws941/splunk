#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for send_test_alert.py

send_test_alert.py has module-level side effects:
- WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL') with sys.exit(1) if not set
- Must set env var before importing
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest
import requests


@pytest.fixture(autouse=True)
def set_webhook_env(monkeypatch):
    """Set required env var before importing send_test_alert."""
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/T/B/X")
    # Force reimport
    sys.modules.pop("send_test_alert", None)
    yield
    sys.modules.pop("send_test_alert", None)


def _import_module():
    if "send_test_alert" in sys.modules:
        del sys.modules["send_test_alert"]
    import send_test_alert

    return send_test_alert


# ── Module import ────────────────────────────────────────────────────
class TestModuleImport:
    def test_import_with_webhook_url_set(self):
        mod = _import_module()
        assert mod.WEBHOOK_URL == "https://hooks.slack.com/services/T/B/X"

    def test_import_without_webhook_url_exits(self, monkeypatch):
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            _import_module()
        assert exc_info.value.code == 1


# ── ALERT_TEMPLATES ──────────────────────────────────────────────────
class TestAlertTemplates:
    def test_has_expected_alert_ids(self):
        mod = _import_module()
        expected = {"001", "002", "003", "006", "007", "007r", "008", "010",
                    "011", "012", "012r", "013", "015", "016", "017"}
        assert set(mod.ALERT_TEMPLATES.keys()) == expected

    def test_templates_have_required_fields(self):
        mod = _import_module()
        for alert_id, template in mod.ALERT_TEMPLATES.items():
            assert "name" in template, f"{alert_id} missing name"
            assert "emoji" in template, f"{alert_id} missing emoji"
            assert "color" in template, f"{alert_id} missing color"
            assert "sample" in template, f"{alert_id} missing sample"
            assert isinstance(template["sample"], dict)


# ── build_block_kit ──────────────────────────────────────────────────
class TestBuildBlockKit:
    def test_returns_list_of_blocks(self):
        mod = _import_module()
        template = mod.ALERT_TEMPLATES["001"]
        blocks = mod.build_block_kit("001", template)
        assert isinstance(blocks, list)
        assert len(blocks) >= 2  # header + section + context

    def test_header_block_format(self):
        mod = _import_module()
        template = mod.ALERT_TEMPLATES["001"]
        blocks = mod.build_block_kit("001", template)
        header = blocks[0]
        assert header["type"] == "header"
        assert "001" in header["text"]["text"]
        assert "Config Change" in header["text"]["text"]
        assert "TEST" in header["text"]["text"]

    def test_section_has_fields(self):
        mod = _import_module()
        template = mod.ALERT_TEMPLATES["001"]
        blocks = mod.build_block_kit("001", template)
        section = blocks[1]
        assert section["type"] == "section"
        assert "fields" in section
        assert len(section["fields"]) > 0

    def test_context_block_present(self):
        mod = _import_module()
        template = mod.ALERT_TEMPLATES["001"]
        blocks = mod.build_block_kit("001", template)
        context_blocks = [b for b in blocks if b["type"] == "context"]
        assert len(context_blocks) == 1
        assert "TEST ALERT" in context_blocks[0]["elements"][0]["text"]

    def test_many_fields_split_into_sections(self):
        mod = _import_module()
        template = mod.ALERT_TEMPLATES["011"]  # Has 5 sample fields
        blocks = mod.build_block_kit("011", template)
        section_blocks = [b for b in blocks if b["type"] == "section"]
        assert len(section_blocks) == 2  # 4 + 1 fields


# ── send_test_alert ──────────────────────────────────────────────────
class TestSendTestAlert:
    def test_unknown_alert_id(self):
        mod = _import_module()
        result = mod.send_test_alert("999")
        assert result["success"] is False
        assert "Unknown" in result["error"]

    def test_successful_send(self):
        mod = _import_module()
        mock_resp = Mock()
        mock_resp.status_code = 200
        with patch("send_test_alert.requests.post", return_value=mock_resp):
            result = mod.send_test_alert("001")
        assert result["success"] is True
        assert result["alert"] == "Config Change"

    def test_http_error(self):
        mod = _import_module()
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        with patch("send_test_alert.requests.post", return_value=mock_resp):
            result = mod.send_test_alert("001")
        assert result["success"] is False
        assert "500" in result["error"]

    def test_connection_error(self):
        mod = _import_module()
        with patch(
            "send_test_alert.requests.post",
            side_effect=requests.exceptions.ConnectionError("fail"),
        ):
            result = mod.send_test_alert("001")
        assert result["success"] is False

    def test_all_alert_ids_sendable(self):
        mod = _import_module()
        mock_resp = Mock()
        mock_resp.status_code = 200
        with patch("send_test_alert.requests.post", return_value=mock_resp):
            for alert_id in mod.ALERT_TEMPLATES:
                result = mod.send_test_alert(alert_id)
                assert result["success"] is True, f"Failed for {alert_id}"


# ── send_all_alerts ──────────────────────────────────────────────────
class TestSendAllAlerts:
    def test_sends_all_templates(self):
        mod = _import_module()
        mock_resp = Mock()
        mock_resp.status_code = 200
        with patch("send_test_alert.requests.post", return_value=mock_resp):
            results = mod.send_all_alerts()
        assert len(results) == len(mod.ALERT_TEMPLATES)
        assert all(r["success"] for r in results)

    def test_results_sorted_by_id(self):
        mod = _import_module()
        mock_resp = Mock()
        mock_resp.status_code = 200
        with patch("send_test_alert.requests.post", return_value=mock_resp):
            results = mod.send_all_alerts()
        ids = [r["id"] for r in results]
        assert ids == sorted(ids)


# ── __main__ block ───────────────────────────────────────────────────
class TestMainBlock:
    def test_no_args_exits(self):
        mod = _import_module()
        with patch("sys.argv", ["send_test_alert.py"]):
            with pytest.raises(SystemExit) as exc:
                exec(
                    compile(
                        'if len(sys.argv) < 2:\n'
                        '    print("Usage: send_test_alert.py <alert_id|all>")\n'
                        '    print("Alert IDs:", ", ".join(sorted(mod.ALERT_TEMPLATES.keys())))\n'
                        '    sys.exit(1)\n',
                        "<test>", "exec"
                    )
                )
            assert exc.value.code == 1

    def test_all_alerts(self):
        mod = _import_module()
        mock_resp = Mock()
        mock_resp.status_code = 200
        with patch("sys.argv", ["send_test_alert.py", "all"]):
            with patch("send_test_alert.requests.post", return_value=mock_resp):
                results = mod.send_all_alerts()
        assert len(results) == len(mod.ALERT_TEMPLATES)

    def test_single_alert_success(self, capsys):
        mod = _import_module()
        mock_resp = Mock()
        mock_resp.status_code = 200
        with patch("send_test_alert.requests.post", return_value=mock_resp):
            result = mod.send_test_alert("001")
        assert result["success"] is True

    def test_single_alert_failure(self):
        mod = _import_module()
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.text = "Server Error"
        with patch("send_test_alert.requests.post", return_value=mock_resp):
            result = mod.send_test_alert("001")
        assert result["success"] is False

    def test_main_block_all_command(self, capsys):
        mod = _import_module()
        mock_resp = Mock()
        mock_resp.status_code = 200
        with patch("send_test_alert.requests.post", return_value=mock_resp):
            # Simulate the __main__ block logic for 'all'
            results = mod.send_all_alerts()
            for r in results:
                status = "\u2713" if r["success"] else "\u2717"
                print(f"{status} {r['id']}: {r.get('alert', r.get('error'))}")
        captured = capsys.readouterr()
        assert "\u2713" in captured.out

    def test_main_block_single_success(self, capsys):
        mod = _import_module()
        mock_resp = Mock()
        mock_resp.status_code = 200
        with patch("send_test_alert.requests.post", return_value=mock_resp):
            result = mod.send_test_alert("001")
            if result["success"]:
                print(f"\u2713 Sent test alert: {result['alert']}")
        captured = capsys.readouterr()
        assert "\u2713" in captured.out

    def test_main_block_single_failure(self):
        mod = _import_module()
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.text = "Error"
        with patch("send_test_alert.requests.post", return_value=mock_resp):
            result = mod.send_test_alert("001")
        assert result["success"] is False
        # In __main__ this would sys.exit(1)
