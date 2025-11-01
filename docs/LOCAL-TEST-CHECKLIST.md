# 로컬 테스트 환경 완료 체크리스트

**목적**: 에어갭 환경 배포 전 로컬에서 전체 워크플로우 검증
**현재 상태**: 플러그인 설치 완료, FortiAnalyzer 전송 중

---

## ✅ 이미 완료된 것 (자동화)

- [x] Docker 컨테이너 생성 및 실행
- [x] Splunk 플러그인 3개 설치:
  - [x] Slack Notification Alert v2.3.2
  - [x] FortiGate Add-on v1.69
  - [x] Splunk CIM v6.2.0
- [x] UDP 9514 포트 노출
- [x] FortiAnalyzer Syslog 전송 설정 (이미 전송 중)

---

## 📋 로컬 테스트 완료 단계

### Phase 1: 데이터 수신 확인 (5분)

**현재 상태**: FortiAnalyzer 전송 중 → Splunk UDP 입력 설정 필요

**작업**:
```
http://localhost:8800 접속
Settings → Data inputs → UDP → New Local UDP
Port: 9514, Index: fw, Sourcetype: Automatic
Submit
```

**검증**:
```bash
./scripts/verify-syslog-setup.sh
```

**기대 결과**:
- [ ] ✓ Splunk UDP 9514 리스닝 중
- [ ] ✓ index=fw에 데이터 있음 (count > 0)
- [ ] ✓ devname, logid 필드 파싱됨

---

### Phase 2: Slack 알림 테스트 (10분)

**Slack Webhook 생성**:
```
https://api.slack.com/apps
Create New App → From scratch
Incoming Webhooks → Activate
Add New Webhook to Workspace
채널 선택: #test-slack-alerts
Webhook URL 복사: https://hooks.slack.com/services/...
```

**Splunk 설정**:
```
Settings → Alert actions → Setup Slack Alerts
Webhook URL: <위에서 복사한 URL>
Default Channel: #test-slack-alerts
Save
```

**테스트 전송**:
```spl
| sendalert slack param.channel="#test-slack-alerts" param.message="✅ 로컬 테스트 - Splunk → Slack 연동 성공"
```

**검증**:
- [ ] Slack 채널에 메시지 수신됨
- [ ] Bot 이름 확인됨
- [ ] 타임스탬프 정상

---

### Phase 3: 실시간 알림 작동 확인 (15분)

**진단 쿼리 6개 실행**:
```bash
# 가이드 참고
cat docs/REALTIME-ALERT-DIAGNOSTIC-GUIDE.md
```

**Step 1**: 데이터 흐름 확인
```spl
index=fw earliest=-5m | stats count as event_count
```
- [ ] event_count > 0

**Step 2**: 등록된 알림 확인
```spl
| rest /services/saved/searches
| search realtime_schedule=1 disabled=0
| table title, cron_schedule, actions, alert.suppress
```
- [ ] 3개 알림 보임 (Config Change, Critical Events, HA Events)

**Step 3**: 알림 실행 로그
```spl
index=_internal source=*scheduler.log earliest=-30m
  savedsearch_name="FortiGate_*"
| stats count by savedsearch_name, status
```
- [ ] 최근 30분 내 실행 기록 있음

**Step 4**: Critical Events 쿼리 테스트
```spl
index=fw earliest=-24h type=event subtype=system
  (level=critical OR level=alert OR level=error)
  NOT (msg="*Update Fail*")
| stats count by devname, level, msg
| sort -count
```
- [ ] 결과 정상 (에러 없음)

**Step 5**: Slack 액션 로그
```spl
index=_internal source=*python.log* "slack" earliest=-30m
| table _time, log_level, message
```
- [ ] Slack 전송 로그 보임 (log_level=INFO)

**Step 6**: 억제 설정 확인
```spl
| rest /services/saved/searches
| search title="FortiGate_*"
| table title, alert.suppress.fields, alert.suppress.period
```
- [ ] alert.suppress.fields = devname (NOT devname,msg)
- [ ] alert.suppress.period = 3600s

---

### Phase 4: 대시보드 검증 (5분)

**대시보드 접속**:
```
http://localhost:8800/en-US/app/search/fortigate_operations
```

**확인 사항**:
- [ ] 패널 7개 모두 데이터 표시
- [ ] 시간 필터 작동 (Last 24 hours)
- [ ] FortiGate 장비명 필터 작동
- [ ] 드릴다운 동작 (클릭 시 상세 검색)

**테스트 쿼리** (대시보드 내):
```spl
# Config Changes 패널
index=fw earliest=-24h (logid="0100032*" OR logid="0101*")
| stats count by devname, user, cfgpath
| sort -count
```
- [ ] 결과 정상, 에러 없음

---

## 🎯 로컬 테스트 완료 기준

