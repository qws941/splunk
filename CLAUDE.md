# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Project Overview

**FortiGate Firewall Policy Monitoring** - Monitor FortiGate firewall policy changes in Splunk with real-time Slack alerts.

### Core Purpose
1. **Policy Change Tracking** - Monitor firewall policy modifications (Add/Edit/Delete)
2. **Splunk Dashboard** - Visualize policy changes and critical events
3. **Slack Alerts** - Real-time notifications for policy changes and critical security events

---

## 📊 Firewall Policy Monitoring

### Dashboard Location
**File**: `dashboards/fortinet-dashboard.xml`
**Splunk Path**: Search & Reporting → Dashboards → FortiGate Security Dashboard

### Key Panels

#### 1. Configuration Change History
**Panel**: "⚙️ Configuration Change History"
**Purpose**: Track all firewall policy modifications

**SPL Query**:
```spl
index=fw (logid="0100044547" OR logid="0100044546" OR logid="0100044545")
| rex field=_raw "cfgpath=\"?(?<config_path>[^\"]+)\"?"
| eval change_type = case(
    logid="0100044547", "Deleted",
    logid="0100044546", "Edited",
    logid="0100044545", "Added",
    1=1, "Other"
  )
| eval path_category = case(
    match(config_path, "firewall\.policy"), "Firewall Policy",
    match(config_path, "system"), "Interface",
    match(config_path, "user"), "User/Group",
    match(config_path, "firewall\.address"), "Address Object",
    match(config_path, "firewall\.service"), "Service Object",
    1=1, "Other"
  )
| table _time, devname, user, change_type, path_category, config_path
```

**LogID Mapping**:
- `0100044545` → ✅ Added
- `0100044546` → ✏️ Edited
- `0100044547` → 🗑️ Deleted

#### 2. Policy Change Distribution
**Panel**: "📊 Policy Change Distribution"
**Purpose**: Visualize change types (pie chart)

**SPL Query**:
```spl
index=fw (logid="0100044547" OR logid="0100044546" OR logid="0100044545")
| eval change_type = case(
    logid="0100044547", "Deleted",
    logid="0100044546", "Edited",
    logid="0100044545", "Added",
    1=1, "Other"
  )
| stats count by change_type
```

---

## 🔔 Slack Alert Configuration

### Alert Panels

#### Critical Event Alert
**Trigger**: Critical/Emergency severity events (excludes "Update Fail", "Login Fail")

**SPL Query**:
```spl
index=fw (level=critical OR level=alert) earliest=$time_picker.earliest$ latest=$time_picker.latest$
| search NOT msg="*Update Fail*" NOT msg="*Login Fail*"
| head 1
| eval emoji=case(
    level="critical" OR level="emergency", "🔴",
    level="alert", "🟠",
    1=1, "⚠️"
  )
| eval slack_message=emoji + " *CRITICAL EVENT ALERT*\n" +
    "━━━━━━━━━━━━━━━━━━━━━━━━\n" +
    "*Device:* `" + devname + "`\n" +
    "*Severity:* " + upper(level) + "\n" +
    "*Time:* " + strftime(_time, "%Y-%m-%d %H:%M:%S") + "\n\n" +
    "*Error Message:*\n```" + msg + "```"
| sendalert slack param.message=slack_message
```

**Message Format**:
```
🔴 *CRITICAL EVENT ALERT*
━━━━━━━━━━━━━━━━━━━━━━━━
*Device:* `FGT-MAIN-01`
*Severity:* CRITICAL
*Time:* 2025-10-21 14:30:00

*Error Message:*
```System error detected```
```

#### Config Change Alert
**Trigger**: Any firewall policy configuration change

