#!/bin/bash
# Real-time Alert Troubleshooting Script
# Diagnoses why FortiGate alerts are not being sent to Slack
#
# Usage: ./scripts/diagnose-alerts-not-working.sh
#
# Checks 10 common failure points:
# 1. Splunk container running
# 2. Data flowing to index=fortianalyzer
# 3. Saved searches registered and enabled
# 4. Scheduler running real-time searches
# 5. Searches executing without errors
# 6. Slack plugin configured
# 7. Slack webhook URL valid
# 8. Alert triggers configured correctly
# 9. Suppression settings not over-blocking
# 10. Recent Slack notifications sent

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Real-time Alert Diagnostic Tool${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

SPLUNK_USER="admin"
SPLUNK_PASS="changeme"
SPLUNK_API="https://localhost:8089"

# Test 1: Container Running
echo -e "${YELLOW}[1/10]${NC} Checking Splunk container status..."
if docker ps --filter "name=splunk-test" --filter "status=running" | grep -q splunk-test; then
    echo -e "${GREEN}✓${NC} Container 'splunk-test' is running"
else
    echo -e "${RED}✗${NC} Container is not running"
    echo "  Fix: docker start splunk-test"
    exit 1
fi
echo ""

# Test 2: Data in index=fortianalyzer
echo -e "${YELLOW}[2/10]${NC} Checking for data in index=fortianalyzer (last 5 minutes)..."
DATA_COUNT=$(curl -ks -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
  "${SPLUNK_API}/services/search/jobs/export" \
  -d "search=search index=fortianalyzer earliest=-5m | stats count" \
  -d "output_mode=json" 2>/dev/null | \
  grep -o '"count":"[0-9]*"' | \
  grep -o '[0-9]*' || echo "0")

if [ "$DATA_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Data found: $DATA_COUNT events (last 5 minutes)"
else
    echo -e "${RED}✗${NC} No data in index=fortianalyzer"
    echo "  Possible causes:"
    echo "  - FortiAnalyzer not sending logs"
    echo "  - Wrong index name (should be 'fortianalyzer' not 'fw')"
    echo "  - Logs going to different sourcetype"
    echo ""
    echo "  Check: index=* earliest=-5m | stats count by index"
    exit 1
fi
echo ""

# Test 3: Saved Searches Registered
echo -e "${YELLOW}[3/10]${NC} Checking if FortiGate alerts are registered..."
ALERTS=$(curl -ks -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
  "${SPLUNK_API}/services/saved/searches" 2>/dev/null | \
  grep -o "FortiGate_.*_Alert" || echo "")

if [ -n "$ALERTS" ]; then
    echo -e "${GREEN}✓${NC} FortiGate alerts found:"
    echo "$ALERTS" | while read alert; do
        echo "    - $alert"
    done
else
    echo -e "${RED}✗${NC} No FortiGate alerts registered"
    echo "  Fix: Deploy savedsearches-fortigate-alerts.conf"
    echo "  Location: configs/savedsearches-fortigate-alerts.conf"
    exit 1
fi
echo ""

# Test 4: Alerts Enabled
echo -e "${YELLOW}[4/10]${NC} Checking if alerts are enabled..."
DISABLED_ALERTS=$(curl -ks -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
  "${SPLUNK_API}/services/saved/searches" 2>/dev/null | \
  grep -A 1 "FortiGate_.*_Alert" | \
  grep "disabled>1<" || echo "")

if [ -z "$DISABLED_ALERTS" ]; then
    echo -e "${GREEN}✓${NC} All FortiGate alerts are enabled"
else
    echo -e "${RED}✗${NC} Some alerts are disabled"
    echo "  Fix: Settings → Searches, reports, and alerts → Enable"
    echo "  Or: Edit savedsearches.conf → disabled = 0"
fi
echo ""

# Test 5: Real-time Schedule Active
echo -e "${YELLOW}[5/10]${NC} Checking real-time schedule configuration..."
RT_SCHEDULE=$(curl -ks -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
  "${SPLUNK_API}/services/saved/searches" 2>/dev/null | \
  grep -c "realtime_schedule>1<" || echo "0")

if [ "$RT_SCHEDULE" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Real-time scheduling enabled ($RT_SCHEDULE alerts)"
else
    echo -e "${RED}✗${NC} Real-time scheduling NOT enabled"
    echo "  Fix: Add to savedsearches.conf:"
    echo "    realtime_schedule = 1"
    echo "    cron_schedule = * * * * *"
fi
echo ""

# Test 6: Recent Alert Executions
echo -e "${YELLOW}[6/10]${NC} Checking recent alert execution logs (last 30 minutes)..."
EXEC_COUNT=$(curl -ks -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
  "${SPLUNK_API}/services/search/jobs/export" \
  -d "search=search index=_internal source=*scheduler.log savedsearch_name=\"FortiGate_*\" earliest=-30m | stats count" \
  -d "output_mode=json" 2>/dev/null | \
  grep -o '"count":"[0-9]*"' | \
  grep -o '[0-9]*' || echo "0")

if [ "$EXEC_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Alerts have been executed: $EXEC_COUNT times (last 30 min)"
else
    echo -e "${YELLOW}⚠${NC} No alert execution logs found"
    echo "  Possible causes:"
    echo "  - Alerts just registered (wait 1-2 minutes)"
    echo "  - Scheduler not running real-time searches"
    echo "  - Search errors preventing execution"
    echo ""
    echo "  Check: index=_internal source=*scheduler.log | tail 20"
fi
echo ""

# Test 7: Slack Plugin Installed
echo -e "${YELLOW}[7/10]${NC} Checking Slack plugin installation..."
if docker exec splunk-test ls -d /opt/splunk/etc/apps/slack_alerts 2>/dev/null >/dev/null; then
    echo -e "${GREEN}✓${NC} Slack Notification Alert plugin installed"
else
    echo -e "${RED}✗${NC} Slack plugin NOT found"
    echo "  Install from: plugins/slack-notification-alert_232.tgz"
    echo "  Then restart: docker restart splunk-test"
    exit 1
fi
echo ""

# Test 8: Slack Plugin Configured
echo -e "${YELLOW}[8/10]${NC} Checking Slack webhook configuration..."
if docker exec splunk-test test -f /opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Slack alert_actions.conf exists"

    WEBHOOK=$(docker exec splunk-test grep "webhook_url" /opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf 2>/dev/null || echo "")
    if [ -n "$WEBHOOK" ]; then
        echo -e "${GREEN}✓${NC} Webhook URL configured"
    else
        echo -e "${RED}✗${NC} Webhook URL NOT configured"
        echo "  Fix: Settings → Alert actions → Setup Slack Alerts"
        echo "  Enter Slack Webhook URL from: https://api.slack.com/apps"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} Slack not configured"
    echo "  Fix: Settings → Alert actions → Setup Slack Alerts"
    exit 1
fi
echo ""

# Test 9: Recent Slack Send Attempts
echo -e "${YELLOW}[9/10]${NC} Checking recent Slack notification attempts (last 30 minutes)..."
SLACK_LOGS=$(curl -ks -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
  "${SPLUNK_API}/services/search/jobs/export" \
  -d "search=search index=_internal source=*python.log* \"slack\" earliest=-30m | stats count" \
  -d "output_mode=json" 2>/dev/null | \
  grep -o '"count":"[0-9]*"' | \
  grep -o '[0-9]*' || echo "0")

if [ "$SLACK_LOGS" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Slack send attempts found: $SLACK_LOGS (last 30 min)"

    # Check for errors
    SLACK_ERRORS=$(curl -ks -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
      "${SPLUNK_API}/services/search/jobs/export" \
      -d "search=search index=_internal source=*python.log* \"slack\" (ERROR OR error OR failed) earliest=-30m | stats count" \
      -d "output_mode=json" 2>/dev/null | \
      grep -o '"count":"[0-9]*"' | \
      grep -o '[0-9]*' || echo "0")

    if [ "$SLACK_ERRORS" -gt 0 ]; then
        echo -e "${RED}✗${NC} Slack send ERRORS found: $SLACK_ERRORS"
        echo "  Check logs: index=_internal source=*python.log* \"slack\" ERROR"
        echo "  Common errors:"
        echo "    - Invalid webhook URL"
        echo "    - Network unreachable (firewall/air-gap)"
        echo "    - Channel not found (bot not invited)"
    else
        echo -e "${GREEN}✓${NC} No Slack send errors"
    fi
else
    echo -e "${YELLOW}⚠${NC} No Slack send attempts found"
    echo "  Possible causes:"
    echo "  - Alerts not triggering (no matching events)"
    echo "  - Slack action not enabled in alert definition"
    echo "  - Suppression preventing all notifications"
fi
echo ""

# Test 10: Alert Suppression Settings
echo -e "${YELLOW}[10/10]${NC} Checking alert suppression settings..."
echo "  Suppression prevents duplicate alerts. Check current settings:"
echo ""

for ALERT in "FortiGate_Config_Change_Alert" "FortiGate_Critical_Event_Alert" "FortiGate_HA_Event_Alert"; do
    SUPPRESS=$(curl -ks -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
      "${SPLUNK_API}/services/saved/searches/${ALERT}" 2>/dev/null | \
      grep -A 1 "alert.suppress.fields" | \
      tail -1 | \
      grep -o ">.*<" | \
      sed 's/[><]//g' || echo "none")

    PERIOD=$(curl -ks -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
      "${SPLUNK_API}/services/saved/searches/${ALERT}" 2>/dev/null | \
      grep -A 1 "alert.suppress.period" | \
      tail -1 | \
      grep -o ">.*<" | \
      sed 's/[><]//g' || echo "0")

    echo "  $ALERT:"
    echo "    Suppress Fields: $SUPPRESS"
    echo "    Suppress Period: ${PERIOD}s"
done
echo ""

# Summary
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Summary & Recommendations${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

if [ "$DATA_COUNT" -gt 0 ] && [ -n "$ALERTS" ] && [ "$RT_SCHEDULE" -gt 0 ]; then
    if [ "$SLACK_LOGS" -gt 0 ]; then
        echo -e "${GREEN}✅ Alert system is configured and attempting to send${NC}"
        echo ""
        echo "If Slack messages are not received:"
        echo "1. Check Slack bot invited to channel: /invite @bot-name"
        echo "2. Verify webhook URL correct: Settings → Alert actions"
        echo "3. Check firewall/network (air-gap): Test with curl"
        echo "4. Review Slack error logs: index=_internal source=*python.log* \"slack\" ERROR"
    else
        echo -e "${YELLOW}⚠ Alert system configured but not sending to Slack${NC}"
        echo ""
        echo "Likely causes:"
        echo "1. No events matching alert criteria (last 30 sec window)"
        echo "2. Suppression blocking all alerts"
        echo "3. Slack action not enabled in alert definition"
        echo ""
        echo "Manual test:"
        echo "  | sendalert slack param.channel=\"#security-firewall-alert\" param.message=\"Test\""
    fi
else
    echo -e "${RED}❌ Alert system not fully configured${NC}"
    echo ""
    if [ "$DATA_COUNT" -eq 0 ]; then
        echo "  → No data in index=fortianalyzer"
    fi
    if [ -z "$ALERTS" ]; then
        echo "  → FortiGate alerts not registered"
    fi
    if [ "$RT_SCHEDULE" -eq 0 ]; then
        echo "  → Real-time scheduling not enabled"
    fi
fi
echo ""

echo -e "${BLUE}Next Steps:${NC}"
echo "1. Fix any ${RED}✗${NC} errors above"
echo "2. Wait 1-2 minutes for scheduler to run"
echo "3. Generate test event (change FortiGate config)"
echo "4. Check Slack channel for notification"
echo "5. Review logs: index=_internal source=*scheduler.log savedsearch_name=\"FortiGate_*\""
echo ""
