# Legacy Syslog → FortiAnalyzer HEC Migration Guide

**Migration from direct FortiGate Syslog to FortiAnalyzer HEC centralized approach**

**Status**: Migration Plan (2025-10-29)
**Impact**: Zero data loss, improved centralized management
**Downtime**: 0 minutes (parallel operation during transition)

---

## 📊 Architecture Comparison

### Before: Direct Syslog (Legacy)

```
FortiGate-01 ──UDP 9514──┐
FortiGate-02 ──UDP 9514──├──→ Splunk (index=fw, sourcetype=fw_log, source=udp:9514)
FortiGate-03 ──UDP 9514──┘
```

**Characteristics**:
- ✅ Simple setup, direct device-to-Splunk
- ❌ No centralized management
- ❌ Limited log enrichment
- ❌ Each device needs Splunk connectivity
- ❌ No buffering on device failure
- ❌ Limited metadata (only source IP)

### After: FortiAnalyzer HEC (Current)

```
FortiGate-01 ──Logs──┐
FortiGate-02 ──Logs──├──→ FortiAnalyzer ──HEC 8088──→ Splunk (index=fortianalyzer, sourcetype=fortianalyzer:traffic)
FortiGate-03 ──Logs──┘                      ↓
                                    Enrichment, Buffering, Metadata
```

**Characteristics**:
- ✅ Centralized log management via FortiAnalyzer
- ✅ Automatic device metadata (devname, serial, firmware)
- ✅ Buffering and retry on network issues
- ✅ Compression (gzip) for bandwidth optimization
- ✅ Real-time forwarding (< 1 second latency)
- ✅ Single Splunk HEC endpoint (easier firewall rules)
- ✅ FortiManager integration (config change correlation)

---

## 🔄 Migration Strategy

**Approach**: Parallel operation with gradual cutover (zero downtime)

### Phase 1: Deploy HEC (Week 1)

**Goal**: Establish HEC pipeline while keeping Syslog active

1. **Create Dedicated Index** (Splunk) - **REQUIRED**
   - Settings → Indexes → New Index
   - Name: `fortianalyzer` (**NOT `fw`** - separate index for clear migration tracking)
   - Max Size: 500GB, Retention: 90 days
   - This allows:
     - Clear separation during migration
     - Independent retention policies
     - Easy rollback to legacy Syslog
     - No data mixing between old/new sources

2. **Create HEC Token** (Splunk)
   - Settings → Data Inputs → HTTP Event Collector → New Token
   - Name: `fortianalyzer-prod`
   - Index: `fortianalyzer` (**NOT `fw`**)
   - Sourcetype: `fortianalyzer:traffic`
   - Save token value

3. **Configure FortiAnalyzer** (CLI)
   - Apply `configs/faz-to-splunk-hec.conf`
   - Verify `set index "fortianalyzer"` (NOT `fw`)
   - Set status to `enable`
   - Verify: `diagnose log-fetch client-profile status splunk-hec-primary`

4. **Monitor Dual Ingestion** (Splunk)
   ```spl
   # Should see both indexes active
   | metadata type=sources
   | search index=fw OR index=fortianalyzer
   | stats count by index, sourcetype, source

   # Expected:
   # index=fw, sourcetype=fw_log, source=udp:9514, count=10000
   # index=fortianalyzer, sourcetype=fortianalyzer:traffic, source=fortianalyzer-prod, count=10000
   ```

5. **Verify Data Parity**
   ```spl
   # Compare event counts between indexes (should be within 5%)
   (index=fw OR index=fortianalyzer) earliest=-1h
   | timechart span=5m count by index

   # Verify no duplicate devices
   (index=fw OR index=fortianalyzer) earliest=-15m
   | stats dc(index) as index_count by devname
   | where index_count > 1
   # Should return 0 results (no device in both indexes)
   ```

**Success Criteria**: Both pipelines receiving data for 7 days with < 1% difference in event count

### Phase 2: Update Dashboards (Week 2)

**Goal**: Dashboards work with both sourcetypes during transition

1. **Update Dashboard Queries** (search both indexes during migration)
   ```spl
   # Before (Legacy Syslog only)
   index=fw sourcetype=fw_log
   | stats count by devname

   # During Migration (both indexes)
   (index=fw OR index=fortianalyzer)
   | stats count by devname

   # After Cutover (HEC only)
   index=fortianalyzer
   | stats count by devname
   ```

   **Dashboard Update Example**:
   ```xml
   <!-- Before -->
   <query>index=fw | stats count by devname</query>

   <!-- During Migration (Phase 2-4, supports both) -->
   <query>(index=fw OR index=fortianalyzer) | stats count by devname</query>

   <!-- After Cutover (Phase 5+, HEC only) -->
   <query>index=fortianalyzer | stats count by devname</query>
   ```

