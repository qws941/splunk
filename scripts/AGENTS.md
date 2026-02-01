# SCRIPTS KNOWLEDGE BASE

**Parent:** [../AGENTS.md](../AGENTS.md)

## OVERVIEW

80+ scripts for deployment, validation, and diagnostics. Mixed languages: Bash (primary), Python, Node.js.

## STRUCTURE

```
scripts/
├── deploy-*.sh (15)      # Deployment automation
├── validate-*.sh (12)    # Configuration validation
├── diagnose-*.sh (10)    # Troubleshooting utilities
├── check-stanza.py       # Local config validator (227 LOC)
├── validate-configs.py   # Extended config validation (213 LOC)
└── *.js                  # Node.js utilities
```

## WHERE TO LOOK

| Task | Script | Notes |
|------|--------|-------|
| Deploy to Synology | `deploy-secmon-only.sh` | Recommended for most cases |
| Deploy hybrid setup | `deploy-hybrid.sh` | FAZ + direct syslog |
| Validate configs locally | `check-stanza.py` | No Splunk required |
| Test Slack connection | `test-slack.sh` | Requires bot token |
| Diagnose container | `diagnose-docker.sh` | Synology Docker context |

## KEY SCRIPTS

### check-stanza.py (Run Before Every Deploy)

```bash
./scripts/check-stanza.py [config_file]

# Validates:
# - alert_actions.conf: [slack] stanza + 7 params
# - savedsearches.conf: 15 alerts, cron format, required fields
# - transforms.conf: 13 lookups + CSV existence

# Output indicators:
# 🟢 active alert  ⚪ inactive  📱 Slack enabled  ❌ error
```

### deploy-secmon-only.sh (Standard Deploy)

```bash
./scripts/deploy-secmon-only.sh

# Steps:
# 1. Validates configs locally
# 2. Creates tarball
# 3. Syncs to Synology via rsync
# 4. Restarts Splunk container
```

## CONVENTIONS

| Rule | Example |
|------|---------|
| Shebang | `#!/usr/bin/env bash` |
| Error handling | `set -euo pipefail` |
| Synology SSH | `ssh -p 1111 jclee@192.168.50.215` |
| Docker context | `docker context use synology` first |

## ANTI-PATTERNS

| NEVER | Why |
|-------|-----|
| `cd` without returning | Use `pushd/popd` or subshell |
| Hardcode paths | Use `$SCRIPT_DIR` relative paths |
| Skip validation | Always run `check-stanza.py` first |
| Direct rsync to OPS | Use release tarball, manual transfer |

## ENVIRONMENT VARIABLES

```bash
SPLUNK_HOST=192.168.50.215
SPLUNK_PORT=1111            # SSH port for Synology
DOCKER_CONTEXT=synology
SPLUNK_CONTAINER=splunk
```

## OUTPUT CONVENTIONS

```bash
# Emoji indicators for status
✅ Success    ❌ Error    ⚠️ Warning    🔄 In Progress
🟢 Active     ⚪ Inactive  📱 Slack enabled
```
