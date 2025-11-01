#!/bin/bash
# 실제 FortiGate 로그 데이터 가져오기

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Splunk에서 실제 FortiGate 7.4.5 로그 조회"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Splunk 접속 정보 (환경변수에서 읽기)
SPLUNK_HOST="${SPLUNK_HOST:-splunk.jclee.me}"
SPLUNK_PORT="${SPLUNK_PORT:-8089}"
SPLUNK_USER="${SPLUNK_USER:-admin}"

if [ -z "$SPLUNK_PASSWORD" ]; then
  echo "❌ SPLUNK_PASSWORD 환경변수가 설정되지 않았습니다."
  echo ""
  echo "설정 방법:"
  echo "  export SPLUNK_PASSWORD='your-password'"
  echo "  ./get-actual-logs.sh"
  echo ""
  echo "또는 Splunk Web UI에서 직접 실행:"
  echo "  https://$SPLUNK_HOST:8000/app/search/search"
  echo ""
  echo "쿼리:"
  echo "  index=fw earliest=-1h | head 10 | table _time, devname, cfgpath, msg, _raw"
  exit 1
fi

echo "🔍 Splunk 연결 중: $SPLUNK_HOST:$SPLUNK_PORT"
echo ""

# 1. 실제 로그 10개 가져오기
QUERY='search index=fw earliest=-1h | head 10 | table _time, devname, type, logid, cfgpath, msg, _raw'

curl -k -u "$SPLUNK_USER:$SPLUNK_PASSWORD" \
  "https://$SPLUNK_HOST:$SPLUNK_PORT/services/search/jobs/export" \
  -d "search=$QUERY" \
  -d "output_mode=json" \
  -d "earliest_time=-1h" \
  -d "latest_time=now" 2>/dev/null | jq -r '.result | .[] | "\(.devname) | \(.cfgpath // "N/A") | \(._time) | \(._raw[0:200])"' | head -10

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ 실제 로그 조회 성공"
else
  echo ""
  echo "❌ 로그 조회 실패 - Splunk REST API 확인 필요"
fi
