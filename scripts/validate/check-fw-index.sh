#!/bin/bash
# Check index=fw data and verify alert configurations
# Splunk 9.3.1

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=== index=fw 데이터 확인 스크립트 ===${NC}"
echo ""

# ============================================================================
# 1. 기본 데이터 확인
# ============================================================================
echo -e "${YELLOW}1. index=fw 기본 데이터 확인 (최근 1시간)${NC}"
echo ""
echo "Splunk Web UI에서 실행할 쿼리:"
echo ""
echo -e "${BLUE}index=fw earliest=-1h latest=now${NC}"
echo -e "${BLUE}| stats count by sourcetype, host${NC}"
echo ""
echo "예상 결과:"
echo "  sourcetype=fw_log, host=fortianalyzer.local, count=1234"
echo ""
read -p "Enter를 눌러 계속..."
echo ""

# ============================================================================
# 2. sourcetype 확인
# ============================================================================
echo -e "${YELLOW}2. sourcetype 종류 확인${NC}"
echo ""
echo "쿼리:"
echo ""
echo -e "${BLUE}index=fw earliest=-24h latest=now${NC}"
echo -e "${BLUE}| stats count by sourcetype${NC}"
echo ""
echo "확인사항:"
echo "  - sourcetype=fw_log 인지 확인"
echo "  - 다른 sourcetype이 있는지 확인"
echo ""
read -p "Enter를 눌러 계속..."
echo ""

# ============================================================================
# 3. FAZ Critical 데이터 확인
# ============================================================================
echo -e "${YELLOW}3. FAZ Critical 이벤트 확인 (알림 대상)${NC}"
echo ""
echo "쿼리:"
echo ""
echo -e "${BLUE}index=fw sourcetype=fw_log earliest=-24h latest=now${NC}"
echo -e "${BLUE}| search (severity=critical OR level=critical)${NC}"
echo -e "${BLUE}| search NOT msg=\"*Update Fail*\"${NC}"
echo -e "${BLUE}| search NOT logid IN (\"0100032001\",\"0100032002\",\"0100032003\",\"0100032004\",\"0100032005\",\"0101039424\",\"0101039425\",\"0101039426\",\"0101039427\",\"0101039428\",\"0102043008\",\"0102043009\",\"0102043010\")${NC}"
echo -e "${BLUE}| stats count${NC}"
echo ""
echo "확인사항:"
echo "  - count > 0 이면 알림이 발송될 데이터 존재"
echo "  - count = 0 이면 크리티컬 이벤트 없음 (정상)"
echo ""
read -p "Enter를 눌러 계속..."
echo ""

# ============================================================================
# 4. FMG Policy Install 확인
# ============================================================================
echo -e "${YELLOW}4. FMG Policy Install 이벤트 확인${NC}"
echo ""
echo "쿼리:"
echo ""
echo -e "${BLUE}index=fw sourcetype=fw_log earliest=-24h latest=now${NC}"
echo -e "${BLUE}| search (action=install OR action=\"install\" OR msg=\"*install*policy*\")${NC}"
echo -e "${BLUE}| stats count${NC}"
echo ""
read -p "Enter를 눌러 계속..."
echo ""

# ============================================================================
# 5. FMG Policy CRUD 확인
# ============================================================================
echo -e "${YELLOW}5. FMG Policy CRUD 이벤트 확인${NC}"
echo ""
echo "쿼리:"
echo ""
echo -e "${BLUE}index=fw sourcetype=fw_log earliest=-24h latest=now${NC}"
echo -e "${BLUE}| search object=\"*policy*\"${NC}"
echo -e "${BLUE}| search operation IN (add,set,delete,create,modify,remove)${NC}"
echo -e "${BLUE}| stats count by operation${NC}"
echo ""
read -p "Enter를 눌러 계속..."
echo ""

# ============================================================================
# 6. FMG Object CRUD 확인
# ============================================================================
echo -e "${YELLOW}6. FMG Object CRUD 이벤트 확인${NC}"
echo ""
echo "쿼리:"
echo ""
echo -e "${BLUE}index=fw sourcetype=fw_log earliest=-24h latest=now${NC}"
echo -e "${BLUE}| search object IN (address,service,vip,addrgrp,servgrp)${NC}"
echo -e "${BLUE}| search operation IN (add,set,delete,create,modify,remove)${NC}"
echo -e "${BLUE}| stats count by object, operation${NC}"
echo ""
read -p "Enter를 눌러 계속..."
echo ""

