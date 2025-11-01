# Splunk Syslog 설정 빠른 시작 가이드 (에어갭 환경)

**생성일**: 2025-10-30
**예상 소요 시간**: 20분 (Splunk 5분 + FortiAnalyzer 10분 + 검증 5분)
**상태**: ✅ 플러그인 설치 완료, Syslog 설정 대기 중

---

## ✅ 완료된 작업 (자동화)

- [x] Docker 컨테이너 재생성 (bind mount 문제 해결)
- [x] Splunk 플러그인 3개 설치:
  - Slack Notification Alert v2.3.2
  - FortiGate Add-on v1.69 (로그 파싱)
  - Splunk CIM v6.2.0
- [x] UDP 9514 포트 노출 확인
- [x] Syslog 설정 가이드 생성

---

## 📋 당신이 해야 할 일 (3단계, 20분)

### 1단계: Splunk UDP 입력 설정 (5분) ⭐

```
http://localhost:8800 접속
로그인: admin / changeme
```

**경로**: Settings → Data inputs → UDP → **New Local UDP** 클릭

**설정값**:
```
Port: 9514
Source type: Automatic
Index: fw
Connection host: ip
```

**저장**: Review → Submit

**✅ 확인**: 재시작 불필요 (UDP 입력은 즉시 활성화됨)

---

### 2단계: FortiAnalyzer Syslog 포워딩 설정 (10분) ⭐

**FortiAnalyzer Web UI 접속**:
```
https://<your-faz-ip>
```

**경로**: Log & Report → Log Forwarding → Create New → **Generic Syslog**

**설정값**:
```
Name: splunk-syslog
Server IP/FQDN: <Splunk 서버 IP>
Port: 9514
Protocol: UDP
Mode: Realtime
Encryption: None
Format: RFC 5424
Facility: local7

Log Types (체크):
☑ Traffic
☑ Event
☑ UTM
```

**저장**: Apply → OK

**✅ 테스트** (FortiAnalyzer CLI):
```bash
execute log test-connectivity splunk-syslog
```

**기대 결과**:
```
Connectivity test to remote syslog server splunk-syslog succeeded.
```

---

### 3단계: 데이터 수신 검증 (5분) ⭐

**자동 검증 스크립트 실행**:
```bash
cd /home/jclee/app/splunk
./scripts/verify-syslog-setup.sh
```

**스크립트 체크 항목** (6가지):
1. ✓ Splunk 컨테이너 running & healthy
2. ✓ UDP 9514 포트 노출됨
3. ✓ Splunk UDP 9514 리스닝 중
4. ✓ FortiGate Add-on 설치됨
5. ✓ index=fw에 최근 5분간 데이터 있음
6. ✓ devname, logid 필드 파싱 작동

**수동 확인** (Splunk Web UI):
```spl
index=fw earliest=-5m | stats count
```
- **기대**: count > 0 (로그 수신 중)

```spl
index=fw earliest=-5m | stats count by host, sourcetype, devname
```
- **기대**: host=FortiAnalyzer IP, devname=FortiGate 장비명

---

## 🔧 문제 해결 (빠른 참조)

### ❌ FortiAnalyzer 연결 테스트 실패

**증상**:
```
Connectivity test failed. Connection refused.
```

**해결**:
1. Splunk UDP 입력 확인: Settings → Data inputs → UDP → 9514 Enabled 확인
2. 방화벽 확인:
   ```bash
   sudo firewall-cmd --list-ports | grep 9514
   # 없으면 추가:
   sudo firewall-cmd --add-port=9514/udp --permanent
   sudo firewall-cmd --reload
   ```
3. Docker 포트 확인:
   ```bash
   docker port splunk-test | grep 9514
   # 기대: 0.0.0.0:9514->9514/udp
   ```

---

### ❌ Splunk에 데이터 안 보임

**증상**: `index=fw earliest=-5m | stats count` → count = 0

**해결 1**: Sourcetype 확인
```spl
index=fw earliest=-5m | stats count by sourcetype
```
- 다른 sourcetype으로 들어왔으면 UDP 입력 재설정

**해결 2**: FortiAnalyzer 로그 전송 확인 (CLI)
```bash
diagnose test application logforward 1
```

