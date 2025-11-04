# CLAUDE.md - Splunk Security Alert System

This file provides guidance to Claude Code when working with the Splunk security alert application codebase.

## ⚡ Quick Start for Development

**Common Commands**:
```bash
# Navigate to project
cd /home/jclee/app/splunk

# Create deployment package
tar -czf security_alert.tar.gz security_alert/

# Validate configuration files
python3 -m py_compile security_alert/bin/*.py
grep -n "enableSched" security_alert/default/savedsearches.conf

# Commit changes
git add security_alert/
git commit -m "feat: Your change description"
git push origin master
```

**Testing Alerts** (on Splunk server):
```bash
# Run validators
/opt/splunk/etc/apps/security_alert/bin/auto_validator.py
/opt/splunk/etc/apps/security_alert/bin/deployment_health_check.py

# Check alert status
/opt/splunk/bin/splunk btool savedsearches list | grep -E "^\[0[0-9]{2}_"

# View logs
tail -f /opt/splunk/var/log/splunk/splunkd.log | grep security_alert
```

**Important Directories**:
- **Active development**: `security_alert/` (modify this)
- **Deployment package**: `security_alert.tar.gz` (generated from above)
- **Reference only**: `configs/`, `lookups/`, `docs/` (examples)
- **Legacy (ignore)**: `nextrade/`, `archive-dev/`, `xwiki/`

## 🎯 Project Overview

**Splunk Security Alert System for FortiGate Monitoring** (v2.0.4)

A production-ready Splunk app that provides dynamic, state-aware alert management for FortiGate security events with Slack integration using Block Kit formatting.

**Key Characteristics**:
- **Architecture**: 3-layer system (Dashboards → Python Backend → Splunk Configuration)
- **Alert Strategy**: 15 pre-configured alerts (12 active, 3 state-tracking-only)
- **State Management**: EMS-style state tracking using CSV lookups (prevents duplicate alerts)
- **Slack Integration**: Dual authentication (Bot Token OAuth or Webhook URL)
- **Deployment**: Single tarball package (`security_alert.tar.gz`, ~26KB, 38 files)
- **Data Source**: FortiGate syslog to `index=fw`

---

## 🏗️ High-Level Architecture

### Three-Layer System

```
LAYER 1: PRESENTATION (Splunk Dashboards)
  └─ Data Explorer → Browse FortiGate events
  └─ Alert Management → View/Edit/Delete/Enable alerts
  └─ Custom Dashboards → Real-time metrics

LAYER 2: BUSINESS LOGIC (Python Backend)
  └─ slack_blockkit_alert.py     → Format & send Slack messages
  └─ auto_validator.py           → Validate configuration integrity
  └─ deployment_health_check.py  → Verify deployment status
  └─ splunk_feature_checker.py   → Check Splunk features availability
  └─ fortigate_auto_response.py  → Auto-response actions (optional)

LAYER 3: CONFIGURATION (Splunk Config Files)
  └─ savedsearches.conf    → Alert definitions (15 alerts)
  └─ macros.conf           → Centralized query parameters
  └─ transforms.conf       → Lookup table definitions (10 CSV files)
  └─ alert_actions.conf    → Slack action configuration
  └─ app.conf              → App metadata & Slack credentials
  └─ props.conf            → Auto-field extraction rules
```

### Data Flow

```
FortiGate Syslog
      ↓
Splunk HEC/UDP Input
      ↓
index=fw (raw events)
      ↓
├─ Real-time Saved Searches (15 alerts)
│   ├─ Macro expansion (`fortigate_index`, `logids_*`)
│   ├─ Lookup enrichment (`enrich_with_logid_lookup`)
│   ├─ State tracking (join with *_state_tracker CSV)
│   ├─ Condition evaluation (state changed = 1?)
│   └─ Alert trigger (if true)
│
└─ Alert Triggered
    ├─ Slack action invoked
    ├─ slack_blockkit_alert.py executed
    ├─ Results gzipped & passed to script
    ├─ Block Kit message formatted
    └─ POST to Slack API (Bot Token or Webhook)
          ↓
    Slack Channel (#security-firewall-alert)
```

---

## 🚨 Alert Categories (15 Total)

### Active Alerts (12) - Generate Slack Notifications

