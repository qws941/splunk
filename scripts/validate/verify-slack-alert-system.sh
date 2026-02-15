#!/bin/bash
# Slack Alert System Verification Script
# Tests: Python script, environment, Slack connectivity, message formatting
# Usage: ./verify-slack-alert-system.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Test results array
declare -a TEST_RESULTS

# Helper functions
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

print_test() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_pass() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    ((TESTS_PASSED++))
    TEST_RESULTS+=("PASS: $1")
}

print_fail() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    ((TESTS_FAILED++))
    TEST_RESULTS+=("FAIL: $1")
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Test 1: Python Version
print_header "Test 1: Python Environment"
print_test "Checking Python version"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    print_pass "Python available: $PYTHON_VERSION"
else
    print_fail "Python3 not found in PATH"
    exit 1
fi

# Test 2: Script Existence
print_header "Test 2: Python Script Files"
print_test "Checking slack-advanced-alert.py"

SCRIPT_PATH="$SCRIPT_DIR/slack-advanced-alert.py"
if [ -f "$SCRIPT_PATH" ]; then
    print_pass "Script exists: $SCRIPT_PATH"

    # Check if executable
    if [ -x "$SCRIPT_PATH" ]; then
        print_pass "Script is executable"
    else
        print_fail "Script is not executable (run: chmod +x $SCRIPT_PATH)"
    fi
else
    print_fail "Script not found: $SCRIPT_PATH"
fi

# Test 3: Environment Variables
print_header "Test 3: Environment Variables"
print_test "Checking required environment variables"

if [ -n "${SLACK_BOT_TOKEN:-}" ]; then
    # Mask token for security
    MASKED_TOKEN="${SLACK_BOT_TOKEN:0:10}...${SLACK_BOT_TOKEN: -4}"
    print_pass "SLACK_BOT_TOKEN is set: $MASKED_TOKEN"
else
    print_fail "SLACK_BOT_TOKEN not set"
    print_info "Set with: export SLACK_BOT_TOKEN='SLACK_BOT_TOKEN_PLACEHOLDER'"
fi

if [ -n "${SLACK_CHANNEL:-}" ]; then
    print_pass "SLACK_CHANNEL is set: $SLACK_CHANNEL"
else
    print_fail "SLACK_CHANNEL not set"
    print_info "Set with: export SLACK_CHANNEL='C09DSD6JH2Q'"
fi

# Test 4: Slack API Connectivity
print_header "Test 4: Slack API Connectivity"
print_test "Testing Slack auth.test endpoint"

if [ -n "${SLACK_BOT_TOKEN:-}" ]; then
    AUTH_RESPONSE=$(curl -s -X POST https://slack.com/api/auth.test \
        -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
        -H "Content-Type: application/json")

    if echo "$AUTH_RESPONSE" | grep -q '"ok":true'; then
        BOT_USER=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('user', 'unknown'))")
        BOT_TEAM=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('team', 'unknown'))")
        print_pass "Slack bot authenticated: @$BOT_USER in $BOT_TEAM"
    else
        ERROR_MSG=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', 'unknown'))")
        print_fail "Slack authentication failed: $ERROR_MSG"
    fi
else
    print_fail "Cannot test Slack connectivity - SLACK_BOT_TOKEN not set"
fi

# Test 5: Channel Access
print_header "Test 5: Slack Channel Access"
print_test "Checking channel permissions"

if [ -n "${SLACK_BOT_TOKEN:-}" ] && [ -n "${SLACK_CHANNEL:-}" ]; then
    CHANNEL_RESPONSE=$(curl -s -X POST https://slack.com/api/conversations.info \
        -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "channel=$SLACK_CHANNEL")

    if echo "$CHANNEL_RESPONSE" | grep -q '"ok":true'; then
        CHANNEL_NAME=$(echo "$CHANNEL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('channel', {}).get('name', 'unknown'))")
        print_pass "Channel accessible: #$CHANNEL_NAME ($SLACK_CHANNEL)"
    else
        ERROR_MSG=$(echo "$CHANNEL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', 'unknown'))")
        print_fail "Channel access failed: $ERROR_MSG"

        if [ "$ERROR_MSG" = "channel_not_found" ]; then
            print_info "Invite bot to channel: /invite @YourBot to #splunk-alerts"
        fi
    fi
else
    print_fail "Cannot test channel access - environment variables not set"
fi

