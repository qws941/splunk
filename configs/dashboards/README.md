# Splunk Dashboards

**FortiAnalyzer → Splunk Integration Dashboards**

This directory contains Splunk dashboards for security monitoring, correlation analysis, and operational visibility.

---

## 📂 Directory Structure

```
dashboards/
├── correlation-analysis.xml          # 🔥 PRODUCTION - Advanced correlation engine
├── fortigate-operations.xml          # 🔥 PRODUCTION - Firewall operations
├── slack-alert-control.xml           # 🔥 PRODUCTION - Slack notification control
├── studio/                            # Dashboard Studio (Splunk 9.0+)
│   ├── correlation-analysis-studio.json
│   ├── fortinet-management-dashboard.json
│   └── slack-toggle-control.json
├── test/                              # Testing dashboards
│   ├── fortigate-operations-test.xml
│   ├── slack-test-simple.xml
│   └── slack-test.xml
└── archive/                           # Backup/Legacy dashboards
    ├── fortigate-unified.xml
    ├── fortigate.xml
    ├── fortigate-operations-integrated.xml
    ├── fortinet-management-slack-control.xml
    └── slack-toggle.json (Korean version)
```

---

## 🔥 Production Dashboards

### correlation-analysis.xml (729 lines)
**Purpose**: Advanced threat correlation engine with automated response

**Features**:
- 6 correlation rules (Multi-Factor, Repeated Events, Weak Signals, etc.)
- Automated FortiGate blocking for high-confidence threats
- Slack alerts for analyst review
- Summary index: `index=summary_fw marker="correlation_detection=*"`

**Data Source**: `index=fw` (FortiAnalyzer Syslog)

**Deploy**:
```bash
# Splunk Web UI
Settings → User Interface → Dashboards → Create New Dashboard
→ Source mode → Paste XML

# Or via REST API
node scripts/deploy-dashboards.js
```

---

### fortigate-operations.xml (269 lines)
**Purpose**: Real-time firewall operations monitoring

**Panels**:
- Traffic statistics by action (accept/deny/block)
- Top source/destination IPs
- Policy hit counts
- Bandwidth usage trends

**Data Source**: `index=fw`

**Use Case**: Daily operations, traffic analysis, capacity planning

---

### slack-alert-control.xml (218 lines)
**Purpose**: Slack notification ON/OFF control panel

**Features**:
- Enable/disable Slack alerts dynamically
- Current alert status monitoring
- Slack delivery verification
- KV Store: `slack_toggle_log`

**Integration**: Works with `savedsearches-slack-toggle.conf`

---

## 🎨 Dashboard Studio (studio/)

**Requires**: Splunk 9.0+

Modern JSON-based dashboards with enhanced UI/UX:

| File | Lines | Purpose |
|------|-------|---------|
| `correlation-analysis-studio.json` | 732 | Studio version of correlation dashboard |
| `fortinet-management-dashboard.json` | 991 | Comprehensive device management |
| `slack-toggle-control.json` | 318 | Slack control (Studio version) |

**Advantages**:
- Responsive design
- Better visualizations
- Faster rendering
- Modern editing experience

**Deploy**: Splunk Web UI → Dashboards → Create Dashboard Studio → Import JSON

---

## 🧪 Test Dashboards (test/)

**Purpose**: Development and validation

| File | Purpose |
|------|---------|
| `fortigate-operations-test.xml` | Test operations dashboard features |
| `slack-test-simple.xml` | Simple Slack integration test |
| `slack-test.xml` | Full Slack integration test |

**Usage**: Not for production - use for testing Slack webhooks, queries, etc.

---

## 🗂️ Archive Dashboards (archive/)

**Purpose**: Historical reference and rollback

| File | Reason |
|------|--------|
| `fortigate-unified.xml` | Experimental unified dashboard (not finalized) |
| `fortigate.xml` | Older security dashboard (replaced by operations.xml) |
| `fortigate-operations-integrated.xml` | Combined ops + Slack (split into separate) |
| `fortinet-management-slack-control.xml` | Legacy device management |
| `slack-toggle.json` | Korean version (use English version instead) |