**Binary State Changes** (4 alerts - uses EMS state tracking):
- `002_VPN_Tunnel` - VPN tunnel DOWN/UP transitions
- `007_Hardware` - Hardware component FAIL/OK transitions
- `008_HA_State` - HA role change (primary ↔ backup)
- `012_Interface` - Network interface DOWN/UP transitions

**Threshold-Based** (3 alerts - baseline anomaly detection):
- `006_CPU_Memory` - CPU/Memory 20%+ above 8-day baseline
- `010_Resource` - Resource usage >75%
- `015_Traffic_Spike` - Traffic spike 3x above baseline

**Event-Driven** (5 alerts - single-event triggers):
- `001_Config_Change` - Configuration modifications detected
- `011_Admin_Login` - Failed admin authentication attempts
- `013_VPN_Brute_Force` - SSL VPN brute force attacks
- `016_System_Reboot` - System reboot detected
- `017_License` - License expiry warning

### Inactive Alerts (3) - State Tracking Only

These alerts update CSV state files but don't send Slack notifications (`enableSched = 0`):
- `011_Admin_Login` - State tracking only
- `013_VPN_Brute_Force` - State tracking only
- `017_License` - State tracking only

---

## 🔑 Critical Technical Concepts

### 1. EMS State Tracking Pattern

**Problem**: Duplicate alerts (e.g., VPN DOWN → UP → DOWN sends 3 alerts)

**Solution**: CSV-based state tracking (join pattern)

```spl
# Example: Alert 002_VPN_Tunnel
| eval current_state = if(vpn_status="down", "DOWN", "UP")
| join device vpn_name [
    | inputlookup vpn_state_tracker
    | rename state as prev_state ]
| eval changed = if(prev_state != current_state, 1, 0)
| where changed=1
| outputlookup append=t vpn_state_tracker
```

**CSV File Structure** (`*_state_tracker.csv`):
```csv
device,prev_state,current_state,last_change,_key
firewall-01,DOWN,UP,2025-11-04 10:30:45,firewall-01_vpn-site1
firewall-01,UP,UP,2025-11-04 10:35:12,firewall-01_vpn-site2
```

**Benefits**:
- ✅ No alert suppression needed
- ✅ Captures state transitions (DOWN→UP recovery alerts)
- ✅ Persistent state tracking across searches
- ✅ CSV updates with `outputlookup append=t`

### 2. Slack Dual Authentication

**Method 1: Bot Token (OAuth)** - Preferred, more features

```python
# slack_blockkit_alert.py (lines 180-199)
if bot_token.startswith('xoxb-'):
    response = requests.post(
        'https://slack.com/api/chat.postMessage',
        headers={'Authorization': f'Bearer {bot_token}'},
        json=payload
    )
```

**Required Scopes**:
- `chat:write` - Send messages
- `chat:write.public` - Send to public channels
- `channels:read` - List channels

**Method 2: Webhook URL** - Fallback, simpler

```python
# slack_blockkit_alert.py (lines 202-216)
if webhook_url.startswith('https://hooks.slack.com'):
    response = requests.post(webhook_url, json=payload)
```

**Configuration** (both stored in `local/alert_actions.conf`):
```ini
[slack]
param.bot_token = SLACK_BOT_TOKEN_PLACEHOLDER
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK
param.channel = #security-firewall-alert
```

### 3. Block Kit Message Formatting

**Structure** (`slack_blockkit_alert.py`, lines 62-167):

```python
blocks = [
    {
        "type": "header",                    # Title with emoji
        "text": { "type": "plain_text", ... }
    },
    {
        "type": "section",                   # Metadata (Alert, Count, Time, Source)
        "fields": [ ... ]
    },
    {
        "type": "divider"                    # Visual separator
    },
    # Event details (up to 5 events shown)
    {
        "type": "section",
        "fields": [                          # Emoji-enhanced fields
            {"text": "🖥️ *Device:* firewall-01"}
            {"text": "🌐 *Source IP:* 192.168.1.100"}
            ...
        ]
    },
    {
        "type": "context",                   # Footer ("Showing 5 of N events")
        "elements": [ ... ]
    },
    {
        "type": "actions",                   # "View in Splunk" button
        "elements": [ { "type": "button", "url": view_link } ]
    }
]
```

