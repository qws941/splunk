#!/bin/bash
# FAZ/FMG Slack 알림 전체 테스트

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Slack 알림 전체 테스트 ===${NC}"
echo ""

# 1. 데이터 확인
echo -e "${YELLOW}1. 데이터 확인 (index=fw)${NC}"
DATA_COUNT=$(splunk search "index=fw sourcetype=fw_log earliest=-1h | stats count" -auth admin:password 2>/dev/null | grep -oP '\d+' || echo "0")
echo "데이터: ${DATA_COUNT}건"
if [ "$DATA_COUNT" -eq 0 ]; then
  echo -e "${RED}❌ 데이터 없음! FortiAnalyzer → Splunk 연동 확인 필요${NC}"
else
  echo -e "${GREEN}✅ 데이터 정상${NC}"
fi
echo ""

# 2. Slack Webhook 설정 확인
echo -e "${YELLOW}2. Slack Webhook 설정 확인${NC}"
if splunk show alert-actions slack 2>/dev/null | grep -q "webhook_url"; then
  echo -e "${GREEN}✅ Webhook 설정됨${NC}"
else
  echo -e "${RED}❌ Webhook 미설정${NC}"
  echo "   Settings → Alert actions → Slack → Webhook URL 입력"
fi
echo ""

# 3. 알림 존재 확인
echo -e "${YELLOW}3. 저장된 알림 확인${NC}"
ALERTS=(
  "FAZ_Critical_Alerts"
  "FMG_Policy_Install"
  "FMG_Policy_CRUD"
  "FMG_Admin_Login"
)

for alert in "${ALERTS[@]}"; do
  if splunk list search "$alert" 2>/dev/null | grep -q "$alert"; then
    ENABLED=$(splunk list search "$alert" 2>/dev/null | grep "disabled" | grep -oP '(0|1)' || echo "1")
    if [ "$ENABLED" -eq 0 ]; then
      echo -e "  ${GREEN}✅ $alert (활성)${NC}"
    else
      echo -e "  ${YELLOW}⚠️  $alert (비활성)${NC}"
    fi
  else
    echo -e "  ${RED}❌ $alert (없음)${NC}"
  fi
done
echo ""

# 4. 수동 테스트 알림 발송
echo -e "${YELLOW}4. 테스트 알림 발송${NC}"
read -p "Slack 테스트 메시지 보낼까요? (y/n): " SEND_TEST

if [[ "$SEND_TEST" == "y" || "$SEND_TEST" == "Y" ]]; then
  echo "테스트 메시지 발송 중..."
  splunk search '| makeresults | eval message="🧪 Splunk Slack 알림 테스트 - FAZ/FMG 연동 확인" | sendalert slack param.channel="#splunk-alerts" param.message=message' -auth admin:password 2>/dev/null
  echo -e "${GREEN}✅ 발송 완료! Slack 채널 확인하세요${NC}"
else
  echo "건너뛰기"
fi
echo ""

# 5. 최근 알림 발송 내역
echo -e "${YELLOW}5. 최근 알림 발송 내역 (24시간)${NC}"
splunk search 'index=_audit action="alert_fired" (savedsearch_name="FAZ_*" OR savedsearch_name="FMG_*") | eval time_str=strftime(_time, "%Y-%m-%d %H:%M:%S") | table time_str, savedsearch_name | head 10' -auth admin:password 2>/dev/null || echo "내역 없음"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}테스트 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "다음 단계:"
echo "1. Slack 채널에서 테스트 메시지 확인"
echo "2. 알림 활성화: Settings → Searches, reports, and alerts → Enable"
echo "3. 5-10분 후 실제 알림 발송 확인"
echo ""
