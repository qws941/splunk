# Splunk 빠른 배포 가이드

**목적**: 검증 완료된 Splunk 구성요소를 30분 내에 배포
**대상**: Splunk 관리자, SOC 팀
**전제조건**: Splunk Enterprise 8.0+, Slack 워크스페이스 관리자 권한

---

## 🚀 배포 순서 (권장)

### 1단계: Slack Block Kit (15분) ⭐ **최우선**
### 2단계: 대시보드 배포 (10분)
### 3단계: Correlation Rules (5분)

---

## 1단계: Slack Block Kit 배포 (15분)

### 사전 준비
```bash
# 1. Slack App 생성 및 Bot Token 발급
# https://api.slack.com/apps → Create New App → From scratch
# OAuth Scopes 추가: chat:write, chat:write.public, channels:read
# Bot Token 복사: xoxb-<example>
```

### 배포 명령
```bash
# 1. SSH to Splunk server
ssh admin@splunk.jclee.me

# 2. 스크립트 배포
sudo cp ~/app/splunk/scripts/slack_blockkit_alert.py \
    /opt/splunk/etc/apps/search/bin/

sudo chmod +x /opt/splunk/etc/apps/search/bin/slack_blockkit_alert.py

# 3. 환경 변수 설정
sudo vim /opt/splunk/etc/splunk-launch.conf
# 파일 끝에 추가:
# SLACK_BOT_TOKEN=SLACK_BOT_TOKEN_PLACEHOLDER
# SPLUNK_HOST=splunk.jclee.me

# 4. Alert Action 설정 배포
sudo cp ~/app/splunk/configs/alert_actions-slack-blockkit.conf \
    /opt/splunk/etc/apps/search/local/alert_actions.conf

# 5. Splunk 재시작
sudo -u splunk /opt/splunk/bin/splunk restart

# 대기: 2-3분
sudo -u splunk /opt/splunk/bin/splunk status
```

### 검증
```bash
# 1. Alert Action 등록 확인
curl -k -u admin:password \
  "https://splunk.jclee.me:8089/services/admin/alert_actions?output_mode=json" \
  | jq '.entry[] | select(.name == "slack_blockkit")'

# 기대 출력:
# {
#   "name": "slack_blockkit",
#   "label": "Slack Block Kit Alert"
# }
```

### 테스트
```spl
# Splunk Search에서 실행
| makeresults count=1
| eval src_ip="192.168.1.100",
       dst_ip="10.0.0.1",
       severity="critical",
       message="Test Block Kit alert",
       event_count=5,
       alert_title="Slack Block Kit Test"
| sendalert slack_blockkit param.channel="#splunk-alerts" param.severity="critical"
```

**기대 결과**: Slack 채널에 Block Kit 메시지 수신 (버튼, 색상, 필드 포함)

---

## 2단계: 대시보드 배포 (10분)

### 방법 1: Web UI (추천 - 간단)
```
1. Splunk Web → Settings → User Interface → Views
2. "New View" 버튼 클릭
3. "Upload dashboard XML" 선택
4. 파일 선택:
   - configs/dashboards/faz-fmg-monitoring-final.xml
   - configs/dashboards/fortigate-operations.xml
   - configs/dashboards/slack-control.xml
5. "Save" 클릭
```

### 방법 2: REST API (빠름 - 대량 배포)
```bash
# 3개 대시보드 일괄 배포
for dashboard in faz-fmg-monitoring-final fortigate-operations slack-control; do
  curl -k -u admin:password \
    -d "eai:data=$(cat configs/dashboards/${dashboard}.xml)" \
    "https://splunk.jclee.me:8089/servicesNS/nobody/search/data/ui/views/${dashboard}"

  echo "✅ Deployed: ${dashboard}"
done
```

### 방법 3: 파일 시스템 복사 (수동)
```bash
sudo cp configs/dashboards/*.xml \
    /opt/splunk/etc/apps/search/local/data/ui/views/

sudo chown -R splunk:splunk /opt/splunk/etc/apps/search/local/data/ui/views/

# Splunk 웹 재시작 (데몬은 재시작 안 함)
sudo -u splunk /opt/splunk/bin/splunk restart splunkweb
```

### 검증
```
# Splunk Web → Dashboards 메뉴
# 확인 항목:
# - FAZ FMG Monitoring Final (13 panels)
# - FortiGate Operations (12 panels)
# - Slack Control (2 panels)
```

---

## 3단계: Correlation Rules 배포 (5분)

### 배포 명령
```bash
# 1. Correlation Rules 배포
sudo cat ~/app/splunk/configs/correlation-rules.conf >> \
    /opt/splunk/etc/apps/search/local/savedsearches.conf

# 2. Splunk 설정 리로드 (재시작 불필요)
curl -k -u admin:password -X POST \
  "https://splunk.jclee.me:8089/services/admin/savedsearches/_reload"
```

### 검증
```spl
# 1. Correlation Rule 수동 실행 테스트
| savedsearch Correlation_Multi_Factor_Threat_Score

# 2. Summary Index 확인
index=summary_fw marker="correlation_detection=*" earliest=-24h
| stats count by correlation_rule

# 3. 스케줄 실행 확인 (15분 후)
index=_internal source=*scheduler.log savedsearch_name="Correlation_*"
| stats avg(run_time) as avg_runtime_sec by savedsearch_name
```

---

## 배포 후 검증 체크리스트

### ✅ Slack Block Kit
- [ ] Alert Action `slack_blockkit` 등록 확인
- [ ] 테스트 메시지 Slack 수신 확인
- [ ] Block Kit UI (버튼, 색상) 정상 표시
- [ ] 6개 예제 alert 설정 파일 위치 확인

