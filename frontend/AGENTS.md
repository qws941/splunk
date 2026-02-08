# FRONTEND KNOWLEDGE BASE

**Scope:** React dashboard for FortiAnalyzer-Splunk monitoring

## OVERVIEW

Vite-powered React 18 SPA. Zustand state, Recharts visualization, react-router-dom routing. Connects to backend/server.js via API.

## STRUCTURE

```
frontend/
├── src/
│   ├── App.jsx           # Root component + routes
│   ├── main.jsx          # Entry point
│   ├── components/       # Reusable UI components
│   ├── hooks/            # Custom React hooks
│   ├── pages/            # Route page components
│   ├── services/         # API service layer
│   ├── store/            # Zustand state stores
│   └── styles/           # CSS styles
├── package.json          # Dependencies (React 18, Zustand, Recharts)
└── vite.config.js        # Vite configuration
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add new page | `src/pages/` + update `App.jsx` routes |
| Add API call | `src/services/` |
| Add global state | `src/store/` (Zustand) |
| Add chart | Use Recharts in `src/components/` |
| Add shared component | `src/components/` |
| Add custom hook | `src/hooks/` |

## CONVENTIONS

| Rule | Convention |
|------|------------|
| State management | Zustand (not Redux/Context) |
| Charting | Recharts only |
| Routing | react-router-dom v6 |
| Module format | ES modules |
| Node version | >=18.0.0 |

## COMMANDS

```bash
npm run dev       # Dev server (Vite)
npm run build     # Production build
npm run lint      # ESLint check
npm test          # Vitest unit tests
npm run preview   # Preview production build
```

## ANTI-PATTERNS

| NEVER | Why |
|-------|-----|
| Use Redux/Context for state | Zustand is standard here |
| Import from `../../../` | Use path aliases if needed |
| Add new chart library | Recharts handles all charts |
| Skip ESLint | `--max-warnings 0` enforced |

## KEY PAGES

| Page | File | Purpose |
|------|------|---------|
| SecurityOverview | `pages/SecurityOverview.jsx` | Main dashboard view |
| SystemHealth | `pages/SystemHealth.jsx` | System metrics display |
| ThreatIntelligence | `pages/ThreatIntelligence.jsx` | Threat data visualization |
| CorrelationAnalysis | `pages/CorrelationAnalysis.jsx` | Cross-data correlation |

## TESTING

```bash
npm test                  # Vitest unit tests
```

Config: `vitest.config.js`, setup: `test/setup.js`

## DEPENDENCIES

**Runtime:** react, react-dom, react-router-dom, zustand, recharts, date-fns

**Dev:** vite, vitest, eslint, @vitejs/plugin-react