**SPL Query**:
```spl
index=fw (logid="0100044547" OR logid="0100044546" OR logid="0100044545") earliest=$time_picker.earliest$ latest=$time_picker.latest$
| head 1
| rex field=_raw "cfgpath=\"?(?<cfg_path>[^\"]+)\"?"
| eval change_type=case(
    logid="0100044545", "✅ Added",
    logid="0100044546", "✏️ Edited",
    logid="0100044547", "🗑️ Deleted",
    1=1, "📝 Modified"
  )
| eval category=case(
    match(cfg_path, "firewall\.policy"), "🛡️ Firewall Policy",
    match(cfg_path, "system"), "⚙️ System",
    match(cfg_path, "user"), "👤 User/Group",
    1=1, "📂 Other"
  )
| eval slack_message="⚙️ *CONFIGURATION CHANGE*\n" +
    "━━━━━━━━━━━━━━━━━━━━━━━━\n" +
    "*Device:* `" + devname + "`\n" +
    "*User:* *" + user + "*\n" +
    "*Category:* " + category + "\n" +
    "*Action:* " + change_type + "\n\n" +
    "*Config Path:*\n```" + cfg_path + "```\n\n" +
    "*Time:* " + strftime(_time, "%Y-%m-%d %H:%M:%S")
| sendalert slack param.message=slack_message
```

**Message Format**:
```
⚙️ *CONFIGURATION CHANGE*
━━━━━━━━━━━━━━━━━━━━━━━━
*Device:* `FGT-MAIN-01`
*User:* *admin*
*Category:* 🛡️ Firewall Policy
*Action:* ✏️ Edited

*Config Path:*
```firewall.policy.12```

*Time:* 2025-10-21 14:30:00
```

---

## ⚙️ Slack Plugin Configuration

### OAuth Token (Recommended)

**File**: `configs/slack-alert-actions.conf.example`

```ini
[slack]
# Bot User OAuth Token (xoxb-로 시작)
param.token = SLACK_BOT_TOKEN_PLACEHOLDER

# 기본 채널
param.channel = #splunk-alerts

# Bot 표시 이름
param.from_user = Splunk FortiGate Alert

# Bot 아이콘
param.icon_emoji = :fire:

# 메시지 링크 표시
param.link_names = 1
```

### Required OAuth Scopes
```
chat:write           - 메시지 전송
chat:write.public    - Public 채널 자동 참여
channels:read        - 채널 목록 읽기
```

### Testing
```bash
# Token 유효성 확인
curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer SLACK_BOT_TOKEN_PLACEHOLDER"

# 메시지 전송 테스트
curl -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer SLACK_BOT_TOKEN_PLACEHOLDER" \
  -H "Content-Type: application/json" \
  -d '{"channel":"#splunk-alerts","text":"Test message"}'
```

---

## 🔧 FortiGate Configuration

### HEC Direct Integration

**File**: `configs/fortianalyzer-hec-direct.conf`

**FortiAnalyzer Configuration**:
```bash
config system log-fetch client-profile
    edit "splunk-hec-primary"
        set server-type splunk
        set server-ip "YOUR_SPLUNK_HEC_HOST"
        set server-port 8088
        set secure-connection enable
        set client-key "YOUR_HEC_TOKEN_HERE"
        set data-format splunk-hec
        set log-type traffic utm event
        set upload-interval realtime
        set status enable
    next
end
```

### Syslog Integration

**File**: `configs/fortigate-syslog.conf`

**FortiGate Configuration**:
```bash
config log syslogd setting
    set status enable
    set server "YOUR_SYSLOG_SERVER_IP"
    set port 514
    set mode reliable                          # TCP
    set format rfc5424                         # Structured syslog
    set facility local7
end

config log syslogd filter
    set forward-traffic enable
    set local-traffic enable
    set severity information
    set filter "severity>=warning"
end
```

---

## 📝 Dashboard Modification Guide

### Editing Firewall Policy Panels

**File**: `dashboards/fortinet-dashboard.xml`

#### 1. Add New Policy Category

**Location**: Lines 359-375 (Config Change History panel)

```xml
| eval path_category = case(
    match(config_path, "firewall\.policy"), "Firewall Policy",
    match(config_path, "system"), "Interface",
    match(config_path, "user"), "User/Group",
    match(config_path, "firewall\.address"), "Address Object",
    match(config_path, "firewall\.service"), "Service Object",
    match(config_path, "YOUR_NEW_PATTERN"), "YOUR_NEW_CATEGORY",  ← Add here
    1=1, "Other"
  )
```

#### 2. Add New LogID

**Location**: Lines 359-364

