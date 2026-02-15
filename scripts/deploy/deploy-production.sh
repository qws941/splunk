#!/bin/bash
# 운영 환경 배포 스크립트 (에러 없이 바로 작동)

SPLUNK_HOME="/opt/splunk"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Security Alert System 배포"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. 압축 해제
echo "1️⃣ 앱 설치 중..."
sudo tar -xzf security_alert.tar.gz -C ${SPLUNK_HOME}/etc/apps/

# 2. 권한 설정
echo "2️⃣ 권한 설정 중..."
sudo chown -R splunk:splunk ${SPLUNK_HOME}/etc/apps/security_alert

# 3. 설정 파일 확인
echo "3️⃣ 설정 파일 검증 중..."
${SPLUNK_HOME}/bin/splunk btool check --app=security_alert 2>&1 | tee /tmp/btool-check.log

# 4. Splunk 재시작
echo ""
echo "4️⃣ Splunk 재시작 중..."
sudo ${SPLUNK_HOME}/bin/splunk restart

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 배포 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📂 위치: ${SPLUNK_HOME}/etc/apps/security_alert/"
echo ""
echo "🔐 현재 접근 권한:"
echo "   ✅ admin role - 읽기/쓰기 가능"
echo "   ✅ power role - 읽기 가능"
echo "   ❌ 일반 사용자 - 접근 불가"
echo ""
echo "⚙️  다음 단계:"
echo ""
echo "1️⃣ Slack 설정 (필수)"
echo "   Splunk Web → Apps → Security Alert System → Setup"
echo "   → Bot Token 또는 Webhook URL 입력 → Save"
echo ""
echo "2️⃣ Alert 확인"
echo "   Splunk Web → Settings → Searches, reports, and alerts"
echo "   → 15개 alert 확인 (12 active, 3 inactive)"
echo ""
echo "3️⃣ 특정 사용자만 접근 설정 (선택사항)"
echo "   Settings → Roles → New Role → secmon_role 생성"
echo "   Settings → Users → secmon → secmon_role 할당"
echo "   metadata/default.meta 수정:"
echo "   access = read : [ secmon_role, admin ], write : [ admin ]"
echo ""
echo "📋 검증 로그: /tmp/btool-check.log"