**Key Features**:
- Emoji mapping (🖥️ device, 🌐 IP, 🔐 VPN, etc.)
- Field truncation (100 chars per field, 10 fields per event)
- Event limiting (max 5 events shown, "Showing 5 of N" footer)
- Dynamic severity emoji (🔴 critical, 🟠 high, 🟡 medium, 🔵 low)

### 4. Lookup Table System

**10 State Tracking CSVs** (auto-created if missing):
```
vpn_state_tracker.csv
hardware_state_tracker.csv
ha_state_tracker.csv
interface_state_tracker.csv
cpu_memory_state_tracker.csv
resource_state_tracker.csv
admin_login_state_tracker.csv
vpn_brute_force_state_tracker.csv
traffic_spike_state_tracker.csv
license_state_tracker.csv
```

**3 Reference Lookups** (manually maintained):
```
fortigate_logid_notification_map.csv (6KB, 50+ LogIDs)
auto_response_actions.csv (auto-response rules)
severity_priority.csv (severity mapping)
```

**Additional Threat Intelligence**:
```
abuseipdb_lookup.csv (IP reputation)
virustotal_lookup.csv (malware detection)
ip_whitelist.csv (trusted IPs)
fortinet_mitre_mapping.csv (MITRE ATT&CK mapping)
```

**Lookup Definitions** (`transforms.conf`, lines 1-72):
- `fortigate_logid_lookup` - Maps LogID to description, category, severity
- `auto_response_lookup` - Maps threat pattern to auto-response action
- `*_state_tracker` - No external file mapping, uses `inputlookup` directly

### 5. Macro System (Centralized Configuration)

**Index & Time Range** (`macros.conf`):
```spl
[fortigate_index]
definition = index=fw

[baseline_time_range]
definition = earliest=-8d latest=-1d    # 8-day baseline window

[realtime_time_range]
definition = earliest=-10m latest=now   # Real-time window
```

**Threshold Macros** (`macros.conf`):
```spl
[cpu_high_threshold]
definition = 80

[memory_high_threshold]
definition = 85

[baseline_anomaly_multiplier]
definition = 2          # 2x above baseline = ABNORMAL
```

**LogID Groups** (`macros.conf`, lines 37-94):
```spl
[logids_config_change]
definition = (logid=0100044546 OR logid=0100044547)

[logids_vpn_tunnel]
definition = (logid=0101037124 OR logid=0101037131 OR logid=0101037134)
# ... 12 more LogID macros for each alert
```

**Enrichment Macro** (`macros.conf`, line 100):
```spl
[enrich_with_logid_lookup]
definition = lookup fortigate_logid_lookup logid \
  OUTPUT category,severity,notify_slack,description,available_fields
```

**Usage in Alerts**:
```spl
# Alert 001_Config_Change (savedsearches.conf, line 15)
`fortigate_index` `logids_config_change` \
| `enrich_with_logid_lookup` \
```

---

## 📂 Directory Structure (Source vs. Deployed)

### Repository Root (`/home/jclee/app/splunk/`)

```
/home/jclee/app/splunk/
├── security_alert/              # ✅ PRIMARY - Active development
│   ├── bin/                     # Python backend scripts
│   ├── default/                 # Configuration files
│   ├── lookups/                 # CSV reference data
│   ├── local/                   # User overrides (gitignored)
│   └── metadata/                # Permission settings
│
├── security_alert.tar.gz        # ✅ Deployment package (26KB)
│
├── CLAUDE.md                    # ✅ This file - Development guide
├── README.md                    # ✅ User-facing documentation
├── INSTALLATION_GUIDE.md        # ✅ Installation instructions
│
├── lookups/                     # 📚 Reference - Common CSV templates
├── configs/                     # 📚 Reference - Config examples
├── docs/                        # 📚 Reference - Additional documentation
│
├── nextrade/                    # ❌ LEGACY (v2.0.3) - Ignore
├── archive-dev/                 # ❌ LEGACY - Development archive - Ignore
└── xwiki/                       # ❌ LEGACY - Old documentation - Ignore
```

**Key Points**:
- **Active development**: Only modify `security_alert/` directory
- **Deployment**: Use `security_alert.tar.gz` for production deployment
- **Reference only**: `lookups/`, `configs/`, `docs/` are examples/references
- **Ignore**: `nextrade/`, `archive-dev/`, `xwiki/` are legacy/deprecated

### Source Directory (`/home/jclee/app/splunk/security_alert/`)

