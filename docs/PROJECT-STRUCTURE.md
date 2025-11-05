# Project Structure

**Last Updated**: 2025-11-05
**Cleanup Version**: Post-cleanup standard structure

---

## Directory Overview

```
/home/jclee/app/splunk/
├── archived/                   # ❌ Archived legacy folders (deletion scheduled 2025-12-31)
│   ├── dashboards/            # Legacy dashboard files
│   ├── test-data/             # Old test data
│   ├── test-queries/          # Legacy query examples
│   └── README.md              # Archive documentation
│
├── backend/                    # ✅ Backend API services
│   ├── api/                   # API endpoints
│   ├── websocket/             # WebSocket handlers
│   └── server.js              # Express server (8KB)
│
├── configs/                    # ✅ Configuration files
│   ├── dashboards/            # Dashboard configurations
│   ├── fortigate/             # FortiGate specific configs
│   └── splunk/                # Splunk configurations
│
├── docs/                       # ✅ Documentation (centralized)
│   ├── DEMO-ENVIRONMENT.md    # Demo environment setup
│   ├── DEPLOYMENT-STRUCTURE.md # Deployment architecture
│   ├── PROJECT-STRUCTURE.md   # This file
│   ├── TRAEFIK-INTEGRATION-SUMMARY.md
│   └── TRAEFIK-TROUBLESHOOTING.md
│
├── domains/                    # ✅ Domain-driven design (ACTIVE - required by index.js)
│   ├── defense/               # Defense domain logic
│   ├── integration/           # Integration connectors
│   │   ├── fortianalyzer-direct-connector.js
│   │   ├── slack-connector.js
│   │   └── splunk-api-connector.js
│   └── security/              # Security event processing
│       └── security-event-processor.js
│
├── lookups/                    # ✅ Splunk CSV lookup files
│   ├── fortigate_logid_notification_map.csv
│   └── [other CSV lookups]
│
├── plugins/                    # ✅ Splunk add-ons (.tgz packages)
│   └── [.tgz files]
│
├── release/                    # ✅ Release packages
│   └── security_alert.tar.gz  # Deployment tarball
│
├── scripts/                    # ✅ Automation scripts
│   ├── check-stanza.py        # Configuration validator
│   ├── deploy-*.sh            # Deployment scripts
│   └── [other utility scripts]
│
├── security_alert/             # ✅ PRIMARY - Splunk app (active development)
│   ├── bin/                   # Python backend scripts
│   ├── default/               # Default configuration
│   ├── lookups/               # CSV state trackers
│   ├── local/                 # User overrides (gitignored)
│   └── metadata/              # Permission settings
│
├── security_alert_user/        # ✅ User-customizable variant (no Python backend)
│   ├── default/
│   └── metadata/
│
├── src/                        # ✅ Source code
│   └── worker.js              # Worker threads (14KB)
│
├── docker-compose.yml          # ✅ Main deployment (with Traefik integration)
├── docker-compose-demo.yml     # ✅ Demo environment
├── Dockerfile                  # ✅ Container build
├── index.js                    # ✅ Main entry point (imports from domains/)
├── package.json                # ✅ Node.js dependencies
├── CLAUDE.md                   # ✅ AI development guide
├── INSTALLATION_GUIDE.md       # ✅ Installation instructions
└── README.md                   # ✅ Project overview
```

---

## Key Directories Explained

### Active Development Directories

**`security_alert/`** - Primary Splunk app
- Modify this directory for alert updates
- Contains Python backend (slack.py, auto_validator.py, etc.)
- 15 pre-configured alerts with EMS state tracking
- Deploy as tarball: `security_alert.tar.gz`

**`domains/`** - Domain-driven design (ACTIVE)
- **CRITICAL**: Required by index.js (main entry point)
- Contains connectors: FortiAnalyzer, Splunk HEC, Slack
- Contains SecurityEventProcessor
- **DO NOT ARCHIVE**: Application will fail without this

**`backend/`** - API services
- Express server (port 8080)
- API endpoints
- WebSocket handlers

**`docs/`** - Centralized documentation
- All project documentation in one place
- Deployment guides, troubleshooting, architecture

**`scripts/`** - Automation and utilities
- Deployment scripts: `deploy-*.sh`
- Validation: `check-stanza.py`
- Configuration helpers

---

### Reference/Deployment Directories

**`configs/`** - Configuration templates
- Dashboard examples
- FortiGate specific settings
- Splunk configuration references

**`lookups/`** - Splunk CSV files
- LogID mappings
- Threat intelligence data

**`plugins/`** - Splunk add-ons
- Pre-packaged .tgz files

**`release/`** - Distribution packages
- `security_alert.tar.gz` for production deployment

---

### Archived/Legacy Directories

