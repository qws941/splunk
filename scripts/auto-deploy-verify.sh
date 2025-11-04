#!/bin/bash
# Auto deploy and verify Splunk app
# Usage: ./auto-deploy-verify.sh [splunk-server]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE="${SCRIPT_DIR}/../release/security_alert.tar.gz"
SPLUNK_SERVER="${1:-splunk-server}"
SPLUNK_USER="${SPLUNK_USER:-splunk}"
SPLUNK_HOME="${SPLUNK_HOME:-/opt/splunk}"

echo "🚀 Deploying to ${SPLUNK_SERVER}..."

# 1. Copy package
echo "📦 Copying package..."
scp "${PACKAGE}" "${SPLUNK_SERVER}:/tmp/" || {
    echo "❌ Failed to copy package"
    exit 1
}

# 2. Deploy and verify on remote server
echo "🔧 Deploying and verifying..."
ssh "${SPLUNK_SERVER}" bash << 'EOF'
set -euo pipefail

SPLUNK_HOME="/opt/splunk"
APP_NAME="security_alert"
APP_PATH="${SPLUNK_HOME}/etc/apps/${APP_NAME}"

echo "  → Removing old app..."
sudo rm -rf "${APP_PATH}"

echo "  → Extracting new app..."
sudo tar -xzf /tmp/security_alert.tar.gz -C "${SPLUNK_HOME}/etc/apps/"

echo "  → Setting permissions..."
sudo chown -R splunk:splunk "${APP_PATH}"
sudo chmod 755 "${APP_PATH}/bin"/*.py

echo "  → Restarting Splunk..."
sudo ${SPLUNK_HOME}/bin/splunk restart

echo "⏳ Waiting for Splunk to start..."
sleep 10

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 BTOOL VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# btool alert_actions check
echo ""
echo "📋 Alert Actions Configuration:"
${SPLUNK_HOME}/bin/splunk btool alert_actions list slack --debug 2>&1 | grep -E "^\[slack\]|^param\.|^is_custom|^label|^python\.version|Invalid|Error" || echo "✅ No errors"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📂 FILE STRUCTURE CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Python scripts:"
ls -lh "${APP_PATH}/bin"/*.py | awk '{print $1, $9}'

echo ""
echo "Config files:"
ls -1 "${APP_PATH}/default"/*.conf 2>/dev/null || echo "No conf files"

echo ""
echo "Spec file:"
ls -lh "${APP_PATH}/README"/*.spec 2>/dev/null || echo "❌ No spec file"

echo ""
echo "CSV lookups:"
ls -1 "${APP_PATH}/lookups"/*.csv | wc -l | awk '{print $1 " CSV files"}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️ ERROR CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Recent errors in splunkd.log:"
tail -100 "${SPLUNK_HOME}/var/log/splunk/splunkd.log" | grep -i "security_alert\|slack" | grep -iE "error|warn|invalid|fail" | tail -5 || echo "✅ No recent errors"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOYMENT COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Setup URL: https://your-splunk:8000/en-US/manager/security_alert/apps/local/security_alert/setup"
echo ""

EOF

echo ""
echo "🎉 Done!"
