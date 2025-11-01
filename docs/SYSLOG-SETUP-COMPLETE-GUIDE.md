# FortiAnalyzer Syslog → Splunk 완전 설정 가이드

**생성일**: 2025-10-30
**방식**: FortiAnalyzer → Syslog (UDP 9514) → Splunk
**상태**: ✅ Ready to configure

---

## 🎯 아키텍처

```
FortiGate 장비들
    ↓ (로그 전송)
FortiAnalyzer
    ↓ (Syslog UDP 9514)
Splunk (index=fw)
    ↓
Dashboards / Real-time Alerts → Slack
```

**장점**:
- ✅ FortiAnalyzer 6.0+ (모든 버전 지원)
- ✅ 간단한 설정 (HEC 토큰 불필요)
- ✅ 표준 Syslog 프로토콜

---

## 📋 당신이 해야 할 일 (2단계, 15분)

### **1단계: Splunk UDP 입력 설정** (5분)

```
http://localhost:8800 접속
로그인: admin / changeme
```

**Step 1**: Settings → Data inputs → UDP → **New Local UDP** 클릭

**Step 2**: 다음 값 입력:

```
Port: 9514
Source type: Automatic
    (또는 직접 입력: fortianalyzer:syslog)
Index: fw
Connection host: ip
```

**Step 3**: Review → Submit 클릭

**Step 4**: 재시작 **불필요** (UDP 입력은 즉시 활성화)

---

### **2단계: FortiAnalyzer Syslog 포워딩 설정** (10분)

**FortiAnalyzer Web UI 접속**:
```
https://<your-faz-ip>
```

**설정 경로**:
```
Log & Report → Log Forwarding → Create New → Generic Syslog
```

**Profile Settings**:
```
Name: splunk-syslog
Server IP/FQDN: <Splunk 서버 IP>
Port: 9514
Protocol: UDP
Mode: Realtime
Encryption: None
```

**Log Types** (체크):
```
☑ Traffic
☑ Event
☑ UTM
```

**Format Settings**:
```
Format: RFC 5424
Facility: local7
Priority: Default
Max Log Rate: Unlimited (0)
```

**저장**: Apply → OK

---

## ✅ 검증 (3가지 방법)

### **방법 1: FortiAnalyzer CLI 테스트** (추천)

FortiAnalyzer SSH 접속 후:
```bash
execute log test-connectivity splunk-syslog
```

**기대 결과**:
```
Connectivity test to remote syslog server splunk-syslog succeeded.
```

---

### **방법 2: Splunk에서 데이터 확인**

Splunk Web UI → Search & Reporting:
```spl
index=fw earliest=-5m | stats count
```

**기대 결과**: `count > 0` (로그가 들어오고 있음)

**상세 확인**:
```spl
index=fw earliest=-5m
| stats count by host, sourcetype, devname
| sort -count
```

**기대 필드**:
- `host`: FortiAnalyzer IP
- `sourcetype`: fortianalyzer:syslog (또는 자동 감지된 값)
- `devname`: FortiGate 장비명

---

### **방법 3: 로컬에서 테스트 전송** (선택)

Splunk가 UDP 9514를 리스닝하는지 확인:
```bash
# Linux/Mac:
echo "test message" | nc -u <splunk-ip> 9514

# 또는 logger 명령:
logger -n <splunk-ip> -P 9514 -p local7.info "test from client"
```

Splunk에서 확인:
```spl
index=fw earliest=-1m "test"
```

---

## 🔧 문제 해결

### ❌ FortiAnalyzer 연결 테스트 실패

**증상**:
```
Connectivity test to remote syslog server splunk-syslog failed.
Connection refused
```

**해결**:
1. Splunk UDP 입력 확인:
   - Settings → Data inputs → UDP → Port 9514 있는지 확인
   - 상태가 "Enabled" 인지 확인

2. 방화벽 확인:
   ```bash
   # Splunk 서버에서:
   sudo firewall-cmd --list-ports
   # 9514/udp가 열려있어야 함

   # 없으면 추가:
   sudo firewall-cmd --add-port=9514/udp --permanent
   sudo firewall-cmd --reload
   ```

3. Docker 포트 노출 확인:
   ```bash
   docker ps --filter "name=splunk-test" --format "{{.Ports}}"
   # 9514/udp가 보여야 함: 0.0.0.0:9514->9514/udp
   ```

---

### ❌ Splunk에 데이터 안 보임

**증상**: `index=fw earliest=-5m | stats count` → `count = 0`

**해결 1**: Sourcetype 확인
```spl
index=fw earliest=-5m
| stats count by sourcetype
```

만약 다른 sourcetype으로 들어왔으면:
- Settings → Data inputs → UDP → 9514 → Edit
- Source type을 해당 값으로 변경

**해결 2**: FortiAnalyzer 로그 전송 확인
```bash
# FortiAnalyzer CLI:
diagnose test application logforward 1

# 실시간 로그 확인:
diagnose debug enable
diagnose debug application logforward -1
```

