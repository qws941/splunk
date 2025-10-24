# FMG/FAZ Modular Architecture Deployment Guide

**Version**: 2.0 (Modular & Advanced)
**Date**: 2025-10-24
**Purpose**: Deploy modularized FMG/FAZ monitoring with critical alert filtering

---

## 📦 Architecture Overview

### Modular Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Splunk Architecture                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐      ┌──────────────────┐             │
│  │  LogID Filters  │      │   SPL Macros     │             │
│  │  (26 exclusions)│──────│   (50+ reusable) │             │
│  └─────────────────┘      └──────────────────┘             │
│           │                         │                        │
│           ▼                         ▼                        │
│  ┌─────────────────────────────────────────────┐            │
│  │         Dashboard Studio JSON                │            │
│  │  - 12 panels (macro-based queries)          │            │
│  │  - Critical alerts only (filtered)          │            │
│  │  - 80 device monitoring                     │            │
│  └─────────────────────────────────────────────┘            │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────┐            │
│  │         index=fw (sourcetype-based)         │            │
│  │  - sourcetype=fmg:* (config/audit/device)  │            │
│  │  - sourcetype=faz:* (event/traffic/utm)    │            │
│  └─────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Critical Alert Filtering

**Excluded LogIDs (26 total)**:
- **Login Failures** (13 logids): Admin login, VPN auth, firewall auth
- **Update Failures** (11 logids): Signature updates, firmware updates, FortiGuard
- **Result**: Only actionable critical alerts (security incidents)

---

## 🚀 Deployment Steps

### 1. Prerequisites

```bash
# Verify Splunk version (require 9.0+ for Dashboard Studio)
$SPLUNK_HOME/bin/splunk version

# Check existing indexes
$SPLUNK_HOME/bin/splunk list index | grep "fw"

# Verify data ingestion
splunk search "index=fw | head 10"
```

### 2. Deploy Configuration Files

```bash
cd /home/jclee/app/splunk

# Copy configurations to Splunk
sudo cp configs/fmg-faz-logid-exclusions.conf \
  $SPLUNK_HOME/etc/apps/search/local/

sudo cp configs/macros-fmg-faz.conf \
  $SPLUNK_HOME/etc/apps/search/local/macros.conf

sudo cp configs/props-fmg-faz.conf \
  $SPLUNK_HOME/etc/apps/search/local/props.conf

sudo cp configs/indexes-fmg-faz.conf \
  $SPLUNK_HOME/etc/apps/search/local/indexes.conf

# Deploy Dashboard Studio JSON
sudo cp configs/dashboards/studio/fmg-faz-operations.json \
  $SPLUNK_HOME/etc/apps/search/local/data/ui/views/fmg_faz_operations.json

# Set permissions
sudo chown -R splunk:splunk $SPLUNK_HOME/etc/apps/search/local
```

### 3. Restart Splunk

```bash
# Method 1: Graceful restart
sudo $SPLUNK_HOME/bin/splunk restart

# Method 2: Quick restart (faster, no active search wait)
sudo $SPLUNK_HOME/bin/splunk restart --answer-yes

# Method 3: Debug mode (if restart fails)
sudo $SPLUNK_HOME/bin/splunk restart --debug
```

### 4. Verify Deployment

#### Check Macros

```bash
# List all FMG/FAZ macros
splunk btool macros list | grep -A 2 "fmg\|faz"

# Test critical alert macro
splunk search "`faz_critical_events` earliest=-1h | head 10"
```

#### Check Dashboard

```bash
# Via Web UI
open https://splunk.jclee.me:8000/app/search/fmg_faz_operations

# Via REST API
curl -k -u admin:password \
  https://splunk.jclee.me:8000/servicesNS/nobody/search/data/ui/views/fmg_faz_operations
```

#### Validate LogID Exclusions

```spl
# Count excluded events (should be login/update failures only)
index=fw sourcetype=faz:event severity="critical"
logid IN ("0100032001","0100032002","0100032003",...)
| stats count by logid, msg
| sort -count

# Count included events (should be security incidents)
`faz_critical_events` earliest=-24h
| stats count by log_subtype, msg
| sort -count
```

---

## 🔧 Configuration Details

### File: `fmg-faz-logid-exclusions.conf`

**Purpose**: Centralized logid exclusion list
**Location**: `$SPLUNK_HOME/etc/apps/search/local/`
**Size**: ~150 lines

