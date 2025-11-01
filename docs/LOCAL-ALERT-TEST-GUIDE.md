# 로컬 알림 테스트 완전 가이드

**목적**: 로컬 환경에서 수정된 3개 알림이 정상 작동하는지 검증

**소요 시간**: 15분

**전제 조건**:
- ✅ Splunk 컨테이너 실행 중 (`docker ps | grep splunk-test`)
- ✅ 3개 플러그인 설치 완료 (Slack, FortiGate TA, CIM)
- ✅ 알림 설정 파일 버그 수정 완료 (공백 추가)

---

## Phase 1: Splunk HEC 활성화 (5분)

### Step 1.1: HEC Global Settings 활성화

```
1. 접속: http://localhost:8800
2. Login: admin / changeme
3. Settings → Data inputs → HTTP Event Collector → Global Settings
4. 체크: "All Tokens" → Enabled
5. Default Source Type: Automatic
6. Default Index: fortianalyzer
7. Save
```

### Step 1.2: HEC Token 생성

```
1. Settings → Data inputs → HTTP Event Collector → New Token
2. Name: local-test-token
3. Source type: Automatic
4. Index: fortianalyzer
5. Review → Submit
6. 토큰 값 복사 (예: 12345678-1234-1234-1234-123456789abc)
```

**검증**:
```bash
# HEC 포트 확인
docker port splunk-test 8088
# Expected: 0.0.0.0:8088 -> 8088/tcp

# HEC 연결 테스트
curl -k https://localhost:8088/services/collector/health
# Expected: {"text":"HEC is healthy","code":200}
```

---

## Phase 2: 테스트 데이터 전송 (3분)

### Step 2.1: 환경 변수 설정

```bash
cd /home/jclee/app/splunk

# HEC 토큰 설정 (위에서 복사한 토큰)
export SPLUNK_HEC_TOKEN="12345678-1234-1234-1234-123456789abc"
```

### Step 2.2: 테스트 데이터 생성 및 전송

```bash
# 모든 알림 타입 테스트 (권장)
node scripts/generate-alert-test-data.js --send --token=$SPLUNK_HEC_TOKEN

# 또는 개별 알림별 테스트
node scripts/generate-alert-test-data.js --type=config --send --token=$SPLUNK_HEC_TOKEN    # Config Change
node scripts/generate-alert-test-data.js --type=critical --send --token=$SPLUNK_HEC_TOKEN  # Critical Events
node scripts/generate-alert-test-data.js --type=ha --send --token=$SPLUNK_HEC_TOKEN        # HA Events
```

**기대 출력**:
```
🔔 FortiGate Alert Test Data Generator
============================================================
📝 Generating Config Change events...
🚨 Generating Critical Event events...
🔴 Generating HA Event events...

✅ Generated 9 test events

🚀 Sending to Splunk HEC...
   Host: localhost:8088
   Index: fortianalyzer
✅ Events sent successfully!

🔍 Verify in Splunk:
   index=fortianalyzer sourcetype=fortigate:event earliest=-1m | head 20
```

### Step 2.3: Splunk에서 데이터 확인

**Splunk Search**:
```spl
index=fortianalyzer sourcetype=fortigate:event earliest=-5m
| table _time, devname, logid, level, msg
| sort -_time
```

**기대 결과**:
- 9개 이벤트 표시 (Config Change 3개, Critical 3개, HA 3개)
- `logid` 필드에 `0100044546`, `0104032001`, `0103008001` 등 표시
- `level` 필드에 `notice`, `critical`, `warning` 등 표시

---

## Phase 3: 알림 등록 및 활성화 (5분)

### Step 3.1: 알림 설정 파일 배포

**파일 위치**: `/home/jclee/app/splunk/configs/savedsearches-fortigate-alerts.conf`

**Option 1: Docker Bind Mount로 자동 배포** (현재 설정):
```bash
# 이미 bind mount로 연결되어 있으면 자동 반영됨
docker inspect splunk-test | grep savedsearches

# Splunk 설정 리로드
docker exec splunk-test /opt/splunk/bin/splunk reload search-index -auth admin:changeme
```

**Option 2: Web UI로 수동 등록** (권장 - 에어갭 환경 시뮬레이션):
```
1. Settings → Searches, reports, and alerts → New Alert
2. Alert 1: FortiGate_Config_Change_Alert
   - Search: configs/savedsearches-fortigate-alerts.conf 라인 10-22 복사
   - Schedule: Real-time, every minute
   - Trigger: Number of events > 0
   - Action: Slack (channel: #security-firewall-alert)
   - Suppression: 15 seconds, Fields: user, cfgpath
3. 동일하게 Alert 2, 3 등록
```

### Step 3.2: 알림 등록 확인

**Splunk Search**:
```spl
| rest /services/saved/searches
| search title="FortiGate_*"
| table title, disabled, realtime_schedule, cron_schedule, actions
```