# ============================================================================
# 7. 필드 추출 확인
# ============================================================================
echo -e "${YELLOW}7. 주요 필드 추출 확인${NC}"
echo ""
echo "쿼리:"
echo ""
echo -e "${BLUE}index=fw sourcetype=fw_log earliest=-1h latest=now${NC}"
echo -e "${BLUE}| head 10${NC}"
echo -e "${BLUE}| table _time, severity, level, srcip, src, dstip, dst, msg, logid, action, operation, object, user${NC}"
echo ""
echo "확인사항:"
echo "  - severity 또는 level 필드 존재"
echo "  - srcip 또는 src 필드 존재"
echo "  - dstip 또는 dst 필드 존재"
echo "  - msg 필드 존재"
echo ""
read -p "Enter를 눌러 계속..."
echo ""

# ============================================================================
# 8. 알림 실행 이력 확인
# ============================================================================
echo -e "${YELLOW}8. 알림 실행 이력 확인 (최근 24시간)${NC}"
echo ""
echo "쿼리:"
echo ""
echo -e "${BLUE}index=_internal source=*scheduler.log${NC}"
echo -e "${BLUE}| search savedsearch_name IN (\"FAZ_Critical_Alerts\", \"FMG_Policy_Install\", \"FMG_Policy_CRUD\", \"FMG_Object_CRUD\")${NC}"
echo -e "${BLUE}| table _time, savedsearch_name, status, result_count, run_time${NC}"
echo -e "${BLUE}| sort -_time${NC}"
echo ""
echo "확인사항:"
echo "  - status=success: 알림 정상 실행"
echo "  - result_count > 0: 알림 발송됨"
echo "  - result_count = 0: 조건 미충족 (알림 미발송)"
echo ""
read -p "Enter를 눌러 계속..."
echo ""

# ============================================================================
# 9. Slack 알림 발송 이력 확인
# ============================================================================
echo -e "${YELLOW}9. Slack 알림 발송 이력 확인${NC}"
echo ""
echo "쿼리:"
echo ""
echo -e "${BLUE}index=_internal source=*splunkd.log slack${NC}"
echo -e "${BLUE}| table _time, log_level, message${NC}"
echo -e "${BLUE}| sort -_time${NC}"
echo ""
echo "또는:"
echo ""
echo -e "${BLUE}index=_internal source=*alert_actions.log${NC}"
echo -e "${BLUE}| search action_name=slack${NC}"
echo -e "${BLUE}| table _time, action_name, search_name, result${NC}"
echo ""
read -p "Enter를 눌러 계속..."
echo ""

# ============================================================================
# 10. 데이터 수신 확인 (최근 1시간)
# ============================================================================
echo -e "${YELLOW}10. 데이터 수신 확인 (분당 이벤트 수)${NC}"
echo ""
echo "쿼리:"
echo ""
echo -e "${BLUE}index=fw sourcetype=fw_log earliest=-1h latest=now${NC}"
echo -e "${BLUE}| timechart span=1m count${NC}"
echo ""
echo "확인사항:"
echo "  - 꾸준히 데이터가 들어오는지"
echo "  - 데이터가 끊긴 구간이 있는지"
echo ""
read -p "Enter를 눌러 계속..."
echo ""

# ============================================================================
# 요약
# ============================================================================
echo -e "${GREEN}=== 확인 완료 ===${NC}"
echo ""
echo "위의 모든 쿼리를 Splunk Web UI에서 실행하여:"
echo ""
echo "1. ✅ index=fw에 데이터가 정상적으로 들어오는지 확인"
echo "2. ✅ sourcetype=fw_log 인지 확인"
echo "3. ✅ 알림 대상 이벤트가 존재하는지 확인"
echo "4. ✅ 알림이 정상적으로 실행되는지 확인"
echo "5. ✅ Slack으로 알림이 발송되는지 확인"
echo ""
echo "문제가 있으면:"
echo "  - 데이터 없음 → FortiAnalyzer Syslog 설정 확인"
echo "  - 알림 실행 안됨 → Settings → Searches, reports, and alerts에서 Enable 확인"
echo "  - Slack 알림 안옴 → Settings → Alert actions → Slack 설정 확인"
echo ""
