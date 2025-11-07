# Troubleshooting Guide

## Common Issues

### 1. Alert Not Triggering

**Symptom:** Expected alerts are not being sent to Slack

**Diagnosis:**
```spl
# Check if events exist in index
`fortigate_index` `logids_vpn_tunnel` earliest=-1h
| stats count by logid, device

# Verify alert execution
index=_internal source=*scheduler.log savedsearch_name="002_VPN_Tunnel_Down"
| stats count by status, result_count

# Check alert action
index=_internal source=*alert_actions.log savedsearch_name="002_VPN_Tunnel_Down"
| table _time, action_name, action_status, stderr
```

**Solutions:**

**Case 1: No events in index**
- Verify FortiGate syslog forwarding is active
- Check firewall rules between FortiGate and Splunk
- Confirm index name in `macros.conf` matches data source

**Case 2: Alert disabled**
```bash
# Check if alert is enabled
grep -A 5 "002_VPN_Tunnel_Down" local/savedsearches.conf
# If enableSched = 0, set to 1 or remove line
```

**Case 3: State tracker blocking alerts**
```spl
# Reset state tracker
| inputlookup vpn_state_tracker
| eval state = "RESET"
| outputlookup vpn_state_tracker
```

### 2. Duplicate Alerts

**Symptom:** Multiple alerts for the same event

**Diagnosis:**
```spl
# Check state tracker updates
index=_internal source=*python.log "outputlookup" "vpn_state_tracker"
| table _time, message

# Verify state changes
| inputlookup vpn_state_tracker
| sort - last_seen
| head 20
```

**Solutions:**

**Case 1: Missing state_changed filter**
```spl
# Verify SPL includes this line:
| where state_changed=1
```

**Case 2: CSV lock errors**
```spl
# Use append mode (atomic writes)
| outputlookup append=t state_tracker  # ✓ Correct
| outputlookup state_tracker           # ✗ Wrong
```

**Case 3: Multiple alert instances**
```bash
# Check running searches
/opt/splunk/bin/splunk list search-jobs \
  | grep "002_VPN_Tunnel_Down"

# Should only show 1 active job per alert
```

### 3. Slack Messages Not Delivered

**Symptom:** Alerts trigger but Slack channel receives nothing

**Diagnosis:**
```spl
# Check Slack alert action logs
index=_internal source=*alert_actions.log action_name="slack"
| stats count by action_status, stderr
| sort - count
```

**Solutions:**

**Case 1: Webhook URL not configured**
```bash
# Verify configuration exists
cat local/alert_actions.conf
# Should contain:
# [slack]
# param.webhook_url = https://hooks.slack.com/services/...

# If missing, create it:
cat > local/alert_actions.conf <<EOF
[slack]
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EOF
```

**Case 2: Invalid webhook URL**
```bash
# Test webhook manually
curl -X POST "$(grep webhook_url local/alert_actions.conf | cut -d'=' -f2 | tr -d ' ')" \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message"}'

# Expected: "ok"
# If 404: Webhook URL expired or incorrect
# If 500: Slack service issue
```

**Case 3: Slack rate limiting**
```spl
# Check for 429 errors
index=_internal source=*alert_actions.log "429"
| stats count by _time

# If rate limited, adjust alert throttling
```

### 4. State Tracker Performance Issues

**Symptom:** Alerts slow to execute (>60 seconds)

**Diagnosis:**
```spl
# Check state tracker size
| inputlookup vpn_state_tracker
| stats count, dc(device), dc(component)

# Check search performance
index=_internal source=*metrics.log search_id=*002_VPN_Tunnel_Down*
| stats avg(total_run_time) as avg_runtime by savedsearch_name
```

**Solutions:**

**Case 1: State tracker too large (>10,000 rows)**
```spl
# Clean up old states (run monthly)
| inputlookup vpn_state_tracker
| where last_seen > relative_time(now(), "-30d")
| outputlookup vpn_state_tracker

# Expected: Reduce to <1,000 rows
```

**Case 2: Inefficient join**
```spl
# Use stats instead of join
| stats latest(*) as * by device, component
# Then compare with state tracker
```

### 5. Python Dependency Errors

**Symptom:** Alert actions fail with `ImportError` or `ModuleNotFoundError`

**Diagnosis:**
```bash
# Check bundled libraries exist
ls -la lib/python3/

# Test import manually
/opt/splunk/bin/splunk cmd python3 -c "import requests; print(requests.__version__)"
```

**Solutions:**

**Case 1: Missing libraries**
```bash
# Re-extract tarball (includes bundled dependencies)
cd /opt/splunk/etc/apps/
tar -xzf security_alert-v2.0.4-production.tar.gz
chown -R splunk:splunk security_alert
```

**Case 2: Python path issue**
```bash
# Verify bin/slack.py has path setup
grep -A 5 "sys.path.insert" bin/slack.py
# Should contain:
# LIB_DIR = os.path.join(APP_DIR, 'lib', 'python3')
# sys.path.insert(0, LIB_DIR)
```

