#!/bin/bash
# 간단 확인 스크립트

echo "=== FAZ/FMG → Splunk → Slack 체크 ==="
echo ""

# 1. 데이터 있나?
echo "1. index=fw 데이터:"
splunk search "index=fw sourcetype=fw_log | head 1" -auth admin:password 2>/dev/null | head -5

echo ""
echo "2. Critical 이벤트 (알림 발송 대상):"
splunk search "index=fw sourcetype=fw_log severity=critical | head 1" -auth admin:password 2>/dev/null | head -5

echo ""
echo "3. Slack 테스트 (지금 바로 발송):"
splunk search '| makeresults | sendalert slack param.channel="#splunk-alerts" param.message="테스트"' -auth admin:password 2>/dev/null

echo ""
echo "✅ Slack 채널 확인하세요!"
