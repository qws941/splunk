# FortiAnalyzer → Splunk HEC Deployment Guide (Direct HEC)

**Complete step-by-step deployment guide for FortiAnalyzer to Splunk integration via HTTP Event Collector (HEC)**

**Status**: Alternative Method (2025-10-29)
**Prerequisites**: FortiAnalyzer 7.4.0+, Splunk Enterprise/Cloud with admin access
**Estimated Time**: 30-45 minutes for initial setup

---

## 🆕 Recommended Approach: Fluentd-HEC (2025-10-29)

**⚠️ This guide covers Direct HEC (FortiAnalyzer → Splunk HEC). For production deployments, consider Fluentd-HEC for added flexibility.**

**Fluentd-HEC Benefits**:
- ✅ Log transformation and enrichment (GeoIP, custom fields)
- ✅ Multiple destinations (Splunk + S3 + Kafka)
- ✅ Buffer management and retry logic
- ✅ Vendor-agnostic (not tied to FortiAnalyzer version)

**Quick Fluentd-HEC Deployment**:
```bash
./scripts/deploy-fluentd-hec.sh
```

**Detailed Guide**: `docs/FLUENTD_QUICK_START.md`

---

## 📋 Overview (Direct HEC Method)

This guide walks you through deploying real-time log forwarding from FortiAnalyzer directly to Splunk using HTTP Event Collector (HEC) - **without Fluentd middleware**.

**Data Flow**:
```
FortiGate Devices → FortiAnalyzer → Splunk HEC (Port 8088) → index=fortianalyzer → Dashboards
```

**Use this method if**:
- ✅ You need <1 second latency (Fluentd adds 5-10s)
- ✅ You don't need log transformation or enrichment
- ✅ Splunk is your only destination
- ✅ You have FortiAnalyzer 7.4.0+ with native HEC client

**Use Fluentd-HEC instead if**:
- ✅ You need GeoIP, custom fields, or log filtering
- ✅ You want to send logs to multiple destinations
- ✅ You prefer vendor-agnostic log pipeline
- ✅ You need advanced buffer management

**What You'll Accomplish**:
- ✅ Create and configure Splunk HEC token
- ✅ Configure FortiAnalyzer log forwarding
- ✅ Verify data flow end-to-end
- ✅ Deploy operational monitoring dashboards
- ✅ Configure operational alerts

---

## Phase 1: Splunk HEC Token Creation (5-10 minutes)

### Step 1.1: Enable HEC Globally

1. **Login to Splunk Web**: Navigate to `https://your-splunk-host:8000`
2. **Go to Settings**: Click `Settings` (top-right) → `Data Inputs`
3. **Open HEC Settings**: Click `HTTP Event Collector`
4. **Click Global Settings** (top-right green button)
5. **Enable HEC**:
   - ☑️ Check `All Tokens` → Enabled
   - **HTTP Port Number**: `8088` (default)
   - **Enable SSL**: ☑️ Checked (recommended)
   - ☐ **Enable indexer acknowledgment**: Unchecked (adds latency)
6. **Save** → You'll see "HTTP Event Collector settings have been updated"

### Step 1.2: Create Dedicated Index (REQUIRED)

**⚠️ IMPORTANT**: HEC uses separate `fortianalyzer` index (not legacy `fw` for Syslog)

1. **Navigate**: Settings → Indexes → New Index
2. **Index Settings**:
   - **Index Name**: `fortianalyzer`
   - **Index Data Type**: Events
   - **Max Size of Entire Index**: 500GB (adjust based on log volume)
   - **Retention**: 90 days (adjust based on compliance requirements)
3. **Click Save**

### Step 1.3: Create New HEC Token

1. **Return to HEC page**: Settings → Data Inputs → HTTP Event Collector
2. **Click "New Token"** (top-right green button)
3. **Name and Description** (Step 1 of 4):
   - **Name**: `fortianalyzer-prod`
   - **Description**: `FortiAnalyzer real-time log forwarding`
   - **Source name override**: `fortianalyzer-prod`
   - Click **Next**

4. **Input Settings** (Step 2 of 4):
   - **Source type**: Select `Automatic` (or create custom `fortianalyzer:traffic`)
   - **App Context**: `search` (default)
   - Click **Next**

