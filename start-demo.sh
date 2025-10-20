#!/bin/bash
# =============================================================================
# 원스톱 Splunk 대시보드 데모 환경 구축
# =============================================================================
#
# 이 스크립트는 다음을 자동으로 수행합니다:
# 1. Splunk Enterprise Docker 컨테이너 시작
# 2. Splunk Index 생성 (fortigate_security)
# 3. HEC Token 활성화
# 4. 모의 데이터 1000개 생성 및 전송
# 5. Splunk 대시보드 4개 자동 배포
# 6. 브라우저에서 확인 가능
#
# Usage: ./start-demo.sh
#
# =============================================================================

set -e

echo "🚀 Splunk Dashboard Demo - 자동 환경 구축"
echo "============================================================"
echo ""

# =============================================================================
# 설정
# =============================================================================

SPLUNK_HOST="localhost"
SPLUNK_WEB_PORT="8000"
SPLUNK_HEC_PORT="8088"
SPLUNK_MGMT_PORT="8089"
SPLUNK_PASSWORD="Admin123!"
SPLUNK_USERNAME="admin"
SPLUNK_HEC_TOKEN="00000000-0000-0000-0000-000000000000"
SPLUNK_INDEX="fortigate_security"

# =============================================================================
# 1. Docker Compose 시작
# =============================================================================

echo "📦 Step 1: Splunk Docker 컨테이너 시작..."

if docker ps | grep -q splunk-demo; then
    echo "   ℹ️  Splunk 컨테이너가 이미 실행 중입니다"
else
    docker compose up -d
    echo "   ✅ Splunk 컨테이너 시작됨"
fi

echo ""
echo "⏳ Splunk 초기화 대기 중 (약 60초)..."
echo "   (Splunk가 처음 시작될 때는 시간이 걸립니다)"

# Splunk Web UI가 응답할 때까지 대기
MAX_WAIT=120
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s -o /dev/null -w "%{http_code}" http://${SPLUNK_HOST}:${SPLUNK_WEB_PORT} | grep -q "200\|303"; then
        echo "   ✅ Splunk 준비 완료!"
        break
    fi
    echo "   대기 중... ${WAITED}초"
    sleep 5
    WAITED=$((WAITED + 5))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "   ❌ Splunk 시작 시간 초과. 수동으로 확인해주세요."
    exit 1
fi

sleep 10  # 추가 안정화 대기

# =============================================================================
# 2. Splunk Index 생성
# =============================================================================

echo ""
echo "📊 Step 2: Splunk Index 생성 (${SPLUNK_INDEX})..."

docker exec splunk-demo /opt/splunk/bin/splunk add index ${SPLUNK_INDEX} \
    -maxTotalDataSizeMB 500000 \
    -frozenTimePeriodInSecs 7776000 \
    -auth ${SPLUNK_USERNAME}:${SPLUNK_PASSWORD} 2>/dev/null || true

echo "   ✅ Index 생성 완료"

# =============================================================================
# 3. HEC Token 활성화
# =============================================================================

echo ""
echo "🔑 Step 3: HEC Token 활성화..."

docker exec splunk-demo /opt/splunk/bin/splunk http-event-collector enable \
    -uri https://localhost:${SPLUNK_MGMT_PORT} \
    -auth ${SPLUNK_USERNAME}:${SPLUNK_PASSWORD} 2>/dev/null || true

docker exec splunk-demo /opt/splunk/bin/splunk http-event-collector create \
    fortianalyzer-hec \
    -uri https://localhost:${SPLUNK_MGMT_PORT} \
    -description "FortiAnalyzer HEC Token" \
    -disabled 0 \
    -index ${SPLUNK_INDEX} \
    -indexes ${SPLUNK_INDEX} \
    -token ${SPLUNK_HEC_TOKEN} \
    -auth ${SPLUNK_USERNAME}:${SPLUNK_PASSWORD} 2>/dev/null || true

echo "   ✅ HEC Token 활성화 완료"

# =============================================================================
# 4. 모의 데이터 생성 및 전송
# =============================================================================

echo ""
echo "🎲 Step 4: 모의 데이터 1000개 생성 및 전송..."

SPLUNK_HEC_HOST=${SPLUNK_HOST} \
SPLUNK_HEC_PORT=${SPLUNK_HEC_PORT} \
SPLUNK_HEC_TOKEN=${SPLUNK_HEC_TOKEN} \
SPLUNK_INDEX_FORTIGATE=${SPLUNK_INDEX} \
node scripts/generate-mock-data.js --count=1000 --send

echo "   ✅ 모의 데이터 전송 완료"

# =============================================================================
# 5. 대시보드 배포
# =============================================================================

echo ""
echo "📊 Step 5: Splunk 대시보드 4개 배포..."

# Export dashboards to XML files
node scripts/export-dashboards.js

# Deploy dashboards via REST API
SPLUNK_HOST=${SPLUNK_HOST} \
SPLUNK_PORT=${SPLUNK_MGMT_PORT} \
SPLUNK_USERNAME=${SPLUNK_USERNAME} \
SPLUNK_PASSWORD=${SPLUNK_PASSWORD} \
SPLUNK_APP=search \
node scripts/deploy-dashboards.js

echo "   ✅ 대시보드 배포 완료"

# =============================================================================
# 6. 완료 메시지
# =============================================================================

echo ""
echo "============================================================"
echo "✅ 🎉 Splunk Dashboard Demo 환경 구축 완료!"
echo "============================================================"
echo ""
echo "🌐 접속 정보:"
echo "   Splunk Web UI: http://${SPLUNK_HOST}:${SPLUNK_WEB_PORT}"
echo "   Username: ${SPLUNK_USERNAME}"
echo "   Password: ${SPLUNK_PASSWORD}"
echo ""
echo "📊 대시보드 URL:"
echo "   1. Security Overview:"
echo "      http://${SPLUNK_HOST}:${SPLUNK_WEB_PORT}/app/search/fortigate-security-overview"
echo ""
echo "   2. Threat Intelligence:"
echo "      http://${SPLUNK_HOST}:${SPLUNK_WEB_PORT}/app/search/threat-intelligence"
echo ""
echo "   3. Traffic Analysis:"
echo "      http://${SPLUNK_HOST}:${SPLUNK_WEB_PORT}/app/search/traffic-analysis"
echo ""
echo "   4. Performance Monitoring:"
echo "      http://${SPLUNK_HOST}:${SPLUNK_WEB_PORT}/app/search/performance-monitoring"
echo ""
echo "🔍 Splunk 쿼리 예제:"
echo "   index=${SPLUNK_INDEX} | head 100"
echo "   index=${SPLUNK_INDEX} severity=critical | stats count by attack_name"
echo ""
echo "🛑 종료 방법:"
echo "   docker-compose down"
echo ""
echo "============================================================"
