#!/usr/bin/env python3
"""
Slack Block Kit Alert Action for Splunk
Purpose: Send interactive Slack notifications with Block Kit UI
Author: JC Lee
Date: 2025-10-25
Version: 1.0

Features:
- Rich UI with sections, buttons, context
- Severity-based color coding
- Interactive buttons (Acknowledge, Disable Alert, View Dashboard)
- Better mobile experience
"""

import sys
import json
import os
import re
from datetime import datetime
from urllib import request, parse, error

# =============================================================================
# Configuration
# =============================================================================

# Get environment variables or use defaults
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN', '')
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', '')
SPLUNK_HOST = os.environ.get('SPLUNK_HOST', 'splunk.jclee.me')

# Severity to color mapping
SEVERITY_COLORS = {
    'critical': '#DC3545',   # Red
    'high': '#FD7E14',       # Orange
    'medium': '#FFC107',     # Amber
    'low': '#28A745',        # Green
    'info': '#17A2B8'        # Blue
}

# Severity to emoji mapping
SEVERITY_EMOJIS = {
    'critical': ':rotating_light:',
    'high': ':warning:',
    'medium': ':large_orange_diamond:',
    'low': ':large_blue_diamond:',
    'info': ':information_source:'
}

# =============================================================================
# Block Kit Message Builder
# =============================================================================

def build_blockkit_message(alert_data):
    """
    Build Slack Block Kit JSON structure

    Args:
        alert_data: Dictionary containing alert information
            {
                'title': 'Alert title',
                'severity': 'critical',
                'src_ip': '192.168.1.100',
                'dst_ip': '10.0.0.1',
                'message': 'Alert description',
                'alert_name': 'FAZ_Critical_Alerts',
                'event_count': 5,
                'timestamp': '2025-10-25 14:30:00'
            }

    Returns:
        Dictionary: Block Kit JSON structure
    """

    severity = alert_data.get('severity', 'info').lower()
    color = SEVERITY_COLORS.get(severity, '#6C757D')
    emoji = SEVERITY_EMOJIS.get(severity, ':bell:')

    # Build header block with emoji
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} {alert_data.get('title', 'Splunk Alert')}",
                "emoji": True
            }
        },
        {
            "type": "divider"
        }
    ]

    # Build main information section
    fields = []

    # Severity field
    if 'severity' in alert_data:
        fields.append({
            "type": "mrkdwn",
            "text": f"*Severity:*\n{severity.upper()}"
        })

    # Source IP
    if 'src_ip' in alert_data and alert_data['src_ip'] != 'N/A':
        fields.append({
            "type": "mrkdwn",
            "text": f"*Source IP:*\n`{alert_data['src_ip']}`"
        })

    # Destination IP
    if 'dst_ip' in alert_data and alert_data['dst_ip'] != 'N/A':
        fields.append({
            "type": "mrkdwn",
            "text": f"*Destination IP:*\n`{alert_data['dst_ip']}`"
        })

    # Event count
    if 'event_count' in alert_data:
        fields.append({
            "type": "mrkdwn",
            "text": f"*Event Count:*\n{alert_data['event_count']}"
        })

    # User (for FMG alerts)
    if 'user' in alert_data and alert_data['user'] != 'N/A':
        fields.append({
            "type": "mrkdwn",
            "text": f"*User:*\n{alert_data['user']}"
        })

    # Action (for FMG alerts)
    if 'action' in alert_data and alert_data['action'] != 'N/A':
        fields.append({
            "type": "mrkdwn",
            "text": f"*Action:*\n{alert_data['action']}"
        })

    if fields:
        blocks.append({
            "type": "section",
            "fields": fields
        })

    # Message/Description block
    if 'message' in alert_data and alert_data['message'] != 'N/A':
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Message:*\n{alert_data['message']}"
            }
        })

    blocks.append({"type": "divider"})

    # Interactive buttons
    buttons = [
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "✅ Acknowledge",
                "emoji": True
            },
            "style": "primary",
            "value": f"ack_{alert_data.get('alert_name', 'unknown')}",
            "action_id": "acknowledge_alert"
        },
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "🔕 Disable Alert",
                "emoji": True
            },
            "style": "danger",
            "value": f"disable_{alert_data.get('alert_name', 'unknown')}",
            "action_id": "disable_alert",
            "confirm": {
                "title": {
                    "type": "plain_text",
                    "text": "Disable Alert?"
                },
                "text": {
                    "type": "mrkdwn",
                    "text": f"Are you sure you want to disable *{alert_data.get('alert_name', 'this alert')}*?"
                },
                "confirm": {
                    "type": "plain_text",
                    "text": "Disable"
                },
                "deny": {
                    "type": "plain_text",
                    "text": "Cancel"
                },
                "style": "danger"
            }
        },
        {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "📊 View Dashboard",
                "emoji": True
            },
            "url": f"https://{SPLUNK_HOST}:8000/app/search/fortigate_operations",
            "action_id": "view_dashboard"
        }
    ]

    blocks.append({
        "type": "actions",
        "elements": buttons
    })

    # Context footer (timestamp, alert name)
    context_elements = []

    if 'timestamp' in alert_data:
        context_elements.append({
            "type": "mrkdwn",
            "text": f":clock3: {alert_data['timestamp']}"
        })

    if 'alert_name' in alert_data:
        context_elements.append({
            "type": "mrkdwn",
            "text": f":bell: {alert_data['alert_name']}"
        })

    if context_elements:
        blocks.append({
            "type": "context",
            "elements": context_elements
        })

    # Build final message
    message = {
        "blocks": blocks,
        "attachments": [
            {
                "color": color,
                "fallback": alert_data.get('message', 'Splunk Alert')
            }
        ]
    }

    return message

