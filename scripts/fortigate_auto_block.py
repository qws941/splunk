#!/usr/bin/env python3
"""
FortiGate Automated IP Blocking Script

Automatically blocks malicious IP addresses on FortiGate firewall via REST API.
Designed to run as Splunk Alert Action or standalone script.

Features:
- IP blocking (create address object + deny policy)
- IP unblocking (delete policy + address object)
- Whitelist checking (trusted IPs never blocked)
- Approval workflow (manual approval before blocking)
- Slack notification integration
- Audit logging
- Scheduled auto-unblock after 24 hours

Usage:
  python3 fortigate_auto_block.py --action block --ip 192.168.1.100
  python3 fortigate_auto_block.py --action unblock --ip 192.168.1.100
  python3 fortigate_auto_block.py --action list-blocked
  python3 fortigate_auto_block.py --source splunk --approval-required

Phase 3.2 - Automated Response Actions
"""

import os
import sys
import json
import argparse
import csv
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import ssl

# Configuration
FORTIGATE_HOST = os.environ.get('FORTIGATE_HOST', 'fortigate.jclee.me')
FORTIGATE_PORT = int(os.environ.get('FORTIGATE_PORT', '443'))
FORTIGATE_API_TOKEN = os.environ.get('FORTIGATE_API_TOKEN', '')
FORTIGATE_VDOM = os.environ.get('FORTIGATE_VDOM', 'root')

WHITELIST_FILE = os.path.join(os.path.dirname(__file__), '../lookups/ip_whitelist.csv')
BLOCKED_IPS_FILE = os.path.join(os.path.dirname(__file__), '../lookups/blocked_ips.csv')
AUDIT_LOG_FILE = os.path.join(os.path.dirname(__file__), '../logs/fortigate_auto_block.log')

SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', '')

AUTO_UNBLOCK_HOURS = int(os.environ.get('AUTO_UNBLOCK_HOURS', '24'))

# Address Group for Auto-Blocked IPs
AUTO_BLOCK_GROUP_NAME = "Auto_Blocked_IPs"

