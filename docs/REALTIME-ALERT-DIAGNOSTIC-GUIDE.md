# Splunk Real-time Alert 진단 & 플러그인 가이드

## 📋 목차
1. [실시간 진단 쿼리 (Web UI)](#1-실시간-진단-쿼리)
2. [다운로드된 플러그인 설치](#2-다운로드된-플러그인-설치)
3. [추천 플러그인 목록](#3-추천-플러그인-목록)
4. [문제 해결](#4-문제-해결)

---

## 1. 실시간 진단 쿼리

### 🎯 Splunk Web UI에서 바로 실행 가능한 쿼리

#### Step 1: 데이터 흐름 확인 (최근 5분)
```spl
index=fw earliest=-5m
| stats count as event_count,
        latest(_time) as last_event
| eval last_event=strftime(last_event, "%Y-%m-%d %H:%M:%S")
| eval status=if(event_count>0, "✅ 데이터 정상", "❌ 데이터 없음")
| table status, event_count, last_event
```

**기대 결과**:
- ✅ `status="✅ 데이터 정상"`, `event_count > 0` → 데이터 흐름 정상
- ❌ `event_count=0` → 데이터 수집 문제

---

#### Step 2: 등록된 실시간 알림 확인
```spl
| rest /services/saved/searches splunk_server=local
| search is_scheduled=1 realtime_schedule=1
| table title, cron_schedule, disabled, actions,
         alert.suppress.fields, alert.suppress.period,
         dispatch.earliest_time, dispatch.latest_time
```

**기대 결과**:
- `disabled=0` → 알림 활성화
- `realtime_schedule=1` → 실시간 알림 활성화
- `actions=slack` → Slack 액션 설정됨
- `alert.suppress.fields=devname` (NOT `devname,msg`) → 억제 설정 정상

---

#### Step 3: 알림 실행 로그 (최근 30분)
```spl
index=_internal source=*scheduler.log earliest=-30m
| search savedsearch_name="Critical_Events" OR savedsearch_name="*Alert"
| stats count,
        latest(_time) as last_run,
        values(status) as statuses,
        values(result_count) as results
  by savedsearch_name
| eval last_run=strftime(last_run, "%Y-%m-%d %H:%M:%S")
| sort -last_run
```

**기대 결과**:
- `count > 0` → 알림이 실행됨
- `last_run` → 마지막 실행 시간 확인
- `status=success` → 알림 실행 성공
- `result_count > 0` → 알림이 조건에 맞는 이벤트를 찾음

---

#### Step 4: Critical Events 쿼리 테스트
```spl
index=fw type=event
  (logid=0103040* OR
   msg=*fan*fail* OR
   msg=*power*fail* OR
   msg=*temperature*critical* OR
   msg=*hardware*error*)
| search NOT (
   msg=*update*fail* OR
   msg=*login*fail* OR
   msg=*Request*interrupted*)
| stats count as event_count,
        latest(_time) as last_event,
        values(msg) as messages,
        values(level) as severities
  by devname
| where event_count>0
```

**기대 결과**:
- `event_count > 0` → Critical 이벤트가 존재함
- 결과 없음 → 최근 Critical 이벤트 없음 (정상)

---

#### Step 5: Slack 액션 로그
```spl
index=_internal (source=*slack* OR source=*python.log*) earliest=-30m
| rex field=_raw "(?<log_level>ERROR|WARN|INFO)"
| stats count by log_level, source, _raw
| sort -count
```

**기대 결과**:
- `log_level=INFO` → Slack 메시지 전송 성공
- `log_level=ERROR` → Slack 전송 오류 확인 필요

---

#### Step 6: 억제(Suppression) 설정 확인
```spl
| rest /services/saved/searches splunk_server=local
| search title="Critical_Events"
| table title,
         alert.suppress,
         alert.suppress.period,
         alert.suppress.fields
```

**기대 결과**:
- `alert.suppress=1` → 억제 활성화
- `alert.suppress.period=15m` → 15분간 억제
- `alert.suppress.fields=devname` → 디바이스별 억제 (OK)
- ❌ `alert.suppress.fields=devname,msg` → 과도한 억제 (수정 필요)

---

## 2. 다운로드된 플러그인 설치

### ✅ 이미 다운로드된 플러그인

```bash
/home/jclee/app/splunk/plugins/
├── slack-notification-alert_232.tgz      # Slack 알림 (v2.32)
├── fortinet-fortigate-add-on-for-splunk_169.tgz  # FortiGate TA (v1.69)
└── splunk-common-information-model-cim_620.tgz   # CIM (v6.20)
```

### 📦 설치 방법 1: Docker Volume 마운트 (권장)

```bash
# 1. 플러그인을 Docker 볼륨에 복사
docker cp /home/jclee/app/splunk/plugins/slack-notification-alert_232.tgz \
  splunk-test:/opt/splunk/etc/apps/

docker cp /home/jclee/app/splunk/plugins/fortinet-fortigate-add-on-for-splunk_169.tgz \
  splunk-test:/opt/splunk/etc/apps/

# 2. 컨테이너 내부에서 압축 해제
docker exec splunk-test tar -xzf /opt/splunk/etc/apps/slack-notification-alert_232.tgz \
  -C /opt/splunk/etc/apps/

docker exec splunk-test tar -xzf /opt/splunk/etc/apps/fortinet-fortigate-add-on-for-splunk_169.tgz \
  -C /opt/splunk/etc/apps/

# 3. Splunk 재시작
docker restart splunk-test

# 4. 설치 확인
docker exec splunk-test ls -1 /opt/splunk/etc/apps/ | grep -E "(slack|forti)"
```

### 📦 설치 방법 2: Splunk Web UI (간편)

1. **Splunk Web UI 접속**: http://localhost:8800
2. **Apps → Manage Apps** 클릭
3. **Install app from file** 클릭
4. **Browse** 클릭 후 다음 파일 선택:
   - `/home/jclee/app/splunk/plugins/slack-notification-alert_232.tgz`
5. **Upload** 클릭
6. 반복하여 FortiGate TA도 설치
7. **Restart Splunk** 클릭

---

## 3. 추천 플러그인 목록

### 🎯 1. Slack Notification Alert (필수) ✅ 다운로드됨

- **버전**: 2.3.2 (2025-05-08)
- **호환성**: Splunk 9.3, 9.4
- **URL**: https://splunkbase.splunk.com/app/2878
- **상태**: ✅ **이미 다운로드됨** (`slack-notification-alert_232.tgz`)

**설치 후 설정**:
```bash
# Settings → Alert actions → Setup Slack Alerts
# Webhook URL 입력: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**테스트**:
```spl
| sendalert slack param.channel="#security-firewall-alert" param.message="테스트 메시지"
```

---

### 🎯 2. Fortinet FortiGate Add-on (필수) ✅ 다운로드됨

- **버전**: 1.69
- **URL**: https://splunkbase.splunk.com/app/2846
- **상태**: ✅ **이미 다운로드됨** (`fortinet-fortigate-add-on-for-splunk_169.tgz`)

**기능**:
- FortiGate 로그 파싱
- 필드 추출 (src_ip, dest_ip, action, logid 등)
- 대시보드 템플릿

**설치 후 설정**:
- 별도 설정 불필요 (자동 적용)
- 인덱스가 `fw` 또는 `fortianalyzer`면 자동으로 sourcetype 매칭

---

### 🎯 3. Alert Manager (선택)

- **URL**: https://splunkbase.splunk.com/app/2665
- **다운로드**: 수동 다운로드 필요
- **버전**: 3.0+ 권장

**기능**:
- 알림 이력 관리
- 알림 상태 추적 (New → In Progress → Resolved)
- 알림 할당 및 에스컬레이션
- 대시보드로 알림 모니터링

**설치**:
```bash
# Splunkbase에서 다운로드 후
cd /home/jclee/app/splunk/plugins
# alert_manager_*.tgz 다운로드
docker cp alert_manager_*.tgz splunk-test:/opt/splunk/etc/apps/
docker exec splunk-test tar -xzf /opt/splunk/etc/apps/alert_manager_*.tgz -C /opt/splunk/etc/apps/
docker restart splunk-test
```

---

### 🎯 4. Splunk CIM (Common Information Model) ✅ 다운로드됨

- **버전**: 6.2.0
- **URL**: https://splunkbase.splunk.com/app/1621
- **상태**: ✅ **이미 다운로드됨** (`splunk-common-information-model-cim_620.tgz`)

**기능**:
- 표준화된 데이터 모델
- `Fortinet_Security` 데이터 모델 제공
- `tstats` 쿼리 성능 향상 (30배 빠름)

**설치 후**:
```spl
# 데이터 모델 가속화 활성화 (Settings → Data models → Fortinet_Security → Edit → Acceleration)
```

---

## 4. 문제 해결

### ❌ 문제 1: "Slack 알림이 안 옴"

**진단 쿼리** (Step 5):
```spl
index=_internal source=*python.log* "slack" earliest=-30m
| rex field=_raw "(?<log_level>ERROR|WARN|INFO)"
| search log_level=ERROR
```

**해결 방법**:

1. **Bot 토큰 확인**:
   ```bash
   curl -X POST https://slack.com/api/auth.test \
     -H "Authorization: Bearer SLACK_BOT_TOKEN_PLACEHOLDER"
   ```

2. **채널에 Bot 초대**:
   ```
   Slack 채널에서: /invite @your-bot-name
   ```

3. **Webhook URL 재설정**:
   - Settings → Alert actions → Setup Slack Alerts
   - Webhook URL 재입력

---

### ❌ 문제 2: "알림은 실행되는데 결과가 없음"

**진단 쿼리** (Step 4 - Critical Events):
```spl
index=fw earliest=-24h type=event
  (logid=0103040* OR msg=*fan*fail*)
| stats count
```

**해결 방법**:

1. **쿼리 조건 완화**:
   - `earliest=-24h` → 최근 24시간으로 범위 확대
   - `msg=*fan*fail*` → 조건 하나씩 제거하며 테스트

2. **데이터 확인**:
   ```spl
   index=fw earliest=-5m | head 100
   ```

3. **로그 형식 확인**:
   - `type=event` 필드가 없을 수 있음
   - `logid` 형식 확인 (0103040001 vs 103040001)

---

### ❌ 문제 3: "시간 범위 충돌"

**확인**:
```spl
| rest /services/saved/searches
| search title="Critical_Events"
| table dispatch.earliest_time, dispatch.latest_time
```

**해결** (이미 적용됨):
- SPL 쿼리에서 `earliest=/latest=` 제거
- `dispatch.earliest_time=rt-5m`, `dispatch.latest_time=rt` 사용

---

### ❌ 문제 4: "과도한 억제"

**확인**:
```spl
| rest /services/saved/searches
| search title="Critical_Events"
| table alert.suppress.fields
```

**해결** (이미 적용됨):
- `alert.suppress.fields=devname,msg` → `devname` 변경
- 같은 디바이스에서 다른 메시지는 알림 허용

---

## 5. 다음 단계

### ✅ 체크리스트

- [ ] **Step 1-6 진단 쿼리 실행** (Splunk Web UI)
- [ ] **Slack Notification Alert 설치** (이미 다운로드됨)
- [ ] **FortiGate TA 설치** (이미 다운로드됨)
- [ ] **Slack Webhook URL 설정**
- [ ] **알림 재등록** (`register-alerts-interactive.ps1` 재실행)
- [ ] **테스트 알림 전송** (`| sendalert slack ...`)
- [ ] **실시간 모니터링** (`index=_internal source=*scheduler.log`)

### 📞 추가 지원

- **Splunk 공식 문서**: https://docs.splunk.com/Documentation/Splunk/latest
- **Slack 앱 설정**: https://api.slack.com/apps
- **GitHub Issues**: https://github.com/splunk/slack-alerts/issues

---

**생성일**: 2025-10-30
**버전**: 1.0
**상태**: ✅ Ready for production
