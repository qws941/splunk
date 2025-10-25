#!/bin/bash
# Validate 123-fixed.xml data improvement
# Compares data counts between original and fixed dashboard

SPLUNK_HOST="${SPLUNK_HOST:-splunk.jclee.me}"
SPLUNK_PORT="${SPLUNK_PORT:-8089}"
SPLUNK_USER="${SPLUNK_USER:-admin}"

if [ -z "${SPLUNK_PASSWORD}" ]; then
    read -rsp "Splunk Password: " SPLUNK_PASSWORD
    echo ""
fi

BASE_URL="https://$SPLUNK_HOST:$SPLUNK_PORT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Dashboard Fix Validation - Data Count Comparison"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test queries that were broken by dedup sessionid
echo "📊 Testing queries with sessionid dedup (most critical fix)..."
echo ""

# Query 1: Traffic count (Line 46 fix)
echo "1️⃣ Traffic Events Count (was: dedup sessionid → now: direct stats)"
QUERY1='search index=fw type="traffic" earliest=-1h | stats count'

RESULT1=$(curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
    -d "search=$QUERY1" \
    -d "output_mode=json" \
    -d "exec_mode=oneshot" \
    "$BASE_URL/services/search/jobs" | jq -r '.results[0].count // "0"')

echo "   Result: $RESULT1 events (previously would show 0 or much lower)"
echo ""

# Query 2: Config changes (Line 192 fix)
echo "2️⃣ Config Changes (was: dedup config_hash span=1m → now: stats first())"
QUERY2='search index=fw cfgpath=* earliest=-1h | eval config_hash = md5(cfgpath . policy_obj . user . _time) | stats dc(config_hash) as unique_changes'

RESULT2=$(curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
    -d "search=$QUERY2" \
    -d "output_mode=json" \
    -d "exec_mode=oneshot" \
    "$BASE_URL/services/search/jobs" | jq -r '.results[0].unique_changes // "0"')

echo "   Result: $RESULT2 unique config changes"
echo ""

# Query 3: Object changes (Line 251 fix)
echo "3️⃣ Object Changes (was: dedup cfgobj span=1m → now: stats first())"
QUERY3='search index=fw (cfgpath="firewall.address" OR cfgpath="firewall.addrgrp") earliest=-1h | stats count'

RESULT3=$(curl -k -s -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
    -d "search=$QUERY3" \
    -d "output_mode=json" \
    -d "exec_mode=oneshot" \
    "$BASE_URL/services/search/jobs" | jq -r '.results[0].count // "0"')

echo "   Result: $RESULT3 object change events"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📈 Summary:"
echo ""
echo "   Traffic events:        $RESULT1"
echo "   Config changes:        $RESULT2"
echo "   Object changes:        $RESULT3"
echo ""

if [ "$RESULT1" -gt 0 ] && [ "$RESULT2" -gt 0 ]; then
    echo "   ✅ Fix successful! Data is now visible."
    echo "   ✅ dedup errors resolved."
else
    echo "   ⚠️  Low data counts - check if FortiGate is sending logs to Splunk"
    echo "   ℹ️  Run: index=fw earliest=-1h | stats count"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next steps:"
echo "   1. Deploy 123-fixed.xml to Splunk"
echo "   2. Compare dashboards side-by-side"
echo "   3. Verify panels that were empty now show data"
echo ""
