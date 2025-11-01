#!/bin/bash
# Syslog Setup Verification Script
# Run this AFTER completing Splunk UDP input and FortiAnalyzer syslog configuration
#
# Usage: ./scripts/verify-syslog-setup.sh
#
# Checks:
# 1. Splunk container running and healthy
# 2. UDP port 9514 exposed and listening
# 3. Splunk UDP input configured
# 4. Data flowing to index=fw
# 5. FortiGate Add-on active (for field parsing)
# 6. Recent logs received

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Splunk Syslog Setup Verification${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Test 1: Container Status
echo -e "${YELLOW}[1/6]${NC} Checking Splunk container status..."
if docker ps --filter "name=splunk-test" --filter "status=running" | grep -q splunk-test; then
    echo -e "${GREEN}✓${NC} Container 'splunk-test' is running"

    # Check health status
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' splunk-test 2>/dev/null || echo "unknown")
    if [ "$HEALTH" = "healthy" ]; then
        echo -e "${GREEN}✓${NC} Container health: healthy"
    else
        echo -e "${YELLOW}⚠${NC} Container health: $HEALTH (may still be starting)"
    fi
else
    echo -e "${RED}✗${NC} Container 'splunk-test' is not running"
    echo "  Start with: docker start splunk-test"
    exit 1
fi
echo ""

# Test 2: UDP Port Exposed
echo -e "${YELLOW}[2/6]${NC} Checking UDP port 9514 exposure..."
if docker port splunk-test | grep -q "9514/udp"; then
    PORT_MAP=$(docker port splunk-test 9514/udp)
    echo -e "${GREEN}✓${NC} UDP port 9514 is exposed: $PORT_MAP"
else
    echo -e "${RED}✗${NC} UDP port 9514 is NOT exposed in container"
    echo "  Container needs to be recreated with: -p 9514:9514/udp"
    exit 1
fi
echo ""

# Test 3: UDP Port Listening Inside Container
echo -e "${YELLOW}[3/6]${NC} Checking if Splunk is listening on UDP 9514..."
if docker exec splunk-test netstat -uln 2>/dev/null | grep -q ":9514"; then
    echo -e "${GREEN}✓${NC} Splunk is listening on UDP 9514"
else
    echo -e "${RED}✗${NC} Splunk is NOT listening on UDP 9514"
    echo "  Configure UDP input in Splunk Web UI:"
    echo "  Settings → Data inputs → UDP → New Local UDP"
    echo "  Port: 9514, Index: fw, Sourcetype: Automatic"
    exit 1
fi
echo ""

# Test 4: FortiGate Add-on Installed
echo -e "${YELLOW}[4/6]${NC} Checking FortiGate Add-on installation..."
if docker exec splunk-test ls -d /opt/splunk/etc/apps/Splunk_TA_fortinet_fortigate 2>/dev/null >/dev/null; then
    echo -e "${GREEN}✓${NC} FortiGate Add-on (TA) is installed"
else
    echo -e "${YELLOW}⚠${NC} FortiGate Add-on NOT found"
    echo "  Install from: plugins/fortinet-fortigate-add-on-for-splunk_169.tgz"
fi
echo ""

# Test 5: Recent Data in index=fw
echo -e "${YELLOW}[5/6]${NC} Checking for recent data in index=fw (last 5 minutes)..."
echo "  This requires Splunk REST API access..."

# Try to query via REST API (may fail if default password)
COUNT=$(curl -ks -u "admin:changeme" \
  "https://localhost:8089/services/search/jobs/export" \
  -d "search=search index=fw earliest=-5m | stats count" \
  -d "output_mode=json" 2>/dev/null | \
  grep -o '"count":"[0-9]*"' | \
  grep -o '[0-9]*' || echo "0")

if [ "$COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Data found in index=fw: $COUNT events (last 5 minutes)"
else
    echo -e "${YELLOW}⚠${NC} No data found in index=fw (last 5 minutes)"
    echo ""
    echo "  Possible reasons:"
    echo "  1. FortiAnalyzer syslog forwarding not configured yet"
    echo "  2. FortiAnalyzer connectivity test failed"
    echo "  3. Logs not matching index routing"
    echo ""
    echo "  Check FortiAnalyzer CLI:"
    echo "  execute log test-connectivity splunk-syslog"
    echo ""
    echo "  If test succeeds but no data, check Splunk index routing:"
    echo "  Settings → Data inputs → UDP → 9514 → Index should be 'fw'"
fi
echo ""

# Test 6: Field Parsing (if data exists)
if [ "$COUNT" -gt 0 ]; then
    echo -e "${YELLOW}[6/6]${NC} Checking field parsing (devname, logid)..."

    FIELDS=$(curl -ks -u "admin:changeme" \
      "https://localhost:8089/services/search/jobs/export" \
      -d "search=search index=fw earliest=-5m | stats count by devname, logid | head 1" \
      -d "output_mode=json" 2>/dev/null | \
      grep -o '"devname"' || echo "")

    if [ -n "$FIELDS" ]; then
        echo -e "${GREEN}✓${NC} FortiGate fields are being extracted (devname, logid found)"
    else
        echo -e "${YELLOW}⚠${NC} FortiGate fields NOT being extracted"
        echo "  FortiGate Add-on may need restart:"
        echo "  docker restart splunk-test"
    fi
else
    echo -e "${YELLOW}[6/6]${NC} Skipping field parsing check (no data yet)"
fi
echo ""

# Summary
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

if [ "$COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ SUCCESS:${NC} Syslog pipeline is working!"
    echo ""
    echo "Next steps:"
    echo "1. Configure Slack webhook in Splunk (Settings → Alert actions)"
    echo "2. Run diagnostic queries: docs/REALTIME-ALERT-DIAGNOSTIC-GUIDE.md"
    echo "3. Verify real-time alerts are triggering"
    echo ""
    echo "Helpful queries:"
    echo "  index=fw earliest=-5m | stats count by host, sourcetype, devname"
    echo "  index=fw earliest=-1h | timechart span=5m count"
else
    echo -e "${YELLOW}⚠ INCOMPLETE:${NC} Container and UDP input configured, but no data yet"
    echo ""
    echo "Complete these manual steps:"
    echo ""
    echo "1. Configure FortiAnalyzer Syslog Forwarding:"
    echo "   - Log & Report → Log Forwarding → Create New → Generic Syslog"
    echo "   - Server: $(hostname -I | awk '{print $1}' || echo '<Splunk IP>')"
    echo "   - Port: 9514"
    echo "   - Protocol: UDP"
    echo "   - Format: RFC 5424"
    echo "   - Enable: Traffic, Event, UTM logs"
    echo ""
    echo "2. Test FortiAnalyzer connectivity (CLI):"
    echo "   execute log test-connectivity splunk-syslog"
    echo ""
    echo "3. Wait 1-2 minutes, then re-run this script:"
    echo "   ./scripts/verify-syslog-setup.sh"
    echo ""
    echo "Guide: docs/SYSLOG-SETUP-COMPLETE-GUIDE.md"
fi
echo ""
