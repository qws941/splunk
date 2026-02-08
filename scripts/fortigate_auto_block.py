#!/usr/bin/env python3
"""
FortiGate Auto-Block Script - Correlation Engine Integration
Location: $SPLUNK_HOME/etc/apps/fortigate/bin/fortigate_auto_block.py

Phase 4.1 - Advanced Correlation Engine
Receives correlation detection results from Splunk alert actions and triggers
automated IP blocking on FortiGate via REST API (Phase 3.2 integration).

Workflow:
1. Receive correlation results from Splunk via stdin (alert action)
2. Extract src_ip, correlation_score, correlation_rule
3. Validate against whitelist (fortigate_whitelist.csv)
4. Check if IP already blocked (avoid duplicates)
5. Call FortiGate REST API to create address object & firewall policy
6. Log action to Splunk (_internal index)
7. Send Slack notification (success/failure)

Requirements:
- Phase 3.2: FortiGate API client configured
- Python 3.6+ with requests library
- Environment variables: FORTIGATE_HOST, FORTIGATE_API_KEY
- Whitelist CSV: $SPLUNK_HOME/etc/apps/fortigate/lookups/fortigate_whitelist.csv

Installation:
1. chmod +x $SPLUNK_HOME/etc/apps/fortigate/bin/fortigate_auto_block.py
2. Configure alert action: Settings → Alert Actions → Script
3. Test: splunk cmd python fortigate_auto_block.py < test_input.json

Author: Claude (Phase 4.1 Implementation)
Date: 2025-10-21
"""

import csv
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Third-party imports (fallback for non-Splunk execution)
try:
    import requests
except ImportError:
    # Splunk environment - use built-in http library
    import urllib.error
    import urllib.request as requests

# Splunk SDK imports
try:
    import splunk.Intersplunk as si
except ImportError:
    # Non-Splunk environment - stub for testing
    class DummyIntersplunk:
        def readResults(self):
            return json.load(sys.stdin)

        def outputResults(self, results):
            json.dump(results, sys.stdout)

    si = DummyIntersplunk()

# ============================================================================
# Configuration
# ============================================================================

SPLUNK_HOME = os.environ.get("SPLUNK_HOME", "/opt/splunk")
APP_HOME = Path(SPLUNK_HOME) / "etc" / "apps" / "fortigate"

# FortiGate API Configuration (from environment or splunkenv.conf)
FORTIGATE_HOST = os.environ.get("FORTIGATE_HOST", "192.168.1.99")
FORTIGATE_PORT = int(os.environ.get("FORTIGATE_PORT", "443"))
FORTIGATE_API_KEY = os.environ.get("FORTIGATE_API_KEY", "")
FORTIGATE_VDOM = os.environ.get("FORTIGATE_VDOM", "root")

# Paths
WHITELIST_CSV = APP_HOME / "lookups" / "fortigate_whitelist.csv"
BLOCKED_IPS_CSV = APP_HOME / "lookups" / "fortigate_blocked_ips.csv"
LOG_FILE = APP_HOME / "logs" / "fortigate_auto_block.log"

# Slack webhook (optional - from Phase 3.2)
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# Auto-block thresholds (align with correlation rules)
AUTO_BLOCK_THRESHOLD = 90  # correlation_score >= 90
REVIEW_THRESHOLD = 80  # 80-89 requires manual review

# ============================================================================
# Logging Setup
# ============================================================================

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s action=%(action)s ip=%(ip)s score=%(score)s rule=%(rule)s status=%(status)s message="%(message)s"',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stderr),  # Splunk captures stderr
    ],
)

logger = logging.getLogger(__name__)

# ============================================================================
# Utility Functions
# ============================================================================