5. **Index** (Step 3 of 4):
   - **Available indexes**: Select `fortianalyzer` (created in Step 1.2)
   - ⚠️ **Do NOT use `fw`** (reserved for legacy Syslog during migration)
   - Click **Review**

6. **Review and Submit** (Step 4 of 4):
   - Verify all settings
   - Click **Submit**

7. **Copy Token Value**:
   - ⚠️ **IMPORTANT**: Copy the token value immediately
   - Format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (UUID with hyphens)
   - Save to password manager or `.env` file
   - You can view it later at: Settings → Data Inputs → HTTP Event Collector → Token name → Token Value

### Step 1.4: Verify HEC Endpoint

Test HEC endpoint from your workstation:

```bash
# Test HEC health endpoint (should return {"text":"HEC is healthy","code":17})
curl -k https://your-splunk-host:8088/services/collector/health

# Test token authentication (should return success)
curl -k https://your-splunk-host:8088/services/collector/event \
  -H "Authorization: Splunk YOUR_HEC_TOKEN" \
  -d '{"event":"test from FortiAnalyzer setup","sourcetype":"test"}'
```

**Expected response**: `{"text":"Success","code":0}`

---

## Phase 2: FortiAnalyzer Configuration (10-15 minutes)

### Step 2.1: Access FortiAnalyzer CLI

**Option A: SSH**:
```bash
ssh admin@your-fortianalyzer-host
# Enter password when prompted
```

**Option B: Web UI Console**:
1. Login to FortiAnalyzer Web UI
2. Click **System Settings** (gear icon)
3. Click **Console** (bottom-left)

### Step 2.2: Apply HEC Client Profile

Copy/paste the configuration from `configs/faz-to-splunk-hec.conf` with your values:

```bash
config system log-fetch client-profile
    edit "splunk-hec-primary"
        set server-type splunk
        set server-ip "YOUR_SPLUNK_HOST"              # Replace with Splunk hostname/IP
        set server-port 8088
        set secure-connection enable
        set client-key "YOUR_HEC_TOKEN"               # Replace with token from Step 1.2
        set data-format splunk-hec
        set log-type traffic utm event
        set upload-interval realtime
        set upload-option store-and-upload
        set compress gzip
        set max-log-rate 10000
        set sourcetype "fortianalyzer:traffic"
        set source "fortianalyzer-prod"
        set index "fortianalyzer"                     # Dedicated index (not legacy fw)
        set host-field devname
        set status enable
    next
end
```

**⚠️ Replace**:
- `YOUR_SPLUNK_HOST`: Splunk server IP or hostname (e.g., `splunk.example.com` or `192.168.1.100`)
- `YOUR_HEC_TOKEN`: Token value from Step 1.2 (UUID format with hyphens)

### Step 2.3: Configure Global Log Fetch Settings

```bash
config system log-fetch server-settings
    set status enable
    set max-conn-timeout 300
    set unencrypted-logging disable
    set upload-max-conn 5
    set max-logs-per-batch 5000
    set upload-retry-max 3
    set buffer-max-send 10000000
    set buffer-max-disk 100000000
end
```

### Step 2.4: Verify Configuration

```bash
# View your configuration
show system log-fetch client-profile splunk-hec-primary

# Expected output should show:
# - server-ip: YOUR_SPLUNK_HOST
# - client-key: YOUR_HEC_TOKEN
# - status: enable
```

---

## Phase 3: Verification & Testing (10-15 minutes)

### Step 3.1: FortiAnalyzer Health Check

Run these commands on FortiAnalyzer CLI:

```bash
# 1. Check log fetch service status
diagnose test application fazd 1
# Expected: Shows running status and active connections

# 2. View HEC profile status
diagnose log-fetch client-profile status splunk-hec-primary
# Expected: State: Connected, Upload: Running

# 3. Monitor upload queue (should drain to near 0)
diagnose log-fetch queue status
# Expected: Queue size: 0-100 (realtime), rapidly decreasing

# 4. View recent upload logs
diagnose log-fetch upload-log list | tail -20
# Expected: Shows successful uploads with status: success
```

**Troubleshooting**:

| Status | Meaning | Action |
|--------|---------|--------|
| `State: Disconnected` | Cannot reach Splunk HEC | Check network, firewall rules, port 8088 |
| `State: Connected, Upload: Failed` | Authentication error | Verify HEC token is correct and enabled |
| `Queue size > 1000` (persistent) | Upload lag | Increase `max-logs-per-batch`, check Splunk performance |