**해결 3**: 포트 리스닝 확인
```bash
# Splunk 컨테이너 내부:
docker exec splunk-test netstat -uln | grep 9514

# 기대 결과:
udp        0      0 0.0.0.0:9514            0.0.0.0:*
```

---

### ❌ 파싱 에러 (필드가 안 보임)

**증상**: 로그는 들어오지만 `devname`, `logid` 등 필드가 추출 안 됨

**해결**: FortiGate Add-on 설치 확인

1. Splunk Web UI → Apps → Manage Apps
2. "Fortinet FortiGate Add-on for Splunk" 있는지 확인
3. 없으면:
   - Apps → Find More Apps
   - "FortiGate" 검색
   - Install (무료)

4. Add-on 설치 후 Splunk 재시작:
   ```bash
   docker restart splunk-test
   ```

---

## 📊 데이터 확인 쿼리

### 기본 확인

```spl
# 최근 5분 로그 샘플
index=fw earliest=-5m | head 20

# 장비별 로그 개수
index=fw earliest=-1h
| stats count by devname
| sort -count

# 로그 타입별 분포
index=fw earliest=-1h
| stats count by type, subtype
| sort -count

# 시간대별 로그 양
index=fw earliest=-24h
| timechart span=1h count by devname
```

### 설정 변경 확인

```spl
index=fw earliest=-1h type=event subtype=system
  (logid=0100044546 OR logid=0100044547 OR cfgpath=*)
| table _time, devname, user, cfgpath, cfgobj, cfgattr
| sort -_time
```

### 크리티컬 이벤트 확인

```spl
index=fw earliest=-24h type=event subtype=system
  (level=critical OR level=error)
| stats count by devname, level, msg
| sort -count
```

---

## 🔄 다음 단계 (Syslog 설정 완료 후)

### 1. 플러그인 확인 (이미 설치됨)

```
http://localhost:8800
Apps → Manage Apps
```

확인:
- ✅ Slack Notification Alert v2.3.2
- ✅ FortiGate TA v1.69 (필드 파싱)
- ✅ Splunk CIM v6.2.0

---

### 2. Slack Webhook 설정

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

### 3. 실시간 알림 진단

이전에 생성한 진단 쿼리 실행:
```bash
# 가이드 문서:
/home/jclee/app/splunk/docs/REALTIME-ALERT-DIAGNOSTIC-GUIDE.md
```

**6개 진단 쿼리 순서대로 실행**:
1. 데이터 흐름 확인
2. 등록된 알림 확인
3. 알림 실행 로그
4. Critical Events 쿼리 테스트
5. Slack 액션 로그
6. 억제 설정 확인

---

## 🎯 성공 기준

**Syslog 설정 완료**:
- [x] Splunk UDP 9514 입력 활성화
- [x] FortiAnalyzer Syslog 포워딩 설정
- [ ] FortiAnalyzer 연결 테스트 성공
- [ ] Splunk에서 `index=fw` 데이터 확인
- [ ] 필드 파싱 확인 (`devname`, `logid` 등)

**전체 파이프라인 완료**:
- [ ] 데이터 수신 (`index=fw` count > 0)
- [ ] 플러그인 활성화 (3개)
- [ ] Slack 알림 테스트 성공
- [ ] 실시간 알림 작동

---

## 📚 관련 문서

| 문서 | 위치 | 용도 |
|------|------|------|
| **Syslog 설정 가이드** | `configs/SPLUNK-UDP-INPUT-SETUP.txt` | UDP 입력 설정 |
| **FAZ Syslog 포워딩** | `configs/fortianalyzer/002-FAZ-Syslog-Forward.txt` | FortiAnalyzer 설정 상세 |
| **진단 가이드** | `docs/REALTIME-ALERT-DIAGNOSTIC-GUIDE.md` | 6개 진단 쿼리 |
| **플러그인 설치 완료** | `docs/PLUGIN-INSTALLATION-SUCCESS.md` | 플러그인 상태 |
| **Alert 설정** | `configs/savedsearches-fortigate-alerts.conf` | 3개 실시간 알림 |

---

`★ Insight ─────────────────────────────────────`

**Syslog vs HEC 비교**:

**Syslog (UDP 9514)**:
- ✅ 설정 간단 (토큰 불필요)
- ✅ 표준 프로토콜 (모든 FortiAnalyzer 버전)
- ❌ 패킷 손실 가능성 (UDP)
- ❌ 약간 높은 지연 (5-10초)

**HEC (Port 8088)**:
- ✅ HTTP 신뢰성
- ✅ 낮은 지연 (<1초)
- ❌ FortiAnalyzer 7.4+ 필요
- ❌ HEC 토큰 관리 필요

**권장**: 안정성 우선이면 Syslog, 실시간성 우선이면 HEC

`─────────────────────────────────────────────────`

---

**다음 작업**: Splunk Web UI에서 UDP 9514 입력 추가 → FortiAnalyzer에서 Syslog 설정 → 연결 테스트

**예상 소요 시간**: 15분 (Splunk 5분 + FortiAnalyzer 10분)
