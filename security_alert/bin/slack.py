#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slack Block Kit Alert Action for Splunk
Sends formatted FortiGate alerts to Slack using Block Kit

Optimized version with improved modularity and type hints
"""

import sys
import json
import requests
import os
import gzip
import csv
from datetime import datetime
from typing import List, Dict, Optional, Any

def parse_splunk_results(results_file: str) -> List[Dict[str, str]]:
    """
    Parse Splunk search results from gzipped CSV

    Args:
        results_file: Path to gzipped CSV results file

    Returns:
        List of dictionaries containing search results
    """
    results = []
    try:
        with gzip.open(results_file, 'rt', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
    except (IOError, gzip.BadGzipFile) as e:
        print(f"Error reading gzipped file: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error parsing results: {e}", file=sys.stderr)
    return results

def get_severity_emoji(alert_name: str) -> str:
    """
    Get emoji based on alert name priority

    Args:
        alert_name: Name of the alert

    Returns:
        Emoji string representing severity level
    """
    severity_map = {
        'Hardware': '🔴',
        'VPN': '🔴',
        'HA': '🟠',
        'Interface': '🟠',
        'Config': '🟡',
        'CPU': '🟡'
    }

    for keyword, emoji in severity_map.items():
        if keyword in alert_name:
            return emoji
    return '🔵'

def format_field_value(key: str, value: str, max_length: int = 100) -> str:
    """
    Format field value with proper emoji and formatting

    Args:
        key: Field name
        value: Field value
        max_length: Maximum length for value truncation

    Returns:
        Formatted field string with emoji
    """
    # Truncate long values
    if isinstance(value, str) and len(value) > max_length:
        value = value[:max_length - 3] + "..."

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
    formatted_key = key.replace('_', ' ').title()
    return f"{emoji} *{formatted_key}:* {value}"

def build_header_block(alert_name: str, severity_emoji: str) -> Dict[str, Any]:
    """
    Build header block for Slack message

    Args:
        alert_name: Name of the alert
        severity_emoji: Emoji representing severity

    Returns:
        Header block dictionary
    """
    return {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"{severity_emoji} FortiGate Alert: {alert_name}",
            "emoji": True
        }
    }

def build_metadata_section(search_name: str, result_count: int) -> Dict[str, Any]:
    """
    Build metadata section with alert details

    Args:
        search_name: Name of the search
        result_count: Number of results

    Returns:
        Metadata section dictionary
    """
    return {
        "type": "section",
        "fields": [
            {"type": "mrkdwn", "text": f"*Alert:* {search_name}"},
            {"type": "mrkdwn", "text": f"*Count:* {result_count} events"},
            {"type": "mrkdwn", "text": f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S KST')}"},
            {"type": "mrkdwn", "text": "*Source:* NextTrade Security Alert"}
        ]
    }

def build_event_fields(result: Dict[str, str], max_fields: int = 10) -> List[Dict[str, str]]:
    """
    Build fields for a single event

    Args:
        result: Event data dictionary
        max_fields: Maximum number of fields to include

    Returns:
        List of field dictionaries
    """
    important_fields = [
        'device', 'user', 'source_ip', 'srcip', 'vpn_name',
        'interface', 'component', 'criticality', 'severity',
        'logdesc', 'msg', 'details'
    ]
    excluded_fields = ['_time', '_raw', 'count']

    fields = []

    # Add important fields first
    for key in important_fields:
        if key in result and result[key]:
            fields.append({
                "type": "mrkdwn",
                "text": format_field_value(key, result[key])
            })

    # Add other fields
    for key, value in result.items():
        if key not in important_fields and key not in excluded_fields and value:
            fields.append({
                "type": "mrkdwn",
                "text": format_field_value(key, value)
            })

    return fields[:max_fields]

def build_event_blocks(results: List[Dict[str, str]], max_events: int = 5) -> List[Dict[str, Any]]:
    """
    Build blocks for event details

    Args:
        results: List of event dictionaries
        max_events: Maximum number of events to display

    Returns:
        List of block dictionaries
    """
    blocks = []

    for i, result in enumerate(results[:max_events]):
        if i > 0:
            blocks.append({"type": "divider"})

        fields = build_event_fields(result)
        if fields:
            blocks.append({
                "type": "section",
                "fields": fields
            })

    return blocks

def build_footer_blocks(result_count: int, view_link: str, max_events: int = 5) -> List[Dict[str, Any]]:
    """
    Build footer blocks with count and view button

    Args:
        result_count: Total number of results
        view_link: URL to view in Splunk
        max_events: Maximum events shown

    Returns:
        List of footer block dictionaries
    """
    blocks = []

    if result_count > max_events:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"📌 Showing {max_events} of {result_count} events. Check Splunk for full details."
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

def build_block_kit_message(alert_name: str, search_name: str, results: List[Dict[str, str]], view_link: str = "") -> List[Dict[str, Any]]:
    """
    Build complete Block Kit formatted message

    Args:
        alert_name: Name of the alert
        search_name: Name of the search
        results: List of event dictionaries
        view_link: URL to view in Splunk

    Returns:
        List of Block Kit blocks
    """
    severity_emoji = get_severity_emoji(alert_name)
    result_count = len(results)

    # Build message components
    blocks = [
        build_header_block(alert_name, severity_emoji),
        build_metadata_section(search_name, result_count),
        {"type": "divider"}
    ]

    # Add event blocks
    blocks.extend(build_event_blocks(results))

    # Add footer blocks
    blocks.extend(build_footer_blocks(result_count, view_link))

    return blocks

def send_to_slack(webhook_url: Optional[str], bot_token: Optional[str], channel: str,
                  blocks: List[Dict[str, Any]], proxies: Optional[Dict[str, str]] = None) -> bool:
    """
    Send message to Slack via webhook or Bot Token

    Args:
        webhook_url: Slack webhook URL (fallback method)
        bot_token: Slack bot token (preferred method)
        channel: Target Slack channel
        blocks: Block Kit formatted message blocks
        proxies: Optional proxy configuration

    Returns:
        True if message sent successfully, False otherwise
    """
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
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Warning: Failed to parse configuration from stdin: {e}", file=sys.stderr)
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