### Step 3.2: Splunk Data Verification

Run these searches in Splunk Web (Search & Reporting app):

**1. Check data arrival** (should return results within 1-2 minutes):
```spl
index=fortianalyzer sourcetype=fortianalyzer:*
| head 10
| table _time, host, sourcetype, _raw
```

**2. Verify data sources**:
```spl
index=fortianalyzer earliest=-5m
| stats count by host, sourcetype, source
| sort -count
```

**Expected results**:
- `host`: FortiGate device names (e.g., `FGT-HQ-FW01`)
- `sourcetype`: `fortianalyzer:traffic`
- `source`: `fortianalyzer-prod`
- `index`: `fortianalyzer` (NOT `fw`)
- `count`: Growing number (100s-1000s per minute)

**3. Verify index separation** (if legacy Syslog still active):
```spl
| metadata type=sources
| search index=fortianalyzer OR index=fw
| stats count by index, source, sourcetype

# Expected:
# index=fortianalyzer, source=fortianalyzer-prod, sourcetype=fortianalyzer:traffic
# index=fortianalyzer, source=udp:9514, sourcetype=fw_log (if Syslog still active)
```

**3. Check HEC health**:
```spl
index=_internal source=*http_event_collector* earliest=-15m
| stats count by status, channel
```

**Expected**: `status=200` (success), no 401/403 errors

### Step 3.3: FortiGate Device Visibility

Verify logs from all FortiGate devices:

```spl
index=fortianalyzer earliest=-15m
| stats count by devname, type, subtype
| sort -count
```

**Expected**: See all FortiGate devices sending logs:
- `devname`: FGT-HQ-FW01, FGT-Branch-01, etc.
- `type`: traffic, utm, event
- `count`: Distributed across devices

**During Migration** (if legacy Syslog still active):
```spl
# Compare both data sources
(index=fortianalyzer OR index=fortianalyzer) earliest=-15m
| stats count by index, devname
| sort index, -count

# Verify no duplicate devices between indexes
```

---

## Phase 4: Dashboard Deployment (5-10 minutes)

### Step 4.1: Import Production Dashboards

**Option A: Splunk Web UI (Recommended)**

1. **Navigate**: Splunk Web → Dashboards → Create New Dashboard → Dashboard Studio
2. **Click "Source"** (top-right, `</>` icon)
3. **Paste JSON**:
   - Open `configs/dashboards/studio-production/01-fortigate-operations.json`
   - Copy entire JSON content
   - Paste into Source editor
4. **Save**: Give it a name (e.g., `FortiGate Operations`)
5. **Repeat** for remaining dashboards:
   - `02-fmg-operations.json`
   - `03-slack-alert-control.json`
   - `fortigate-fmg-monitoring.json`

**Option B: REST API (Automated)**

```bash
# Validate JSON first
jq empty configs/dashboards/studio-production/*.json

# Note: Automated deployment requires enterprise environment approval
# See: docs/ENTERPRISE_DASHBOARD_DEPLOYMENT.md for full process
```

### Step 4.2: Verify Dashboard Data

Open `FortiGate Operations` dashboard:

**Expected panels**:
- ☑️ **Device Status**: Shows all FortiGate devices with CPU/Memory/Session stats
- ☑️ **Configuration Changes**: Recent admin actions
- ☑️ **Critical Events**: Hardware failures, HA failover events
- ☑️ **Network Interfaces**: Interface status changes

**If panels show "No results"**:
1. Check time range (default: Last 24 hours)
2. Verify data is flowing: `index=fortianalyzer | stats count`
3. Check LogID filters match your FortiGate firmware version

---

## Phase 5: Operational Alerts (5-10 minutes)

### Step 5.1: Deploy Alert Configurations

Copy alert definitions to Splunk:

```bash
# Option A: Splunk Web UI
# Settings → Searches, reports, and alerts → New Alert

# Option B: Deploy saved searches
# Copy configs/savedsearches-fortigate-alerts.conf to:
# /opt/splunk/etc/apps/search/local/savedsearches.conf
```

**Key operational alerts** (see `configs/savedsearches-fortigate-alerts.conf`):

