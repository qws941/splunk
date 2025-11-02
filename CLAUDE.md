# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Project Overview

**FortiAnalyzer → Splunk Integration with Advanced Correlation Engine**

Security event processing system with three deployment modes and zero runtime dependencies (backend only).

**Key Facts**:
- **Version**: 2.0.0 (React Dashboard + Legacy Backend + Cloudflare Workers)
- **Runtime Dependencies**: 0 (backend uses Node.js built-ins only)
- **Frontend**: React 18, Vite, Zustand, Recharts (~318 packages, dev only)
- **Architecture**: Triple-entry (React Dashboard, Legacy, Workers)
- **Data Flow**: FortiAnalyzer Syslog → Splunk (index=fw) → Correlation Engine → Auto-Block/Slack
- **Repository**: https://github.com/qws941/splunk.git

**Key Indexes**:
- `index=fw` - Primary Syslog data (104+ references)
- `index=summary_fw` - Correlation results (18 references)

---

## 🚀 Essential Commands

### Development Workflow

```bash
# React Dashboard (v2.0 - Recommended)
npm install                              # Install backend deps
cd frontend && npm install               # Install frontend deps

# Development (requires 2 terminals)
npm start                                # Terminal 1: Backend API (port 3001)
cd frontend && npm run dev               # Terminal 2: React frontend (port 3000)

# Production build
cd frontend && npm run build             # Build frontend → frontend/dist/
npm start                                # Serve backend API only

# Health checks
curl http://localhost:3001/health        # Backend API health
curl http://localhost:3001/metrics       # Prometheus metrics
```

### Legacy Backend (v1.x)

```bash
npm run start:legacy                     # Port 3000, no frontend
curl http://localhost:3000/health        # Health check
```

### Cloudflare Workers (Serverless)

```bash
# Setup secrets (one-time)
npm run secret:faz-host                  # FortiAnalyzer hostname
npm run secret:faz-username              # Admin username
npm run secret:faz-password              # Admin password
npm run secret:splunk-host               # Splunk HEC hostname
npm run secret:splunk-token              # HEC token
npm run secret:slack-token               # Slack bot token (xoxb-<example>)
npm run secret:slack-channel             # Slack channel (#splunk-alerts)

# Development & deployment
npm run dev:worker                       # Local dev with hot reload
npm run deploy:worker                    # Deploy to production
npm run tail:worker                      # Real-time logs

# Debug deployment issues
wrangler secret list                     # Verify secrets configured
grep "account_id" wrangler.toml          # Verify account ID
```

### Splunk Dashboard Operations

```bash
# Validate dashboard XML before deployment
python3 -c "import xml.etree.ElementTree as ET; ET.parse('configs/dashboards/correlation-analysis.xml'); print('✅ Valid XML')"

# Deploy dashboards via REST API
node scripts/deploy-dashboards.js

# Test correlation rules manually
splunk search "| savedsearch Correlation_Multi_Factor_Threat_Score"

# Check correlation detections
index=summary_fw marker="correlation_detection=*" | stats count by correlation_type

# Monitor auto-block actions
index=_internal source=*fortigate_auto_block.log
```

### Testing & Debugging

```bash
# Generate mock data
node scripts/generate-mock-data.js --count=100 --send

# Test Slack notifications
node scripts/slack-alert-cli.js --test
node scripts/slack-alert-cli.js --channel="splunk-alerts" --message="Test from CLI"

# Verify data model acceleration
index=_internal source=*summarization.log | stats count by savedsearch_name

# Check summary index data
index=summary_fw marker="correlation_detection=*" earliest=-24h | stats count by marker
```

---

## 🏗️ Architecture Deep Dive

### Triple Entry Point Pattern (Critical!)

This codebase has **three completely different entry points** that share domain logic differently:

| Aspect | React v2.0 | Legacy v1.x | Cloudflare Workers |
|--------|------------|-------------|--------------------|
| Entry | `backend/server.js` | `index.js` | `src/worker.js` |
| Ports | Backend: 3001, Frontend: 3000 | 3000 | N/A (serverless) |
| Domain Imports | `import X from '../domains/...'` | `import X from './domains/...'` | **Inline classes (no imports!)** |
| Frontend | React 18 + WebSocket | None | None |
| Environment | `process.env.VAR` | `process.env.VAR` | `env.VAR` (function param) |

