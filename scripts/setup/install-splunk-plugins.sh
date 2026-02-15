#!/bin/bash
###############################################################################
# Splunk 플러그인 자동 설치 스크립트
###############################################################################

set -euo pipefail

CONTAINER_NAME="splunk-test"
PLUGINS_DIR="/home/jclee/app/splunk/plugins"
SPLUNK_APPS_DIR="/opt/splunk/etc/apps"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Splunk 플러그인 설치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Splunk 컨테이너가 실행 중이 아닙니다: $CONTAINER_NAME"
    echo "   docker start $CONTAINER_NAME"
    exit 1
fi

echo "✅ Splunk 컨테이너 실행 중: $CONTAINER_NAME"
echo ""

# Function to install plugin
install_plugin() {
    local plugin_file="$1"
    local plugin_name=$(basename "$plugin_file" .tgz)

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 설치 중: $plugin_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Copy to container
    echo "1️⃣  컨테이너로 복사..."
    docker cp "$plugin_file" "$CONTAINER_NAME:/tmp/"
    echo "   ✅ 복사 완료"

    # Extract in container
    echo "2️⃣  압축 해제..."
    docker exec "$CONTAINER_NAME" tar -xzf "/tmp/$(basename "$plugin_file")" \
        -C "$SPLUNK_APPS_DIR"
    echo "   ✅ 압축 해제 완료"

    # Clean up
    echo "3️⃣  임시 파일 삭제..."
    docker exec "$CONTAINER_NAME" rm -f "/tmp/$(basename "$plugin_file")"
    echo "   ✅ 정리 완료"

    echo ""
}

# Install plugins
if [[ -f "$PLUGINS_DIR/slack-notification-alert_232.tgz" ]]; then
    install_plugin "$PLUGINS_DIR/slack-notification-alert_232.tgz"
else
    echo "⚠️  Slack 플러그인을 찾을 수 없습니다"
fi

if [[ -f "$PLUGINS_DIR/fortinet-fortigate-add-on-for-splunk_169.tgz" ]]; then
    install_plugin "$PLUGINS_DIR/fortinet-fortigate-add-on-for-splunk_169.tgz"
else
    echo "⚠️  FortiGate TA를 찾을 수 없습니다"
fi

if [[ -f "$PLUGINS_DIR/splunk-common-information-model-cim_620.tgz" ]]; then
    install_plugin "$PLUGINS_DIR/splunk-common-information-model-cim_620.tgz"
else
    echo "⚠️  CIM을 찾을 수 없습니다"
fi

# Restart Splunk
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Splunk 재시작 중..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker restart "$CONTAINER_NAME"

echo "⏳ Splunk 시작 대기 중 (30초)..."
sleep 30

# Verify installation
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 설치된 앱 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec "$CONTAINER_NAME" ls -1 "$SPLUNK_APPS_DIR" | grep -iE "(slack|forti|cim)" || echo "⚠️  설치 확인 실패"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 설치 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "다음 단계:"
echo "1. Splunk Web UI 접속: http://localhost:8800"
echo "2. Settings → Alert actions → Setup Slack Alerts"
echo "3. Webhook URL 입력"
echo "4. 테스트: | sendalert slack param.channel=\"#test\" param.message=\"테스트\""
echo ""
