#!/bin/bash
# Deploy Simple Alert Dashboard and Saved Search to Splunk
# Method: Direct file copy (not REST API)

set -e

# Splunk paths
SPLUNK_HOME="${SPLUNK_HOME:-/opt/splunk}"
DASHBOARD_DIR="$SPLUNK_HOME/etc/apps/search/local/data/ui/views"
SAVEDSEARCH_DIR="$SPLUNK_HOME/etc/apps/search/local"

echo "🚀 Deploying Simple Alert to Splunk..."
echo "   Splunk Home: $SPLUNK_HOME"
echo ""

# Check if running as splunk user or root
if [ "$EUID" -ne 0 ] && [ "$(whoami)" != "splunk" ]; then
  echo "⚠️  Warning: Not running as root or splunk user"
  echo "   You may need to use: sudo ./scripts/deploy-simple-alert.sh"
  echo ""
fi

# 1. Deploy Dashboard (Simple XML)
echo "📊 Deploying dashboard: simple-alert-onoff.xml..."

# Create directory if not exists
mkdir -p "$DASHBOARD_DIR"

# Copy dashboard file
if cp configs/dashboards/simple-alert-onoff.xml "$DASHBOARD_DIR/simple_alert_onoff.xml"; then
  echo "   ✅ Dashboard copied to: $DASHBOARD_DIR/simple_alert_onoff.xml"
else
  echo "   ❌ Failed to copy dashboard"
  exit 1
fi

# 2. Deploy Saved Search
echo ""
echo "🔔 Deploying saved search: Test_Simple_Slack_Alert..."

# Copy savedsearches config
if cp configs/savedsearches-simple-test.conf "$SAVEDSEARCH_DIR/savedsearches.conf.d/simple-test.conf" 2>/dev/null || \
  cat configs/savedsearches-simple-test.conf >> "$SAVEDSEARCH_DIR/savedsearches.conf"; then
  echo "   ✅ Saved search added to: $SAVEDSEARCH_DIR/savedsearches.conf"
else
  echo "   ❌ Failed to copy saved search"
  exit 1
fi

# 3. Set permissions
echo ""
echo "🔐 Setting permissions..."
chown -R splunk:splunk "$DASHBOARD_DIR" "$SAVEDSEARCH_DIR" 2>/dev/null || true

# 4. Restart Splunk
echo ""
echo "🔄 Restarting Splunk..."
"$SPLUNK_HOME/bin/splunk" restart

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Deployment Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Deployed Files:"
echo "   Dashboard: $DASHBOARD_DIR/simple_alert_onoff.xml"
echo "   Saved Search: $SAVEDSEARCH_DIR/savedsearches.conf"
echo ""
echo "🌐 Dashboard URL:"
echo "   https://splunk.jclee.me:8000/app/search/simple_alert_onoff"
echo ""
echo "🧪 Test Steps:"
echo "   1. Wait ~30 seconds for Splunk to restart"
echo "   2. Open dashboard URL above"
echo "   3. Click 'Enable Alert' button"
echo "   4. Go to Settings → Searches → Test_Simple_Slack_Alert"
echo "   5. Click 'Run' to test"
echo "   6. Check Slack #splunk-alerts channel"
echo ""