def load_whitelist():
    """Load IP whitelist from CSV file."""
    whitelist = set()
    try:
        with open(WHITELIST_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                whitelist.add(row["ip"])
        logger.info(
            "",
            extra={
                "action": "load_whitelist",
                "ip": "-",
                "score": "-",
                "rule": "-",
                "status": "success",
                "message": f"Loaded {len(whitelist)} whitelisted IPs",
            },
        )
    except FileNotFoundError:
        logger.warning(
            "",
            extra={
                "action": "load_whitelist",
                "ip": "-",
                "score": "-",
                "rule": "-",
                "status": "warning",
                "message": "Whitelist file not found - continuing without whitelist",
            },
        )
    return whitelist


def load_blocked_ips():
    """Load already blocked IPs from CSV file."""
    blocked = set()
    try:
        with open(BLOCKED_IPS_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                blocked.add(row["ip"])
        logger.info(
            "",
            extra={
                "action": "load_blocked_ips",
                "ip": "-",
                "score": "-",
                "rule": "-",
                "status": "success",
                "message": f"Loaded {len(blocked)} already blocked IPs",
            },
        )
    except FileNotFoundError:
        # File doesn't exist yet - will be created on first block
        logger.info(
            "",
            extra={
                "action": "load_blocked_ips",
                "ip": "-",
                "score": "-",
                "rule": "-",
                "status": "info",
                "message": "Blocked IPs file not found - creating new tracking file",
            },
        )
    return blocked


def save_blocked_ip(ip, correlation_score, correlation_rule, action_result):
    """Append newly blocked IP to tracking CSV."""
    try:
        BLOCKED_IPS_CSV.parent.mkdir(parents=True, exist_ok=True)
        file_exists = BLOCKED_IPS_CSV.exists()
        with open(BLOCKED_IPS_CSV, "a") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "ip",
                    "blocked_at",
                    "correlation_score",
                    "correlation_rule",
                    "status",
                ],
            )
            if not file_exists:
                writer.writeheader()
            writer.writerow(
                {
                    "ip": ip,
                    "blocked_at": datetime.now().isoformat(),
                    "correlation_score": correlation_score,
                    "correlation_rule": correlation_rule,
                    "status": action_result,
                }
            )
        logger.info(
            "",
            extra={
                "action": "save_blocked_ip",
                "ip": ip,
                "score": correlation_score,
                "rule": correlation_rule,
                "status": "success",
                "message": "Saved to blocked IPs tracking file",
            },
        )
    except Exception as e:
        logger.error(
            "",
            extra={
                "action": "save_blocked_ip",
                "ip": ip,
                "score": correlation_score,
                "rule": correlation_rule,
                "status": "error",
                "message": str(e),
            },
        )


def send_slack_notification(
    ip, correlation_score, correlation_rule, action_result, error_message=None
):
    """Send Slack notification about block action."""
    if not SLACK_WEBHOOK_URL:
        return

    color = "#d93f3c" if action_result == "blocked" else "#f58f39"
    title = (
        f"🚫 Auto-Block: {ip}"
        if action_result == "blocked"
        else f"⚠️ Block Failed: {ip}"
    )

    payload = {
        "attachments": [
            {
                "color": color,
                "title": title,
                "fields": [
                    {"title": "IP Address", "value": ip, "short": True},
                    {
                        "title": "Correlation Score",
                        "value": f"{correlation_score}/100",
                        "short": True,
                    },
                    {
                        "title": "Correlation Rule",
                        "value": correlation_rule,
                        "short": True,
                    },
                    {"title": "Action", "value": action_result, "short": True},
                ],
                "footer": "Phase 4.1 - Correlation Engine",
                "ts": int(datetime.now().timestamp()),
            }
        ]
    }

    if error_message:
        payload["attachments"][0]["fields"].append(
            {"title": "Error", "value": error_message, "short": False}
        )

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code == 200:
            logger.info(
                "",
                extra={
                    "action": "slack_notify",
                    "ip": ip,
                    "score": correlation_score,
                    "rule": correlation_rule,
                    "status": "success",
                    "message": "Slack notification sent",
                },
            )
    except Exception as e:
        logger.error(
            "",
            extra={
                "action": "slack_notify",
                "ip": ip,
                "score": correlation_score,
                "rule": correlation_rule,
                "status": "error",
                "message": str(e),
            },
        )


# ============================================================================
# FortiGate API Client
# ============================================================================


