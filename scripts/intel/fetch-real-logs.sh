#!/bin/bash
# 실제 FortiGate 로그 1개만 가져오기 (빠른 확인)

source .env 2>/dev/null

SPLUNK_URL="${SPLUNK_HEC_URL:-https://splunk.jclee.me:8088}"
SPLUNK_HOST=$(echo "$SPLUNK_URL" | sed 's|https\?://||' | cut -d: -f1)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 실제 FortiGate 로그 확인 (최근 1시간)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Splunk: $SPLUNK_HOST"
echo ""

if [ -z "$SPLUNK_HEC_TOKEN" ]; then
  echo "⚠️  .env에서 Splunk 접속 정보를 찾을 수 없습니다."
  echo ""
  echo "📋 Splunk Web UI에서 직접 실행하세요:"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  cat << 'QUERY'
## 1. 실제 로그 1개 확인 (모든 필드 표시)
index=fw earliest=-1h
| head 1
| transpose
| rename column AS "필드명", "row 1" AS "값"
| where isnotnull(값)

## 2. 설정 변경 로그 실제 데이터 (최근 10개)
index=fw earliest=-1h (config OR policy OR address OR service OR cfgpath=*)
| head 10
| table _time, devname, user, cfgpath, action, msg, _raw

## 3. cfgpath 있는 로그만
index=fw earliest=-1h cfgpath=*
| head 10
| table _time, devname, cfgpath, user, msg
QUERY
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "위 쿼리를 Splunk Search에 붙여넣기해서 실행하세요."
  echo ""
  exit 0
fi

echo "✅ Splunk 연결 정보 확인됨"
echo ""
echo "📌 다음 쿼리를 Splunk에서 실행하세요:"
echo "   (REST API로는 복잡한 쿼리 실행이 제한적입니다)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat << 'QUERY'
index=fw earliest=-1h
| head 10
| table _time, devname, type, subtype, logid, cfgpath, user, action, msg, logdesc, _raw
QUERY
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