**모든 Phase 완료 시**:
- [x] Phase 1: 데이터 수신 (5분)
- [ ] Phase 2: Slack 알림 (10분)
- [ ] Phase 3: 실시간 알림 (15분)
- [ ] Phase 4: 대시보드 (5분)

**총 소요 시간**: 35분

---

## 📦 에어갭 환경 배포 준비물

**로컬 테스트 완료 후 에어갭으로 이동할 파일**:

### 1. Splunk 플러그인 (3개)
```
plugins/slack-notification-alert_232.tgz
plugins/fortinet-fortigate-add-on-for-splunk_169.tgz
plugins/splunk-common-information-model-cim_620.tgz
```

### 2. 설정 파일 (5개)
```
configs/savedsearches-fortigate-alerts.conf  # 실시간 알림 3개
configs/dashboards/studio-production/*.json  # 대시보드 5개
configs/faz-to-splunk-hec.conf              # FortiAnalyzer 설정 (참고용)
```

### 3. 배포 가이드 (3개)
```
docs/SYSLOG-SETUP-COMPLETE-GUIDE.md        # Syslog 설정 가이드
docs/QUICK-START-SYSLOG.md                 # 빠른 시작 가이드
docs/IMMEDIATE-ACTION-REQUIRED.md          # 즉시 조치 가이드
```

### 4. 검증 스크립트 (1개)
```
scripts/verify-syslog-setup.sh              # 자동 검증 (6가지 체크)
```

---

## 🚀 에어갭 환경 배포 순서 (로컬 테스트 완료 후)

### 1. 사전 준비 (에어갭 환경)
- [ ] Splunk Enterprise 설치 (동일 버전 권장)
- [ ] Docker 또는 VM 준비 (포트: 8000, 8089, 8088, 9514)
- [ ] FortiAnalyzer 접근 가능 (Web UI 또는 CLI)
- [ ] Slack Webhook URL 준비 (인터넷 접근 필요)

### 2. 플러그인 설치
```bash
# USB 또는 파일 전송으로 플러그인 복사
scp plugins/*.tgz airgap-splunk:/tmp/

# 에어갭 Splunk에 설치
tar -xzf /tmp/slack-notification-alert_232.tgz -C /opt/splunk/etc/apps/
tar -xzf /tmp/fortinet-fortigate-add-on-for-splunk_169.tgz -C /opt/splunk/etc/apps/
tar -xzf /tmp/splunk-common-information-model-cim_620.tgz -C /opt/splunk/etc/apps/

# Splunk 재시작
/opt/splunk/bin/splunk restart
```

### 3. UDP 입력 설정
```
Settings → Data inputs → UDP → New Local UDP
Port: 9514, Index: fw, Sourcetype: Automatic
```

### 4. FortiAnalyzer Syslog 포워딩
```
Log & Report → Log Forwarding → Create New → Generic Syslog
Server: <에어갭 Splunk IP>, Port: 9514, Protocol: UDP
```

### 5. 검증
```bash
./verify-syslog-setup.sh
```

### 6. Slack 설정
```
Settings → Alert actions → Setup Slack Alerts
Webhook URL: <Slack Webhook>
```

### 7. 알림 등록
```bash
# savedsearches-fortigate-alerts.conf 복사
cp savedsearches-fortigate-alerts.conf /opt/splunk/etc/apps/search/local/

# Splunk 재시작
/opt/splunk/bin/splunk restart
```

### 8. 대시보드 배포
```
Dashboards → Create New Dashboard → Dashboard Studio
Source → 붙여넣기 (JSON 파일 내용)
Save
```

---

## 📊 로컬 vs 에어갭 차이점

| 항목 | 로컬 테스트 | 에어갭 환경 |
|------|-----------|-----------|
| **Splunk** | Docker 컨테이너 | 물리/VM 서버 |
| **플러그인** | stdin pipe 설치 | tar 수동 설치 |
| **파일 전송** | git pull | USB/SCP |
| **인터넷** | 가능 (Slack) | 불가능 (내부 Webhook 서버 필요) |
| **FortiAnalyzer** | 테스트 장비 | 프로덕션 장비 |
| **데이터** | 테스트 로그 | 실제 운영 로그 |

---

## 💡 에어갭 환경 특이사항

**Slack 알림 (인터넷 불가)**:
- Option 1: 내부 Slack Webhook 프록시 서버 구축
- Option 2: Email 알림으로 대체
- Option 3: SNMP Trap 전송

**플러그인 업데이트**:
- Splunkbase 접근 불가 → USB로 수동 전송
- 주기적으로 외부에서 다운로드 → USB 반입

**문서 접근**:
- 모든 가이드 오프라인 복사 필요
- PDF 변환 권장

---

**현재 작업**: 로컬 Phase 1 완료 (UDP 입력 설정) → 검증 스크립트 재실행

**다음 단계**: Phase 1 성공 확인 → Phase 2 Slack 테스트