**When modifying domain classes**:
1. Edit `domains/integration/*.js` or `domains/security/*.js`
2. Changes automatically reflected in `backend/server.js` and `index.js`
3. **For `src/worker.js`**: Manually copy class code (it cannot use imports due to Workers limitations)

**Why this matters**: If you add a new method to `SecurityEventProcessor`, you must:
- ✅ Edit `domains/security/security-event-processor.js` (React + Legacy auto-update)
- ⚠️ Manually copy the class to `src/worker.js` inline code

### React Dashboard Real-time Architecture

**State Synchronization Pattern**:

```
┌─────────────────────────────────────────────────┐
│         Zustand Store (Single Source)            │
│  - stats, events, alerts, correlation, threats   │
└────────────┬────────────────────────┬────────────┘
             │                        │
        REST Polling          WebSocket Real-time
        (Initial Load)        (Live Updates)
             │                        │
    ┌────────┴────────┐      ┌────────┴────────┐
    │ fetchStats()    │      │ addRealtimeEvent │
    │ fetchEvents()   │      │ updateRealtimeStats│
    └─────────────────┘      └──────────────────┘
             │                        │
    ┌────────┴────────────────────────┴────────┐
    │         Backend API Server               │
    │  ┌──────────┐      ┌──────────────┐     │
    │  │APIRouter │      │WebSocketServer│     │
    │  │(REST)    │      │(RFC 6455)     │     │
    │  └──────────┘      └──────────────┘     │
    └──────────────────────────────────────────┘
```

**Key Pattern**:
- **Initial page load**: REST API (`fetchStats()`, `fetchEvents()`) populates Zustand store
- **After load**: WebSocket updates (`addRealtimeEvent()`) merge into same store
- **No race conditions**: Store mutations are synchronous, updates append to existing arrays
- **Memory management**: `events` array sliced to last 100 entries automatically

### Zero-Dependency HTTP Client Pattern

**Critical for adding new connectors**: All HTTP requests use Node.js `https` module only.

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
          reject(new Error(`HTTP ${res.statusCode}: ${body}`));
        }
      });
    });
    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}
```

**DO NOT introduce**: `axios`, `node-fetch`, `got`, or any HTTP library. This pattern must be followed for all new API integrations.

### Event Processing Queue Pattern

**How events flow from FAZ to Splunk/Slack**:

```
FortiAnalyzer API
        ↓
SecurityEventProcessor.addEvents(events)    // Add to queue
        ↓
eventQueue: [evt1, evt2, evt3, ...]         // In-memory queue
        ↓
processEventBatch() (every 5 seconds)       // Background processing
        ↓
For each event:
  ├─ enrichEvent()           // Add risk_score, severity
  ├─ correlateEvent()        // Check correlation rules
  ├─ shouldAlert()           // Check alert thresholds
  │   ├─ true → triggerAlert() → Slack notification
  │   └─ false → continue
  └─ sendToSplunk()          // HEC submission
        ↓
Splunk HEC (index=fw)
        ↓
Correlation Engine (6 rules, configs/correlation-rules.conf)
        ↓
summary_fw index (marker="correlation_detection=*")
        ↓
Automated Response:
  ├─ score ≥ 90 → FortiGate auto-block (fortigate_auto_block.py)
  └─ score 80-89 → Slack review request
```

**Critical timing**:
- FAZ polling: Every 60 seconds
- Event processing: Every 5 seconds (batch of up to 100 events)
- Correlation rules: Every 5-15 minutes (scheduled searches)
- WebSocket broadcast: Immediately after batch processing

---

## 🔧 Critical Implementation Constraints

### 1. ES Modules `.js` Extension Requirement

**All imports MUST include `.js` extension** or they will fail at runtime:

```javascript
// ✅ CORRECT (backend/server.js)
import FortiAnalyzerDirectConnector from '../domains/integration/fortianalyzer-direct-connector.js';
import SecurityEventProcessor from '../domains/security/security-event-processor.js';

// ❌ WRONG - will crash at runtime
import FortiAnalyzerDirectConnector from '../domains/integration/fortianalyzer-direct-connector';

