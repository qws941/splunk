#!/bin/bash
# FortiGate 7.4.5 Slack 알림 3개 자동 배포 (Real-time)
# Splunk REST API 사용
#
# ⚠️  Real-time 알림: CPU/메모리 사용량 높음 - 배포 후 반드시 모니터링
# 성능 확인: index=_internal source=*metrics.log group=search_concurrency

set -e

# ============================================================================
# 설정
# ============================================================================

SPLUNK_HOST="${SPLUNK_HOST:-splunk.jclee.me}"
SPLUNK_PORT="${SPLUNK_PORT:-8089}"
SPLUNK_USER="${SPLUNK_USER:-admin}"
SPLUNK_PASS="${SPLUNK_PASS}"

if [ -z "$SPLUNK_PASS" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  에러: SPLUNK_PASS 환경변수 필요"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "사용법:"
    echo "  SPLUNK_PASS='your-password' $0"
    echo ""
    exit 1
fi

BASE_URL="https://${SPLUNK_HOST}:${SPLUNK_PORT}"
AUTH="${SPLUNK_USER}:${SPLUNK_PASS}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 FortiGate Slack 알림 배포 시작 (Real-time)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "서버: ${SPLUNK_HOST}:${SPLUNK_PORT}"
echo "사용자: ${SPLUNK_USER}"
echo "채널: #security-firewall-alert"
echo ""

# ============================================================================
# Alert 1: Config Change (Real-time)
# ============================================================================

echo "📝 [1/3] FortiGate_Config_Change_Alert 생성 중..."

curl -k -u "$AUTH" \
    "$BASE_URL/servicesNS/nobody/search/saved/searches" \
    -d name="FortiGate_Config_Change_Alert" \
    -d description="FortiGate 설정 변경 시 Slack 알림 (Real-time)" \
    -d 'search=index=fw earliest=rt-30s latest=rt type=event subtype=system (logid=0100044546 OR logid=0100044547 OR cfgpath=*) | dedup devname, user, cfgpath, action | eval 변경유형 = case(match(cfgpath, "firewall\.policy"), "정책", match(cfgpath, "firewall\.address"), "주소객체", match(cfgpath, "firewall\.service"), "서비스객체", match(cfgpath, "system\."), "시스템설정", match(cfgpath, "log\."), "로그설정", 1=1, "기타설정") | eval 관리자 = coalesce(user, "system") | eval 접속 = coalesce(ui, "N/A") | eval 객체 = coalesce(cfgobj, "N/A") | eval 변경내용 = if(isnotnull(cfgattr) AND len(cfgattr)<200, cfgattr, "상세 내용 생략") | eval alert_msg = "*FortiGate " + 변경유형 + " 변경: " + action + "*" + " | " + "관리자: " + 관리자 + " | " + "장비: " + devname + " | " + "접속: " + 접속 + " | " + "객체: " + 객체 + " | " + "경로: " + cfgpath + " | " + "변경내용: " + 변경내용 | table alert_msg, devname, user, cfgpath' \
    -d is_scheduled="1" \
    -d realtime_schedule="1" \
    -d schedule_priority="highest" \
    -d alert.track="1" \
    -d counttype="number of events" \
    -d relation="greater than" \
    -d quantity="0" \
    -d action.slack="1" \
    -d action.slack.param.channel="#security-firewall-alert" \
    -d 'action.slack.param.message=$result.alert_msg$' \
    -d alert.suppress="1" \
    -d alert.suppress.period="15s" \
    -d 'alert.suppress.fields=user, cfgpath' \
    -d disabled="0" \
    > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ Alert 1 생성 완료"
else
    echo "   ⚠️  Alert 1 생성 실패 (이미 존재할 수 있음)"
fi

# ============================================================================
# Alert 2: Critical Event (Real-time)
# ============================================================================

echo "🚨 [2/3] FortiGate_Critical_Event_Alert 생성 중..."

curl -k -u "$AUTH" \
    "$BASE_URL/servicesNS/nobody/search/saved/searches" \
    -d name="FortiGate_Critical_Event_Alert" \
    -d description="FortiGate Critical/Error 이벤트 Slack 알림 (Real-time)" \
    -d 'search=index=fw earliest=rt-30s latest=rt type=event subtype=system (level=critical OR level=error OR level=emergency OR level=alert) logid!=0100044546 logid!=0100044547 NOT cfgpath=* | dedup devname, logid, level | eval 이벤트유형 = case(match(logid, "^0103"), "HA", match(logid, "^0104"), "시스템", match(logid, "^0105"), "인터페이스", match(logid, "^0106"), "성능", 1=1, "기타") | eval 설명 = coalesce(logdesc, msg, "N/A") | eval alert_msg = "*FortiGate " + upper(level) + " - " + 이벤트유형 + "*" + " | " + "장비: " + devname + " | " + "LogID: " + logid + " | " + "설명: " + 설명 | table alert_msg, devname, level, logid' \
    -d is_scheduled="1" \
    -d realtime_schedule="1" \
    -d schedule_priority="highest" \
    -d alert.track="1" \
    -d counttype="number of events" \
    -d relation="greater than" \
    -d quantity="0" \
    -d action.slack="1" \
    -d action.slack.param.channel="#security-firewall-alert" \
    -d 'action.slack.param.message=$result.alert_msg$' \
    -d alert.suppress="1" \
    -d alert.suppress.period="15s" \
    -d 'alert.suppress.fields=devname, logid' \
    -d disabled="0" \
    > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ Alert 2 생성 완료"
else
    echo "   ⚠️  Alert 2 생성 실패 (이미 존재할 수 있음)"
fi

# ============================================================================
# Alert 3: HA Event (Real-time)
# ============================================================================

echo "🔄 [3/3] FortiGate_HA_Event_Alert 생성 중..."

curl -k -u "$AUTH" \
    "$BASE_URL/servicesNS/nobody/search/saved/searches" \
    -d name="FortiGate_HA_Event_Alert" \
    -d description="FortiGate HA 이벤트 Slack 알림 (Real-time)" \
    -d 'search=index=fw earliest=rt-30s latest=rt type=event subtype=system logid=0103* NOT cfgpath=* | dedup devname, logid, level | eval 설명 = coalesce(logdesc, msg, "N/A") | eval alert_msg = "*FortiGate HA 이벤트*" + " | " + "장비: " + devname + " | " + "LogID: " + logid + " | " + "심각도: " + level + " | " + "설명: " + 설명 | table alert_msg, devname, logid, level' \
    -d is_scheduled="1" \
    -d realtime_schedule="1" \
    -d schedule_priority="highest" \
    -d alert.track="1" \
    -d counttype="number of events" \
    -d relation="greater than" \
    -d quantity="0" \
    -d action.slack="1" \
    -d action.slack.param.channel="#security-firewall-alert" \
    -d 'action.slack.param.message=$result.alert_msg$' \
    -d alert.suppress="1" \
    -d alert.suppress.period="15s" \
    -d 'alert.suppress.fields=devname, logid' \
    -d disabled="0" \
    > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ Alert 3 생성 완료"
else
    echo "   ⚠️  Alert 3 생성 실패 (이미 존재할 수 있음)"
fi

# ============================================================================
# 완료
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ FortiGate Slack 알림 배포 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 확인 방법:"
echo "  1. Web UI: Settings → Searches, reports, and alerts"
echo "  2. 'FortiGate_' 검색"
echo "  3. 3개 알림 확인 (Config Change, Critical Event, HA Event)"
echo ""
echo "⚠️  성능 모니터링 (필수):"
echo "  index=_internal source=*metrics.log group=search_concurrency"
echo "  | stats avg(active_hist_searches) by host"
echo ""
echo "  CPU 사용률 급증 시 → Real-time 비활성화 고려"
echo ""
echo "🧪 테스트:"
echo "  각 알림 클릭 → Run 버튼"
echo ""
echo "🎛️  ON/OFF:"
echo "  알림 클릭 → Enable 체크박스"
echo ""
