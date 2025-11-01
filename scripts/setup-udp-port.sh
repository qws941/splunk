#!/bin/bash
# Splunk UDP Port Setup Script
# FortiAnalyzer/FortiManager Syslog 수신 설정

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=== Splunk UDP Port 설정 ===${NC}"
echo ""

# Select port
echo -e "${YELLOW}사용할 UDP 포트 선택:${NC}"
echo "1. 5140 (권장, 일반 사용자)"
echo "2. 514 (표준 Syslog, root 권한 필요)"
echo "3. 9514 (대체 포트)"
echo "4. 직접 입력"
echo ""
read -p "선택 (1-4): " PORT_CHOICE

case $PORT_CHOICE in
  1)
    UDP_PORT=5140
    ;;
  2)
    UDP_PORT=514
    echo -e "${YELLOW}⚠️  포트 514는 root 권한이 필요합니다${NC}"
    ;;
  3)
    UDP_PORT=9514
    ;;
  4)
    read -p "UDP 포트 입력: " UDP_PORT
    ;;
  *)
    echo -e "${RED}잘못된 선택. 기본값 5140 사용${NC}"
    UDP_PORT=5140
    ;;
esac

echo ""
echo -e "${GREEN}선택한 포트: ${UDP_PORT}${NC}"
echo ""

# Get Splunk credentials
echo -e "${YELLOW}Splunk 인증 정보:${NC}"
read -p "Username (기본값: admin): " SPLUNK_USER
SPLUNK_USER=${SPLUNK_USER:-admin}
read -s -p "Password: " SPLUNK_PASSWORD
echo ""
echo ""

# Method selection
echo -e "${YELLOW}설정 방법 선택:${NC}"
echo "1. CLI로 설정 (빠름)"
echo "2. inputs.conf 파일로 설정"
echo "3. Web UI 안내만 보기"
echo ""
read -p "선택 (1-3): " METHOD_CHOICE
echo ""

case $METHOD_CHOICE in
  1)
    # CLI method
    echo -e "${YELLOW}CLI로 UDP 포트 설정 중...${NC}"
    sudo /opt/splunk/bin/splunk add udp ${UDP_PORT} \
      -sourcetype fw_log \
      -index fw \
      -auth ${SPLUNK_USER}:${SPLUNK_PASSWORD}

    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✅ UDP 포트 ${UDP_PORT} 설정 완료${NC}"
    else
      echo -e "${RED}❌ 설정 실패${NC}"
      exit 1
    fi
    ;;

  2)
    # inputs.conf method
    echo -e "${YELLOW}inputs.conf 파일 생성 중...${NC}"
    CONFIG_FILE="/opt/splunk/etc/apps/search/local/inputs.conf"

    sudo mkdir -p /opt/splunk/etc/apps/search/local

    sudo tee -a ${CONFIG_FILE} > /dev/null << EOF

# UDP Input for FortiAnalyzer/FortiManager
[udp://${UDP_PORT}]
connection_host = ip
sourcetype = fw_log
index = fw
no_priority_stripping = true
no_appending_timestamp = true
EOF

    sudo chown splunk:splunk ${CONFIG_FILE}
    sudo chmod 644 ${CONFIG_FILE}

    echo -e "${GREEN}✅ inputs.conf 파일 생성 완료${NC}"
    echo ""
    echo -e "${YELLOW}Splunk 재시작 필요${NC}"
    read -p "지금 재시작하시겠습니까? (y/n): " RESTART
    if [[ "$RESTART" == "y" || "$RESTART" == "Y" ]]; then
      sudo /opt/splunk/bin/splunk restart
      echo -e "${GREEN}✅ Splunk 재시작 완료${NC}"
    else
      echo -e "${YELLOW}나중에 수동으로 재시작하세요: sudo /opt/splunk/bin/splunk restart${NC}"
    fi
    ;;

  3)
    # Web UI guide only
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Web UI 설정 방법:${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "1. Splunk Web UI 접속"
    echo "2. Settings → Data inputs"
    echo "3. UDP → Add new"
    echo "4. Port: ${UDP_PORT}"
    echo "5. Source type: fw_log"
    echo "6. Index: fw"
    echo "7. Save"
    echo ""
    exit 0
    ;;

  *)
    echo -e "${RED}잘못된 선택${NC}"
    exit 1
    ;;
esac

# Verify
echo ""
echo -e "${YELLOW}설정 확인 중...${NC}"
sleep 2

sudo /opt/splunk/bin/splunk list udp -auth ${SPLUNK_USER}:${SPLUNK_PASSWORD} | grep ${UDP_PORT}

if [ $? -eq 0 ]; then
  echo ""
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}✅ UDP 포트 ${UDP_PORT} 설정 완료!${NC}"
  echo -e "${GREEN}========================================${NC}"
  echo ""
  echo "다음 단계:"
  echo ""
  echo "1. FortiAnalyzer/FortiManager에서 Syslog 설정:"
  echo "   - Syslog 서버: $(hostname -I | awk '{print $1}')"
  echo "   - 포트: ${UDP_PORT}"
  echo "   - 프로토콜: UDP"
  echo ""
  echo "2. 데이터 수신 확인:"
  echo "   Splunk Web UI → Search & Reporting"
  echo "   쿼리: index=fw sourcetype=fw_log | head 10"
  echo ""
  echo "3. 방화벽에서 포트 열기 (필요시):"
  echo "   sudo firewall-cmd --permanent --add-port=${UDP_PORT}/udp"
  echo "   sudo firewall-cmd --reload"
  echo ""
else
  echo -e "${RED}❌ 설정 확인 실패. 수동으로 확인하세요.${NC}"
  exit 1
fi
