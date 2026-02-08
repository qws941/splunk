#!/usr/bin/env python3
"""
Splunk Alert Deployment via REST API
Purpose: Terraform-equivalent deployment using only Python + REST API
Usage: python3 scripts/deploy-with-rest-api.py
"""

import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================

SPLUNK_URL = "https://localhost:8089"
SPLUNK_USER = "admin"
SPLUNK_PASS = "changeme"
HEC_PORT = "8088"
INDEX_NAME = "fortianalyzer"
SLACK_CHANNEL = "#security-firewall-alert"

# Alert definitions (same as Terraform)
ALERTS = [
    {
        "name": "FortiGate_Config_Change_Alert",
        "search": f"""index={INDEX_NAME} earliest=rt-30s latest=rt type=event subtype=system
  (logid=0100044546 OR logid=0100044547)
  (cfgpath="firewall.policy*" OR cfgpath="firewall.address*" OR
   cfgpath="firewall.service*" OR cfgpath="system.interface*" OR
   cfgpath="router.static*" OR cfgpath="vpn.ipsec*")
| dedup devname, user, cfgpath
| eval details = case(
    isnull(cfgattr), "No details available",
    1=1, substr(cfgattr, 1, 100))
| eval alert_message = "🔥 FortiGate Config Change - Device: " + devname +
    " | Admin: " + user + " (" + ui + ") | " +
    "Path: " + cfgpath + " | Object: " + cfgobj + " | " +
    "Details: " + details
| table alert_message""",
        "suppress_fields": "user,cfgpath",
        "description": "FortiGate configuration changes via CLI or GUI",
    },
    {
        "name": "FortiGate_Critical_Event_Alert",
        "search": f"""index={INDEX_NAME} earliest=rt-30s latest=rt type=event subtype=system level=critical
  logid!=0100044546 logid!=0100044547
| search NOT msg="*Update Fail*"
| dedup devname, logid
| eval alert_message = "🚨 FortiGate CRITICAL Event - Device: " + devname +
    " | LogID: " + logid + " | Severity: " + level + " | " +
    "Description: " + msg
| table alert_message""",
        "suppress_fields": "devname",
        "description": "Critical system events (memory, CPU, crashes)",
    },
    {
        "name": "FortiGate_HA_Event_Alert",
        "search": f"""index={INDEX_NAME} earliest=rt-30s latest=rt type=event subtype=system logid=0103*
| dedup devname, logid, level
| eval icon = case(
    level="critical", "🔴",
    level="error", "🟠",
    level="warning", "🟡",
    1=1, "🔵")
| eval alert_message = icon + " FortiGate HA Event - Device: " + devname +
    " | Severity: " + level + " | LogID: " + logid + " | " +
    "Description: " + msg
| table alert_message""",
        "suppress_fields": "devname",
        "description": "High Availability failover and sync events",
    },
]

# ============================================================================
# Helper Functions
# ============================================================================

# SSL context for self-signed certificates
ssl_context = ssl._create_unverified_context()


def make_request(endpoint, method="GET", data=None, parse_json=True):
    """Make authenticated request to Splunk REST API"""
    url = f"{SPLUNK_URL}{endpoint}"

    # Create password manager
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, SPLUNK_USER, SPLUNK_PASS)

    # Create auth handler
    auth_handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    opener = urllib.request.build_opener(
        auth_handler, urllib.request.HTTPSHandler(context=ssl_context)
    )

    # Prepare request
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    if data:
        if isinstance(data, dict):
            data = urllib.parse.urlencode(data).encode("utf-8")
        elif isinstance(data, str):
            data = data.encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        response = opener.open(req)
        content = response.read().decode("utf-8")

        if parse_json and content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content
        return content
    except urllib.error.HTTPError as e:
        if e.code in [200, 201, 409]:  # 409 = already exists (OK)
            return e.read().decode("utf-8")
        print(f"❌ HTTP Error {e.code}: {e.read().decode('utf-8')}")
        raise
    except Exception as e:
        print(f"❌ Request failed: {e}")
        raise


def print_step(step_num, total, message):
    """Print formatted step message"""
    print(f"\n{'='*60}")
    print(f"[{step_num}/{total}] {message}")
    print("=" * 60)


# ============================================================================
# Deployment Steps
# ============================================================================