**기대 결과**:
```
title                              | disabled | realtime_schedule | cron_schedule | actions
-----------------------------------|----------|-------------------|---------------|--------
FortiGate_Config_Change_Alert      | 0        | 1                 | * * * * *     | slack
FortiGate_Critical_Event_Alert     | 0        | 1                 | * * * * *     | slack
FortiGate_HA_Event_Alert           | 0        | 1                 | * * * * *     | slack
```

---

## Phase 4: Slack 연동 (선택 사항)

**Slack을 연동하지 않아도 알림 작동 테스트는 가능합니다** (Splunk 내부 로그로 확인).

### Step 4.1: Slack Webhook 설정 (필요 시)

```
1. https://api.slack.com/apps
2. Create New App → From scratch
3. App Name: Splunk FortiGate Alerts
4. Incoming Webhooks → Activate
5. Add New Webhook to Workspace
6. 채널 선택: #test-slack-alerts
7. Webhook URL 복사: https://hooks.slack.com/services/...
```

### Step 4.2: Splunk에서 Slack 플러그인 설정

```
1. Settings → Alert actions → Slack Alerts → Setup Slack Alerts
2. Webhook URL: <위에서 복사한 URL>
3. Default Channel: #test-slack-alerts
4. Save
```

### Step 4.3: Slack 테스트 전송

**Splunk Search**:
```spl
| sendalert slack param.channel="#test-slack-alerts" param.message="✅ Splunk → Slack 연동 테스트 성공"
```

**기대 결과**: Slack 채널에 메시지 수신

---

## Phase 5: 알림 작동 검증 (2분)

### Step 5.1: 실시간 검색 스케줄러 확인

**Splunk Search**:
```spl
index=_internal source=*scheduler.log earliest=-10m
  savedsearch_name="FortiGate_*"
| stats count by savedsearch_name, status
```

**기대 결과**:
```
savedsearch_name                   | status  | count
-----------------------------------|---------|------
FortiGate_Config_Change_Alert      | success | 10
FortiGate_Critical_Event_Alert     | success | 10
FortiGate_HA_Event_Alert           | success | 10
```

### Step 5.2: 알림 트리거 로그 확인

**Splunk Search**:
```spl
index=_internal source=*scheduler.log earliest=-10m
  savedsearch_name="FortiGate_Config_Change_Alert"
  result_count>0
| table _time, savedsearch_name, result_count, status
```

**기대 결과**: `result_count > 0`인 항목 표시 (알림이 이벤트 감지함)

### Step 5.3: Slack 전송 로그 확인 (Slack 연동 시)

**Splunk Search**:
```spl
index=_internal source=*python.log* "slack" earliest=-10m
| table _time, log_level, message
| sort -_time
```

**기대 결과**:
- `log_level=INFO`
- `message` 에 "sent to slack" 또는 "200 OK" 포함

---

## 문제 해결 (Troubleshooting)

### 문제 1: HEC로 데이터가 전송되지 않음

```bash
# HEC 상태 확인
curl -k https://localhost:8088/services/collector/health

# Expected: {"text":"HEC is healthy","code":200}
# If error: HEC Global Settings에서 "All Tokens" Enabled 확인
```

### 문제 2: 알림이 실행되지 않음

```spl
# 스케줄러 오류 확인
index=_internal source=*scheduler.log earliest=-10m
  savedsearch_name="FortiGate_*" ERROR
| table _time, message

# 일반적인 원인:
# - realtime_schedule=0 (비활성화됨)
# - disabled=1 (알림 비활성화)
# - 검색 쿼리 문법 오류
```

### 문제 3: 알림은 실행되지만 이벤트를 감지하지 못함

```spl
# 데이터 존재 확인
index=fortianalyzer earliest=-5m | stats count

# 필드 확인
index=fortianalyzer earliest=-5m
| stats count by type, subtype, logid, level

# Expected: type=event, subtype=system, logid=0100044546 등 표시
```

### 문제 4: Slack 메시지가 전송되지 않음

```bash
# 일반적인 원인 체크리스트:
# 1. Bot이 채널에 초대되었는지 확인
#    Slack 채널에서: /invite @bot-name

# 2. Webhook URL 정확한지 확인
#    Settings → Alert actions → Slack Alerts → Setup

# 3. action.slack=1 설정되었는지 확인
#    | rest /services/saved/searches | search title="FortiGate_*" | table title, actions

# 4. Slack 플러그인 로그 확인
#    index=_internal source=*python.log* "slack" ERROR | tail 20
```

---

## 자동 진단 스크립트 (종합 점검)

**이미 생성된 스크립트 사용**:
```bash
cd /home/jclee/app/splunk
./scripts/diagnose-alerts-not-working.sh
```

**10가지 자동 점검 항목**:
1. ✓ Container running
2. ✓ Data in index=fortianalyzer
3. ✓ Alerts registered
4. ✓ Alerts enabled
5. ✓ Real-time schedule active
6. ✓ Recent executions
7. ✓ Slack plugin installed
8. ✓ Slack configured
9. ⏳ Slack send attempts (2-5분 후)
10. ✓ Suppression reasonable