**Key Sections**:
- `[faz_login_failure_logids]` - 13 logids
- `[faz_update_failure_logids]` - 11 logids
- `[faz_excluded_logids_all]` - Combined list (26 logids)

**Maintenance**: Review quarterly, add new noise patterns

### File: `macros-fmg-faz.conf`

**Purpose**: Reusable SPL search patterns
**Location**: `$SPLUNK_HOME/etc/apps/search/local/macros.conf`
**Size**: ~270 lines, 50+ macros

**Key Macros**:
- `faz_critical_events` - Critical alerts with exclusions
- `fmg_config_search` - FMG configuration changes
- `faz_blocked_events` - Blocked traffic events
- `format_timestamp` - Timestamp formatting
- `add_status_icon` - Status icon helper

**Usage Example**:
```spl
`faz_critical_events` `time_last_24h`
| `format_timestamp`
| table formatted_time, src_ip, dst_ip, msg
```

### File: `props-fmg-faz.conf`

**Purpose**: Field extraction for 6 sourcetypes
**Location**: `$SPLUNK_HOME/etc/apps/search/local/props.conf`
**Size**: ~240 lines

**Sourcetypes**:
- `fmg:config` - Configuration changes
- `fmg:audit` - Admin audit logs
- `fmg:device` - Device inventory
- `faz:event` - Security events
- `faz:traffic` - Traffic logs
- `faz:utm` - UTM logs (IPS/AV/Web)

### File: `fmg-faz-operations.json`

**Purpose**: Dashboard Studio JSON
**Location**: `$SPLUNK_HOME/etc/apps/search/local/data/ui/views/`
**Size**: ~310 lines, 12 panels

**Panels**:
1. FMG Config Changes (24h)
2. Active Administrators
3. Connected Devices / 80
4. FAZ Critical Alerts Only (filtered)
5. FMG Configuration Changes Timeline
6. Recent Configuration Changes (Last 50)
7. Critical Events Timeline (line chart)
8. Top Critical Threats (Action Required)
9. Top Blocked Source IPs
10. FMG Device Inventory & Health
11. FAZ Traffic Top Talkers (Last Hour)
12. FMG Admin Activity Audit

---

## 🧪 Testing Checklist

### Functional Tests

- [ ] **Macro Execution**: `splunk search "`faz_critical_events` | head 10"`
- [ ] **LogID Filtering**: Verify no login/update failures in critical alerts
- [ ] **Dashboard Load**: Dashboard loads without errors (< 5 seconds)
- [ ] **Device Count**: Shows "X / 80" connected devices
- [ ] **Time Range Picker**: Changing time range updates all panels
- [ ] **Device Filter**: Filtering by device updates relevant panels

### Data Quality Tests

- [ ] **Critical Event Count**: `faz_critical_events` count matches expected volume
- [ ] **Exclusion Rate**: Excluded events = 10-30% of total critical events
- [ ] **False Negative Check**: Manual review of 10 excluded events (should be noise)
- [ ] **False Positive Check**: Manual review of 10 included events (should be incidents)

### Performance Tests

```spl
# Measure macro performance
| rest /services/search/jobs
| search label="faz_critical_events*"
| stats avg(runDuration) as avg_runtime_sec, max(runDuration) as max_runtime_sec

# Expected: avg < 3 seconds, max < 10 seconds
```

---

## 📊 Monitoring & Maintenance

### Daily Health Checks

```spl
# 1. Data ingestion rate
index=fw sourcetype=fmg:* OR sourcetype=faz:* earliest=-1h
| bin _time span=1m
| stats count as events_per_min by _time
| eventstats avg(events_per_min) as avg_rate
| where events_per_min < (avg_rate * 0.5)  # Alert if < 50% of average
```

```spl
# 2. Critical alert volume (should be < 100/day for 80 devices)
`faz_critical_events` `time_last_24h`
| stats count
| where count > 100  # Alert if too many critical alerts
```

```spl
# 3. Device connectivity (should be > 75 devices up)
`fmg_connected_devices`
| stats count as connected
| where connected < 75  # Alert if < 75 devices online
```

### Weekly Reviews

- **Excluded LogID Review**: Check if new noise patterns emerged
- **Macro Performance**: Review slow-running macros
- **Dashboard Usage**: Check dashboard views (Splunk internal logs)

