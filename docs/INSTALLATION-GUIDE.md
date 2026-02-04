# 🚀 Security Alert System - Installation Guide

**Package**: `security_alert.tar.gz` (69KB, 54 files)
**Version**: 4.2.3
**Date**: 2026-02-04
**Status**: ✅ All Splunk stanza errors fixed

---

## Quick Installation

### Method 1: Splunk Web UI (Recommended)

1. **Login** to Splunk Web
2. **Navigate** to Apps → Manage Apps
3. **Click** "Install app from file"
4. **Upload** `security_alert.tar.gz`
5. **Click** "Upload"
6. **Restart** Splunk when prompted
7. **Configure** Slack credentials (see Setup below)

### Method 2: Command Line

```bash
# Copy to Splunk server
scp security_alert.tar.gz splunk-server:/tmp/

# SSH to server
ssh splunk-server

# Extract to apps directory
cd /opt/splunk/etc/apps/
sudo tar -xzf /tmp/security_alert.tar.gz

# Fix permissions
sudo chown -R splunk:splunk security_alert

# Restart Splunk
sudo /opt/splunk/bin/splunk restart
```

---

## Slack Configuration

### Setup via Web UI

1. **Navigate** to Apps → Security Alert System → Setup
2. **Enter** Slack App OAuth Token (see below for how to get)
3. **Click** Save

### Get Slack App OAuth Token

**Step 1**: Create Slack App
- Go to https://api.slack.com/apps
- Click "Create New App" → "From scratch"
- Name: "FortiGate Security Alert"
- Workspace: Select your workspace

**Step 2**: Add OAuth Scopes
- Navigate to "OAuth & Permissions"
- Add Bot Token Scopes:
  - `chat:write` - Send messages
  - `chat:write.public` - Send to public channels
  - `channels:read` - Read channel list

**Step 3**: Install App
- Click "Install to Workspace"
- Authorize the app
- Copy **Bot User OAuth Token** (starts with `xoxb-`)

**Step 4**: Paste Token
- Splunk Web → Apps → Security Alert System → Setup
- Paste token in "Slack App OAuth Token" field
- Save

**Step 5**: Invite Bot to Channel (Optional)
```
# In Slack channel #security-firewall-alert
/invite @FortiGate Security Alert
```

Note: If you have `chat:write.public` scope, invitation is optional.

---

## Validation

### 1. Verify Installation

```bash
# Check app is installed
/opt/splunk/bin/splunk display app security_alert

# Check configuration (should show NO errors)
/opt/splunk/bin/splunk btool alert_actions list slack --debug

# Expected output:
# [slack]
# description = Send formatted alert to Slack using Block Kit
# param.slack_app_oauth_token =
# param.webhook_url =
# (no "Invalid key" errors)
```

### 2. Test Slack Integration

**Manual Test**:
```spl
| makeresults
| eval device="test-firewall", logdesc="Test Alert", msg="Configuration test"
| sendalert slack param.channel="#security-firewall-alert"
```

**Check Logs**:
```spl
index=_internal source=*alert_actions.log "slack_blockkit"
| table _time, action_mode, search_name, result
```

**Expected Result**:
- ✅ Message appears in Slack channel #security-firewall-alert
- ✅ Block Kit format (header, fields, divider)
- ✅ No errors in splunkd.log

---

## What Was Fixed

### Root Cause (from 123.log)

Splunk btool validation showed ALL custom parameter names were invalid:
- `param.bot_token` → Invalid (should be `param.slack_app_oauth_token`)
- `param.channel` → Invalid (NOT supported by Splunk)
- `param.icon_emoji` → Invalid (hardcoded in Python instead)
- `param.username` → Invalid (hardcoded in Python instead)

### Files Modified

**1. alert_actions.conf**
- Changed `param.bot_token` → `param.slack_app_oauth_token`
- Removed `param.channel` (not supported)
- Only: `param.slack_app_oauth_token` and `param.webhook_url`

**2. slack_blockkit_alert.py**
- Reads `slack_app_oauth_token` (official name)
- Fallback to `bot_token` for compatibility
- Channel hardcoded to `#security-firewall-alert`

**3. setup.xml**
- Changed "Bot Token" → "Slack App OAuth Token"
- Removed channel, username, icon_emoji fields
- Only shows OAuth token and Webhook URL inputs

**4. savedsearches.conf** (previous fix)
- Removed 30 unused parameter lines (15 alerts × 2 params)

---

## Troubleshooting

### Alerts Not Triggering

**Check Data**:
```spl
index=fw earliest=-1h | stats count
# Should return count > 0
```

**Check Alert Status**:
```bash
/opt/splunk/bin/splunk btool savedsearches list | grep enableSched
```

**Run Alert Manually**:
```spl
index=fw earliest=rt-10m latest=rt logid=0100044546
| head 10
```

### Slack Messages Not Received

**Test Token**:
```bash
curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer SLACK_BOT_TOKEN_PLACEHOLDER"

# Expected: {"ok":true,"user":"bot-name"}
```

**Check Logs**:
```bash
tail -100 /opt/splunk/var/log/splunk/splunkd.log | grep -i slack
```

**Common Issues**:
- Bot not invited to #security-firewall-alert channel
- Missing OAuth scopes: chat:write, chat:write.public
- Token expired or revoked
- Firewall blocking api.slack.com

---

## Next Steps

1. ✅ **Installation Complete**
2. ⚠️ **Configure Slack** (follow Setup via Web UI above)
3. ⚠️ **Test Integration** (send manual test alert)
4. ⚠️ **Monitor Alerts** (check real FortiGate events)

---

**Documentation**:
- ROOT-CAUSE-FOUND.md - Technical details
- STANZA-FIX-COMPLETE.md - Parameter cleanup
- INSTALLATION-GUIDE.md - This file

**Support**: Run validators after deployment
```bash
/opt/splunk/etc/apps/security_alert/bin/auto_validator.py
/opt/splunk/etc/apps/security_alert/bin/deployment_health_check.py
```
