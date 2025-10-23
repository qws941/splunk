# React Dashboard Framework - Quick Start Guide

## 🎯 Overview

Modern React-based security monitoring dashboard for FortiAnalyzer-Splunk integration with real-time WebSocket streaming and modular component architecture.

**Version**: 2.0.0
**Technology Stack**: React 18 + Vite + Zustand + Recharts + WebSocket

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Port 3000)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Dashboard │  │Security  │  │Correlation│  │ Alerts  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│         │                │                │           │      │
│         └────────────────┴────────────────┴───────────┘     │
│                          │                                   │
│                    Zustand Store                             │
│                          │                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
               REST API      WebSocket (Real-time)
                    │             │
┌───────────────────┴─────────────┴───────────────────────────┐
│              Backend API Server (Port 3001)                  │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│  │  API Router  │  │   WebSocket   │  │  Service Layer  │  │
│  │   (REST)     │  │    Server     │  │ (FAZ, Splunk,   │  │
│  │              │  │  (Real-time)  │  │  Slack, etc.)   │  │
│  └──────────────┘  └───────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js**: 18+ (ES Modules support)
- **npm**: 8+
- **Environment Variables**: Configured in `.env`

### Installation

```bash
# Install backend dependencies (zero runtime dependencies!)
npm install

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Development Mode

```bash
# Terminal 1: Start backend API server
npm start
# → Backend API: http://localhost:3001
# → WebSocket: ws://localhost:3001

# Terminal 2: Start React frontend (with Vite)
cd frontend
npm run dev
# → Frontend: http://localhost:3000
```

### Production Build

```bash
# Build React frontend
cd frontend
npm run build
# → Output: frontend/dist/

# Start backend API server
npm start
```

---

## 📂 Project Structure

```
/home/jclee/app/splunk/
├── backend/                    # Node.js API Server
│   ├── api/
│   │   └── router.js          # REST API endpoints
│   ├── websocket/
│   │   └── websocket-server.js # Real-time streaming
│   └── server.js              # Main server entry point
│
├── frontend/                   # React Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout/        # Layout & Navigation
│   │   │   ├── Cards/         # StatsCard components
│   │   │   ├── Charts/        # Chart components (Recharts)
│   │   │   └── Tables/        # Table components
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx           # Main dashboard
│   │   │   ├── SecurityOverview.jsx    # Security monitoring
│   │   │   ├── CorrelationAnalysis.jsx # Correlation rules
│   │   │   ├── AlertManagement.jsx     # Alert management
│   │   │   ├── ThreatIntelligence.jsx  # Threat analysis
│   │   │   └── SystemHealth.jsx        # System status
│   │   ├── hooks/
│   │   │   └── useWebSocket.js # WebSocket custom hook
│   │   ├── services/
│   │   │   └── api.js          # API client
│   │   ├── store/
│   │   │   └── store.js        # Zustand state management
│   │   ├── styles/
│   │   │   └── global.css      # Global styles
│   │   ├── App.jsx             # Main React app
│   │   └── main.jsx            # React entry point
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── domains/                    # Domain logic (shared with backend)
│   ├── integration/
│   ├── security/
│   └── defense/
│
├── configs/                    # Splunk configurations
├── scripts/                    # Utility scripts
└── docs/                       # Documentation
```

---

## 🔌 API Endpoints

### REST API (Backend)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/events` | GET | Get security events |
| `/api/stats` | GET | Get system statistics |
| `/api/correlation` | GET | Get correlation analysis |
| `/api/alerts` | GET | Get active alerts |
| `/api/alerts/acknowledge` | POST | Acknowledge alert |
| `/api/threats` | GET | Get threat intelligence |
| `/api/dashboards` | GET | Get dashboard list |
| `/api/slack/test` | GET | Test Slack integration |
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |

**Example**:
```bash
# Get recent events
curl http://localhost:3001/api/events?limit=50&timeRange=-1h

# Get system stats
curl http://localhost:3001/api/stats

# Test Slack
curl http://localhost:3001/api/slack/test
```

### WebSocket (Real-time)

**Connection**: `ws://localhost:3001/ws`

**Message Types**:
```javascript
// Subscribe to channels
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['events', 'stats', 'alerts']
}));

// Incoming events
{
  type: 'events',
  data: [...],
  timestamp: '2025-10-23T10:00:00Z'
}

// Incoming stats
{
  type: 'stats',
  data: { ... },
  timestamp: '2025-10-23T10:00:00Z'
}
```

---

## 🎨 Component Modules

### 1. Layout Components

**`Layout.jsx`**: Main application layout with sidebar navigation

- Header with connection status
- Sidebar navigation
- Real-time stats display

### 2. Card Components

**`StatsCard.jsx`**: Metric display cards

Props:
- `title`: Card title
- `value`: Metric value
- `trend`: Trend percentage
- `trendUp`: Trend direction (boolean)
- `icon`: Icon emoji
- `variant`: 'default' | 'critical' | 'high' | 'warning'

### 3. Chart Components

**`EventsChart.jsx`**: Time-series event chart (Recharts)

Props:
- `events`: Array of event objects

Features:
- 5-minute time buckets
- Critical/High event highlighting
- Interactive tooltips

### 4. Table Components

**`AlertsTable.jsx`**: Alert display table

Props:
- `alerts`: Array of alert objects

Features:
- Severity color coding
- Action badges (AUTO_BLOCK, REVIEW_AND_BLOCK, MONITOR)
- Timestamp formatting

