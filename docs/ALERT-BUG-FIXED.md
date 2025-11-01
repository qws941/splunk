# 🐛 실시간 알림 버그 수정 완료

**발견일**: 2025-10-30
**버그**: 인덱스명과 `earliest` 파라미터 사이 공백 누락
**영향**: 3개 실시간 알림 모두 작동 불가
**수정**: ✅ 완료 (모든 알림에 공백 추가)

---

## 🔍 버그 상세

### 문제가 된 코드

```ini
# ❌ 잘못된 코드 (공백 없음)
search = index=fortianalyzerearliest=rt-30s latest=rt type=event subtype=system
                        ↑↑↑ 공백 없음! Splunk이 파싱 실패
```

### 수정된 코드

```ini
# ✅ 올바른 코드 (공백 있음)
search = index=fortianalyzer earliest=rt-30s latest=rt type=event subtype=system
                        ↑ 공백 추가! Splunk이 정상 파싱
```

### 영향받은 알림

1. **FortiGate_Config_Change_Alert** - Line 10 수정
2. **FortiGate_Critical_Event_Alert** - Line 52 수정
3. **FortiGate_HA_Event_Alert** - Line 91 수정

---

## ✅ 수정 사항 요약

| 알림명 | 라인 | 수정 전 | 수정 후 |
|--------|-----|---------|---------|
| Config Change | 10 | `index=fortianalyzerearliest=` | `index=fortianalyzer earliest=` |
| Critical Event | 52 | `index=fortianalyzerearliest=` | `index=fortianalyzer earliest=` |
| HA Event | 91 | `index=fortianalyzerearliest=` | `index=fortianalyzer earliest=` |

**파일**: `/home/jclee/app/splunk/configs/savedsearches-fortigate-alerts.conf`

---

## 🚀 배포 방법

### 방법 1: Docker Bind Mount (로컬 테스트)

**현재 상태**: 이미 bind mount로 연결됨
```bash
docker inspect splunk-test | grep savedsearches
# Should show: /home/jclee/app/splunk/configs/savedsearches-fortigate-alerts.conf
```

**작동 방식**: 파일 수정 즉시 Splunk에 반영됨 (재시작 필요 없음)

**검증**:
```bash
# Splunk 컨테이너 내부에서 확인
docker exec splunk-test cat /opt/splunk/etc/apps/search/local/savedsearches.conf | grep "index=fortianalyzer earliest"

# 3개 라인이 나와야 함 (공백 있는 버전)
```

**재시작** (선택):
```bash
# 설정 즉시 반영 (재시작 불필요)
# 하지만 확실히 하려면:
docker exec splunk-test /opt/splunk/bin/splunk reload search -auth admin:changeme
```

---

### 방법 2: REST API (에어갭 환경)

**파일 복사**:
```bash
# 수정된 파일을 에어갭 환경으로 전송 (USB, SCP 등)
scp configs/savedsearches-fortigate-alerts.conf airgap-splunk:/tmp/
```

**REST API로 등록**:
```bash
# 에어갭 Splunk 서버에서 실행
SPLUNK_URL="https://localhost:8089"
SPLUNK_USER="admin"
SPLUNK_PASS="your_password"

# Alert 1: Config Change
curl -ks -u "${SPLUNK_USER}:${SPLUNK_PASS}" \
  "${SPLUNK_URL}/servicesNS/nobody/search/saved/searches/FortiGate_Config_Change_Alert" \
  -d "search=search index=fortianalyzer earliest=rt-30s latest=rt type=event subtype=system (logid=0100044546 OR logid=0100044547)..." \
  -d "realtime_schedule=1" \
  -d "cron_schedule=* * * * *" \
  -d "action.slack=1" \
  -d "action.slack.param.channel=#security-firewall-alert"

# Alert 2, 3 동일하게 등록
```

---

### 방법 3: Web UI (수동, 권장)

**경로**: Settings → Searches, reports, and alerts

**각 알림별 수정** (3회 반복):

1. **검색**: `FortiGate_Config_Change_Alert` 클릭
2. **Edit → Edit Search** 클릭
3. **Search 쿼리 수정**:
   ```spl
   # 기존 (공백 없음)
   index=fortianalyzerearliest=rt-30s latest=rt

   # 수정 (공백 추가)
   index=fortianalyzer earliest=rt-30s latest=rt
   ```
