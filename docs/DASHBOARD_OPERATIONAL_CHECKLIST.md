# Dashboard Operational Checklist

**Date**: 2025-10-25
**Purpose**: Pre-deployment validation and post-deployment verification
**Estimated Time**: 15-20 minutes

---

## ✅ Phase 1: Pre-Deployment Validation (10 minutes)

### 1.1 Environment Check

```bash
# Run compatibility validator
./scripts/validate-dashboard-compatibility.sh

# Expected output:
# ✅ Splunk Version: 9.x.x supports Dashboard Studio
# ✅ JSON Validation: 3/3 passed
# ✅ Feature Compatibility: All features compatible
```

**Checklist**:
- [ ] Splunk version 9.0+ installed
- [ ] All 3 JSON files valid syntax
- [ ] No version-specific feature conflicts

---

### 1.2 Data Availability Check

```bash
# Check index=fortianalyzer data exists
splunk search "index=fortianalyzer earliest=-1h | head 1"

# Check event count (should be > 0)
splunk search "index=fortianalyzer earliest=-24h | stats count"

# Verify required fields
splunk search "index=fortianalyzer earliest=-1h | stats count by severity, src_ip, dst_ip, action"
```

**Checklist**:
- [ ] `index=fortianalyzer` contains data (last 1 hour)
- [ ] Events have required fields: `severity`, `src_ip`, `dst_ip`, `action`
- [ ] Event count > 100 (sufficient for testing)

---

### 1.3 Slack Plugin Check

```bash
# Run Slack plugin validator
./scripts/check-slack-plugin.sh

# Expected output:
# ✅ Slack Add-on: Installed
# ✅ Configuration: Found
# ✅ Bot token configured
```

**Checklist**:
- [ ] Slack Add-on installed (any of: `slack_alerts`, `TA-slack`, `slack-notification-alert`)
- [ ] `alert_actions.conf` configured with webhook URL or bot token
- [ ] Default channel configured (e.g., `#splunk-alerts`)

---

### 1.4 SPL Query Validation

```bash
# Test sample queries from dashboards
# Query 1: Event timeline
splunk search 'index=fortianalyzer earliest=-24h | timechart span=1h count by severity'

# Query 2: Top sources
splunk search 'index=fortianalyzer earliest=-1h | stats count by src_ip | sort -count | head 10'

# Query 3: Blocked traffic
splunk search 'index=fortianalyzer earliest=-1h action=blocked | timechart span=5m count'

# Query 4: REST API (Slack alert status)
splunk search '| rest /servicesNS/nobody/search/saved/searches | search title="*Slack*" | table title, disabled'
```

**Checklist**:
- [ ] All 4 queries return results without errors
- [ ] Query execution time < 10 seconds each
- [ ] REST API query returns alert status

---

## 🚀 Phase 2: Deployment (5 minutes)

### 2.1 Dashboard Deployment

**Method 1: Splunk Web UI (Recommended)**

1. Navigate to: **Dashboards → Create New Dashboard → Dashboard Studio**
2. Click **"Source"** button (top right)
3. Copy JSON content from:
   - `configs/dashboards/studio-production/01-fortigate-operations.json`
4. Paste into Source editor
5. Click **"Save"**
6. Repeat for remaining 2 dashboards

**Method 2: PowerShell (Windows)**

```powershell
# Deploy all dashboards
.\scripts\Deploy-SplunkDashboards.ps1 -DashboardPath "configs\dashboards\studio-production"

# Or deploy single dashboard
.\scripts\Deploy-SplunkDashboards.ps1 -DashboardPath "01-fortigate-operations.json"
```

**Method 3: REST API (Linux/Mac)**

```bash
# Deploy using curl
for dashboard in configs/dashboards/studio-production/*.json; do
  dashboard_name=$(basename "$dashboard" .json)

  curl -k -u admin:password \
    -H "Content-Type: application/json" \
    -d @"$dashboard" \
    "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views"

  sleep 2
done
```

