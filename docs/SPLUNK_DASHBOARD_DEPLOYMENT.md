# Splunk Web UI 대시보드 배포 가이드

**목적**: Splunk Web UI에 XML 대시보드 배포

---

## 📊 사용 가능한 대시보드

### 1. Correlation Analysis Dashboard (권장) ⭐
**파일**: `configs/dashboards/correlation-analysis.xml`
**크기**: 27KB
**기능**:
- 6개 고급 상관분석 규칙
- 자동 차단 권장 (AUTO_BLOCK, REVIEW_AND_BLOCK, MONITOR)
- 실시간 Slack 알림 테스트 패널
- 21개 패널, 13개 행

**데이터 소스**: `index=fw` (FortiAnalyzer Syslog)

### 2. FortiGate Operations Dashboard
**파일**: `configs/dashboards/fortigate-operations-integrated.xml`
**크기**: 18KB
**기능**:
- 운영 모니터링
- 트래픽 분석
- 차단/허용 이벤트

### 3. Slack Alert Control Dashboard
**파일**: `configs/dashboards/fortinet-management-slack-control.xml`
**크기**: 8.5KB
**기능**:
- Slack 알림 제어
- 테스트 메시지 전송

---

## 🚀 배포 방법

### Method 1: Splunk Web UI (수동 업로드)

#### Step 1: Splunk Web 로그인
```
https://your-splunk-host:8000
```

#### Step 2: 대시보드 생성
1. **Settings** → **User Interface** → **Dashboards**
2. **Create New Dashboard** 클릭
3. **Source** 탭 선택
4. XML 파일 내용 복사/붙여넣기
5. **Save** 클릭

#### Step 3: 대시보드 접근
```
https://your-splunk-host:8000/app/search/correlation_analysis
```

### Method 2: Splunk REST API (자동 배포)

#### 스크립트 사용
```bash
node scripts/deploy-dashboards.js
```

#### 수동 API 호출
```bash
# 환경변수 설정
export SPLUNK_HOST="your-splunk.example.com"
export SPLUNK_PORT="8089"
export SPLUNK_USERNAME="admin"
export SPLUNK_PASSWORD="your_password"
export SPLUNK_APP="search"

# 대시보드 배포
curl -k -u $SPLUNK_USERNAME:$SPLUNK_PASSWORD \
  https://$SPLUNK_HOST:$SPLUNK_PORT/servicesNS/admin/$SPLUNK_APP/data/ui/views \
  -d "name=correlation_analysis" \
  -d "eai:data=$(cat configs/dashboards/correlation-analysis.xml)"
```

### Method 3: Splunk App 배포

#### Step 1: App 디렉토리 생성
```bash
mkdir -p /opt/splunk/etc/apps/fortianalyzer_dashboard/default/data/ui/views/
```

#### Step 2: 대시보드 복사
```bash
cp configs/dashboards/*.xml \
  /opt/splunk/etc/apps/fortianalyzer_dashboard/default/data/ui/views/
```

#### Step 3: Splunk 재시작
```bash
/opt/splunk/bin/splunk restart
```

---

## ⚙️ 대시보드 설정

### 데이터 소스 확인

모든 대시보드는 **`index=fw`** 데이터를 사용합니다.

#### 데이터 확인
```spl
index=fortianalyzer earliest=-1h | head 10
```

**결과 없음?** → FortiAnalyzer Syslog 설정 확인 필요

### Syslog 설정 (FortiAnalyzer → Splunk)

#### FortiAnalyzer 설정
```
System Settings → Advanced → Syslog Server
- Server: <splunk-host>
- Port: 514 (UDP) or 6514 (TCP)
- Facility: local0
- Log Format: Syslog
```

#### Splunk 설정
```bash
# inputs.conf
[udp://514]
connection_host = ip
sourcetype = fortinet:fortigate:syslog
index = fw

# props.conf
[fortinet:fortigate:syslog]
SHOULD_LINEMERGE = false
TIME_PREFIX = date=
TIME_FORMAT = %Y-%m-%d time=%H:%M:%S
MAX_TIMESTAMP_LOOKAHEAD = 32
```

---

## 📈 대시보드 사용법

