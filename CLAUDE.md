# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Security Alert System v2.0.4** - FortiGate security event monitoring and Slack notification system for Splunk.

This is a **fully self-contained** Splunk app that monitors FortiGate firewall events and sends intelligent alerts to Slack using EMS (Event Management System) state tracking to eliminate duplicate notifications.

**Key Capabilities:**
- 15 active alert types covering VPN, HA, hardware, resources, admin logins, and traffic
- EMS-based state tracking (only alerts on state changes)
- Slack Block Kit formatted notifications
- Automated response capabilities (IP blocking, bandwidth limiting, account disabling)
- 10 CSV state tracker files for persistent state management
- ⭐ **All Python dependencies bundled** - works on air-gapped servers
- ⭐ **Zero external dependencies** - no pip install required

---

## Architecture

### Core Components

1. **Saved Searches** (`default/savedsearches.conf`)
   - 15 alert definitions with SPL queries
   - Real-time scheduling (cron + realtime mode)
   - State tracking logic using CSV lookups

2. **State Tracking** (`lookups/*.csv`)
   - 10 state tracker CSV files (plus 3 additional lookup files)
   - EMS pattern: compares `previous_state` vs `current_state`
   - Only triggers alerts when state changes (prevents duplicates)

3. **Alert Actions** (`bin/*.py`)
   - `slack.py` - Slack Block Kit message formatter
   - `fortigate_auto_response.py` - Automated remediation engine
   - `splunk_feature_checker.py` - System health validator

4. **Configuration**
   - `macros.conf` - Centralized LogID groups and thresholds
   - `transforms.conf` - Lookup table definitions
   - `alert_actions.conf` - Slack webhook configuration

### Alert State Machine

All binary state alerts (VPN, Hardware, Interface, HA) follow this pattern:

```spl
| eval current_state = if(condition, "FAIL", "OK")
| join type=left device [| inputlookup state_tracker | rename state as previous_state]
| eval state_changed = if(isnull(previous_state) OR previous_state!=current_state, 1, 0)
| where state_changed=1
| eval state = current_state
| outputlookup append=t state_tracker
```

Threshold-based alerts (CPU, Resource, Brute Force) use states like `ABNORMAL/NORMAL`, `EXCEEDED/NORMAL`, `ATTACK/NORMAL`.

---

## Development Commands

### Testing & Validation

```bash
# Run installation verification (bundled dependencies check)
cd /opt/splunk/etc/apps/security_alert
bash bin/install.sh

# Validate SPL syntax
splunk btool savedsearches list --debug

# Check alert execution logs
index=_internal source=*scheduler.log savedsearch_name="*Alert*"

# Check Slack delivery logs
index=_internal source=*alert_actions.log action_name="slack"

# Validate state tracker integrity
| inputlookup vpn_state_tracker
| stats count by device, state

# Run feature checker (validates all Splunk components)
python3 bin/splunk_feature_checker.py /opt/splunk
```

### Deployment

**✅ All dependencies are bundled - NO external installation required!**

```bash
# Package app for distribution (with bundled dependencies)
tar -czf security_alert-v2.0.4-bundled.tar.gz \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.log' \
  security_alert/

# Install on Splunk server
cd /opt/splunk/etc/apps/
tar -xzf security_alert-v2.0.4-bundled.tar.gz
chown -R splunk:splunk security_alert

# Run installation check
cd security_alert
bash bin/install.sh

# Restart Splunk to load app
/opt/splunk/bin/splunk restart
```

**Key Features:**
- ✅ All Python dependencies bundled in `lib/python3/`
- ✅ No `pip install` required
- ✅ Works on air-gapped/isolated Splunk servers
- ✅ Automatic dependency path resolution

### Configuration

```bash
# Set Slack webhook URL (required)
vim default/alert_actions.conf
# Set: param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Or use environment variable
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Configure FortiManager for auto-response
vim bin/fortigate_auto_response.py
# Set: FORTIMANAGER_URL and FORTIMANAGER_TOKEN
```

