# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Project Overview

**FortiAnalyzer → Splunk Integration with Advanced Correlation Engine**

Multi-phase security event processing system that collects FortiAnalyzer events, performs correlation analysis, automates threat response, and sends Slack notifications.

### Quick Facts

- **Language**: JavaScript (ES Modules, Node.js 18+)
- **Runtime Dependencies**: 0 (zero - uses only Node.js built-ins)
- **Architecture**: Domain-Driven Design (3 domains: Integration, Security, Defense)
- **Deployment**: Dual mode (Local/Docker OR Cloudflare Workers)
- **Phase**: 4.1 - Advanced Correlation Engine (Production Ready)
- **LOC**: ~4,000 lines core JavaScript + 29 SPL queries + 1 production dashboard

### System Flow

```
FortiAnalyzer (보안 이벤트 수집)
    ↓
    Syslog Forwarding (UDP 514 또는 TCP 6514)
    ↓
Splunk (index=fw)
    ↓
Correlation Engine (6개 규칙, configs/correlation-rules.conf)
    ├─ Multi-Factor Threat Score (abuse + geo + login + frequency)
    ├─ Repeated High-Risk Events (tstats on risk_score > 70)
    ├─ Weak Signal Combination (5 indicators)
    ├─ Geo + Attack Pattern (high-risk countries)
    ├─ Time-Based Anomaly (Z-score > 3)
    └─ Cross-Event Type Correlation (APT detection)
    ↓
├─→ Data Model Acceleration (Fortinet_Security)
│   └─ Summary Indexing (summary_fw)
└─→ Automated Response
    ├─ FortiGate API (IP 차단, score ≥ 90)
    └─ Slack (알림, score 80-89 또는 특정 패턴)
```

**Recommended Setup**: FAZ Syslog → Splunk (가장 간단, 설정 2분)
- Alternative: Node.js HEC client available but not required for most use cases

---

## 🚀 Quick Start

### Essential Commands

```bash
# Local execution (Node.js 18+)
npm start

# Docker Compose (if available)
docker-compose up -d
docker-compose logs -f

# Cloudflare Workers (serverless production)
npm run dev:worker          # Local development with hot reload
npm run deploy:worker       # Deploy to production
npm run tail:worker         # Real-time logs

# Health check (Local/Docker)
curl http://localhost:3000/health
```

### Cloudflare Workers Secrets (one-time setup)

```bash
npm run secret:faz-host        # FortiAnalyzer host
npm run secret:faz-username    # admin
npm run secret:faz-password    # password
npm run secret:splunk-host     # Splunk HEC host
npm run secret:splunk-token    # HEC token
npm run secret:slack-token     # xoxb-<example>
npm run secret:slack-channel   # #splunk-alerts
```

### Dashboard Validation

```bash
# XML validation
python3 -c "import xml.etree.ElementTree as ET; ET.parse('configs/dashboards/correlation-analysis.xml'); print('✅ Valid')"

# Deploy dashboard via Splunk REST API
node scripts/deploy-dashboards.js
```

### Testing

```bash
# Generate mock data and send to Splunk
node scripts/generate-mock-data.js --count=100 --send

# Test Slack notifications
node scripts/slack-alert-cli.js --test
node scripts/slack-alert-cli.js --channel="splunk-alerts" --message="Test"
```

**Note on Testing**: This project has no formal automated test suite. Testing is performed via:
- Manual testing with mock data generation scripts
- Dashboard XML validation scripts
- Integration testing against real FortiAnalyzer/Splunk instances
- Slack notification test tools

---

## 🏗️ Architecture (Domain-Driven Design Level 3)

### Entry Points (2 deployment options)

**1. `index.js` - Local/Docker Execution**
- Direct Node.js: `npm start`
- HTTP server with health/metrics endpoints (:3000)
- PM2 process management support
- Continuous polling (1-minute interval)

**2. `src/worker.js` - Cloudflare Workers (Recommended for Production)**
- Serverless deployment: `npm run deploy:worker`
- Cron-triggered execution (every 1 minute)
- Global edge network
- Auto-scaling, zero infrastructure management