**Checklist**:
- [ ] Dashboard 1: `fortigate_operations` deployed
- [ ] Dashboard 2: `faz_fmg_monitoring` deployed
- [ ] Dashboard 3: `slack_alert_control` deployed
- [ ] No HTTP 4xx/5xx errors during deployment

---

### 2.2 Verify Deployment

```bash
# PowerShell
.\scripts\Deploy-SplunkDashboards.ps1 -Verify

# Bash
curl -k -u admin:password \
  "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views?output_mode=json" \
  | jq '.entry[] | select(.name | contains("fortigate") or contains("faz") or contains("slack")) | .name'
```

**Expected output**:
```
fortigate_operations
faz_fmg_monitoring
slack_alert_control
```

**Checklist**:
- [ ] All 3 dashboards visible in Splunk Web UI
- [ ] Dashboards appear in: **Dashboards** menu
- [ ] No "Dashboard not found" errors

---

## 🔍 Phase 3: Functional Testing (5-10 minutes)

### 3.1 Dashboard Loading Test

**Dashboard 1: FortiGate Operations**

1. Open: `http://splunk.jclee.me:8000/app/search/fortigate_operations`
2. Wait for all panels to load
3. **Check**:
   - [ ] Event timeline chart displays
   - [ ] Severity pie chart displays
   - [ ] Top sources table populated
   - [ ] Blocked traffic single value shows number
   - [ ] Critical events single value shows number
   - [ ] Recent events table shows data
   - [ ] Loading time < 5 seconds

**Dashboard 2: FAZ/FMG Monitoring**

1. Open: `http://splunk.jclee.me:8000/app/search/faz_fmg_monitoring`
2. **Check**:
   - [ ] Total events single value displays
   - [ ] Critical count single value displays (red background)
   - [ ] High severity single value displays (orange background)
   - [ ] Event timeline area chart displays
   - [ ] Top attackers table shows threat scores
   - [ ] Attack types bar chart displays
   - [ ] Geographic choropleth map displays (if geo data available)
   - [ ] Policy changes table shows FMG events

**Dashboard 3: Slack Alert Control**

1. Open: `http://splunk.jclee.me:8000/app/search/slack_alert_control`
2. **Check**:
   - [ ] Alert status table shows 5 alerts
   - [ ] "Alert Enabled" column shows 1 (green) or 0 (red)
   - [ ] "Slack Enabled" column shows 1 (green) or 0 (red)
   - [ ] Recent alerts table shows last 20 triggers
   - [ ] Alert frequency bar chart displays
   - [ ] Slack delivery single value shows count
   - [ ] Alert errors single value shows count (should be 0)
   - [ ] REST API guide markdown panel displays

---

### 3.2 Auto-Refresh Test

1. Open any dashboard
2. Wait 30 seconds (auto-refresh interval)
3. **Check**:
   - [ ] Dashboard refreshes automatically
   - [ ] New data appears (check timestamp in tables)
   - [ ] No "Search failed" errors

---

### 3.3 Time Range Selector Test

1. Click **Time Range** dropdown (top of dashboard)
2. Select **Last 4 hours**
3. **Check**:
   - [ ] All panels update to 4-hour data
   - [ ] Query completes without timeout
   - [ ] Event counts increase

4. Select **Last 15 minutes**
5. **Check**:
   - [ ] All panels update to 15-minute data
   - [ ] Loading faster than 4-hour range

---

### 3.4 Slack Alert Test

**Test 1: Manual Slack Notification**

```bash
# Send test message via Slack webhook
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H "Content-Type: application/json" \
  -d '{"text":"✅ Splunk Dashboard Test - All systems operational"}'
```

**Checklist**:
- [ ] Test message received in Slack channel
- [ ] Message format correct
- [ ] No authentication errors

**Test 2: Alert Trigger Test**

