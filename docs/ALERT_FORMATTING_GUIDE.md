# Alert Formatting Guide - FortiGate Operational Monitoring

**Created**: 2025-10-29
**Purpose**: Complete guide for configuring Splunk alerts with proper Slack formatting
**Scope**: Configuration changes, Critical events, HA events

---

## 📋 Quick Reference

| Alert Name | Trigger | Slack Channel | Icon |
|------------|---------|---------------|------|
| FortiGate_Config_Change_Alert | Every config change | #security-firewall-alert | 🔥 |
| FortiGate_Critical_Event_Alert | Critical system events | #security-firewall-alert | 🚨 |
| FortiGate_HA_Event_Alert | HA failover/sync issues | #security-firewall-alert | 🔴🟠🟡 |

---

## 🔥 Alert 1: Configuration Change Alert

### Splunk Configuration

**Save Search As**: `FortiGate_Config_Change_Alert`

**Search Query** (from `03-full-config-alert-query.spl`):
```spl
index=fortianalyzer earliest=-1h type=event subtype=system \
    (logid=0100044546 OR logid=0100044547) \
    (cfgpath="firewall.policy*" OR cfgpath="firewall.address*" OR cfgpath="firewall.service*" OR cfgpath="system.interface*" OR cfgpath="router.*" OR cfgpath="vpn.*") \
| dedup devname, user, cfgpath \
| eval device = devname \
| eval admin = coalesce(user, "system") \
| eval access_method = case(logid="0100044546", "CLI", logid="0100044547", "GUI", 1=1, coalesce(ui, "N/A")) \
| eval config_path = cfgpath \
| eval action_type = coalesce(action, "Modified") \
| eval object_name = coalesce(cfgobj, "-") \
| eval details = case(isnull(cfgattr), "No details", 1=1, substr(cfgattr, 1, 100)) \
| eval alert_message = "🔥 FortiGate Config Change - Device: " + device + " | Admin: " + admin + " (" + access_method + ") | Action: " + action_type + " | Path: " + config_path + " | Object: " + object_name + " | Details: " + details \
| table alert_message, device, admin, config_path
```

### Alert Settings

**Schedule**:
- Type: Real-time
- Cron Expression: `* * * * *` (Every minute)
- Time Range: Last 60 minutes (`earliest=-1h`)

**Trigger Conditions**:
- Trigger alert when: `Number of Results`
- Is greater than: `0`

**Throttle**:
- ✅ **IMPORTANT**: Enable suppression
- Suppress results containing same values in fields: `user, cfgpath`
- For: `15 seconds`
- **Reason**: Prevents duplicate alerts when admin makes multiple changes to same object

### Actions

**Slack Configuration**:
```ini
[FortiGate_Config_Change_Alert]
action.slack = 1
action.slack.param.channel = #security-firewall-alert
action.slack.param.message = $result.alert_message$
action.slack.param.attachment =
action.slack.param.webhook_url =
```

**Email Configuration** (optional):
```ini
action.email = 1
action.email.to = security-team@company.com
action.email.subject = FortiGate Configuration Change - $result.device$
action.email.message.alert = $result.alert_message$
```

### Slack Message Format

**Example Output**:
```
🔥 FortiGate Config Change - Device: FGT-01 | Admin: admin (CLI) | Action: Modified | Path: firewall.policy[10] | Object: policy_10 | Details: srcaddr=all dstaddr=all service=HTTP action=accept
```

**Fields Included**:
- Device name
- Admin user
- Access method (CLI/GUI)
- Action type (Modified/Created/Deleted)
- Configuration path
- Object name
- Details (first 100 characters)

---

## 🚨 Alert 2: Critical Event Alert

### Splunk Configuration

**Save Search As**: `FortiGate_Critical_Event_Alert`

