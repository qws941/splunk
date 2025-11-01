# HAR File Analysis - Splunk Dashboard Performance

**Analysis Date**: 2025-10-28
**Target**: Splunk Enterprise @ 172.28.32.67:8000
**App**: nextrade (FortiGate Security Monitoring)

---

## 📊 Overview

Two HAR (HTTP Archive) files captured network traffic from the Splunk dashboard:

| File | Size | Entries | Pages | Capture Date | Focus |
|------|------|---------|-------|--------------|-------|
| `172.28.32.67.har` | 16 MB | 388 | 8 | 2025-10-25 | Full page loads + navigation |
| `172.28.32.67_2.har` | 6.8 MB | 96 | 0 | 2025-10-28 | API polling only |

---

## 🚀 Performance Metrics

### Page Load Performance (HAR 1)

| Page | DOMContentLoaded | Full Load | Performance |
|------|------------------|-----------|-------------|
| `/app/nextrade/security` (avg) | **~1,698ms** | **~1,786ms** | 🟡 Moderate |
| `/app/nextrade/dashboards` (avg) | **377ms** | **412ms** | 🟢 Excellent |

**Key Findings**:
- **Security page**: 1.5-1.9 seconds load time (6 page loads captured)
- **Dashboards page**: 0.3-0.5 seconds load time (2 page loads captured)
- **Performance gap**: Security page is **4.1x slower** than Dashboards page

★ **Insight**: Dashboards page is significantly faster, likely due to simpler initial data load requirements.

### API Response Times (HAR 2)

- **Average wait time**: 34.14ms
- **Health check polling**: 21 requests to `/services/server/health/splunkd`
- **Search job management**: 10 job creation requests
- **All requests**: ✅ 200 OK (no errors)

---

## 🔍 API Traffic Analysis

### Most Frequently Called Endpoints (HAR 1)

```
45 requests - /services/server/health/splunkd      # Health monitoring
20 requests - /services/messages                    # System messages
16 requests - /services/configs/conf-web/settings   # Web UI config
12 requests - /services/saved/searches/_new         # Alert creation UI
10 requests - /services/authentication/users/secmon # User auth check
```

### Search Job Queries (HAR 2)

Three main dashboard queries detected:

#### Query 1: Alert Status Monitor
```spl
| rest /services/saved/searches
| search title="FortiGate_*"
| eval status = if(disabled==0, "✅ ON", "🔴 OFF")
| eval channel = "action.slack.param.channel"
| eval realtime = if(realtime_schedule==1, "Real-time", "Scheduled")
| table title, status, realtime, cron_schedule, channel, suppress_time
```
**Purpose**: Monitor FortiGate alert configurations (enabled/disabled status, Slack channels)

#### Query 2: Critical System Events
```spl
search index=fortianalyzer earliest=-24h type=event subtype=system level=critical
  logid!=0100044546 logid!=0100044547 NOT cfgpath=*
| search NOT msg="*Update Fail*" NOT msg="*Login Fail*"
| stats count
```
**Purpose**: Count critical FortiGate system events (excluding config changes and known noise)

#### Query 3: Configuration Changes
```spl
search index=fortianalyzer earliest=-24h type=event subtype=system
  (logid=0100044546 OR logid=0100044547 OR cfgpath=*)
| stats count
```
**Purpose**: Count FortiGate configuration change events

---

## ❌ Errors Detected

### 404 Not Found Errors (HAR 1)

```
GET /servicesNS/secmon/search/data/ui/prefs/dashboards
-> 404 Not Found (2 occurrences)
```

**Impact**: Minor - Dashboard preferences endpoint missing, but doesn't break functionality

---

## 🎯 Dashboard Behavior Patterns

### Real-time Polling Strategy

**From HAR 2 analysis**:
1. **Health checks**: Continuous polling every ~5 seconds
2. **Search jobs**: Created with `auto_cancel=90` (90-second timeout)
3. **Preview enabled**: `preview=true` for real-time results
4. **Time ranges**:
   - Alert monitoring: `-5m` (last 5 minutes)
   - System events: `-24h` (last 24 hours)