**해결 3**: Splunk UDP 리스닝 확인
```bash
docker exec splunk-test netstat -uln | grep 9514
# 기대: udp  0  0  0.0.0.0:9514  0.0.0.0:*
```

---

### ❌ 필드 파싱 안 됨 (devname, logid 없음)

**증상**: 로그는 보이지만 FortiGate 필드가 추출 안 됨

**해결**: FortiGate Add-on 확인
```bash
docker exec splunk-test ls -d /opt/splunk/etc/apps/Splunk_TA_fortinet_fortigate
```
- 없으면: 플러그인 재설치 필요
- 있으면: Splunk 재시작
  ```bash
  docker restart splunk-test
  ```

---

## 🎯 다음 단계 (데이터 수신 확인 후)

### 1. Slack Webhook 설정 (10분)

**Slack App 생성**:
```
https://api.slack.com/apps → Create New App
Incoming Webhooks → Activate
Add New Webhook to Workspace
채널 선택: #security-firewall-alert
Webhook URL 복사
```

**Splunk 설정**:
```
Settings → Alert actions → Setup Slack Alerts
Webhook URL 입력
Default Channel: #security-firewall-alert
Save
```

**테스트**:
```spl
| sendalert slack param.channel="#security-firewall-alert" param.message="✅ Syslog 설정 완료!"
```

---

### 2. 진단 쿼리 실행 (15분)

**가이드**: `docs/REALTIME-ALERT-DIAGNOSTIC-GUIDE.md`

**6개 진단 쿼리**:
1. 데이터 흐름 확인 (`index=fw earliest=-5m | stats count`)
2. 등록된 알림 확인 (`| rest /services/saved/searches`)
3. 알림 실행 로그 (`index=_internal source=*scheduler.log`)
4. Critical Events 쿼리 테스트
5. Slack 액션 로그 (`index=_internal source=*python.log* "slack"`)
6. 억제 설정 확인 (`alert.suppress.fields`)

---

## 📊 유용한 쿼리 모음

### 기본 확인

```spl
# 최근 5분 로그 샘플
index=fw earliest=-5m | head 20

# 장비별 로그 개수
index=fw earliest=-1h | stats count by devname | sort -count

# 로그 타입별 분포
index=fw earliest=-1h | stats count by type, subtype | sort -count

# 시간대별 로그 양
index=fw earliest=-24h | timechart span=1h count by devname
```

### 설정 변경 확인

```spl
index=fw earliest=-1h type=event subtype=system
  (logid=0100044546 OR logid=0100044547 OR cfgpath=*)
| table _time, devname, user, cfgpath, cfgobj, cfgattr
| sort -_time
```

### Critical Events 확인

```spl
index=fw earliest=-24h type=event subtype=system
  (level=critical OR level=error)
| stats count by devname, level, msg
| sort -count
```

---

## 📚 관련 문서

| 문서 | 위치 | 설명 |
|------|------|------|
| **완전 가이드** | `docs/SYSLOG-SETUP-COMPLETE-GUIDE.md` | 상세 설정 + 문제 해결 (399줄) |
| **검증 스크립트** | `scripts/verify-syslog-setup.sh` | 자동 검증 (6가지 체크) |
| **진단 가이드** | `docs/REALTIME-ALERT-DIAGNOSTIC-GUIDE.md` | 6개 진단 쿼리 |
| **플러그인 상태** | `docs/PLUGIN-INSTALLATION-SUCCESS.md` | 플러그인 설치 완료 |

---

## ✅ 성공 기준

**1단계 완료 (Syslog 설정)**:
- [x] Splunk UDP 9514 입력 활성화
- [x] FortiAnalyzer Syslog 포워딩 설정
- [ ] FortiAnalyzer 연결 테스트 성공
- [ ] Splunk에서 `index=fw` 데이터 확인
- [ ] 필드 파싱 확인 (`devname`, `logid`)

**2단계 완료 (알림 파이프라인)**:
- [ ] Slack Webhook 설정
- [ ] 진단 쿼리 6개 실행
- [ ] 실시간 알림 작동 확인
- [ ] Slack 채널에 테스트 메시지 수신

---

**다음 작업**: 위 3단계 완료 후 검증 스크립트 실행
**예상 소요 시간**: 총 45분 (설정 20분 + Slack 10분 + 진단 15분)
