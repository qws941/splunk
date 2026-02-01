# DOMAINS KNOWLEDGE BASE

**Parent:** [../AGENTS.md](../AGENTS.md)

## OVERVIEW

DDD (Domain-Driven Design) integration layer. Node.js modules connecting FortiAnalyzer, Splunk, and Slack. Used by backend service for FAZ→Splunk HEC bridge.

## STRUCTURE

```
domains/
├── defense/              # Resilience patterns
│   └── circuit-breaker.js    # Failure isolation (1.5KB)
├── integration/          # External connectors
│   ├── fortianalyzer-direct-connector.js  # FAZ API client (530 LOC)
│   ├── splunk-api.js          # Splunk REST client (12KB)
│   ├── splunk-dashboards.js   # Dashboard management (744 LOC)
│   ├── splunk-queries.js      # SPL query builder (503 LOC)
│   └── slack-*.js             # Slack notification (2 files)
└── security/             # Event processing
    └── security-event-processor.js  # Core processor (485 LOC)
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add FAZ endpoint | `integration/fortianalyzer-direct-connector.js` | Follow existing API pattern |
| Add Splunk query | `integration/splunk-queries.js` | SPL builder methods |
| Modify circuit breaker | `defense/circuit-breaker.js` | Threshold/timeout config |
| Add event processor | `security/security-event-processor.js` | Chain of responsibility |

## HIGH-COMPLEXITY FILES

| File | LOC | Complexity | Refactor Notes |
|------|-----|------------|----------------|
| `security-event-processor.js` | 485 | 65 | Extract to chain of responsibility |
| `fortianalyzer-direct-connector.js` | 530 | 51 | Split by API category |
| `splunk-dashboards.js` | 744 | 3 | Low complexity, keep as-is |

## CIRCUIT BREAKER PATTERN

```javascript
// defense/circuit-breaker.js
const breaker = new CircuitBreaker({
  failureThreshold: 5,      // Failures before opening
  successThreshold: 2,      // Successes to close
  timeout: 60000            // Recovery timeout (ms)
});

// States: CLOSED → OPEN → HALF_OPEN → CLOSED
```

## ANTI-PATTERNS

| NEVER | Why |
|-------|-----|
| Archive/delete `domains/` | Active DDD modules in use |
| Direct API calls | Use circuit breaker wrapper |
| Hardcode credentials | Use environment variables |
| Sync file I/O in connectors | Use async/await |

## ENVIRONMENT VARIABLES

```bash
# FortiAnalyzer
FAZ_HOST=192.168.1.100
FAZ_USERNAME=admin
FAZ_PASSWORD=<from-env>

# Splunk HEC
SPLUNK_HEC_HOST=splunk.company.com
SPLUNK_HEC_TOKEN=<from-env>
SPLUNK_INDEX_FORTIGATE=fortianalyzer

# Circuit Breaker
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60000
```

## CONVENTIONS

| Item | Convention |
|------|------------|
| Exports | ES modules (`export default`) |
| Error handling | Try/catch with circuit breaker |
| Logging | Structured JSON to stdout |
| Config | Environment variables only |

## MODULE BOUNDARIES

```
backend/server.js
      ↓ imports
domains/integration/*
      ↓ wraps
domains/defense/circuit-breaker.js
      ↓ processes
domains/security/security-event-processor.js
      ↓ sends
External APIs (FAZ, Splunk HEC, Slack)
```
