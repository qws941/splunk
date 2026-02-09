#!/usr/bin/env python3
"""Send test Slack alerts for each alert type."""

import os
import sys
from datetime import datetime

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
if not WEBHOOK_URL:
    print("ERROR: SLACK_WEBHOOK_URL environment variable is required", file=sys.stderr)
    print(
        "Usage: SLACK_WEBHOOK_URL='https://hooks.slack.com/...' python send_test_alert.py",
        file=sys.stderr,
    )
    sys.exit(1)

ALERT_TEMPLATES = {
    "001": {
        "name": "Config Change",
        "emoji": "⚙️",
        "color": "#FFA500",
        "sample": {
            "devname": "FGT-HQ-01",
            "user": "admin",
            "action": "edit",
            "path": "firewall policy 101",
        },
    },
    "002": {
        "name": "VPN Tunnel Down",
        "emoji": "🔴",
        "color": "#FF0000",
        "sample": {
            "devname": "FGT-BR-01",
            "tunnel": "HQ-to-Branch",
            "peer": "203.0.113.1",
            "reason": "peer timeout",
        },
    },
    "003": {
        "name": "VPN Tunnel Up",
        "emoji": "🟢",
        "color": "#00FF00",
        "sample": {
            "devname": "FGT-BR-01",
            "tunnel": "HQ-to-Branch",
            "peer": "203.0.113.1",
        },
    },
    "006": {
        "name": "CPU/Memory Anomaly",
        "emoji": "📊",
        "color": "#FF6600",
        "sample": {
            "devname": "FGT-DC-01",
            "cpu": "92%",
            "memory": "87%",
            "threshold": "80%",
        },
    },
    "007": {
        "name": "Hardware Failure",
        "emoji": "🔴",
        "color": "#FF0000",
        "sample": {"devname": "FGT-DC-01", "component": "PSU 2", "status": "failed"},
    },
    "007r": {
        "name": "Hardware Restored",
        "emoji": "🟢",
        "color": "#00FF00",
        "sample": {"devname": "FGT-DC-01", "component": "PSU 2", "status": "restored"},
    },
    "008": {
        "name": "HA State Change",
        "emoji": "🔄",
        "color": "#0066FF",
        "sample": {
            "devname": "FGT-HQ-01",
            "old_state": "standby",
            "new_state": "active",
            "reason": "failover",
        },
    },
    "010": {
        "name": "Resource Limit",
        "emoji": "⚠️",
        "color": "#FFCC00",
        "sample": {
            "devname": "FGT-HQ-01",
            "resource": "session",
            "current": "980000",
            "limit": "1000000",
        },
    },
    "011": {
        "name": "Admin Login Failed",
        "emoji": "🚫",
        "color": "#FF0000",
        "sample": {
            "devname": "FGT-HQ-01",
            "user": "admin",
            "srcip": "192.168.1.100",
            "reason": "invalid password",
            "attempts": "5",
        },
    },
    "012": {
        "name": "Interface Down",
        "emoji": "🔴",
        "color": "#FF0000",
        "sample": {"devname": "FGT-BR-01", "interface": "port1", "reason": "link down"},
    },
    "012r": {
        "name": "Interface Up",
        "emoji": "🟢",
        "color": "#00FF00",
        "sample": {"devname": "FGT-BR-01", "interface": "port1", "status": "link up"},
    },
    "013": {
        "name": "SSL VPN Brute Force",
        "emoji": "🚨",
        "color": "#FF0000",
        "sample": {
            "devname": "FGT-HQ-01",
            "srcip": "45.33.32.156",
            "attempts": "50",
            "timespan": "5 minutes",
        },
    },
    "015": {
        "name": "Abnormal Traffic Spike",
        "emoji": "📈",
        "color": "#FF6600",
        "sample": {
            "devname": "FGT-DC-01",
            "interface": "wan1",
            "current_mbps": "950",
            "baseline_mbps": "200",
        },
    },
    "016": {
        "name": "System Reboot",
        "emoji": "🔄",
        "color": "#0066FF",
        "sample": {
            "devname": "FGT-HQ-01",
            "reason": "firmware upgrade",
            "uptime_before": "45 days",
        },
    },
    "017": {
        "name": "License Expiry Warning",
        "emoji": "⏰",
        "color": "#FFCC00",
        "sample": {
            "devname": "FGT-HQ-01",
            "license": "FortiCare Support",
            "expires_in": "7 days",
            "expiry_date": "2026-02-11",
        },
    },
}


def build_block_kit(alert_id, template):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sample = template["sample"]

    fields = [{"type": "mrkdwn", "text": f"*{k}:*\n{v}"} for k, v in sample.items()]

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{template['emoji']} [{alert_id}] {template['name']} (TEST)",
                "emoji": True,
            },
        },
        {"type": "section", "fields": fields[:4]},
    ]

    if len(fields) > 4:
        blocks.append({"type": "section", "fields": fields[4:8]})

    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"🧪 *TEST ALERT* | {now} | Splunk Security Alert System",
                }
            ],
        }
    )

    return blocks


def send_test_alert(alert_id):
    if alert_id not in ALERT_TEMPLATES:
        return {"success": False, "error": f"Unknown alert ID: {alert_id}"}

    template = ALERT_TEMPLATES[alert_id]
    blocks = build_block_kit(alert_id, template)

    payload = {"blocks": blocks, "attachments": [{"color": template["color"]}]}

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code == 200:
            return {"success": True, "alert": template["name"]}
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_all_alerts():
    results = []
    for alert_id in sorted(ALERT_TEMPLATES.keys()):
        result = send_test_alert(alert_id)
        results.append({"id": alert_id, **result})
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: send_test_alert.py <alert_id|all>")
        print("Alert IDs:", ", ".join(sorted(ALERT_TEMPLATES.keys())))
        sys.exit(1)

    alert_id = sys.argv[1]

    if alert_id == "all":
        results = send_all_alerts()
        for r in results:
            status = "✓" if r["success"] else "✗"
            print(f"{status} {r['id']}: {r.get('alert', r.get('error'))}")
    else:
        result = send_test_alert(alert_id)
        if result["success"]:
            print(f"✓ Sent test alert: {result['alert']}")
        else:
            print(f"✗ Error: {result['error']}")
            sys.exit(1)
