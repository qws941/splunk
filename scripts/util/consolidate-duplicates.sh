#!/bin/bash
# File: scripts/consolidate-duplicates.sh
# Purpose: Consolidate duplicate CSV files to security_alert/lookups/
# Requires: Phase 2 legacy directories deleted first

set -e

cd /home/jclee/app/splunk

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Duplicate CSV Consolidation (Phase 3)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Compare files before deletion (sanity check)
echo "1. Comparing duplicate CSV files..."
echo ""

compare_files() {
    local file1=$1
    local file2=$2
    local basename=$(basename "$file2")

    if [ -f "$file1" ] && [ -f "$file2" ]; then
        if diff -q "$file1" "$file2" > /dev/null 2>&1; then
            echo "  ✅ $basename: Identical (safe to delete duplicate)"
        else
            echo "  ⚠️  $basename: DIFFERENT (review before delete)"
            echo "      Primary: $file1"
            echo "      Duplicate: $file2"
        fi
    elif [ ! -f "$file2" ]; then
        echo "  ℹ️  $basename: Already deleted or doesn't exist"
    fi
}

# Compare CSVs
compare_files "security_alert/lookups/fortigate_logid_notification_map.csv" "lookups/fortigate_logid_notification_map.csv"
compare_files "security_alert/lookups/abuseipdb_lookup.csv" "lookups/abuseipdb_lookup.csv"
compare_files "security_alert/lookups/auto_response_actions.csv" "lookups/auto_response_actions.csv"
compare_files "security_alert/lookups/severity_priority.csv" "lookups/severity_priority.csv"

echo ""
echo "2. Deleting duplicate CSVs from lookups/..."
echo ""

# Delete duplicates from lookups/ (root level)
delete_if_exists() {
    local file=$1
    local basename=$(basename "$file")
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "  ✅ Deleted: $basename"
    else
        echo "  ℹ️  Already deleted: $basename"
    fi
}

delete_if_exists "lookups/fortigate_logid_notification_map.csv"
delete_if_exists "lookups/abuseipdb_lookup.csv"
delete_if_exists "lookups/auto_response_actions.csv"
delete_if_exists "lookups/severity_priority.csv"

# Check if lookups/ directory is now empty or only has expected files
echo ""
echo "3. Checking remaining files in lookups/..."
echo ""

if [ -d "lookups" ]; then
    REMAINING_FILES=$(find lookups/ -type f | wc -l)
    if [ "$REMAINING_FILES" -eq 0 ]; then
        echo "  ℹ️  lookups/ is empty (can be deleted if not needed)"
    else
        echo "  ℹ️  lookups/ has $REMAINING_FILES remaining files:"
        find lookups/ -type f | sed 's/^/     - /'
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Phase 3 Complete: Duplicate CSVs consolidated"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "All CSV files now in: security_alert/lookups/"
echo ""
echo "Next steps:"
echo "  1. Review configs/: bash scripts/review-configs.sh"
echo "  2. Test deployment: tar -czf security_alert.tar.gz security_alert/"
echo "  3. Git commit: git add . && git commit -m 'chore: Consolidate duplicate CSVs'"
echo ""
