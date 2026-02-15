#!/bin/bash
#
# Disable High-Skip Real-time Searches
# Disables searches that are skipping excessively due to concurrency limits
#

set -e

# Splunk credentials from .env
SPLUNK_HOST="${SPLUNK_HOST:-localhost}"
SPLUNK_PORT="${SPLUNK_PORT:-8089}"
SPLUNK_USER="${SPLUNK_USERNAME:-admin}"
SPLUNK_PASS="${SPLUNK_PASSWORD:-changeme}"

BASE_URL="https://${SPLUNK_HOST}:${SPLUNK_PORT}"

echo "🔍 Disabling high-skip real-time searches..."
echo ""

# Array of searches to disable: "app:search_name"
SEARCHES=(
    "search:fortinet_fw_alert_object"
    "nextrade:FW_Object"
)

for search_spec in "${SEARCHES[@]}"; do
    IFS=':' read -r app search_name <<< "$search_spec"

    echo "📌 Processing: $search_name (app=$app)"

    # Check if search exists
    STATUS=$(curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASS" \
        "${BASE_URL}/servicesNS/nobody/${app}/saved/searches/${search_name}" \
        -w "%{http_code}" -o /dev/null)

    if [ "$STATUS" -eq 200 ]; then
        # Disable the search
        RESULT=$(curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASS" \
            "${BASE_URL}/servicesNS/nobody/${app}/saved/searches/${search_name}" \
            -d "is_scheduled=0" \
            -d "disabled=1" \
            -X POST)

        if echo "$RESULT" | grep -q "200 OK\|updated"; then
            echo "   ✅ Disabled: $search_name"
        else
            echo "   ⚠️  Failed to disable: $search_name"
            echo "   Response: $RESULT"
        fi
    elif [ "$STATUS" -eq 404 ]; then
        echo "   ℹ️  Not found (already deleted?): $search_name"
    else
        echo "   ❌ Error (HTTP $STATUS): $search_name"
    fi

    echo ""
done

echo "✅ Done!"
echo ""
echo "📊 Verify with:"
echo "   index=_internal source=*scheduler.log | stats count by savedsearch_name, status"
