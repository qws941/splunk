#!/usr/bin/env python3
"""
Splunk Alert Action Wrapper for FortiGate Auto-Block

This script is called by Splunk when an alert fires. It reads alert data
from stdin and calls fortigate_auto_block.py to block the IP address.

Installation:
1. Copy to $SPLUNK_HOME/etc/apps/fortigate/bin/splunk-auto-block-wrapper.py
2. chmod +x splunk-auto-block-wrapper.py
3. Configure alert action in savedsearches.conf

Usage (by Splunk):
  echo '{"result":{"srcip":"192.168.1.100","reason":"High-risk IP"}}' | python3 splunk-auto-block-wrapper.py

Phase 3.2 - Automated Response Actions
"""

import json
import os
import subprocess
import sys

# Path to main auto-block script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUTO_BLOCK_SCRIPT = os.path.join(SCRIPT_DIR, "fortigate_auto_block.py")


def read_alert_data():
    """Read alert data from Splunk stdin"""
    try:
        alert_data = json.loads(sys.stdin.read())
        return alert_data
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse alert data: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: Failed to read alert data: {e}", file=sys.stderr)
        return None


def extract_ip_and_reason(alert_data):
    """Extract IP address and reason from alert data"""
    result = alert_data.get("result", {})

    # Try common field names for IP address
    ip_address = (
        result.get("srcip")
        or result.get("src_ip")
        or result.get("ip")
        or result.get("source_ip")
    )

    # Try common field names for reason
    reason = (
        result.get("reason")
        or result.get("description")
        or result.get("message")
        or "Malicious activity detected"
    )

    return ip_address, reason


def call_auto_block(ip_address, reason):
    """Call fortigate_auto_block.py to block the IP"""
    try:
        cmd = [
            "python3",
            AUTO_BLOCK_SCRIPT,
            "--action",
            "block",
            "--ip",
            ip_address,
            "--reason",
            reason,
            "--source",
            "splunk",
        ]

        # Note: approval_required is set to False for automated alerts
        # For manual approval, set to True in savedsearches.conf

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        print(f"STDOUT: {result.stdout}", file=sys.stderr)
        print(f"STDERR: {result.stderr}", file=sys.stderr)
        print(f"Return Code: {result.returncode}", file=sys.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"ERROR: Auto-block script timed out after 120 seconds", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: Failed to call auto-block script: {e}", file=sys.stderr)
        return False


def main():
    """Main execution"""
    print(f"INFO: Splunk Auto-Block Wrapper started", file=sys.stderr)

    # Read alert data from stdin
    alert_data = read_alert_data()
    if not alert_data:
        print(f"ERROR: No alert data received", file=sys.stderr)
        sys.exit(1)

    print(f"INFO: Alert data: {json.dumps(alert_data)}", file=sys.stderr)

    # Extract IP and reason
    ip_address, reason = extract_ip_and_reason(alert_data)

    if not ip_address:
        print(f"ERROR: No IP address found in alert data", file=sys.stderr)
        print(
            f"   Available fields: {list(alert_data.get('result', {}).keys())}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"INFO: IP to block: {ip_address}", file=sys.stderr)
    print(f"INFO: Reason: {reason}", file=sys.stderr)

    # Call auto-block script
    success = call_auto_block(ip_address, reason)

    if success:
        print(f"SUCCESS: IP {ip_address} blocked successfully", file=sys.stderr)
        sys.exit(0)
    else:
        print(f"ERROR: Failed to block IP {ip_address}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