---

## Alert Types

### Binary State Alerts (4 types)

| Alert | State Transition | Severity | LogIDs |
|-------|-----------------|----------|--------|
| `002_VPN_Tunnel_Down/Up` | DOWN ↔ UP | Critical | 0101037124, 0101037131, 0101037134 |
| `007_Hardware_Failure/Restored` | FAIL ↔ OK | Critical | 0103040001-0103040003 |
| `012_Interface_Down/Up` | DOWN ↔ UP | Medium-High | 0100032001, 0100020007 |
| `008_HA_State_Change` | State transitions | Medium-High | 0100020010, 0104043544-45 |

### Threshold-Based Alerts (6 types)

| Alert | Threshold | State | LogIDs |
|-------|-----------|-------|--------|
| `006_CPU_Memory_Anomaly` | 20% deviation from baseline | ABNORMAL | 0104043001-02 |
| `010_Resource_Limit` | 75% usage | EXCEEDED | 0104043003-04 |
| `011_Admin_Login_Failed` | 3+ failures | ATTACK | 0105032003-05 |
| `013_SSL_VPN_Brute_Force` | 5+ failures | ATTACK | 0101039424-26 |
| `015_Abnormal_Traffic_Spike` | 3x baseline | SPIKE | 0000000013-14 |
| `017_License_Expiry_Warning` | 30 days remaining | WARNING | 0104043009-10 |

### Other Alerts (5 types)

- `001_Config_Change` - Configuration changes (CLI/GUI)
- `016_System_Reboot` - System reboot/crash events

---

## State Tracker Files

All state trackers use the same CSV structure:

```csv
device,component,state,last_seen,details
fw01,tunnel1,DOWN,1699123456,Phase1 negotiation failed
fw01,tunnel1,UP,1699123789,Tunnel restored
```

**Files:**
- `vpn_state_tracker.csv` - VPN tunnel states
- `hardware_state_tracker.csv` - Hardware component health
- `ha_state_tracker.csv` - HA role/state changes
- `interface_state_tracker.csv` - Network interface status
- `cpu_memory_state_tracker.csv` - CPU/Memory anomalies
- `resource_state_tracker.csv` - Resource exhaustion
- `admin_login_state_tracker.csv` - Admin login failures
- `vpn_brute_force_state_tracker.csv` - VPN brute force attempts
- `traffic_spike_state_tracker.csv` - Traffic anomalies
- `license_state_tracker.csv` - License expiry warnings

---

## SPL Query Patterns

### Standard Alert Structure

```spl
`fortigate_index` `logids_<category>`
| `enrich_with_logid_lookup`
| eval device = coalesce(devname, "unknown")
| [... alert-specific logic ...]
| eval current_state = if(condition, "FAIL", "OK")
| stats latest(*) as * by device, <key_field>
| join type=left device <key_field> [
    | inputlookup <state_tracker>
    | rename state as previous_state
]
| eval state_changed = if(isnull(previous_state) OR previous_state!=current_state, 1, 0)
| where state_changed=1
| eval state = current_state
| outputlookup append=t <state_tracker>
| table _time, device, [relevant_fields]
```

### Macro Usage

All alerts use centralized macros from `macros.conf`:

```spl
`fortigate_index`              → index=fw
`logids_vpn_tunnel`            → (logid=0101037124 OR logid=0101037131 ...)
`enrich_with_logid_lookup`     → lookup fortigate_logid_lookup logid OUTPUT ...
```

**Key thresholds:**
- `cpu_high_threshold` → 80
- `memory_high_threshold` → 85
- `baseline_anomaly_multiplier` → 2

---

## Automated Response System

The `fortigate_auto_response.py` script provides automated remediation:

### Supported Actions

1. **IP Blacklisting** (Brute Force)
   - Triggers: SSL VPN ≥10 failures
   - Action: Add to FortiGate address blacklist
   - API: `POST /api/v2/cmdb/firewall/address`

