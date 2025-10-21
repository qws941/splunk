#!/bin/bash
# Slack 알림 테스트 스크립트
# 사용법: ./test-slack-notification.sh

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수: 에러 출력
error() {
    echo -e "${RED}❌ ERROR: $1${NC}" >&2
}

# 함수: 성공 출력
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 함수: 정보 출력
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 함수: 경고 출력
warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 헤더 출력
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Slack 알림 테스트 스크립트"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Slack Token 로드
TOKEN_FILE="../secrets/slack_token.zip"
if [ ! -f "$TOKEN_FILE" ]; then
    error "Slack token 파일이 없습니다: $TOKEN_FILE"
    info "설정 가이드: ../docs/SLACK_TOKEN_SETUP.md 참고"
    exit 1
fi

info "Slack Bot Token 추출 중..."
SLACK_BOT_TOKEN=$(unzip -p "$TOKEN_FILE" slack_token.txt 2>/dev/null)

if [ -z "$SLACK_BOT_TOKEN" ]; then
    error "Slack token 추출 실패"
    exit 1
fi

# Slack Channel 설정
SLACK_CHANNEL="${SLACK_CHANNEL:-splunk-alerts}"

info "테스트 설정:"
echo "  - Channel: #$SLACK_CHANNEL"
echo "  - Token: ${SLACK_BOT_TOKEN:0:12}..."
echo ""

# 테스트 1: 단순 메시지 전송
info "테스트 1: 단순 메시지 전송"
RESPONSE=$(curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"$SLACK_CHANNEL\",
    \"text\": \"🧪 Slack 테스트 메시지 - $(date '+%Y-%m-%d %H:%M:%S')\"
  }")

if echo "$RESPONSE" | jq -e '.ok' >/dev/null 2>&1; then
    success "단순 메시지 전송 성공"
else
    error "단순 메시지 전송 실패"
    echo "$RESPONSE" | jq '.'
    exit 1
fi

sleep 2

# 테스트 2: Rich Attachment 메시지
info "테스트 2: Rich Attachment 메시지 (보안 이벤트 시뮬레이션)"
RESPONSE=$(curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"$SLACK_CHANNEL\",
    \"text\": \"🚨 FortiGate 보안 이벤트 테스트\",
    \"attachments\": [
      {
        \"color\": \"#DC143C\",
        \"pretext\": \"*Critical Security Event Detected*\",
        \"author_name\": \"FortiGate Firewall\",
        \"title\": \"Splunk Alert Action 테스트\",
        \"title_link\": \"https://splunk.example.com\",
        \"fields\": [
          {
            \"title\": \"Severity\",
            \"value\": \"Critical\",
            \"short\": true
          },
          {
            \"title\": \"Event Type\",
            \"value\": \"차단됨\",
            \"short\": true
          },
          {
            \"title\": \"Source IP\",
            \"value\": \"192.168.1.100\",
            \"short\": true
          },
          {
            \"title\": \"Destination IP\",
            \"value\": \"10.0.0.50\",
            \"short\": true
          },
          {
            \"title\": \"차단 횟수\",
            \"value\": \"15\",
            \"short\": false
          }
        ],
        \"footer\": \"Splunk Alert Action\",
        \"ts\": $(date +%s)
      }
    ]
  }")

if echo "$RESPONSE" | jq -e '.ok' >/dev/null 2>&1; then
    success "Rich Attachment 메시지 전송 성공"
else
    error "Rich Attachment 메시지 전송 실패"
    echo "$RESPONSE" | jq '.'
    exit 1
fi

sleep 2

# 테스트 3: 대시보드 데이터 시뮬레이션
info "테스트 3: 대시보드 데이터 알림 (객관적 데이터 표현)"
RESPONSE=$(curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"$SLACK_CHANNEL\",
    \"text\": \"📊 FortiGate 대시보드 요약\",
    \"attachments\": [
      {
        \"color\": \"#6DB7C6\",
        \"pretext\": \"*최근 1시간 통계*\",
        \"fields\": [
          {
            \"title\": \"전체 이벤트\",
            \"value\": \"1,234\",
            \"short\": true
          },
          {
            \"title\": \"차단된 패킷\",
            \"value\": \"456\",
            \"short\": true
          },
          {
            \"title\": \"활성 소스 IP\",
            \"value\": \"89\",
            \"short\": true
          },
          {
            \"title\": \"Critical 이벤트\",
            \"value\": \"12\",
            \"short\": true
          },
          {
            \"title\": \"설정 변경\",
            \"value\": \"2\",
            \"short\": true
          },
          {
            \"title\": \"평균 CPU\",
            \"value\": \"45%\",
            \"short\": true
          }
        ],
        \"footer\": \"FortiGate Dashboard\",
        \"ts\": $(date +%s)
      }
    ]
  }")

if echo "$RESPONSE" | jq -e '.ok' >/dev/null 2>&1; then
    success "대시보드 데이터 알림 전송 성공"
else
    error "대시보드 데이터 알림 전송 실패"
    echo "$RESPONSE" | jq '.'
    exit 1
fi

sleep 2

# 테스트 4: 버튼 액션 포함
info "테스트 4: Interactive Message (버튼 포함)"
RESPONSE=$(curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"channel\": \"$SLACK_CHANNEL\",
    \"text\": \"🔔 Splunk 알림 설정 테스트\",
    \"attachments\": [
      {
        \"color\": \"#65A637\",
        \"text\": \"Slack Alert Action이 정상적으로 작동하고 있습니다.\",
        \"actions\": [
          {
            \"type\": \"button\",
            \"text\": \"Splunk 대시보드 열기\",
            \"url\": \"https://splunk.example.com/app/search/fortinet_dashboard\"
          },
          {
            \"type\": \"button\",
            \"text\": \"문서 확인\",
            \"url\": \"https://github.com/your-repo/splunk/blob/master/README.md\"
          }
        ],
        \"footer\": \"Test Message\",
        \"ts\": $(date +%s)
      }
    ]
  }")

if echo "$RESPONSE" | jq -e '.ok' >/dev/null 2>&1; then
    success "Interactive Message 전송 성공"
else
    error "Interactive Message 전송 실패"
    echo "$RESPONSE" | jq '.'
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
success "모든 Slack 알림 테스트 완료!"
echo "════════════════════════════════════════════════════════════════"
echo ""
info "Slack 채널 #$SLACK_CHANNEL 에서 4개의 테스트 메시지를 확인하세요."
echo ""