// ✅ CORRECT (React components - Vite resolves)
import { useStore } from '../store/store';  // No extension needed in React
import Layout from '../components/Layout/Layout.jsx';  // .jsx optional but recommended
```

**Why this matters**: `package.json` has `"type": "module"`, which enforces ES modules. Node.js requires explicit `.js` extensions for relative imports. Forgetting this is the #1 cause of "Cannot find module" errors.

### 2. Port Conflicts Between Modes

**Port assignments**:
- React Backend API: 3001 (configurable via `API_PORT` env var)
- React Frontend: 3000 (Vite default, configured in `frontend/vite.config.js`)
- Legacy Backend: 3000 (configurable via `PORT` env var)

**If running React + Legacy simultaneously**:
```bash
# Change legacy to different port
PORT=3002 npm run start:legacy

# OR change React frontend port
# Edit frontend/vite.config.js:
server: { port: 3005 }
```

**Vite proxy configuration**: Frontend proxies `/api` and `/ws` to backend port 3001. If you change backend port, update `frontend/vite.config.js`:
```javascript
server: {
  proxy: {
    '/api': 'http://localhost:3001',  // Update if backend port changes
    '/ws': { target: 'ws://localhost:3001', ws: true }
  }
}
```

### 3. Dashboard XML Entity Encoding (Frequent Error)

**Splunk dashboard XML requires HTML entity encoding**:

| Character | Encoded | Context |
|-----------|---------|---------|
| `&` | `&amp;` | Always (most common error) |
| `<` | `&lt;` | In text/values/SPL queries |
| `>` | `&gt;` | In text/values |
| `"` | `&quot;` | In attribute values |

**Common mistake**:
```xml
<!-- ❌ WRONG - XML parsing error: "not well-formed (invalid token)" -->
<choice value="REVIEW_AND_BLOCK">Review & Block</choice>
| where abuse_score >= 50 AND abuse_score < 70
"Low (<50)":"#32CD32"

<!-- ✅ CORRECT -->
<choice value="REVIEW_AND_BLOCK">Review &amp; Block</choice>
| where abuse_score >= 50 AND abuse_score &lt; 70
"Low (&lt;50)":"#32CD32"
```

**Validation before deployment**:
```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('configs/dashboards/correlation-analysis.xml'); print('✅ Valid')"
```

### 4. Correlation Rules Threshold Tuning

**Location**: `configs/correlation-rules.conf`

**Score calculation formula** (Rule 1: Multi-Factor Threat Score):
```ini
# Components
abuse_component = abuse_score * 0.4        # 40% weight
geo_component = geo_risk * 0.2             # 20% weight
login_failures = 30 (if pattern match)     # Fixed 30 points
frequency_component = case(                 # Max 30 points
  event_count > 100, 30,
  event_count > 50, 20,
  event_count > 10, 10,
  1=1, 0)
correlation_score = sum(components)        # Total: 0-100

# Action thresholds
correlation_score >= 90  → AUTO_BLOCK           # FortiGate blocking
correlation_score >= 80  → REVIEW_AND_BLOCK     # Slack review request
correlation_score >= 75  → MONITOR              # Log only
```

**Tuning workflow**:
1. Start conservative (higher thresholds): `>= 90` for AUTO_BLOCK
2. Monitor false positives for 2 weeks: `index=summary_fw marker="correlation_detection=*"`
3. Adjust component weights if needed (e.g., increase geo_component from 0.2 to 0.3)
4. Gradually lower thresholds as confidence increases
5. Use whitelist (`fortigate_whitelist.csv`) for known false positives

### 5. Cloudflare Workers Inline Classes

**`src/worker.js` cannot use ES module imports** due to Workers bundler limitations. When modifying domain classes:

```javascript
// ❌ DOES NOT WORK in src/worker.js
import SecurityEventProcessor from './domains/security/security-event-processor.js';

// ✅ REQUIRED PATTERN - inline class definition
class SecurityEventProcessor {
  constructor() { /* ... */ }
  async processEvent(event) { /* ... */ }
}

// Use directly in worker
export default {
  async scheduled(event, env, ctx) {
    const processor = new SecurityEventProcessor();
    // ...
  }
}
```

**Maintenance burden**: When you add a method to `domains/security/security-event-processor.js`, you must manually copy it to the inline class in `src/worker.js`. This is the trade-off for serverless deployment.

---

## 🎨 Common Development Tasks

### Adding New API Endpoint (React Dashboard)

