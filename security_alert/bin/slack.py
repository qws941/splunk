#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slack Block Kit Alert Action for Splunk
Sends formatted FortiGate alerts to Slack using Block Kit
"""

import sys
import os

# Add bundled libraries to path
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(APP_DIR, 'lib', 'python3')
if os.path.exists(LIB_DIR) and LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

import json
import requests
import gzip
import csv
from datetime import datetime

def parse_splunk_results(results_file):
    """Parse Splunk search results from gzipped CSV"""
    results = []
    try:
        with gzip.open(results_file, 'rt', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
    except Exception as e:
        print(f"Error parsing results: {e}", file=sys.stderr)
    return results

def get_severity_emoji(alert_name):
    """Get emoji based on alert name"""
    if 'Hardware' in alert_name or 'VPN' in alert_name:
        return '🔴'
    elif 'HA' in alert_name or 'Interface' in alert_name:
        return '🟠'
    elif 'Config' in alert_name or 'CPU' in alert_name:
        return '🟡'
    else:
        return '🔵'

def format_field_value(key, value):
    """Format field value with proper emoji and formatting"""
    # Truncate long values
    if isinstance(value, str) and len(value) > 100:
        value = value[:97] + "..."

    # Add emoji for specific fields
    emoji_map = {
        'device': '🖥️',
        'user': '👤',
        'source_ip': '🌐',
        'srcip': '🌐',
        'dstip': '🎯',
        'vpn_name': '🔐',
        'interface': '🔌',
        'component': '⚙️',
        'criticality': '⚡',
        'severity': '📊'
    }

    emoji = emoji_map.get(key, '')
    return f"{emoji} *{key.replace('_', ' ').title()}:* {value}"

def build_block_kit_message(alert_name, search_name, results, view_link=""):
    """Build Block Kit formatted message"""

    severity_emoji = get_severity_emoji(alert_name)
    result_count = len(results)

    # Header block
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{severity_emoji} FortiGate Alert: {alert_name}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Alert:* {search_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Count:* {result_count} events"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Source:* NextTrade Security Alert"
                }
            ]
        },
        {
            "type": "divider"
        }
    ]

    # Add result details (limit to first 5 events)
    for i, result in enumerate(results[:5]):
        if i > 0:
            blocks.append({"type": "divider"})

        # Build fields for this event
        fields = []
        important_fields = ['device', 'user', 'source_ip', 'srcip', 'vpn_name',
                           'interface', 'component', 'criticality', 'severity',
                           'logdesc', 'msg', 'details']

        # Add important fields first
        for key in important_fields:
            if key in result and result[key]:
                fields.append({
                    "type": "mrkdwn",
                    "text": format_field_value(key, result[key])
                })

        # Add other fields
        for key, value in result.items():
            if key not in important_fields and key not in ['_time', '_raw', 'count'] and value:
                fields.append({
                    "type": "mrkdwn",
                    "text": format_field_value(key, value)
                })

        # Limit to 10 fields per event
        if fields:
            blocks.append({
                "type": "section",
                "fields": fields[:10]
            })

    # Add footer with view link
    if result_count > 5:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"📌 Showing 5 of {result_count} events. Check Splunk for full details."
                }
            ]
        })

    if view_link:
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View in Splunk",
                        "emoji": True
                    },
                    "url": view_link,
                    "style": "primary"
                }
            ]
        })

    return blocks

def send_to_slack(webhook_url, bot_token, channel, blocks, proxies=None):
    """Send message to Slack via webhook or Bot Token"""

    payload = {
        "channel": channel,
        "username": "FortiGate Security Alert",
        "icon_emoji": ":rotating_light:",
        "blocks": blocks
    }

    try:
        # Method 1: Bot Token (OAuth) - Preferred
        if bot_token and bot_token.startswith('xoxb-'):
            response = requests.post(
                'https://slack.com/api/chat.postMessage',
                json=payload,
                timeout=10,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {bot_token}'
                },
                proxies=proxies
            )
            response.raise_for_status()
            result = response.json()

            if result.get('ok'):
                print("Alert sent to Slack successfully (Bot Token)", file=sys.stderr)
                return True
            else:
                print(f"Slack API error: {result.get('error', 'unknown')}", file=sys.stderr)
                return False

        # Method 2: Webhook URL - Fallback
        elif webhook_url and webhook_url.startswith('https://hooks.slack.com'):
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'},
                proxies=proxies
            )
            response.raise_for_status()

            if response.text == 'ok':
                print("Alert sent to Slack successfully (Webhook)", file=sys.stderr)
                return True
            else:
                print(f"Slack webhook response: {response.text}", file=sys.stderr)
                return False

        else:
            print("Error: No valid Slack credentials (need bot_token or webhook_url)", file=sys.stderr)
            return False

    except requests.exceptions.Timeout:
        print("Error: Request to Slack timed out", file=sys.stderr)
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error sending to Slack: {e}", file=sys.stderr)
        return False

def main():
    """Main execution"""

    if len(sys.argv) < 2:
        print("Error: Missing arguments. Usage: slack_blockkit_alert.py <results_file>", file=sys.stderr)
        sys.exit(1)

    # Get configuration from environment or Splunk settings
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    bot_token = os.environ.get('SLACK_BOT_TOKEN')
    channel = os.environ.get('SLACK_CHANNEL', '#security-firewall-alert')

    # Proxy configuration
    proxies = None

    # Try to read from stdin for configuration (Splunk alert action format)
    try:
        config_str = sys.stdin.read()
        if config_str:
            config = json.loads(config_str)
            webhook_url = config.get('configuration', {}).get('webhook_url', webhook_url)
            # Splunk uses 'slack_app_oauth_token' not 'bot_token'
            bot_token = config.get('configuration', {}).get('slack_app_oauth_token', bot_token)
            # Fallback to bot_token for backward compatibility
            if not bot_token:
                bot_token = config.get('configuration', {}).get('bot_token', bot_token)
            # Channel hardcoded (Splunk doesn't support param.channel)
            channel = '#security-firewall-alert'
            search_name = config.get('search_name', 'Unknown Alert')
            view_link = config.get('results_link', '')

            # Read proxy configuration
            proxy_enabled = config.get('configuration', {}).get('proxy_enabled', '0')
            if proxy_enabled == '1' or proxy_enabled is True:
                proxy_url = config.get('configuration', {}).get('proxy_url', '')
                proxy_port = config.get('configuration', {}).get('proxy_port', '')
                proxy_username = config.get('configuration', {}).get('proxy_username', '')
                proxy_password = config.get('configuration', {}).get('proxy_password', '')

                if proxy_url and proxy_port:
                    # Build proxy URL
                    if proxy_username and proxy_password:
                        proxy_auth = f"{proxy_username}:{proxy_password}@"
                    else:
                        proxy_auth = ""

                    proxy_full_url = f"http://{proxy_auth}{proxy_url}:{proxy_port}"
                    proxies = {
                        'http': proxy_full_url,
                        'https': proxy_full_url
                    }
                    print(f"Using proxy: {proxy_url}:{proxy_port}", file=sys.stderr)
    except:
        search_name = sys.argv[1] if len(sys.argv) > 1 else 'Manual Alert'
        view_link = ''

    if not webhook_url and not bot_token:
        print("Error: Neither SLACK_WEBHOOK_URL nor SLACK_BOT_TOKEN configured", file=sys.stderr)
        print("Configure via: Splunk Web → Apps → Security Alert System → Setup", file=sys.stderr)
        sys.exit(1)

    # Parse results file
    results_file = sys.argv[1] if len(sys.argv) > 1 else None
    if results_file and os.path.exists(results_file):
        results = parse_splunk_results(results_file)
    else:
        print(f"Warning: Results file not found: {results_file}", file=sys.stderr)
        results = []

    if not results:
        print("No results to send", file=sys.stderr)
        sys.exit(0)

    # Extract alert name from search name
    alert_name = search_name.replace('_', ' ').title()

    # Build and send message
    blocks = build_block_kit_message(alert_name, search_name, results, view_link)
    success = send_to_slack(webhook_url, bot_token, channel, blocks, proxies)

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
