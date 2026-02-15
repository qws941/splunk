#!/bin/bash
#
# Find Real-time Search Conversion Candidates
# Identifies searches that can be converted to Scheduled
#

echo "🎯 Real-time → Scheduled 전환 후보 찾기"
echo "========================================"
echo ""
echo "📋 Splunk UI에서 실행할 SPL 쿼리:"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣ 실행 빈도가 낮은 검색 (전환하기 좋음)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cat << 'SPL'
| rest /services/saved/searches
| search is_scheduled=1 realtime_schedule=1 disabled=0
| eval cron_interval = case(
    match(cron_schedule, "\*/1 "), "1분마다",
    match(cron_schedule, "\*/5 "), "5분마다",
    match(cron_schedule, "\*/10 "), "10분마다",
    match(cron_schedule, "\*/15 "), "15분마다",
    1=1, cron_schedule
)
| table title, eai:acl.app, cron_interval, next_scheduled_time
| rename title as "검색 이름", eai:acl.app as "앱", cron_interval as "실행 주기"
| sort "실행 주기"
SPL

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣ 최근 실행 기록이 없는 검색 (비활성화 고려)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
cat << 'SPL'
| rest /services/saved/searches
| search is_scheduled=1 realtime_schedule=1 disabled=0
| eval days_since_run = round((now() - strptime(next_scheduled_time, "%Y-%m-%dT%H:%M:%S%z")) / 86400, 1)
| where isnull(next_scheduled_time) OR days_since_run > 7
| table title, eai:acl.app, eai:acl.owner, updated
| rename title as "검색 이름", eai:acl.app as "앱", eai:acl.owner as "소유자"
SPL

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣ 스킵 횟수가 많은 검색 (우선 처리)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "이건 로그 파일에서 이미 확인:"
echo "  1. fortinet_fw_alert_object: 66,763 skips"
echo "  2. FW_Object: 730 skips"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 전환 기준 (Conversion Criteria)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Real-time → Scheduled 전환 OK:"
echo "  - Alert 검색 (5분 지연 허용 가능)"
echo "  - 통계/리포트 검색"
echo "  - 대시보드 백엔드 검색 (새로고침 간격 > 1분)"
echo ""
echo "❌ Real-time 유지 필요:"
echo "  - 실시간 모니터링 대시보드 (1초 단위 업데이트)"
echo "  - 보안 위협 즉시 탐지 (침입 차단 등)"
echo "  - SLA 요구사항 (< 1분 응답 필요)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 전환 방법 (How to Convert)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Splunk UI:"
echo "   Settings → Searches, reports, and alerts"
echo "   → 검색 선택 → Edit → Schedule"
echo "   → 'Real-time schedule' 체크 해제"
echo "   → 'Schedule' 체크 → Cron '*/5 * * * *' (5분마다)"
echo ""
echo "2. REST API (대량 전환):"
echo ""
cat << 'BASH'
for search in "검색1" "검색2" "검색3"; do
  curl -k -u admin:password \
    -d "realtime_schedule=0" \
    -d "cron_schedule=*/5 * * * *" \
    https://localhost:8089/servicesNS/nobody/search/saved/searches/$search
done
BASH

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 예상 효과 (Expected Impact)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Real-time 검색 30개 전환 시:"
echo "  - 슬롯 사용: 70/70 (100%) → 40/70 (57%)"
echo "  - 스킵률: 24.6% → 5% 이하"
echo "  - CPU 사용률: ~20% 감소"
echo ""
