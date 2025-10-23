# FortiAnalyzer-Splunk React Dashboard

**Modern Security Monitoring Dashboard with Real-time Event Streaming**

<div align="center">

[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?logo=node.js)](https://nodejs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.1-646CFF?logo=vite)](https://vitejs.dev/)
[![License](https://img.shields.io/badge/License-Private-red)]()

</div>

---

## ✨ Features

### 🎯 Core Capabilities

- **Real-time Event Streaming** - WebSocket-based live updates
- **Modular Component Architecture** - Reusable React components
- **Zero Runtime Dependencies** - Backend uses only Node.js built-ins
- **Advanced Correlation Engine** - 6 correlation rules for threat detection
- **Automated Response** - Auto-blocking with FortiGate API integration
- **Slack Integration** - Real-time alert notifications

### 📊 Dashboard Modules

| Module | Description | Status |
|--------|-------------|--------|
| **Dashboard** | Overview with live stats & charts | ✅ Ready |
| **Security** | Security event monitoring | ✅ Ready |
| **Correlation** | Advanced pattern detection | ✅ Ready |
| **Alerts** | Alert management & acknowledgment | ✅ Ready |
| **Threats** | Threat intelligence & geo-analysis | ✅ Ready |
| **System** | Health monitoring & metrics | ✅ Ready |

---

## 🚀 Quick Start

### Prerequisites

```bash
Node.js 18+ | npm 8+ | Modern browser with WebSocket support
```

### Installation & Run

```bash
# 1. Install backend dependencies
npm install

# 2. Install frontend dependencies
cd frontend && npm install && cd ..

# 3. Configure environment
cp .env.example .env
nano .env  # Configure FAZ, Splunk, Slack credentials

# 4. Start backend API (Terminal 1)
npm start  # → http://localhost:3001

# 5. Start React frontend (Terminal 2)
cd frontend && npm run dev  # → http://localhost:3000
```

**Access**: Open http://localhost:3000 in your browser

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         React Frontend (Vite)               │
│  Dashboard | Security | Correlation | ...   │
│              ↓ Zustand Store ↓              │
└─────────────┬───────────────┬───────────────┘
              │               │
         REST API         WebSocket
              │               │
┌─────────────┴───────────────┴───────────────┐
│         Backend API Server (Node.js)         │
│  ┌────────────┐  ┌──────────────────────┐  │
│  │ API Router │  │ WebSocket Server     │   │
│  └────────────┘  └──────────────────────┘   │
│                                               │
│  ┌──────────────────────────────────────┐   │
│  │ Service Layer (Zero Dependencies)    │   │
│  │ • FortiAnalyzer Connector             │   │
│  │ • Splunk HEC Connector                │   │
│  │ • Slack Connector                     │   │
│  │ • Security Event Processor            │   │
│  │ • Circuit Breaker                     │   │
│  └──────────────────────────────────────┘   │
└───────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
splunk/
├── backend/                    # 🔧 Node.js API Server
│   ├── api/router.js           # REST endpoints
│   ├── websocket/              # WebSocket server
│   └── server.js               # Main entry point
│
├── frontend/                   # ⚛️ React Dashboard
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── Layout/         # App layout & nav
│   │   │   ├── Cards/          # Metric cards
│   │   │   ├── Charts/         # Data visualization
│   │   │   └── Tables/         # Data tables
│   │   ├── pages/              # Dashboard pages
│   │   │   ├── Dashboard.jsx
│   │   │   ├── SecurityOverview.jsx
│   │   │   ├── CorrelationAnalysis.jsx
│   │   │   └── ...
│   │   ├── hooks/              # Custom React hooks
│   │   │   └── useWebSocket.js
│   │   ├── services/           # API clients
│   │   │   └── api.js
│   │   ├── store/              # Zustand state
│   │   │   └── store.js
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── domains/                    # 🎯 Business Logic (DDD)
│   ├── integration/            # External connectors
│   ├── security/               # Security processing
│   └── defense/                # Resilience patterns
│
├── configs/                    # ⚙️ Splunk Configurations
│   ├── correlation-rules.conf  # 6 correlation rules
│   ├── datamodels.conf         # Data models
│   └── savedsearches-*.conf    # Saved searches
│
├── scripts/                    # 🛠️ Utility Scripts
│   ├── fortigate_auto_block.py # Auto-blocking
│   ├── fetch_*_intel.py        # Threat intelligence
│   └── cleanup-legacy.sh       # Migration helper
│
├── docs/                       # 📚 Documentation
│   └── REACT_DASHBOARD_GUIDE.md # This guide
│
├── package.json                # Backend dependencies
└── README-REACT.md             # This file
```

---

## 🔌 API Reference

### Backend REST API

**Base URL**: `http://localhost:3001/api`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/events` | GET | Get security events |
| `/stats` | GET | System statistics |
| `/correlation` | GET | Correlation analysis |
| `/alerts` | GET | Active alerts |
| `/alerts/acknowledge` | POST | Acknowledge alert |
| `/threats` | GET | Threat intelligence |
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |

**Example**:
```bash
curl http://localhost:3001/api/stats
curl http://localhost:3001/api/events?limit=50&timeRange=-1h
```

### WebSocket API

**URL**: `ws://localhost:3001/ws`

**Subscribe to channels**:
```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['events', 'stats', 'alerts']
}));
```

**Receive real-time events**:
```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  // { type: 'events', data: [...], timestamp: '...' }
};
```

---

## 🎨 Component Library

### StatsCard

Display metric with trend indicator

```jsx
import StatsCard from './components/Cards/StatsCard';

<StatsCard
  title="Total Events"
  value={1234}
  trend="+12%"
  trendUp={true}
  icon="📊"
  variant="default"
/>
```

### EventsChart

Time-series chart with Recharts

```jsx
import EventsChart from './components/Charts/EventsChart';

<EventsChart events={events} />
```

### AlertsTable

Alert display with severity badges

```jsx
import AlertsTable from './components/Tables/AlertsTable';

<AlertsTable alerts={alerts} />
```

---

## 🔄 State Management

**Zustand Store** - Lightweight state management

```javascript
import { useStore } from './store/store';

function MyComponent() {
  const {
    stats,
    events,
    alerts,
    fetchStats,
    fetchEvents,
    fetchAlerts
  } = useStore();

  useEffect(() => {
    fetchStats();
    fetchEvents({ limit: 50 });
    fetchAlerts();
  }, []);

  return <div>{stats?.processor?.processedCount}</div>;
}
```

**Store Actions**:
- `fetchStats()` - Get system statistics
- `fetchEvents(params)` - Get security events
- `fetchAlerts()` - Get active alerts
- `fetchCorrelation(timeRange)` - Get correlation analysis
- `fetchThreats()` - Get threat intelligence
- `acknowledgeAlert(id, by, comment)` - Acknowledge alert

---

## 🚀 Deployment

### Development

```bash
# Terminal 1: Backend
npm start

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Production

```bash
# Build frontend
cd frontend && npm run build

# Start backend
npm start

# TODO: Serve static files from backend
```

### Docker (Coming Soon)

```bash
docker-compose up -d
```

---

## 🔧 Configuration

### Environment Variables

**Required** (`.env`):
```bash
# FortiAnalyzer
FAZ_HOST=your-faz.example.com
FAZ_USERNAME=admin
FAZ_PASSWORD=your_password

# Splunk HEC
SPLUNK_HEC_HOST=your-splunk.example.com
SPLUNK_HEC_PORT=8088
SPLUNK_HEC_TOKEN=your_hec_token
SPLUNK_INDEX_FORTIGATE=fw

# Slack (Optional)
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL=splunk-alerts
SLACK_ENABLED=true

# API Server
API_PORT=3001
```

### Backend Configuration

**File**: `backend/server.js`
- API port: 3001 (default)
- WebSocket endpoint: `/ws`
- Event polling interval: 60 seconds

### Frontend Configuration

**File**: `frontend/vite.config.js`
- Dev server port: 3000
- API proxy: `http://localhost:3001/api`
- WebSocket proxy: `ws://localhost:3001/ws`

---

## 🧹 Migration from Legacy

### What Changed?

**Version 1.x (Legacy)**:
- XML dashboards in Splunk
- Manual dashboard deployment
- No real-time updates
- Scattered scripts

**Version 2.0 (React)**:
- Modern React dashboard
- Real-time WebSocket streaming
- Modular component architecture
- Integrated API backend

### Legacy Files

Archived to: `/home/jclee/app/splunk/archive-YYYYMMDD/`

**Archived**:
- XML dashboards (`configs/dashboards/*.xml`)
- Legacy scripts (`deploy-dashboards.js`, etc.)
- Enhanced duplicates (`*-enhanced.*`)

**To restore**: `cp -r archive-YYYYMMDD/* .`

---

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:3001/health
```

### Prometheus Metrics

```bash
curl http://localhost:3001/metrics
```

**Metrics**:
- `dashboard_api_uptime_seconds`
- `dashboard_api_requests_total`
- `dashboard_api_errors_total`
- `dashboard_ws_connections`
- `dashboard_processed_events_total`

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check environment variables
cat .env

# Check port availability
lsof -i :3001
```

### Frontend can't connect

```bash
# Check backend is running
curl http://localhost:3001/health

# Check Vite proxy config
cat frontend/vite.config.js
```

### WebSocket connection failed

```bash
# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://localhost:3001/ws
```

### Build fails

```bash
# Clean and reinstall
rm -rf frontend/node_modules
cd frontend && npm install
npm run build
```

---

## 📚 Documentation

- **Quick Start**: `docs/REACT_DASHBOARD_GUIDE.md`
- **Legacy Migration**: Run `scripts/cleanup-legacy.sh`
- **Component Examples**: Check `frontend/src/components/`
- **API Reference**: See Backend REST API section above

---

## 🛠️ Development

### Adding New Page

```bash
# 1. Create page component
cat > frontend/src/pages/MyPage.jsx << 'EOF'
function MyPage() {
  return <div>My Page</div>;
}
export default MyPage;
EOF

# 2. Add route in App.jsx
<Route path="/mypage" element={<MyPage />} />

# 3. Add navigation in Layout.jsx
{ path: '/mypage', label: 'My Page', icon: '🎯' }
```

### Adding New API Endpoint

```javascript
// backend/api/router.js
async myEndpoint(req, res) {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ success: true }));
}

// Add to routes object
'GET /api/myendpoint': () => this.myEndpoint(req, res)
```

---

## 📈 Performance

- **Backend**: Zero runtime dependencies, minimal overhead
- **Frontend**: Vite + React 18 (Fast Refresh, HMR)
- **WebSocket**: Efficient binary protocol, automatic reconnection
- **API**: HTTP/1.1 with connection pooling

---

## 🔒 Security

- **Environment Variables**: Sensitive data in `.env` (gitignored)
- **CORS**: Configured for same-origin policy
- **WebSocket**: Origin validation
- **API**: Input validation on all endpoints

---

## 📝 License

**Private** - Internal Use Only

---

## 👤 Author

**jclee**

---

## 🎯 Roadmap

- [ ] Docker Compose deployment
- [ ] Static file serving from backend
- [ ] User authentication
- [ ] Advanced filtering & search
- [ ] Export to PDF/CSV
- [ ] Mobile responsive design improvements
- [ ] More chart types (Pie, Bar, Heatmap)
- [ ] Alert rule customization UI

---

**Status**: ✅ Production Ready
**Version**: 2.0.0
**Last Updated**: 2025-10-23
**Migration**: Legacy XML dashboards replaced with React framework