```
security_alert/
├── bin/                              # Python backend (5 scripts)
│   ├── slack_blockkit_alert.py      # Format & send Slack messages (283 lines)
│   ├── auto_validator.py            # Validate app integrity (390 lines)
│   ├── deployment_health_check.py   # 10-point health check (533 lines)
│   ├── splunk_feature_checker.py    # Check Splunk version/features
│   └── fortigate_auto_response.py   # Auto-response actions (optional)
│
├── default/                         # Read-only default configuration
│   ├── app.conf                     # App metadata (v2.0.4)
│   ├── alert_actions.conf           # Slack action specs (Python3)
│   ├── savedsearches.conf           # 15 alert definitions
│   ├── macros.conf                  # Centralized query parameters
│   ├── transforms.conf              # Lookup table definitions
│   ├── props.conf                   # Field extraction rules
│   ├── setup.xml                    # Setup UI definition
│   └── data/
│       └── ui/
│           ├── nav/default.xml      # App navigation menu
│           └── views/               # Dashboard XML (if any)
│
├── lookups/                         # CSV reference data (18 files)
│   ├── *_state_tracker.csv (10)    # EMS state tracking
│   ├── fortigate_logid_notification_map.csv
│   ├── severity_priority.csv
│   ├── auto_response_actions.csv
│   └── [threat intel lookups]
│
├── local/                           # User-modified configuration
│   └── [User overrides of default/ files]
│
└── metadata/
    └── default.meta                 # Permission settings
```

### Deployed Directory (`/opt/splunk/etc/apps/security_alert/`)

**Same structure as source**. Key points:
- `default/` = Read-only app defaults
- `local/` = User modifications (created during setup)
- `lookups/` = CSV files (modified by alert runs via `outputlookup`)
- `bin/` = Python scripts must have execute permissions

---

## 🔧 Configuration File Hierarchy

**Priority** (highest to lowest):
1. `local/` - User modifications (created by Setup UI or manual edits)
2. `default/` - App defaults
3. `/opt/splunk/etc/system/` - Splunk system defaults

**Example**: When both `default/alert_actions.conf` and `local/alert_actions.conf` exist:
- Settings in `local/` override `default/`
- Slack token goes to `local/alert_actions.conf` (via Setup UI)

---

## 🚀 Deployment Commands

### Development Workflow

**1. Make Changes**:
```bash
cd /home/jclee/app/splunk

# Edit files in security_alert/ directory
vim security_alert/default/savedsearches.conf
vim security_alert/bin/slack_blockkit_alert.py
```

**2. Test Locally** (if possible):
```bash
# Validate Python syntax
python3 -m py_compile security_alert/bin/*.py

# Check for common config errors
grep -n "enableSched" security_alert/default/savedsearches.conf
```

**3. Commit Changes**:
```bash
# Stage changes
git add security_alert/

# Commit with descriptive message
git commit -m "feat: Add new alert for XYZ"
# or
git commit -m "fix: Correct LogID mapping for alert 002"

# Push to repository
git push origin master
```

### Package Creation

```bash
# Update source after modifications
cd /home/jclee/app/splunk

# Create tarball for deployment
tar -czf security_alert.tar.gz security_alert/

# Verify tarball contents
tar -tzf security_alert.tar.gz | head -20

# Check file count
tar -tzf security_alert.tar.gz | wc -l  # Should be ~38 files

# View final size
ls -lh security_alert.tar.gz            # Should be ~26KB
```

### Web UI Deployment (Recommended)

```
1. Splunk Web → Apps → Manage Apps → Install app from file
2. Upload security_alert.tar.gz
3. Click "Upload"
4. Splunk prompts restart → Click "Restart Splunk"
5. After restart, go to Apps → Security Alert System → Setup
6. Enter Slack credentials → Save
```

### CLI Deployment

```bash
# Copy to Splunk server
scp security_alert.tar.gz splunk-server:/tmp/

# SSH to Splunk server
ssh splunk-server
cd /opt/splunk/etc/apps/

# Extract
sudo tar -xzf /tmp/security_alert.tar.gz

# Fix permissions
sudo chown -R splunk:splunk security_alert

# Restart Splunk
sudo /opt/splunk/bin/splunk restart
```

### Post-Deployment Validation

