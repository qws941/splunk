#!/bin/bash
# Quick deployment script for real-time Slack alerts
# Created: 2025-10-31

set -e

echo "🚀 Deploying Real-time Slack Alert Configurations..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  Please run with sudo: sudo bash $0"
    exit 1
fi

# Verify Splunk is installed
if [ ! -d "/opt/splunk" ]; then
    echo "❌ Splunk not found at /opt/splunk"
    exit 1
fi

# Verify source files exist
if [ ! -f "configs/savedsearches-fortigate-alerts.conf" ]; then
    echo "❌ savedsearches-fortigate-alerts.conf not found"
    exit 1
fi

if [ ! -f "configs/alert_actions.conf" ]; then
    echo "❌ alert_actions.conf not found"
    exit 1
fi

# Check for placeholder token
if grep -q "xoxb-your-slack-bot-token" configs/alert_actions.conf; then
    echo "⚠️  WARNING: Slack token is still placeholder!"
    echo "   Edit configs/alert_actions.conf line 17 first"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create app directory if not exists
mkdir -p /opt/splunk/etc/apps/fortigate/local

# Deploy configurations
echo "📋 Copying alert_actions.conf..."
cp configs/alert_actions.conf /opt/splunk/etc/apps/fortigate/local/

echo "📋 Copying savedsearches.conf..."
cp configs/savedsearches-fortigate-alerts.conf /opt/splunk/etc/apps/search/local/savedsearches.conf

# Set permissions
chown -R splunk:splunk /opt/splunk/etc/apps/fortigate/local/
chown splunk:splunk /opt/splunk/etc/apps/search/local/savedsearches.conf

echo "🔄 Restarting Splunk..."
/opt/splunk/bin/splunk restart

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📌 Next Steps:"
echo "1. Verify saved searches loaded:"
echo "   /opt/splunk/bin/splunk search '| rest /services/saved/searches | search title=FortiGate_* | table title'"
echo ""
echo "2. Test real-time alert manually:"
echo "   /opt/splunk/bin/splunk search '| savedsearch FortiGate_Config_Change_Alert'"
echo ""
echo "3. Invite Slack bot to channel:"
echo "   In Slack: /invite @Splunk FortiGate Alert to #security-firewall-alert"
echo ""
echo "4. Monitor Splunk scheduler logs:"
echo "   tail -f /opt/splunk/var/log/splunk/scheduler.log | grep FortiGate_"