### Core Domains

**`domains/integration/`** - External System Connectors
- `fortianalyzer-direct-connector.js` - FAZ REST API client (JSON-RPC)
- `splunk-api-connector.js` - Splunk HEC client
- `splunk-rest-client.js` - Splunk REST API (dashboard deployment)
- `slack-connector.js` - Slack Bot API
- `splunk-queries.js` - 29 production SPL queries
- `splunk-dashboards.js` - 4 dashboard templates

**`domains/security/`** - Security Event Processing (Core Domain)
- `security-event-processor.js`
  - Event analysis: severity, risk_score, event_type classification
  - Alert triggering: `shouldAlert()` threshold evaluation
  - Correlation analysis: `correlateEvent()` multi-event pattern matching
  - Batch processing: `processEventBatch()` queue-based processing (every 5 seconds)

**`domains/defense/`** - Resilience Patterns
- `circuit-breaker.js`
  - States: CLOSED → OPEN → HALF_OPEN
  - Failure threshold: 5 consecutive failures trigger OPEN
  - Recovery timeout: 60 seconds before HALF_OPEN attempt

### Configuration Files (`configs/`)

| File | Purpose | Phase |
|------|---------|-------|
| `correlation-rules.conf` | 6 correlation rules (19KB) | 4.1 |
| `datamodels.conf` | Fortinet_Security data model | 3.3 |
| `savedsearches-acceleration.conf` | Summary indexing, baselines | 3.3 |
| `savedsearches-auto-block.conf` | Auto-blocking rules (3 searches) | 3.2 |

### Dashboard (`configs/dashboards/`)

**Production Dashboard**:
- `correlation-analysis.xml` (27KB)
  - Data source: `index=fw` (Syslog input from FAZ)
  - 21 panels across 13 rows
  - 6 correlation rules visualization
  - Automated response tracking
  - Interactive Slack notification test panel
  - Performance metrics

### Python Scripts (`scripts/`)

| Script | Purpose | Usage |
|--------|---------|-------|
| `fortigate_auto_block.py` | FortiGate API auto-blocking | Splunk alert action |
| `fetch_abuseipdb_intel.py` | AbuseIPDB threat intelligence | Cron (hourly) |
| `fetch_virustotal_intel.py` | VirusTotal threat intelligence | Cron (hourly) |

---

## 📊 Phase Implementation Status

### Phase 3.1: Threat Intelligence Integration ✅
**Components**:
- Lookups: `abuseipdb_lookup.csv`, `virustotal_lookup.csv`
- Scripts: `fetch_abuseipdb_intel.py`, `fetch_virustotal_intel.py`

**Key Queries**:
```spl
# AbuseIPDB integration
| lookup abuseipdb_lookup.csv ip AS src_ip OUTPUT abuse_score, country, isp
| where abuse_score >= 90

# Geo-location risk scoring
| eval geo_risk = case(
    country IN ("CN", "RU", "KP", "IR"), 50,
    country IN ("VN", "BR", "IN"), 30,
    1=1, 20)
```

### Phase 3.2: Automated Response System ✅
**Components**:
- Script: `fortigate_auto_block.py` (400 LOC)
- Config: `savedsearches-auto-block.conf` (3 searches)

**Auto-Block Workflow**:
```python
# fortigate_auto_block.py
process_correlation_results()
  → load_whitelist() (IP exclusion list)
  → load_blocked_ips() (prevent duplicates)
  → fg_client.block_ip(src_ip)
      → create_address_object()  # FortiGate address object
      → create_deny_policy()     # Deny policy creation
  → save_blocked_ip()
  → send_slack_notification()
```

### Phase 3.3: Search Acceleration & Data Model ✅
**Components**:
- Data Model: `datamodels.conf` (Fortinet_Security)
- Saved Searches: `savedsearches-acceleration.conf` (6 searches)

