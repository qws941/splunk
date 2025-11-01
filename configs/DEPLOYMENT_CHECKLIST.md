# Splunk Alert Configuration Deployment Checklist

## ✅ Pre-Deployment Validation

### 1. Configuration Review
- [ ] Reviewed all `⚙️ CHANGEME` markers (13 locations)
- [ ] Updated Slack channel names: `#security-firewall-alert` → `#your-channel`
- [ ] Verified index name: `index=fw` matches your environment
- [ ] Adjusted suppress periods if needed (30s, 2m, 3m, 1d)

### 2. Syntax Validation
```bash
# Basic syntax check
python3 -c "
import configparser
config = configparser.ConfigParser()
config.read('configs/savedsearches-fortigate-alerts-logid-based.conf')
print(f'✅ {len(config.sections())} stanzas loaded')
"

# Check for CHANGEME markers
grep -n "⚙️ CHANGEME" configs/savedsearches-fortigate-alerts-logid-based.conf
```

### 3. Slack Integration
- [ ] Slack bot created and OAuth token obtained
- [ ] Bot invited to target channel(s): `/invite @your-bot`
- [ ] Bot has required scopes: `chat:write`, `channels:read`, `chat:write.public`
- [ ] Tested bot with manual message

### 4. Data Verification
```bash
# Verify data exists in index
index=fw type=event subtype=system | head 10

# Check for config change events (logid 0100044546, 0100044547)
index=fw logid=0100044546 OR logid=0100044547 | head 5

# Verify field extraction works
index=fw | table _time, devname, logid, user, cfgpath | head 10
```

---

## 🚀 Deployment Steps

### Step 1: Backup Existing Config
```bash
sudo cp /opt/splunk/etc/apps/search/local/savedsearches.conf \
  /opt/splunk/etc/apps/search/local/savedsearches.conf.backup.$(date +%Y%m%d_%H%M%S)
```

### Step 2: Deploy New Config
```bash
# Option A: Copy entire file (if no existing saved searches)
sudo cp configs/savedsearches-fortigate-alerts-logid-based.conf \
  /opt/splunk/etc/apps/search/local/savedsearches.conf

# Option B: Append to existing file (if you have other saved searches)
cat configs/savedsearches-fortigate-alerts-logid-based.conf | \
  sudo tee -a /opt/splunk/etc/apps/search/local/savedsearches.conf > /dev/null
```

### Step 3: Validate with Splunk btool
```bash
# Check for syntax errors
splunk btool savedsearches list --debug 2>&1 | grep -i error

# Verify our alerts loaded
splunk btool savedsearches list | grep -A 2 "^\[FortiGate_"
```

### Step 4: Reload Splunk Config
```bash
# Reload without restart (preferred)
sudo /opt/splunk/bin/splunk reload apps -auth admin:changeme

# OR full restart (if reload doesn't work)
sudo systemctl restart splunkd
```

---

## 🧪 Testing

### Test 1: Manual Search Execution
```bash
# Test each alert manually (from Splunk Search bar)
| savedsearch FortiGate_Config_Change
| savedsearch FortiGate_Interface_Status
| savedsearch FortiGate_HA_Status
| savedsearch FortiGate_Device_Events
| savedsearch FortiGate_System_Resource
| savedsearch FortiGate_Admin_Activity
```

### Test 2: Monitor Scheduler Execution
```bash
# Check if alerts are running
index=_internal source=*scheduler.log savedsearch_name="FortiGate_*"
| stats count, latest(_time) as last_run by savedsearch_name, status
```

### Test 3: Verify Slack Notifications
- [ ] Trigger a test config change on FortiGate
- [ ] Verify Slack message received within 1 minute
- [ ] Check message formatting (Block Kit JSON)

---

## 📊 Post-Deployment Monitoring

### First 24 Hours
```bash
# Monitor alert execution
index=_internal source=*scheduler.log savedsearch_name="FortiGate_*" earliest=-24h
| stats count, avg(run_time) as avg_runtime_sec, max(run_time) as max_runtime_sec by savedsearch_name, status
| sort -avg_runtime_sec

# Check for errors
index=_internal source=*scheduler.log savedsearch_name="FortiGate_*" status=failure
| table _time, savedsearch_name, message
```

### Alert Volume Analysis
```bash
# How many alerts fired?
index=_internal source=*alert_actions.log action=slack earliest=-24h
| stats count by savedsearch_name
| sort -count

# Suppression effectiveness
index=_internal source=*alert_actions.log action=slack earliest=-24h
| stats count as fired, dc(alert_id) as unique_alerts by savedsearch_name
```

---

## 🔧 Troubleshooting

### Issue: No Alerts Firing
**Diagnosis:**
```bash
# 1. Check if searches are scheduled
splunk btool savedsearches list | grep -B 5 "cron_schedule = \* \* \* \*"

# 2. Check for data in index
index=fw type=event subtype=system earliest=-1h | stats count

# 3. Check scheduler logs
index=_internal source=*scheduler.log savedsearch_name="FortiGate_Config_Change" earliest=-1h
```

**Solutions:**
- Verify `enableSched = 1` in config
- Check `dispatch.earliest_time = rt` for real-time
- Confirm data exists in `index=fw`

### Issue: Slack Not Receiving Messages
**Diagnosis:**
```bash
# Check if Slack action executed
index=_internal source=*alert_actions.log action=slack earliest=-1h
| table _time, savedsearch_name, result

# Check for errors
index=_internal "slack" error earliest=-1h
```

**Solutions:**
- Verify bot invited to channel
- Check Slack token in `alert_actions.conf`
- Test bot manually: `curl -X POST https://slack.com/api/auth.test -H "Authorization: Bearer SLACK_BOT_TOKEN_PLACEHOLDER"`

### Issue: Too Many Duplicate Alerts
**Solution:** Increase suppression periods
```bash
# Current settings
alert.suppress.period = 30s   # Config changes
alert.suppress.period = 2m    # Interface status
alert.suppress.period = 3m    # HA events
alert.suppress.period = 1d    # Hardware/resource events

# Recommended adjustments for noisy environments
alert.suppress.period = 5m    # Config changes (increased)
alert.suppress.period = 10m   # Interface status (increased)
```

---

## 📈 Success Metrics

### Week 1 Targets
- [ ] All 6 alerts executing on schedule (100% success rate)
- [ ] Average runtime < 5 seconds per alert
- [ ] No `status=failure` in scheduler logs
- [ ] Slack messages formatted correctly (Block Kit)

### Week 2 Optimization
- [ ] Fine-tune suppression periods based on alert volume
- [ ] Adjust severity thresholds if needed
- [ ] Review and update LogID filters based on actual events

---

## 📝 Change Log

| Date | Change | Author | Notes |
|------|--------|--------|-------|
| 2025-11-02 | Initial deployment | AI | Added 6 real-time alerts with logid-based filtering |
| 2025-11-02 | Documentation enhanced | AI | Added CHANGEME markers and troubleshooting guide |

---

**Validation Status:** ✅ PASSED (All syntax checks completed)
**Ready for Deployment:** YES
**Estimated Deployment Time:** 10-15 minutes