```bash
# Check file structure
ls -la /opt/splunk/etc/apps/security_alert/

# Verify Python script permissions
ls -la /opt/splunk/etc/apps/security_alert/bin/*.py
# Should show: -rwxr-xr-x (755)

# Check if app is enabled
/opt/splunk/bin/splunk display app security_alert

# Tail logs for errors
tail -f /opt/splunk/var/log/splunk/splunkd.log | grep security_alert
```

---

## ✅ Testing & Validation

### Automated Validation Scripts

**Run all validators**:
```bash
# From Splunk server
/opt/splunk/etc/apps/security_alert/bin/auto_validator.py
/opt/splunk/etc/apps/security_alert/bin/deployment_health_check.py
/opt/splunk/etc/apps/security_alert/bin/splunk_feature_checker.py
```

**Auto Validator** (`auto_validator.py`, 390 lines):
- Validates 13 CSV lookup files (checks headers, row counts)
- Checks `transforms.conf` stanzas
- Checks `props.conf` auto-lookup definitions
- Validates SPL syntax in savedsearches.conf
- Verifies cron_schedule format (5-field requirement)
- Checks `alert_actions.conf` for Slack parameters

**Deployment Health Check** (`deployment_health_check.py`, 533 lines):
- 10-point system health check:
  1. File structure (required dirs/files)
  2. Splunk service status
  3. App enabled/disabled status
  4. Data availability (`index=fw`)
  5. Alert scheduler status (count of active alerts)
  6. Slack integration config
  7. Lookup file health (detect empty files)
  8. REST API endpoint definitions
  9. Dashboard accessibility
  10. Python script permissions
- Output: Human-readable or JSON (`--json` flag)

### Manual Testing

**Verify data in index**:
```spl
index=fw earliest=-1h | stats count
# Should return count > 0
```

**Check alert execution**:
```spl
index=_internal source=*scheduler.log savedsearch_name="*Alert*"
| stats count by savedsearch_name, status
```

**Monitor Slack notifications**:
```spl
index=_internal source=*alert_actions.log "slack"
| table _time, action_mode, sid, search_name, result
```

**Test specific alert manually**:
```spl
# Alert 001: Config Change
index=fw earliest=rt-10m latest=rt logid=0100044546 OR logid=0100044547
| table _time, devname, user, cfgpath, msg

# Alert 002: VPN Tunnel
index=fw earliest=rt-10m latest=rt logid=0101037124 OR logid=0101037131 OR logid=0101037134
| table _time, devname, vpn_name, vpn_status, msg

# Alert 006: CPU/Memory Anomaly
index=fw earliest=rt-10m latest=rt logid=0104043001 OR logid=0104043002
| table _time, devname, cpu, memory, session_count

# Alert 007: Hardware Failure
index=fw earliest=rt-10m latest=rt logid=0103040001 OR logid=0103040002 OR logid=0103040003
| table _time, devname, component, status, msg

# Alert 008: HA State Change
index=fw earliest=rt-10m latest=rt logid=0100020010 OR logid=0104043544 OR logid=0104043545
| table _time, devname, ha_role, ha_state, msg
```

**View state tracking**:
```spl
| inputlookup vpn_state_tracker
| inputlookup hardware_state_tracker
| inputlookup ha_state_tracker
| inputlookup cpu_memory_state_tracker
| inputlookup interface_state_tracker
```

---

## 🔍 Understanding File Modifications

### When to Modify `default/` vs. `local/`

**Never modify `default/`** (except during development):
- `default/` files are the app source
- User changes go to `local/` automatically
- Splunk merges `local/` over `default/`

**Modify `default/` only when**:
- Updating base alert definitions (savedsearches.conf)
- Adding new macros (macros.conf)
- Updating LogID mappings (transforms.conf, fortigate_logid_notification_map.csv)
- Changing app metadata (app.conf)

**Modify `local/` when**:
- Configuring Slack credentials (Setup UI writes here)
- Disabling/enabling specific alerts
- Creating custom dashboards

### Key Configuration Files Explained

