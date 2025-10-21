#!/usr/bin/env python3
"""
Splunk Alert Action Script with MITRE ATT&CK Integration

This script is called by Splunk when alert conditions are met.
It sends enriched alerts to Slack with MITRE ATT&CK context.

Installation:
1. Copy to: $SPLUNK_HOME/bin/scripts/splunk-alert-action-enhanced.py
2. Make executable: chmod +x splunk-alert-action-enhanced.py
3. Configure in alert_actions.conf

Usage:
- Triggered automatically by Splunk alerts
- Reads alert data from stdin
- Calls Node.js enhanced Slack handler

Phase 2.3 - Advanced Slack Notifications
"""

import sys
import json
import os
import subprocess
from datetime import datetime

# Splunk passes alert data via stdin
def read_alert_data():
    """Read alert data from Splunk stdin"""
    try:
        alert_data = json.loads(sys.stdin.read())
        return alert_data
    except Exception as e:
        print(f"ERROR: Failed to parse alert data: {e}", file=sys.stderr)
        return None

def extract_alert_fields(alert_data):
    """Extract key fields from Splunk alert data"""
    try:
        # Splunk alert structure
        result = alert_data.get('result', {})
        search_name = alert_data.get('search_name', 'Unknown Alert')

        # Extract fields
        fields = {
            'message': search_name,
            'severity': result.get('severity', 'medium'),
            'logid': result.get('logid'),
            'srcip': result.get('srcip'),
            'dstip': result.get('dstip'),
            'action': result.get('action'),
            'devname': result.get('devname'),
            'user': result.get('user'),
            'admin': result.get('admin'),
            'msg': result.get('msg'),
            'time': result.get('_time', datetime.now().isoformat())
        }

        # Determine alert type and title
        if 'config' in search_name.lower():
            fields['title'] = '⚙️ Configuration Change Detected'
            fields['type'] = 'config_change'
        elif 'critical' in search_name.lower() or 'high' in search_name.lower():
            fields['title'] = '🔴 Critical Security Event'
            fields['type'] = 'security_event'
        elif 'vpn' in search_name.lower():
            fields['title'] = '🔐 VPN Access Event'
            fields['type'] = 'vpn_event'
        elif 'policy' in search_name.lower():
            fields['title'] = '📋 Policy Change Detected'
            fields['type'] = 'policy_change'
        else:
            fields['title'] = '⚠️ Security Alert'
            fields['type'] = 'generic'

        return fields

    except Exception as e:
        print(f"ERROR: Failed to extract alert fields: {e}", file=sys.stderr)
        return None

def send_to_slack(alert_fields):
    """Send alert to Slack using enhanced Node.js handler"""
    try:
        # Path to Node.js CLI script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cli_script = os.path.join(script_dir, 'slack-alert-cli-enhanced.js')

        if not os.path.exists(cli_script):
            print(f"ERROR: CLI script not found: {cli_script}", file=sys.stderr)
            return False

        # Build command
        cmd = ['node', cli_script]

        # Add message
        if alert_fields.get('message'):
            cmd.extend(['--message', alert_fields['message']])

        # Add severity
        if alert_fields.get('severity'):
            cmd.extend(['--severity', alert_fields['severity']])

        # Add title
        if alert_fields.get('title'):
            cmd.extend(['--title', alert_fields['title']])

        # Add logid (for MITRE enrichment)
        if alert_fields.get('logid'):
            cmd.extend(['--logid', alert_fields['logid']])

        # Build data JSON
        data = {}
        for key in ['srcip', 'dstip', 'action', 'devname', 'user', 'admin', 'msg', 'time']:
            if alert_fields.get(key):
                data[key] = alert_fields[key]

        if data:
            cmd.extend(['--data', json.dumps(data)])

        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"SUCCESS: Alert sent to Slack", file=sys.stdout)
            return True
        else:
            print(f"ERROR: Slack CLI failed: {result.stderr}", file=sys.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("ERROR: Slack CLI timeout (30s)", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: Failed to send to Slack: {e}", file=sys.stderr)
        return False

def main():
    """Main execution"""
    print("INFO: Splunk Alert Action started", file=sys.stdout)

    # Read alert data from Splunk
    alert_data = read_alert_data()
    if not alert_data:
        print("ERROR: No alert data received", file=sys.stderr)
        sys.exit(1)

    # Extract fields
    alert_fields = extract_alert_fields(alert_data)
    if not alert_fields:
        print("ERROR: Failed to extract alert fields", file=sys.stderr)
        sys.exit(1)

    print(f"INFO: Processing alert: {alert_fields.get('title', 'Unknown')}", file=sys.stdout)

    # Send to Slack
    success = send_to_slack(alert_fields)

    if success:
        print("INFO: Alert action completed successfully", file=sys.stdout)
        sys.exit(0)
    else:
        print("ERROR: Alert action failed", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
