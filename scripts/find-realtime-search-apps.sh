#!/bin/bash
#
# Find Apps Creating Real-time Searches
# Shows which apps/plugins are the culprits
#

echo "🔍 Analyzing Real-time Searches by App"
echo "======================================"
echo ""
echo "📊 Run this SPL query in Splunk UI:"
echo ""
echo "| rest /services/saved/searches"
echo "| search is_scheduled=1 realtime_schedule=1 disabled=0"
echo "| stats count by eai:acl.app"
echo "| rename eai:acl.app as App"
echo "| sort -count"
echo ""
echo "🎯 To find the actual search names:"
echo ""
echo "| rest /services/saved/searches"
echo "| search is_scheduled=1 realtime_schedule=1 disabled=0"
echo "| table title, eai:acl.app, eai:acl.owner, cron_schedule"
echo "| rename eai:acl.app as App, eai:acl.owner as Owner, title as \"Search Name\""
echo "| sort App"
echo ""
echo "💡 Possible culprits to look for:"
echo "   - Fortinet apps (fortinet_*)"
echo "   - Monitoring apps (*_monitoring, *_metrics)"
echo "   - Alert apps (*_alert, *_alerts)"
echo "   - Custom apps (nextrade, search, etc.)"