# Test 6: Script Syntax
print_header "Test 6: Python Script Syntax"
print_test "Checking Python syntax"

if python3 -m py_compile "$SCRIPT_PATH" 2>/dev/null; then
    print_pass "Python syntax is valid"
else
    print_fail "Python syntax error detected"
fi

# Test 7: Test Message Send
print_header "Test 7: Test Message Send"
print_test "Sending test alert to Slack"

if [ -n "${SLACK_BOT_TOKEN:-}" ] && [ -n "${SLACK_CHANNEL:-}" ] && [ -f "$SCRIPT_PATH" ]; then
    # Create test data
    TEST_DATA=$(cat <<'EOF'
{
  "devname": "FG-VERIFY-TEST",
  "event_time": "2025-10-23 00:00:00",
  "status": "Active",
  "event_count": 999,
  "logdesc": "Verification test alert - automated script check",
  "priority": "LOW",
  "mode": "realtime",
  "threshold": 0
}
EOF
)

    # Send test alert
    if echo "$TEST_DATA" | python3 "$SCRIPT_PATH" 2>&1 | grep -q "successfully"; then
        print_pass "Test alert sent successfully"
        print_info "Check Slack channel #splunk-alerts for test message"
    else
        print_fail "Failed to send test alert"
    fi
else
    print_fail "Cannot send test alert - prerequisites not met"
fi

# Test 8: Configuration Files
print_header "Test 8: Configuration Files"
print_test "Checking dashboard and saved searches"

DASHBOARD_FILE="$PROJECT_ROOT/configs/dashboards/fortinet-management-dashboard.json"
SAVEDSEARCHES_FILE="$PROJECT_ROOT/configs/savedsearches-alerts.conf"

if [ -f "$DASHBOARD_FILE" ]; then
    print_pass "Dashboard file exists"

    # Check JSON syntax
    if python3 -c "import json; json.load(open('$DASHBOARD_FILE'))" 2>/dev/null; then
        print_pass "Dashboard JSON syntax is valid"
    else
        print_fail "Dashboard JSON syntax error"
    fi

    # Check for alert inputs
    ALERT_COUNT=$(grep -c "input_alert_" "$DASHBOARD_FILE" || true)
    if [ "$ALERT_COUNT" -ge 12 ]; then
        print_pass "Dashboard has $ALERT_COUNT alert inputs (expected: 13)"
    else
        print_fail "Dashboard has only $ALERT_COUNT alert inputs (expected: 13)"
    fi
else
    print_fail "Dashboard file not found: $DASHBOARD_FILE"
fi

if [ -f "$SAVEDSEARCHES_FILE" ]; then
    print_pass "Saved searches file exists"

    # Count saved searches
    SEARCH_COUNT=$(grep -c "^\[Fortinet_.*_Alert\]" "$SAVEDSEARCHES_FILE" || true)
    if [ "$SEARCH_COUNT" -eq 4 ]; then
        print_pass "Found 4 saved searches"
    else
        print_fail "Found $SEARCH_COUNT saved searches (expected: 4)"
    fi
else
    print_fail "Saved searches file not found: $SAVEDSEARCHES_FILE"
fi

# Test 9: Deployment Guide
print_header "Test 9: Documentation"
print_test "Checking deployment documentation"

DEPLOYMENT_GUIDE="$PROJECT_ROOT/docs/SLACK_ADVANCED_ALERT_DEPLOYMENT.md"
if [ -f "$DEPLOYMENT_GUIDE" ]; then
    print_pass "Deployment guide exists"

    GUIDE_SIZE=$(wc -l < "$DEPLOYMENT_GUIDE")
    print_info "Deployment guide: $GUIDE_SIZE lines"
else
    print_fail "Deployment guide not found: $DEPLOYMENT_GUIDE"
fi

# Test Summary
print_header "Test Summary"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo -e "${BLUE}📊 Total Tests:  $TOTAL_TESTS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED - System is ready for deployment!${NC}\n"
    exit 0
else
    echo -e "${RED}⚠️  SOME TESTS FAILED - Please fix issues before deployment${NC}\n"

    echo -e "${YELLOW}Failed Tests:${NC}"
    for result in "${TEST_RESULTS[@]}"; do
        if [[ $result == FAIL:* ]]; then
            echo -e "  ${RED}• ${result#FAIL: }${NC}"
        fi
    done
    echo ""

    exit 1
fi
