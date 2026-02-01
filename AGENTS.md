# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-01  
**Commit:** 0f9bb46  
**Branch:** master

## OVERVIEW

Splunk Security Alert System for FortiGate monitoring. Hybrid monorepo: Splunk app (Python), Node.js integration services, React frontend, deployment scripts.

## STRUCTURE

```
splunk/
├── security_alert/      # Core Splunk app (tarball deployment)
│   ├── bin/             # Python alert handlers (5 scripts)
│   ├── default/         # Configs (15 alerts, macros, transforms)
│   └── lookups/         # CSV state trackers (13 files)
├── domains/             # DDD integration layer (Node.js)
│   ├── defense/         # Circuit breaker, retry logic
│   ├── integration/     # FAZ, Splunk, Slack connectors
│   └── security/        # Event processor
├── scripts/             # Deployment & validation (80+ files)
├── backend/             # Express server (FAZ→Splunk HEC)
├── frontend/            # React dashboard (Vite)
└── splunk.wiki/         # Documentation (XWiki format)
```

## ENTRY POINTS

| System | Entry | Purpose |
|--------|-------|---------|
| Splunk App | `security_alert/bin/slack_blockkit_alert.py` | Alert→Slack notifications |
| Integration | `backend/server.js` | FAZ API→Splunk HEC bridge |
| Frontend | `frontend/src/main.jsx` | React dashboard |
| Scripts | `scripts/deploy-*.sh` | Deployment automation |

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new alert | `security_alert/default/savedsearches.conf` | Follow 0XX_ naming |
| Add LogID mapping | `security_alert/default/macros.conf` | `[logids_*]` stanzas |
| Modify Slack format | `security_alert/bin/slack_blockkit_alert.py` | Block Kit structure |
| Add FAZ connector | `domains/integration/` | Follow existing pattern |
| Deploy to Synology | `scripts/deploy-secmon-only.sh` | Uses Docker context |

## CONVENTIONS

| Item | Convention |
|------|------------|
| Python | Black 88 cols, Flake8 120 cols |
| Line endings | LF only (`.gitattributes`) |
| Alert naming | `0XX_Alert_Name` (3-digit prefix) |
| Cron format | 5-field: `* * * * *` (no seconds) |
| State tracking | EMS pattern: join→eval→outputlookup |

## ANTI-PATTERNS

| NEVER | Why |
|-------|-----|
| `print()` in Python | Breaks Splunk alert protocol |
| Tokens in `default/` | Must use `local/` (gitignored) |
| Modify `bin/lib/`, `vendor/` | Third-party dependencies |
| `docker compose` without context | Must use `synology` context |
| Archive `domains/` | Active DDD modules |

## MUST DO

| Requirement | Reason |
|-------------|--------|
| UID 41812 for Splunk container | Splunk user inside container |
| Preserve symlinks in tarball | `tar -czf` not `tar -czhf` |
| Run `check-stanza.py` before deploy | Catches config errors locally |
| Test on Synology before production | Air-gapped OPS server |

## DEPLOYMENT

**Hybrid Pattern:** Source on Rocky Linux, execution on Synology NAS.

```bash
# Development (Rocky Linux)
cd /home/jclee/dev/splunk
vim security_alert/default/savedsearches.conf
./scripts/check-stanza.py          # Local validation

# Package
tar -czf security_alert.tar.gz security_alert/

# Deploy (Synology Docker)
docker context use synology
docker compose up -d --build
```

## TESTING

```bash
# Local validation (no Splunk required)
./scripts/check-stanza.py                    # Config syntax
python3 -m py_compile security_alert/bin/*.py  # Python syntax

# On Splunk server
/opt/splunk/etc/apps/security_alert/bin/auto_validator.py
/opt/splunk/etc/apps/security_alert/bin/deployment_health_check.py
```

## CRITICAL FILES

| File | Purpose | LOC |
|------|---------|-----|
| `savedsearches.conf` | 15 alert definitions | ~400 |
| `macros.conf` | Centralized SPL params | ~120 |
| `slack_blockkit_alert.py` | Slack Block Kit formatter | 283 |
| `deployment_health_check.py` | 10-point health check | 533 |
| `auto_validator.py` | Config integrity validator | 390 |

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
```

## SUBDIRECTORY AGENTS

- `scripts/AGENTS.md` - Deployment and validation scripts
- `security_alert/AGENTS.md` - Splunk app internals
- `domains/AGENTS.md` - DDD integration layer
