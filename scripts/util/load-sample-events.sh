#!/bin/bash
# Load FortiGate sample events into Splunk index=fw
# Usage: ./scripts/load-sample-events.sh

set -e

SPLUNK_HOME=${SPLUNK_HOME:-/opt/splunk}
SPLUNK_BIN="${SPLUNK_HOME}/bin/splunk"
SAMPLE_FILE="$(cd "$(dirname "$0")/.." && pwd)/sample-events.txt"
INDEX="fw"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Loading FortiGate Sample Events to Splunk"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if sample file exists
if [ ! -f "$SAMPLE_FILE" ]; then
    echo "❌ Error: Sample file not found at $SAMPLE_FILE"
    exit 1
fi

# Count events (excluding comments and empty lines)
EVENT_COUNT=$(grep -cvE '^(#|$)' "$SAMPLE_FILE")
echo "📋 Found $EVENT_COUNT sample events in: $SAMPLE_FILE"
echo ""

# Check if Splunk is running
if ! pgrep -x "splunkd" > /dev/null; then
    echo "⚠️  Warning: Splunk doesn't appear to be running"
    echo "   Start Splunk first: sudo systemctl start splunkd"
    exit 1
fi

# Check if index exists
if ! $SPLUNK_BIN list index | grep -q "^$INDEX\$"; then
    echo "⚠️  Warning: Index '$INDEX' not found"
    echo "   Create it in Splunk Web: Settings → Indexes → New Index"
    echo "   Or via CLI: $SPLUNK_BIN add index $INDEX -auth admin:changeme"
    exit 1
fi

echo "🚀 Loading events into index=$INDEX..."
echo ""

# Method 1: Using oneshot (recommended)
if command -v sudo &> /dev/null; then
    sudo "$SPLUNK_BIN" add oneshot "$SAMPLE_FILE" \
        -index "$INDEX" \
        -sourcetype "fortigate:syslog" \
        -auth admin:changeme

    echo ""
    echo "✅ Sample events loaded successfully!"
else
    echo "⚠️  sudo not available, trying without sudo..."
    "$SPLUNK_BIN" add oneshot "$SAMPLE_FILE" \
        -index "$INDEX" \
        -sourcetype "fortigate:syslog" \
        -auth admin:changeme || {
        echo "❌ Failed to load events. Try running with sudo."
        exit 1
    }
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Verify Data in Splunk"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Run these searches in Splunk:"
echo ""
echo "1. Check total events:"
echo "   index=fw | stats count"
echo ""
echo "2. View by LogID:"
echo "   index=fw | stats count by logid | sort -count"
echo ""
echo "3. Test Config Change alert:"
echo "   | savedsearch FortiGate_Config_Change"
echo ""
echo "4. Test all alerts:"
echo "   | savedsearch FortiGate_Config_Change"
echo "   | savedsearch FortiGate_Interface_Status"
echo "   | savedsearch FortiGate_HA_Status"
echo "   | savedsearch FortiGate_Device_Events"
echo "   | savedsearch FortiGate_System_Resource"
echo "   | savedsearch FortiGate_Admin_Activity"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Done!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
