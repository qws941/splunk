#!/bin/bash
#
# Find Top Skipped Searches
# Identifies searches with highest skip counts
#

echo "🔍 Top 10 Most Skipped Searches (24h)"
echo "======================================"
echo ""

# Parse the log data from files
if [ -f "/home/jclee/1.txt" ]; then
    LOG_FILE="/home/jclee/1.txt"
elif [ -f "/home/jclee/2.x2x" ]; then
    LOG_FILE="/home/jclee/2.x2x"
else
    echo "❌ Log file not found"
    exit 1
fi

echo "📁 Analyzing: $LOG_FILE"
echo ""

grep "status=skipped" "$LOG_FILE" | \
grep -oE 'savedsearch_name="[^"]+"|skipped_count=[0-9]+' | \
paste - - | \
sed 's/savedsearch_name="//; s/" skipped_count=/\t/' | \
sort -t$'\t' -k2 -rn | \
head -10 | \
awk -F'\t' '
BEGIN {
    print "Rank | Search Name                                    | Skip Count"
    print "-----+------------------------------------------------+-----------"
}
{
    printf "%-4d | %-46s | %s\n", NR, $1, $2
}
END {
    print ""
    print "💡 Recommendation:"
    print "   - Disable searches with skip_count > 1,000"
    print "   - Convert to Scheduled if still needed"
}
'

echo ""
echo "🔧 Next Steps:"
echo "   1. Go to: Settings → Searches, reports, and alerts"
echo "   2. Search for the names above"
echo "   3. Click search name → Disable button"
