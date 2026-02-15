# Scripts

80+ automation scripts organized by function. See `AGENTS.md` for detailed documentation.

## Directory Structure

| Directory | Scripts | Purpose |
|-----------|---------|---------|
| `deploy/` | 17 | Deployment to Synology Docker |
| `validate/` | 15 | Config validation, CI checks, verification |
| `diagnose/` | 5 | Diagnostic & troubleshooting |
| `cleanup/` | 4 | Legacy cleanup automation |
| `test/` | 4 | Test & demo runners |
| `slack/` | 6 | Slack integration & notifications |
| `intel/` | 4 | Threat intelligence fetching |
| `fortigate/` | 2 | FortiGate/FAZ specific |
| `generate/` | 2 | Data & config generators |
| `setup/` | 5 | Installation & environment setup |
| `util/` | 12 | Miscellaneous utilities |

## Quick Start

```bash
# Validate configs (run before every deploy)
python scripts/validate/check-stanza.py

# Deploy to Synology
./scripts/deploy/deploy-secmon-only.sh

# Verify deployment
./scripts/validate/verify-splunk-deployment.sh

# Diagnose issues
./scripts/diagnose/diagnose-splunk-issues.sh
```