**Data Model Structure**:
```
Fortinet_Security (acceleration: 7 days)
└── Security_Events (Root Dataset)
    ├─ src_ip, dst_ip, severity, attack_name, risk_score
    └─ index=fw sourcetype="fortinet:fortigate:*"
```

**Performance**: 10x faster (tstats vs raw search), CPU -60%

### Phase 4.1: Advanced Correlation Engine ✅
**Components**:
- Dashboard: `correlation-analysis.xml` (21 panels, 13 rows)
- Config: `correlation-rules.conf` (6 rules)

**6 Correlation Rules**:

| Rule | Detection Method | Threshold | Schedule | Action |
|------|------------------|-----------|----------|--------|
| Multi-Factor Threat Score | abuse + geo + login + frequency | ≥75 | */15 min | Script |
| Repeated High-Risk Events | tstats on risk_score > 70 | ≥80 | */10 min | Script |
| Weak Signal Combination | 5 indicators | ≥80 | */15 min | Slack |
| Geo + Attack Pattern | High-risk country + active attack | ≥85 | */10 min | Script |
| Time-Based Anomaly | Z-score > 3, spike ratio > 10x | ≥85 | */10 min | Script |
| Cross-Event Type | 3+ attack types = APT | ≥90 | */15 min | Script + Slack |

**Automated Response Thresholds**:
- **90-100**: AUTO_BLOCK (FortiGate immediate blocking)
- **80-89**: REVIEW_AND_BLOCK (Slack review request)
- **75-79**: MONITOR (logging only)

**Dashboard Row 12-13** (Phase 4.1 features):
- Slack notification test panel (Interactive button)
- Alert history (24 hours)
- Success rate monitoring (Color-coded single value)

---

## 🔧 Key Implementation Patterns

### 1. Zero-Dependency HTTP Client (Critical!)

**All connectors use only Node.js built-in `https` module** - no external runtime dependencies:

```javascript
import https from 'https';

function makeRequest(options, data = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(body));
        } else {
          reject(new Error(`HTTP ${res.statusCode}`));
        }
      });
    });
    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}
```

**Why this matters**: When adding new connectors or modifying existing ones, **DO NOT introduce axios, node-fetch, or any HTTP library**. Use the pattern above.

### 2. Circuit Breaker Pattern

```javascript
import CircuitBreaker from './domains/defense/circuit-breaker.js';

const breaker = new CircuitBreaker({
  failureThreshold: 5,
  resetTimeout: 60000
});

const result = await breaker.call(
  () => fazConnector.getEvents(),           // Actual API call
  () => ({ events: [], fallback: true })    // Fallback when circuit is OPEN
);
```

### 3. Event Processing Queue Pattern

```javascript
// security-event-processor.js
processor.addEvents(events);  // Add to queue
processor.startProcessing();  // Background batch processing (every 5 seconds)

// Processing flow
addEvent() → enrichEvent() → eventQueue.push()
  ↓ (every 5 seconds)
processEventBatch() → processEvent()
  ↓
├─ correlateEvent()         # Correlation analysis
├─ shouldAlert() → triggerAlert() → Slack
└─ sendToSplunk()
```

### 4. ES Modules (Critical!)

**All files use ES Modules** (`package.json:type = "module"`):

```javascript
// ✅ CORRECT (.js extension is REQUIRED!)
import Connector from './domains/integration/fortianalyzer-direct-connector.js';

// ❌ WILL NOT WORK (.js extension missing)
import Connector from './domains/integration/fortianalyzer-direct-connector';

// ✅ CORRECT (Named export)
export { SecurityEventProcessor };
export default SecurityEventProcessor;
```

**Common mistake**: Forgetting `.js` extension in import statements will cause runtime errors.

### 5. Dual Entry Point Architecture

This codebase supports **two deployment models**:

| Aspect | `index.js` (Local/Docker) | `src/worker.js` (Cloudflare) |
|--------|---------------------------|------------------------------|
| Environment | `process.env.VAR` | `env.VAR` (function param) |
| Imports | `import X from './domains/...'` | Inline class definitions (no imports) |
| Scheduling | External cron/setInterval | `wrangler.toml` crons |