**`savedsearches.conf` (15 alerts)**:
- Each alert is a stanza: `[001_Config_Change]`, `[002_VPN_Tunnel]`, etc.
- Fields:
  - `search =` - SPL query (expands macros, joins lookups)
  - `cron_schedule =` - Cron format: `minute hour day month weekday`
  - `enableSched =` - 1 (active) or 0 (disabled/state-tracking-only)
  - `realtime_schedule =` - 1 (real-time) or 0 (scheduled)
  - `dispatch.earliest_time =` - Time range: `rt-10m` (real-time 10min window)
  - `alert.suppress =` - 1 (suppress duplicates)
  - `alert.suppress.fields =` - Grouping key for suppression
  - `alert.suppress.period =` - Duration: `5m`, `10m`, `15m`, or `30m`
  - `action.slack =` - 1 (send to Slack)
  - `action.slack.param.channel =` - Target channel: `#security-firewall-alert`

**`macros.conf` (centralized parameters)**:
- Index definition: `[fortigate_index]`
- Time ranges: `[baseline_time_range]`, `[realtime_time_range]`
- Thresholds: `[cpu_high_threshold]`, `[memory_high_threshold]`
- LogID groups: `[logids_config_change]`, `[logids_vpn_tunnel]`, etc. (12 total)
- Enrichment macro: `[enrich_with_logid_lookup]`
- Used in alerts: `` `fortigate_index` `logids_vpn_tunnel` ``

**`transforms.conf` (lookup definitions)**:
- Maps CSV filename to lookup name
- Example: `[fortigate_logid_lookup]` points to `fortigate_logid_notification_map.csv`
- No mappings needed for `*_state_tracker.csv` (used via `inputlookup` directly)