```bash
# 1. Add route in backend/api/router.js
const routes = {
  'GET /api/myendpoint': () => this.getMyData(req, res, url),
  // ...
};

# 2. Implement handler method
async getMyData(req, res, url) {
  const params = url.searchParams;
  const data = await this.services.faz.getSomething();

  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ success: true, data }));
}

# 3. Add API client method (frontend/src/services/api.js)
export const api = {
  getMyData: (params) =>
    fetch(`/api/myendpoint?${new URLSearchParams(params)}`)
      .then(r => r.json()),
  // ...
};

# 4. Add Zustand action (frontend/src/store/store.js)
fetchMyData: async (params) => {
  const data = await api.getMyData(params);
  set({ myData: data });
},

# 5. Use in component
import { useStore } from '../store/store';

function MyComponent() {
  const { myData, fetchMyData } = useStore();

  useEffect(() => {
    fetchMyData({ param: 'value' });
  }, [fetchMyData]);

  return <div>{myData?.value}</div>;
}
```

### Adding New Correlation Rule

```bash
# 1. Edit correlation-rules.conf
vim configs/correlation-rules.conf

# 2. Add new [Correlation_YOUR_RULE_NAME] section
[Correlation_Custom_Attack_Pattern]
description = Detect custom attack pattern based on <your criteria>
search = | tstats count WHERE datamodel=Fortinet_Security.Security_Events \
    <your SPL query> \
| eval correlation_score = <scoring logic> \
| where correlation_score >= 75 \
| collect index=summary_fw marker="correlation_detection=custom_pattern"

cron_schedule = */10 * * * *
enableSched = 1
dispatch.earliest_time = -15m
dispatch.latest_time = now

alert.track = 1
alert.condition = search correlation_score >= 90
action.script = 1
action.script.filename = fortigate_auto_block.py

# 3. Test manually before enabling schedule
splunk search "| savedsearch Correlation_Custom_Attack_Pattern"

# 4. Verify results in summary index
index=summary_fw marker="correlation_detection=custom_pattern" | stats count

# 5. Monitor execution
index=_internal source=*scheduler.log savedsearch_name="Correlation_Custom_Attack_Pattern" \
| stats avg(run_time) as avg_runtime_sec
```

### Debugging Correlation Rules Not Running

```bash
# 1. Check saved search exists
splunk btool savedsearches list --debug | grep "Correlation_"

# 2. Verify cron schedule syntax
grep -A 5 "Correlation_Multi_Factor_Threat_Score" configs/correlation-rules.conf | grep cron_schedule

# 3. Check data model acceleration status
index=_internal source=*summarization.log savedsearch_name="Fortinet_*" \
| stats count, latest(_time) as last_run by savedsearch_name

# 4. Verify source data exists
| tstats count WHERE datamodel=Fortinet_Security.Security_Events earliest=-1h

# 5. Check for search errors
index=_internal source=*scheduler.log savedsearch_name="Correlation_*" status=failure \
| table _time savedsearch_name status message

# 6. Run correlation manually to see errors
splunk search "| savedsearch Correlation_Multi_Factor_Threat_Score" -maxout 0

# 7. Check summary index for results
index=summary_fw marker="correlation_detection=*" earliest=-24h \
| stats count by marker, correlation_rule
```

### Troubleshooting WebSocket Connection Issues

```bash
# 1. Check backend WebSocket server running
curl http://localhost:3001/health | jq '.components.websocket'

# 2. Test WebSocket handshake
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:3001/

# Expected response:
# HTTP/1.1 101 Switching Protocols
# Upgrade: websocket
# Connection: Upgrade
# Sec-WebSocket-Accept: <hash>

# 3. Check frontend WebSocket connection status
# Open browser console on http://localhost:3000
# Should see: "WebSocket connected" or "WebSocket disconnected"

# 4. Verify Vite proxy configuration
cat frontend/vite.config.js | grep -A 5 proxy
# Should have: '/ws': { target: 'ws://localhost:3001', ws: true }
```

---

## 🚨 Critical Gotchas

### 1. Forgetting to Update `src/worker.js` After Domain Changes

**Symptom**: Changes to `SecurityEventProcessor` work in React/Legacy modes but not in Cloudflare Workers.

**Cause**: Workers cannot import from `domains/`, requires inline class definitions.

**Solution**: After editing `domains/security/security-event-processor.js`, manually copy changes to `src/worker.js` inline class (starts around line 100).

