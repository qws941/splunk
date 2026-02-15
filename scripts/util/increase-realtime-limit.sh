#!/bin/bash
#
# Increase Splunk Real-time Search Limit
# Changes from 70 to 140 concurrent searches
#

set -e

LIMITS_FILE="/opt/splunk/etc/system/local/limits.conf"

echo "🔧 Increasing Splunk Real-time Search Limit"
echo "==========================================="
echo ""

# Check if file exists
if [ ! -f "$LIMITS_FILE" ]; then
    echo "📁 Creating new limits.conf..."
    sudo mkdir -p /opt/splunk/etc/system/local
fi

echo "📝 Backing up current limits.conf..."
if [ -f "$LIMITS_FILE" ]; then
    sudo cp "$LIMITS_FILE" "$LIMITS_FILE.backup.$(date +%Y%m%d-%H%M%S)"
fi

echo "✏️  Modifying limits.conf..."
cat <<'EOF' | sudo tee -a "$LIMITS_FILE"

[realtime]
# Increased from default (max_searches_per_cpu = 1)
# Default: 70 concurrent searches (70 CPUs * 1)
# New: 140 concurrent searches (70 CPUs * 2)
max_searches_per_cpu = 2

# Alternative: Set absolute number
# max_searches = 140
EOF

echo ""
echo "✅ limits.conf updated!"
echo ""
echo "📊 New Settings:"
echo "   Real-time search limit: 70 → 140"
echo ""
echo "⚠️  IMPORTANT: Splunk restart required!"
echo ""
read -p "Restart Splunk now? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Restarting Splunk..."
    sudo /opt/splunk/bin/splunk restart
    echo "✅ Done! Real-time limit increased to 140"
else
    echo "ℹ️  Please restart Splunk manually:"
    echo "   sudo /opt/splunk/bin/splunk restart"
fi