# =============================================================================
# Slack API Clients
# =============================================================================

def send_via_bot_token(channel, message):
    """
    Send message via Slack Bot Token (chat.postMessage API)
    Supports Block Kit and interactive components
    """

    if not SLACK_BOT_TOKEN:
        raise ValueError("SLACK_BOT_TOKEN environment variable not set")

    url = 'https://slack.com/api/chat.postMessage'

    payload = {
        'channel': channel,
        **message  # Includes blocks and attachments
    }

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {SLACK_BOT_TOKEN}'
    }

    req = request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))

            if not result.get('ok'):
                raise Exception(f"Slack API error: {result.get('error', 'Unknown')}")

            return result

    except error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"HTTP {e.code}: {error_body}")


def send_via_webhook(message):
    """
    Send message via Slack Incoming Webhook
    Limited Block Kit support (no interactive components)
    """

    if not SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL environment variable not set")

    # Webhook only supports text, blocks, attachments (no channel override)
    payload = message

    req = request.Request(
        SLACK_WEBHOOK_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json; charset=utf-8'},
        method='POST'
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                raise Exception(f"Webhook HTTP {response.status}")
            return {'ok': True}

    except error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"HTTP {e.code}: {error_body}")


# =============================================================================
# Splunk Alert Action Entry Point
# =============================================================================

def main():
    """
    Main entry point for Splunk alert action

    Splunk passes alert data via stdin as JSON:
    {
        "result": {
            "src_ip": "192.168.1.100",
            "dst_ip": "10.0.0.1",
            "severity": "critical",
            "message": "High severity event detected",
            "alert_text": "..."  # Legacy field
        },
        "search_name": "FAZ_Critical_Alerts",
        "results_link": "https://splunk.jclee.me:8000/...",
        "server_host": "splunk.jclee.me"
    }
    """

    # Read input from Splunk (stdin)
    try:
        input_data = sys.stdin.read()
        splunk_data = json.loads(input_data)
    except Exception as e:
        print(f"ERROR: Failed to parse Splunk input: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract alert fields
    result = splunk_data.get('result', {})
    search_name = splunk_data.get('search_name', 'Unknown Alert')

    # Build alert data dictionary
    alert_data = {
        'title': result.get('alert_title', search_name),
        'severity': result.get('severity', result.get('severity_level', 'info')),
        'src_ip': result.get('src_ip', 'N/A'),
        'dst_ip': result.get('dst_ip', 'N/A'),
        'message': result.get('message', result.get('msg', result.get('alert_text', 'No message'))),
        'alert_name': search_name,
        'event_count': result.get('event_count', result.get('count', 1)),
        'user': result.get('user', result.get('user_name', 'N/A')),
        'action': result.get('action', result.get('operation_type', 'N/A')),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Build Block Kit message
    try:
        message = build_blockkit_message(alert_data)
    except Exception as e:
        print(f"ERROR: Failed to build Block Kit message: {e}", file=sys.stderr)
        sys.exit(1)

    # Send to Slack
    channel = result.get('channel', '#splunk-alerts')

    try:
        if SLACK_BOT_TOKEN:
            # Preferred: Bot Token (supports interactive buttons)
            result = send_via_bot_token(channel, message)
            print(f"SUCCESS: Message sent via Bot Token to {channel}")
        elif SLACK_WEBHOOK_URL:
            # Fallback: Webhook (no interactive buttons)
            result = send_via_webhook(message)
            print(f"SUCCESS: Message sent via Webhook (no interactive buttons)")
        else:
            print("ERROR: Neither SLACK_BOT_TOKEN nor SLACK_WEBHOOK_URL configured", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: Failed to send Slack message: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
