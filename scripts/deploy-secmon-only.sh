#!/bin/bash
# secmon 사용자만 볼 수 있도록 배포 (모든 기능 작동)

SPLUNK_HOME="/opt/splunk"

echo "📦 secmon 전용 앱 배포..."
echo ""
echo "방법: 시스템 전역 배포 + Role 접근 제한"
echo ""

# 1. 시스템 앱 디렉토리에 배포
echo "1️⃣ 앱 압축 해제..."
sudo tar -xzf security_alert.tar.gz -C ${SPLUNK_HOME}/etc/apps/

# 2. 권한 설정
sudo chown -R splunk:splunk ${SPLUNK_HOME}/etc/apps/security_alert

echo ""
echo "2️⃣ Splunk에서 Role 설정 필요:"
echo ""
echo "   Settings → Access controls → Roles → New Role"
echo "   ┌─────────────────────────────────────┐"
echo "   │ Role name: secmon_role              │"
echo "   │ Capabilities: (기본값 유지)          │"
echo "   │ Resources: (기본값 유지)             │"
echo "   └─────────────────────────────────────┘"
echo "   Save 클릭"
echo ""
echo "3️⃣ secmon 사용자를 role에 할당:"
echo ""
echo "   Settings → Access controls → Users → secmon"
echo "   → Roles 탭 → secmon_role 체크 → Save"
echo ""

# 3. Splunk 재시작
echo "🔄 Splunk 재시작..."
sudo ${SPLUNK_HOME}/bin/splunk restart

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 배포 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "위치: ${SPLUNK_HOME}/etc/apps/security_alert/"
echo ""
echo "✅ 작동하는 모든 기능:"
echo "  ✅ Slack 알림 전송"
echo "  ✅ 자동 Field Extraction"
echo "  ✅ Alert 자동 실행"
echo "  ✅ Lookup/Transform"
echo ""
echo "🔒 접근 제한:"
echo "  ✅ secmon_role + admin만 앱 보임"
echo "  ❌ 다른 사용자는 완전히 숨김"
echo ""
echo "⚠️  주의: Splunk Web에서 secmon_role 생성 및 사용자 할당 필수!"
