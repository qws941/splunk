# FortiGate Slack Alerts - Final Production Files

**Status**: ✅ Production Ready
**Last Updated**: 2025-10-28
**Language**: English

---

## 📁 Essential Files (Only 3 Required!)

### 1. Alert Configuration ⭐ MOST IMPORTANT

**File**: `savedsearches-fortigate-alerts.conf` (3.9 KB)

**What it contains**:
- 3 real-time alerts: Config Change, Critical Event, HA Event
- English field names (SPL parser compatible)
- Simple text messages (no Block Kit)
- Unified Slack channel: `#security-firewall-alert`
- 3-layer deduplication (no alert spam)

**How to deploy (Web UI method)**:
```
Splunk Web UI → Settings → Searches, reports, and alerts → New Alert

For EACH alert (3 total):
1. Title: Copy alert name from conf file (e.g., FortiGate_Config_Change_Alert)
2. Search: Copy entire SPL query starting from "index=fw" to "| table ..."
3. Alert Type: Real-time
4. Trigger: Number of Results > 0
5. Actions: Add action → Slack
   - Channel: #security-firewall-alert
   - Message: $result.alert_message$
6. Throttle: Enable "Suppress results containing field values"
   - Fields: user, cfgpath (for Alert 1) / devname, logid (for Alert 2, 3)
   - Suppress for: 15 seconds
7. Save
```

**Copy these SPL queries from the conf file**:
- Alert 1: Lines 10-22 (Config Change Alert)
- Alert 2: Lines 52-61 (Critical Event Alert)
- Alert 3: Lines 91-99 (HA Event Alert)

---

### 2. Main Dashboard

**File**: `dashboards/fortigate-monitoring.xml` (21 KB)

**What it contains**:
- Alert ON/OFF controls (JavaScript buttons)
- Alert status display (✅/🔴)
- Configuration changes (last 50)
- Operational events (last 50)
- Time-series charts (event trends)

**How to deploy**:
```
Splunk Web UI → Dashboards → Create New Dashboard → Classic Dashboards

1. Create New Dashboard
   - Title: FortiGate Real-time Monitoring
   - ID: fortigate_monitoring
   - Permissions: Shared in App

2. Edit → Source (top right corner)

3. Copy ENTIRE XML from:
   dashboards/fortigate-monitoring.xml

4. Paste into source editor

5. Save
```

---

### 3. Syslog Input (UDP)

**File**: `inputs-udp.conf` (6.7 KB)

**What it contains**:
- UDP port 6514 (FortiGate default syslog port)
- Sourcetype: `fgt_log`
- Index: `fw`
- Multi-device support

**How to deploy**:
```
Splunk Web UI → Settings → Data inputs → UDP → New Local UDP

Port: 6514
Source name: fortigate
Source type: fgt_log
Host: IP
Index: fw
```

---

## 📋 Optional Files (If Needed)

### Additional Dashboards (2 files)

**File**: `dashboards/fmg-all-changes-v2.xml` (8.0 KB)
- Detailed configuration change analysis
- Policy, Address, Service breakdown
- Admin activity tracking

**File**: `dashboards/fmg-operational-events.xml` (9.5 KB)
- Operational event detailed analysis
- System, HA, Interface events
- Critical/Error event filtering

**Deployment**: Same as main dashboard

---

### Deployment Script (PowerShell)

**File**: `Deploy-SplunkDashboards.ps1`

**Usage**:
```powershell
.\Deploy-SplunkDashboards.ps1 `
    -SplunkHost "192.168.x.x" `
    -SplunkPass "password"
```

**What it does**:
- Deploys dashboards via REST API
- Requires .env file with credentials
- Windows PowerShell 5.1+ or PowerShell Core 7+

---

## 🚀 Quick Start (10 Minutes)

### Step 1: Deploy Alerts (5 minutes)

```
1. Open savedsearches-fortigate-alerts.conf
2. Splunk Web → Settings → Searches, reports, and alerts
3. Create Alert 1: FortiGate_Config_Change_Alert
   - Copy SPL query (lines 10-22)
   - Set Real-time, Slack action, Throttle 15s
4. Create Alert 2: FortiGate_Critical_Event_Alert
   - Copy SPL query (lines 52-61)
   - Set Real-time, Slack action, Throttle 15s
5. Create Alert 3: FortiGate_HA_Event_Alert
   - Copy SPL query (lines 91-99)
   - Set Real-time, Slack action, Throttle 15s
```

### Step 2: Deploy Dashboard (2 minutes)

```
1. Open dashboards/fortigate-monitoring.xml
2. Splunk Web → Dashboards → Create → Classic
3. Edit → Source
4. Copy XML → Paste → Save
```

### Step 3: Configure UDP Input (1 minute)

```
Splunk Web → Settings → Data inputs → UDP → New
Port: 6514
Source type: fgt_log
Index: fw
```

### Step 4: Configure FortiGate (2 minutes)

```bash
# SSH to FortiGate
config log syslogd setting
  set status enable
  set server "your-splunk-ip"
  set port 6514
  set format default
end
```

### Step 5: Verify (2 minutes)

```spl
# Check data
index=fw earliest=-5m | stats count

# Check alerts
| rest /services/saved/searches
| search title="FortiGate_*"
| table title, disabled
```

---

## ✅ Verification Checklist