**Search Query** (from `04-critical-events.spl`):
```spl
index=fortianalyzer earliest=-24h type=event subtype=system level=critical \
    logid!=0100044546 logid!=0100044547 logid!=010032021 \
| search NOT msg="*Update Fail*" NOT msg="*Login Fail*" \
| dedup devname, logid \
| eval device = devname \
| eval log_id = logid \
| eval severity = level \
| eval description = coalesce(logdesc, msg, "No details available") \
| eval alert_message = "🚨 FortiGate CRITICAL Event - Device: " + device + " | LogID: " + log_id + " | Description: " + description \
| table alert_message, device, log_id, severity, description
```

### Alert Settings

**Schedule**:
- Type: Real-time
- Cron Expression: `* * * * *` (Every minute)
- Time Range: Last 24 hours (`earliest=-24h`)

**Trigger Conditions**:
- Trigger alert when: `Number of Results`
- Is greater than: `0`

**Throttle**:
- ✅ **IMPORTANT**: Enable suppression
- Suppress results containing same values in fields: `device, logid`
- For: `5 minutes`
- **Reason**: Critical events may repeat, suppress for 5 minutes to avoid flooding

### Actions

**Slack Configuration**:
```ini
[FortiGate_Critical_Event_Alert]
action.slack = 1
action.slack.param.channel = #security-firewall-alert
action.slack.param.message = $result.alert_message$
action.slack.param.attachment =
action.slack.param.webhook_url =
```

**Webhook Configuration** (optional - for incident management):
```ini
action.webhook = 1
action.webhook.param.url = https://your-incident-system.com/api/v1/incidents
action.webhook.param.method = POST
```

### Slack Message Format

**Example Output**:
```
🚨 FortiGate CRITICAL Event - Device: FGT-01 | LogID: 0104001234 | Description: HA member down detected
```

**Expected Critical Events**:
- HA failover
- Disk full
- Fan failure
- Memory critical
- Service crashed
- Hardware malfunction

---

## 🔴 Alert 3: HA Event Alert

### Splunk Configuration

**Save Search As**: `FortiGate_HA_Event_Alert`

**Search Query** (from `05-ha-events.spl`):
```spl
index=fortianalyzer earliest=-24h type=event subtype=system logid=0103* \
| dedup devname, logid, level \
| eval device = devname \
| eval log_id = logid \
| eval severity = level \
| eval description = coalesce(logdesc, msg, "HA event occurred") \
| eval icon = case(level="critical", "🔴", level="error", "🟠", level="warning", "🟡", 1=1, "🔵") \
| eval alert_message = icon + " FortiGate HA Event - Device: " + device + " | Severity: " + severity + " | LogID: " + log_id + " | Description: " + description \
| table alert_message, device, log_id, severity, description
```

### Alert Settings

**Schedule**:
- Type: Real-time
- Cron Expression: `* * * * *` (Every minute)
- Time Range: Last 24 hours (`earliest=-24h`)

**Trigger Conditions**:
- Trigger alert when: `Number of Results`
- Is greater than: `0`

**Severity-Based Filtering** (recommended):
```spl
| where severity IN ("critical", "error", "warning")
```

**Throttle**:
- ✅ **IMPORTANT**: Enable suppression
- Suppress results containing same values in fields: `device, logid, severity`
- For: `3 minutes`
- **Reason**: HA events during failover may generate multiple logs

### Actions

**Slack Configuration**:
```ini
[FortiGate_HA_Event_Alert]
action.slack = 1
action.slack.param.channel = #security-firewall-alert
action.slack.param.message = $result.alert_message$
action.slack.param.attachment =
action.slack.param.webhook_url =
```

### Slack Message Format

**Example Output**:
```
🔴 FortiGate HA Event - Device: FGT-01 | Severity: critical | LogID: 0103008002 | Description: HA member down
🟠 FortiGate HA Event - Device: FGT-01 | Severity: error | LogID: 0103008001 | Description: HA sync failed
🟡 FortiGate HA Event - Device: FGT-01 | Severity: warning | LogID: 0103008004 | Description: HA member up
```

