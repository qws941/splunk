# Release Files

This directory contains official release packages for deployment to Splunk servers.

## Latest Release

**Package**: `security_alert.tar.gz` (71KB)
**Date**: 2025-11-04

## Release Notes (2025-11-04)

### Features Added
- ✅ Slack Block Kit integration with dual authentication (Bot Token OAuth + Webhook)
- ✅ HTTP/HTTPS proxy support for enterprise environments
- ✅ EMS state tracking for 15 alerts (12 active, 3 state-tracking)
- ✅ Setup UI with comprehensive configuration options

### Bug Fixes
- ✅ Fixed setup.xml structure - merged proxy settings into main Slack block
- ✅ Added alert_actions.conf.spec to resolve Splunk parameter validation errors
- ✅ Fixed Python script permissions (755)
- ✅ Removed Python cache files from git tracking

### Configuration Files
- `alert_actions.conf` - 7 custom parameters (Slack auth + proxy config)
- `setup.xml` - Unified Slack and proxy configuration UI
- `alert_actions.conf.spec` - Parameter schema definitions
- `slack_blockkit_alert.py` - Proxy-enabled Slack integration

### Deployment Instructions

```bash
# 1. Copy to Splunk server
scp security_alert.tar.gz splunk-server:/tmp/

# 2. SSH to Splunk server
ssh splunk-server
cd /opt/splunk/etc/apps/

# 3. Backup existing (if any)
sudo tar -czf security_alert.backup-$(date +%Y%m%d).tar.gz security_alert/

# 4. Extract new version
sudo rm -rf security_alert/
sudo tar -xzf /tmp/security_alert.tar.gz
sudo mv security_alert security_alert_temp
sudo mkdir security_alert
sudo mv security_alert_temp/* security_alert/
sudo rmdir security_alert_temp

# 5. Fix permissions
sudo chown -R splunk:splunk security_alert
sudo chmod 755 security_alert/bin/*.py

# 6. Restart Splunk
sudo /opt/splunk/bin/splunk restart

# 7. Verify deployment
/opt/splunk/bin/splunk btool alert_actions list slack
/opt/splunk/etc/apps/security_alert/bin/deployment_health_check.py
```

### Post-Deployment Verification

1. **Check App Status**
   ```bash
   /opt/splunk/bin/splunk display app security_alert
   # Expected: enabled=true
   ```

2. **Verify Alert Action Registration**
   ```bash
   curl -k -u admin:password \
     "https://localhost:8089/services/admin/alert_actions?output_mode=json" \
     | jq '.entry[] | select(.name == "slack")'
   ```

3. **Access Setup Page**
   - URL: `https://your-splunk:8000/en-US/manager/security_alert/apps/local/security_alert/setup`
   - Configure: Slack Bot Token or Webhook URL
   - Optional: Enable proxy configuration

4. **Test Alert**
   ```spl
   index=fw earliest=-1h | savedsearch 001_Config_Change_Alert
   ```

5. **Check Logs**
   ```bash
   tail -100 /opt/splunk/var/log/splunk/splunkd.log | grep security_alert
   index=_internal source=*alert_actions.log "slack"
   ```

## Recent Updates

- Proxy configuration support (enterprise environments)
- Setup UI improvements
- Splunk parameter validation fixes
- EMS state tracking for 15 alerts

## Package Contents

```
security_alert/
├── README/
│   └── alert_actions.conf.spec    # Parameter schema (NEW)
├── bin/                            # 5 Python scripts
│   ├── slack_blockkit_alert.py    # Slack integration (UPDATED)
│   ├── auto_validator.py
│   ├── deployment_health_check.py
│   ├── fortigate_auto_response.py
│   └── splunk_feature_checker.py
├── default/                        # Configuration files
│   ├── alert_actions.conf         # Slack action config (UPDATED)
│   ├── setup.xml                  # Setup UI (UPDATED)
│   ├── savedsearches.conf         # 15 alert definitions
│   ├── macros.conf                # Centralized parameters
│   ├── transforms.conf            # Lookup definitions
│   ├── props.conf                 # Field extraction
│   └── app.conf                   # App metadata
├── lookups/                        # 18 CSV files
│   ├── *_state_tracker.csv (10)   # EMS state tracking
│   └── fortigate_logid_*.csv      # Reference data
└── metadata/
    └── default.meta               # Permissions

Total: 54 files, 71KB compressed
```

## Support

- **Validators**: `auto_validator.py`, `deployment_health_check.py`
- **Documentation**: `/docs/` directory in repository
- **Issues**: Check `splunkd.log` and `alert_actions.log`

## SHA256 Checksum

```bash
sha256sum security_alert.tar.gz
```

---

**Maintainer**: NextTrade Security Team
**Repository**: https://github.com/qws941/splunk.git
**License**: Internal Use Only
