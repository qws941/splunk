# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Security Alert System v2.0.4** - A production Splunk app for FortiGate security event monitoring with Slack notifications.

**Key Architecture:**
- **EMS-based State Tracking**: Eliminates duplicate alerts by tracking state transitions in CSV files
- **15 Alert Definitions**: Configured in `savedsearches.conf` with SPL queries
- **Self-contained Dependencies**: All Python libraries bundled in `lib/python3/` for air-gapped deployment
- **Slack Integration**: Uses Splunk's official Slack alert action with plain text formatting

---

## Development Commands

### Testing & Validation

```bash
# Validate SPL syntax (all alerts)
cd /opt/splunk/etc/apps/security_alert
splunk btool savedsearches list --debug

# Test specific alert SPL (replace with alert name)
splunk search "`fortigate_index` `logids_vpn_tunnel` earliest=-1h | head 10"

# Check alert execution logs
splunk search "index=_internal source=*scheduler.log savedsearch_name=\"*Alert*\" | stats count by savedsearch_name, status"

# Check Slack delivery status
splunk search "index=_internal source=*alert_actions.log action_name=\"slack\" | stats count by action_status"

# Validate state tracker integrity
splunk search "| inputlookup vpn_state_tracker | stats count by device, state"
```

### Deployment

```bash
# Package app for distribution (production-ready)
cd /home/jclee/app/alert
tar -czf security_alert-v2.0.4-production.tar.gz \
  --exclude='security_alert/__pycache__' \
  --exclude='security_alert/*.pyc' \
  --exclude='security_alert/local/*' \
  --exclude='security_alert/*.log' \
  security_alert/

# Install on Splunk server
cd /opt/splunk/etc/apps/
tar -xzf security_alert-v2.0.4-production.tar.gz
chown -R splunk:splunk security_alert

# Configure Slack webhook (REQUIRED)
cat > security_alert/local/alert_actions.conf <<EOF
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EOF

# Restart Splunk to load app
/opt/splunk/bin/splunk restart
```

### Configuration

```bash
# Set Slack webhook (Option 1: local config file)
vim security_alert/local/alert_actions.conf

# Set FortiGate index (if not 'index=fw')
vim security_alert/default/macros.conf
# Edit: [fortigate_index] definition = index=your_index

# Enable/disable specific alerts
vim security_alert/local/savedsearches.conf
# Add: [alert_name] enableSched = 0 (to disable)
```

---

## Architecture & Key Concepts

### State Tracking System (EMS Pattern)

All alerts use CSV-based state tracking to prevent duplicate notifications. The pattern:

1. **Calculate current state** from real-time events
2. **Load previous state** from CSV lookup
3. **Compare states** - only trigger if changed
4. **Update state** back to CSV for next iteration

**SPL Pattern:**
```spl
| eval current_state = if(condition, "FAIL", "OK")
| join type=left device [| inputlookup state_tracker | rename state as previous_state]
| eval state_changed = if(isnull(previous_state) OR previous_state!=current_state, 1, 0)
| where state_changed=1
| eval state = current_state
| outputlookup append=t state_tracker
```

**11 State Tracker Files** (in `lookups/`):
- `vpn_state_tracker.csv` - VPN tunnel UP/DOWN
- `hardware_state_tracker.csv` - Hardware FAIL/OK
- `ha_state_tracker.csv` - HA role changes
- `interface_state_tracker.csv` - Interface UP/DOWN
- `cpu_memory_state_tracker.csv` - CPU/Memory ABNORMAL/NORMAL
- `resource_state_tracker.csv` - Resource EXCEEDED/NORMAL
- `admin_login_state_tracker.csv` - Admin login ATTACK/NORMAL
- `vpn_brute_force_state_tracker.csv` - VPN brute force ATTACK/NORMAL
- `traffic_spike_state_tracker.csv` - Traffic SPIKE/NORMAL
- `license_state_tracker.csv` - License WARNING/NORMAL
- `fmg_sync_state_tracker.csv` - FortiManager sync FAIL/OK

### Alert Message Formatting

All alerts generate a `formatted_message` field using this pattern:

```spl
| eval formatted_message = <type> . " | " . <key_info> . " | " . <details>
| rex mode=sed field=formatted_message "s/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[UUID]/g"
| eval formatted_message = if(len(formatted_message) > 200, substr(formatted_message, 1, 197) + "...", formatted_message)
```

