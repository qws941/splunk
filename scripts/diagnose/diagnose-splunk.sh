#!/bin/bash
# Splunk 환경 진단 스크립트

echo "=========================================="
echo "Splunk 환경 진단"
echo "=========================================="
echo ""

# 1. Splunk 서비스 상태 체크
echo "1. Splunk 서비스 상태"
if systemctl is-active --quiet splunk 2>/dev/null; then
    echo "✅ Splunk 서비스 실행 중"
else
    echo "❌ Splunk 서비스 중지됨"
    echo "   → 실행: sudo systemctl start splunk"
fi
echo ""

# 2. 데이터 존재 확인
echo "2. FortiGate 데이터 확인 (index=fw)"
if command -v splunk &> /dev/null; then
    DATA_COUNT=$(splunk search "index=fw earliest=-1h" -auth admin:changeme 2>/dev/null | grep -c "^")
    if [ "$DATA_COUNT" -gt 0 ]; then
        echo "✅ 데이터 있음: $DATA_COUNT 건"
    else
        echo "❌ 데이터 없음 (최근 1시간)"
        echo "   → FortiGate에서 syslog 전송 확인 필요"
    fi
else
    echo "⚠️ splunk 명령어 없음 (Splunk 미설치 또는 PATH 설정 필요)"
fi
echo ""

# 3. Slack 앱 설치 확인
echo "3. Slack Alert 앱 설치 확인"
if [ -d "/opt/splunk/etc/apps/slack_alerts" ] || [ -d "/opt/splunk/etc/apps/SA-slack" ]; then
    echo "✅ Slack 앱 설치됨"
else
    echo "❌ Slack 앱 미설치"
    echo "   → Splunk Web → Apps → Find More Apps → 'Slack Notification Alert' 설치 필요"
fi
echo ""

# 4. 저장된 검색 (alerts) 확인
echo "4. 저장된 Alert 확인"
if [ -f "/opt/splunk/etc/users/admin/search/local/savedsearches.conf" ]; then
    ALERT_COUNT=$(grep -c "^\[FortiGate_.*_Alert\]" /opt/splunk/etc/users/admin/search/local/savedsearches.conf 2>/dev/null || echo "0")
    if [ "$ALERT_COUNT" -gt 0 ]; then
        echo "✅ FortiGate Alert 존재: $ALERT_COUNT 개"
    else
        echo "⚠️ FortiGate Alert 없음"
        echo "   → Web UI에서 수동 생성 필요"
    fi
else
    echo "⚠️ savedsearches.conf 없음"
    echo "   → Alert를 아직 생성하지 않음"
fi
echo ""

# 5. UDP 포트 리스닝 확인
echo "5. UDP 6514 포트 리스닝 확인"
if ss -ulnp 2>/dev/null | grep -q ":6514"; then
    echo "✅ UDP 6514 포트 리스닝 중"
else
    echo "❌ UDP 6514 포트 리스닝 안함"
    echo "   → Splunk Web → Settings → Data inputs → UDP → New Local UDP"
fi
echo ""

# 6. 환경변수 확인
echo "6. 환경변수 설정 확인"
if [ -f "/home/jclee/app/splunk/.env" ]; then
    if grep -q "your-fortianalyzer.example.com" /home/jclee/app/splunk/.env; then
        echo "❌ .env 파일에 placeholder 값 있음"
        echo "   → FAZ_HOST, SPLUNK_HEC_TOKEN, SLACK_BOT_TOKEN 실제 값으로 수정 필요"
    else
        echo "✅ .env 파일 설정됨"
    fi
else
    echo "⚠️ .env 파일 없음"
fi
echo ""

echo "=========================================="
echo "진단 완료"
echo "=========================================="
