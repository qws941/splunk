#!/bin/bash
###############################################################################
# FortiAnalyzer → Splunk HEC 원라이너 설정 스크립트
###############################################################################
#
# 사용법:
#   ./setup-faz-hec-oneliner.sh <splunk_host> <hec_token> <faz_ip>
#
# 예시:
#   ./setup-faz-hec-oneliner.sh splunk.jclee.me e4b7c8a9-1234-5678-9abc-def012345678 172.28.32.100
#
# 이 스크립트는:
#   1. Splunk HEC 토큰 검증
#   2. Splunk index=fortianalyzer 생성
#   3. FortiAnalyzer 설정 파일 생성 (복붙 전용)
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
# 사용법 출력
# =============================================================================
usage() {
    echo "사용법: $0 <splunk_host> <hec_token> <faz_ip>"
    echo ""
    echo "예시:"
    echo "  $0 splunk.jclee.me e4b7c8a9-1234-5678-9abc-def012345678 172.28.32.100"
    echo ""
    echo "필수 파라미터:"
    echo "  splunk_host - Splunk 서버 호스트명/IP (예: splunk.jclee.me)"
    echo "  hec_token   - Splunk HEC 토큰 (UUID 형식)"
    echo "  faz_ip      - FortiAnalyzer IP 주소"
    exit 1
}

