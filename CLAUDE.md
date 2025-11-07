# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Security Alert System v2.0.4** - Production Splunk app for FortiGate security monitoring.

**Core Pattern - EMS State Tracking:**
The entire alerting system is built on an Event-Metric-State (EMS) pattern to eliminate duplicate notifications:
1. Real-time events → Current state calculation
2. Join with previous state (CSV lookup)
3. Alert only on state changes (`state_changed=1`)
4. Update state atomically (`outputlookup append=t`)

This pattern is replicated across all 15 alerts with 11 state tracker CSV files.

**Critical Implementation Details:**
- **SPL-first architecture**: All logic in Splunk search queries (no external processing)
- **Macro-based configuration**: LogID groups, thresholds, index name centralized in `macros.conf`
- **Bundled dependencies**: Zero external dependencies - all Python libs in `lib/python3/`
- **Single-line messages**: Slack receives plain text via official alert action

---

## Development Commands

### Testing & Validation

```bash
# Test alert SPL directly
splunk search "`fortigate_index` `logids_vpn_tunnel` earliest=-1h | head 10"

# Validate all alert syntax
splunk btool savedsearches list --debug

# Check alert execution status
splunk search "index=_internal source=*scheduler.log savedsearch_name=\"*Alert*\" | stats count by savedsearch_name, status"

# Verify Slack delivery
splunk search "index=_internal source=*alert_actions.log action_name=\"slack\" | stats count by action_status"

# Inspect state tracker data
splunk search "| inputlookup vpn_state_tracker | stats count by device, state"
```

### Packaging & Deployment

```bash
# Build production tarball
cd /home/jclee/app/alert
tar -czf dist/security_alert-v2.0.4-production.tar.gz \
  --exclude='security_alert/__pycache__' \
  --exclude='security_alert/*.pyc' \
  --exclude='security_alert/local/*' \
  --exclude='security_alert/*.log' \
  security_alert/

# Install (Splunk server)
cd /opt/splunk/etc/apps/ && tar -xzf security_alert-v2.0.4-production.tar.gz
chown -R splunk:splunk security_alert
/opt/splunk/bin/splunk restart
```

### Required Configuration

```bash
# 1. Set Slack webhook (REQUIRED before alerts work)
cat > security_alert/local/alert_actions.conf <<EOF
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EOF

# 2. Override FortiGate index (if not 'index=fw')
# Edit: security_alert/local/macros.conf
[fortigate_index]
definition = index=your_custom_index

# 3. Disable specific alerts
# Edit: security_alert/local/savedsearches.conf
[002_VPN_Tunnel_Down]
enableSched = 0
```

---

## Architecture Deep Dive

### State Tracking System (Critical to Understand)

**Problem this solves:** Without state tracking, Splunk alerts would fire every minute (cron schedule) while a condition persists, flooding Slack with duplicate messages.

**EMS Pattern Implementation:**
```spl
# Step 1: Calculate current state from real-time events
| eval current_state = if(condition, "FAIL", "OK")

# Step 2: Load previous state from CSV (atomic read)
| join type=left device [| inputlookup state_tracker | rename state as previous_state]

# Step 3: Detect state change (NULL means first occurrence)
| eval state_changed = if(isnull(previous_state) OR previous_state!=current_state, 1, 0)

# Step 4: Filter to only changed states (critical filter!)
| where state_changed=1

# Step 5: Update state for next iteration (atomic append)
| eval state = current_state
| outputlookup append=t state_tracker
```

**Why `append=t` matters:** Prevents CSV lock errors with concurrent writes. Without it, multiple alerts writing simultaneously will fail.

**State Tracker Files (11 total):**
Each tracks a specific alert category's state transitions in `lookups/`:
- Binary states: UP/DOWN, FAIL/OK, NORMAL/ABNORMAL
- Multi-value states: HA role transitions (primary→secondary→standalone)
- Composite keys: device + component (e.g., fw01 + PSU-1)

**Common pitfall:** Removing `| where state_changed=1` causes duplicate alerts.

### Message Formatting Pipeline

**Design goal:** Single-line Slack messages under 200 chars with critical info only.

**Standard transformation chain:**
```spl
# 1. Build structured message
| eval formatted_message = <type> . " | " . <key_info> . " | " . <details>

# 2. Sanitize UUIDs (FortiGate includes these in many fields)
| rex mode=sed field=formatted_message "s/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[UUID]/g"

# 3. Truncate to fit Slack (200 char limit)
| eval formatted_message = if(len(formatted_message) > 200, substr(formatted_message, 1, 197) + "...", formatted_message)

# 4. Collapse multi-value fields
| eval user_list = mvjoin(mvindex(users, 0, 2), ", ")
| eval user_list = if(mvcount(users) > 3, user_list . " +more", user_list)
```

