# SCRIPTS KNOWLEDGE BASE

**Scope:** Deployment and validation scripts (80+ files)

## OVERVIEW

Bash-first automation: deploy to Synology Docker, validate Splunk configs, diagnose issues. All scripts run from Rocky Linux dev machine targeting remote Synology NAS.

## STRUCTURE

```
scripts/
├── deploy-*.sh          # 15 deployment scripts
├── validate-*.sh        # 12 validation scripts
├── diagnose-*.sh        # 10 diagnostic scripts
├── check-stanza.py      # Config validation (227 LOC) ★
├── validate-configs.py  # Config integrity (213 LOC)
└── *.sh, *.py, *.js     # Utilities
```

## KEY SCRIPTS

| Script | Purpose | Run When |
|--------|---------|----------|
| `check-stanza.py` | Validate Splunk configs | **Before every deploy** |
| `deploy-secmon-only.sh` | Standard deployment | App updates |
| `verify-splunk-deployment.sh` | Post-deploy check | After deployment |
| `diagnose-splunk-issues.sh` | Troubleshooting | On errors |

## WHERE TO LOOK

| Task | Script |
|------|--------|
| Deploy app | `deploy-secmon-only.sh` |
| Validate before deploy | `check-stanza.py` |
| Check Splunk health | `diagnose-splunk-issues.sh` |
| Sync configs | `sync-splunk-configs.sh` |

## CONVENTIONS

| Rule | Example |
|------|---------|
| Shebang | `#!/usr/bin/env bash` |
| Strict mode | `set -euo pipefail` |
| SSH port | `-p 1111` (Synology) |
| Docker context | `docker context use synology` first |

## ANTI-PATTERNS

| NEVER | Why |
|-------|-----|
| `cd` without `|| return` | Script continues in wrong dir |
| Hardcode paths | Use `$SCRIPT_DIR`, `$PROJECT_ROOT` |
| Skip `check-stanza.py` | Catches errors before deploy |
| Direct rsync to OPS | OPS is air-gapped; use release tarball |
| Assume docker context | Always set context first |

## ENVIRONMENT

```bash
SPLUNK_HOST=192.168.50.215
SPLUNK_PORT=1111            # SSH port
DOCKER_CONTEXT=synology
SPLUNK_CONTAINER=splunk
```

## REFACTOR CANDIDATES

| Script | LOC | Issue |
|--------|-----|-------|
| `verify-splunk-deployment.sh` | 403 | Too many responsibilities |
| `deploy-fluentd-hec.sh` | 348 | Could be modularized |

## OUTPUT CONVENTIONS

```
✅ Success
⚠️  Warning
❌ Error
🔵 Info
```