---

## 🎛️ State Management (Zustand)

**Store**: `frontend/src/store/store.js`

### State

```javascript
{
  stats: null,           // System statistics
  events: [],            // Security events
  alerts: [],            // Active alerts
  correlation: null,     // Correlation analysis
  threats: null,         // Threat intelligence
  wsConnected: false,    // WebSocket status
  loading: false,        // Loading state
  error: null            // Error message
}
```

### Actions

```javascript
fetchStats()                          // Fetch system stats
fetchEvents(params)                   // Fetch security events
fetchAlerts()                         // Fetch alerts
acknowledgeAlert(id, by, comment)     // Acknowledge alert
fetchCorrelation(timeRange)           // Fetch correlation data
fetchThreats()                        // Fetch threat intelligence
addRealtimeEvent(event)               // Add real-time event
updateRealtimeStats(stats)            // Update real-time stats
```

### Usage

```javascript
import { useStore } from '../store/store';

function MyComponent() {
  const { stats, fetchStats } = useStore();

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return <div>{stats?.processor?.processedCount}</div>;
}
```

---

## 🔄 Real-time Updates

### WebSocket Hook

**Hook**: `frontend/src/hooks/useWebSocket.js`

**Features**:
- Automatic connection/reconnection
- Heartbeat (ping/pong)
- Channel subscription
- Message handling

**Usage**:
```javascript
import { useWebSocket } from '../hooks/useWebSocket';

function App() {
  const { connect, disconnect, send } = useWebSocket();

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return <div>...</div>;
}
```

---

## 🎨 Styling

### Theme

**Dark Theme** with green accents:
- Background: `#0f0f0f`
- Cards: `#1a1a1a`
- Borders: `#333`
- Text: `#e0e0e0`
- Accent: `#4ade80` (green)
- Critical: `#ef4444` (red)
- Warning: `#f59e0b` (orange)

### Global Styles

**File**: `frontend/src/styles/global.css`

- Reset CSS
- Dark scrollbars
- System fonts

---

## 🚀 Deployment

### Option 1: Separate Deployment

```bash
# Backend
npm start                    # Port 3001

# Frontend
cd frontend
npm run build
npm run preview             # Port 3000
```

### Option 2: Integrated Deployment

```bash
# Build frontend
cd frontend
npm run build

# Serve frontend from backend (TODO: Add static file serving)
npm start
```

### Option 3: Docker (TODO)

```bash
docker-compose up -d
```

---

## 🧹 Migration from XML Dashboards

### What Changed?

**Removed**:
- ❌ XML dashboards (`configs/dashboards/*.xml`)
- ❌ Legacy dashboard scripts (`deploy-dashboards.js`, etc.)
- ❌ Enhanced duplicates (`*-enhanced.*`)

**Added**:
- ✅ React frontend (`frontend/`)
- ✅ Backend API (`backend/`)
- ✅ WebSocket real-time streaming
- ✅ Modular component architecture

### Archive

Legacy files archived to: `/home/jclee/app/splunk/archive-YYYYMMDD/`

To restore: `cp -r archive-YYYYMMDD/* .`

---

## 🔧 Development Guide

### Adding New Components

```bash
# Create component
mkdir -p frontend/src/components/MyComponent
touch frontend/src/components/MyComponent/{MyComponent.jsx,MyComponent.css}
```

### Adding New Pages

```bash
# Create page
touch frontend/src/pages/MyPage.jsx

# Add route in App.jsx
<Route path="/mypage" element={<MyPage />} />

# Add navigation in Layout.jsx
{ path: '/mypage', label: 'My Page', icon: '🎯' }
```

### Adding New API Endpoints

```javascript
// backend/api/router.js
async myNewEndpoint(req, res) {
  // Implementation
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ success: true }));
}

// Add to routes
'GET /api/myendpoint': () => this.myNewEndpoint(req, res)
```

---

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:3001/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "dashboard-api-server",
  "version": "2.0.0",
  "uptime_seconds": 3600,
  "components": {
    "fortianalyzer": { "connected": true, "status": "healthy" },
    "splunk": { "connected": true, "status": "healthy" },
    "slack": { "connected": true, "status": "healthy" },
    "websocket": { "connections": 2, "status": "healthy" }
  },
  "metrics": {
    "total_requests": 1234,
    "ws_connections": 2,
    "errors": 0,
    "processed_events": 5678
  }
}
```

### Prometheus Metrics

```bash
curl http://localhost:3001/metrics
```

---

## 🐛 Troubleshooting

### Frontend not connecting to backend

**Check**: Vite proxy configuration in `vite.config.js`

```javascript
server: {
  proxy: {
    '/api': 'http://localhost:3001',
    '/ws': {
      target: 'ws://localhost:3001',
      ws: true
    }
  }
}
```

### WebSocket connection failed

**Check**:
1. Backend server running on port 3001
2. No firewall blocking WebSocket
3. Browser console for errors

### Build errors

```bash
# Clear node_modules and reinstall
rm -rf frontend/node_modules
cd frontend
npm install
npm run build
```

---

## 📚 Additional Documentation

- **Backend API**: `docs/API_REFERENCE.md` (TODO)
- **Component Library**: `docs/COMPONENT_LIBRARY.md` (TODO)
- **Deployment**: `docs/DEPLOYMENT.md` (TODO)

---

**Migration Complete**: Legacy XML dashboards replaced with modern React framework
**Status**: Production Ready
**Last Updated**: 2025-10-23
