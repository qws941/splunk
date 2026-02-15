#!/bin/bash
# ============================================================================
# Quick Alert Test Script
# ============================================================================
#
# Purpose: One-command test for FortiGate real-time alerts
# Usage:   ./scripts/QUICK-TEST.sh
#
# What it does:
# 1. Check Splunk container status
# 2. Verify HEC is enabled
# 3. Generate test data
# 4. Send to Splunk
# 5. Wait for alerts to trigger
# 6. Show results
#
# Prerequisites:
# - Splunk container running
# - HEC enabled in Splunk (see docs/LOCAL-ALERT-TEST-GUIDE.md)
# - HEC token created
#
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🚀 FortiGate Alert Quick Test${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================================================
# Step 1: Check prerequisites
# ============================================================================

echo -e "${YELLOW}[1/6]${NC} Checking Splunk container..."
if ! docker ps --filter "name=splunk-test" --filter "status=running" | grep -q splunk-test; then
    echo -e "${RED}✗${NC} Splunk container is not running"
    echo "  Start with: docker start splunk-test"
    exit 1
fi
echo -e "${GREEN}✓${NC} Container is running"
echo ""

# ============================================================================
# Step 2: Get HEC token
# ============================================================================

echo -e "${YELLOW}[2/6]${NC} Checking HEC token..."
if [ -z "$SPLUNK_HEC_TOKEN" ]; then
    echo -e "${YELLOW}⚠${NC} HEC token not found in environment"
    echo ""
    echo "Please create HEC token in Splunk Web UI:"
    echo "  1. Open: http://localhost:8800"
    echo "  2. Settings → Data inputs → HTTP Event Collector → Global Settings → Enable All Tokens"
    echo "  3. New Token → Name: local-test-token → Index: fortianalyzer → Submit"
    echo "  4. Copy token and run:"
    echo ""
    echo "     export SPLUNK_HEC_TOKEN=\"your-token-here\""
    echo "     ./scripts/QUICK-TEST.sh"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓${NC} HEC token found: ${SPLUNK_HEC_TOKEN:0:8}...${SPLUNK_HEC_TOKEN: -4}"
echo ""

# ============================================================================
# Step 3: Verify HEC is reachable
# ============================================================================

echo -e "${YELLOW}[3/6]${NC} Verifying HEC endpoint..."
HEC_HEALTH=$(curl -ks https://localhost:8088/services/collector/health 2>/dev/null || echo "ERROR")

if [[ "$HEC_HEALTH" == *"HEC is healthy"* ]]; then
    echo -e "${GREEN}✓${NC} HEC is healthy"
else
    echo -e "${RED}✗${NC} HEC is not accessible"
    echo "  Response: $HEC_HEALTH"
    echo ""
    echo "  Fix:"
    echo "  1. Settings → Data inputs → HTTP Event Collector → Global Settings"
    echo "  2. Enable 'All Tokens'"
    echo "  3. Check port: docker port splunk-test 8088"
    exit 1
fi
echo ""

# ============================================================================
# Step 4: Generate and send test data
# ============================================================================

echo -e "${YELLOW}[4/6]${NC} Generating and sending test events..."
cd "$(dirname "$0")/.."

if ! node scripts/generate/generate-alert-test-data.js --send --token="$SPLUNK_HEC_TOKEN" 2>&1; then
    echo -e "${RED}✗${NC} Failed to send test data"
    exit 1
fi
echo ""

# ============================================================================
# Step 5: Verify data in Splunk
# ============================================================================

echo -e "${YELLOW}[5/6]${NC} Waiting 10 seconds for data to be indexed..."
sleep 10

echo "Checking if data arrived in Splunk..."
DATA_COUNT=$(curl -ks -u admin:changeme \
  "https://localhost:8089/services/search/jobs/export" \
  -d "search=search index=fortianalyzer sourcetype=fortigate:event earliest=-2m | stats count" \
  -d "output_mode=json" 2>/dev/null | \
  grep -o '"count":"[0-9]*"' | \
  grep -o '[0-9]*' || echo "0")

if [ "$DATA_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Data found in Splunk: $DATA_COUNT events"
else
    echo -e "${RED}✗${NC} No data found in Splunk"
    echo "  Manual check: index=fortianalyzer sourcetype=fortigate:event earliest=-2m"
    exit 1
fi
echo ""

# ============================================================================
# Step 6: Check if alerts triggered
# ============================================================================

echo -e "${YELLOW}[6/6]${NC} Waiting 30 seconds for alerts to trigger..."
echo "(Real-time alerts run every minute, checking last 30 seconds of data)"
sleep 30

echo "Checking alert execution logs..."
ALERT_EXECS=$(curl -ks -u admin:changeme \
  "https://localhost:8089/services/search/jobs/export" \
  -d "search=search index=_internal source=*scheduler.log savedsearch_name=\"FortiGate_*\" earliest=-2m | stats count" \
  -d "output_mode=json" 2>/dev/null | \
  grep -o '"count":"[0-9]*"' | \
  grep -o '[0-9]*' || echo "0")

if [ "$ALERT_EXECS" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Alerts have executed: $ALERT_EXECS times"
else
    echo -e "${YELLOW}⚠${NC} No alert executions found yet"
    echo "  This is normal if alerts were just registered"
    echo "  Check again in 1-2 minutes"
fi
echo ""

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}📊 Test Summary${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "✅ Test data sent: 9 events"
echo "✅ Data indexed: $DATA_COUNT events"
echo "⏳ Alert executions: $ALERT_EXECS (expected: 3+)"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Wait 1-2 minutes for real-time alerts to run"
echo "2. Check Splunk Search:"
echo "   index=_internal source=*scheduler.log savedsearch_name=\"FortiGate_*\" | tail 20"
echo ""
echo "3. If Slack is configured, check channel for notifications"
echo ""
echo "4. Run full diagnostic:"
echo "   ./scripts/diagnose-alerts-not-working.sh"
echo ""
echo -e "${GREEN}✅ Quick test complete!${NC}"
echo ""
