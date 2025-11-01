#!/bin/bash
#
# Check Current Search Skip Statistics
# Shows real-time status after disabling searches
#

echo "📊 Splunk Search Skip Statistics (Real-time)"
echo "=============================================="
echo ""

# Get latest scheduler.log location
LOG_FILE="/opt/splunk/var/log/splunk/scheduler.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "⚠️  Splunk scheduler.log not found at: $LOG_FILE"
    echo ""
    echo "💡 Please provide the correct Splunk log path:"
    echo "   Example: /var/log/splunk/scheduler.log"
    exit 1
fi

echo "📁 Log file: $LOG_FILE"
echo ""

# Last 1000 lines analysis (recent 5-10 minutes)
echo "🔍 Analyzing last 1000 log entries..."
echo ""

tail -1000 "$LOG_FILE" | grep "SavedSplunker" | \
awk '
BEGIN {
    total = 0
    skipped = 0
    success = 0
}
/status=skipped/ {
    skipped++
    total++
    # Extract skip count if available
    if (match($0, /skipped_count=([0-9]+)/, arr)) {
        skip_count = arr[1]
        if (skip_count > max_skip_count) {
            max_skip_count = skip_count
            max_skip_search = $0
        }
    }
}
/status=success/ {
    success++
    total++
}
END {
    printf "📈 Statistics:\n"
    printf "   Total Searches: %d\n", total
    printf "   ✅ Success: %d (%.1f%%)\n", success, (success/total)*100
    printf "   ❌ Skipped: %d (%.1f%%)\n", skipped, (skipped/total)*100
    printf "\n"

    if (max_skip_count > 0) {
        printf "🔥 Highest Skip Count: %d\n", max_skip_count
        printf "   (Check if still problematic)\n"
    }

    printf "\n"
    if (skipped/total > 0.20) {
        printf "⚠️  WARNING: Skip rate > 20%% (Current: %.1f%%)\n", (skipped/total)*100
        printf "   Action needed: Disable more searches\n"
    } else if (skipped/total > 0.05) {
        printf "ℹ️  NOTICE: Skip rate > 5%% (Current: %.1f%%)\n", (skipped/total)*100
        printf "   Monitor closely\n"
    } else {
        printf "✅ HEALTHY: Skip rate < 5%% (Current: %.1f%%)\n", (skipped/total)*100
        printf "   System operating normally\n"
    }
}
'

echo ""
echo "🕐 Analysis time: $(date '+%Y-%m-%d %H:%M:%S')"
