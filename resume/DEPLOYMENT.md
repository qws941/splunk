# Deployment Guide

## Prerequisites

- Splunk Enterprise 9.x+ (or compatible version)
- FortiGate syslog forwarding configured
- Slack webhook URL

## Installation Steps

### 1. Download Distribution

```bash
# Get latest production release
cd /tmp
wget https://github.com/qws941/splunk/releases/download/v2.0.4/security_alert-v2.0.4-production.tar.gz
```

### 2. Install on Splunk

```bash
# Extract to apps directory
cd /opt/splunk/etc/apps/
tar -xzf /tmp/security_alert-v2.0.4-production.tar.gz

# Set ownership
chown -R splunk:splunk security_alert
```

### 3. Configure Slack Webhook

```bash
# Create local configuration
mkdir -p /opt/splunk/etc/apps/security_alert/local

cat > /opt/splunk/etc/apps/security_alert/local/alert_actions.conf <<EOF
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EOF

chown splunk:splunk /opt/splunk/etc/apps/security_alert/local/alert_actions.conf
chmod 600 /opt/splunk/etc/apps/security_alert/local/alert_actions.conf
```

### 4. Configure FortiGate Index (if not default)

```bash
# Edit macros to match your index name
cat > /opt/splunk/etc/apps/security_alert/local/macros.conf <<EOF
[fortigate_index]
definition = index=your_fortigate_index_name
iseval = 0
EOF
```

### 5. Restart Splunk

```bash
# Restart to load app
/opt/splunk/bin/splunk restart

# Verify app loaded
/opt/splunk/bin/splunk display app security_alert
```

## Post-Installation Verification

### 1. Check Alert Schedules

```spl
# Splunk Search & Reporting app
| rest /servicesNS/-/security_alert/saved/searches
| search title="*Alert*"
| table title, cron_schedule, disabled, actions
```

### 2. Test Alert Execution

```bash
# Trigger test alert manually
/opt/splunk/bin/splunk search \
  '`fortigate_index` `logids_vpn_tunnel` earliest=-1h | head 1' \
  -app security_alert
```

### 3. Verify Slack Integration

```spl
# Check alert action logs
index=_internal source=*alert_actions.log action_name="slack"
| stats count by action_status
```

### 4. Validate State Trackers

```spl
# Check state tracker files loaded
| rest /services/data/transforms/lookups
| search title="*state_tracker*"
| table title, filename
```

## Production Deployment

### Search Head Cluster

```bash
# Deploy via Cluster Master
cd /opt/splunk/etc/shcluster/apps/
tar -xzf security_alert-v2.0.4-production.tar.gz

# Push to search heads
/opt/splunk/bin/splunk apply shcluster-bundle \
  -target https://cluster-master:8089 \
  -auth admin:password
```

### Environment Variables

**None required** - all configuration is file-based.

### Resource Requirements

- **CPU**: <5% average (15 concurrent searches)
- **Memory**: ~100MB (state tracker caching)
- **Disk**: ~10MB (app + state data)
- **Network**: Minimal (Slack webhooks only)

## Upgrade Procedure

### From v2.0.x to v2.0.4

```bash
# 1. Backup current configuration
cp -r /opt/splunk/etc/apps/security_alert/local /tmp/security_alert_backup

# 2. Stop Splunk
/opt/splunk/bin/splunk stop

# 3. Remove old version
rm -rf /opt/splunk/etc/apps/security_alert

# 4. Extract new version
cd /opt/splunk/etc/apps/
tar -xzf security_alert-v2.0.4-production.tar.gz
chown -R splunk:splunk security_alert

# 5. Restore configuration
cp -r /tmp/security_alert_backup/* /opt/splunk/etc/apps/security_alert/local/

# 6. Start Splunk
/opt/splunk/bin/splunk start
```

### From v1.x (breaking changes)

**State tracker schema changed** - manual migration required:

```spl
# Export old state data
| inputlookup old_state_tracker
| table device, component, state
| outputcsv /tmp/old_states.csv

# Transform to new format
# (manual column mapping needed)

# Import to new tracker
| inputcsv /tmp/old_states.csv
| eval last_seen = now()
| outputlookup append=t new_state_tracker
```

## Rollback Procedure

```bash
# 1. Stop Splunk
/opt/splunk/bin/splunk stop

# 2. Restore previous version
cd /opt/splunk/etc/apps/
rm -rf security_alert
tar -xzf /tmp/security_alert-v2.0.3-production.tar.gz

# 3. Restore configuration
cp -r /tmp/security_alert_backup/* security_alert/local/

# 4. Start Splunk
/opt/splunk/bin/splunk start
```

## Uninstallation

```bash
# 1. Disable all alerts
cat > /opt/splunk/etc/apps/security_alert/local/savedsearches.conf <<EOF
# Disable all alerts
[002_VPN_Tunnel_Down]
enableSched = 0
# ... repeat for all 15 alerts
EOF

# 2. Wait for scheduled searches to complete
/opt/splunk/bin/splunk list search-jobs -app security_alert

# 3. Stop Splunk
/opt/splunk/bin/splunk stop

# 4. Remove app
rm -rf /opt/splunk/etc/apps/security_alert

# 5. Start Splunk
/opt/splunk/bin/splunk start
```

## Troubleshooting

### App Not Loading

```bash
# Check Splunk logs
tail -f /opt/splunk/var/log/splunk/splunkd.log | grep security_alert

# Verify file permissions
ls -la /opt/splunk/etc/apps/security_alert/
```

### Alerts Not Firing

```spl
# Check scheduler status
index=_internal source=*scheduler.log
| stats count by status, savedsearch_name
```

### Slack Not Sending

```bash
# Test webhook manually
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message from security_alert"}'
```

## Support

- **Documentation**: `/opt/splunk/etc/apps/security_alert/README/`
- **GitHub Issues**: https://github.com/qws941/splunk/issues
- **Logs**: `index=_internal source=*security_alert*`