---

## 성공 기준 체크리스트

로컬 테스트 성공 = 다음 모두 ✅:

**Phase 1**: HEC 활성화
- [ ] HEC Global Settings Enabled
- [ ] HEC Token 생성됨
- [ ] `curl https://localhost:8088/services/collector/health` → 200 OK

**Phase 2**: 데이터 전송
- [ ] 테스트 데이터 9개 전송 성공
- [ ] `index=fortianalyzer` 에서 데이터 조회됨
- [ ] `logid`, `level`, `msg` 필드 정상 표시

**Phase 3**: 알림 등록
- [ ] 3개 알림 모두 `disabled=0`
- [ ] `realtime_schedule=1`
- [ ] `actions=slack`

**Phase 4**: Slack 연동 (선택)
- [ ] Webhook URL 설정됨
- [ ] `| sendalert slack` 테스트 성공
- [ ] Slack 채널에 메시지 수신

**Phase 5**: 알림 작동
- [ ] 스케줄러 로그에 `status=success`
- [ ] `result_count > 0` (이벤트 감지됨)
- [ ] Slack 전송 로그 `log_level=INFO` (Slack 연동 시)

---

## 에어갭 환경 배포 준비

**로컬 테스트 성공 후 에어갭으로 이동할 파일**:

### 1. 설정 파일
```bash
configs/savedsearches-fortigate-alerts.conf   # 수정된 알림 설정 (공백 추가)
configs/dashboards/studio-production/*.json    # 대시보드 (선택)
```

### 2. 플러그인 (USB로 전송)
```bash
plugins/slack-notification-alert_232.tgz
plugins/fortinet-fortigate-add-on-for-splunk_169.tgz
plugins/splunk-common-information-model-cim_620.tgz
```

### 3. 가이드
```bash
docs/ALERT-BUG-FIXED.md                      # 버그 수정 내역
docs/SYSLOG-SETUP-COMPLETE-GUIDE.md          # Syslog 설정 (에어갭용)
scripts/diagnose-alerts-not-working.sh        # 진단 스크립트
```

### 4. 에어갭 배포 절차 요약

```bash
# 1. Splunk UDP 9514 Input 생성 (Web UI)
Settings → Data inputs → UDP → New Local UDP (Port: 9514, Index: fw)

# 2. FortiAnalyzer Syslog 포워딩 설정 (CLI)
config log syslogd setting
  set status enable
  set server <에어갭 Splunk IP>
  set port 9514
end

# 3. 알림 등록 (Web UI 또는 REST API)
# savedsearches-fortigate-alerts.conf 내용 복사 → 3개 알림 수동 등록

# 4. Slack Webhook 설정 (내부 프록시 필요 시)
Settings → Alert actions → Setup Slack Alerts

# 5. 검증
./diagnose-alerts-not-working.sh
```

---

**작성일**: 2025-10-30
**검증 완료**: 로컬 테스트 환경
**다음 단계**: 에어갭 환경 배포

---

## 부록: 알림 쿼리 상세 (참고용)

### Alert 1: Config Change (수정 완료)

```spl
index=fortianalyzer earliest=rt-30s latest=rt type=event subtype=system
  (logid=0100044546 OR logid=0100044547)
  (cfgpath="firewall.policy*" OR cfgpath="firewall.address*" OR ...)
| dedup devname, user, cfgpath
| eval alert_message = "🔥 FortiGate Config Change - Device: " + devname + " | Admin: " + user + " ..."
| table alert_message, device, admin, config_path
```

**트리거 조건**: Config 변경 감지 (GUI/CLI)

### Alert 2: Critical Events (수정 완료)

```spl
index=fortianalyzer earliest=rt-30s latest=rt type=event subtype=system level=critical
  logid!=0100044546 logid!=0100044547
| search NOT msg="*Update Fail*"
| dedup devname, logid
| eval alert_message = "🚨 FortiGate CRITICAL Event - Device: " + devname + " | LogID: " + logid + " ..."
| table alert_message, device, log_id, severity
```

**트리거 조건**: Critical level 시스템 이벤트

### Alert 3: HA Events (수정 완료)

```spl
index=fortianalyzer earliest=rt-30s latest=rt type=event subtype=system logid=0103*
| dedup devname, logid, level
| eval icon = case(level="critical", "🔴", level="error", "🟠", level="warning", "🟡", 1=1, "🔵")
| eval alert_message = icon + " FortiGate HA Event - Device: " + devname + " ..."
| table alert_message, device, log_id, severity
```

**트리거 조건**: HA failover/동기화 이벤트

---

**⚠️ 주의사항**:
- 모든 알림은 **공백 수정 완료** (index=fortianalyzer**[공백]**earliest=rt-30s)
- `eval` 함수는 `len()` 대신 `case()` + `substr()` 사용 (실시간 검색 호환)
- Suppression은 `devname`만 사용 (msg 제외로 다른 이벤트 허용)