**When modifying domain logic**:
1. Edit files in `domains/` → `index.js` auto-reflects changes
2. For `src/worker.js` → **manually copy class code** (it cannot import from domains/)

---

## 🔔 Slack Integration (2 methods)

### Method 1: Splunk Plugin (action.slack) - For Dashboards ⭐

**Configuration**: `/opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf`

```ini
[slack]
param.token = xoxb-YOUR-BOT-TOKEN
param.channel = #splunk-alerts
param.from_user = Splunk FortiGate Alert
param.icon_emoji = :fire:
```

**Used in**:
- `correlation-rules.conf` lines 197-199 (Weak Signal)
- `correlation-rules.conf` lines 358-360 (Sophisticated Threat)
- Dashboard Row 12 test button

**Advantage**: Directly usable from dashboard, configured via Splunk Web UI

### Method 2: Python Script Webhook - For Auto-blocking

**Configuration**: `.env` file's `SLACK_WEBHOOK_URL`

**Used in**:
- `fortigate_auto_block.py` lines 155-190 (`send_slack_notification()`)

**Advantage**: Full customization, no plugin installation required

---

## 📝 Correlation Rules Modification Guide

### Location: `configs/correlation-rules.conf`

#### Rule 1: Multi-Factor Threat Score Adjustment

**Score calculation formula** (lines 38-47):
```ini
| eval abuse_component = coalesce(abuse_score, 0) * 0.4    # 40% weight
| eval geo_component = geo_risk * 0.2                      # 20% weight
| eval login_failures = if(match(msg, "..."), 30, 0)       # 30 points
| eval frequency_component = case(                          # max 30 points
    event_count > 100, 30,
    event_count > 50, 20,
    event_count > 10, 10,
    1=1, 0)
| eval correlation_score = round(abuse_component + geo_component + login_failures + frequency_component, 2)
```

**Threshold adjustment** (lines 48-57):
```ini
| where correlation_score >= 75    # Change this value (current: 75)

| eval action_recommendation = case(
    max_correlation_score >= 90, "AUTO_BLOCK",      # AUTO_BLOCK threshold
    max_correlation_score >= 80, "REVIEW_AND_BLOCK", # REVIEW threshold
    1=1, "MONITOR")
```

#### Rule 3: Weak Signal Combination Modification

**5 indicators** (lines 141-186):
```ini
# 1. Low abuse_score (lines 143-145)
| eval has_low_abuse = if(abuse_score > 0 AND abuse_score < 50, 1, 0)

# 2. Failed login (lines 148-150)
| eval has_failed_login = if(match(msg, "(?i)(failed.*login|authentication.*fail)"), 1, 0)

# 3. Port scan (lines 153-155)
| eval has_port_scan = if(match(msg, "(?i)(port.*scan|network.*scan)"), 1, 0)

# 4. Multiple targets (lines 158-160)
| eval has_multiple_targets = if(unique_dst_count > 5, 1, 0)  # 5+ targets

# 5. High frequency (lines 163-165)
| eval has_high_frequency = if(event_count > 20, 1, 0)  # 20+ events
```

---

## 🎨 Dashboard Modification Guide

### XML Entity Encoding (Important!)

Dashboard XML requires HTML entity encoding for special characters:

```xml
<!-- ❌ WRONG (XML parsing error) -->
<choice value="REVIEW_AND_BLOCK">Review & Block</choice>
"Low (<50)":"#32CD32"

<!-- ✅ CORRECT -->
<choice value="REVIEW_AND_BLOCK">Review &amp; Block</choice>
"Low (&lt;50)":"#32CD32"
```

**Encoding rules**:
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&apos;`

### Slack Test Button (Reference: Row 12)

**Location**: `configs/dashboards/correlation-analysis.xml` lines 527-604

```xml
<panel>
  <title>🚀 Slack 알림 실행</title>
  <html>
    <a href="/app/search/search?q=search%20index%3Dfw..."
       target="_blank"
       style="display: inline-block; background: ...; ">
      📤 Send Test Alert to Slack
    </a>
  </html>