### 6. CSV Lock Errors

**Symptom:** `Error in 'outputlookup': The lookup table is locked`

**Diagnosis:**
```spl
# Check concurrent writes
index=_internal source=*python.log "outputlookup" "locked"
| stats count by savedsearch_name
```

**Solutions:**

**Case 1: Using overwrite mode**
```spl
# Always use append mode
| outputlookup append=t state_tracker  # ✓ Atomic
| outputlookup state_tracker           # ✗ Exclusive lock
```

**Case 2: Multiple alerts writing simultaneously**
```bash
# Stagger alert schedules
# Instead of all at "* * * * *", use:
# Alert 1: "0,10,20,30,40,50 * * * *"
# Alert 2: "1,11,21,31,41,51 * * * *"
```

### 7. Message Formatting Issues

**Symptom:** Slack messages show raw data or truncated content

**Diagnosis:**
```spl
# Check formatted_message field
`fortigate_index` `logids_vpn_tunnel` earliest=-5m
| head 1
| table formatted_message

# Should be single-line, <200 chars
```

**Solutions:**

**Case 1: UUID not replaced**
```spl
# Add regex substitution
| rex mode=sed field=formatted_message "s/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/[UUID]/g"
```

**Case 2: Message too long**
```spl
# Truncate to 200 chars
| eval formatted_message = if(len(formatted_message) > 200, substr(formatted_message, 1, 197) + "...", formatted_message)
```

### 8. LogID Lookup Failures

**Symptom:** Alerts missing category, severity, or description

**Diagnosis:**
```spl
# Check lookup file loaded
| rest /services/data/transforms/lookups
| search title="fortigate_logid_notification_map"
| table title, filename

# Test lookup manually
| makeresults count=1
| eval logid=0101037124
| lookup fortigate_logid_notification_map logid OUTPUT category, severity, description
| table logid, category, severity, description
```

**Solutions:**

**Case 1: Lookup file missing**
```bash
# Verify file exists
ls -la lookups/fortigate_logid_notification_map.csv

# Should be 6091 lines
wc -l lookups/fortigate_logid_notification_map.csv
```

**Case 2: Lookup not registered**
```bash
# Check transforms.conf
grep -A 5 "fortigate_logid_notification_map" default/transforms.conf

# Should contain:
# [fortigate_logid_notification_map]
# filename = fortigate_logid_notification_map.csv
```

## Debug Mode

### Enable Verbose Logging

```bash
# Edit bin/slack.py
# Add at top of send_slack_message():
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Received payload: {payload}")
```

### Monitor Logs in Real-Time

```bash
# Splunk internal logs
tail -f /opt/splunk/var/log/splunk/python.log | grep security_alert

# Alert action logs
tail -f /opt/splunk/var/log/splunk/alert_actions.log | grep slack
```

### Test SPL Manually

```bash
# Run search from command line
/opt/splunk/bin/splunk search \
  '`fortigate_index` `logids_vpn_tunnel` earliest=-1h | head 10' \
  -app security_alert \
  -maxout 10
```

## Performance Tuning

### Reduce Search Load

```ini
# local/savedsearches.conf
[002_VPN_Tunnel_Down]
# Increase interval
cron_schedule = */5 * * * *  # Every 5 minutes instead of 1

# Narrow time window
dispatch.earliest_time = rt-5m  # Instead of rt-10m
```

### Optimize SPL

```spl
# Use stats instead of join
| stats latest(*) as * by device, component

# Filter early
`fortigate_index` `logids_vpn_tunnel`
| where isnotnull(vpnname)  # Filter before enrichment

# Avoid wildcards in base search
index=fw logid=0101037124  # ✓ Specific
index=fw logid=0101*        # ✗ Expensive
```

## Getting Help

### Collect Diagnostic Information

```bash
# Generate diagnostic bundle
cat > /tmp/diagnostic.sh <<'EOF'
#!/bin/bash
echo "=== App Status ==="
/opt/splunk/bin/splunk display app security_alert

echo "=== Alert Schedules ==="
grep -r "enableSched" etc/apps/security_alert/

echo "=== Recent Errors ==="
/opt/splunk/bin/splunk search 'index=_internal source=*security_alert* ERROR' -maxout 20

echo "=== State Tracker Stats ==="
for csv in etc/apps/security_alert/lookups/*_state_tracker.csv; do
  echo "$(basename $csv): $(wc -l < $csv) rows"
done
EOF

bash /tmp/diagnostic.sh > /tmp/security_alert_diagnostic.txt
```

### Report Issues

Include:
1. Diagnostic bundle output
2. Splunk version (`/opt/splunk/bin/splunk version`)
3. App version (`cat etc/apps/security_alert/app.manifest | grep version`)
4. Error messages (from splunkd.log)
5. Steps to reproduce

Submit to: https://github.com/qws941/splunk/issues