**Why this matters:** Slack mobile notifications truncate at ~120 chars. First 40 chars must identify the issue.

### Macro System (Configuration Abstraction)

**Purpose:** Single point of configuration for index name, LogID groups, and time ranges. Changing the FortiGate index requires editing only one line.

**Key macros in `default/macros.conf`:**
```ini
[fortigate_index]
definition = index=fw
# Override in local/macros.conf to change index for entire app

[logids_vpn_tunnel]
definition = (logid=0101037124 OR logid=0101037125 OR ...)
# Groups all LogIDs related to VPN tunnel events

[enrich_with_logid_lookup]
definition = lookup fortigate_logid_notification_map logid OUTPUT category, severity, description
# Adds human-readable metadata from 6091-line CSV
```

**Why macro-based:** Avoids hardcoding `index=fw` in 15 separate alert queries. Enables environment-specific overrides without editing default configs.

**Override pattern:**
```bash
# local/macros.conf (gitignored)
[fortigate_index]
definition = index=production_firewall_logs
```

### Python Dependencies (Air-Gapped Design)

**Why bundled:** Many Splunk deployments are air-gapped or lack pip/internet access. All dependencies included.

**Library loading pattern (in `bin/slack.py`):**
```python
import sys, os
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_DIR = os.path.join(APP_DIR, 'lib', 'python3')
sys.path.insert(0, LIB_DIR)  # Prioritize bundled libs over system
```

**Bundled versions (in `lib/python3/`):**
- requests (2.32.5), urllib3 (2.5.0), certifi (2025.10.5), charset-normalizer (3.4.4), idna (3.11)

**Critical:** When updating dependencies, replace entire directories (not individual files) to maintain internal consistency.

---

## Alert Type Taxonomy

**15 total alerts** across 3 behavioral categories:

### Binary State (4 alerts)
Alert on state transitions (UP→DOWN, DOWN→UP). Both directions send alerts.
- 002: VPN Tunnel, 007: Hardware, 012: Interface, 008: HA Role

### Threshold-Based (6 alerts)
Alert when crossing threshold, then again when returning to normal.
- 006: CPU/Memory (20% baseline deviation)
- 010: Resource (75% usage)
- 011/013: Brute force (3-5 failures/10min)
- 015: Traffic (3x baseline)
- 017: License (30 days expiry)

### Event-Based (5 alerts)
No state tracking - fire on event occurrence with suppression window.
- 001: Config Change (10min suppress)
- 016: Reboot (30min suppress)
- 018: FMG Sync (15min suppress)

**Key difference:** Binary/threshold use `state_changed=1` filter. Event-based use `alert.suppress.period`.

---

## SPL Patterns (Copy-Paste Templates)

### Standard State-Based Alert Template

```spl
`fortigate_index` `logids_<category>`
| `enrich_with_logid_lookup`
| eval device = coalesce(devname, "unknown")
| eval component = coalesce(field_name, "N/A")
| eval current_state = if(condition, "FAIL", "OK")
| stats latest(*) as * by device, component              # Dedup concurrent events
| join type=left device component [
    | inputlookup state_tracker
    | rename state as previous_state
]
| eval state_changed = if(isnull(previous_state) OR previous_state!=current_state, 1, 0)
| where state_changed=1                                   # CRITICAL: Only changed states
| eval state = current_state
| outputlookup append=t state_tracker                     # CRITICAL: append=t for atomic write
| eval formatted_message = component . " | " . state . " | Device: " . device
| table _time, device, component, state, previous_state, formatted_message
```

### Baseline Anomaly Detection (Alert 006 pattern)

```spl
# Historical baseline
| search `baseline_time_range`
| stats avg(cpu) as baseline_cpu by device
| eval threshold = baseline_cpu * 1.2

# Current vs baseline
| append [search `realtime_time_range` | stats avg(cpu) as current_cpu by device]
| eventstats values(baseline_cpu) as baseline_cpu by device
| eval current_state = if(current_cpu > baseline_cpu * 1.2, "ABNORMAL", "NORMAL")
```

**Why this works:** `append` combines historical and real-time data. `eventstats` broadcasts baseline to all rows.

---

## Critical Files (Where to Look First)