2. **Bandwidth Limiting** (Traffic Spike)
   - Triggers: Traffic ≥5x baseline
   - Action: Apply 10 Mbps traffic shaper
   - API: `POST /api/v2/cmdb/firewall/shaping-policy`

3. **Account Disabling** (Admin Login)
   - Triggers: Admin login ≥5 failures
   - Action: Disable admin account
   - API: `PUT /api/v2/cmdb/system/admin/{user}`

### Integration

Configure in `savedsearches.conf`:

```ini
action.script = 1
action.script.filename = fortigate_auto_response.py
```

Pass alert data via stdin (JSON format).

---

## Troubleshooting

### Alert Not Triggering

```spl
# Check if events exist
`fortigate_index` `logids_vpn_tunnel` earliest=-1h
| stats count by logid, device

# Check state tracker
| inputlookup vpn_state_tracker
| table device, vpn_name, state, last_seen

# Check scheduler logs
index=_internal source=*scheduler.log savedsearch_name="002_VPN_Tunnel_Down"
| stats count by status, result_count
```

### Duplicate Alerts

1. Verify `state_changed=1` filter is present
2. Check state tracker CSV has correct previous states
3. Validate `outputlookup append=t` is writing correctly

### Slack Not Sending

```spl
# Check alert action logs
index=_internal source=*alert_actions.log action_name="slack"
| table _time, sid, action_name, action_status, stderr

# Verify webhook URL
cat default/alert_actions.conf | grep webhook_url
```

---

## File Structure

```
security_alert/
├── README.md                          # User documentation
├── app.manifest                       # App manifest (v2.0.4)
├── metadata/default.meta               # App metadata
├── default/
│   ├── app.conf                       # App definition
│   ├── savedsearches.conf             # 15 alert definitions
│   ├── macros.conf                    # LogID groups & thresholds
│   ├── transforms.conf                # Lookup definitions
│   ├── alert_actions.conf             # Slack configuration
│   ├── props.conf                     # Field extractions
│   └── data/ui/
│       ├── views/*.xml                # Dashboards
│       └── nav/default.xml            # Navigation
├── bin/
│   ├── install.sh                     # ⭐ Installation verification script
│   ├── slack.py                       # Slack Block Kit formatter
│   ├── fortigate_auto_response.py     # Automated remediation
│   ├── splunk_feature_checker.py      # System validator
│   ├── deployment_health_check.py     # Deployment checker
│   ├── post_install_check.py          # Post-install checker
│   └── auto_validator.py              # Alert validator
├── lib/                               # ⭐ NEW: Bundled dependencies
│   └── python3/                       # Python 3 libraries
│       ├── requests/                  # HTTP library (v2.32.5)
│       ├── urllib3/                   # Connection pooling (v2.5.0)
│       ├── charset_normalizer/        # Character encoding (v3.4.4)
│       ├── certifi/                   # SSL certificates (v2025.10.5)
│       └── idna/                      # Internationalized domain names (v3.11)
└── lookups/
    ├── fortigate_logid_notification_map.csv  # LogID reference
    ├── auto_response_actions.csv      # Response mapping
    ├── severity_priority.csv          # Severity levels
    └── *_state_tracker.csv            # 10 state trackers
```

### Bundled Dependencies

**All Python dependencies are included in the app - no external installation required!**

The app automatically loads bundled libraries from `lib/python3/`:

```python
# Automatic path resolution in bin/slack.py and bin/fortigate_auto_response.py
import sys
import os

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(APP_DIR, 'lib', 'python3')
if os.path.exists(LIB_DIR) and LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

import requests  # Now works without pip install!
```

**Bundled libraries:**
- `requests` (2.32.5) - HTTP client for Slack/FortiManager API
- `urllib3` (2.5.0) - HTTP connection pooling
- `charset-normalizer` (3.4.4) - Character encoding detection
- `certifi` (2025.10.5) - SSL/TLS certificate bundle
- `idna` (3.11) - Internationalized domain names

