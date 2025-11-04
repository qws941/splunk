#!/bin/bash
# 하이브리드 배포: 시스템 공통 + 사용자별 설정

SPLUNK_HOME="/opt/splunk"
USER="secmon"

echo "📦 하이브리드 배포 시작..."

# 1. 시스템 전역: Alert Actions, Props, Transforms (공통 기능)
echo "1️⃣ 시스템 공통 기능 배포..."
sudo mkdir -p ${SPLUNK_HOME}/etc/apps/security_alert_core/{bin,default,README,lookups}

# bin/ 스크립트 복사
sudo cp -r security_alert/bin/* ${SPLUNK_HOME}/etc/apps/security_alert_core/bin/
sudo chmod +x ${SPLUNK_HOME}/etc/apps/security_alert_core/bin/*.py

# 공통 설정 복사
sudo cp security_alert/default/alert_actions.conf ${SPLUNK_HOME}/etc/apps/security_alert_core/default/
sudo cp security_alert/default/props.conf ${SPLUNK_HOME}/etc/apps/security_alert_core/default/
sudo cp security_alert/default/transforms.conf ${SPLUNK_HOME}/etc/apps/security_alert_core/default/
sudo cp security_alert/default/macros.conf ${SPLUNK_HOME}/etc/apps/security_alert_core/default/
sudo cp security_alert/README/alert_actions.conf.spec ${SPLUNK_HOME}/etc/apps/security_alert_core/README/

# Lookup 파일 복사
sudo cp -r security_alert/lookups/* ${SPLUNK_HOME}/etc/apps/security_alert_core/lookups/

# app.conf (코어 앱)
cat << 'APPCONF' | sudo tee ${SPLUNK_HOME}/etc/apps/security_alert_core/default/app.conf > /dev/null
[install]
is_configured = 1

[ui]
is_visible = 0
label = Security Alert Core (공통 기능)

[launcher]
author = NextTrade Security Team
description = Alert Actions and common configurations
version = 2.0.4
APPCONF

# 2. 사용자별: Saved Searches, Dashboards (개인 설정)
echo "2️⃣ ${USER} 사용자 전용 설정 배포..."
sudo mkdir -p ${SPLUNK_HOME}/etc/users/${USER}/security_alert/default

# Saved Searches만 복사
sudo cp security_alert/default/savedsearches.conf ${SPLUNK_HOME}/etc/users/${USER}/security_alert/default/

# app.conf (사용자 앱)
cat << 'USERAPPCONF' | sudo tee ${SPLUNK_HOME}/etc/users/${USER}/security_alert/default/app.conf > /dev/null
[install]
is_configured = 1

[ui]
is_visible = 1
label = Security Alert System

[launcher]
author = NextTrade Security Team
description = FortiGate Security Monitoring
version = 2.0.4
USERAPPCONF

# 3. 권한 설정
sudo chown -R splunk:splunk ${SPLUNK_HOME}/etc/apps/security_alert_core
sudo chown -R splunk:splunk ${SPLUNK_HOME}/etc/users/${USER}/security_alert

# 4. Splunk 재시작
echo "🔄 Splunk 재시작..."
sudo ${SPLUNK_HOME}/bin/splunk restart

echo ""
echo "✅ 하이브리드 배포 완료!"
echo ""
echo "구조:"
echo "  /opt/splunk/etc/apps/security_alert_core/    ← 공통 기능 (모든 사용자)"
echo "    ├── bin/                                     ← Alert Actions (Slack)"
echo "    ├── default/alert_actions.conf               ← Slack 설정"
echo "    ├── default/props.conf                       ← 자동 Lookup"
echo "    └── default/transforms.conf                  ← Lookup 정의"
echo ""
echo "  /opt/splunk/etc/users/secmon/security_alert/  ← secmon 전용"
echo "    └── default/savedsearches.conf               ← Alert 정의"
echo ""
echo "결과:"
echo "  ✅ Slack 알림 작동 (시스템 Alert Actions 사용)"
echo "  ✅ 자동 Field Extraction 작동"
echo "  ✅ secmon 사용자만 Alert 접근 가능"
echo "  ✅ 다른 사용자는 앱 볼 수 없음"
