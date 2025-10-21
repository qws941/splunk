# 활성 세션수 (Active Sessions) 가이드

## 📊 활성 세션수란?

**활성 세션수**는 FortiGate 방화벽 디바이스에서 현재 활성화된 네트워크 연결(세션)의 총 개수를 의미합니다.

### 세션(Session)의 정의

네트워크 세션은 다음과 같은 5-tuple로 구성됩니다:
```
1. Source IP Address (출발지 IP)
2. Source Port (출발지 포트)
3. Destination IP Address (목적지 IP)
4. Destination Port (목적지 포트)
5. Protocol (프로토콜: TCP/UDP/ICMP 등)
```

예제:
```
192.168.1.100:52341 → 8.8.8.8:443 (TCP)
```
→ 이것이 1개의 세션입니다.

---

## 🎯 왜 모니터링하는가?

### 1. 성능 지표
- FortiGate는 세션 수에 따라 성능이 좌우됨
- 모델별 최대 세션 수 제한:
  - FortiGate 60F: ~300,000 sessions
  - FortiGate 100F: ~600,000 sessions
  - FortiGate 200F: ~1,000,000 sessions

### 2. 이상 징후 감지
- 급격한 세션 증가 → DDoS 공격 가능성
- 비정상적인 패턴 → 봇넷 활동, 포트 스캔

### 3. 용량 계획
- 평균/최대 세션 수 추이 분석
- 디바이스 업그레이드 시기 판단

---

## 📈 대시보드에서의 표시

### 1. FortiGate 대시보드 (`fortinet-dashboard.xml`)

```xml
<panel>
  <title>🔌 활성 세션</title>
  <single>
    <search>
      <query>index=fw devname=$device_filter$ session=*
             earliest=$time_picker.earliest$ latest=$time_picker.latest$
| stats avg(session) as avg_sessions
| eval avg_sessions = round(avg_sessions, 0)</query>
    </search>
    <option name="underLabel">Active Sessions</option>
  </single>
</panel>
```

**데이터 소스**:
- **Index**: `fw` (FortiGate 로그 인덱스)
- **Field**: `session` (FortiGate가 보고하는 현재 세션 수)
- **계산**: 평균값 (선택한 시간 범위 내)

**출력 예시**:
```
12,345
Active Sessions
```

### 2. Performance 대시보드 (`splunk-dashboards.js`)

```javascript
<panel>
  <title>Active Sessions</title>
  <single>
    <search>
      <query>index=${this.baseIndex} session_count=* earliest=-5m
| stats avg(session_count) as sessions
| eval sessions=round(sessions,0)
| fields sessions</query>
    </search>
  </single>
</panel>
```

**데이터 소스**:
- **Index**: `fortigate_security` (또는 설정된 인덱스)
- **Field**: `session_count`
- **시간 범위**: 최근 5분
- **리프레시**: 30초마다 자동 갱신

---

## 🔍 세션 데이터 출처

### FortiGate에서 Splunk로 전송되는 로그 형식

```json
{
  "devname": "FGT-MAIN-01",
  "devid": "FG100F12345678",
  "vd": "root",
  "timestamp": 1729483200,
  "session_count": 12345,      // ← 활성 세션 수
  "cpu": 35,
  "memory": 45,
  "logver": 700000000,
  "type": "event",
  "subtype": "system"
}
```

### FortiGate CLI에서 확인

```bash
# 현재 세션 수 확인
get system performance status

# 출력 예시:
# CPU: 35%
# Memory: 45%
# Sessions: 12345
# Session Rate: 150/s
```

---

## 📊 세션 수 추이 그래프

**타임라인 차트** (Performance Dashboard):

```xml
<panel>
  <title>Active Sessions Timeline</title>
  <chart>
    <search>
      <query>index=fortigate_security session_count=* earliest=-1h
| timechart span=1m avg(session_count) by device_name</query>
    </search>
    <option name="charting.chart">area</option>
    <option name="charting.axisTitleY.text">Sessions</option>
  </chart>
</panel>
```

**출력 예시**:
```
         │
 15,000  │     ╱‾‾╲
         │    ╱    ╲    ╱‾╲
 10,000  │ __╱      ╲__╱   ╲___
         │
  5,000  │
         │
      0  └────────────────────────────→
         12:00  12:30  13:00  13:30
```

---

