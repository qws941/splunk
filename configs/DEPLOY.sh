#!/bin/bash
# FortiGate Alerts 한 번에 배포

echo "📦 FortiGate Block Kit Alerts 배포 중..."

# 1. 통합 conf 파일 배포 (두 위치로 복사)
sudo cp configs/fortigate-alerts-all.conf /opt/splunk/etc/apps/search/local/alert_actions.conf
sudo cp configs/fortigate-alerts-all.conf /opt/splunk/etc/apps/search/local/savedsearches.conf

# 2. Python 스크립트 배포
sudo cp scripts/slack_blockkit_alert.py /opt/splunk/etc/apps/search/bin/
sudo chmod +x /opt/splunk/etc/apps/search/bin/slack_blockkit_alert.py

echo "✅ 배포 완료!"
echo ""
echo "⚠️  다음 작업 필요:"
echo "1. Slack Bot Token 설정"
echo "2. Splunk 재시작"
