#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slack Block Kit Alert Action for Splunk
Sends formatted FortiGate alerts to Slack using Block Kit
"""

import os
import sys

# Add vendored libraries to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

import csv
import fcntl
import gzip
import json
from datetime import datetime

import requests


def parse_splunk_results(results_file):
    """Parse Splunk search results from gzipped CSV"""
    results = []
    try:
        with gzip.open(results_file, "rt", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
    except Exception as e:
        print(f"Error parsing results: {e}", file=sys.stderr)
    return results


def get_severity_emoji(alert_name):
    """Get emoji based on alert name"""
    if "Hardware" in alert_name or "VPN" in alert_name:
        return "🔴"
    elif "HA" in alert_name or "Interface" in alert_name:
        return "🟠"
    elif "Config" in alert_name or "CPU" in alert_name:
        return "🟡"
    else:
        return "🔵"


def format_field_value(key, value):
    if isinstance(value, str) and len(value) > 100:
        value = value[:97] + "..."

    emoji_map = {
        "device": "🖥️",
        "user": "👤",
        "source_ip": "🌐",
        "srcip": "🌐",
        "dstip": "🎯",
        "vpn_name": "🔐",
        "interface": "🔌",
        "component": "⚙️",
        "criticality": "⚡",
        "severity": "📊",
    }

    emoji = emoji_map.get(key, "")
    return f"{emoji} *{key.replace('_', ' ').title()}:* {value}"


def build_block_kit_message(
    alert_name, search_name, results, view_link="", alert_id=None
):
    """Build Block Kit formatted message with interactive buttons"""

    severity_emoji = get_severity_emoji(alert_name)
    result_count = len(results)

    alert_id = alert_id or f"{search_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{severity_emoji} FortiGate Alert: {alert_name}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Alert:* {search_name}"},
                {"type": "mrkdwn", "text": f"*Count:* {result_count} events"},
                {
                    "type": "mrkdwn",
                    "text": f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}",
                },
                {"type": "mrkdwn", "text": "*Source:* NextTrade Security Alert"},
            ],
        },
        {"type": "divider"},
    ]

    for i, result in enumerate(results[:5]):
        if i > 0:
            blocks.append({"type": "divider"})

        fields = []
        important_fields = [
            "device",
            "user",
            "source_ip",
            "srcip",
            "vpn_name",
            "interface",
            "component",
            "criticality",
            "severity",
            "logdesc",
            "msg",
            "details",
        ]

        for key in important_fields:
            if key in result and result[key]:
                fields.append(
                    {"type": "mrkdwn", "text": format_field_value(key, result[key])}
                )

        for key, value in result.items():
            if (
                key not in important_fields
                and key not in ["_time", "_raw", "count"]
                and value
            ):
                fields.append(
                    {"type": "mrkdwn", "text": format_field_value(key, value)}
                )

        if fields:
            blocks.append({"type": "section", "fields": fields[:10]})

    # Add footer with view link
    if result_count > 5:
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📌 Showing 5 of {result_count} events. Check Splunk for full details.",
                    }
                ],
            }
        )

    if view_link:
        action_elements = [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "View in Splunk", "emoji": True},
                "url": view_link,
                "style": "primary",
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "✅ Acknowledge", "emoji": True},
                "action_id": "ack_alert",
                "value": alert_id,
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "🔇 Snooze 1h", "emoji": True},
                "action_id": "snooze_alert_1h",
                "value": alert_id,
            },
        ]
        blocks.append({"type": "actions", "elements": action_elements})
    else:
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Acknowledge",
                            "emoji": True,
                        },
                        "action_id": "ack_alert",
                        "value": alert_id,
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔇 Snooze 1h",
                            "emoji": True,
                        },
                        "action_id": "snooze_alert_1h",
                        "value": alert_id,
                    },
                ],
            }
        )

    return blocks


def get_alert_state_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "..", "lookups", "alert_state.csv")


def get_recent_alert_thread_ts(search_name, channel, max_age_minutes=60):
    """Find recent open alert to thread under. Returns thread_ts or None."""
    state_file = get_alert_state_path()

    if not os.path.exists(state_file):
        return None

    try:
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(minutes=max_age_minutes)

        with open(state_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reversed(list(reader)):
                if (
                    row.get("search_name") == search_name
                    and row.get("channel") == channel
                    and row.get("status") == "open"
                ):

                    created = datetime.strptime(
                        row.get("created_at", ""), "%Y-%m-%d %H:%M:%S"
                    )
                    if created > cutoff:
                        return row.get("message_ts")
    except Exception:
        pass

    return None


def save_alert_state(search_name, message_ts, channel):
    state_file = get_alert_state_path()

    fieldnames = [
        "alert_id",
        "search_name",
        "message_ts",
        "channel",
        "status",
        "created_at",
        "updated_at",
        "acked_by",
    ]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_id = f"{search_name}_{message_ts}"

    new_row = {
        "alert_id": alert_id,
        "search_name": search_name,
        "message_ts": message_ts,
        "channel": channel,
        "status": "open",
        "created_at": now,
        "updated_at": now,
        "acked_by": "",
    }

    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)

        if not os.path.exists(state_file):
            with open(state_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(new_row)
            return

        with open(state_file, "r+", encoding="utf-8", newline="") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                reader = csv.DictReader(f)
                rows = list(reader)
                rows.append(new_row)

                f.seek(0)
                f.truncate()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows[-1000:])
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception as e:
        print(f"Error saving alert state: {e}", file=sys.stderr)


def send_to_slack(webhook_url, bot_token, channel, blocks, proxies=None):
    """Send message to Slack via webhook or Bot Token. Returns (success, message_ts)"""

    payload = {
        "channel": channel,
        "username": "FortiGate Security Alert",
        "icon_emoji": ":rotating_light:",
        "blocks": blocks,
    }

    try:
        if bot_token and bot_token.startswith("xoxb-"):
            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                json=payload,
                timeout=10,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {bot_token}",
                },
                proxies=proxies,
            )
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                message_ts = result.get("ts", "")
                print(
                    f"Alert sent to Slack successfully (Bot Token) ts={message_ts}",
                    file=sys.stderr,
                )
                return True, message_ts
            else:
                print(
                    f"Slack API error: {result.get('error', 'unknown')}",
                    file=sys.stderr,
                )
                return False, None

        elif webhook_url and webhook_url.startswith("https://hooks.slack.com"):
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
                proxies=proxies,
            )
            response.raise_for_status()

            if response.text == "ok":
                print("Alert sent to Slack successfully (Webhook)", file=sys.stderr)
                return True, None
            else:
                print(f"Slack webhook response: {response.text}", file=sys.stderr)
                return False, None

        else:
            print(
                "Error: No valid Slack credentials (need bot_token or webhook_url)",
                file=sys.stderr,
            )
            return False, None

    except requests.exceptions.Timeout:
        print("Error: Request to Slack timed out", file=sys.stderr)
        return False, None
    except requests.exceptions.RequestException as e:
        print(f"Error sending to Slack: {e}", file=sys.stderr)
        return False, None


def main():
    """Main execution"""

    if len(sys.argv) < 2:
        print(
            "Error: Missing arguments. Usage: slack_blockkit_alert.py <results_file>",
            file=sys.stderr,
        )
        sys.exit(1)

    # Get configuration from environment or Splunk settings
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    channel = os.environ.get("SLACK_CHANNEL", "#security-firewall-alert")

    proxies = None

    search_name = sys.argv[1] if len(sys.argv) > 1 else "Manual Alert"
    view_link = ""

    try:
        config_str = sys.stdin.read()
        if config_str:
            config = json.loads(config_str)
            webhook_url = config.get("configuration", {}).get(
                "webhook_url", webhook_url
            )
            bot_token = config.get("configuration", {}).get(
                "slack_app_oauth_token", bot_token
            )
            if not bot_token:
                bot_token = config.get("configuration", {}).get("bot_token", bot_token)
            channel = config.get("configuration", {}).get("channel", channel)
            search_name = config.get("search_name", "Unknown Alert")
            view_link = config.get("results_link", "")

            proxy_enabled = config.get("configuration", {}).get("proxy_enabled", "0")
            if proxy_enabled == "1" or proxy_enabled is True:
                proxy_url = config.get("configuration", {}).get("proxy_url", "")
                proxy_port = config.get("configuration", {}).get("proxy_port", "")
                proxy_username = config.get("configuration", {}).get(
                    "proxy_username", ""
                )
                proxy_password = config.get("configuration", {}).get(
                    "proxy_password", ""
                )

                if proxy_url and proxy_port:
                    if proxy_username and proxy_password:
                        proxy_auth = f"{proxy_username}:{proxy_password}@"
                    else:
                        proxy_auth = ""

                    proxy_full_url = f"http://{proxy_auth}{proxy_url}:{proxy_port}"
                    proxies = {"http": proxy_full_url, "https": proxy_full_url}
                    print(f"Using proxy: {proxy_url}:{proxy_port}", file=sys.stderr)
    except Exception:
        pass

    if not webhook_url and not bot_token:
        print(
            "Error: Neither SLACK_WEBHOOK_URL nor SLACK_BOT_TOKEN configured",
            file=sys.stderr,
        )
        print(
            "Configure via: Splunk Web → Apps → Security Alert System → Setup",
            file=sys.stderr,
        )
        sys.exit(1)

    results_file = sys.argv[1] if len(sys.argv) > 1 else None
    if results_file and os.path.exists(results_file):
        results = parse_splunk_results(results_file)
    else:
        print(f"Warning: Results file not found: {results_file}", file=sys.stderr)
        results = []

    if not results:
        print("No results to send", file=sys.stderr)
        sys.exit(0)

    alert_name = search_name.replace("_", " ").title()

    blocks = build_block_kit_message(alert_name, search_name, results, view_link)
    success, message_ts = send_to_slack(
        webhook_url, bot_token, channel, blocks, proxies
    )

    if success and message_ts:
        save_alert_state(search_name, message_ts, channel)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