</panel>
```

**How it works**:
1. Button click → Opens Splunk Search page
2. Generates test data (correlation_score=95)
3. Saves to `summary_fw` index
4. Triggers correlation rule
5. Executes `action.slack = 1`
6. Sends to Slack #splunk-alerts

---

## 🔍 Troubleshooting

### 1. Dashboard XML Parsing Error

**Symptom**: "not well-formed (invalid token): line X"

**Cause**: Special characters not encoded (`&`, `<`, `>`, `"`)

**Solution**:
```bash
# Run validation script
python3 /tmp/validate_dashboards.py

# Manual validation
python3 -c "import xml.etree.ElementTree as ET; ET.parse('configs/dashboards/correlation-analysis.xml')"
```

### 2. Correlation Rule Not Running

**Checks**:
```bash
# 1. Verify saved search exists
splunk btool savedsearches list --debug | grep "Correlation_"

# 2. Check cron schedule
grep "cron_schedule" configs/correlation-rules.conf

# 3. Data model acceleration status
index=_internal source=*summarization.log | stats count by savedsearch_name

# 4. Verify summary_fw index data
index=summary_fw marker="correlation_detection=*" | stats count by marker
```

### 3. FortiGate Auto-blocking Failure

**Checks**:
```bash
# 1. Python script permissions
ls -la scripts/fortigate_auto_block.py  # Should be -rwxr-xr-x

# 2. Environment variables
grep "FORTIGATE_" .env

# 3. Script logs
tail -f /opt/splunk/etc/apps/fortigate/logs/fortigate_auto_block.log

# 4. Whitelist check
cat /opt/splunk/etc/apps/fortigate/lookups/fortigate_whitelist.csv
```

### 4. Slack Notifications Not Received

**Checks**:
```bash
# 1. Bot token validity
curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer SLACK_BOT_TOKEN_PLACEHOLDER"

# 2. Bot channel invitation
# In Slack: /invite @Splunk FortiGate Alert

# 3. OAuth scopes (required: chat:write, channels:read, chat:write.public)
# https://api.slack.com/apps → Your App → OAuth & Permissions

# 4. Splunk alert action logs
tail -f /opt/splunk/var/log/splunk/splunkd.log | grep -i slack
```

### 5. Cloudflare Workers Deployment Failure

**Checks**:
```bash
# 1. Verify account_id in wrangler.toml
grep "account_id" wrangler.toml

# 2. Check secrets configuration
wrangler secret list

# 3. Local testing
npm run dev:worker

# 4. Deployment logs
npm run deploy:worker 2>&1 | tee deploy.log
```

---

## 📚 Key Documentation Files

### Setup Guides
- `docs/SIMPLE_SETUP_GUIDE.md` - 2-minute setup guide (Syslog method, recommended)
- `docs/HEC_INTEGRATION_GUIDE.md` - Alternative HEC setup methods
- `docs/CLOUDFLARE_DEPLOYMENT.md` - Cloudflare Workers deployment

### Phase Reports (Implementation History)
- `docs/DASHBOARD_OPTIMIZATION_PHASE3.1_REPORT.md` - Threat Intelligence (58KB)
- `docs/DASHBOARD_OPTIMIZATION_PHASE3.2_REPORT.md` - Automated Response (62KB)
- `docs/DASHBOARD_OPTIMIZATION_PHASE3.3_REPORT.md` - Data Model Acceleration (47KB)
- `docs/DASHBOARD_OPTIMIZATION_PHASE4.1_REPORT.md` - Correlation Engine (58KB)

### System Validation
- `docs/SYSTEM_HEALTH_VALIDATION_REPORT.md` - Full system validation (58KB)
- `docs/DASHBOARD_SLACK_INTEGRATION_GUIDE.md` - Complete Slack integration guide (28KB)

