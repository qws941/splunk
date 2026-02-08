# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-08
**Commit:** be5e4e5
**Branch:** master

## OVERVIEW

Splunk Security Alert System for FortiGate monitoring. Hybrid monorepo: Splunk app (Python), Node.js DDD integration, React frontend, 80+ deployment scripts. Dual-server architecture (legacy `index.js` vs modern `backend/server.js`). Slack interactive callbacks (Ack/Snooze) via custom REST handler.

## STRUCTURE

```
splunk/
├── security_alert/      # Core Splunk app (tarball deployment)
│   ├── bin/             # Python alert handlers (8 scripts)
│   ├── default/         # Configs (15 alerts, macros, transforms)
│   └── lookups/         # CSV state trackers (13 files)
├── domains/             # DDD integration layer (Node.js)
│   ├── defense/         # Circuit breaker, retry logic
│   ├── integration/     # FAZ, Splunk, Slack connectors
│   └── security/        # Event processor
├── scripts/             # Deployment & validation (80+ files)
├── backend/             # Express server (FAZ→Splunk HEC)
├── frontend/            # React dashboard (Vite)
├── tests/               # E2E test suite (pytest, 13 test files)
├── splunk.wiki/         # Documentation (XWiki submodule)
└── configs/             # Docker, dashboards, provisioning
```

## ENTRY POINTS

| System | Entry | Purpose |
|--------|-------|---------|
| Splunk App | `security_alert/bin/slack_blockkit_alert.py` | Alert→Slack notifications |
| Integration | `backend/server.js` | FAZ API→Splunk HEC bridge |
| Legacy | `index.js` | Deprecated monolithic entry |
| Frontend | `frontend/src/main.jsx` | React dashboard |
| Scripts | `scripts/deploy-*.sh` | Deployment automation |
| Tests | `pytest tests/e2e -v` | E2E test suite |

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new alert | `security_alert/default/savedsearches.conf` | Follow 0XX_ naming |
| Add LogID mapping | `security_alert/default/macros.conf` | `[logids_*]` stanzas |
| Modify Slack format | `security_alert/bin/slack_blockkit_alert.py` | Block Kit structure |
| Add Slack callback | `security_alert/bin/slack_callback.py` | Ack/Snooze buttons |
| Send test alert | `security_alert/bin/send_test_alert.py` | CLI test tool |
| Add FAZ connector | `domains/integration/` | Follow DDD pattern |
| Deploy to Synology | `scripts/deploy-secmon-only.sh` | Uses Docker context |
| Validate configs | `scripts/check-stanza.py` | Run before deploy |

## CONVENTIONS

| Item | Convention |
|------|------------|
| Python formatting | Black 88 cols (strict) |
| Python linting | Flake8 120 cols (relaxed) |
| Line endings | LF only (`.gitattributes`) |
| Alert naming | `0XX_Alert_Name` (3-digit prefix) |
| Cron format | 5-field: `* * * * *` (no seconds) |
| State tracking | EMS pattern: join→eval→outputlookup |
| Docker context | `docker context use synology` first |

## ANTI-PATTERNS

| NEVER | Why |
|-------|-----|
| `print()` in bin/*.py | Breaks Splunk alert protocol |
| Tokens in `default/` | Must use `local/` (gitignored) |
| Modify `bin/lib/`, `vendor/`, `extras/addons/` | Third-party dependencies |
| `docker compose` without context | Must use `synology` context |
| Archive `domains/` | Active DDD modules |
| Direct rsync to OPS | Use release tarball, manual transfer |
| CRLF line endings | LF only enforced |

## MUST DO

| Requirement | Reason |
|-------------|--------|
| UID 41812 for Splunk container | Splunk user inside container |
| Preserve symlinks in tarball | `tar -czf` not `tar -czhf` |
| Run `check-stanza.py` before deploy | Catches config errors locally |
| Test on Synology before production | Air-gapped OPS server |
| Run pre-commit hooks | Black, Flake8, trailing whitespace |

## DEPLOYMENT

**Pattern:** Rocky Linux (dev) → tarball → Synology NAS (Docker)

```bash
./scripts/check-stanza.py                        # Validate configs
tar -czf security_alert.tar.gz security_alert/   # Package
docker context use synology && docker compose up -d --build  # Deploy
```

**Env:** `SPLUNK_HOST=192.168.50.215`, `SPLUNK_PORT=1111`, `DOCKER_CONTEXT=synology`

## TESTING

```bash
./scripts/check-stanza.py                    # Config syntax (local)
pytest tests/e2e -v -m "not splunk_live"     # E2E tests (local)
pre-commit run --all-files                   # Hooks
```

## DATA FLOW

```
FortiGate Syslog → Splunk index=fw
                        ↓
              Saved Search (15 alerts)
                        ↓
              EMS State Tracking (CSV join)
                        ↓
              State Changed? → slack_blockkit_alert.py
                        ↓
              Slack #security-firewall-alert
                        ↓
              Ack/Snooze buttons → slack_callback.py
                        ↓
              Update alert_state.csv
```

## CI/CD

**GitHub Actions** (.github/workflows/):
- `ci.yml`: validate-syntax, security scans (Semgrep, detect-secrets), unit tests
- `deploy.yml`: wiki deploy, dev/prod deploy, changelog generation

**Triggers:** push/PR to master/main/develop, version tags (v*)

## KNOWN ISSUES

| Issue | Status | Notes |
|-------|--------|-------|
| Dual entry points | Tech debt | Use `backend/server.js`, not `index.js` |
| Missing barrel exports | Tech debt | domains/, backend/ lack index.js |
| print() in validators | Violation | 4 bin/*.py files use print() |
| Flat scripts/ | Organization | 80+ scripts need categorization |

## SUBDIRECTORY AGENTS

- `security_alert/AGENTS.md` - Splunk app internals
- `scripts/AGENTS.md` - Deployment and validation scripts
- `domains/AGENTS.md` - DDD integration layer
- `frontend/AGENTS.md` - React dashboard (Vite)
- `backend/AGENTS.md` - Zero-dep API server (Node.js)
- `tests/AGENTS.md` - E2E test suite (pytest)
- `splunk.wiki/docs/AGENTS.md` - Documentation system (XWiki format)