```xml
| eval change_type = case(
    logid="0100044547", "Deleted",
    logid="0100044546", "Edited",
    logid="0100044545", "Added",
    logid="YOUR_NEW_LOGID", "YOUR_ACTION_TYPE",  ← Add here
    1=1, "Other"
  )
```

#### 3. Modify Slack Message Format

**Location**: Lines 445-457 (Config Change Alert panel)

```xml
| eval slack_message="⚙️ *CONFIGURATION CHANGE*\n" +
    "━━━━━━━━━━━━━━━━━━━━━━━━\n" +
    "*Device:* `" + devname + "`\n" +
    "*User:* *" + user + "*\n" +
    "*Category:* " + category + "\n" +
    "*Action:* " + change_type + "\n\n" +
    "*YOUR_CUSTOM_FIELD:* " + your_field + "\n" +  ← Add custom fields
    "*Config Path:*\n```" + cfg_path + "```\n\n" +
    "*Time:* " + strftime(_time, "%Y-%m-%d %H:%M:%S")
```

### XML Validation

```bash
# Validate XML syntax
python3 -c "import xml.etree.ElementTree as ET; tree = ET.parse('dashboards/fortinet-dashboard.xml'); print('✅ XML syntax valid')"
```

---

## 🚀 Essential Commands

### Dashboard Deployment

```bash
# Deploy dashboard to Splunk (REST API)
node scripts/deploy-dashboards.js

# Export current dashboard from Splunk
node scripts/export-dashboards.js

# Validate dashboard XML
python3 -c "import xml.etree.ElementTree as ET; tree = ET.parse('dashboards/fortinet-dashboard.xml')"
```

### Slack Testing

```bash
# Test Slack webhook
node scripts/slack-alert-cli.js --webhook="https://hooks.slack.com/..." --test

# Send custom message
node scripts/slack-alert-cli.js --channel="splunk-alerts" --message="Test alert"
```

### Git Workflow

```bash
# Stage and commit changes
git add dashboards/fortinet-dashboard.xml
git commit -m "feat: Add new policy category to dashboard"
git push origin master

# Check status
git status
```

---

## 🛠️ Troubleshooting

### Slack Alerts Not Received

**Check**:
1. Bot token valid: `curl -X POST https://slack.com/api/auth.test -H "Authorization: Bearer xoxb-TOKEN"`
2. Bot invited to channel: `/invite @your-bot` in Slack
3. OAuth scopes: `chat:write`, `channels:read`, `chat:write.public`
4. `SLACK_ENABLED=true` in `.env` or Splunk alert_actions.conf

### Dashboard Not Updating

**Check**:
1. XML syntax valid: `python3 -c "import xml.etree.ElementTree..."`
2. Splunk index exists: `index=fw | head 1`
3. LogIDs correct: `index=fw logid=0100044545 OR logid=0100044546 OR logid=0100044547 | head 10`
4. Time range valid: Check `$time_picker.earliest$` and `$time_picker.latest$` tokens

### Config Changes Not Appearing

**Check**:
1. FortiGate/FortiAnalyzer logging enabled
2. Correct logids: `0100044545` (Added), `0100044546` (Edited), `0100044547` (Deleted)
3. Splunk HEC receiving data: `curl -k https://SPLUNK_HOST:8088/services/collector/health`
4. Index populated: `index=fw | stats count by logid | sort -count`

---

## 📚 Related Files

### Configuration Files
- `configs/slack-alert-actions.conf.example` - Slack plugin configuration
- `configs/fortianalyzer-hec-direct.conf` - HEC direct integration guide
- `configs/fortigate-syslog.conf` - Syslog integration guide

### Documentation
- `docs/SLACK_ALERT_PLUGIN_GUIDE.md` - Slack plugin setup guide
- `README_DASHBOARDS.md` - Dashboard overview
- `FILE_ORGANIZATION.md` - Complete file structure

### Scripts
- `scripts/deploy-dashboards.js` - Deploy dashboard via REST API
- `scripts/export-dashboards.js` - Export current dashboard
- `scripts/slack-alert-cli.js` - Test Slack alerts

---

**Status**: Production Ready
**Version**: 1.0.0
**Updated**: 2025-10-21
**Focus**: Firewall Policy Monitoring