4. **Save** 클릭
5. 나머지 2개 알림 동일 반복

---

## 🔍 검증 방법

### 자동 진단 스크립트 실행

```bash
cd /home/jclee/app/splunk
./scripts/diagnose-alerts-not-working.sh
```

**기대 결과** (10가지 체크):
- [x] ✓ Container running
- [x] ✓ Data in index=fortianalyzer
- [x] ✓ Alerts registered
- [x] ✓ Alerts enabled
- [x] ✓ Real-time schedule active
- [x] ✓ Recent executions
- [x] ✓ Slack plugin installed
- [x] ✓ Slack configured
- [ ] ⏳ Slack send attempts (2-5분 후)
- [x] ✓ Suppression reasonable

---

### 수동 검증 쿼리

**Step 1**: 알림 등록 확인
```spl
| rest /services/saved/searches
| search title="FortiGate_*"
| table title, search, realtime_schedule, disabled, actions
```

**기대 결과**:
- `search` 필드에 `index=fortianalyzer earliest=` 보임 (공백 있음)
- `realtime_schedule` = 1
- `disabled` = 0
- `actions` = slack

**Step 2**: 최근 실행 로그
```spl
index=_internal source=*scheduler.log
  savedsearch_name="FortiGate_*"
  earliest=-10m
| stats count by savedsearch_name, status, result_count
```

**기대 결과**:
- `status` = success (NOT error)
- `result_count` = 숫자 (매칭된 이벤트 수)

**Step 3**: Slack 전송 로그
```spl
index=_internal source=*python.log*
  "slack"
  earliest=-10m
| table _time, log_level, message
```

**기대 결과**:
- `log_level` = INFO (NOT ERROR)
- `message` 에 "sent to slack" 또는 "200 OK" 포함

---

## 🧪 테스트 시나리오

### 시나리오 1: Config Change 알림 테스트

**작업**:
1. FortiGate Web UI 접속
2. Policy 또는 Address 수정
3. 저장 (CLI: `set name test` → `next`)

**기대 결과** (30초 이내):
- Slack 채널에 메시지 수신:
  ```
  🔥 FortiGate Config Change
  Device: FGT-HQ-01
  Admin: admin (GUI)
  Path: firewall.policy
  Object: policy-123
  ```

---

### 시나리오 2: Critical Event 알림 테스트

**작업**: Critical level 이벤트 발생 대기 (예: 메모리 90% 초과)

**또는 수동 테스트**:
```spl
| sendalert slack param.channel="#security-firewall-alert" param.message="🚨 FortiGate CRITICAL Event - Device: TEST | LogID: 0104032001 | Description: Memory usage high"
```

**기대 결과**: Slack 메시지 즉시 수신

---

### 시나리오 3: HA Event 알림 테스트

**작업**: HA failover 테스트 (또는 대기)

**또는 수동 테스트**:
```spl
| sendalert slack param.channel="#security-firewall-alert" param.message="🔴 FortiGate HA Event - Device: FGT-HA-01 | Severity: critical | LogID: 0103008001 | Description: HA failover occurred"
```

---

## 🐛 추가로 발견된 문제들 (이미 수정 완료)

### 1. ~~Over-suppression~~ (이전에 수정됨)

**문제**: `alert.suppress.fields = devname, msg`
- 같은 장비에서 다른 메시지도 15초간 차단됨

**수정**: `alert.suppress.fields = devname` (또는 `user, cfgpath`)
- 같은 장비에서 다른 이벤트는 허용

### 2. ~~Eval 함수 에러~~ (이전에 수정됨)

**문제**: `eval details = if(len(cfgattr) > 100, ...)`
- `len()` 함수가 실시간 검색에서 오류

**수정**: `eval details = case(isnull(cfgattr), "No details", 1=1, substr(cfgattr, 1, 100))`
- `case()` + `substr()` 조합 사용

### 3. ~~시간 범위 충돌~~ (이전에 수정됨)

**문제**: SPL 쿼리 내 `earliest=` + Dispatch 설정 충돌

