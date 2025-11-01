#!/bin/bash
###############################################################################
# Fluentd-HEC Deployment Script
###############################################################################
#
# 사용법:
#   ./scripts/deploy-fluentd-hec.sh
#
# 이 스크립트는:
#   1. 환경 변수 확인
#   2. Fluentd 컨테이너 배포 (docker-compose-fluentd.yml)
#   3. FortiAnalyzer 설정 파일 생성
#   4. 연결 테스트
#
###############################################################################

set -e

# =============================================================================
# 색상 정의
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# =============================================================================
# 환경 변수 확인
# =============================================================================
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Fluentd-HEC 배포 스크립트${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""

# .env 파일 로드
if [ -f .env ]; then
    source .env
    echo -e "${GREEN}✅ .env 파일 로드 완료${NC}"
else
    echo -e "${RED}❌ .env 파일이 없습니다. .env.example을 복사하세요.${NC}"
    exit 1
fi

# 필수 변수 확인
REQUIRED_VARS=(
    "SPLUNK_HEC_HOST"
    "SPLUNK_HEC_TOKEN"
    "SPLUNK_INDEX_FORTIGATE"
)

for VAR in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR}" ]; then
        echo -e "${RED}❌ 환경 변수 ${VAR}이 설정되지 않았습니다.${NC}"
        exit 1
    fi
done

echo ""
echo "환경 변수:"
echo "  SPLUNK_HEC_HOST: ${SPLUNK_HEC_HOST}"
echo "  SPLUNK_HEC_PORT: ${SPLUNK_HEC_PORT:-8088}"
echo "  SPLUNK_INDEX: ${SPLUNK_INDEX_FORTIGATE}"
echo "  HEC Token: ${SPLUNK_HEC_TOKEN:0:8}...${SPLUNK_HEC_TOKEN: -8}"
echo ""

# =============================================================================
# Docker Compose 배포
# =============================================================================
echo -e "${YELLOW}[1/5] Fluentd 컨테이너 배포 중...${NC}"

if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}❌ docker-compose를 찾을 수 없습니다.${NC}"
    exit 1
fi

# 기존 컨테이너 중지
if [ "$(docker ps -q -f name=fluentd-faz-hec)" ]; then
    echo "기존 Fluentd 컨테이너 중지 중..."
    $COMPOSE_CMD -f docker-compose-fluentd.yml down
fi

# 컨테이너 시작
echo "Fluentd 컨테이너 시작 중..."
$COMPOSE_CMD -f docker-compose-fluentd.yml up -d

# 헬스체크 대기 (최대 60초)
echo "Fluentd 시작 대기 중..."
for i in {1..12}; do
    if docker exec fluentd-faz-hec curl -sf http://localhost:24220/api/plugins.json > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Fluentd 정상 시작됨${NC}"
        break
    fi
    if [ $i -eq 12 ]; then
        echo -e "${RED}❌ Fluentd 시작 실패 (타임아웃)${NC}"
        docker logs fluentd-faz-hec --tail 50
        exit 1
    fi
    sleep 5
done

# =============================================================================
# Fluentd 상태 확인
# =============================================================================
echo ""
echo -e "${YELLOW}[2/5] Fluentd 상태 확인 중...${NC}"

# 플러그인 확인
echo "설치된 플러그인:"
docker exec fluentd-faz-hec fluent-gem list | grep splunk || echo "  (splunk-hec plugin 설치 중... 잠시 대기)"

# 포트 확인
echo ""
echo "열린 포트:"
docker port fluentd-faz-hec

# 로그 확인 (최근 20줄)
echo ""
echo "Fluentd 로그 (최근 20줄):"
docker logs fluentd-faz-hec --tail 20

# =============================================================================
# FortiAnalyzer 설정 파일 생성
# =============================================================================
echo ""
echo -e "${YELLOW}[3/5] FortiAnalyzer 설정 파일 생성 중...${NC}"

FLUENTD_HOST=$(hostname -I | awk '{print $1}')
OUTPUT_FILE="faz-fluentd-config-$(date +%Y%m%d-%H%M%S).txt"

