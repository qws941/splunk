# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Project Overview

**FortiAnalyzer → Splunk Integration with Advanced Correlation Engine**

A security event processing system with three deployment modes and zero runtime dependencies (backend only). Features a React 18 dashboard with real-time WebSocket streaming, 6 advanced correlation rules, and automated threat response.

**Key Facts**:
- **Version**: 2.0.0 (React Dashboard + Legacy Backend + Cloudflare Workers)
- **Runtime Dependencies**: 0 (backend uses Node.js built-ins only)
- **Frontend**: React 18, Vite, Zustand, Recharts (~318 packages, dev only)
- **Architecture**: Triple-entry (React Dashboard, Legacy, Workers)
- **Phase**: 4.1 (Advanced Correlation Engine + React Dashboard)
- **Data Flow**: FortiAnalyzer Syslog → Splunk (index=fw) → Correlation Engine → Auto-Block/Slack
- **Repository**: https://github.com/qws941/splunk.git
- **Development Period**: 2025-10-21 to 2025-10-23 (30 commits in 3 days)

### 📊 Project Statistics
- **Total Dashboard Files**: 14 (10 XML Legacy + 4 JSON Studio)
- **Production Dashboards**: 2 XML (`correlation-analysis.xml`, `fortigate-operations.xml`)
- **Configuration Files**: 15 (~4,600 lines)
- **Correlation Rules**: 7 (6 active + 1 master view)
- **Primary Index**: `index=fw` (Syslog data, 104 references)
- **Summary Index**: `index=summary_fw` (Correlation results, 18 references)

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
curl http://localhost:3000/metrics       # Metrics
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

## 📁 File Organization & Classification

### Dashboard Files (14 total)

#### 🖥️ Production XML Dashboards (Classic, Splunk 6.x+)
| File | Lines | Purpose |
|------|-------|---------|
| `correlation-analysis.xml` | 729 | **PRIMARY** - 6 correlation rules + auto-response |
| `fortigate-operations.xml` | 269 | **PRIMARY** - Firewall operations monitoring |
| `slack-alert-control.xml` | 218 | Slack notification ON/OFF control panel |

#### 🎨 Dashboard Studio JSON (Modern, Splunk 9.0+)
| File | Lines | Purpose |
|------|-------|---------|
| `fortinet-management-dashboard.json` | 991 | Comprehensive device management |
| `correlation-analysis-studio.json` | 732 | Studio version of correlation dashboard |
| `slack-toggle-control.json` | 318 | Slack control panel (Studio) |

**Note**: XML dashboards have broader compatibility (Splunk 6.x+), JSON dashboards offer better UI/UX but require Splunk 9.0+

#### 🗂️ Backup/Archive Dashboards
- `fortigate-unified.xml` (434 lines) - Experimental unified dashboard
- `fortigate.xml` (397 lines) - Older security dashboard version
- `fortigate-operations-integrated.xml` (445 lines) - Operations + Slack combined
- `fortinet-management-slack-control.xml` (175 lines) - Legacy device management
- `slack-toggle.json` (187 lines) - Korean version, use `slack-toggle-control.json` instead

#### 🧪 Test Dashboards
- `fortigate-operations-test.xml` (263 lines)
- `slack-test-simple.xml` (114 lines)
- `slack-test.xml` (109 lines)

**Recommendation**: Move test files to `configs/dashboards/test/` subdirectory

### Configuration Files by Category

#### 📡 Data Ingestion (3 files)
| File | Lines | Current Status |
|------|-------|----------------|
| `fortigate-syslog.conf` | 437 | ✅ **ACTIVE** - Current approach (index=fw) |
| `fortigate-hec-setup.conf` | 338 | 🗂️ Alternative: FortiGate → HEC direct |
| `fortianalyzer-hec-direct.conf` | 389 | 🗂️ Alternative: FortiAnalyzer → HEC |

**Current Setup** (as of commit 0a0ee15): Using Syslog → Splunk → `index=fw`

#### 🔄 Data Processing (3 files)
- `props.conf` (117 lines) - Field extraction rules
- `transforms.conf` (87 lines) - Field transformations
- `inputs.conf` (78 lines) - Input configurations