2. **Deploy Updated Dashboards**
   - Dashboards already use `index=fw` without sourcetype filter (no changes needed)
   - Verify all panels show data from both sources

3. **Test Operational Queries**
   - All 13 test queries in `test-queries/*.spl` use `index=fw` (no changes needed)
   - Run each query, verify results

**Success Criteria**: All dashboards and queries show data from both pipelines

### Phase 3: Update Alerts (Week 2)

**Goal**: Alerts trigger on both sourcetypes

1. **Review Alert Configurations**
   - `configs/savedsearches-fortigate-alerts.conf` uses `index=fw` (no changes needed)
   - Test each alert with both Syslog and HEC data

2. **Consolidate Alert Configs** (cleanup)
   - Keep: `savedsearches-fortigate-alerts.conf` (production, no eval errors)
   - Archive: `savedsearches-fortigate-alerts-fixed.conf` (duplicate)

**Success Criteria**: Alerts trigger correctly on both sourcetypes for 7 days

### Phase 4: Cutover Preparation (Week 3)

**Goal**: Validate HEC as primary data source

1. **7-Day Stability Check**
   ```spl
   # HEC upload success rate (should be > 99%)
   index=_internal source=*http_event_collector* earliest=-7d
   | stats count by status
   | eval success_rate = round(count/sum(count)*100, 2)

   # FortiAnalyzer queue status (should be near 0)
   # Run on FAZ CLI: diagnose log-fetch queue status
   ```

2. **Performance Comparison**
   ```spl
   # Compare latency (HEC should be < 1 second)
   index=fw earliest=-1h
   | eval latency = _indextime - _time
   | stats avg(latency) as avg_latency_sec by sourcetype
   ```

3. **Data Quality Check**
   ```spl
   # Verify enriched fields from FortiAnalyzer
   index=fw sourcetype=fortianalyzer:* earliest=-1h
   | stats dc(devname) as unique_devices,
           dc(type) as log_types,
           dc(subtype) as log_subtypes

   # Should see: devname, type, subtype, logid, level, etc.
   ```

**Success Criteria**: HEC pipeline stable for 7 consecutive days with < 0.1% errors

### Phase 5: Disable Syslog (Week 4)

**Goal**: Switch to HEC-only operation

1. **Disable Syslog Input** (Splunk)
   - Settings → Data Inputs → UDP → 9514 → Disable
   - OR comment out in `inputs.conf`:
     ```ini
     # DEPRECATED: Replaced by FortiAnalyzer HEC (2025-10-29)
     # [udp://9514]
     # ...
     ```

2. **Monitor for Issues** (24 hours)
   ```spl
   # Verify no data loss
   index=fw earliest=-1h
   | timechart span=5m count

   # Should show continuous data flow, no gaps
   ```

3. **Disable FortiGate Syslog** (optional, after 7 days)
   - FortiGate logs already going to FortiAnalyzer
   - No configuration change needed on FortiGate
   - Syslog was redundant (both FAZ and Splunk receiving logs)

4. **Archive Legacy Config**
   ```bash
   # Archive legacy Syslog configuration
   mkdir -p configs/archive-2025-10-29
   mv configs/inputs-udp.conf configs/archive-2025-10-29/
   ```

**Success Criteria**: 7 days of HEC-only operation with no incidents

### Phase 6: Post-Migration Cleanup (Week 5)

**Goal**: Remove legacy references, document new architecture

1. **Update Documentation**
   - ✅ `CLAUDE.md`: Update data flow section
   - ✅ `README.md`: Reference HEC setup guide
   - ✅ `docs/FAZ_HEC_SETUP_GUIDE.md`: Already created

2. **Consolidate Configurations**
   - Keep: `faz-to-splunk-hec.conf` (production)
   - Archive: `inputs-udp.conf` (legacy Syslog)
   - Keep: `savedsearches-fortigate-alerts.conf` (production)
   - Archive: `savedsearches-fortigate-alerts-fixed.conf` (duplicate)

3. **Update CLAUDE.md Data Flow** (from Syslog to HEC)

**Success Criteria**: Documentation reflects HEC-only architecture

---

## 📋 Pre-Migration Checklist

Before starting Phase 1:

- [ ] FortiAnalyzer firmware ≥ 6.4.0
- [ ] FortiGate devices already sending logs to FortiAnalyzer
- [ ] Splunk has available HEC token quota
- [ ] Network allows FortiAnalyzer → Splunk:8088 (firewall rules)
- [ ] Backup current Splunk configuration (`inputs.conf`, dashboards)
- [ ] Test HEC endpoint: `curl -k https://splunk:8088/services/collector/health`

---

## 🔧 Rollback Plan

If issues occur during migration:

### Immediate Rollback (< 5 minutes)

1. **Disable HEC Client Profile** (FortiAnalyzer CLI)
   ```bash
   config system log-fetch client-profile
       edit "splunk-hec-primary"
           set status disable
       next
   end
   ```

2. **Re-enable Syslog Input** (Splunk)
   - Settings → Data Inputs → UDP → 9514 → Enable
   - Restart Splunk: `/opt/splunk/bin/splunk restart`

3. **Verify Syslog Data Flow**
   ```spl
   index=fw sourcetype=fw_log earliest=-5m
   | stats count
   ```

### Full Rollback (if HEC abandoned)

1. Archive HEC configuration:
   ```bash
   mv configs/faz-to-splunk-hec.conf configs/archive-2025-10-29/
   ```

2. Restore legacy Syslog config:
   ```bash
   mv configs/archive-2025-10-29/inputs-udp.conf configs/
   ```

3. Update documentation to reflect Syslog-only architecture

---

## 📊 Key Differences (Reference)

| Aspect | Legacy Syslog | FortiAnalyzer HEC |
|--------|---------------|-------------------|
| **Protocol** | UDP 9514 | HTTPS 8088 |
| **Data Flow** | FortiGate → Splunk | FortiGate → FAZ → Splunk |
| **Sourcetype** | `fw_log` | `fortianalyzer:traffic` |
| **Source** | `udp:9514` | `fortianalyzer-prod` |
| **Host Field** | Source IP (e.g., `192.168.50.10`) | Device name (e.g., `FGT-HQ-FW01`) |
| **Metadata** | Limited (IP only) | Rich (devname, serial, firmware, type, subtype, logid) |
| **Buffering** | None (UDP is lossy) | FortiAnalyzer buffers 100MB locally |
| **Compression** | None | gzip (saves 60-80% bandwidth) |
| **Latency** | < 1 second | < 1 second (realtime) |
| **Management** | Per-device Syslog config | Centralized via FortiAnalyzer |
| **Failover** | None | Automatic retry, secondary HEC endpoint |

---

## 🎯 Expected Benefits Post-Migration

1. **Centralized Management**
   - Single FortiAnalyzer configuration for all FortiGate devices
   - Easier to add new devices (no Splunk config change)

2. **Better Metadata**
   - Device name (devname) instead of IP address
   - Automatic enrichment with device serial, firmware version
   - Log type/subtype/logid automatically extracted

3. **Improved Reliability**
   - FortiAnalyzer buffers 100MB locally (survives network outages)
   - Automatic retry on failure (3 attempts)
   - Secondary HEC endpoint for HA

4. **Bandwidth Optimization**
   - gzip compression saves 60-80% bandwidth
   - Larger batches (5000 logs per batch vs. 1 log per packet with Syslog)

5. **Operational Efficiency**
   - FortiManager integration (correlate config changes with events)
   - Unified log management platform (FortiAnalyzer GUI)
   - Better troubleshooting (FAZ diagnostics: `diagnose log-fetch queue status`)

---

## 📚 References

**Configuration Files**:
- `configs/faz-to-splunk-hec.conf` - FortiAnalyzer HEC configuration (NEW)
- `configs/archive-2025-10-29/inputs-udp.conf` - Legacy Syslog configuration (DEPRECATED)
- `configs/savedsearches-fortigate-alerts.conf` - Alert definitions (works with both)

**Deployment Guides**:
- `docs/FAZ_HEC_SETUP_GUIDE.md` - Step-by-step HEC deployment (NEW)
- `test-queries/README.md` - 13 operational monitoring queries (works with both)

**Architecture Docs**:
- `CLAUDE.md` - Project architecture (update data flow section post-migration)
- `README.md` - Quick start guide (update deployment method)

---

**Migration Version**: 1.0
**Last Updated**: 2025-10-29
**Estimated Duration**: 5 weeks (parallel operation) or 1 week (aggressive cutover)
**Risk Level**: Low (parallel operation eliminates data loss risk)
**Rollback Time**: < 5 minutes