### Quarterly Tasks

- **LogID List Update**: Add new exclusions if needed
- **Macro Optimization**: Refactor slow macros
- **Field Extraction Tuning**: Update props.conf for new log formats

---

## 🔧 Troubleshooting

### Issue 1: Macros Not Found

**Symptom**: Dashboard shows "Unknown search command `faz_critical_events`"

**Solution**:
```bash
# Verify macros deployed
splunk btool macros list | grep faz_critical_events

# If not found, redeploy macros.conf
sudo cp configs/macros-fmg-faz.conf \
  $SPLUNK_HOME/etc/apps/search/local/macros.conf
sudo $SPLUNK_HOME/bin/splunk restart
```

### Issue 2: Too Many Critical Alerts

**Symptom**: Dashboard shows 500+ critical events/day

**Diagnosis**:
```spl
# Check what's triggering critical alerts
`faz_critical_events` `time_last_24h`
| stats count by logid, msg
| sort -count
| head 20
```

**Solution**: Add noisy logids to `fmg-faz-logid-exclusions.conf`

### Issue 3: Dashboard Loads Slowly (> 10 seconds)

**Diagnosis**:
```spl
# Check macro performance
| rest /services/search/jobs
| search label="*fmg*faz*"
| stats avg(runDuration) as avg_sec, max(runDuration) as max_sec by label
| sort -max_sec
```

**Solutions**:
- Enable data model acceleration for `Fortinet_Security`
- Use `tstats` instead of raw searches in macros
- Reduce time range (24h → 6h)
- Add more specific filters early in searches

### Issue 4: Missing Device Data

**Symptom**: "0 / 80" devices shown

**Diagnosis**:
```spl
# Check if device data exists
index=fw sourcetype=fmg:device
| head 10

# Check field extraction
index=fw sourcetype=fmg:device
| table _raw, device_name, connection_status
```

**Solution**: Verify `props-fmg-faz.conf` field extraction rules deployed

---

## 📚 Reference

### Key Macros Quick Reference

| Macro | Purpose | Example |
|-------|---------|---------|
| `faz_critical_events` | Filtered critical alerts | `\`faz_critical_events\` \| stats count` |
| `fmg_config_search` | FMG config changes | `\`fmg_config_search\` \| stats count by admin_user` |
| `faz_blocked_events` | Blocked traffic | `\`faz_blocked_events\` \| stats count by src_ip` |
| `time_last_24h` | Time range macro | `\`faz_event_search\` \`time_last_24h\`` |
| `format_timestamp` | Format _time field | `\| \`format_timestamp\` \| table formatted_time` |

### Excluded LogID Categories

| Category | Count | Examples |
|----------|-------|----------|
| Admin login failures | 5 | 0100032001-0100032005 |
| VPN auth failures | 5 | 0101039424-0101039428 |
| Firewall auth failures | 3 | 0102043008-0102043010 |
| Signature updates | 4 | 0104044001-0104044004 |
| Firmware updates | 4 | 0103043200-0103043203 |
| System updates | 3 | 0100033100-0100033102 |

### Dashboard Panel Query Patterns

All panels use macro-based queries for consistency:

```javascript
// Pattern 1: Simple metric
{
  "query": "`faz_critical_events` earliest=$time_range.earliest$ latest=$time_range.latest$\n| stats count as event_count"
}

// Pattern 2: Timeline chart
{
  "query": "`fmg_config_search` device_name=$device_filter$ earliest=$time_range.earliest$ latest=$time_range.latest$\n| timechart count by config_operation"
}

// Pattern 3: Table with formatting
{
  "query": "`fmg_audit_search` earliest=$time_range.earliest$ latest=$time_range.latest$\n| `format_timestamp`\n| `add_status_icon`\n| table formatted_time, status_icon, admin_user"
}
```

---

## 🎯 Success Criteria

Deployment is successful when:

- ✅ Dashboard loads in < 5 seconds
- ✅ Critical alert count = 10-100/day (filtered from 50-500/day)
- ✅ Device count shows "75-80 / 80" (> 93% uptime)
- ✅ No macro execution errors in `index=_internal source=*splunkd.log`
- ✅ All 12 panels display data (no "No results found")

---

**Deployed By**: Claude Code
**Repository**: https://git.jclee.me/gitadmin/splunk.git
**Support**: Check `CLAUDE.md` for project-specific instructions