**Severity Icons**:
- 🔴 Critical: HA member down, split brain
- 🟠 Error: Sync failures, communication issues
- 🟡 Warning: Sync delays, minor issues
- 🔵 Info: Normal HA events (member up)

---

## 📊 Alert Management

### Viewing Triggered Alerts

**Splunk Web UI**:
```
Settings → Searches, reports, and alerts → Select alert → View recent alerts
```

**Search for Alert History**:
```spl
index=_audit action=alert_fired savedsearch_name="FortiGate_*"
| table _time, savedsearch_name, user, result_count
| sort -_time
```

### Enabling/Disabling Alerts

**Via Web UI**:
1. Settings → Searches, reports, and alerts
2. Find alert name
3. Edit → Actions → Enable/Disable

**Via CLI**:
```bash
# Disable alert
splunk edit saved-search FortiGate_Config_Change_Alert -disabled 1

# Enable alert
splunk edit saved-search FortiGate_Config_Change_Alert -disabled 0

# Check status
splunk list saved-search FortiGate_Config_Change_Alert
```

### Testing Alerts

**Manual Test** (without waiting for real events):
```bash
# Trigger alert manually with test data
splunk search "|makeresults | eval alert_message=\"🔥 TEST - FortiGate Config Change\" | sendalert slack param.channel=#security-firewall-alert param.message=alert_message"
```

**Dry Run** (check if alert would trigger):
```spl
# Run search and check result count
index=fortianalyzer earliest=-1h (logid=0100044546 OR logid=0100044547)
| stats count
# If count > 0, alert would trigger
```

---

## 🎨 Advanced Slack Formatting

### Block Kit Format (Interactive Alerts)

**Location**: See `docs/SLACK_BLOCKKIT_DEPLOYMENT.md` for full guide

**Example Configuration** (`configs/alert_actions-slack-blockkit.conf`):
```ini
[FortiGate_Config_Change_Alert_BlockKit]
action.slack.param.channel = #security-firewall-alert
action.slack.param.blocks = [
  {
    "type": "header",
    "text": {
      "type": "plain_text",
      "text": "🔥 FortiGate Configuration Change"
    }
  },
  {
    "type": "section",
    "fields": [
      {"type": "mrkdwn", "text": "*Device:*\n$result.device$"},
      {"type": "mrkdwn", "text": "*Admin:*\n$result.admin$"},
      {"type": "mrkdwn", "text": "*Method:*\n$result.access_method$"},
      {"type": "mrkdwn", "text": "*Action:*\n$result.action_type$"}
    ]
  },
  {
    "type": "section",
    "text": {
      "type": "mrkdwn",
      "text": "*Config Path:*\n`$result.config_path$`\n\n*Details:*\n$result.details$"
    }
  },
  {
    "type": "actions",
    "elements": [
      {
        "type": "button",
        "text": {"type": "plain_text", "text": "View in Splunk"},
        "url": "https://splunk.jclee.me/app/search/search?q=search%20index%3Dfw%20device%3D$result.device$",
        "style": "primary"
      },
      {
        "type": "button",
        "text": {"type": "plain_text", "text": "Acknowledge"},
        "value": "ack_$result.device$_$result._time$"
      }
    ]
  }
]
```

**Benefits**:
- Structured formatting with sections
- Clickable buttons (View in Splunk, Acknowledge)
- Rich text with markdown support
- Better visual hierarchy

---

## 📝 Configuration File Examples

### Complete Alert Actions Configuration

**File**: `configs/alert_actions.conf`