**Note**: Do not deploy - kept for reference only

---

## 📊 Data Sources

All dashboards use the following indexes:

| Index | Purpose | Data Source |
|-------|---------|-------------|
| `index=fw` | Primary security events | FortiAnalyzer Syslog |
| `index=summary_fw` | Correlation results | Scheduled searches |
| `index=_internal` | Splunk monitoring | Splunk internal logs |
| `index=slack_toggle_log` | Slack state tracking | KV Store writes |

**Current Setup** (as of commit 0a0ee15): Using Syslog → Splunk → `index=fw`

**Legacy**: Some files may reference `index=fortigate_security` (old HEC approach)

---

## 🚀 Deployment Guide

### Method 1: Splunk Web UI (Recommended)
```
1. Go to Settings → User Interface → Dashboards
2. Click "Create New Dashboard"
3. Choose "Dashboard Source" from dropdown
4. Paste XML content
5. Save as "{dashboard-name}"
```

### Method 2: REST API (Automated)
```bash
# Deploy all production dashboards
node scripts/deploy-dashboards.js

# Deploy specific dashboard
curl -k -u admin:password https://splunk.example.com:8089/servicesNS/nobody/search/data/ui/views \
  -d "name=correlation_analysis" \
  --data-urlencode eai:data@configs/dashboards/correlation-analysis.xml
```

### Method 3: File System (Manual)
```bash
# Copy to Splunk app directory
cp correlation-analysis.xml $SPLUNK_HOME/etc/apps/fortigate/local/data/ui/views/

# Restart Splunk
splunk restart splunkweb
```

---

## 🔧 Maintenance

### Validate XML Syntax
```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('correlation-analysis.xml'); print('✅ Valid')"
```

### Validate JSON Syntax
```bash
jq empty studio/correlation-analysis-studio.json && echo "✅ Valid"
```

### Check Dashboard Permissions
```
Splunk Web → Settings → User Interface → Dashboards → [Dashboard Name] → Edit Permissions
```

### Export Dashboard
```
Settings → Dashboards → [Dashboard] → Edit → Source → Copy XML/JSON
```

---

## 📝 Best Practices

1. **Always test in non-production** before deploying
2. **Validate XML/JSON syntax** before deployment
3. **Use descriptive panel titles** for clarity
4. **Optimize queries** - use `tstats` for data models
5. **Set appropriate time ranges** - avoid "All time"
6. **Document custom searches** with comments
7. **Version control** - commit dashboard changes to Git

---

## 🐛 Troubleshooting

### Dashboard Not Showing Data
```spl
# Check if index has data
index=fw earliest=-1h | head 10

# Check data model acceleration
| rest /services/admin/summarization by_tstats=true
| search summary.id=*Fortinet_Security*
```

### XML Parse Error
```bash
# Validate XML
python3 -c "import xml.etree.ElementTree as ET; ET.parse('dashboard.xml')"

# Common issues:
# - Unescaped special characters: & → &amp;, < → &lt;
# - Missing closing tags
# - Invalid attribute syntax
```

### Dashboard Studio JSON Error
```bash
# Validate JSON
jq empty dashboard.json

# Common issues:
# - Trailing commas
# - Unescaped quotes in strings
# - Invalid property names
```

---

## 📚 Related Documentation

- **Correlation Rules**: `../correlation-rules.conf`
- **Alert Actions**: `../alert_actions.conf`
- **Data Models**: `../datamodels.conf`
- **Deployment Guide**: `../../docs/SPLUNK_DASHBOARD_DEPLOYMENT.md`
- **Analysis Report**: `../../docs/DASHBOARD_ANALYSIS_REPORT.md`

---

**Last Updated**: 2025-10-24
**Maintainer**: jclee
**Repository**: https://github.com/qws941/splunk.git
