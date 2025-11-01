#!/bin/bash
#
# List All Real-time Searches
# Shows how many Real-time searches exist
#

echo "🔍 Scanning All Real-time Searches"
echo "===================================="
echo ""

# This SPL query counts all Real-time searches
SPLUNK_CMD="/opt/splunk/bin/splunk"

if [ ! -f "$SPLUNK_CMD" ]; then
    echo "❌ Splunk not found at: $SPLUNK_CMD"
    echo ""
    echo "💡 대신 Splunk UI에서 실행하세요:"
    echo ""
    echo "| rest /services/saved/searches"
    echo "| search is_scheduled=1 realtime_schedule=1"
    echo "| stats count"
    exit 1
fi

echo "📊 Counting Real-time searches..."
echo ""

COUNT=$(sudo $SPLUNK_CMD search "| rest /services/saved/searches | search is_scheduled=1 realtime_schedule=1 disabled=0 | stats count" -auth admin:changeme 2>/dev/null | grep -oE '[0-9]+' | tail -1)

if [ -z "$COUNT" ]; then
    echo "⚠️  Could not get count automatically"
    echo ""
    echo "📋 Please run this in Splunk UI:"
    echo ""
    echo "| rest /services/saved/searches"
    echo "| search is_scheduled=1 realtime_schedule=1 disabled=0"
    echo "| stats count"
    echo ""
    exit 0
fi

echo "📈 Results:"
echo "   Total Real-time Searches: $COUNT"
echo "   Current Limit: 70"
echo "   Oversubscribed by: $((COUNT - 70))"
echo ""

if [ $COUNT -gt 100 ]; then
    echo "🔥 CRITICAL: $COUNT Real-time searches!"
    echo ""
    echo "💡 Recommendations:"
    echo "   1. Increase limit to 140+ (quick fix)"
    echo "   2. Convert unnecessary ones to Scheduled (best)"
    echo "   3. Disable unused searches"
elif [ $COUNT -gt 70 ]; then
    echo "⚠️  WARNING: $COUNT searches exceeds limit (70)"
    echo ""
    echo "💡 Need to either:"
    echo "   - Increase limit to $((COUNT + 10))"
    echo "   - OR disable $((COUNT - 60)) searches"
else
    echo "✅ HEALTHY: Under limit"
fi

echo ""
echo "🔧 Quick Actions:"
echo ""
echo "1. Increase limit:"
echo "   ./scripts/increase-realtime-limit.sh"
echo ""
echo "2. List top 20 searches:"
echo "   | rest /services/saved/searches"
echo "   | search is_scheduled=1 realtime_schedule=1 disabled=0"
echo "   | table title, author, app"
echo "   | head 20"