class FortiGateAPIClient:
    """FortiGate REST API client for automated IP blocking (Phase 3.2 integration)."""

    def __init__(self, host, port, api_key, vdom="root"):
        self.base_url = f"https://{host}:{port}/api/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.vdom = vdom
        self.session = requests.Session() if hasattr(requests, "Session") else None
        if self.session:
            self.session.headers.update(self.headers)
            # Disable SSL verification (use environment variable to enable)
            self.session.verify = (
                os.environ.get("FORTIGATE_SSL_VERIFY", "false").lower() == "true"
            )

    def create_address_object(self, ip):
        """Create firewall address object for blocked IP."""
        address_name = f'correlation_blocked_{ip.replace(".", "_")}'
        url = f"{self.base_url}/cmdb/firewall/address"
        params = {"vdom": self.vdom}

        payload = {
            "name": address_name,
            "type": "ipmask",
            "subnet": f"{ip} 255.255.255.255",
            "comment": f'Auto-blocked by Correlation Engine on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        }

        try:
            if self.session:
                response = self.session.post(
                    url, params=params, json=payload, timeout=10
                )
                response.raise_for_status()
            logger.info(
                "",
                extra={
                    "action": "fortigate_create_address",
                    "ip": ip,
                    "score": "-",
                    "rule": "-",
                    "status": "success",
                    "message": f"Created address object: {address_name}",
                },
            )
            return address_name
        except Exception as e:
            logger.error(
                "",
                extra={
                    "action": "fortigate_create_address",
                    "ip": ip,
                    "score": "-",
                    "rule": "-",
                    "status": "error",
                    "message": str(e),
                },
            )
            raise

    def create_deny_policy(self, address_name, ip):
        """Create firewall policy to deny all traffic from IP."""
        policy_name = f'DENY_correlation_{ip.replace(".", "_")}'
        url = f"{self.base_url}/cmdb/firewall/policy"
        params = {"vdom": self.vdom}

        payload = {
            "name": policy_name,
            "srcintf": [{"name": "any"}],
            "dstintf": [{"name": "any"}],
            "srcaddr": [{"name": address_name}],
            "dstaddr": [{"name": "all"}],
            "action": "deny",
            "schedule": "always",
            "service": [{"name": "ALL"}],
            "logtraffic": "all",
            "comments": f'Auto-created by Correlation Engine - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        }

        try:
            if self.session:
                response = self.session.post(
                    url, params=params, json=payload, timeout=10
                )
                response.raise_for_status()
            logger.info(
                "",
                extra={
                    "action": "fortigate_create_policy",
                    "ip": ip,
                    "score": "-",
                    "rule": "-",
                    "status": "success",
                    "message": f"Created deny policy: {policy_name}",
                },
            )
            return policy_name
        except Exception as e:
            logger.error(
                "",
                extra={
                    "action": "fortigate_create_policy",
                    "ip": ip,
                    "score": "-",
                    "rule": "-",
                    "status": "error",
                    "message": str(e),
                },
            )
            raise

    def block_ip(self, ip):
        """Complete workflow: Create address object + deny policy."""
        try:
            address_name = self.create_address_object(ip)
            policy_name = self.create_deny_policy(address_name, ip)
            return {"status": "success", "address": address_name, "policy": policy_name}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# ============================================================================
# Main Processing Logic
# ============================================================================


def process_correlation_results(results):
    """Process correlation detection results and trigger auto-blocking."""
    whitelist = load_whitelist()
    already_blocked = load_blocked_ips()

    # Initialize FortiGate API client
    if not FORTIGATE_API_KEY:
        logger.error(
            "",
            extra={
                "action": "init_api_client",
                "ip": "-",
                "score": "-",
                "rule": "-",
                "status": "error",
                "message": "FORTIGATE_API_KEY not configured - auto-blocking disabled",
            },
        )
        return

    fg_client = FortiGateAPIClient(
        FORTIGATE_HOST, FORTIGATE_PORT, FORTIGATE_API_KEY, FORTIGATE_VDOM
    )

    for result in results:
        src_ip = result.get("src_ip", "")
        correlation_score = float(result.get("correlation_score", 0))
        correlation_rule = result.get("correlation_rule", "unknown")
        action_recommendation = result.get("action_recommendation", "MONITOR")

        # Skip if missing required fields
        if not src_ip:
            logger.warning(
                "",
                extra={
                    "action": "validate_result",
                    "ip": "-",
                    "score": "-",
                    "rule": correlation_rule,
                    "status": "warning",
                    "message": "Missing src_ip field - skipping",
                },
            )
            continue

        # Check whitelist
        if src_ip in whitelist:
            logger.info(
                "",
                extra={
                    "action": "check_whitelist",
                    "ip": src_ip,
                    "score": correlation_score,
                    "rule": correlation_rule,
                    "status": "skipped",
                    "message": "IP is whitelisted - skipping auto-block",
                },
            )
            continue

        # Check if already blocked
        if src_ip in already_blocked:
            logger.info(
                "",
                extra={
                    "action": "check_blocked",
                    "ip": src_ip,
                    "score": correlation_score,
                    "rule": correlation_rule,
                    "status": "skipped",
                    "message": "IP already blocked - skipping duplicate",
                },
            )
            continue

        # Check auto-block threshold
        if (
            action_recommendation != "AUTO_BLOCK"
            or correlation_score < AUTO_BLOCK_THRESHOLD
        ):
            logger.info(
                "",
                extra={
                    "action": "check_threshold",
                    "ip": src_ip,
                    "score": correlation_score,
                    "rule": correlation_rule,
                    "status": "skipped",
                    "message": f"Score {correlation_score} below auto-block threshold {AUTO_BLOCK_THRESHOLD} - manual review required",
                },
            )

            # Send Slack alert for review-required IPs
            if action_recommendation == "REVIEW_AND_BLOCK":
                send_slack_notification(
                    src_ip, correlation_score, correlation_rule, "review_required"
                )
            continue

        # Execute auto-block
        logger.info(
            "",
            extra={
                "action": "auto_block_start",
                "ip": src_ip,
                "score": correlation_score,
                "rule": correlation_rule,
                "status": "processing",
                "message": f"Starting auto-block (score: {correlation_score}, rule: {correlation_rule})",
            },
        )

        block_result = fg_client.block_ip(src_ip)

        if block_result["status"] == "success":
            logger.info(
                "",
                extra={
                    "action": "auto_block_complete",
                    "ip": src_ip,
                    "score": correlation_score,
                    "rule": correlation_rule,
                    "status": "success",
                    "message": f'Successfully blocked IP (address: {block_result["address"]}, policy: {block_result["policy"]})',
                },
            )

            # Save to blocked IPs tracking
            save_blocked_ip(src_ip, correlation_score, correlation_rule, "blocked")

            # Send success notification
            send_slack_notification(
                src_ip, correlation_score, correlation_rule, "blocked"
            )

        else:
            error_msg = block_result.get("error", "Unknown error")
            logger.error(
                "",
                extra={
                    "action": "auto_block_failed",
                    "ip": src_ip,
                    "score": correlation_score,
                    "rule": correlation_rule,
                    "status": "error",
                    "message": error_msg,
                },
            )

            # Send failure notification
            send_slack_notification(
                src_ip, correlation_score, correlation_rule, "failed", error_msg
            )


# ============================================================================
# Entry Point
# ============================================================================


def main():
    """Main entry point for Splunk alert action."""
    try:
        # Read correlation results from Splunk via stdin
        results = si.readResults()

        if not results:
            logger.warning(
                "",
                extra={
                    "action": "read_results",
                    "ip": "-",
                    "score": "-",
                    "rule": "-",
                    "status": "warning",
                    "message": "No results received from Splunk",
                },
            )
            return

        logger.info(
            "",
            extra={
                "action": "read_results",
                "ip": "-",
                "score": "-",
                "rule": "-",
                "status": "success",
                "message": f"Received {len(results)} correlation detection(s) from Splunk",
            },
        )

        # Process correlation results and trigger auto-blocking
        process_correlation_results(results)

        logger.info(
            "",
            extra={
                "action": "processing_complete",
                "ip": "-",
                "score": "-",
                "rule": "-",
                "status": "success",
                "message": "Correlation result processing completed",
            },
        )

    except Exception as e:
        logger.error(
            "",
            extra={
                "action": "main",
                "ip": "-",
                "score": "-",
                "rule": "-",
                "status": "error",
                "message": str(e),
            },
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