**Configuration Layer:**
- `default/savedsearches.conf` - All 15 alert definitions (800+ lines, PRIMARY LOGIC)
- `default/macros.conf` - LogID groups, thresholds, index name
- `default/transforms.conf` - CSV lookup registrations

**Execution Layer:**
- `bin/slack.py` - Slack message formatter (compatible with official add-on)
- `lib/python3/` - Bundled dependencies (requests, urllib3, etc.)

**Data Layer:**
- `lookups/*_state_tracker.csv` - 11 state files (runtime state, not in git)
- `lookups/fortigate_logid_notification_map.csv` - 6091 LogID mappings

**Override Layer (gitignored):**
- `local/alert_actions.conf` - Slack webhook URL (REQUIRED to enable alerts)
- `local/macros.conf` - Environment-specific index name
- `local/savedsearches.conf` - Disable specific alerts

**Not in use:**
- `bin/fortigate_auto_response.py` - Disabled auto-remediation (contains hardcoded credentials)
- `default/props.conf` - No custom field extractions defined

---

## Adding a New Alert (Complete Workflow)

**Prerequisites:** Know the FortiGate LogIDs to monitor (check `fortigate_logid_notification_map.csv`).

**Steps:**

1. **Define LogID macro** (`default/macros.conf`):
```ini
[logids_new_alert]
definition = (logid=0100000001 OR logid=0100000002)
iseval = 0
```

2. **Create state tracker CSV** (`lookups/new_alert_state_tracker.csv`):
```csv
device,component,state,last_seen,details
```

3. **Register lookup** (`default/transforms.conf`):
```ini
[new_alert_state_tracker]
filename = new_alert_state_tracker.csv
```

4. **Write alert query** (`default/savedsearches.conf`) - use template from "SPL Patterns" section above.

5. **Test query** (before enabling scheduler):
```bash
splunk search "`fortigate_index` `logids_new_alert` earliest=-1h | head 10"
```

6. **Enable alert** (set `enableSched = 1` in savedsearches.conf).

7. **Verify execution**:
```spl
index=_internal source=*scheduler.log savedsearch_name="019_New_Alert" | stats count by status
```

### Modifying Existing Alerts (Safe Changes)

**Safe to change:**
- Thresholds: Edit `macros.conf` values (e.g., CPU threshold from 20% to 30%)
- LogID lists: Add/remove LogIDs in macro definitions
- Time windows: Adjust `dispatch.earliest_time` (e.g., `rt-10m` → `rt-5m`)
- Slack channel: Override in `local/savedsearches.conf`

**Dangerous changes (will break alerts):**
- Remove `| where state_changed=1` → Duplicate alerts every minute
- Change `outputlookup append=t` to `outputlookup` → CSV lock errors, overwrites state
- Rename CSV columns → State tracker won't match, alerts reset
- Rename alert stanza names → Breaks Slack integration references

### Disabling Alerts (Temporary or Permanent)

**Temporary disable** (preserves state):
```ini
# local/savedsearches.conf
[002_VPN_Tunnel_Down]
enableSched = 0
```

**Permanent disable** (also clear state):
```spl
# 1. Disable alert (above)
# 2. Clear state tracker
| inputlookup vpn_state_tracker | where device!="*" | outputlookup vpn_state_tracker
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

## Operational Best Practices

### State Tracker Maintenance

**Monthly cleanup** (prevent CSV bloat >10,000 rows):
```spl
| inputlookup state_tracker
| where last_seen > relative_time(now(), "-30d")
| outputlookup state_tracker
```

**Before major changes:**
```bash
cp -r lookups/ lookups.backup-$(date +%Y%m%d)/
```

### Alert Tuning Workflow

1. Deploy with conservative thresholds
2. Monitor false positive rate (first 7 days)
3. Adjust thresholds in `macros.conf`
4. Use suppression only for event-based alerts (not state-based)
5. Never suppress on alert name - use `alert.suppress.fields = device,component`

---

## Security Notes

**Before deploying to production:**

1. **Remove hardcoded credentials** in `bin/fortigate_auto_response.py` (currently disabled, but contains placeholder tokens)

2. **Set Slack webhook** in `local/alert_actions.conf`:
```ini
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

3. **Verify .gitignore** excludes:
```
local/*             # Contains webhook URL
*.log
__pycache__/
lookups/*_state_tracker.csv  # Runtime state
```

4. **Permissions** on Slack webhook file:
```bash
chmod 600 security_alert/local/alert_actions.conf
chown splunk:splunk security_alert/local/alert_actions.conf
```