cat > "${OUTPUT_FILE}" <<EOF
###############################################################################
# FortiAnalyzer → Fluentd → Splunk HEC 설정 (복붙 전용)
# 생성일: $(date '+%Y-%m-%d %H:%M:%S')
# Fluentd: ${FLUENTD_HOST}:514 (Syslog UDP)
# Splunk: ${SPLUNK_HEC_HOST}:${SPLUNK_HEC_PORT:-8088} (HEC)
###############################################################################

# ============================================================
# 1단계: FortiAnalyzer CLI에 복붙
# ============================================================
# SSH로 FortiAnalyzer 접속:
#   ssh admin@<FAZ_IP>
#
# 아래 명령어를 전체 복사 → 붙여넣기 → Enter

config system log-forward
    edit "fluentd-syslog"
        set server-name "fluentd-primary"
        set server-ip "${FLUENTD_HOST}"
        set server-port 514
        set protocol udp
        set mode real-time
        set log-type traffic utm event
        set log-field-exclusion disable
        set priority default
        set max-log-rate 0
        set status enable
    next
end


# ============================================================
# 2단계: 설정 확인 (FortiAnalyzer CLI에서 실행)
# ============================================================

# Syslog 전송 상태 확인
diagnose test application logfwd

# 로그 큐 확인 (0에 가까워야 정상)
diagnose log-forward queue-status

# 최근 전송 로그 확인
diagnose log-forward logfwd-log list | tail -20


# ============================================================
# 3단계: Fluentd에서 로그 확인
# ============================================================

# Fluentd 컨테이너 로그 확인 (실시간)
docker logs -f fluentd-faz-hec

# Fluentd 모니터링 API
curl http://localhost:24220/api/plugins.json | jq .

# Buffer 상태 확인
docker exec fluentd-faz-hec ls -lh /var/log/fluentd/buffer/


# ============================================================
# 4단계: Splunk에서 데이터 확인 (Splunk Web Search)
# ============================================================

# 데이터 도착 확인 (1-2분 대기 후)
index=${SPLUNK_INDEX_FORTIGATE} sourcetype=fortianalyzer:fluentd earliest=-5m
| stats count by host, devname, type, subtype
| sort -count

# 최근 로그 확인
index=${SPLUNK_INDEX_FORTIGATE} sourcetype=fortianalyzer:fluentd earliest=-5m
| head 100
| table _time, devname, logid, type, subtype, srcip, dstip, action

# Fluentd 메타데이터 확인
index=${SPLUNK_INDEX_FORTIGATE} sourcetype=fortianalyzer:fluentd earliest=-5m
| stats count by log_source, fluentd_host, event_category


# ============================================================
# 트러블슈팅 (문제 발생 시)
# ============================================================

# 1. 네트워크 연결 테스트 (FortiAnalyzer CLI)
execute ping ${FLUENTD_HOST}
execute telnet ${FLUENTD_HOST} 514

# 2. Fluentd 포트 확인 (Fluentd 서버)
sudo netstat -tunlp | grep -E ":(514|6514|24220)"

# 3. Fluentd 설정 파일 문법 검사
docker exec fluentd-faz-hec fluentd --dry-run -c /fluentd/etc/fluent.conf

# 4. Fluentd 상세 로그 활성화
docker exec fluentd-faz-hec kill -USR1 1  # log_level을 debug로 변경

# 5. Buffer 파일 확인 (로그가 쌓이고 있는지)
docker exec fluentd-faz-hec ls -lh /var/log/fluentd/buffer/splunk_hec/

# 6. Splunk HEC 연결 테스트 (로컬 PC)
curl -k https://${SPLUNK_HEC_HOST}:${SPLUNK_HEC_PORT:-8088}/services/collector/event \\
  -H "Authorization: Splunk ${SPLUNK_HEC_TOKEN}" \\
  -d '{"event":"test from fluentd","sourcetype":"test"}'

# 7. Fluentd 재시작
docker restart fluentd-faz-hec


###############################################################################
# 설정 완료!
###############################################################################

예상 결과:
  - FortiAnalyzer 로그가 Fluentd를 경유하여 Splunk에 전송됨
  - Fluentd에서 로그 파싱 및 필드 추출
  - Splunk index=${SPLUNK_INDEX_FORTIGATE}에 저장됨
  - 레이턴시: 5-10초 (Fluentd 버퍼 flush 간격)