### 2. Slack Notifications Not Received Despite No Errors

**Common causes**:
1. Bot not invited to channel: `/invite @your-bot` in Slack
2. Missing OAuth scopes: `chat:write`, `channels:read`, `chat:write.public`
3. Wrong channel name: Must be `#channel-name` format in config
4. Splunk plugin not configured: Check `/opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf`

**Verify bot token**:
```bash
curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer SLACK_BOT_TOKEN_PLACEHOLDER"
# Expected: {"ok":true,"user":"bot-name",...}
```

### 3. React Frontend Shows Stale Data Despite Backend Updates

**Cause**: Frontend caching + WebSocket not broadcasting updates.

**Debug checklist**:
```bash
# 1. Verify WebSocket broadcasting in backend
# backend/server.js lines 180-190 should call:
this.wsServer.broadcast({ type: 'events', data: events });

# 2. Check frontend WebSocket hook listening
# frontend/src/hooks/useWebSocket.js should handle:
case 'events': message.data.forEach(evt => addRealtimeEvent(evt));

# 3. Verify Zustand action updates state
# frontend/src/store/store.js:
addRealtimeEvent: (event) => set((state) => ({
  events: [event, ...state.events].slice(0, 100)
}));

# 4. Hard refresh browser (Ctrl+Shift+R) to clear cache
```

### 4. Correlation Rules Timeout or Run Slowly

**Symptom**: `index=_internal source=*scheduler.log` shows `run_time > 60 seconds`.

**Solutions**:
```spl
# 1. Use tstats instead of raw search (10x faster)
# ❌ SLOW
index=fw earliest=-1h | stats count by src_ip

# ✅ FAST
| tstats count WHERE datamodel=Fortinet_Security.Security_Events earliest=-1h BY Security_Events.src_ip

# 2. Verify data model acceleration enabled
| rest /services/admin/summarization by_tstats=true
| search summary.id=*Fortinet_Security*
| table summary.id, summary.complete

# 3. Reduce search time window
# Change: earliest=-24h → earliest=-1h

# 4. Add more specific filters early in search
| tstats WHERE datamodel=... Security_Events.severity IN ("critical","high")  # Filter early
```

### 5. FortiGate Auto-Block Script Not Executing

**Check execution logs**:
```bash
# 1. Verify script permissions
ls -la scripts/fortigate_auto_block.py
# Should be: -rwxr-xr-x

# 2. Check Splunk alert action logs
tail -f /opt/splunk/var/log/splunk/splunkd.log | grep fortigate_auto_block

# 3. Test script manually with mock data
echo '{"src_ip":"192.168.1.100","correlation_score":95}' | \
  python3 scripts/fortigate_auto_block.py

# 4. Verify whitelist not blocking execution
cat /opt/splunk/etc/apps/fortigate/lookups/fortigate_whitelist.csv

# 5. Check FortiGate API credentials
grep "FORTIGATE_" .env
```

---

## 📚 Key Documentation

**Essential Guides**:
- `docs/REACT_DASHBOARD_GUIDE.md` - React 18 + WebSocket implementation
- `docs/SIMPLE_SETUP_GUIDE.md` - 2-minute Syslog setup
- `docs/CLOUDFLARE_DEPLOYMENT.md` - Serverless deployment
- `docs/HEC_INTEGRATION_GUIDE.md` - HTTP Event Collector reference
- `configs/dashboards/README-slack-control.md` - Slack alert ON/OFF control

**Production Dashboards**:
- `correlation-analysis.xml` - 6 correlation rules + auto-response
- `fortigate-operations.xml` - Firewall operations monitoring
- `slack-control.xml` - Slack alert ON/OFF control via REST API

**Key Configuration**:
- `configs/correlation-rules.conf` - 6 correlation rules (440 lines)
- `configs/savedsearches-fortigate-production-alerts.conf` - Real-time alerts (5 alerts)
- `configs/fortigate-syslog.conf` - Current active config (index=fw)

---

**Version**: 2.0.1
**Last Updated**: 2025-10-24
**Architecture**: Triple-mode (React + Legacy + Workers)
**Dependencies**: Backend: 0 (Node.js built-ins only) | Frontend: 318 packages (dev only)
**Repository**: https://github.com/qws941/splunk.git