class FortiGateAPIClient:
    """FortiGate REST API Client"""

    def __init__(self, host, port, api_token, vdom='root'):
        self.host = host
        self.port = port
        self.api_token = api_token
        self.vdom = vdom
        self.base_url = f"https://{host}:{port}/api/v2/cmdb"

        # SSL context (skip verification for self-signed certs)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def _make_request(self, method, endpoint, data=None):
        """Make HTTP request to FortiGate API"""
        url = f"{self.base_url}/{endpoint}?vdom={self.vdom}"

        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        req = Request(url, headers=headers, method=method)

        if data:
            req.data = json.dumps(data).encode('utf-8')

        try:
            with urlopen(req, context=self.ssl_context, timeout=30) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data) if response_data else {}
        except HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"ERROR: HTTP {e.code} {e.reason}: {error_body}", file=sys.stderr)
            return None
        except URLError as e:
            print(f"ERROR: Network error: {e.reason}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"ERROR: Request failed: {e}", file=sys.stderr)
            return None

    def create_address_object(self, name, ip_address, comment=''):
        """Create firewall address object"""
        endpoint = "firewall/address"
        data = {
            "name": name,
            "subnet": f"{ip_address}/32",
            "type": "ipmask",
            "comment": comment or f"Auto-blocked by Splunk at {datetime.now().isoformat()}"
        }

        print(f"INFO: Creating address object '{name}' for IP {ip_address}", file=sys.stderr)
        result = self._make_request('POST', endpoint, data)

        if result and result.get('http_status') == 200:
            print(f"SUCCESS: Address object '{name}' created", file=sys.stderr)
            return True
        else:
            print(f"ERROR: Failed to create address object '{name}'", file=sys.stderr)
            return False

    def delete_address_object(self, name):
        """Delete firewall address object"""
        endpoint = f"firewall/address/{name}"

        print(f"INFO: Deleting address object '{name}'", file=sys.stderr)
        result = self._make_request('DELETE', endpoint)

        if result and result.get('http_status') == 200:
            print(f"SUCCESS: Address object '{name}' deleted", file=sys.stderr)
            return True
        else:
            print(f"WARNING: Address object '{name}' may not exist or already deleted", file=sys.stderr)
            return False

    def create_deny_policy(self, policy_id, src_addr_name, comment=''):
        """Create firewall deny policy"""
        endpoint = "firewall/policy"
        data = {
            "policyid": policy_id,
            "name": f"Auto_Block_{policy_id}",
            "srcintf": [{"name": "any"}],
            "dstintf": [{"name": "any"}],
            "srcaddr": [{"name": src_addr_name}],
            "dstaddr": [{"name": "all"}],
            "action": "deny",
            "schedule": "always",
            "service": [{"name": "ALL"}],
            "logtraffic": "all",
            "comments": comment or f"Auto-blocked by Splunk at {datetime.now().isoformat()}",
            "status": "enable"
        }

        print(f"INFO: Creating deny policy {policy_id} for '{src_addr_name}'", file=sys.stderr)
        result = self._make_request('POST', endpoint, data)

        if result and result.get('http_status') == 200:
            print(f"SUCCESS: Deny policy {policy_id} created", file=sys.stderr)
            return True
        else:
            print(f"ERROR: Failed to create deny policy {policy_id}", file=sys.stderr)
            return False

    def delete_policy(self, policy_id):
        """Delete firewall policy"""
        endpoint = f"firewall/policy/{policy_id}"

        print(f"INFO: Deleting policy {policy_id}", file=sys.stderr)
        result = self._make_request('DELETE', endpoint)

        if result and result.get('http_status') == 200:
            print(f"SUCCESS: Policy {policy_id} deleted", file=sys.stderr)
            return True
        else:
            print(f"WARNING: Policy {policy_id} may not exist or already deleted", file=sys.stderr)
            return False

    def get_next_available_policy_id(self):
        """Get next available policy ID"""
        endpoint = "firewall/policy"

        result = self._make_request('GET', endpoint)

        if result and 'results' in result:
            policy_ids = [int(p['policyid']) for p in result['results'] if 'policyid' in p]
            next_id = max(policy_ids) + 1 if policy_ids else 1000
            print(f"INFO: Next available policy ID: {next_id}", file=sys.stderr)
            return next_id
        else:
            print(f"WARNING: Could not determine next policy ID, using 1000", file=sys.stderr)
            return 1000


def is_whitelisted(ip_address):
    """Check if IP is in whitelist"""
    if not os.path.exists(WHITELIST_FILE):
        print(f"INFO: Whitelist file not found: {WHITELIST_FILE}", file=sys.stderr)
        return False

    with open(WHITELIST_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('ip') and row['ip'] == ip_address:
                print(f"INFO: IP {ip_address} is whitelisted", file=sys.stderr)
                return True

    return False


def is_already_blocked(ip_address):
    """Check if IP is already blocked"""
    if not os.path.exists(BLOCKED_IPS_FILE):
        return False

    with open(BLOCKED_IPS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('ip') and row['ip'] == ip_address:
                return True

    return False


def add_to_blocked_list(ip_address, reason, policy_id, unblock_time):
    """Add IP to blocked IPs CSV"""
    os.makedirs(os.path.dirname(BLOCKED_IPS_FILE), exist_ok=True)

    # Check if file exists and has header
    file_exists = os.path.exists(BLOCKED_IPS_FILE)

    with open(BLOCKED_IPS_FILE, 'a', newline='') as f:
        fieldnames = ['ip', 'blocked_at', 'unblock_at', 'reason', 'policy_id', 'blocked_by']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'ip': ip_address,
            'blocked_at': datetime.now().isoformat(),
            'unblock_at': unblock_time.isoformat(),
            'reason': reason,
            'policy_id': policy_id,
            'blocked_by': 'Splunk Auto-Block'
        })

    print(f"SUCCESS: Added {ip_address} to blocked list", file=sys.stderr)


def remove_from_blocked_list(ip_address):
    """Remove IP from blocked IPs CSV"""
    if not os.path.exists(BLOCKED_IPS_FILE):
        return

    # Read all rows except the one to remove
    rows = []
    with open(BLOCKED_IPS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader if row.get('ip') != ip_address]

    # Write back
    with open(BLOCKED_IPS_FILE, 'w', newline='') as f:
        fieldnames = ['ip', 'blocked_at', 'unblock_at', 'reason', 'policy_id', 'blocked_by']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"SUCCESS: Removed {ip_address} from blocked list", file=sys.stderr)