**Formatting Rules:**
- Replace UUIDs with `[UUID]` placeholder
- Truncate long values (30-50 chars depending on field importance)
- Use `mvjoin()` for multi-value fields
- Trim whitespace with `trim()`
- Include emojis for visual clarity

**Example outputs:**
```
VPN Type: tunnel1 | Tunnel Down | Remote: 10.1.1.1 | Reason: Phase1 negotiation failed
🟠 Brute Force from 192.168.1.100 | 15 failures | Users: admin, user1, user2 +more
🔴 Hardware: PSU-1 | Status: FAIL | Device: fw01 | Severity: Critical
```

### Macro System

Centralized configuration in `default/macros.conf`:

**Index & Time Macros:**
- `fortigate_index` → `index=fw` (modify for your index)
- `baseline_time_range` → `-8d to -1d`
- `realtime_time_range` → `rt-10m to now`

**LogID Group Macros** (15 alert types):
- `logids_vpn_tunnel` → `(logid=0101037124 OR ...)`
- `logids_hardware_failure` → `(logid=0103040001 OR ...)`
- `logids_ha_state` → `(logid=0100020010 OR ...)`
- etc.

**Enrichment Macro:**
- `enrich_with_logid_lookup` → Adds category, severity, description from CSV

**Usage in alerts:**
```spl
`fortigate_index` `logids_vpn_tunnel`
| `enrich_with_logid_lookup`
```

### Bundled Dependencies

All Python dependencies are **pre-bundled** in `lib/python3/` - no pip install required:

- `requests` (2.32.5) - HTTP client for Slack/FortiManager
- `urllib3` (2.5.0) - Connection pooling
- `charset-normalizer` (3.4.4) - Encoding detection
- `certifi` (2025.10.5) - SSL certificates
- `idna` (3.11) - Domain name encoding

**Auto-loaded** via sys.path modification in `bin/slack.py` and `bin/fortigate_auto_response.py`:
```python
import sys, os
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(APP_DIR, 'lib', 'python3')
if os.path.exists(LIB_DIR):
    sys.path.insert(0, LIB_DIR)
```

---

## Alert Categories

### Binary State Alerts (4 types)

State transitions between two values (e.g., UP/DOWN, FAIL/OK):

| Alert ID | Description | States | Severity |
|----------|-------------|--------|----------|
| 002 | VPN Tunnel | DOWN ↔ UP | Critical |
| 007 | Hardware Failure | FAIL ↔ OK | Critical |
| 012 | Interface Status | DOWN ↔ UP | Medium-High |
| 008 | HA State Change | Role transitions | Medium-High |

### Threshold-Based Alerts (6 types)

Trigger when values exceed defined thresholds:

| Alert ID | Description | Threshold | States |
|----------|-------------|-----------|--------|
| 006 | CPU/Memory Anomaly | 20% deviation from 7-day baseline | ABNORMAL/NORMAL |
| 010 | Resource Limit | 75% usage | EXCEEDED/NORMAL |
| 011 | Admin Login Failed | ≥3 failures in 10min | ATTACK/NORMAL |
| 013 | SSL VPN Brute Force | ≥5 failures in 10min | ATTACK/NORMAL |
| 015 | Traffic Spike | 3x baseline | SPIKE/NORMAL |
| 017 | License Expiry | 30 days remaining | WARNING/NORMAL |

### Event-Based Alerts (5 types)

Fire on specific events without state tracking:

| Alert ID | Description | Suppression |
|----------|-------------|-------------|
| 001 | Config Change | 10min (device+user+path) |
| 016 | System Reboot | 30min (device) |
| 018 | FMG Out of Sync | 15min (device) |

---

## Common SPL Patterns

### Standard Alert Structure

```spl
`fortigate_index` `logids_<category>`
| `enrich_with_logid_lookup`
| eval device = coalesce(devname, "unknown")
| eval component = coalesce(field_name, "N/A")
| eval current_state = if(condition, "FAIL", "OK")
| stats latest(*) as * by device, component
| join type=left device component [
    | inputlookup state_tracker
    | rename state as previous_state
]
| eval state_changed = if(isnull(previous_state) OR previous_state!=current_state, 1, 0)
| where state_changed=1
| eval state = current_state
| outputlookup append=t state_tracker
| eval formatted_message = component . " | " . state . " | Device: " . device
| table _time, device, component, state, previous_state, formatted_message
```