**Benefits:**
- ✅ Works on air-gapped/isolated Splunk servers
- ✅ No internet access required
- ✅ No admin privileges needed for pip
- ✅ Consistent versions across all deployments
- ✅ No dependency conflicts with other apps

---

## Best Practices

### Modifying Alerts

1. **Always preserve state tracking logic** - Don't remove the `state_changed` filter
2. **Use macros for LogIDs** - Edit `macros.conf` instead of hardcoding
3. **Test with `| head 10` first** - Validate SPL before enabling alert
4. **Update state tracker schema carefully** - Changing CSV columns breaks existing states

### Adding New Alerts

1. Define LogID macro in `macros.conf`:
   ```ini
   [logids_new_alert]
   definition = (logid=0100000001 OR logid=0100000002)
   ```

2. Create state tracker CSV in `lookups/`:
   ```csv
   device,component,state,last_seen,details
   ```

3. Add lookup definition in `transforms.conf`:
   ```ini
   [new_alert_state_tracker]
   filename = new_alert_state_tracker.csv
   ```

4. Create alert in `savedsearches.conf` using standard pattern (see SPL Query Patterns above)

5. Test thoroughly before enabling:
   ```spl
   `fortigate_index` `logids_new_alert` earliest=-1h
   | [... your alert logic ...]
   | head 10
   ```

### Performance Optimization

- Use `dispatch.rt_backfill = 1` for real-time alerts
- Set `auto_summarize = 0` to prevent summary indexing overhead
- Keep time windows narrow (rt-10m preferred)
- Use `stats latest(*)` to deduplicate before state comparison

---

## Common Issues

### Issue: "No module named 'requests'"

**Symptom:** Alert actions fail with `ModuleNotFoundError: No module named 'requests'`

**Root Cause:** Bundled libraries not loaded properly

**Solution:**
```bash
# 1. Verify lib directory exists
ls -la /opt/splunk/etc/apps/security_alert/lib/python3/

# 2. Verify permissions
chmod -R 755 /opt/splunk/etc/apps/security_alert/lib/

# 3. Check Python scripts have sys.path modification
head -20 /opt/splunk/etc/apps/security_alert/bin/slack.py
# Should contain: sys.path.insert(0, LIB_DIR)

# 4. Test import manually
cd /opt/splunk/etc/apps/security_alert
python3 -c "
import sys, os
sys.path.insert(0, 'lib/python3')
import requests
print('OK')
"
```

### Issue: CSV Lock Errors

**Symptom:** `Error in 'outputlookup': The lookup table is locked`

**Solution:** Use `append=t` instead of overwriting entire CSV:
```spl
| outputlookup append=t state_tracker
```

### Issue: State Tracker Growing Too Large

**Symptom:** Alert performance degrades over time

**Solution:** Implement periodic cleanup:
```spl
| inputlookup state_tracker
| where last_seen > relative_time(now(), "-7d")
| outputlookup state_tracker
```

### Issue: Macro Not Found

**Symptom:** `Error in 'search': Unknown search command 'logids_vpn_tunnel'`

**Solution:** Restart Splunk to reload macros:
```bash
/opt/splunk/bin/splunk restart
```

### Issue: Permission Denied on lib/ Directory

**Symptom:** Python scripts can't access bundled libraries

**Solution:**
```bash
cd /opt/splunk/etc/apps/security_alert
chown -R splunk:splunk lib/
chmod -R 755 lib/
```

---

## Version History

**v2.0.4** (2025-11-04)
- Implemented EMS state tracking for all alerts
- Added 10 state tracker CSV files
- Integrated Slack Block Kit formatting
- Enabled 15 alerts

**v2.0.1** (2025-11-03)
- Enhanced field parsing with coalesce()
- Fixed LogID definitions based on sample data
- Added automated response system

---

## Repository

**Source:** https://github.com/qws941/splunk.git

**Maintainer:** NextTrade Security Team