```bash
# Create test alert that triggers immediately
# Splunk Web UI: Settings → Searches, reports, and alerts → New Alert

# Search: index=fortianalyzer earliest=-1h | head 1
# Trigger: Number of Results > 0
# Action: Send to Slack
# Channel: #splunk-test
# Message: Test alert from Splunk Dashboard
```

**Checklist**:
- [ ] Alert fires successfully
- [ ] Slack notification received
- [ ] Alert visible in "Recent Alert Triggers" table on Dashboard 3

---

### 3.5 Browser Compatibility Test

**Test without JavaScript**:

1. Open Chrome DevTools (F12)
2. Settings → Debugger → Disable JavaScript
3. Refresh dashboard
4. **Check**:
   - [ ] All panels still display (no JavaScript required!)
   - [ ] Data loads from SPL queries
   - [ ] No "Enable JavaScript" errors

**Mobile Test**:

1. Open dashboard on mobile browser (Chrome/Safari)
2. **Check**:
   - [ ] Dashboard displays in mobile viewport
   - [ ] Panels stack vertically
   - [ ] Text readable without zooming
   - [ ] Touch scrolling works

---

## 🚨 Phase 4: Error Testing

### 4.1 Simulate No Data

```bash
# Query non-existent index
splunk search "index=nonexistent earliest=-1h"

# Expected: No results found (not an error)
```

**Checklist**:
- [ ] Dashboard handles "No results" gracefully
- [ ] No red error messages
- [ ] Empty panels show "No data" message

---

### 4.2 Simulate Query Timeout

```bash
# Run expensive query
splunk search 'index=fortianalyzer earliest=-7d | stats count by src_ip, dst_ip, severity, msg'

# If query takes > 30s, it will timeout
```

**Checklist**:
- [ ] Dashboard shows "Search is taking longer than expected" message
- [ ] User can cancel search
- [ ] Dashboard doesn't crash

---

### 4.3 Simulate Network Issue

1. Disconnect network temporarily
2. Wait for auto-refresh (30s)
3. **Check**:
   - [ ] Dashboard shows "Connection error" or similar
   - [ ] Dashboard doesn't hang
   - [ ] Reconnecting restores functionality

---

## 📊 Phase 5: Performance Monitoring (24 hours)

### 5.1 Dashboard Query Performance

```spl
# Monitor dashboard search performance (run daily)
index=_internal source=*metrics.log component=Dispatch earliest=-24h
  dashboard IN ("fortigate_operations", "faz_fmg_monitoring", "slack_alert_control")
| stats avg(elapsed_ms) as avg_time_ms,
        max(elapsed_ms) as max_time_ms,
        p95(elapsed_ms) as p95_time_ms,
        count as queries
  by dashboard
| eval avg_time_sec=round(avg_time_ms/1000, 2),
       max_time_sec=round(max_time_ms/1000, 2),
       p95_time_sec=round(p95_time_ms/1000, 2)
| table dashboard, queries, avg_time_sec, p95_time_sec, max_time_sec
| sort dashboard

# Target: avg < 5s, p95 < 15s, max < 60s
```

**Performance Targets**:
- **Average query time**: < 5 seconds
- **P95 query time**: < 15 seconds
- **Max query time**: < 60 seconds
- **Error rate**: < 1%

---

### 5.2 Dashboard Usage Tracking

```spl
# Track dashboard views and users (run weekly)
index=_audit action=view object_type=dashboard earliest=-7d
  object IN ("fortigate_operations", "faz_fmg_monitoring", "slack_alert_control")
| stats count as views, dc(user) as unique_users by object
| rename object as dashboard
| sort -views

# Expected: > 50 views/week for active dashboards
```

---

### 5.3 Error Monitoring

```spl
# Monitor dashboard errors (run daily)
index=_internal source=*splunkd.log earliest=-24h
  (ERROR OR WARN)
  (dashboard="fortigate_operations" OR dashboard="faz_fmg_monitoring" OR dashboard="slack_alert_control")
| stats count by log_level, message
| sort -count

# Target: 0 errors
```