def step1_verify_splunk():
    """Verify Splunk is accessible"""
    print_step(1, 6, "Verifying Splunk Connectivity")

    try:
        result = make_request("/services/server/info", parse_json=False)
        if "version" in result:
            print("✅ Splunk REST API accessible")
            # Extract version
            import re

            version_match = re.search(r'<s:key name="version">([^<]+)</s:key>', result)
            if version_match:
                print(f"   Splunk version: {version_match.group(1)}")
            return True
    except Exception as e:
        print(f"❌ Cannot connect to Splunk: {e}")
        return False


def step2_enable_hec():
    """Enable HEC globally"""
    print_step(2, 6, "Enabling HTTP Event Collector (HEC)")

    data = {"disabled": "0", "enableSSL": "1", "port": HEC_PORT}

    try:
        make_request(
            "/servicesNS/nobody/splunk_httpinput/data/inputs/http/http",
            method="POST",
            data=data,
            parse_json=False,
        )
        print("✅ HEC enabled globally")
        print(f"   Port: {HEC_PORT}")
        return True
    except Exception as e:
        if "409" in str(e):
            print("✅ HEC already enabled")
            return True
        print(f"❌ Failed to enable HEC: {e}")
        return False


def step3_create_hec_token():
    """Create HEC token for FortiGate events"""
    print_step(3, 6, "Creating HEC Token")

    token_name = "fortigate-rest-api-test"

    data = {
        "name": token_name,
        "index": INDEX_NAME,
        "source": "fortigate:hec",
        "sourcetype": "fortigate:event",
        "disabled": "0",
        "useACK": "0",
    }

    try:
        result = make_request(
            "/servicesNS/nobody/splunk_httpinput/data/inputs/http",
            method="POST",
            data=data,
            parse_json=False,
        )

        # Extract token from response
        import re

        token_match = re.search(r'<s:key name="token">([^<]+)</s:key>', result)

        if token_match:
            token = token_match.group(1)
            print(f"✅ HEC token created: {token[:8]}...{token[-4:]}")
            print(f"   Full token: {token}")
            return token
        else:
            print("⚠️  Token created but couldn't extract value")
            # Try to get existing token
            get_result = make_request(
                f"/servicesNS/nobody/splunk_httpinput/data/inputs/http/{token_name}",
                parse_json=False,
            )
            token_match = re.search(r'<s:key name="token">([^<]+)</s:key>', get_result)
            if token_match:
                token = token_match.group(1)
                print(f"✅ Retrieved existing token: {token[:8]}...{token[-4:]}")
                return token
            return None
    except Exception as e:
        if "409" in str(e):
            print("⚠️  HEC token already exists, retrieving...")
            # Get existing token
            get_result = make_request(
                f"/servicesNS/nobody/splunk_httpinput/data/inputs/http/{token_name}",
                parse_json=False,
            )
            import re

            token_match = re.search(r'<s:key name="token">([^<]+)</s:key>', get_result)
            if token_match:
                token = token_match.group(1)
                print(f"✅ Using existing token: {token[:8]}...{token[-4:]}")
                return token
        print(f"❌ Failed to create HEC token: {e}")
        return None


def step4_create_index():
    """Create fortianalyzer index"""
    print_step(4, 6, "Creating Splunk Index")

    data = {
        "name": INDEX_NAME,
        "datatype": "event",
        "maxTotalDataSizeMB": "500000",
        "frozenTimePeriodInSecs": "188697600",  # 6 years
    }

    try:
        make_request(
            "/servicesNS/nobody/system/data/indexes",
            method="POST",
            data=data,
            parse_json=False,
        )
        print(f"✅ Index '{INDEX_NAME}' created")
        return True
    except Exception as e:
        if "409" in str(e):
            print(f"✅ Index '{INDEX_NAME}' already exists")
            return True
        print(f"❌ Failed to create index: {e}")
        return False


def step5_deploy_alerts():
    """Deploy all 3 FortiGate alerts"""
    print_step(5, 6, "Deploying FortiGate Alerts (3)")

    deployed_count = 0

    for alert in ALERTS:
        print(f"\n📝 Deploying: {alert['name']}")

        data = {
            "name": alert["name"],
            "search": alert["search"],
            "disabled": "0",
            "is_scheduled": "1",
            "realtime_schedule": "1",
            "cron_schedule": "* * * * *",
            "alert_type": "number of events",
            "alert_comparator": "greater than",
            "alert_threshold": "0",
            "alert.suppress": "1",
            "alert.suppress.period": "15s",
            "alert.suppress.fields": alert["suppress_fields"],
            "action.slack": "1",
            "action.slack.param.channel": SLACK_CHANNEL,
            "action.slack.param.message": "$result.alert_message$",
            "description": alert["description"],
        }

        try:
            make_request(
                "/servicesNS/nobody/search/saved/searches",
                method="POST",
                data=data,
                parse_json=False,
            )
            print(f"   ✅ Alert deployed")
            deployed_count += 1
        except Exception as e:
            if "409" in str(e):
                print(f"   ⚠️  Alert already exists, updating...")
                # Try to update existing alert
                try:
                    make_request(
                        f"/servicesNS/nobody/search/saved/searches/{alert['name']}",
                        method="POST",
                        data=data,
                        parse_json=False,
                    )
                    print(f"   ✅ Alert updated")
                    deployed_count += 1
                except Exception as update_error:
                    print(f"   ❌ Failed to update: {update_error}")
            else:
                print(f"   ❌ Failed to deploy: {e}")

    print(f"\n✅ Deployed {deployed_count}/3 alerts")
    return deployed_count == 3


