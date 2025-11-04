#!/bin/bash
# 간단 배포: 사용자별 앱 (기능 제한됨)

SPLUNK_HOME="/opt/splunk"
USER="secmon"

echo "⚠️  경고: 이 방법은 기능이 제한됩니다!"
echo "   - Slack 알림 작동 안 함"
echo "   - 자동 field extraction 작동 안 함"
echo ""
echo "권장: deploy-hybrid.sh 사용"
echo ""
read -r -p "계속하시겠습니까? (y/N): " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "취소되었습니다."
    exit 0
fi

echo "📦 사용자별 앱 배포..."

# 사용자 디렉토리에 압축 해제
sudo tar -xzf security_alert.tar.gz -C ${SPLUNK_HOME}/etc/users/${USER}/

# 권한 설정
sudo chown -R splunk:splunk ${SPLUNK_HOME}/etc/users/${USER}/security_alert

# Splunk 재시작
sudo ${SPLUNK_HOME}/bin/splunk restart

echo "✅ 완료!"
echo ""
echo "위치: ${SPLUNK_HOME}/etc/users/${USER}/security_alert/"
echo ""
echo "❌ 작동 안 하는 것:"
echo "  - Slack 알림"
echo "  - 자동 field extraction"
echo "  - Alert 자동 실행"