## 🎨 시각화 옵션

### Color Ranges (세션 수에 따른 색상)

```xml
<option name="rangeColors">["0x6DB7C6","0x65A637","0xF7BC38"]</option>
<option name="rangeValues">[0,5000]</option>
```

**색상 의미**:
- 🔵 Blue (0-5,000): 정상
- 🟢 Green (5,000-10,000): 보통
- 🟡 Yellow (10,000+): 높음

### Drilldown 설정

```xml
<drilldown>
  <link target="_blank">
    /app/search/search?q=index=fw session_count=*
    | timechart span=1m avg(session_count)
  </link>
</drilldown>
```

클릭 시 → 상세 세션 분석 페이지로 이동

---

## 📈 디바이스별 세션 비교

**Table 형식**:

```xml
<panel>
  <title>Device Session Status</title>
  <table>
    <search>
      <query>index=fw session_count=* earliest=-5m
| stats latest(session_count) as sessions,
        latest(cpu) as cpu,
        latest(memory) as mem
  by device_name
| eval health=case(
    sessions > 100000, "Critical",
    sessions > 50000, "Warning",
    1=1, "Healthy"
  )
| sort -sessions
| rename device_name as "Device",
         sessions as "Sessions",
         cpu as "CPU %",
         mem as "Memory %",
         health as "Status"</query>
    </search>
    <format type="color" field="Status">
      <colorPalette type="map">
        {"Healthy":"#53A051",
         "Warning":"#F8BE34",
         "Critical":"#DC4E41"}
      </colorPalette>
    </format>
  </table>
</panel>
```

**출력 예시**:

| Device      | Sessions | CPU % | Memory % | Status   |
|-------------|----------|-------|----------|----------|
| FGT-MAIN-01 | 85,432   | 65    | 72       | 🟡 Warning |
| FGT-EDGE-02 | 12,345   | 35    | 45       | 🟢 Healthy |
| FGT-DMZ-03  | 8,901    | 28    | 38       | 🟢 Healthy |

---

## ⚠️ 임계값 설정

### Alert 조건 예시

```spl
index=fw session_count=*
| stats avg(session_count) as avg_sessions by device_name
| where avg_sessions > 80000
```

**Alert Action**: Slack 알림 전송

```json
{
  "channel": "splunk-alerts",
  "text": "⚠️ High Session Count Detected",
  "attachments": [{
    "color": "warning",
    "fields": [
      {"title": "Device", "value": "FGT-MAIN-01"},
      {"title": "Sessions", "value": "85,432"},
      {"title": "Time", "value": "2025-10-21 14:30:00"}
    ]
  }]
}
```

---

## 🛠️ 문제 해결

### Q1: 세션 수가 0으로 표시됨

**원인**:
- FortiGate 로그에 `session` 또는 `session_count` 필드가 없음
- 로그 형식이 잘못됨

**해결**:
```bash
# FortiGate CLI에서 로그 형식 확인
show log syslogd setting

# session 정보 포함하도록 설정
config log syslogd setting
    set format default
    set status enable
end
```

### Q2: 세션 수가 비정상적으로 높음

**확인 사항**:
1. DDoS 공격 여부
2. 세션 타임아웃 설정
3. 불필요한 트래픽 (브로드캐스트, 멀티캐스트)

**FortiGate CLI**:
```bash
# 세션 테이블 확인
diagnose sys session list

# 세션 통계
diagnose sys session stat

# Top talkers
diagnose sys session top-cpu
```

### Q3: 대시보드에 데이터가 나타나지 않음

**디버깅**:
```spl
# 1. 인덱스에 데이터가 있는지 확인
index=fw earliest=-1h | head 10

# 2. session 필드가 있는지 확인
index=fw earliest=-1h | stats count by session

# 3. 필드명 확인
index=fw earliest=-1h | table _time devname session session_count

# 4. 로그 파싱 확인
index=fw earliest=-1h | rex field=_raw "session=(?<session_extracted>\d+)"
```

---

## 📚 참고 자료

- **FortiGate 세션 관리**: https://docs.fortinet.com/document/fortigate/latest/administration-guide/session-table
- **Splunk 타임차트**: https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Timechart
- **대시보드 예제**: `/home/jclee/app/splunk/dashboards/fortinet-dashboard.xml`

---

**Updated**: 2025-10-21
**작성자**: Claude Code