### Baseline Anomaly Detection

Used by Alert 006 (CPU/Memory):

```spl
# Calculate 7-day baseline
| search `baseline_time_range`
| stats avg(cpu) as baseline_cpu by device
| eval threshold = baseline_cpu * 1.2

# Compare to current values
| append [search `realtime_time_range` | stats avg(cpu) as current_cpu by device]
| eventstats values(baseline_cpu) as baseline_cpu by device
| eval current_state = if(current_cpu > baseline_cpu * 1.2, "ABNORMAL", "NORMAL")
```

### Multi-value Field Handling

```spl
# Show first 3 items, indicate if more exist
| eval user_list = mvjoin(mvindex(users, 0, 2), ", ")
| eval user_list = if(mvcount(users) > 3, user_list . " +more", user_list)
```

---

## File Structure Reference

```
security_alert/
├── app.manifest                   # Splunk app manifest (version 2.0.4)
├── README.md                      # User documentation (Korean)
├── default/                       # Default configuration
│   ├── app.conf                   # App metadata
│   ├── savedsearches.conf         # 15 alert definitions (PRIMARY)
│   ├── macros.conf                # LogID groups, thresholds, index config
│   ├── transforms.conf            # 11 state tracker + 3 reference lookups
│   ├── alert_actions.conf         # Slack webhook configuration
│   ├── props.conf                 # Field extractions (not used)
│   └── data/ui/
│       ├── views/                 # Dashboards (4 XML files)
│       └── nav/default.xml        # Navigation
├── local/                         # User overrides (gitignored)
│   ├── alert_actions.conf         # Slack webhook (REQUIRED)
│   └── savedsearches.conf         # Alert enable/disable overrides
├── bin/                           # Python scripts
│   ├── slack.py                   # Slack Block Kit formatter (official compatible)
│   ├── fortigate_auto_response.py # Automated remediation (NOT IN USE)
│   ├── safe_fmt.py                # Safe string formatting
│   └── six.py                     # Python 2/3 compatibility
├── lib/python3/                   # Bundled dependencies (NO pip needed)
│   ├── requests/
│   ├── urllib3/
│   ├── charset_normalizer/
│   ├── certifi/
│   └── idna/
├── lookups/                       # CSV state trackers + reference data
│   ├── *_state_tracker.csv        # 11 state tracking files
│   └── fortigate_logid_notification_map.csv  # LogID reference (6091 lines)
└── metadata/
    └── default.meta               # Permissions
```

---

## Modifying Alerts

### Adding a New Alert

1. **Define LogID macro** (`default/macros.conf`):
```ini
[logids_new_alert]
definition = (logid=0100000001 OR logid=0100000002)
iseval = 0
```

2. **Create state tracker** (`lookups/new_alert_state_tracker.csv`):
```csv
device,component,state,last_seen,details
```

3. **Register lookup** (`default/transforms.conf`):
```ini
[new_alert_state_tracker]
filename = new_alert_state_tracker.csv
```

4. **Create alert** (`default/savedsearches.conf`):
```ini
[019_New_Alert]
description = Description of alert
search = `fortigate_index` `logids_new_alert` \
| [... use standard pattern above ...]
cron_schedule = * * * * *
enableSched = 1
realtime_schedule = 1
dispatch.earliest_time = rt-10m
dispatch.latest_time = rt
alert.track = 1
alert.severity = 5
action.slack = 1
action.slack.param.channel = #security-firewall-alert
action.slack.param.message = $result.formatted_message$
```

5. **Test before enabling**:
```bash
splunk search "`fortigate_index` `logids_new_alert` earliest=-1h | head 10"
```

### Modifying Existing Alerts

**DO:**
- Edit thresholds in `macros.conf`
- Add/remove LogIDs to macro definitions
- Adjust time windows (`dispatch.earliest_time`)
- Change Slack channels in `local/savedsearches.conf`