### Data Flow
- [ ] FortiGate sending syslog to Splunk port 6514
- [ ] Splunk receiving events: `index=fw | stats count` shows > 0
- [ ] Events have correct sourcetype: `fgt_log`

### Alerts
- [ ] All 3 alerts exist in Settings → Searches, reports, and alerts
- [ ] All 3 alerts have `disabled=0` (enabled)
- [ ] All 3 alerts have Real-time schedule
- [ ] Slack channel configured: `#security-firewall-alert`

### Dashboard
- [ ] Dashboard loads without errors
- [ ] Alert ON/OFF buttons work
- [ ] Alert status shows ✅/🔴 correctly
- [ ] Recent events display in tables

### Slack
- [ ] Bot invited to #security-firewall-alert
- [ ] Test alert received in Slack
- [ ] Message format correct (device, admin, path, etc.)

---

## 📁 Directory Structure

```
configs/
├── savedsearches-fortigate-alerts.conf  ⭐ Alert config (REQUIRED)
├── inputs-udp.conf                              ⭐ UDP input (REQUIRED)
├── Deploy-SplunkDashboards.ps1                  ⚪ Optional script
├── dashboards/
│   ├── fortigate-monitoring.xml                 ⭐ Main dashboard (REQUIRED)
│   ├── fmg-all-changes-v2.xml                   ⚪ Optional
│   └── fmg-operational-events.xml               ⚪ Optional
├── docs/                                        ℹ️ Documentation
└── archive-2025-10-28/                          🗄️ Legacy files (DO NOT USE)
```

**Key**:
- ⭐ REQUIRED: Essential for production
- ⚪ Optional: Additional features
- ℹ️ Documentation: Reference guides
- 🗄️ Archive: Old versions (keep for reference)

---

## 🚫 Deprecated Files (DO NOT USE)

### Old Conf Files
- ❌ `savedsearches-fortigate-alerts.conf` - Korean field names (SPL errors)
- ❌ `savedsearches-fortigate-alerts-blockkit-fixed.conf` - Block Kit not working
- ❌ `savedsearches-fortigate-alerts-logid-blockkit.conf` - Too complex
- ❌ `savedsearches-simple.conf` - Incomplete

### Old Dashboard Files
- ❌ `fortigate-alert-control-debug.xml` - Debug version
- ❌ `dashboards/fortigate-alert-control.xml` - Redundant (use main dashboard)
- ❌ `dashboards/fortigate-alert-test.xml` - Test version

### Archive
- ❌ `archive-2025-10-28/*` - 39 legacy files (keep for reference only)

---

## 📊 File Summary Table

| File | Size | Purpose | Deploy Method | Required |
|------|------|---------|---------------|----------|
| `savedsearches-fortigate-alerts.conf` | 3.9 KB | Alert definitions | Web UI (manual) | ✅ YES |
| `dashboards/fortigate-monitoring.xml` | 21 KB | Main dashboard | Web UI (copy XML) | ✅ YES |
| `inputs-udp.conf` | 6.7 KB | Syslog input | Web UI (settings) | ✅ YES |
| `dashboards/fmg-all-changes-v2.xml` | 8.0 KB | Config details | Web UI (optional) | ⚪ No |
| `dashboards/fmg-operational-events.xml` | 9.5 KB | Event details | Web UI (optional) | ⚪ No |
| `Deploy-SplunkDashboards.ps1` | - | Automation | PowerShell | ⚪ No |

**Total REQUIRED**: 3 files only!

---

## ❓ FAQ

### Q: Why can't I upload conf files via Web UI?
**A**: Splunk Web UI doesn't support direct conf upload. You must either:
- Copy conf to `/opt/splunk/etc/apps/search/local/` (requires shell access)
- Create alerts manually via Web UI (copy SPL from conf file) ⭐ RECOMMENDED
- Use REST API script (PowerShell)

### Q: Why English field names instead of Korean?
**A**: SPL parser cannot handle non-ASCII characters in `eval` statements. Using English in eval + rename to Korean for display works perfectly.

### Q: Can I skip the deduplication?
**A**: Not recommended. Without 3-layer deduplication (rt-30s window + dedup command + 15s suppress), you'll get alert spam under heavy log volume.

### Q: Why plain text instead of Block Kit?
**A**: Block Kit formatting has compatibility issues across Slack app versions. Plain text works reliably everywhere.

### Q: Do I need to restart Splunk after creating alerts?
**A**: No. Alerts created via Web UI are immediately active.

---

## 📚 Additional Documentation

Located in `docs/` folder:

**Deployment Guides**:
- `DEPLOYMENT-FINAL.md` - Complete deployment guide
- `UDP-WEBUI-SETUP-GUIDE.md` - UDP setup via Web UI
- `QUICK-FIX-GUIDE.md` - Troubleshooting guide

**Alert Reference**:
- `ALERT-PRODUCTION-SIMPLE.md` - Alert details with verification
- `ALERT-SIMPLE-VERSION.txt` - Alert quick reference
- `ALERT-CHANGES-SUMMARY.md` - Change history

**Dashboard Reference**:
- `DASHBOARD-CONTENTS-CHECK.md` - Dashboard panel details
- `TEST-CONFIG-CHANGE-DATA.md` - Test data guide

---

**Done!** With these 3 files, you can deploy production-ready FortiGate Slack alerts.

**Total deployment time**: ~10 minutes
**Maintenance**: Zero (alerts auto-run, no manual intervention)
