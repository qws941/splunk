# Splunk Production Dashboards

**FortiAnalyzer → Splunk Integration** monitoring dashboards.

---

## 🔥 Production Dashboards (3 files only)

All production dashboards are in **Dashboard Studio JSON format** (no JavaScript).

```
studio-production/
├── 01-fortigate-operations.json      # Firewall operations monitoring
├── 02-faz-fmg-monitoring.json        # FAZ/FMG integrated monitoring
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
- Real-time traffic statistics (accept/deny/block)
- Top source/destination IPs
- Policy hit counts
- Bandwidth usage trends

**Data**: `index=fw` (FortiAnalyzer Syslog)

---

### 02-faz-fmg-monitoring.json
- FortiAnalyzer device status
- FortiManager operations
- Log ingestion rates
- System health metrics

**Data**: `index=fw`

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
├── test/                # Test dashboards
└── studio/              # Old Studio versions
```

**Total archived**: 42 files (20+ were duplicates/experiments)

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
