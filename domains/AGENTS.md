# DOMAINS KNOWLEDGE BASE

**Scope:** DDD integration layer (Node.js)

## OVERVIEW

Domain-Driven Design modules connecting FortiAnalyzer → Splunk HEC → Slack. Circuit breaker pattern for fault tolerance. ES modules with async I/O.

## STRUCTURE

```
domains/
├── defense/             # Resilience patterns
│   └── circuit-breaker.js
├── integration/         # External connectors
│   ├── fortianalyzer-direct-connector.js  (530 LOC) ★
│   ├── splunk-api.js                       (12KB)
│   ├── splunk-dashboards.js                (744 LOC)
│   ├── splunk-queries.js                   (503 LOC)
│   └── slack-*.js
└── security/            # Event processing
    └── security-event-processor.js         (485 LOC)
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add FAZ connector | `integration/fortianalyzer-*.js` |
| Add Splunk integration | `integration/splunk-*.js` |
| Add Slack notification | `integration/slack-*.js` |
| Handle failures | `defense/circuit-breaker.js` |

## CIRCUIT BREAKER

```javascript
// All external calls MUST use circuit breaker
const breaker = new CircuitBreaker({
  failureThreshold: 5,
  successThreshold: 2,
  timeout: 60000  // 60 seconds
});

await breaker.execute(() => externalCall());
```

## CONVENTIONS

| Rule | Convention |
|------|------------|
| Module format | ES modules (`import/export`) |
| Error handling | `try/catch` + circuit breaker |
| Logging | Structured JSON |
| Config | Environment variables only |
| I/O | Async only (never blocking) |

## ANTI-PATTERNS

| NEVER | Why |
|-------|-----|
| Archive `domains/` | Active DDD modules, not legacy |
| Skip circuit breaker | External calls can cascade failure |
| Hardcode credentials | Use `process.env.*` |
| Sync I/O | Blocks event loop |

## COMPLEXITY SCORES

| Module | Score | Notes |
|--------|-------|-------|
| `security-event-processor.js` | 65 | HIGH |
| `fortianalyzer-connector.js` | 51 | MEDIUM-HIGH |
| `splunk-api.js` | 45 | MEDIUM |

## MISSING (TECH DEBT)

- No `index.js` barrel export
- No TypeScript types
- No unit tests for connectors