1. **FortiGate Config Change Alert**
   - Trigger: Admin modifies FortiGate configuration
   - Severity: Informational
   - Channel: `#splunk-config-changes`

2. **FortiGate Critical Event Alert**
   - Trigger: Hardware failure, HA failover, high CPU/memory
   - Severity: Critical
   - Channel: `#splunk-critical`

3. **FortiGate Device Offline Alert**
   - Trigger: No logs received from device for 10+ minutes
   - Severity: Warning
   - Channel: `#splunk-device-status`

### Step 5.2: Configure Slack Integration (Optional)

If using Slack notifications:

1. **Install Splunk Slack Alert Plugin**:
   - Apps → Find More Apps → Search "Slack"
   - Install "Splunk Add-on for Slack"

2. **Configure Slack Bot Token**:
   - Edit `.env` (project root)
   - Add: `SLACK_BOT_TOKEN=xoxb-your-token`
   - Add: `SLACK_CHANNEL=#splunk-alerts`

3. **Test Slack Alert**:
   ```bash
   node scripts/slack-alert-cli.js --test
   ```

**Expected**: Message appears in Slack channel

---

## Phase 6: Post-Deployment Checklist

### ✅ Verification Checklist

Run this checklist 24 hours after deployment:

**FortiAnalyzer**:
- [ ] Upload queue size < 100 (`diagnose log-fetch queue status`)
- [ ] Upload success rate > 99% (`diagnose log-fetch upload-log list`)
- [ ] No connection errors in last 24h
- [ ] All FortiGate devices sending logs

**Splunk**:
- [ ] Data ingestion rate stable (1000-10000 events/min)
- [ ] HEC errors = 0 (`index=_internal source=*http_event_collector* status!=200`)
- [ ] All dashboards showing data
- [ ] Alerts not triggering false positives

**Operational Dashboards**:
- [ ] Device status panel shows all devices
- [ ] Configuration changes tracking properly
- [ ] Critical events correlating correctly
- [ ] Time ranges functioning (Last 24h, Last 7d)

### 📊 Performance Metrics

Monitor these metrics for the first week:

```spl
# 1. Daily event volume
index=fortianalyzer earliest=-7d
| timechart span=1d count by sourcetype

# 2. Per-device event rate
index=fortianalyzer earliest=-24h
| stats count by devname
| sort -count

# 3. HEC performance
index=_internal source=*http_event_collector* earliest=-24h
| timechart span=1h avg(data.ack_id) as avg_latency_ms
```

**Expected results**:
- Event volume: Consistent daily pattern
- Per-device rate: Distributed evenly across devices
- HEC latency: < 100ms average

---

## 🔧 Troubleshooting

### Common Issues

#### Issue 1: "Connection Timeout" in FortiAnalyzer

**Symptoms**:
- `diagnose log-fetch client-profile status` shows `State: Disconnected`
- Upload logs show `connection timeout`

**Solution**:
```bash
# 1. Test network connectivity from FortiAnalyzer
execute ping YOUR_SPLUNK_HOST

# 2. Test port 8088 accessibility
execute telnet YOUR_SPLUNK_HOST 8088

# 3. Check firewall rules allow FortiAnalyzer IP → Splunk:8088
```

**Common causes**:
- Firewall blocking port 8088
- Splunk HEC not listening on all interfaces
- DNS resolution failure

#### Issue 2: "Authentication Failed (401)" in Splunk Logs

**Symptoms**:
- Logs show `index=_internal source=*http_event_collector* status=401`
- FortiAnalyzer shows `authentication failed`

**Solution**:
1. **Verify token in Splunk**: Settings → Data Inputs → HTTP Event Collector → Token name → Token Value
2. **Check token is enabled**: Toggle should be green (enabled)
3. **Verify token format**: Must be UUID with hyphens (not base64)
4. **Re-apply token in FortiAnalyzer**:
   ```bash
   config system log-fetch client-profile
       edit "splunk-hec-primary"
           set client-key "CORRECT_TOKEN_HERE"
       next
   end
   ```

#### Issue 3: "Logs Not Appearing in Splunk"

**Symptoms**:
- `index=fortianalyzer` search returns 0 results
- FortiAnalyzer shows successful uploads

