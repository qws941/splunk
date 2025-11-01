# Splunk Slack Alerts - Reference Guide
**Real-world Examples from GitHub & Official Documentation**

> Created: 2025-10-31
> Sources: Splunk official docs, GitHub repositories, Splunkbase

---

## 📚 Table of Contents

1. [Official Documentation](#official-documentation)
2. [GitHub Real-world Examples](#github-real-world-examples)
3. [Our Implementation Comparison](#our-implementation-comparison)
4. [Best Practices](#best-practices)
5. [Troubleshooting Resources](#troubleshooting-resources)

---

## 📖 Official Documentation

### Splunk Docs: Configure Alerts in savedsearches.conf

**Source**: https://docs.splunk.com/Documentation/Splunk/latest/Alert/Configuringalertsinsavedsearches.conf

**Key Configuration Parameters**:

```ini
[Your_Alert_Name]
# Search query
search = index=your_index earliest=-5m latest=now | stats count

# Schedule
enableSched = 1
cron_schedule = */5 * * * *
schedule_priority = default

# Trigger conditions
alert.track = 1
counttype = number of events
relation = greater than
quantity = 0

# Alert actions
action.email = 1
action.email.to = admin@example.com

# For custom alert actions (like Slack)
action.slack = 1
action.slack.param.channel = #alerts
action.slack.param.message = Alert triggered!

# Suppression (prevent alert spam)
alert.suppress = 1
alert.suppress.period = 300s
alert.suppress.fields = host
```

### Real-time Search Configuration

```ini
# Real-time vs Scheduled
realtime_schedule = 1           # Enable real-time mode
cron_schedule = * * * * *        # Every minute (required even for real-time)
dispatch.earliest_time = rt-30s  # Real-time window: last 30 seconds
dispatch.latest_time = rt        # Real-time window: now
```

**⚠️ Important**: Even real-time searches need `cron_schedule = * * * * *` to trigger evaluation every minute.

---

## 🔍 GitHub Real-world Examples

### Example 1: Twitter App - Real-time Stream Alert

**Source**: https://github.com/splunk/splunk-app-twitter

```ini
[Tweet Stream]
action.email.inline = 1
action.email.reportServerEnabled = 0
alert.digest_mode = True
alert.suppress = 0
alert.track = 0
cron_schedule = * * * * *
dispatch.earliest_time = rt-30s
dispatch.latest_time = rt
displayview = flashtimeline
request.ui_dispatch_view = flashtimeline
search = index=twitter text=* | table text | sort -_time
vsid = h324tlu5
```

**Key Takeaway**: Real-time search with `rt-30s` to `rt` window, evaluated every minute.

---

### Example 2: NSA Cyber SAMI - High-frequency Alert with Summary Index

**Source**: https://github.com/nsacyber/Splunk-Assessment-of-Mitigation-Implementations

```ini
[Network - Mitigation High Confidence IDS - Rule]
action.email.reportServerEnabled = 0
action.keyindicator.invert = 0
action.summary_index = 1
action.summary_index._name = notable
action.summary_index.ttl = 1p
alert.suppress = 1
alert.suppress.fields = src
alert.suppress.period = 86300
alert.track = 0
counttype = number of events
cron_schedule = */1 * * * *
dispatch.earliest_time = -24h
dispatch.latest_time = +0s
enableSched = 1
quantity = 0
realtime_schedule = 0
relation = greater than
search = | tstats `summariesonly` count from datamodel=Intrusion_Detection where earliest=-24h@h latest=+0s
```

**Key Takeaway**:
- Uses `alert.suppress.period = 86300` (24 hours) to prevent duplicate alerts on same source IP
- Summary index action for logging all detections
- Uses tstats for performance

---

### Example 3: Splunk Mitigation Framework - Real-time Security Alert

**Source**: https://github.com/josehelps/Splunk-Mitigation-Framework

```ini
[Network - Mitigation High Confidence IDS - Rule]
alert.suppress = 1
alert.suppress.fields = src
alert.suppress.period = 86300
cron_schedule = */1 * * * *
enableSched = 1
quantity = 0
realtime_schedule = 0
search = | tstats `summariesonly` count from datamodel=Intrusion_Detection
```

**Key Takeaway**: Uses `alert.suppress.fields = src` to suppress per-source IP, not globally.

---

### Example 4: Cisco ISE App - Scheduled Lookup Builder

**Source**: https://github.com/splunk/splunk-app-cisco-ise

```ini
[Lookup - Locations]
action.email.inline = 1
alert.suppress = 0
alert.track = 0
cron_schedule = 0 * * * *
description = Updates the ISE_Locations.csv lookup file
dispatch.earliest_time = -24h@h
dispatch.latest_time = now
enableSched = 1
run_on_startup = true
search = eventtype="cisco-ise" Location="*" | stats count by Location | inputlookup append=T ISE_Locations.csv | stats count by Location | table Location | outputlookup ISE_Locations.csv
```

**Key Takeaway**: Uses `run_on_startup = true` for initialization tasks.

---

## 🔄 Our Implementation Comparison

### Current Configuration (FortiGate Alerts)

```ini
[FortiGate_Config_Change_Alert]
description = FortiGate configuration change notifications
search = index=fw earliest=rt-30s latest=rt type=event subtype=system \
    (logid=0100044546 OR logid=0100044547) \
    (cfgpath="firewall.policy*" OR cfgpath="firewall.address*" ...) \
| dedup devname, user, cfgpath \
| eval alert_message = "🔥 FortiGate Config Change - Device: " + device + " | Admin: " + admin + "..." \
| table alert_message, device, admin, config_path

# Real-time schedule
enableSched = 1
realtime_schedule = 1
cron_schedule = * * * * *
schedule_priority = highest

# Trigger
alert.track = 1
counttype = number of events
quantity = 0
relation = greater than

# Slack action
action.slack = 1
action.slack.param.channel = #security-firewall-alert
action.slack.param.message = $result.alert_message$

# Suppress
alert.suppress = 1
alert.suppress.period = 15s
alert.suppress.fields = user, cfgpath
```

### ✅ What We're Doing Right

1. **Real-time configuration**: `rt-30s` to `rt` window ✅
2. **Deduplication**: Using `dedup` to prevent duplicate alerts ✅
3. **Suppression**: 15-second period to prevent alert storms ✅
4. **Field-based suppression**: `alert.suppress.fields = user, cfgpath` prevents duplicate per-user-per-path ✅
5. **Priority**: `schedule_priority = highest` ensures timely execution ✅
6. **Message template**: Using eval to build structured message ✅

### 📊 Comparison with Industry Examples

| Feature | Our Config | Twitter App | NSA SAMI | Cisco ISE |
|---------|------------|-------------|----------|-----------|
| Real-time | ✅ rt-30s | ✅ rt-30s | ❌ Scheduled | ❌ Scheduled |
| Cron frequency | Every minute | Every minute | Every minute | Hourly |
| Suppression | 15s | None | 24 hours | None |
| Suppress fields | user, cfgpath | N/A | src | N/A |
| Priority | highest | default | default | default |
| Dedup | ✅ In SPL | None | tstats | None |

**Verdict**: Our configuration follows best practices for real-time security alerting! 🎉

---

## 📋 Best Practices (from GitHub Examples)

### 1. Suppression Strategy

```ini
# Short suppression for high-frequency events (our approach)
alert.suppress.period = 15s
alert.suppress.fields = user, cfgpath

# Long suppression for persistent conditions (NSA SAMI approach)
alert.suppress.period = 86300  # 24 hours
alert.suppress.fields = src    # Per-source IP
```

**When to use**:
- **Short (seconds)**: Config changes, login events (transient events)
- **Long (hours)**: IDS alerts, persistent threats (ongoing conditions)

### 2. Performance Optimization

```spl
# ❌ SLOW (raw search)
index=fw earliest=-1h | stats count by src_ip

# ✅ FAST (data model acceleration)
| tstats count WHERE datamodel=Security.Events BY Events.src_ip

# ✅ FASTER (summary index pre-aggregation)
index=summary_fw marker="correlation_detection=*"
```

### 3. Message Formatting

```spl
# ✅ Good: Structured eval message (our approach)
| eval alert_message = "🔥 Device: " + device + " | Admin: " + admin + " | Action: " + action

# ✅ Better: Include context
| eval alert_message = "🔥 FortiGate Config Change\nDevice: " + device + "\nAdmin: " + admin + " (" + access_method + ")\nPath: " + config_path + "\nTime: " + strftime(_time, "%Y-%m-%d %H:%M:%S")

# ❌ Bad: Raw field values
action.slack.param.message = $devname$ $user$ $action$
```

### 4. Real-time vs Scheduled

```ini
# Real-time (for immediate threats)
realtime_schedule = 1
cron_schedule = * * * * *
dispatch.earliest_time = rt-30s
dispatch.latest_time = rt

# Scheduled (for aggregated analysis)
realtime_schedule = 0
cron_schedule = */5 * * * *
dispatch.earliest_time = -10m
dispatch.latest_time = -5m
```

**Use real-time for**: Config changes, critical errors, security breaches
**Use scheduled for**: Trending, statistics, resource-intensive searches

---

## 🚨 Troubleshooting Resources

### Common Issues from GitHub Issues

#### Issue 1: Alerts Not Firing

**Symptom**: Saved search runs but no Slack messages received

**Checks**:
```bash
# 1. Verify saved search exists
/opt/splunk/bin/splunk search "| rest /services/saved/searches | search title=FortiGate_* | table title"

# 2. Check scheduler logs
tail -f /opt/splunk/var/log/splunk/scheduler.log | grep FortiGate_

# 3. Test alert action manually
| makeresults | eval message="Test alert" | sendalert slack param.channel="#security-firewall-alert" param.message=message

# 4. Verify data exists in index
index=fw earliest=-5m | stats count
```

#### Issue 2: Alert Storms

**Symptom**: Too many Slack messages

**Solutions**:
```ini
# Option 1: Increase suppression period
alert.suppress.period = 300s  # 5 minutes instead of 15s

# Option 2: Add more suppress fields
alert.suppress.fields = user, cfgpath, devname

# Option 3: Increase quantity threshold
quantity = 5  # Only alert if > 5 events

# Option 4: Add NOT filters to SPL
| search NOT msg="*Update Fail*" NOT msg="*Login Fail*"
```

#### Issue 3: Real-time Search Skipped

**Symptom**: `scheduler.log` shows "skipped" status

**Causes**:
- Too many concurrent real-time searches
- Search takes longer than cron interval
- Splunk max_concurrent limit reached

**Solutions**:
```bash
# Check concurrent searches
grep "concurrent" /opt/splunk/etc/system/local/limits.conf

# Increase limit (edit limits.conf)
[scheduler]
max_concurrent_realtime = 10  # Default is 3

# Optimize search query
# Use tstats, reduce time window, add early filters
```

---

## 📚 Additional Resources

### Official Splunk Documentation
- **savedsearches.conf reference**: https://docs.splunk.com/Documentation/Splunk/latest/Admin/Savedsearchesconf
- **Alert actions**: https://docs.splunk.com/Documentation/Splunk/latest/Alert/AlertActionReference
- **Real-time searches**: https://docs.splunk.com/Documentation/Splunk/latest/Search/Aboutrealtimesearches

### Splunkbase Apps
- **Slack Notification Alert**: https://splunkbase.splunk.com/app/2878
  - Official Slack integration app
  - GitHub: https://github.com/splunk/slack-alerts
  - Supports webhook URLs and Slack Apps

### GitHub Examples
- **Twitter App** (real-time): https://github.com/splunk/splunk-app-twitter
- **NSA SAMI** (security alerts): https://github.com/nsacyber/Splunk-Assessment-of-Mitigation-Implementations
- **Cisco ISE** (lookup builders): https://github.com/splunk/splunk-app-cisco-ise
- **Mitigation Framework**: https://github.com/josehelps/Splunk-Mitigation-Framework

### Community Resources
- **Splunk Answers**: https://community.splunk.com/
- **Splunk Docs Forum**: https://community.splunk.com/t5/Splunk-Search/bd-p/splunk-search
- **Stack Overflow**: Tag `splunk` for general questions

---

## ✅ Validation Checklist

Before deploying Slack alerts, verify:

- [ ] Slack Bot token configured (xoxb-* format)
- [ ] Bot invited to channel (`/invite @bot-name`)
- [ ] alert_actions.conf has correct token and channel
- [ ] savedsearches.conf uses correct index (index=fw)
- [ ] Test query returns results: `index=fw earliest=-5m | stats count`
- [ ] Suppression period appropriate for event frequency
- [ ] Message template includes relevant context
- [ ] Schedule priority set (highest for critical alerts)
- [ ] Tested manually: `| sendalert slack ...`

---

**Last Updated**: 2025-10-31
**Maintained By**: FortiGate-Splunk Integration Team
**Repository**: https://github.com/qws941/splunk