```ini
# FortiGate Configuration Change Alert
[FortiGate_Config_Change_Alert]
action.slack = 1
action.slack.param.channel = #security-firewall-alert
action.slack.param.message = $result.alert_message$

# FortiGate Critical Event Alert
[FortiGate_Critical_Event_Alert]
action.slack = 1
action.slack.param.channel = #security-firewall-alert
action.slack.param.message = $result.alert_message$
action.email = 1
action.email.to = security-team@company.com
action.email.subject = FortiGate Critical Event - $result.device$

# FortiGate HA Event Alert
[FortiGate_HA_Event_Alert]
action.slack = 1
action.slack.param.channel = #security-firewall-alert
action.slack.param.message = $result.alert_message$
action.slack.param.attachment = severity=$result.severity$, device=$result.device$
```

### Slack Plugin Configuration

**File**: `/opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf`

```ini
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
param.channel = #security-firewall-alert
param.username = Splunk Alert Bot
param.icon_emoji = :fire:
```

---

## 🔧 Troubleshooting

### Alert Not Triggering

**Check 1: Search Returns Results**
```spl
# Run search manually
index=fortianalyzer earliest=-1h (logid=0100044546 OR logid=0100044547)
| stats count
# Should show count > 0
```

**Check 2: Alert is Enabled**
```bash
splunk list saved-search FortiGate_Config_Change_Alert | grep disabled
# Should show: disabled = 0
```

**Check 3: Scheduler Status**
```spl
index=_internal source=*scheduler.log savedsearch_name="FortiGate_*"
| table _time, savedsearch_name, status, result_count
| sort -_time
```

### Slack Notifications Not Received

**Check 1: Bot Invited to Channel**
```
In Slack: /invite @splunk-alert-bot
```

**Check 2: Bot Token Valid**
```bash
curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer SLACK_BOT_TOKEN_PLACEHOLDER"
```

**Check 3: Channel Name Format**
```
✅ CORRECT: #security-firewall-alert
❌ WRONG: security-firewall-alert (missing #)
```

**Check 4: Slack Plugin Logs**
```spl
index=_internal source=*slack* ERROR
| table _time, log_level, message
```

### Too Many Alerts (Alert Fatigue)

**Solution 1: Increase Suppression Time**
```
Current: 15 seconds → Increase to: 5 minutes
```

**Solution 2: Add More Specific Filters**
```spl
# Only alert for critical config paths
| where match(config_path, "firewall.policy") OR match(config_path, "vpn")

# Only alert during business hours
| where date_hour >= 9 AND date_hour <= 18
```

**Solution 3: Summary Alert** (hourly digest)
```spl
# Instead of real-time, schedule every hour
# Cron: 0 * * * * (Every hour)
index=fortianalyzer earliest=-1h (logid=0100044546 OR logid=0100044547)
| stats count by device, admin, config_path
| eval alert_message = "📊 FortiGate Config Summary: " + count + " changes by " + admin + " on " + device
```

---

## 📋 Deployment Checklist

Before going to production:

- [ ] Test queries return expected results (use `test-queries/`)
- [ ] Alert suppression configured (prevent duplicates)
- [ ] Slack bot invited to channel
- [ ] Slack bot has correct OAuth scopes (`chat:write`, `channels:read`)
- [ ] Email recipients confirmed (if using email)
- [ ] Alert schedule appropriate (real-time vs scheduled)
- [ ] Throttling tested (send 5 events, verify only 1 alert)
- [ ] Dashboard deployed (`fortigate-config-monitoring-v2.xml`)
- [ ] Alert actions tested with `| sendalert` command
- [ ] Documentation updated with alert names and channels

---

## 📚 Related Documentation

- **Test Queries**: `test-queries/README.md` - 5 ready-to-use queries
- **Block Kit Alerts**: `docs/SLACK_BLOCKKIT_DEPLOYMENT.md` - Interactive Slack alerts
- **Dashboard Guide**: `fortigate-config-monitoring-v2.xml` - Full monitoring dashboard
- **Query Fix Comparison**: `configs/EVAL_FIX_COMPARISON.md` - Before/after eval fixes

---

**Version**: 1.0
**Created**: 2025-10-29
**Maintained by**: Security Operations Team