**`archived/`** - Deprecated folders (scheduled deletion 2025-12-31)
- `dashboards/` - Superseded by configs/dashboards/
- `test-data/` - Old test data
- `test-queries/` - Legacy examples
- See `archived/README.md` for restoration instructions

---

## File Hierarchy Decision Tree

**When creating/modifying files:**

```
New file needed?
├─ Documentation? → docs/
├─ Splunk alert? → security_alert/default/
├─ Python script? → security_alert/bin/
├─ Connector/integration? → domains/integration/
├─ API endpoint? → backend/api/
├─ Configuration template? → configs/
├─ Deployment script? → scripts/
└─ CSV lookup? → lookups/
```

**When reading/referencing:**

```
Need example config? → configs/
Need deployment guide? → docs/
Need Splunk app source? → security_alert/
Need connector code? → domains/integration/
Need deployment package? → release/security_alert.tar.gz
```

---

## Root Directory Files

**Essential Configuration**:
- `docker-compose.yml` - Main deployment with Traefik integration
- `docker-compose-demo.yml` - Demo environment
- `Dockerfile` - Container build definition
- `.env` - Environment variables (gitignored)
- `.env.example` - Environment template
- `.gitignore` - Git ignore rules

**Entry Points**:
- `index.js` - Node.js main entry (imports from domains/)
- `package.json` - Node.js dependencies and scripts

**Documentation**:
- `CLAUDE.md` - AI development guide (hybrid pattern, NFS structure)
- `README.md` - Project overview
- `INSTALLATION_GUIDE.md` - Installation instructions

---

## Import Paths Used in Code

**index.js imports** (lines 8-11):
```javascript
import FortiAnalyzerDirectConnector from './domains/integration/fortianalyzer-direct-connector.js';
import SplunkHECConnector from './domains/integration/splunk-api-connector.js';
import SlackConnector from './domains/integration/slack-connector.js';
import SecurityEventProcessor from './domains/security/security-event-processor.js';
```

**Critical**: `domains/` folder must NOT be moved or archived - application will fail.

---

## Deployment Package Structure

**security_alert.tar.gz** (26KB, 38 files):
```
security_alert/
├── bin/
│   ├── slack_blockkit_alert.py (283 lines)
│   ├── auto_validator.py (390 lines)
│   ├── deployment_health_check.py (533 lines)
│   ├── splunk_feature_checker.py
│   └── fortigate_auto_response.py
├── default/
│   ├── savedsearches.conf (15 alerts)
│   ├── macros.conf (centralized params)
│   ├── transforms.conf (13 lookups)
│   ├── alert_actions.conf (Slack config)
│   ├── app.conf (metadata v2.0.4)
│   ├── props.conf (field extraction)
│   └── setup.xml (Setup UI)
├── lookups/
│   ├── *_state_tracker.csv (10 files)
│   └── fortigate_logid_notification_map.csv
└── metadata/
    └── default.meta (permissions)
```

---

## NFS Data Persistence (Synology)

**Mount Points** (defined in docker-compose.yml):
- `/volume1/splunk/data/var` → `/opt/splunk/var` (Splunk indexes, logs)
- `/volume1/splunk/data/etc` → `/opt/splunk/etc` (configuration)

**Permissions**: UID 41812 (Splunk container user)

**See**: CLAUDE.md "Data Directory Structure (NFS Bind Mounts)" for detailed NFS documentation.

---

## Cleanup History

**2025-11-05 Cleanup**:
- ✅ Removed temporary files: 123.log, 123.csv, docker-compose.yml.backup
- ✅ Moved documentation to docs/: 4 files
- ✅ Archived legacy folders: dashboards/, test-data/, test-queries/
- ✅ Restored domains/ (required by index.js)
- ✅ Created PROJECT-STRUCTURE.md

**Files Deleted**: 3 temporary files
**Files Moved**: 4 to docs/
**Folders Archived**: 3 (dashboards, test-data, test-queries)
**Folders Restored**: 1 (domains - critical dependency)

---

## Maintenance

**Regular Tasks**:
1. Update `security_alert/` for alert modifications
2. Rebuild tarball: `tar -czf security_alert.tar.gz security_alert/`
3. Validate: `./scripts/check-stanza.py`
4. Deploy to Splunk server

**Archive Cleanup**:
- Scheduled deletion: 2025-12-31
- Review archived/ folder before deletion
- Ensure no dependencies exist

**Structure Validation**:
```bash
# Verify critical folders exist
ls -la domains/ backend/ security_alert/ docs/

# Check no broken imports
grep -r "archived/" index.js
# Should return no results

# Verify deployment package
tar -tzf release/security_alert.tar.gz | wc -l
# Should be ~38 files
```

---

**Maintained by**: NextTrade Security Team
**Questions**: See CLAUDE.md or docs/TRAEFIK-TROUBLESHOOTING.md
