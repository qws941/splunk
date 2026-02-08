# BACKEND KNOWLEDGE BASE

**Scope:** Zero-dependency HTTP/WebSocket API server (Node.js)

## OVERVIEW

Pure Node.js API server bridging FortiAnalyzer data to React frontend. No npm dependencies—uses only Node.js built-ins (`http`, `url`, `fs`). Imports connectors from `domains/integration/`.

## STRUCTURE

```
backend/
├── server.js              # DashboardAPIServer class (284 LOC)
├── api/
│   └── router.js          # REST route handlers (363 LOC)
└── websocket/
    └── websocket-server.js # Real-time data feeds (285 LOC)
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add API endpoint | `api/router.js` |
| Add real-time feed | `websocket/websocket-server.js` |
| Change server config | `server.js` (port, CORS) |

## CONVENTIONS

| Rule | Convention |
|------|------------|
| Dependencies | Zero npm deps (Node.js built-ins only) |
| Module format | ES modules (`import/export`) |
| Default port | 3001 |
| Error handling | Try/catch + structured JSON response |
| External calls | Via `domains/defense/circuit-breaker.js` |

## ANTI-PATTERNS

| NEVER | Why |
|-------|-----|
| Add npm dependencies | Zero-dep architecture by design |
| Use CommonJS (`require`) | ES modules throughout |
| Skip circuit breaker | External calls go through `domains/defense/` |
| Hardcode credentials | Use `process.env.*` |

## MISSING (TECH DEBT)

- No `index.js` barrel export
- No TypeScript types
- No unit tests
