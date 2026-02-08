#!/usr/bin/env python3
"""
Splunk Alert Action for Slack
Purpose: Send Splunk alerts to Slack via Webhook (Python-based for Splunk compatibility)
"""

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime


def send_to_slack(webhook_url, alert_data):
    """
    Send alert to Slack via Webhook

    Args:
        webhook_url (str): Slack Webhook URL
        alert_data (dict): Alert data from Splunk

    Returns:
        bool: Success status
    """
    # Extract alert information
    search_name = alert_data.get("search_name", "Unknown")
    severity = alert_data.get("severity", "medium")
    message = alert_data.get("message", "Alert triggered")
    result_count = alert_data.get("result_count", 0)
    results = alert_data.get("results", [])

    # Determine color based on severity
    color_map = {
        "critical": "#DC4E41",
        "high": "#F8BE34",
        "medium": "#87CEEB",
        "low": "#53A051",
        "info": "#6C757D",
    }
    color = color_map.get(severity.lower(), "#CCCCCC")

    # Emoji based on severity
    emoji_map = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
        "info": "🔵",
    }
    emoji = emoji_map.get(severity.lower(), "⚪")

    # Build Slack message
    fields = [
        {"title": "Alert Name", "value": search_name, "short": True},
        {"title": "Severity", "value": severity.upper(), "short": True},
        {"title": "Result Count", "value": str(result_count), "short": True},
        {
            "title": "Time",
            "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "short": True,
        },
    ]

    # Add first 3 results as fields
    if results:
        for idx, result in enumerate(results[:3]):
            if isinstance(result, dict):
                for key, value in list(result.items())[:3]:
                    fields.append(
                        {
                            "title": key,
                            "value": str(value),
                            "short": len(str(value)) < 30,
                        }
                    )

    payload = {
        "text": f"{emoji} *Splunk Alert: {search_name}*",
        "attachments": [
            {
                "color": color,
                "title": f"{severity.upper()} Alert",
                "text": message,
                "fields": fields,
                "footer": "Splunk Alert System",
                "ts": int(datetime.now().timestamp()),
            }
        ],
    }

    # Send to Slack
    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print(
                    f"✅ Slack alert sent successfully: {search_name}", file=sys.stderr
                )
                return True
            else:
                print(f"❌ Slack API returned {response.status}", file=sys.stderr)
                return False

    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error sending to Slack: {str(e)}", file=sys.stderr)
        return False


def main():
    """
    Main function - Read alert data from Splunk and send to Slack

    Splunk passes alert data via:
    1. Environment variables (configuration)
    2. STDIN (search results as JSON)
    """
    # Read configuration from stdin (Splunk alert action format)
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        # Read from stdin
        input_data = sys.stdin.read()

        try:
            config = json.loads(input_data)
        except json.JSONDecodeError:
            print("❌ Invalid JSON input", file=sys.stderr)
            sys.exit(1)

        # Extract configuration
        webhook_url = config.get("configuration", {}).get("webhook_url")
        severity = config.get("configuration", {}).get("severity", "medium")

        if not webhook_url:
            print("❌ Slack Webhook URL not configured", file=sys.stderr)
            sys.exit(1)

        # Extract search results
        results = config.get("result", {})
        search_name = config.get("search_name", "Splunk Alert")

        # Build alert data
        alert_data = {
            "search_name": search_name,
            "severity": severity,
            "message": f"Alert triggered from search: {search_name}",
            "result_count": 1 if results else 0,
            "results": [results] if results else [],
        }

        # Send to Slack
        success = send_to_slack(webhook_url, alert_data)
        sys.exit(0 if success else 1)

    else:
        # Test mode or manual execution
        print("Splunk Alert Action for Slack")
        print("Usage: python3 splunk-alert-action.py --execute < alert_data.json")
        print("\nTest mode: Checking configuration...")

        # Check if webhook URL is in environment
        import os

        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

        if webhook_url:
            print("✅ SLACK_WEBHOOK_URL configured")
            print(f"   URL: {webhook_url[:30]}...")

            # Test connection
            test_data = {
                "search_name": "Connection Test",
                "severity": "info",
                "message": "✅ Splunk → Slack 연결 테스트",
                "result_count": 0,
                "results": [],
            }

            print("\n🧪 Sending test message...")
            success = send_to_slack(webhook_url, test_data)

            if success:
                print("✅ Test successful")
                sys.exit(0)
            else:
                print("❌ Test failed")
                sys.exit(1)
        else:
            print("⚠️  SLACK_WEBHOOK_URL not configured")
            print("   Set environment variable or configure in Splunk")
            sys.exit(1)


if __name__ == "__main__":
    main()
