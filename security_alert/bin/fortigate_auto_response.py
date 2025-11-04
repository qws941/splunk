#!/usr/bin/env python3
"""
FortiGate Automated Response System
Purpose: Execute automated remediation actions based on Splunk alerts
Integration: Splunk Alert Actions, FortiManager API, Slack API
Version: 1.0.0
"""

import sys
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
FORTIMANAGER_URL = "https://fmg.example.com"
FORTIMANAGER_TOKEN = "YOUR_FMG_API_TOKEN"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/splunk/var/log/splunk/auto_response.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)


class FortiManagerAPI:
    """FortiManager REST API client for automated actions"""

    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })

    def add_address_blacklist(self, ip_address: str, description: str) -> Dict:
        """Add IP to FortiGate address blacklist"""
        endpoint = f"{self.url}/api/v2/cmdb/firewall/address"
        payload = {
            "name": f"blacklist_{ip_address.replace('.', '_')}",
            "type": "ipmask",
            "subnet": f"{ip_address}/32",
            "comment": f"Auto-blocked by Splunk: {description}"
        }

        try:
            response = self.session.post(endpoint, json=payload, verify=False, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully added {ip_address} to blacklist")
            return {"status": "success", "ip": ip_address}
        except Exception as e:
            logger.error(f"Failed to add {ip_address} to blacklist: {e}")
            return {"status": "error", "message": str(e)}

    def apply_bandwidth_limit(self, source_ip: str, limit_mbps: int) -> Dict:
        """Apply traffic shaping to source IP"""
        endpoint = f"{self.url}/api/v2/cmdb/firewall/shaping-policy"
        payload = {
            "srcaddr": source_ip,
            "traffic-shaper": f"limit_{limit_mbps}mbps",
            "comment": f"Auto-applied bandwidth limit: {limit_mbps} Mbps"
        }

        try:
            response = self.session.post(endpoint, json=payload, verify=False, timeout=10)
            response.raise_for_status()
            logger.info(f"Applied {limit_mbps} Mbps limit to {source_ip}")
            return {"status": "success", "ip": source_ip, "limit": limit_mbps}
        except Exception as e:
            logger.error(f"Failed to apply bandwidth limit to {source_ip}: {e}")
            return {"status": "error", "message": str(e)}

    def disable_admin_account(self, username: str) -> Dict:
        """Disable admin account"""
        endpoint = f"{self.url}/api/v2/cmdb/system/admin/{username}"
        payload = {"accprofile-override": "enable", "accprofile": "no-access"}

        try:
            response = self.session.put(endpoint, json=payload, verify=False, timeout=10)
            response.raise_for_status()
            logger.warning(f"Disabled admin account: {username}")
            return {"status": "success", "user": username}
        except Exception as e:
            logger.error(f"Failed to disable admin account {username}: {e}")
            return {"status": "error", "message": str(e)}


class SlackNotifier:
    """Slack notification handler"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_notification(self, alert_name: str, action_taken: str, details: Dict) -> bool:
        """Send Slack notification about automated action"""
        message = {
            "text": f"🤖 *Automated Response Executed*",
            "attachments": [{
                "color": "warning",
                "fields": [
                    {"title": "Alert", "value": alert_name, "short": True},
                    {"title": "Action", "value": action_taken, "short": True},
                    {"title": "Details", "value": json.dumps(details, indent=2), "short": False},
                    {"title": "Timestamp", "value": datetime.now().isoformat(), "short": True}
                ]
            }]
        }

        try:
            response = requests.post(self.webhook_url, json=message, timeout=5)
            response.raise_for_status()
            logger.info(f"Slack notification sent for {alert_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class AutoResponseEngine:
    """Main automated response orchestrator"""

    def __init__(self):
        self.fmg_api = FortiManagerAPI(FORTIMANAGER_URL, FORTIMANAGER_TOKEN)
        self.slack = SlackNotifier(SLACK_WEBHOOK_URL)
        self.action_log = []

    def execute_action(self, alert_data: Dict) -> Dict:
        """Execute automated response based on alert type"""
        alert_name = alert_data.get('search_name', 'Unknown')
        action_type = alert_data.get('action_type', 'notification_only')

        logger.info(f"Processing alert: {alert_name}, action: {action_type}")

        # Map alert names to action handlers
        action_handlers = {
            '013_SSL_VPN_Brute_Force': self._handle_brute_force,
            '015_Abnormal_Traffic_Spike': self._handle_traffic_spike,
            '011_Admin_Login_Failed': self._handle_admin_login_failed
        }

        handler = action_handlers.get(alert_name)
        if handler:
            result = handler(alert_data)
        else:
            result = self._handle_notification_only(alert_data)

        # Send Slack notification
        self.slack.send_notification(alert_name, action_type, result)

        # Log action
        self.action_log.append({
            'timestamp': datetime.now().isoformat(),
            'alert': alert_name,
            'action': action_type,
            'result': result
        })

        return result

    def _handle_brute_force(self, alert_data: Dict) -> Dict:
        """Handle SSL VPN brute force attacks"""
        source_ip = alert_data.get('source_ip', 'unknown')
        fail_count = alert_data.get('fail_count', 0)

        if fail_count >= 10:
            # Auto-block if >= 10 failed attempts
            result = self.fmg_api.add_address_blacklist(
                source_ip,
                f"Brute force attack: {fail_count} failed attempts"
            )
            return result
        else:
            return {"status": "monitoring", "ip": source_ip, "count": fail_count}

    def _handle_traffic_spike(self, alert_data: Dict) -> Dict:
        """Handle abnormal traffic spikes"""
        source_ip = alert_data.get('source_ip', 'unknown')
        spike_multiplier = alert_data.get('spike_multiplier', 1)

        if spike_multiplier >= 5:
            # Apply bandwidth limit for 5x spikes
            result = self.fmg_api.apply_bandwidth_limit(source_ip, limit_mbps=10)
            return result
        else:
            return {"status": "monitoring", "ip": source_ip, "multiplier": spike_multiplier}

    def _handle_admin_login_failed(self, alert_data: Dict) -> Dict:
        """Handle admin login failures"""
        source_ip = alert_data.get('source_ip', 'unknown')
        fail_count = alert_data.get('fail_count', 0)
        user = alert_data.get('user', 'unknown')

        if fail_count >= 5:
            # Disable account after 5 failures
            result = self.fmg_api.disable_admin_account(user)
            result['source_ip'] = source_ip
            return result
        else:
            return {"status": "monitoring", "user": user, "count": fail_count}

    def _handle_notification_only(self, alert_data: Dict) -> Dict:
        """Default handler - notification only, no automated action"""
        return {"status": "notified", "action": "none"}


def main():
    """Main entry point for Splunk alert action"""
    try:
        # Read alert data from stdin (Splunk passes JSON)
        alert_data = json.loads(sys.stdin.read())

        # Initialize engine
        engine = AutoResponseEngine()

        # Execute automated response
        result = engine.execute_action(alert_data)

        # Output result
        print(json.dumps({
            'status': 'success',
            'result': result,
            'timestamp': datetime.now().isoformat()
        }))

        sys.exit(0)

    except Exception as e:
        logger.error(f"Auto-response execution failed: {e}")
        print(json.dumps({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()
