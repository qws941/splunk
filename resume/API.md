# API Reference

## Splunk App API

This Splunk app does not expose external APIs. All interactions are via Splunk's built-in mechanisms.

## Internal Interfaces

### 1. Alert Action Interface

**Python Modular Alert** (`bin/slack.py`)

```python
def send_slack_message(payload):
    """
    Send formatted message to Slack webhook

    Args:
        payload (dict): {
            'configuration': {'webhook_url': str, 'channel': str},
            'result': {'formatted_message': str}
        }

    Returns:
        bool: Success status
    """
```

**Environment Variables:**
- None (configured via `alert_actions.conf`)

**Configuration:**
```ini
# local/alert_actions.conf
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 2. Macro Interface

**SPL Macros** (defined in `default/macros.conf`)

| Macro | Purpose | Example |
|-------|---------|---------|
| `fortigate_index` | Define source index | `index=fw` |
| `logids_vpn_tunnel` | VPN-related LogIDs | `(logid=0101037124 OR ...)` |
| `enrich_with_logid_lookup` | Add category/severity | `lookup fortigate_logid_notification_map` |
| `baseline_time_range` | Historical data window | `-8d to -1d` |

**Usage in SPL:**
```spl
`fortigate_index` `logids_vpn_tunnel`
| `enrich_with_logid_lookup`
```

### 3. State Tracker Interface

**CSV Lookup Files** (`lookups/*.csv`)

**Schema:**
```csv
device,component,state,last_seen,details
fw01,vpn-tunnel-1,UP,2025-11-07T10:00:00,Remote: 10.1.1.1
fw02,PSU-1,FAIL,2025-11-07T09:55:00,Hardware failure detected
```

**Operations:**
```spl
# Read state
| inputlookup vpn_state_tracker

# Update state (atomic append)
| outputlookup append=t vpn_state_tracker

# Cleanup old states
| inputlookup vpn_state_tracker
| where last_seen > relative_time(now(), "-30d")
| outputlookup vpn_state_tracker
```

### 4. FortiGate LogID Lookup

**Reference Data** (`lookups/fortigate_logid_notification_map.csv`)

**Schema:**
```csv
logid,category,severity,description,action
0101037124,VPN,critical,Phase1 negotiation failed,monitor
0100032001,System,medium,Admin login failed,alert
```

**Usage:**
```spl
| lookup fortigate_logid_notification_map logid OUTPUT category, severity, description
```

## External Integrations

### Slack Webhook API

**Endpoint:** `https://hooks.slack.com/services/{workspace}/{channel}/{token}`

**Method:** POST

**Payload:**
```json
{
  "channel": "#security-firewall-alert",
  "text": "VPN Type: tunnel1 | Tunnel Down | Remote: 10.1.1.1"
}
```

**Response:**
```
200 OK: "ok"
404 Not Found: Invalid webhook URL
500 Internal Error: Slack service issue
```

**Rate Limits:**
- 1 request per second per webhook
- Handled by Splunk alert throttling

## Troubleshooting APIs

### Splunk Internal Logs

```spl
# Alert execution status
index=_internal source=*scheduler.log savedsearch_name="*Alert*"
| table _time, savedsearch_name, status, result_count

# Slack delivery status
index=_internal source=*alert_actions.log action_name="slack"
| table _time, sid, action_status, stderr

# CSV operations
index=_internal source=*python.log "outputlookup"
| table _time, log_level, message
```

### Health Check

**No dedicated health endpoint** - use Splunk's built-in monitoring:

```bash
# Check Splunk app status
/opt/splunk/bin/splunk display app security_alert

# Verify alert schedules
/opt/splunk/bin/splunk list search-jobs -app security_alert
```

## No REST API

This app does not expose REST endpoints. All configuration is file-based.