**Solution**:
```spl
# 1. Check if index exists
| metadata type=sources index=fw

# 2. Check HEC endpoint received data
index=_internal source=*http_event_collector* earliest=-15m
| stats sum(data.bytes) as total_bytes by host

# 3. Check for parsing errors
index=_internal source=*splunkd.log* "ERROR" earliest=-15m
| search "fortianalyzer"

# 4. Verify clock sync (NTP)
# Time difference > 5 minutes will cause indexing issues
```

#### Issue 4: "High Upload Lag / Queue Building Up"

**Symptoms**:
- `diagnose log-fetch queue status` shows queue size > 5000 (persistent)
- Logs delayed by 10+ minutes

**Solution**:
```bash
# 1. Increase batch size and connections
config system log-fetch server-settings
    set upload-max-conn 10
    set max-logs-per-batch 10000
end

config system log-fetch client-profile
    edit "splunk-hec-primary"
        set max-log-rate 50000
    next
end

# 2. Enable compression (if not already)
config system log-fetch client-profile
    edit "splunk-hec-primary"
        set compress gzip
    next
end

# 3. Check Splunk indexer performance
# index=_internal source=*metrics.log* group=queue earliest=-15m
# | stats avg(current_size) by name
```

**Performance tuning**: See `configs/faz-to-splunk-hec.conf` Section "Performance Tuning"

---

## 📚 Next Steps

### Operational Monitoring

1. **Review Test Queries**: `test-queries/README.md`
   - 13 operational monitoring queries
   - Admin activity, interface status, VPN monitoring, hardware health

2. **Set Up Daily Reports**:
   - Config change summary (daily email)
   - Device health report (weekly)
   - Hardware alert summary (weekly)

3. **Tune Alert Thresholds**:
   - CPU usage threshold (default: 80%)
   - Memory usage threshold (default: 80%)
   - Session table usage threshold (default: 90%)

### Advanced Configuration

1. **High Availability**: Configure secondary HEC endpoint
   - See `configs/faz-to-splunk-hec.conf` Section "Optional: High Availability"

2. **Log Filtering**: Reduce data volume by filtering log types
   - Exclude debug logs: `set log-type traffic utm event` (no verbose)
   - Filter by LogID: Use FortiAnalyzer log filters

3. **Retention Policy**: Configure Splunk index retention
   - Settings → Indexes → fw → Edit
   - Set retention: 90 days (adjust based on compliance requirements)

---

## 📖 References

**Configuration Files**:
- `configs/faz-to-splunk-hec.conf` - Complete FortiAnalyzer configuration
- `configs/savedsearches-fortigate-alerts.conf` - Operational alert definitions
- `configs/dashboards/studio-production/*.json` - Production dashboards

**Operational Guides**:
- `test-queries/README.md` - 13 operational monitoring queries with LogID reference
- `docs/DASHBOARD_OPERATIONAL_CHECKLIST.md` - 6-phase dashboard testing guide
- `docs/SLACK_BLOCKKIT_DEPLOYMENT.md` - Interactive Slack alerts with buttons

**Official Documentation**:
- [FortiAnalyzer Administration Guide](https://docs.fortinet.com/document/fortianalyzer/latest/administration-guide)
- [Splunk HEC Documentation](https://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector)
- [Splunk Dashboard Studio](https://docs.splunk.com/Documentation/SplunkCloud/latest/DashStudio/Introduction)

**Project Repository**:
- GitHub: https://github.com/qws941/splunk.git
- CLAUDE.md: Project-specific AI instructions
- README.md: Project overview and quick start

---

## 📞 Support

**Issues or Questions**:
1. Check troubleshooting section above
2. Review project documentation in `docs/`
3. Open GitHub issue: https://github.com/qws941/splunk/issues
4. Review test queries: `test-queries/README.md`

**Expected Result After Deployment**:
- ✅ FortiGate logs forwarded to Splunk in real-time (< 1 second latency)
- ✅ Operational dashboards show device health and configuration changes
- ✅ Alerts trigger on critical events (hardware failures, HA failover, config changes)
- ✅ 99%+ upload success rate with minimal queue buildup
- ✅ All FortiGate devices visible in Splunk with proper metadata (devname, sourcetype, source)

---

**Guide Version**: 1.0
**Last Updated**: 2025-10-29
**Deployment Time**: 30-45 minutes for initial setup
**Maintenance**: Review quarterly for performance optimization