def send_slack_notification(message, color='#DC143C'):
    """Send Slack notification via webhook"""
    if not SLACK_WEBHOOK_URL:
        print("INFO: Slack webhook URL not configured, skipping notification", file=sys.stderr)
        return

    payload = {
        "attachments": [{
            "color": color,
            "text": message,
            "footer": "FortiGate Auto-Block System",
            "ts": int(datetime.now().timestamp())
        }]
    }

    try:
        req = Request(SLACK_WEBHOOK_URL, headers={'Content-Type': 'application/json'})
        req.data = json.dumps(payload).encode('utf-8')

        with urlopen(req, timeout=10) as response:
            if response.status == 200:
                print("SUCCESS: Slack notification sent", file=sys.stderr)
            else:
                print(f"WARNING: Slack notification failed: HTTP {response.status}", file=sys.stderr)
    except Exception as e:
        print(f"WARNING: Failed to send Slack notification: {e}", file=sys.stderr)


def audit_log(action, ip_address, status, details=''):
    """Write audit log entry"""
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'ip': ip_address,
        'status': status,
        'details': details
    }

    with open(AUDIT_LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


def block_ip(ip_address, reason='Malicious activity detected', approval_required=False):
    """Block IP address on FortiGate"""

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"🚫 BLOCKING IP: {ip_address}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    # Safety check: whitelist
    if is_whitelisted(ip_address):
        print(f"⚠️  BLOCKED: IP {ip_address} is whitelisted", file=sys.stderr)
        audit_log('block_attempt', ip_address, 'denied', 'IP is whitelisted')
        return False

    # Safety check: already blocked
    if is_already_blocked(ip_address):
        print(f"⚠️  SKIPPED: IP {ip_address} is already blocked", file=sys.stderr)
        audit_log('block_attempt', ip_address, 'denied', 'IP already blocked')
        return False

    # Approval workflow
    if approval_required:
        print(f"\n⏸️  APPROVAL REQUIRED for blocking {ip_address}", file=sys.stderr)
        print(f"   Reason: {reason}", file=sys.stderr)
        print(f"   Continue? (yes/no): ", file=sys.stderr, end='')
        approval = input().strip().lower()

        if approval != 'yes':
            print(f"❌ CANCELLED: IP {ip_address} block cancelled by user", file=sys.stderr)
            audit_log('block_attempt', ip_address, 'cancelled', 'User denied approval')
            return False

    # Initialize FortiGate API client
    client = FortiGateAPIClient(FORTIGATE_HOST, FORTIGATE_PORT, FORTIGATE_API_TOKEN, FORTIGATE_VDOM)

    # Get next available policy ID
    policy_id = client.get_next_available_policy_id()
    address_name = f"Auto_Blocked_{ip_address.replace('.', '_')}"

    # Step 1: Create address object
    if not client.create_address_object(address_name, ip_address, reason):
        audit_log('block', ip_address, 'failed', 'Address object creation failed')
        return False

    # Step 2: Create deny policy
    if not client.create_deny_policy(policy_id, address_name, reason):
        # Rollback: delete address object
        client.delete_address_object(address_name)
        audit_log('block', ip_address, 'failed', 'Deny policy creation failed')
        return False

    # Step 3: Add to blocked list
    unblock_time = datetime.now() + timedelta(hours=AUTO_UNBLOCK_HOURS)
    add_to_blocked_list(ip_address, reason, policy_id, unblock_time)

    # Step 4: Send Slack notification
    slack_message = f"🚫 *IP BLOCKED ON FORTIGATE*\n\n" \
                    f"*IP Address:* `{ip_address}`\n" \
                    f"*Reason:* {reason}\n" \
                    f"*Policy ID:* {policy_id}\n" \
                    f"*Auto-Unblock:* {unblock_time.strftime('%Y-%m-%d %H:%M:%S')} (in {AUTO_UNBLOCK_HOURS}h)"

    send_slack_notification(slack_message, color='#DC143C')

    # Audit log
    audit_log('block', ip_address, 'success', f'Policy ID: {policy_id}, Unblock: {unblock_time.isoformat()}')

    print(f"\n✅ SUCCESS: IP {ip_address} blocked (Policy ID: {policy_id})", file=sys.stderr)
    print(f"   Auto-unblock scheduled: {unblock_time.strftime('%Y-%m-%d %H:%M:%S')}\n", file=sys.stderr)

    return True


def unblock_ip(ip_address):
    """Unblock IP address on FortiGate"""

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"✅ UNBLOCKING IP: {ip_address}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)

    # Check if IP is in blocked list
    if not is_already_blocked(ip_address):
        print(f"⚠️  SKIPPED: IP {ip_address} is not in blocked list", file=sys.stderr)
        return False

    # Get policy ID from blocked list
    policy_id = None
    with open(BLOCKED_IPS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('ip') == ip_address:
                policy_id = row.get('policy_id')
                break

    if not policy_id:
        print(f"ERROR: Could not find policy ID for {ip_address}", file=sys.stderr)
        return False

    # Initialize FortiGate API client
    client = FortiGateAPIClient(FORTIGATE_HOST, FORTIGATE_PORT, FORTIGATE_API_TOKEN, FORTIGATE_VDOM)

    address_name = f"Auto_Blocked_{ip_address.replace('.', '_')}"

    # Step 1: Delete deny policy
    client.delete_policy(policy_id)

    # Step 2: Delete address object
    client.delete_address_object(address_name)

    # Step 3: Remove from blocked list
    remove_from_blocked_list(ip_address)

    # Step 4: Send Slack notification
    slack_message = f"✅ *IP UNBLOCKED ON FORTIGATE*\n\n" \
                    f"*IP Address:* `{ip_address}`\n" \
                    f"*Policy ID:* {policy_id}\n" \
                    f"*Unblocked At:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    send_slack_notification(slack_message, color='#28A745')

    # Audit log
    audit_log('unblock', ip_address, 'success', f'Policy ID: {policy_id}')

    print(f"\n✅ SUCCESS: IP {ip_address} unblocked\n", file=sys.stderr)

    return True


def list_blocked_ips():
    """List all currently blocked IPs"""
    if not os.path.exists(BLOCKED_IPS_FILE):
        print("INFO: No blocked IPs found", file=sys.stderr)
        return []

    blocked_ips = []
    with open(BLOCKED_IPS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            blocked_ips.append(row)

    print(f"\n{'='*80}", file=sys.stderr)
    print(f"📋 CURRENTLY BLOCKED IPs ({len(blocked_ips)} total)", file=sys.stderr)
    print(f"{'='*80}\n", file=sys.stderr)

    for ip_data in blocked_ips:
        print(f"IP: {ip_data['ip']}", file=sys.stderr)
        print(f"  Blocked At: {ip_data['blocked_at']}", file=sys.stderr)
        print(f"  Unblock At: {ip_data['unblock_at']}", file=sys.stderr)
        print(f"  Reason: {ip_data['reason']}", file=sys.stderr)
        print(f"  Policy ID: {ip_data['policy_id']}", file=sys.stderr)
        print(f"", file=sys.stderr)

    return blocked_ips


def check_auto_unblock():
    """Check for IPs that should be auto-unblocked"""
    if not os.path.exists(BLOCKED_IPS_FILE):
        return

    now = datetime.now()
    to_unblock = []

    with open(BLOCKED_IPS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            unblock_time = datetime.fromisoformat(row['unblock_at'])
            if now >= unblock_time:
                to_unblock.append(row['ip'])

    print(f"INFO: Found {len(to_unblock)} IPs to auto-unblock", file=sys.stderr)

    for ip in to_unblock:
        print(f"INFO: Auto-unblocking {ip}...", file=sys.stderr)
        unblock_ip(ip)


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='FortiGate Automated IP Blocking')
    parser.add_argument('--action', choices=['block', 'unblock', 'list-blocked', 'check-auto-unblock'],
                       required=True, help='Action to perform')
    parser.add_argument('--ip', help='IP address to block/unblock')
    parser.add_argument('--reason', default='Malicious activity detected',
                       help='Reason for blocking (default: Malicious activity detected)')
    parser.add_argument('--approval-required', action='store_true',
                       help='Require manual approval before blocking')
    parser.add_argument('--source', choices=['cli', 'splunk'], default='cli',
                       help='Source of execution (default: cli)')

    args = parser.parse_args()

    # Validate environment variables
    if not FORTIGATE_API_TOKEN:
        print("ERROR: FORTIGATE_API_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Execute action
    if args.action == 'block':
        if not args.ip:
            print("ERROR: --ip required for block action", file=sys.stderr)
            sys.exit(1)

        success = block_ip(args.ip, args.reason, args.approval_required)
        sys.exit(0 if success else 1)

    elif args.action == 'unblock':
        if not args.ip:
            print("ERROR: --ip required for unblock action", file=sys.stderr)
            sys.exit(1)

        success = unblock_ip(args.ip)
        sys.exit(0 if success else 1)

    elif args.action == 'list-blocked':
        list_blocked_ips()
        sys.exit(0)

    elif args.action == 'check-auto-unblock':
        check_auto_unblock()
        sys.exit(0)


if __name__ == '__main__':
    main()