---

## 🔄 Phase 6: Rollback Test (Optional)

### 6.1 Prepare Rollback

```bash
# Hide Studio dashboards (don't delete)
curl -k -u admin:password -X POST \
  -d "perms.read=admin" \
  "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/fortigate_operations/acl"

# Unhide Legacy XML dashboards
curl -k -u admin:password -X POST \
  -d "perms.read=*" \
  "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/fortigate_operations_legacy/acl"
```

**Checklist**:
- [ ] Studio dashboards hidden from users
- [ ] Legacy dashboards visible again
- [ ] Rollback completed in < 5 minutes

---

### 6.2 Re-deploy Studio Dashboards

```bash
# Re-enable Studio dashboards
curl -k -u admin:password -X POST \
  -d "perms.read=*" \
  "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/fortigate_operations/acl"
```

**Checklist**:
- [ ] Studio dashboards visible again
- [ ] No data loss during rollback test

---

## 📋 Final Approval Checklist

**Before Production Deployment**:

- [ ] All Phase 1 validations passed (Pre-deployment)
- [ ] All Phase 2 deployments successful (Deployment)
- [ ] All Phase 3 functional tests passed (Functional)
- [ ] All Phase 4 error scenarios handled (Error handling)
- [ ] Phase 5 monitoring configured (Performance)
- [ ] Phase 6 rollback tested (Rollback)

**Sign-Off**:

- [ ] **Deployed by**: _________________ Date: _________
- [ ] **Tested by**: _________________ Date: _________
- [ ] **Approved by**: _________________ Date: _________

---

## 🆘 Troubleshooting Guide

### Issue 1: Dashboard doesn't load

**Symptoms**: Blank page, "Dashboard not found"

**Solutions**:
```bash
# Check dashboard exists
curl -k -u admin:password \
  "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/fortigate_operations?output_mode=json"

# Check permissions
curl -k -u admin:password \
  "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/fortigate_operations/acl"

# Re-deploy if needed
curl -k -u admin:password \
  -H "Content-Type: application/json" \
  -d @configs/dashboards/studio-production/01-fortigate-operations.json \
  "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views"
```

---

### Issue 2: Panels show "No results"

**Symptoms**: Empty panels, "No data to display"

**Solutions**:
```bash
# Verify index data
splunk search "index=fortianalyzer earliest=-1h | stats count"

# Check time range (might be too narrow)
# Dashboard → Time Range → Select "Last 24 hours"

# Check field names match
splunk search "index=fortianalyzer earliest=-1h | head 1 | table *"
```

---

### Issue 3: Slack notifications not received

**Symptoms**: Alerts fire but no Slack messages

**Solutions**:
```bash
# Check Slack plugin
./scripts/check-slack-plugin.sh

# Test webhook manually
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H "Content-Type: application/json" \
  -d '{"text":"Test"}'

# Check Splunk logs
index=_internal source=*slack* earliest=-1h ERROR

# Verify bot invited to channel
# Slack: /invite @your-bot-name
```

---

### Issue 4: Dashboard queries timeout

**Symptoms**: "Search is taking too long", spinning loaders

**Solutions**:
```spl
# Reduce time range
# Dashboard → Time Range → Last 1 hour (instead of 24h)

# Check data model acceleration
| rest /services/admin/summarization by_tstats=true
| search summary.id=*Fortinet_Security*
| table summary.id, summary.complete

# Optimize slow queries (use tstats instead of stats)
# Before: index=fortianalyzer | stats count by src_ip
# After: | tstats count WHERE datamodel=Fortinet_Security.Security_Events BY src_ip
```

---

**End of Checklist**

**Status**: Ready for deployment ✅
**Estimated Total Time**: 15-20 minutes validation + 5 minutes deployment
**Success Rate Target**: 100% (all checks passed)