#### 🔗 Analytics & Correlation (4 files)
- `correlation-rules.conf` (440 lines) - **7 correlation rules**
- `datamodels.conf` (196 lines) - Fortinet_Security data model
- `savedsearches-acceleration.conf` (374 lines) - Search acceleration
- `collections.conf` (10 lines) - KV Store for dashboard state

#### 🔔 Alerting (5 files)
- `alert_actions.conf` (169 lines) - Slack alert action config
- `savedsearches-alerts.conf` (174 lines) - General alert definitions
- `savedsearches-alerts-fortios7.conf` (264 lines) - FortiOS 7.x optimized
- `savedsearches-auto-block.conf` (199 lines) - Automated blocking
- `savedsearches-slack-toggle.conf` (43 lines) - Slack toggle controls
- `alert-actions/slack-alert-formatting.conf` - Advanced Slack formatting

### Index Usage Analysis

```
index=fw                  → 104+ references (PRIMARY - Syslog data)
index=summary_fw          →  18 references (Correlation results)
index=_internal           →  16 references (Splunk monitoring)
index=slack_toggle_log    →   6 references (Slack state tracking)
```

**✅ Migration Complete**: All configuration files now use `index=fw`. Legacy HEC config files (`fortianalyzer-hec-direct.conf`, `fortigate-hec-setup.conf`) marked as reference-only with legacy notices.

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

**State Synchronization Pattern** (not obvious from individual files):

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
    │ fetchAlerts()   │      │                  │
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

// Usage example
const result = await makeRequest({
  hostname: 'api.example.com',
  port: 443,
  path: '/v1/events',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  }
}, { event_type: 'security' });
```

**DO NOT introduce**: `axios`, `node-fetch`, `got`, or any HTTP library. This pattern must be followed for all new API integrations.

### Circuit Breaker Integration Pattern

**How Circuit Breaker protects API calls** (spans multiple files):

```javascript
// domains/defense/circuit-breaker.js
class CircuitBreaker {
  constructor({ failureThreshold: 5, resetTimeout: 60000 });
  states: CLOSED → OPEN (on 5 failures) → HALF_OPEN (after 60s) → CLOSED
}

// domains/integration/fortianalyzer-direct-connector.js
async getSecurityEvents() {
  return await breaker.call(
    () => this.fazAPICall('POST', '/api/v2/monitor/...'),  // Protected call
    () => ({ events: [], fallback: true })                 // Fallback on OPEN
  );
}

// backend/server.js (event polling)
setInterval(async () => {
  const events = await faz.getSecurityEvents();  // Circuit-protected
  if (!events.fallback) {
    // Process real events
  } else {
    // Circuit is OPEN, using cached data
  }
}, 60000);
```

**Key insight**: When FAZ fails 5 times consecutively, circuit opens for 60 seconds. During this time, `getSecurityEvents()` returns `{ events: [], fallback: true }` without making HTTP calls. This prevents cascading failures.

### Event Processing Queue Pattern

**How events flow from FAZ to Splunk/Slack** (cross-file architecture):

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
Splunk HEC (index=fw or fortigate_security)
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
- FAZ polling: Every 60 seconds (lightweight)
- Event processing: Every 5 seconds (batch of up to 100 events)
- Correlation rules: Every 5-15 minutes (scheduled searches)
- WebSocket broadcast: Immediately after batch processing

### WebSocket Implementation (Zero Dependencies)

**RFC 6455 compliant WebSocket server** using only Node.js `crypto` module:

```javascript
// backend/websocket/websocket-server.js
class WebSocketServer {
  // Frame encoding/decoding (RFC 6455)
  encodeFrame(data): Buffer          // Text frame with FIN=1, opcode=1
  decodeFrame(buffer): { data, type } // Parse opcode, payload length, mask

  // Connection lifecycle
  handleUpgrade(req, socket) {
    // 1. Validate Sec-WebSocket-Key header
    // 2. Compute Sec-WebSocket-Accept (SHA-1 + base64)
    // 3. Send HTTP 101 Switching Protocols
    // 4. Register socket in this.clients Set
  }

  // Heartbeat (prevent connection timeout)
  startHeartbeat() {
    setInterval(() => {
      this.clients.forEach(client => {
        client.send({ type: 'ping' });
      });
    }, 30000);  // 30 seconds
  }