**수정**: SPL 쿼리에서만 시간 범위 지정 (`earliest=rt-30s latest=rt`)

---

## 📋 체크리스트 (에어갭 환경 배포용)

### 사전 준비
- [ ] 수정된 `savedsearches-fortigate-alerts.conf` 파일 준비
- [ ] 진단 스크립트 `diagnose-alerts-not-working.sh` 전송
- [ ] Slack Webhook URL 확인 (또는 대체 알림 방법)

### 배포 단계
- [ ] 파일을 에어갭 Splunk 서버로 전송 (USB/SCP)
- [ ] Splunk에 파일 배포:
  - [ ] Web UI로 수동 등록 (권장)
  - [ ] 또는 REST API로 등록
  - [ ] 또는 파일 직접 복사: `/opt/splunk/etc/apps/search/local/savedsearches.conf`
- [ ] Splunk 재시작 (파일 복사 방식인 경우):
  ```bash
  /opt/splunk/bin/splunk restart
  ```

### 검증 단계
- [ ] 진단 스크립트 실행: `./diagnose-alerts-not-working.sh`
- [ ] 10가지 체크 모두 ✓ 확인
- [ ] 수동 Slack 테스트:
  ```spl
  | sendalert slack param.channel="#security-firewall-alert" param.message="Test from airgap"
  ```
- [ ] 실제 이벤트 발생 (FortiGate 설정 변경)
- [ ] Slack 메시지 수신 확인 (30초 이내)

### 문제 발생 시
- [ ] 로그 확인:
  ```spl
  index=_internal source=*scheduler.log savedsearch_name="FortiGate_*" | tail 20
  index=_internal source=*python.log* "slack" ERROR | tail 20
  ```
- [ ] 공통 원인:
  - [ ] Slack bot이 채널에 초대되지 않음 (`/invite @bot-name`)
  - [ ] Webhook URL 잘못됨 (Settings → Alert actions 확인)
  - [ ] 네트워크/방화벽 (에어갭: 내부 프록시 필요)
  - [ ] 데이터 없음 (`index=fortianalyzer earliest=-5m | stats count`)

---

## 🎯 성공 기준

**알림 시스템 완전 작동 조건**:
1. ✅ 3개 알림 모두 등록됨 (`disabled=0`)
2. ✅ Real-time schedule 활성화 (`realtime_schedule=1`)
3. ✅ 최근 30분 내 실행 로그 있음
4. ✅ Slack 플러그인 설치 및 설정됨
5. ✅ 수동 테스트 성공 (`| sendalert slack ...`)
6. ✅ 실제 이벤트 발생 시 자동 알림 수신

---

## 📚 관련 문서

| 문서 | 위치 | 용도 |
|------|------|------|
| **버그 수정 파일** | `configs/savedsearches-fortigate-alerts.conf` | 배포용 (공백 수정 완료) |
| **진단 스크립트** | `scripts/diagnose-alerts-not-working.sh` | 10가지 자동 점검 |
| **진단 가이드** | `docs/REALTIME-ALERT-DIAGNOSTIC-GUIDE.md` | 6개 수동 쿼리 |
| **Slack 설정 가이드** | `docs/SLACK_ALERT_FORMATTING_GUIDE.md` | Block Kit, Webhook |

---

**버그 수정자**: Claude Code
**수정 일시**: 2025-10-30
**검증 상태**: ✅ 로컬 테스트 완료 (에어갭 배포 대기)

---

## 💡 인사이트

`★ Insight ─────────────────────────────────────`

**Why This Bug Happened**:
- Splunk 설정 파일은 공백에 민감함
- `index=fortianalyzerearliest=`는 하나의 토큰으로 인식됨
- `earliest=`를 인덱스명의 일부로 파싱 시도 → 실패

**Prevention**:
- 파일 수정 후 항상 `btool check` 실행:
  ```bash
  /opt/splunk/bin/splunk cmd btool savedsearches check
  ```
- Validation 실패 시 라인 번호와 에러 메시지 표시됨

**Best Practice**:
- Web UI로 저장 → 자동 문법 검증
- 파일 직접 편집 → 배포 전 Splunk에서 테스트
- REST API 사용 → 400 Bad Request 에러로 즉시 감지

`─────────────────────────────────────────────────`
