#!/bin/bash
# Analyze index=fw data structure and fields
# 실제 데이터 샘플을 보고 필드 구조 파악

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=== index=fw 데이터 분석 가이드 ===${NC}"
echo ""

echo -e "${YELLOW}다음 쿼리들을 Splunk Web UI에서 실행하세요:${NC}"
echo ""

# Query 1: 기본 샘플 데이터
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}1. 기본 데이터 샘플 (최근 10개)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
cat << 'EOF'
index=fw earliest=-1h latest=now
| head 10
| table _time, _raw
EOF
echo ""
echo "→ 실제 로그 형식을 확인하세요"
echo ""
read -p "Enter를 눌러 다음 쿼리로..."
echo ""

# Query 2: 모든 필드 확인
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}2. 추출된 모든 필드 확인${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
cat << 'EOF'
index=fw earliest=-1h latest=now
| head 1
| transpose
EOF
echo ""
echo "→ 추출된 필드 이름과 값을 확인하세요"
echo ""
read -p "Enter를 눌러 다음 쿼리로..."
echo ""

# Query 3: Severity 필드 확인
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}3. Severity 관련 필드 확인${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
cat << 'EOF'
index=fw earliest=-1h latest=now
| eval has_severity=if(isnotnull(severity), "severity", "")
| eval has_level=if(isnotnull(level), "level", "")
| eval has_priority=if(isnotnull(priority), "priority", "")
| stats count by has_severity, has_level, has_priority
EOF
echo ""
echo "→ 어떤 필드가 사용되는지 확인"
echo ""
read -p "Enter를 눌러 다음 쿼리로..."
echo ""

# Query 4: Critical 이벤트 확인
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}4. Critical 이벤트 샘플${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
cat << 'EOF'
index=fw earliest=-24h latest=now
| search "*critical*" OR "*Critical*" OR "*CRITICAL*"
| head 10
| table _time, severity, level, priority, msg, logid, _raw
EOF
echo ""
echo "→ Critical 이벤트가 어떤 형식인지 확인"
echo ""
read -p "Enter를 눌러 다음 쿼리로..."
echo ""

# Query 5: IP 필드 확인
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}5. IP 주소 필드 확인${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
cat << 'EOF'
index=fw earliest=-1h latest=now
| head 10
| table _time, srcip, src, src_ip, dstip, dst, dst_ip
EOF
echo ""
echo "→ IP 주소가 어떤 필드에 있는지 확인"
echo ""
read -p "Enter를 눌러 다음 쿼리로..."
echo ""

# Query 6: Action/Operation 필드 확인
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}6. Action/Operation 필드 확인${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
cat << 'EOF'
index=fw earliest=-1h latest=now
| stats count by action, operation
| sort -count
EOF
echo ""
echo "→ 어떤 action/operation 값들이 있는지 확인"
echo ""
read -p "Enter를 눌러 다음 쿼리로..."
echo ""

# Query 7: Object 필드 확인
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}7. Object 필드 확인${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
cat << 'EOF'
index=fw earliest=-1h latest=now
| stats count by object
| sort -count
| head 20
EOF
echo ""
echo "→ 어떤 object 값들이 있는지 확인"
echo ""
read -p "Enter를 눌러 다음 쿼리로..."
echo ""

# Query 8: LogID 분포 확인
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}8. LogID 분포 확인${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
cat << 'EOF'
index=fw earliest=-1h latest=now
| stats count by logid
| sort -count
| head 20
EOF
echo ""
echo "→ 어떤 logid 값들이 많은지 확인"
echo ""
read -p "Enter를 눌러 다음 쿼리로..."
echo ""

# Query 9: User 필드 확인
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}9. User 필드 확인${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
cat << 'EOF'
index=fw earliest=-24h latest=now
| search user=*
| stats count by user
| sort -count
| head 20
EOF
echo ""
echo "→ User 필드가 존재하는지, 어떤 값들이 있는지 확인"
echo ""
read -p "Enter를 눌러 다음 쿼리로..."
echo ""

# Query 10: Message 패턴 확인
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}10. Message 패턴 확인${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
cat << 'EOF'
index=fw earliest=-1h latest=now
| rex field=_raw "(?<extracted_msg>msg=\"[^\"]+\")"
| head 10
| table _time, msg, extracted_msg, _raw
EOF
echo ""
echo "→ msg 필드가 어떻게 추출되는지 확인"
echo ""

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}모든 쿼리 실행 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "위 쿼리 결과를 확인한 후, 다음 정보를 알려주세요:"
echo ""
echo "1. Severity 필드:"
echo "   - severity, level, priority 중 어느 것을 사용하나요?"
echo "   - Critical 이벤트의 값은? (예: critical, Critical, 5, high 등)"
echo ""
echo "2. IP 주소 필드:"
echo "   - 출발지: srcip, src, src_ip 중 어느 것?"
echo "   - 목적지: dstip, dst, dst_ip 중 어느 것?"
echo ""
echo "3. FMG 관련:"
echo "   - Policy Install 이벤트가 있나요? (action=install?)"
echo "   - Object 필드에 address, service, vip 등이 있나요?"
echo ""
echo "4. 특이사항:"
echo "   - Update Fail 메시지가 실제로 있나요?"
echo "   - 제외해야 할 logid가 맞나요?"
echo ""