  // Channel-based broadcasting
  broadcast({ type, data }) {
    const frame = this.encodeFrame(JSON.stringify({ type, data }));
    this.clients.forEach(client => client.socket.write(frame));
  }
}
```

**Client-side auto-reconnect** (frontend/src/hooks/useWebSocket.js):
```javascript
ws.onclose = () => {
  setTimeout(() => connect(), 5000);  // Reconnect after 5 seconds
};
```

**Message routing**:
1. Backend broadcasts: `{ type: 'events', data: [...] }`
2. Frontend receives → `useWebSocket.js` parses message
3. Zustand action called: `addRealtimeEvent(event)` or `updateRealtimeStats(stats)`
4. React components re-render automatically (Zustand subscriptions)

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
# Components (lines 38-47)
abuse_component = abuse_score * 0.4        # 40% weight
geo_component = geo_risk * 0.2             # 20% weight
login_failures = 30 (if pattern match)     # Fixed 30 points
frequency_component = case(                 # Max 30 points
  event_count > 100, 30,
  event_count > 50, 20,
  event_count > 10, 10,
  1=1, 0)
correlation_score = sum(components)        # Total: 0-100

# Action thresholds (lines 48-57)
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

**Rule 3: Weak Signal Combination** - modify indicator thresholds:
```ini
# 5 indicators (lines 141-186)
has_low_abuse = if(abuse_score > 0 AND abuse_score < 50, 1, 0)      # Currently 40-60
has_failed_login = if(match(msg, "(?i)(failed.*login...)"), 1, 0)
has_port_scan = if(match(msg, "(?i)(port.*scan...)"), 1, 0)
has_multiple_targets = if(unique_dst_count > 5, 1, 0)               # Currently 5+ targets
has_high_frequency = if(event_count > 20, 1, 0)                     # Currently 20+ events

# Tune these values based on your environment's baseline
```

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
vim backend/api/router.js

# Add to routes object:
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
vim frontend/src/services/api.js

export const api = {
  getMyData: (params) =>
    fetch(`/api/myendpoint?${new URLSearchParams(params)}`)
      .then(r => r.json()),
  // ...
};

# 4. Add Zustand action (frontend/src/store/store.js)
vim frontend/src/store/store.js

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

### Adding Dashboard Panel

```bash
# 1. Backup current dashboard (git handles versioning)
git diff configs/dashboards/correlation-analysis.xml

# 2. Edit dashboard XML
vim configs/dashboards/correlation-analysis.xml

# 3. Add new <row> and <panel> (after line ~600)
<row>
  <panel>
    <title>Your Panel Title</title>
    <table>
      <search>
        <query>
index=fw earliest=-24h
| stats count by src_ip, dst_ip
| sort -count
| head 10
        </query>
        <earliest>-24h@h</earliest>
        <latest>now</latest>
      </search>
      <!-- Remember HTML entity encoding: & → &amp;, < → &lt; -->
    </table>
  </panel>
</row>

# 4. Validate XML syntax
python3 -c "import xml.etree.ElementTree as ET; ET.parse('configs/dashboards/correlation-analysis.xml'); print('✅ Valid')"

# 5. Deploy to Splunk
node scripts/deploy-dashboards.js

# 6. Commit changes
git add configs/dashboards/correlation-analysis.xml
git commit -m "feat: Add panel for <description>"
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

# 4. Inspect WebSocket frames (Chrome DevTools)
# Network tab → WS tab → Click connection → Messages tab

# 5. Check for CORS issues (backend should allow all origins)
# backend/server.js line ~70:
# res.setHeader('Access-Control-Allow-Origin', '*');

# 6. Verify Vite proxy configuration
cat frontend/vite.config.js | grep -A 5 proxy
# Should have: '/ws': { target: 'ws://localhost:3001', ws: true }
```

---

## 📊 Splunk Query Patterns

### Using Data Model (Fast - Recommended)

```spl
# tstats is 10x faster than raw search
| tstats count, values(Security_Events.severity) as severities
  WHERE datamodel=Fortinet_Security.Security_Events
    Security_Events.risk_score > 70
  BY Security_Events.src_ip _time span=1h