def step6_verify_alerts():
    """Verify all alerts are registered"""
    print_step(6, 6, "Verifying Alert Registration")

    try:
        result = make_request(
            "/servicesNS/nobody/search/saved/searches", parse_json=False
        )

        # Count FortiGate alerts
        import re

        fortigate_alerts = re.findall(r"FortiGate_\w+_Alert", result)
        unique_alerts = list(set(fortigate_alerts))

        print(f"✅ Found {len(unique_alerts)} FortiGate alerts:")
        for alert in sorted(unique_alerts):
            # Check if enabled
            alert_details = make_request(
                f"/servicesNS/nobody/search/saved/searches/{alert}", parse_json=False
            )
            disabled = re.search(
                r'<s:key name="disabled">([^<]+)</s:key>', alert_details
            )
            realtime = re.search(
                r'<s:key name="realtime_schedule">([^<]+)</s:key>', alert_details
            )

            status = (
                "✅ Enabled"
                if (disabled and disabled.group(1) == "0")
                else "❌ Disabled"
            )
            rt_status = "RT" if (realtime and realtime.group(1) == "1") else "Not RT"

            print(f"   - {alert}: {status}, {rt_status}")

        return len(unique_alerts) >= 3
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


# ============================================================================
# Main Execution
# ============================================================================


def main():
    print("\n" + "=" * 60)
    print("🚀 Splunk Alert Deployment via REST API")
    print("   (Terraform-equivalent, no installation required)")
    print("=" * 60)
    print(f"\nTarget: {SPLUNK_URL}")
    print(f"Index: {INDEX_NAME}")
    print(f"Alerts: {len(ALERTS)} FortiGate real-time alerts")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Execute deployment steps
    success = True
    hec_token = None

    if not step1_verify_splunk():
        success = False

    if success and not step2_enable_hec():
        success = False

    if success:
        hec_token = step3_create_hec_token()
        if not hec_token:
            success = False

    if success and not step4_create_index():
        success = False

    if success and not step5_deploy_alerts():
        success = False

    if success and not step6_verify_alerts():
        success = False

    # Summary
    print("\n" + "=" * 60)
    print("📊 Deployment Summary")
    print("=" * 60)

    if success:
        print("✅ Status: SUCCESS")
        print(f"✅ HEC Token: {hec_token}")
        print(f"✅ HEC Endpoint: https://localhost:{HEC_PORT}")
        print(f"✅ Index: {INDEX_NAME}")
        print(f"✅ Alerts: 3 real-time alerts enabled")

        print("\n📋 Next Steps:")
        print("1. Test with mock data:")
        print(f'   export SPLUNK_HEC_TOKEN="{hec_token}"')
        print("   node scripts/generate-alert-test-data.js --send")
        print("\n2. Verify alerts executing:")
        print("   curl -k -u admin:changeme \\")
        print("     'https://localhost:8089/services/search/jobs/export' \\")
        print(
            "     -d 'search=search index=_internal source=*scheduler.log savedsearch_name=\"FortiGate_*\" | tail 20'"
        )

        # Save token to file
        with open("/tmp/splunk_hec_token.txt", "w") as f:
            f.write(hec_token)
        print(f"\n💾 Token saved to: /tmp/splunk_hec_token.txt")

        return 0
    else:
        print("❌ Status: FAILED")
        print("\n🔍 Troubleshooting:")
        print("1. Check Splunk is running: docker ps | grep splunk-test")
        print("2. Check credentials: admin:changeme")
        print("3. Check REST API port: https://localhost:8089")
        print("4. Run diagnostic: ./scripts/diagnose-alerts-not-working.sh")
        return 1


if __name__ == "__main__":
    sys.exit(main())