**`alert_actions.conf` (Slack configuration)**:
- Defines alert action: `[slack]`
- Parameters:
  - `param.bot_token =` - OAuth bot token (xoxb-<example>)
  - `param.webhook_url =` - Incoming webhook URL (https://hooks.slack.com/...)
  - `param.channel =` - Default channel (#security-firewall-alert)
  - `python.version = python3` - Required for Python 3 scripts

**`app.conf` (metadata)**:
- App visibility, version, description
- Slack credentials stored here (via Setup UI)

---

## 🛠️ Common Modification Scenarios

### Adding a New Alert

**Step 1**: Add LogID macro to `macros.conf`
```ini
[logids_new_threat]
definition = (logid=0100012345 OR logid=0100012346)
iseval = 0
```

**Step 2**: Create state tracker CSV in `lookups/` (if binary state alert)
```csv
device,prev_state,current_state,last_change,_key
```

**Step 3**: Add stanza to `savedsearches.conf`
```ini
[018_New_Alert_Name]
description = Description of what this detects
search = `fortigate_index` `logids_new_threat` \
| eval device = coalesce(devname, "unknown") \
| eval current_state = "ABNORMAL" \
| join device [ \
  | inputlookup new_threat_state_tracker ] \
| eval changed = if(prev_state != current_state, 1, 0) \
| where changed=1 \
| outputlookup append=t new_threat_state_tracker \
| table _time, device, logdesc, msg

cron_schedule = * * * * *
enableSched = 1
realtime_schedule = 1
dispatch.earliest_time = rt-10m
dispatch.latest_time = rt
alert.track = 1
alert.severity = 4
alert.suppress = 1
alert.suppress.fields = device
alert.suppress.period = 10m
alert.expires = 24h
action.slack = 1
action.slack.param.channel = #security-firewall-alert
```

**Step 4**: Redeploy
```bash
cd /home/jclee/app/splunk
tar -czf security_alert.tar.gz security_alert/
# Deploy via Web UI or CLI
```

### Changing Alert Thresholds

**CPU Memory Threshold** (Alert 006):
1. Edit `macros.conf`: Change `[cpu_high_threshold]` or `[memory_high_threshold]`
2. Edit `savedsearches.conf`: Alert 006 uses these macros in baseline calculation
3. Redeploy

**Resource Limit Threshold** (Alert 010):
1. Edit `savedsearches.conf` (line 143): `where resource_usage > 75` → change 75 to desired %
2. Redeploy

### Modifying Slack Message Format

**Block Kit Structure** (`slack_blockkit_alert.py`, lines 62-167):
1. Edit field ordering (lines 111-121)
2. Add/remove emoji mappings (lines 46-57)
3. Adjust event limit (line 105: `results[:5]` → `results[:10]`)
4. Redeploy

**Alert-Specific Message** (`savedsearches.conf`):
- Field: `action.slack.param.message = [Custom title]`
- Used in Slack action as subtitle
- Supports field references: `$result.device$`

---

## 🔐 Security Considerations

### Slack Token Management

**Storage**:
- Tokens stored in `local/alert_actions.conf` with restricted permissions
- Setup UI writes tokens securely (via Splunk encryption if available)

**Best Practices**:
- Use Bot Token (OAuth) over Webhook URLs for better audit trail
- Rotate tokens regularly (monthly recommended)
- Don't commit `local/alert_actions.conf` to Git
- Separate tokens for dev/staging/prod environments

### Data Exposure in Alerts

**Sensitive Fields Included**:
- Device names (may reveal internal infrastructure)
- Source/destination IPs (network topology)
- Usernames (login failures)
- Configuration changes (security policy details)

**Mitigations**:
- Restrict Slack channel access to security team only
- Use private channels (#security-firewall-alert vs. public)
- Consider sanitizing data in `slack_blockkit_alert.py`:
  ```python
  def sanitize_ip(ip):
      parts = ip.split('.')
      return f"{parts[0]}.{parts[1]}.{parts[2]}.xxx"
  ```

### Alert Definition Integrity

**Protection Mechanisms**:
- `auto_validator.py` catches SPL syntax errors
- `deployment_health_check.py` verifies configurations
- CSV lookups prevent alert tampering (read-only after creation)
- Splunk native RBAC (permissions in `metadata/default.meta`)

---

## 📊 Key CSV Lookup Files

### State Tracking CSVs (EMS Pattern)

**Standard Format** (all 10 files follow this):
```csv
device,prev_state,current_state,last_change,_key
firewall-01,DOWN,UP,2025-11-04 10:35:12,key_value
```

**Auto-created by** `auto_validator.py` if missing

**Updated by** alerts using `outputlookup append=t`

### Reference Lookups

**fortigate_logid_notification_map.csv** (6KB, 50+ LogIDs):
- Columns: `logid`, `category`, `severity`, `notify_slack`, `notify_email`, `description`, `available_fields`, `field_coverage`
- Used by `enrich_with_logid_lookup` macro
- Maps every LogID to alert metadata

**auto_response_actions.csv**:
- Columns: `threat_pattern`, `action`, `severity`, `enabled`
- For auto-response automation (Alert 004 if enabled)

**severity_priority.csv**:
- Maps severity levels to priority for triage

### Threat Intelligence Lookups

**abuseipdb_lookup.csv**:
- IP reputation data (AbuseIPDB API)
- Columns: `ip_address`, `abuse_score`, `total_reports`

**virustotal_lookup.csv**:
- Malware detection results (VirusTotal API)
- Columns: `hash`, `detection_ratio`, `last_analysis_date`

**ip_whitelist.csv**:
- Trusted internal IPs (prevent false positives)
- Columns: `ip_address`, `subnet`, `description`, `exempt_alerts`

---

## 🐛 Troubleshooting

### Alerts Not Triggering

**Diagnosis**:
```bash
# 1. Check data exists
index=fw earliest=-1h | stats count  # Should be > 0

# 2. Check alert is enabled
/opt/splunk/bin/splunk btool savedsearches list 002_VPN_Tunnel | grep enableSched

# 3. Check scheduler status
index=_internal source=*scheduler.log savedsearch_name="*Alert*"

# 4. Run alert manually
index=fw earliest=rt-10m latest=rt logid=0101037124
```

**Common Issues**:
- `enableSched = 0` (alert disabled)
- `index=fw` has no data in past 10 minutes
- Cron schedule syntax error
- LogID not matching actual logs

### Slack Messages Not Received

**Diagnosis**:
```bash
# 1. Test credentials
curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer SLACK_BOT_TOKEN_PLACEHOLDER"
# Expected: {"ok":true,"user":"bot-name"}

# 2. Check alert action logs
index=_internal source=*alert_actions.log action_name="slack"

# 3. Verify channel exists and bot is invited
# In Slack: /invite @BotName to #security-firewall-alert
```

**Common Issues**:
- Bot token not configured (Setup UI not completed)
- Bot not invited to channel
- OAuth scopes missing: `chat:write`, `chat:write.public`, `channels:read`
- Network/firewall blocking Slack API

### Auto Validator Failures

**Check output**:
```bash
/opt/splunk/etc/apps/security_alert/bin/auto_validator.py

# Output includes:
# ❌ 오류 (errors) - Fix immediately
# ⚠️ 경고 (warnings) - Address before production
# ✅ 정상 (OK) - No action needed
```

**Common Errors**:
- Missing CSV files (auto-creation fails due to permissions)
- transforms.conf stanzas missing
- savedsearches.conf SPL syntax errors
- alert_actions.conf missing `[slack]` stanza
- Python 3 version not specified

### Deployment Health Check Warnings

**Check output**:
```bash
/opt/splunk/etc/apps/security_alert/bin/deployment_health_check.py

# 10 checks performed:
# 1. File structure
# 2. Splunk service
# 3. App status
# 4. Data availability
# 5. Scheduler status
# 6. Slack integration
# 7. Lookup health
# 8. REST API
# 9. Dashboards
# 10. Script permissions
```

**Common Warnings**:
- No data in `index=fw` (expected until FortiGate logs arrive)
- Slack credentials not configured (Setup UI incomplete)
- Scripts missing execute permission (`chmod +x *.py`)
- Empty CSV lookup files (expected for state trackers before first run)

---

## 📚 Key Files Reference

**Most Important** (modify these when updating app):
- `security_alert/default/savedsearches.conf` - Alert definitions (15 alerts)
- `security_alert/default/macros.conf` - Centralized configuration
- `security_alert/bin/slack_blockkit_alert.py` - Slack message formatting
- `security_alert/lookups/fortigate_logid_notification_map.csv` - LogID reference (6KB)

**Support Scripts** (auto-validation):
- `security_alert/bin/auto_validator.py` - Verify configuration integrity
- `security_alert/bin/deployment_health_check.py` - 10-point system health check
- `security_alert/bin/splunk_feature_checker.py` - Splunk version/feature check

**Validation Tools** (run after deployment):
- `deployment_health_check.py --json` - JSON output for scripting
- `auto_validator.py` - Comprehensive configuration validation
- Splunk btool: `/opt/splunk/bin/splunk btool savedsearches list`

---

## 🔄 Update Workflow

**When Updating Source Files**:

1. Edit in `/home/jclee/app/splunk/security_alert/`
2. Run validators locally (if possible)
3. Create tarball: `tar -czf security_alert.tar.gz security_alert/`
4. Deploy to test Splunk first
5. Run health check: `deployment_health_check.py`
6. Test alerts manually
7. Deploy to production

**Post-Deployment**:
```bash
# Verify deployment
ls -la /opt/splunk/etc/apps/security_alert/

# Run validators
/opt/splunk/etc/apps/security_alert/bin/auto_validator.py
/opt/splunk/etc/apps/security_alert/bin/deployment_health_check.py

# Check logs
tail -100 /opt/splunk/var/log/splunk/splunkd.log | grep security_alert
```

---

## 📝 Version & Maintenance

**Current Version**: v2.0.4 (2025-11-04)

**Changelog**:
- v2.0.4: EMS state tracking, Slack Block Kit, 15 alerts (12 active + 3 state-tracking)
- v2.0.3: Dynamic alert generation (not used, pre-configured alerts preferred)
- v2.0.0: Initial release with 8 core alerts

**Repository**: https://github.com/qws941/splunk.git

**Last Updated**: 2025-11-04
**Maintainer**: NextTrade Security Team
**Support**: Use validators and health check scripts for troubleshooting

---

## 🎯 Quick Decision Tree

**When working with this app, ask yourself**:

1. **Need to modify alerts?**
   - Edit `savedsearches.conf` in source
   - Add LogID to `macros.conf`
   - Update `fortigate_logid_notification_map.csv`
   - Redeploy tarball

2. **Slack not working?**
   - Run `deployment_health_check.py` → Check Slack section
   - Verify bot is invited to channel
   - Test token: `curl https://slack.com/api/auth.test`

3. **Alerts not triggering?**
   - Check `index=fw` has data
   - Verify `enableSched = 1`
   - Run alert manually in Splunk

4. **Need to understand alert logic?**
   - Read `savedsearches.conf` stanza
   - Expand macros from `macros.conf`
   - Trace join with `*_state_tracker.csv`
   - Understand state change detection

5. **Deployment failed?**
   - Run `auto_validator.py` → Fix errors
   - Run `deployment_health_check.py` → Fix warnings
   - Check file permissions (scripts need 755)
   - Check `splunkd.log` for startup errors