### ✅ 대시보드
- [ ] 3개 XML 대시보드 Splunk Web에서 확인
- [ ] 각 대시보드 패널 정상 로딩 (데이터 없어도 UI 표시)
- [ ] Slack Control 대시보드 ON/OFF 버튼 동작

### ✅ Correlation Rules
- [ ] 6개 correlation rule 등록 확인 (`btool savedsearches list`)
- [ ] Summary index에 데이터 쌓이는지 확인 (15분 후)
- [ ] 스케줄러 로그에서 실행 시간 확인 (60초 이하)

---

## 트러블슈팅

### 문제 1: Slack 메시지 수신 안 됨
```bash
# 원인 확인
tail -f /opt/splunk/var/log/splunk/splunkd.log | grep slack_blockkit

# 일반적 원인:
# 1. SLACK_BOT_TOKEN 미설정
grep SLACK_BOT_TOKEN /opt/splunk/etc/splunk-launch.conf

# 2. Bot이 채널에 초대되지 않음
# Slack에서: /invite @Splunk Block Kit Alerts

# 3. Bot Token 권한 부족
curl -X POST https://slack.com/api/auth.test \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN"
# 기대: {"ok":true, ...}
```

### 문제 2: 대시보드 패널이 비어있음
```spl
# 데이터 확인
index=fortianalyzer earliest=-1h | head 10

# 데이터 모델 확인
| datamodel Fortinet_Security search | head 10

# 데이터 모델 가속화 상태
| rest /services/admin/summarization by_tstats=true
| search summary.id=*Fortinet_Security*
| table summary.id, summary.complete
```

### 문제 3: Correlation Rule 실행 안 됨
```bash
# Cron 스케줄 확인
splunk btool savedsearches list Correlation_Multi_Factor_Threat_Score --debug

# 수동 실행으로 오류 확인
splunk search "| savedsearch Correlation_Multi_Factor_Threat_Score" -maxout 0

# 스케줄러 로그 확인
tail -f /opt/splunk/var/log/splunk/scheduler.log | grep Correlation
```

---

## 롤백 절차 (문제 발생 시)

### Slack Block Kit 롤백
```bash
# 1. Alert Action 비활성화
sudo rm /opt/splunk/etc/apps/search/local/alert_actions.conf

# 2. Splunk 재시작
sudo -u splunk /opt/splunk/bin/splunk restart

# 기존 Slack alert는 정상 동작 (롤백 무해)
```

### 대시보드 롤백
```bash
# Web UI: Settings → Dashboards → 삭제

# 또는 파일 시스템:
sudo rm /opt/splunk/etc/apps/search/local/data/ui/views/faz-fmg-monitoring-final.xml
sudo rm /opt/splunk/etc/apps/search/local/data/ui/views/fortigate-operations.xml
sudo rm /opt/splunk/etc/apps/search/local/data/ui/views/slack-control.xml
```

### Correlation Rules 롤백
```bash
# savedsearches.conf 백업 복원
sudo cp /opt/splunk/etc/apps/search/local/savedsearches.conf.backup \
       /opt/splunk/etc/apps/search/local/savedsearches.conf

# 설정 리로드
curl -k -u admin:password -X POST \
  "https://splunk.jclee.me:8089/services/admin/savedsearches/_reload"
```

---

## 배포 시간 예상

| 단계 | 예상 시간 | 재시작 필요 | 위험도 |
|------|----------|-----------|--------|
| Slack Block Kit | 15분 | Yes (1회) | Low |
| 대시보드 (Web UI) | 5분 | No | Very Low |
| 대시보드 (REST API) | 3분 | No | Very Low |
| Correlation Rules | 5분 | No | Low |
| **총 시간** | **30분** | **1회** | **Low** |

---

## 배포 후 모니터링

### 1주차: 집중 모니터링
```spl
# Slack Block Kit 전송 성공률
index=_internal source=*splunkd.log slack_blockkit earliest=-24h
| stats count as total,
        sum(eval(match(_raw, "SUCCESS"))) as successful
| eval success_rate=round((successful/total)*100, 2)."%"

# Correlation Rule 실행 시간
index=_internal source=*scheduler.log savedsearch_name="Correlation_*" earliest=-7d
| stats avg(run_time) as avg_runtime_sec,
        max(run_time) as max_runtime_sec
  by savedsearch_name
| where max_runtime_sec > 60
| sort -max_runtime_sec
```

### 1개월차: 최적화
```spl
# False Positive 분석
index=summary_fw marker="correlation_detection=*" earliest=-30d
| stats count as detections,
        avg(correlation_score) as avg_score,
        max(correlation_score) as max_score
  by correlation_rule, src_ip
| where max_score >= 75 AND max_score < 90
| sort -count
| head 20

# 임계값 조정이 필요한 Rule 식별 (FP가 많으면 임계값 상향)
```

---

## 참고 문서

- **Slack Block Kit 상세 가이드**: `docs/SLACK_BLOCKKIT_DEPLOYMENT.md`
- **성능 개선 보고서**: `docs/SPLUNK_PERFORMANCE_IMPROVEMENT_REPORT.md`
- **검증 결과**: `docs/VERIFICATION_RESULTS.md`
- **프로젝트 개요**: `CLAUDE.md`

---

## 배포 지원

**문제 발생 시**:
1. 트러블슈팅 섹션 확인
2. 로그 파일 확인: `/opt/splunk/var/log/splunk/splunkd.log`
3. 검증 스크립트 실행: `./scripts/verify-splunk-deployment.sh --full`

**긴급 지원**:
- Slack: #splunk-support
- Email: jclee@jclee.me

---

**작성**: 2025-10-25
**버전**: 1.0
**검증 완료**: 30/30 checks passed
**배포 준비 상태**: ✅ Production-ready