### Configuration Examples
- `configs/slack-alert-actions.conf.example` - Slack plugin configuration template
- `.env.example` - Environment variables template

---

## 🎯 Development Workflow

### 1. Adding New Correlation Rule

```bash
# 1. Edit correlation-rules.conf
vim configs/correlation-rules.conf

# 2. Add new [Correlation_YOUR_RULE_NAME] section
# 3. Write SPL query (tstats recommended)
# 4. Configure action.script or action.slack
# 5. Set cron_schedule

# 6. Git commit
git add configs/correlation-rules.conf
git commit -m "feat: Add new correlation rule for ..."
git push origin master
```

### 2. Adding Dashboard Panel

```bash
# 1. Back up current dashboard (use git history, don't commit backup files)
git diff configs/dashboards/correlation-analysis.xml

# 2. Edit dashboard XML
vim configs/dashboards/correlation-analysis.xml

# 3. Add new <row> and <panel>
# 4. Write SPL query
# 5. HTML entity encoding for special characters (& → &amp;, < → &lt;)

# 6. XML validation
python3 -c "import xml.etree.ElementTree as ET; ET.parse('configs/dashboards/correlation-analysis.xml'); print('✅ Valid')"

# 7. Git commit
git add configs/dashboards/correlation-analysis.xml
git commit -m "feat: Add new panel for ..."
git push origin master
```

### 3. Modifying Python Script (Auto-blocking Logic)

```bash
# 1. Edit script
vim scripts/fortigate_auto_block.py

# 2. Local testing (mock data)
echo '{"src_ip": "192.168.1.100", "correlation_score": 95}' | python3 scripts/fortigate_auto_block.py

# 3. Git commit
git add scripts/fortigate_auto_block.py
git commit -m "fix: Improve auto-block logic for ..."
git push origin master
```

---

## ⚠️ Critical Constraints & Gotchas

### 1. Zero Runtime Dependencies Philosophy

**DO NOT** add runtime dependencies (axios, lodash, etc.). Only `wrangler` is allowed as devDependency.

**Rationale**:
- Minimal attack surface
- Cloudflare Workers compatibility
- Fast startup time

### 2. ES Modules `.js` Extension Requirement

All imports **must** include `.js` extension or they will fail at runtime.

### 3. Dual Entry Point Synchronization

When modifying domain classes, **both** `index.js` and `src/worker.js` must be updated:
- `index.js`: Imports from `domains/` (automatic)
- `src/worker.js`: Inline code (manual copy required)

### 4. Git Workflow & Prohibited Commits

```bash
# Check changes
git status

# Stage (auto-exclude backup files)
git add -A
git reset *.backup *.bak *.old

# Commit (Conventional Commits)
git commit -m "feat: Add new feature"
git commit -m "fix: Resolve XML encoding issue"
git commit -m "docs: Update correlation rules guide"

# Push
git push origin master
```

**NEVER commit**:
- `.env` files (contains secrets)
- `*.backup`, `*.bak`, `*.old` files (use git history instead)
- Documentation in root directory (except README.md, CLAUDE.md, CHANGELOG.md, LICENSE)

### 5. XML Entity Encoding for Dashboards

Dashboard XML requires HTML entity encoding:

| Character | Encoded | Context |
|-----------|---------|---------|
| `&` | `&amp;` | Always |
| `<` | `&lt;` | In text/values |
| `>` | `&gt;` | In text/values |
| `"` | `&quot;` | In attributes |

**Example**:
```xml
<!-- ❌ WRONG - XML parsing error -->
<choice value="REVIEW_AND_BLOCK">Review & Block</choice>

<!-- ✅ CORRECT -->
<choice value="REVIEW_AND_BLOCK">Review &amp; Block</choice>
```

---

**Status**: Production Ready
**Current Phase**: 4.1 (Correlation Engine)
**Next Phase**: 4.2 (Machine Learning Integration)
**Node.js**: 18+
**Runtime Dependencies**: 0 (Zero Dependencies)
**Updated**: 2025-01-22
