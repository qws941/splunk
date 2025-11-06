# Deployment Guide - Security Alert System v2.0.4

## Overview

This is a **user customization package** for an existing Splunk app, not a standalone app installation.

## Architecture

```
security_alert/
├── local/                              # User customizations (deploy these)
│   ├── alert_actions.conf              # Slack webhook configuration
│   ├── macros.conf                     # LogID groups and thresholds
│   ├── savedsearches.conf              # 16 alert definitions
│   └── transforms.conf                 # Lookup table definitions
├── bin/                                # Alert action scripts
│   ├── slack.py                        # Slack Block Kit formatter
│   ├── safe_fmt.py                     # Safe string formatting library
│   └── six.py                          # Python 2/3 compatibility
├── lookups/                            # State tracking CSVs
│   ├── fortigate_logid_notification_map.csv  # LogID reference
│   └── *_state_tracker.csv             # 11 state tracking files
└── default/                            # App defaults (reference only)
```

## Deployment Steps

### 1. Prerequisites

- Splunk Enterprise (tested on 8.x/9.x)
- Existing FortiGate data indexed in Splunk (`index=fw`)
- Slack workspace with incoming webhook configured
- Splunk Slack App installed (official add-on)

### 2. Deploy to Splunk

#### Option A: Deploy to Existing App

```bash
# Copy local/ configs to your existing Splunk app
cp -r local/* $SPLUNK_HOME/etc/apps/YOUR_APP/local/

# Copy bin/ scripts
cp -r bin/* $SPLUNK_HOME/etc/apps/YOUR_APP/bin/

# Copy lookups
cp -r lookups/* $SPLUNK_HOME/etc/apps/YOUR_APP/lookups/

# Set permissions
chown -R splunk:splunk $SPLUNK_HOME/etc/apps/YOUR_APP/
chmod +x $SPLUNK_HOME/etc/apps/YOUR_APP/bin/*.py

# Restart Splunk
$SPLUNK_HOME/bin/splunk restart
```

#### Option B: Deploy as New App

```bash
# Copy entire security_alert/ directory
cp -r security_alert $SPLUNK_HOME/etc/apps/

# Set permissions
chown -R splunk:splunk $SPLUNK_HOME/etc/apps/security_alert

# Restart Splunk
$SPLUNK_HOME/bin/splunk restart
```

### 3. Configure Slack Webhook

Edit `local/alert_actions.conf`:

```ini
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Or set environment variable:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### 4. Verify Deployment

```spl
# Check if alerts are enabled
| rest /services/saved/searches
| search title="*Alert*"
| table title, disabled, cron_schedule

# Check state trackers
| inputlookup vpn_state_tracker
| stats count

# Test Slack integration
index=_internal source=*alert_actions.log action_name="slack"
| table _time, action_status, stderr
```

## File Roles

### local/ Directory (User Customizations)

| File | Purpose | Modify? |
|------|---------|---------|
| **savedsearches.conf** | 16 alert definitions | ✅ Yes - customize thresholds, channels |
| **macros.conf** | LogID groups, thresholds | ✅ Yes - adjust LogIDs, thresholds |
| **transforms.conf** | Lookup definitions | ⚠️ Rarely - only if adding new lookups |
| **alert_actions.conf** | Slack webhook URL | ✅ Yes - set your webhook |

### bin/ Directory (Alert Actions)

| File | Purpose | Modify? |
|------|---------|---------|
| **slack.py** | Slack Block Kit formatter | ❌ No - stable |
| **safe_fmt.py** | Safe formatting library | ❌ No - dependency |
| **six.py** | Python 2/3 compatibility | ❌ No - dependency |

### lookups/ Directory (Data)

| File | Purpose | Modify? |
|------|---------|---------|
| **fortigate_logid_notification_map.csv** | LogID reference | ⚠️ Rarely - add new LogIDs |
| ***_state_tracker.csv** (11 files) | State tracking | ❌ No - managed by alerts |

## Alert Types

### Binary State Alerts (4)

- `002_VPN_Tunnel_Down/Up` - VPN tunnel state changes
- `007_Hardware_Failure/Restored` - Hardware component failures
- `012_Interface_Down/Up` - Network interface state changes
- `008_HA_State_Change` - High Availability state transitions

### Threshold-Based Alerts (6)

- `006_CPU_Memory_Anomaly` - CPU/Memory baseline deviation
- `010_Resource_Limit` - Resource exhaustion (sessions, files)
- `011_Admin_Login_Failed` - Admin login failures
- `013_SSL_VPN_Brute_Force` - VPN brute force attempts
- `015_Abnormal_Traffic_Spike` - Traffic anomalies
- `017_License_Expiry_Warning` - License expiration

### Event-Based Alerts (6)

- `001_Config_Change` - Configuration changes
- `016_System_Reboot` - System reboot/crash events
- `018_FMG_Out_Of_Sync` - FortiManager sync issues

## Customization Examples

### Change Alert Threshold

Edit `local/macros.conf`:

```ini
# Change CPU threshold from 80% to 90%
[cpu_high_threshold]
definition = 90
```

### Change Slack Channel

Edit `local/savedsearches.conf`:

```ini
[001_Config_Change]
...
action.slack.param.channel = #your-custom-channel
```

### Add New LogID

1. Edit `local/macros.conf`:
   ```ini
   [logids_new_category]
   definition = (logid=0100000001 OR logid=0100000002)
   ```

2. Edit `local/transforms.conf`:
   ```ini
   [new_state_tracker]
   filename = new_state_tracker.csv
   ```

3. Create `lookups/new_state_tracker.csv`:
   ```csv
   device,component,state,last_seen,details
   ```

4. Edit `local/savedsearches.conf` - add new alert using standard pattern

## Troubleshooting

### Alerts Not Triggering

```spl
# Check if events exist
`fortigate_index` `logids_vpn_tunnel` earliest=-1h
| stats count by logid, device

# Check scheduler
index=_internal source=*scheduler.log savedsearch_name="002_VPN_Tunnel_Down"
| stats count by status
```

### Slack Not Sending

```spl
# Check alert action logs
index=_internal source=*alert_actions.log action_name="slack"
| table _time, action_status, stderr

# Verify webhook
cat $SPLUNK_HOME/etc/apps/security_alert/local/alert_actions.conf | grep webhook_url
```

### State Tracker Issues

```spl
# Check state tracker
| inputlookup vpn_state_tracker
| table device, vpn_name, state, last_seen

# Verify CSV permissions
ls -la $SPLUNK_HOME/etc/apps/security_alert/lookups/*.csv
```

## Rollback

To remove customizations:

```bash
# Remove local/ configs
rm -rf $SPLUNK_HOME/etc/apps/YOUR_APP/local/savedsearches.conf
rm -rf $SPLUNK_HOME/etc/apps/YOUR_APP/local/macros.conf
rm -rf $SPLUNK_HOME/etc/apps/YOUR_APP/local/transforms.conf

# Restart Splunk
$SPLUNK_HOME/bin/splunk restart
```

## Version History

**v2.0.4** (2025-11-07)
- Restructured to user customization model (local/ directory)
- Removed unused lookups and bin/ scripts
- Cleaned up for deployment to existing Splunk apps
- Added FMG out-of-sync alert (018)

**v2.0.3** (2025-11-04)
- Fixed FMG sync SPL syntax (self-referencing field)
- Implemented EMS state tracking
- Integrated Slack Block Kit formatting

## Support

**Repository**: https://github.com/qws941/splunk.git
**Maintainer**: NextTrade Security Team
**Documentation**: See `CLAUDE.md` for development details
