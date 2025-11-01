#!/bin/bash
# FortiGate 7.4.5 로그 포맷 확인 스크립트

SPLUNK_HOST="${SPLUNK_HOST:-localhost}"
SPLUNK_PORT="${SPLUNK_PORT:-8089}"
SPLUNK_USER="${SPLUNK_USER:-admin}"
SPLUNK_PASS="${SPLUNK_PASS:-password}"

echo "=== FortiGate 7.4.5 로그 샘플 확인 ==="
echo ""

# Test 1: 기본 로그 존재 확인
echo "1. Index fw 로그 확인..."
curl -k -u "$SPLUNK_USER:$SPLUNK_PASS" \
  "https://$SPLUNK_HOST:$SPLUNK_PORT/services/search/jobs/export" \
  -d search='search index=fw earliest=-1h | head 5 | table _time, _raw' \
  -d output_mode=json 2>/dev/null | jq -r '.results[] | .["_raw"]' | head -5

echo ""
echo "2. Config change 로그 확인 (cfgpath)..."
curl -k -u "$SPLUNK_USER:$SPLUNK_PASS" \
  "https://$SPLUNK_HOST:$SPLUNK_PORT/services/search/jobs/export" \
  -d search='search index=fw cfgpath=* earliest=-24h | head 3 | table _time, _raw' \
  -d output_mode=json 2>/dev/null | jq -r '.results[] | .["_raw"]' | head -3

echo ""
echo "3. System event 로그 확인 (logid=0104*)..."
curl -k -u "$SPLUNK_USER:$SPLUNK_PASS" \
  "https://$SPLUNK_HOST:$SPLUNK_PORT/services/search/jobs/export" \
  -d search='search index=fw logid="0104*" earliest=-1h | head 3 | table _time, _raw' \
  -d output_mode=json 2>/dev/null | jq -r '.results[] | .["_raw"]' | head -3

echo ""
echo "4. 사용 가능한 필드 확인..."
curl -k -u "$SPLUNK_USER:$SPLUNK_PASS" \
  "https://$SPLUNK_HOST:$SPLUNK_PORT/services/search/jobs/export" \
  -d search='search index=fw earliest=-1h | head 1 | fieldsummary' \
  -d output_mode=json 2>/dev/null | jq -r '.results[] | "\(.field): \(.distinct_count) values"' | head -20

echo ""
echo "완료"
