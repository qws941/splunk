# SCRIPTS KNOWLEDGE BASE

**Scope:** Deployment, validation, and automation scripts (80+ files, categorized)

## OVERVIEW

Bash-first automation: deploy to Synology Docker, validate Splunk configs, diagnose issues. All scripts run from Rocky Linux dev machine targeting remote Synology NAS.

## STRUCTURE

```
scripts/
├── deploy/        # 17 deployment scripts (deploy-*, Deploy-*)
├── validate/      # 15 validation & verification (check-*, ci-validate-*, validate-*, verify-*)
├── diagnose/      # 5 diagnostic & review (diagnose-*, review-*)
├── cleanup/       # 4 cleanup automation (cleanup-*, consolidate-*, run-full-cleanup)
├── test/          # 4 test & demo runners (test-*, QUICK-TEST, start-demo)
├── slack/         # 6 Slack integration (create-slack-alert, extract-slack-token, etc.)
├── intel/         # 4 threat intelligence fetching (fetch_*, fetch-*, get-*)
├── fortigate/     # 2 FortiGate/FAZ specific (faz-*, fortigate_*)
├── generate/      # 2 data & config generators (generate-*)
├── setup/         # 5 installation & setup (auto-*, install-*, setup-*)
├── util/          # 12 miscellaneous utilities (btool, splunk-*, find-*, etc.)
├── AGENTS.md
└── README.md
```

## KEY SCRIPTS

| Script | Location | Purpose | Run When |
|--------|----------|---------|----------|
| `check-stanza.py` | `validate/` | Validate Splunk configs | **Before every deploy** |
| `deploy-secmon-only.sh` | `deploy/` | Standard deployment | App updates |
| `verify-splunk-deployment.sh` | `validate/` | Post-deploy check | After deployment |
| `diagnose-splunk-issues.sh` | `diagnose/` | Troubleshooting | On errors |
| `ci-validate-security-alert.sh` | `validate/` | CI validation | GitHub Actions |

## WHERE TO LOOK

| Task | Script |
|------|--------|
| Deploy app | `deploy/deploy-secmon-only.sh` |
| Validate before deploy | `validate/check-stanza.py` |
| Check Splunk health | `diagnose/diagnose-splunk-issues.sh` |
| CI validation | `validate/ci-validate-security-alert.sh` |
| Test Slack notifications | `slack/slack_test_alert.py` |
| Fetch threat intel | `intel/fetch_abuseipdb_intel.py` |

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

| Script | Location | LOC | Issue |
|--------|----------|-----|-------|
| `verify-splunk-deployment.sh` | `validate/` | 403 | Too many responsibilities |
| `deploy-fluentd-hec.sh` | `deploy/` | 348 | Could be modularized |

## OUTPUT CONVENTIONS

```
✅ Success
⚠️  Warning
❌ Error
🔵 Info
```
