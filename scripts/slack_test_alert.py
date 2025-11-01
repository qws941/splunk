#!/usr/bin/env python3
"""
Slack Test Alert Action Script
Triggered from dashboard via alert action
"""

import sys
import json
import os
from datetime import datetime

# Slack Webhook URL (configure in alert_actions.conf)
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK_URL', '')
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', '#splunk')

def send_slack_message(message):
    """Send message to Slack using webhook"""
    import urllib.request

    payload = {
        "channel": SLACK_CHANNEL,
        "text": message,
        "username": "Splunk Alert",
        "icon_emoji": ":bell:"
    }

    req = urllib.request.Request(
        SLACK_WEBHOOK,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"ERROR: Failed to send Slack message: {e}", file=sys.stderr)
        return None

def main():
    """Main execution"""
    # Read alert config from stdin
    config = {}
    try:
        config = json.loads(sys.stdin.read())
    except:
        pass

    # Generate test message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"""🧪 *Slack 테스트 알림*

시간: {timestamp}
장비: FortiGate-TEST
상태: 정상
채널: {SLACK_CHANNEL}

✅ Slack 알림 정상 작동 중"""

    # Send to Slack
    result = send_slack_message(message)

    if result:
        print(f"✅ Slack message sent successfully at {timestamp}")
    else:
        print(f"❌ Failed to send Slack message", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