### Correlation Analysis Dashboard

#### 1. Time Range 선택
- `-24h@h` (지난 24시간)
- `-7d@d` (지난 7일)
- 사용자 정의

#### 2. 필터 적용
- **Correlation Type**: Multi-Factor Threat, Repeated High-Risk 등
- **Action Recommendation**: AUTO_BLOCK, REVIEW_AND_BLOCK, MONITOR

#### 3. 주요 패널
- **Row 1**: KPI 메트릭 (Deny Events, High-Risk IPs 등)
- **Row 2-11**: 6개 상관분석 규칙 (각 2개 패널)
- **Row 12**: Slack 알림 테스트 버튼 ⚡
- **Row 13**: 알림 히스토리 및 성공률

#### 4. Slack 알림 테스트
- **Row 12** 패널에서 "📤 Send Test Alert to Slack" 버튼 클릭
- 테스트 데이터 생성 (`correlation_score=95`)
- Slack #splunk-alerts 채널 확인

---

## 🔧 커스터마이징

### 대시보드 수정

#### 1. XML 편집
```bash
vim configs/dashboards/correlation-analysis.xml
```

#### 2. 주요 수정 사항

**시간 범위 기본값 변경** (line 9-11):
```xml
<default>
  <earliest>-24h@h</earliest>  <!-- 기본값 수정 -->
  <latest>now</latest>
</default>
```

**패널 색상 변경** (line 49):
```xml
<option name="rangeColors">["0x65A637","0xF7BC38","0xF58F39","0xD93F3C"]</option>
```

**SPL 쿼리 수정** (line 44-46):
```xml
<query>
index=fortianalyzer action=deny earliest=$time_picker.earliest$ latest=$time_picker.latest$
| stats count as deny_events
</query>
```

#### 3. XML 검증
```bash
python3 -c "import xml.etree.ElementTree as ET; ET.parse('configs/dashboards/correlation-analysis.xml'); print('✅ Valid')"
```

#### 4. 재배포
```bash
node scripts/deploy-dashboards.js
```

---

## 🐛 트러블슈팅

### 문제 1: 대시보드에 데이터가 안 보임

**원인**: `index=fw`에 데이터 없음

**해결**:
```spl
# 데이터 확인
index=fortianalyzer earliest=-1h | head 10

# 인덱스 확인
| eventcount summarize=false index=fw
```

### 문제 2: Slack 알림 버튼 작동 안 함

**원인**: Slack plugin 미설정

**해결**:
```bash
# Slack plugin 설치
/opt/splunk/bin/splunk install app slack_alerts

# 설정 확인
cat /opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf
```

### 문제 3: XML Parsing Error

**원인**: Special characters not encoded

**해결**:
```xml
<!-- ❌ WRONG -->
<choice value="REVIEW_AND_BLOCK">Review & Block</choice>

<!-- ✅ CORRECT -->
<choice value="REVIEW_AND_BLOCK">Review &amp; Block</choice>
```

**인코딩 규칙**:
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`

---

## 📚 관련 문서

- **Phase 4.1 리포트**: `docs/DASHBOARD_OPTIMIZATION_PHASE4.1_REPORT.md`
- **Slack 통합 가이드**: `docs/DASHBOARD_SLACK_INTEGRATION_GUIDE.md`
- **간단 설정 가이드**: `docs/SIMPLE_SETUP_GUIDE.md`

---

## 🎯 Quick Reference

### 배포 명령어
```bash
# REST API 배포
node scripts/deploy-dashboards.js

# 수동 복사 (Splunk App)
cp configs/dashboards/*.xml /opt/splunk/etc/apps/search/local/data/ui/views/

# Splunk 재시작
/opt/splunk/bin/splunk restart
```

### 대시보드 URL
```
https://your-splunk:8000/app/search/correlation_analysis
https://your-splunk:8000/app/search/fortigate_operations_integrated
https://your-splunk:8000/app/search/fortinet_management_slack_control
```

### 데이터 확인
```spl
index=fortianalyzer earliest=-1h | stats count by sourcetype, action, severity
```

---

**작성일**: 2025-10-23
**버전**: 1.0
**상태**: Production Ready
