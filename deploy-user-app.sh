#!/bin/bash
# Splunk 사용자별 앱 배포 스크립트

USER="secmon"
APP="security_alert"
SPLUNK_HOME="/opt/splunk"
USER_APP_DIR="${SPLUNK_HOME}/etc/users/${USER}/${APP}"

echo "📦 사용자별 앱 배포: ${USER}/${APP}"

# 1. 사용자 디렉토리 생성
sudo mkdir -p "${USER_APP_DIR}"

# 2. 앱 압축 해제
sudo tar -xzf security_alert.tar.gz -C "${SPLUNK_HOME}/etc/users/${USER}/"

# 3. 권한 설정
sudo chown -R splunk:splunk "${USER_APP_DIR}"

# 4. Splunk 재시작
sudo ${SPLUNK_HOME}/bin/splunk restart

echo "✅ 완료! ${USER} 사용자만 접근 가능"
echo ""
echo "확인 방법:"
echo "1. secmon 계정으로 Splunk 로그인"
echo "2. Apps → Security Alert System 확인"
echo "3. 다른 사용자로 로그인 → 앱이 보이지 않음"