Architecture:
  FortiGate → FortiAnalyzer → Syslog (514/UDP) → Fluentd → HEC (8088/TCP) → Splunk

Benefits:
  - 유연한 로그 변환 (Fluentd filters)
  - 여러 목적지 동시 전송 가능 (Splunk + S3 + Kafka)
  - 버퍼 관리 및 재시도 기능
  - Prometheus 메트릭 수집

Monitoring:
  - Fluentd Monitoring: http://${FLUENTD_HOST}:24220/api/plugins.json
  - Prometheus Metrics: http://${FLUENTD_HOST}:24231/metrics
  - Container Logs: docker logs -f fluentd-faz-hec

다음 단계:
  1. 대시보드 배포: configs/dashboards/studio-production/*.json
  2. 알림 설정: configs/savedsearches-fortigate-alerts.conf
  3. Fluentd 필터 추가: GeoIP, 커스텀 필드 (필요 시)

###############################################################################
EOF

echo -e "${GREEN}✅ 설정 파일 생성: ${OUTPUT_FILE}${NC}"

# =============================================================================
# 네트워크 연결 테스트
# =============================================================================
echo ""
echo -e "${YELLOW}[4/5] 네트워크 연결 테스트 중...${NC}"

# Splunk HEC 연결 테스트
echo "Splunk HEC 연결 테스트..."
HEC_TEST=$(curl -sk -w "%{http_code}" -o /dev/null \
    -H "Authorization: Splunk ${SPLUNK_HEC_TOKEN}" \
    -d '{"event":"fluentd deployment test","sourcetype":"test"}' \
    "https://${SPLUNK_HEC_HOST}:${SPLUNK_HEC_PORT:-8088}/services/collector/event")

if [ "$HEC_TEST" == "200" ]; then
    echo -e "${GREEN}✅ Splunk HEC 연결 성공 (HTTP ${HEC_TEST})${NC}"
else
    echo -e "${YELLOW}⚠️  Splunk HEC 응답: HTTP ${HEC_TEST}${NC}"
fi

# Fluentd 포트 확인
echo ""
echo "Fluentd 포트 확인..."
if nc -z -w2 localhost 514 2>/dev/null; then
    echo -e "${GREEN}✅ Syslog UDP 포트 514 열림${NC}"
else
    echo -e "${YELLOW}⚠️  Syslog UDP 포트 514 확인 실패 (방화벽 확인 필요)${NC}"
fi

if nc -z -w2 localhost 24220 2>/dev/null; then
    echo -e "${GREEN}✅ Monitoring 포트 24220 열림${NC}"
else
    echo -e "${YELLOW}⚠️  Monitoring 포트 24220 확인 실패${NC}"
fi

# =============================================================================
# 완료 및 다음 단계
# =============================================================================
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Fluentd-HEC 배포 완료!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "📄 생성된 파일: ${OUTPUT_FILE}"
echo ""
echo "다음 단계:"
echo "  1. FortiAnalyzer에 SSH 접속"
echo "  2. ${OUTPUT_FILE} 파일 열고 '1단계' 명령어 복붙"
echo "  3. 5-10분 대기 후 Splunk에서 확인:"
echo "     index=${SPLUNK_INDEX_FORTIGATE} sourcetype=fortianalyzer:fluentd earliest=-5m | head 100"
echo ""
echo "모니터링:"
echo "  - Fluentd 로그: docker logs -f fluentd-faz-hec"
echo "  - Fluentd API: http://localhost:24220/api/plugins.json"
echo "  - Prometheus: http://localhost:24231/metrics"
echo ""
echo "트러블슈팅:"
echo "  - 설정 파일: ${OUTPUT_FILE} 참고"
echo "  - 상세 가이드: docs/FLUENTD_HEC_EVALUATION.md"
echo ""

# =============================================================================
# 파일 자동 열기 (macOS/Linux)
# =============================================================================
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "${OUTPUT_FILE}"
elif command -v xdg-open &> /dev/null; then
    xdg-open "${OUTPUT_FILE}"
else
    echo "파일 위치: $(pwd)/${OUTPUT_FILE}"
fi

echo ""
echo -e "${GREEN}배포 스크립트 실행 완료!${NC}"