**DON'T:**
- Remove `state_changed=1` filter (breaks deduplication)
- Change CSV column names (breaks existing state data)
- Remove `outputlookup append=t` (state won't update)
- Modify alert names (breaks references)

### Disabling Alerts

Create/edit `local/savedsearches.conf`:
```ini
[002_VPN_Tunnel_Down]
enableSched = 0
```

---

## Troubleshooting

### Alert Not Triggering

```spl
# 1. Check if events exist
`fortigate_index` `logids_vpn_tunnel` earliest=-1h
| stats count by logid, device

# 2. Verify state tracker
| inputlookup vpn_state_tracker
| table device, vpn_name, state, last_seen

# 3. Check scheduler execution
index=_internal source=*scheduler.log savedsearch_name="002_VPN_Tunnel_Down"
| stats count by status, result_count

# 4. Check alert action
index=_internal source=*alert_actions.log savedsearch_name="002_VPN_Tunnel_Down"
| table _time, action_name, action_status, stderr
```

### Duplicate Alerts

**Root causes:**
- Missing `state_changed=1` filter in SPL
- State tracker CSV not updating (`outputlookup` failed)
- Multiple alert instances running (check schedule)

**Fix:**
```spl
# Verify state change logic exists
| where state_changed=1

# Verify state update at end
| outputlookup append=t state_tracker
```

### Slack Not Sending

```spl
# Check alert action logs
index=_internal source=*alert_actions.log action_name="slack"
| table _time, sid, action_status, stderr
| sort - _time

# Common errors:
# - "webhook_url not found" → Check local/alert_actions.conf
# - "404 Not Found" → Invalid webhook URL
# - "500 Internal Error" → Slack service issue
```

**Verify configuration:**
```bash
cat local/alert_actions.conf
# Should contain:
# [slack]
# param.webhook_url = https://hooks.slack.com/services/...
```

### CSV Lock Errors

**Symptom:** `Error in 'outputlookup': The lookup table is locked`

**Solution:** Always use `append=t` mode:
```spl
| outputlookup append=t state_tracker  # ✓ Correct
| outputlookup state_tracker           # ✗ Wrong (overwrites entire file)
```

### State Tracker Growing Too Large

**Symptom:** Alert performance degrades (>10,000 rows in CSV)

**Solution:** Implement periodic cleanup (run monthly):
```spl
| inputlookup state_tracker
| where last_seen > relative_time(now(), "-30d")
| outputlookup state_tracker
```

---

## Best Practices

### Performance Optimization

- Use `stats latest(*)` to deduplicate before state comparison
- Keep time windows narrow (`rt-10m` for real-time)
- Use `dispatch.rt_backfill = 1` for missed events
- Set `auto_summarize = 0` to disable summary indexing

### State Tracker Maintenance

- Clean up old states monthly (see above)
- Monitor CSV size: `ls -lh lookups/*_state_tracker.csv`
- Back up state files before major changes
- Use `append=t` mode for atomic writes

### Alert Tuning

- Start with conservative thresholds, adjust based on false positive rate
- Use suppression for noisy alerts (`alert.suppress.period`)
- Group related fields in suppression (`alert.suppress.fields`)
- Set appropriate expiry times (`alert.expires`)

---

## Security Considerations

### Before Deployment

**REMOVE hardcoded credentials** from `bin/fortigate_auto_response.py`:
```python
# ✗ Current (DO NOT DEPLOY)
FORTIMANAGER_URL = "https://fmg.example.com"
FORTIMANAGER_TOKEN = "YOUR_FMG_API_TOKEN"

# ✓ Use environment variables
FORTIMANAGER_URL = os.environ.get('FORTIMANAGER_URL')
FORTIMANAGER_TOKEN = os.environ.get('FORTIMANAGER_TOKEN')
```

**SET Slack webhook** in `local/alert_actions.conf` (not in default):
```ini
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**EXCLUDE sensitive files** from version control:
```
local/*
*.log
__pycache__/
```

---

## Version History

**v2.0.4** (2025-11-04)
- Implemented EMS state tracking for all 15 alerts
- Added 11 state tracker CSV files
- Simplified Slack messages to single-line format
- Bundled all Python dependencies (air-gapped support)

**v2.0.1** (2025-11-03)
- Enhanced field parsing with coalesce()
- Fixed LogID definitions based on sample data
- Added FMG install detection (Alert 001)

---

## Repository

- **GitHub**: https://github.com/qws941/splunk.git
- **Maintainer**: NextTrade Security Team
- **License**: MIT
