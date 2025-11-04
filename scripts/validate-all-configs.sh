#!/bin/bash
# Validate all Splunk configuration files using btool
# Usage: ./validate-all-configs.sh

set -euo pipefail

APP_DIR="/home/jclee/app/splunk/security_alert"
SPLUNK_HOME="${SPLUNK_HOME:-/opt/splunk}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 VALIDATING ALL CONFIGURATION FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if running on Splunk server
if [ ! -d "${SPLUNK_HOME}" ]; then
    echo "⚠️  Not on Splunk server. Doing local validation only."
    echo ""

    # Local file checks
    echo "📂 File Structure Check:"
    echo "  default/*.conf files:"
    ls -1 "${APP_DIR}/default"/*.conf 2>/dev/null || echo "    ❌ No conf files"

    echo "  README/*.spec files:"
    ls -1 "${APP_DIR}/README"/*.spec 2>/dev/null || echo "    ❌ No spec files"

    echo "  bin/*.py scripts:"
    ls -1 "${APP_DIR}/bin"/*.py 2>/dev/null || echo "    ❌ No Python scripts"

    echo "  lookups/*.csv files:"
    find "${APP_DIR}/lookups" -name "*.csv" 2>/dev/null | wc -l | awk '{print "    ✅ " $1 " CSV files"}'

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  For full btool validation, run on Splunk server"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
fi

# Function to validate config file
validate_config() {
    local conf_type="$1"
    local filter="${2:-}"

    echo "📋 ${conf_type}.conf:"

    local output
    if [ -n "${filter}" ]; then
        output=$("${SPLUNK_HOME}"/bin/splunk btool "${conf_type}" list "${filter}" --debug 2>&1 | \
            grep -iE "Invalid|Error|Warning|^\[${filter}\]|^param\." | head -20)
    else
        output=$("${SPLUNK_HOME}"/bin/splunk btool "${conf_type}" list --debug 2>&1 | \
            grep -iE "Invalid|Error|Warning" | head -20)
    fi

    if [ -z "${output}" ]; then
        echo "  ✅ No errors"
    else
        echo "${output}"
    fi
    echo ""
}

# Validate each config type
validate_config "alert_actions" "slack"
validate_config "savedsearches"
validate_config "transforms"
validate_config "props"
validate_config "macros"
validate_config "app"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Count errors in splunkd.log
echo "Recent errors in splunkd.log:"
tail -200 "${SPLUNK_HOME}/var/log/splunk/splunkd.log" | \
    grep -i "security_alert" | \
    grep -iE "error|invalid|fail" | \
    tail -10 || echo "  ✅ No recent errors"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