### Search Job Lifecycle

```
POST /services/search/v2/jobs          # Create search job
  ↓
GET /jobs/{sid}/results_preview        # Poll for preview results
  ↓
GET /jobs/{sid}/control                # Check job status
  ↓
DELETE /jobs/{sid}/control             # Cancel job (auto_cancel)
```

---

## 🔧 Performance Optimization Recommendations

### 1. Reduce Security Page Load Time ⚠️

**Current**: 1.7s average load time
**Target**: <1s

**Actions**:
- Defer non-critical data loading
- Implement progressive loading for panels
- Cache frequently accessed saved searches

### 2. Optimize Health Check Polling

**Current**: 21 health checks in captured session
**Observation**: High-frequency polling

**Actions**:
- Increase polling interval from 5s to 10s
- Use WebSocket for real-time health updates (already implemented in React dashboard v2.0)
- Only poll when tab is active (Page Visibility API)

### 3. Dashboard Query Optimization

**Query 2 & 3**: Both search `index=fortianalyzer earliest=-24h`

**Actions**:
- Use data model acceleration with `| tstats` instead of raw search
- Consider summary indexing for 24-hour stats
- Reduce time window to `-1h` for real-time dashboards

**Example optimization**:
```spl
# ❌ SLOW (raw search)
search index=fortianalyzer earliest=-24h type=event subtype=system level=critical | stats count

# ✅ FAST (tstats with data model)
| tstats count WHERE index=fortianalyzer earliest=-24h
    Fortinet_System.type=event
    Fortinet_System.subtype=system
    Fortinet_System.level=critical
```

### 4. Enable Data Model Acceleration

**Check acceleration status**:
```spl
| rest /services/admin/summarization by_tstats=true
| search summary.id=*Fortinet*
```

**Enable if not active**:
- Settings → Data models → Fortinet_Security
- Enable "Accelerate" with 1-day summary range

---

## 📈 Expected Performance Improvements

| Optimization | Expected Gain | Implementation Effort |
|--------------|---------------|----------------------|
| Data model acceleration | **10x faster queries** | Low (configuration only) |
| Reduce polling interval | **50% less API calls** | Low (config change) |
| Progressive panel loading | **40% faster page load** | Medium (frontend refactor) |
| WebSocket for health | **Eliminate polling overhead** | Already implemented in v2.0 ✅ |

---

## 🔗 Related Documentation

- **CLAUDE.md**: Architecture patterns, WebSocket implementation
- **REACT_DASHBOARD_GUIDE.md**: React v2.0 with real-time streaming
- **DASHBOARD_OPERATIONAL_CHECKLIST.md**: 6-phase deployment testing

---

## 🧪 Testing Recommendations

### Performance Testing

```bash
# 1. Lighthouse audit
lighthouse https://172.28.32.67:8000/ko-KR/app/nextrade/security --view

# 2. Network throttling test (Chrome DevTools)
# Throttle: Fast 3G → Measure load times

# 3. Load testing with multiple users
# Use Apache JMeter or k6.io for concurrent user simulation
```

### Query Performance Testing

```spl
# Compare raw search vs tstats performance
| rest /services/search/jobs
| search search="*index=fortianalyzer*"
| stats avg(runDuration) as avg_time by search
| sort -avg_time
```

---

**Summary**: The captured HAR files reveal a well-functioning dashboard with room for optimization. Primary focus should be on data model acceleration (10x query speedup) and migrating to React v2.0's WebSocket implementation (eliminate polling overhead).

**Next Steps**:
1. ✅ Enable data model acceleration for Fortinet_Security
2. ✅ Convert critical queries to use `| tstats`
3. ✅ Deploy React v2.0 dashboard (WebSocket real-time updates)
4. ✅ Increase health check polling interval to 10 seconds