```

### Summary Index Pattern (Fastest)

```spl
# Pre-aggregated data from scheduled searches
index=summary_fw marker="correlation_detection=*" earliest=-24h
| stats count as detections,
    avg(correlation_score) as avg_score,
    max(correlation_score) as max_score
  by src_ip, correlation_rule
| where max_score >= 80
```

### Correlation Score Debugging

```spl
# Trace how correlation score is calculated
index=fw earliest=-1h
| lookup abuseipdb_lookup.csv ip AS src_ip OUTPUT abuse_score, country
| eval abuse_component = coalesce(abuse_score, 0) * 0.4
| eval geo_risk = case(
    country IN ("CN","RU","KP","IR"), 50,
    country IN ("VN","BR","IN"), 30,
    1=1, 20)
| eval geo_component = geo_risk * 0.2
| eval correlation_score = abuse_component + geo_component
| table src_ip, abuse_score, abuse_component, country, geo_risk, geo_component, correlation_score
| sort -correlation_score
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

## 📚 Additional Resources

**Core Guides** (11 essential docs):
- **React Dashboard**: `docs/REACT_DASHBOARD_GUIDE.md` - React 18 + WebSocket implementation
- **Quick Setup**: `docs/SIMPLE_SETUP_GUIDE.md` - 2-minute Syslog setup (recommended)
- **Cloudflare Workers**: `docs/CLOUDFLARE_DEPLOYMENT.md` - Serverless deployment guide
- **HEC Integration**: `docs/HEC_INTEGRATION_GUIDE.md` - HTTP Event Collector reference
- **Threat Intel**: `docs/THREAT_INTELLIGENCE_INTEGRATION_GUIDE.md` - AbuseIPDB/VirusTotal
- **Dashboard Deployment**: `docs/SPLUNK_DASHBOARD_DEPLOYMENT.md` - Dashboard deployment methods
- **Dashboard Organization**: `configs/dashboards/README.md` - Dashboard reference guide

**Slack Integration** (4 docs):
- `docs/DASHBOARD_SLACK_INTEGRATION_GUIDE.md` - Integration overview
- `docs/SLACK_ADVANCED_ALERT_DEPLOYMENT.md` - Advanced alerting
- `docs/SLACK_ALERT_FORMATTING_GUIDE.md` - Message formatting
- `docs/SLACK_PLUGIN_SETUP_GUIDE.md` - Plugin configuration

**Archived**: 31 documents moved to `archive-20251024/docs-cleanup/` (Phase reports, validation reports, redundant guides)

## 🔍 Validation & Quality Assurance

### Automated Checks
```bash
# Validate all XML dashboards
for file in configs/dashboards/*.xml; do
  python3 -c "import xml.etree.ElementTree as ET; ET.parse('$file'); print('✅ $(basename $file)')" || echo "❌ $(basename $file)"
done

# Validate all JSON dashboards
for file in configs/dashboards/*.json; do
  jq empty "$file" 2>&1 && echo "✅ $(basename $file)" || echo "❌ $(basename $file)"
done

# Check index consistency
grep -rh "index=" configs/ | grep -oE 'index=[a-z_]+' | sort | uniq -c | sort -rn
```

### Quality Standards
- **XML Dashboards**: 10/10 ✅ Valid (as of 2025-10-24)
- **JSON Dashboards**: 4/4 ✅ Valid (as of 2025-10-24)
- **Configuration Files**: 15/15 ✅ Well-formed
- **Index Consistency**: 104 refs to `index=fw` (primary), 7 refs to legacy index

### Known Issues & Recommendations
1. **Medium Priority**: 7 files reference legacy `index=fortigate_security` - consider migration
2. **Low Priority**: Test dashboards should be moved to `configs/dashboards/test/` subdirectory
3. **Low Priority**: `slack-toggle.json` has Korean labels - use English `slack-toggle-control.json`

---

**Version**: 2.0.0
**Last Updated**: 2025-10-24
**Architecture**: Triple-mode (React + Legacy + Workers)
**Dependencies**: Backend: 0 (Node.js built-ins only) | Frontend: 318 packages (dev only)
**Repository**: https://github.com/qws941/splunk.git
**Latest Commit**: 0a0ee15 (2025-10-23)