# =============================================================================
# 파라미터 검증
# =============================================================================
if [ $# -ne 3 ]; then
    usage
fi

SPLUNK_HOST="$1"
HEC_TOKEN="$2"
FAZ_IP="$3"

echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}FortiAnalyzer → Splunk HEC 원라이너 설정${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "Splunk Host: $SPLUNK_HOST"
echo "HEC Token: ${HEC_TOKEN:0:8}...${HEC_TOKEN: -8}"
echo "FAZ IP: $FAZ_IP"
echo ""

# =============================================================================
# Step 1: Splunk HEC 토큰 검증
# =============================================================================
echo -e "${YELLOW}[1/5] Splunk HEC 연결 테스트 중...${NC}"

# HEC 헬스체크
HEALTH_CHECK=$(curl -sk "https://${SPLUNK_HOST}:8088/services/collector/health")
if [[ "$HEALTH_CHECK" == *"HEC is healthy"* ]]; then
    echo -e "${GREEN}✅ HEC 엔드포인트 정상${NC}"
else
    echo -e "${RED}❌ HEC 엔드포인트 응답 없음${NC}"
    echo "HEC가 활성화되어 있는지 확인하세요:"
    echo "  Splunk Web → Settings → Data Inputs → HTTP Event Collector → Global Settings"
    exit 1
fi

# HEC 토큰 검증
TEST_EVENT='{"event":"setup test","sourcetype":"test"}'
TOKEN_TEST=$(curl -sk -w "%{http_code}" -o /dev/null \
    -H "Authorization: Splunk ${HEC_TOKEN}" \
    -d "${TEST_EVENT}" \
    "https://${SPLUNK_HOST}:8088/services/collector/event")

if [ "$TOKEN_TEST" == "200" ]; then
    echo -e "${GREEN}✅ HEC 토큰 인증 성공${NC}"
else
    echo -e "${RED}❌ HEC 토큰 인증 실패 (HTTP ${TOKEN_TEST})${NC}"
    echo "토큰을 확인하세요:"
    echo "  Splunk Web → Settings → Data Inputs → HTTP Event Collector → View tokens"
    exit 1
fi

# =============================================================================
# Step 2: Splunk index=fortianalyzer 생성 (REST API)
# =============================================================================
echo -e "${YELLOW}[2/5] Splunk index 생성 중...${NC}"

# Splunk 관리자 계정 확인
read -p "Splunk admin 사용자명 [admin]: " SPLUNK_USER
SPLUNK_USER=${SPLUNK_USER:-admin}

read -sp "Splunk admin 비밀번호: " SPLUNK_PASS
echo ""

# Index 존재 여부 확인
INDEX_EXISTS=$(curl -sk -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
    "https://${SPLUNK_HOST}:8089/services/data/indexes/fortianalyzer" \
    -w "%{http_code}" -o /dev/null)

if [ "$INDEX_EXISTS" == "200" ]; then
    echo -e "${GREEN}✅ index=fortianalyzer 이미 존재함${NC}"
else
    echo "index=fortianalyzer 생성 중..."
    CREATE_INDEX=$(curl -sk -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
        "https://${SPLUNK_HOST}:8089/services/data/indexes" \
        -d name=fortianalyzer \
        -d datatype=event \
        -d maxTotalDataSizeMB=512000 \
        -w "%{http_code}" -o /dev/null)

    if [ "$CREATE_INDEX" == "201" ]; then
        echo -e "${GREEN}✅ index=fortianalyzer 생성 완료${NC}"
    else
        echo -e "${YELLOW}⚠️  Index 생성 실패 (수동 생성 필요)${NC}"
        echo "Splunk Web에서 수동 생성:"
        echo "  Settings → Indexes → New Index → Name: fortianalyzer"
    fi
fi

# =============================================================================
# Step 3: FortiAnalyzer 설정 파일 생성 (복붙 전용)
# =============================================================================
echo -e "${YELLOW}[3/5] FortiAnalyzer 설정 파일 생성 중...${NC}"

OUTPUT_FILE="faz-hec-config-${FAZ_IP}.txt"

cat > "${OUTPUT_FILE}" <<EOF
###############################################################################
# FortiAnalyzer HEC 설정 (복붙 전용)
# 생성일: $(date '+%Y-%m-%d %H:%M:%S')
# Splunk: ${SPLUNK_HOST}:8088
# FortiAnalyzer: ${FAZ_IP}
###############################################################################

# ============================================================
# 1단계: FortiAnalyzer CLI에 복붙
# ============================================================
# SSH로 FortiAnalyzer 접속:
#   ssh admin@${FAZ_IP}
#
# 아래 명령어를 전체 복사 → 붙여넣기 → Enter

config system log-fetch client-profile
    edit "splunk-hec-primary"
        set server-type splunk
        set server-ip "${SPLUNK_HOST}"
        set server-port 8088
        set secure-connection enable
        set client-key "${HEC_TOKEN}"
        set data-format splunk-hec
        set log-type traffic utm event
        set upload-interval realtime
        set upload-option store-and-upload
        set compress gzip
        set max-log-rate 10000
        set sourcetype "fortianalyzer:traffic"
        set source "fortianalyzer-prod"
        set index "fortianalyzer"
        set host-field devname
        set status enable
    next
end

config system log-fetch server-settings
    set status enable
    set max-conn-timeout 300
    set unencrypted-logging disable
    set upload-max-conn 5
    set max-logs-per-batch 5000
    set upload-retry-max 3
    set buffer-max-send 10000000
    set buffer-max-disk 100000000
end


# ============================================================
# 2단계: 설정 확인 (FortiAnalyzer CLI에서 실행)
# ============================================================

# 연결 상태 확인
diagnose test application fazd 1

# HEC 프로파일 상태 확인
diagnose log-fetch client-profile status splunk-hec-primary

# 업로드 큐 확인 (0에 가까워야 정상)
diagnose log-fetch queue status

# 최근 업로드 로그 확인
diagnose log-fetch upload-log list | tail -20


# ============================================================
# 3단계: Splunk에서 데이터 확인 (Splunk Web Search)
# ============================================================

# 데이터 도착 확인 (1-2분 대기 후)
index=fortianalyzer earliest=-5m
| stats count by host, sourcetype
| sort -count

# 최근 로그 확인
index=fortianalyzer earliest=-5m
| head 100
| table _time, host, logid, type, subtype, msg


# ============================================================
# 트러블슈팅 (문제 발생 시)
# ============================================================

# 1. 네트워크 연결 테스트 (FortiAnalyzer CLI)
execute ping ${SPLUNK_HOST}
execute telnet ${SPLUNK_HOST} 8088

# 2. HEC 토큰 확인 (로컬 PC)
curl -k https://${SPLUNK_HOST}:8088/services/collector/event \\
  -H "Authorization: Splunk ${HEC_TOKEN}" \\
  -d '{"event":"test","sourcetype":"test"}'

# 3. 디버그 모드 활성화 (FortiAnalyzer CLI)
diagnose debug application log-fetch-client -1
diagnose debug enable
# 로그 확인 후 비활성화:
diagnose debug disable


###############################################################################
# 설정 완료!
###############################################################################

예상 결과:
  - FortiAnalyzer 로그가 Splunk index=fortianalyzer에 실시간 전송됨
  - 레이턴시: < 1초
  - 데이터 확인: 1-2분 후 Splunk Search에서 조회 가능

다음 단계:
  1. 대시보드 배포: configs/dashboards/studio-production/*.json
  2. 알림 설정: configs/savedsearches-fortigate-alerts.conf
  3. 상세 가이드: docs/FAZ_HEC_SETUP_GUIDE.md

###############################################################################
EOF

echo -e "${GREEN}✅ 설정 파일 생성: ${OUTPUT_FILE}${NC}"

# =============================================================================
# Step 4: 네트워크 연결 테스트
# =============================================================================
echo -e "${YELLOW}[4/5] 네트워크 연결 테스트 중...${NC}"

# FAZ → Splunk ping 테스트 (선택적)
if command -v ping &> /dev/null; then
    if ping -c 2 -W 2 "${SPLUNK_HOST}" &> /dev/null; then
        echo -e "${GREEN}✅ ${SPLUNK_HOST} ping 응답 확인${NC}"
    else
        echo -e "${YELLOW}⚠️  ${SPLUNK_HOST} ping 응답 없음 (방화벽 ICMP 차단 가능성)${NC}"
    fi
fi

# Port 8088 연결 테스트
if command -v nc &> /dev/null; then
    if nc -z -w2 "${SPLUNK_HOST}" 8088 &> /dev/null; then
        echo -e "${GREEN}✅ ${SPLUNK_HOST}:8088 포트 접근 가능${NC}"
    else
        echo -e "${RED}❌ ${SPLUNK_HOST}:8088 포트 접근 불가${NC}"
        echo "방화벽 규칙을 확인하세요: ${FAZ_IP} → ${SPLUNK_HOST}:8088"
    fi
else
    echo -e "${YELLOW}⚠️  nc 명령어가 없어 포트 테스트 생략${NC}"
fi

# =============================================================================
# Step 5: 완료 및 다음 단계
# =============================================================================
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ 설정 준비 완료!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "📄 생성된 파일: ${OUTPUT_FILE}"
echo ""
echo "다음 단계:"
echo "  1. FortiAnalyzer에 SSH 접속:"
echo "     ssh admin@${FAZ_IP}"
echo ""
echo "  2. ${OUTPUT_FILE} 파일을 열고 '1단계' 명령어를 복붙"
echo ""
echo "  3. 1-2분 대기 후 Splunk에서 확인:"
echo "     index=fortianalyzer earliest=-5m | head 100"
echo ""
echo "  4. 대시보드 배포:"
echo "     Dashboards → Create New Dashboard → Dashboard Studio"
echo "     → Source → 붙여넣기: configs/dashboards/studio-production/*.json"
echo ""

# =============================================================================
# 선택: 파일 자동 열기 (macOS/Linux)
# =============================================================================
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "${OUTPUT_FILE}"
elif command -v xdg-open &> /dev/null; then
    xdg-open "${OUTPUT_FILE}"
else
    echo "파일 위치: $(pwd)/${OUTPUT_FILE}"
fi

echo ""
echo -e "${GREEN}설정 스크립트 실행 완료!${NC}"
