# Draft: Navi View (Navigation) Redesign

## Requirements (confirmed from user)

### 1. Modern Navigation UI
- Replace emoji icons with lucide-react (or similar SVG library)
- Collapsible sidebar (expanded/collapsed states)
- Nested menu support for sub-pages
- Breadcrumb navigation
- Keyboard shortcuts (Cmd+K search)

### 2. Layout Improvements
- Responsive design (mobile sidebar drawer)
- Smooth transitions/animations
- Better visual hierarchy

### 3. Enhanced Pages
- Real content for placeholder pages
- Connect to Splunk data via backend API
- Loading states, error handling

### 4. Splunk Integration
- Deep links to Splunk dashboards
- Unified navigation experience

---

## Current State Analysis

### Layout.jsx (65 LOC)
- **Icons**: Emoji icons (📊🛡️🔗🚨🎯⚙️) - unprofessional
- **Structure**: Flat navigation with 6 items
- **State**: Uses Zustand for stats/wsConnected
- **Missing**: Collapsible sidebar, nested menus, breadcrumbs

### Layout.css (139 LOC)
- **Layout**: Grid - header (70px) + sidebar (240px) + content
- **Theme**: Dark (#0f0f0f, #1a1a1a, #2a2a2a), green accent (#4ade80)
- **Missing**: Responsive design, mobile support, collapsed state

### App.jsx (53 LOC)
- React Router v6 with 6 routes
- WebSocket + 30s stats polling
- No nested routes structure

### Pages Status
| Page | LOC | Status |
|------|-----|--------|
| Dashboard.jsx | 88 | ✅ Full implementation |
| SecurityOverview.jsx | 29 | ⚠️ Minimal placeholder |
| CorrelationAnalysis.jsx | 33 | ⚠️ Basic correlation rules |
| AlertManagement.jsx | 28 | ⚠️ Just AlertsTable wrapper |
| ThreatIntelligence.jsx | 33 | ⚠️ Basic threat list |
| SystemHealth.jsx | 36 | ⚠️ Connection + stats |

### Splunk Navigation (default.xml)
- 3 collections: Security Dashboards, FortiGate Monitoring, Testing/Dev
- 9 dashboard views total
- Green theme (#65A637) - different from React green (#4ade80)

### Dependencies (package.json)
- React 18.3.1, React Router 6.22
- Zustand 4.5 (state)
- Recharts 2.12 (charts)
- **No icon library currently**

---

## Technical Decisions

### Icon Library
- **Options**: lucide-react, heroicons, react-icons
- **Recommendation**: lucide-react (lightweight, tree-shakeable, active maintenance)

### Collapsible Sidebar
- Store collapsed state in localStorage for persistence
- Collapsed width: ~64px (icons only)
- Expanded width: 240px (current)
- Smooth CSS transitions

### Nested Navigation Structure
```
📊 Dashboard (main)
🛡️ Security
  ├── Overview (SecurityOverview)
  ├── Alerts (AlertManagement)
  └── Splunk Deep Links
📈 Monitoring
  ├── FortiGate
  ├── Correlation (CorrelationAnalysis)
  └── Threats (ThreatIntelligence)
⚙️ System
  └── Health (SystemHealth)
```

### Breadcrumb Component
- Auto-generated from route hierarchy
- Clickable path segments
- Shows current location

### Command Palette (Cmd+K)
- Global keyboard shortcut
- Search across pages
- Quick navigation

### Responsive Breakpoints
- Desktop: > 1024px (normal sidebar)
- Tablet: 768-1024px (collapsed by default)
- Mobile: < 768px (drawer overlay)

---

## Decisions Made (User Confirmed)

1. **Page Content Depth**: ✅ FULL
   - New backend API endpoints required
   - Comprehensive visualizations for all pages
   - Significantly larger scope

2. **Color Theme**: ✅ Unify to React green (#4ade80)
   - Update Splunk nav XML to match
   - Brighter, more modern look

3. **Animation Preference**: ✅ "SPLUNK 호환되는거로" (Splunk-compatible)
   - Interpreted as: Enterprise-friendly, subtle transitions
   - Not flashy, professional feel
   - ~200ms transitions, no spring physics

4. **Additional Features**: ✅ New backend API endpoints
   - Will need to extend backend/server.js

## Open Questions (Remaining)

## Final Decisions (All Confirmed)

5. **Splunk Deep Links**: ✅ Environment variable
   - VITE_SPLUNK_BASE_URL config
   - Format: `{VITE_SPLUNK_BASE_URL}/app/security_alert/{view_name}`

6. **Test Strategy**: ✅ Set up tests (Vitest)
   - No test infrastructure currently exists
   - Will set up Vitest for Vite project
   - TDD for new navigation components

---

## Scope Boundaries

### IN SCOPE
- Sidebar redesign (icons, collapse, nested)
- Breadcrumb component
- Command palette (Cmd+K)
- Responsive layout
- CSS animations/transitions
- Splunk deep link integration
- Enhanced pages (loading/error states + proper content)

### OUT OF SCOPE (confirm)
- New backend API endpoints?
- Authentication/login system?
- Dark/light theme toggle?
- Internationalization?
- New chart types in Recharts?
