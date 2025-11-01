# ⚠️ 즉시 조치 필요: Splunk UDP 입력 설정

**상태**: FortiAnalyzer 전송 중 → Splunk 수신 안 함
**원인**: Splunk UDP 9514 입력이 설정되지 않음
**조치**: 아래 5분 설정 필요

---

## 🚨 지금 해야 할 일 (5분)

### Splunk Web UI에서 UDP 입력 추가

**1. 접속**:
```
URL: http://localhost:8800
ID: admin
PW: changeme
```

**2. 경로**:
```
Settings (상단 메뉴)
  → Data inputs
    → UDP
      → New Local UDP (오른쪽 상단 버튼)
```

**3. 설정값 입력**:

| 항목 | 값 | 설명 |
|------|---|------|
| Port | `9514` | FortiAnalyzer 전송 포트 |
| Source type | `Automatic` | 자동 감지 (또는 `fortianalyzer:syslog`) |
| Index | `fw` | 저장될 인덱스 |
| Connection host | `ip` | IP 주소를 호스트명으로 사용 |

**4. 저장**:
```
Review (다음 버튼)
  → Submit (완료)
```

**5. 확인** (재시작 불필요):
- "Successfully created UDP input" 메시지 확인
- 즉시 활성화됨 (Splunk 재시작 필요 없음)

---

## ✅ 설정 후 확인 (1분)

### 자동 검증 스크립트 재실행:
```bash
cd /home/jclee/app/splunk
./scripts/verify-syslog-setup.sh
```

**기대 결과**:
```
[3/6] Checking if Splunk is listening on UDP 9514...
✓ Splunk is listening on UDP 9514

[5/6] Checking for recent data in index=fw...
✓ Data found in index=fw: <숫자> events
```

### 수동 확인 (Splunk Search):
```spl
index=fw earliest=-5m | stats count
```
- **기대**: count > 0 (로그 수신 확인)

```spl
index=fw earliest=-5m | head 10
```
- **기대**: FortiGate 로그 샘플 10개 보임

---

## 🔍 설정 완료 후 필드 확인

**FortiGate 필드 파싱 확인**:
```spl
index=fw earliest=-5m
| stats count by devname, logid, type, subtype
| sort -count
```

**기대 결과**:
- `devname`: FortiGate 장비명 (예: FGT-HQ-01)
- `logid`: 로그 ID (예: 0100032001)
- `type`: 로그 타입 (traffic, event, utm)
- `subtype`: 서브타입 (system, forward, virus 등)

**만약 devname이 안 보이면**:
- FortiGate Add-on 활성화 대기 중 (최대 5분)
- 또는 Splunk 재시작 필요:
  ```bash
  docker restart splunk-test
  ```

---

## 📊 데이터 수신 확인 대시보드

**실시간 로그 확인**:
```spl
index=fw earliest=-5m
| timechart span=1m count
```
- 1분마다 로그 개수 그래프로 확인

**장비별 로그 분포**:
```spl
index=fw earliest=-1h
| stats count by devname
| sort -count
```
- 어느 FortiGate에서 로그가 가장 많이 오는지 확인

---

## 🎯 완료 후 다음 단계

**UDP 입력 설정 완료 → 데이터 수신 확인되면**:

1. **Slack Webhook 설정** (10분)
   - https://api.slack.com/apps → Create App
   - Incoming Webhooks → Activate
   - Splunk에서 Settings → Alert actions → Setup Slack

2. **진단 쿼리 실행** (15분)
   - `docs/REALTIME-ALERT-DIAGNOSTIC-GUIDE.md` 참고
   - 6개 진단 쿼리 순서대로 실행

3. **실시간 알림 테스트**
   - FortiGate 설정 변경 → Slack 알림 수신 확인

---

**⏱️ 소요 시간**: UDP 입력 설정 5분 + 검증 1분 = 총 6분

**다음 작업**: 위 설정 완료 후 `./scripts/verify-syslog-setup.sh` 재실행
