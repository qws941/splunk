# Splunk Production Dashboards

**FortiAnalyzer → Splunk Integration** monitoring dashboards.

---

## 🔥 Production Dashboards (3 files only)

All production dashboards are in **Dashboard Studio JSON format** (no JavaScript).

```
studio-production/
├── 01-fortigate-operations.json      # FortiGate firewall operations
├── 02-fmg-operations.json            # FortiManager policy/object operations
└── 03-slack-alert-control.json       # Slack notification control
```

**Deploy via Splunk Web UI:**
```
1. Dashboards → Create New Dashboard → Dashboard Studio
2. Click "Source" → Paste JSON content
3. Save
```

**⚠️ DO NOT use automated deploy scripts** - Follow `docs/ENTERPRISE_DASHBOARD_DEPLOYMENT.md` for phased rollout.

---

## 📊 Dashboard Details

### 01-fortigate-operations.json
**FortiGate firewall operations monitoring**
- Event timeline by severity
- Severity breakdown (pie chart)
- Top source IPs
- Blocked traffic events
- Critical events
- Recent security events

**Data**: `index=fw` (FortiGate Syslog)

---

### 02-fmg-operations.json
**FortiManager operations dashboard**
- Total events and critical/high severity counts
- Event timeline by severity (stacked area chart)
- Top attack source IPs with threat scoring
- Attack types distribution (horizontal bar)
- Geographic distribution (choropleth map)
- **Policy changes** (recent FMG policy modifications)
- Blocked traffic trend

**Focus**: Policy changes, object CRUD operations, configuration management

**Data**: `index=fw sourcetype=fortimanager`

---

### 03-slack-alert-control.json
- Enable/disable Slack alerts
- Alert delivery status
- Current configuration view

**Integration**: Works with Splunk REST API only (no JavaScript buttons)

**Control alerts via**:
```bash
# Splunk Web UI (Recommended)
Settings → Searches, reports, and alerts → Select alert → Enable/Disable

# REST API
curl -k -u admin:password \
  -d 'disabled=0' \
  https://splunk.jclee.me:8089/servicesNS/nobody/search/saved/searches/FAZ_Critical_Alerts
```

---

## 🗂️ Archive

All legacy dashboards (XML, old JSON, test files) are in:
```
archive-all-legacy/
├── production/          # Old XML versions
├── archive/             # Historical backups
├── archive-legacy/      # Very old files
├── archive-2025-10/     # October 2025 experiments
├── merged-2025-10-27/   # Pre-merge dashboards 01 & 02
├── test/                # Test dashboards
└── studio/              # Old Studio versions
```

**Total archived**: 42 files (legacy XML, old JSON, test files)

**Do not use** - kept for historical reference only.

---

## 🚨 Validation

**Before deploying**:
```bash
# Validate JSON syntax
jq empty studio-production/*.json

# Verify data exists
splunk search "index=fw earliest=-1h | stats count"
```

---

## 📚 Related Docs

- **Enterprise Deployment**: `docs/ENTERPRISE_DASHBOARD_DEPLOYMENT.md`
- **Correlation Rules**: `../correlation-rules.conf`
- **Slack Integration**: `docs/SLACK_BLOCKKIT_DEPLOYMENT.md`

---

**Version**: 2.0 (JSON Studio only)
**Last Cleanup**: 2025-10-27
**Repository**: https://github.com/qws941/splunk.git
