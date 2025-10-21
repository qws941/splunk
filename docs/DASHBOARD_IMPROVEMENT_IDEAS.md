# 대시보드 개선 아이디어 (Dashboard Enhancement Ideas)

**기준 버전**: v1.0.0 (414 lines, 16KB)
**작성일**: 2025-10-21
**출처**: GitHub/Splunk 커뮤니티 Best Practices 분석

---

## 📊 현재 대시보드 강점

- ✅ **객관적 데이터 중심**: 주관적 분석 용어 제거 완료
- ✅ **WCAG Level AA 준수**: 접근성 확보
- ✅ **경량화**: 31KB → 16KB (48% 감소)
- ✅ **일관성**: 전체 쿼리 index=fw 통일
- ✅ **실제 통합**: Splunk Alert Actions 기반 실시간 알림

---

## 🎯 개선 방향 (4개 카테고리)

### 1. 시각화 고도화 (Visualization Enhancements)

#### 1.1 Custom Visualizations
**출처**: splunk/dashboard-studio-resources

**현재 상태**: 기본 차트/테이블만 사용
```xml
<chart>
  <option name="charting.chart">line</option>
</chart>
```

**개선 방안**:
```xml
<!-- Sankey Diagram - 트래픽 흐름 시각화 -->
<viz type="splunk.sankey">
  <search>
    <query>index=fw | stats sum(bytes) by src_ip, dst_ip</query>
  </search>
  <option name="height">400</option>
  <option name="linkColor">gradient</option>
</viz>

<!-- Heatmap - 시간대별 공격 패턴 -->
<viz type="splunk.heatmap">
  <search>
    <query>
      index=fw severity IN (critical, high)
      | bin _time span=1h
      | stats count by _time, attack_type
    </query>
  </search>
  <option name="colorMode">categorical</option>
</viz>

<!-- Geographic Map - 공격 출발지 지도 -->
<viz type="splunk.geospatial">
  <search>
    <query>
      index=fw
      | iplocation src_ip
      | geostats latfield=lat longfield=lon count by Country
    </query>
  </search>
</viz>
```

**필요 리소스**:
- Splunk Dashboard Studio 활성화
- Custom Visualization App 설치 (`$SPLUNK_HOME/etc/apps/`)

**우선순위**: P1 (High Impact, 시각적 개선 효과 큼)

---

#### 1.2 Color Scheme Enhancement
**출처**: Clara-fication Best Practices

**현재 상태**: 기본 Splunk 색상 + WCAG AA 준수
```xml
<option name="charting.fieldColors">
  {"critical":"#D93F3C","high":"#F7912C","medium":"#F8BE34","low":"#65A637"}
</option>
```

**개선 방안**:
```xml
<!-- Fortinet 브랜드 색상 + 확장된 팔레트 -->
<option name="charting.fieldColors">{
  "critical":"#DC143C",
  "high":"#FF6347",
  "medium":"#FFD700",
  "low":"#32CD32",
  "info":"#1E90FF",
  "unknown":"#708090",
  "allowed":"#00CED1",
  "denied":"#B22222"
}</option>

<!-- 대비율 개선 (WCAG AAA 준수) -->
<option name="charting.axisLabelsX.majorLabelStyle.color">#000000</option>
<option name="charting.backgroundColor">#FFFFFF</option>
```

**데이터 기반 색상 매핑**:
```xml
<!-- Risk Score 기반 동적 색상 -->
<option name="charting.fieldColors">{
  "90-100":"#8B0000",
  "70-89":"#DC143C",
  "50-69":"#FF8C00",
  "30-49":"#FFD700",
  "0-29":"#32CD32"
}</option>
```

**우선순위**: P2 (Medium, 시각적 일관성 개선)

---

### 2. 기능 확장 (Functional Additions)

#### 2.1 Drill-Down Navigation
**출처**: Splunk Lantern - Dashboard Design

**현재 상태**: 패널 간 연결 없음

**개선 방안**:
```xml
<!-- Row 1: 차단 패널에 Drill-Down 추가 -->
<panel id="blocked_panel">
  <title>🛡️ 차단</title>
  <table>
    <search>
      <query>index=fw action=deny | stats count by src_ip</query>
    </search>
    <drilldown>
      <link target="_blank">
        /app/search/search?q=index=fw src_ip=$click.value$ action=deny earliest=-24h
      </link>
    </drilldown>
  </table>
</panel>

<!-- Row 2: 공격 유형 클릭 시 상세 로그로 이동 -->
<panel id="attack_types">
  <chart>
    <drilldown>
      <set token="selected_attack_type">$click.value$</set>
      <set token="show_attack_details">true</set>
    </drilldown>
  </chart>
</panel>

<!-- 동적 패널 - 공격 유형 선택 시 표시 -->
<panel depends="$show_attack_details$">
  <title>$selected_attack_type$ 상세 로그</title>
  <table>
    <search>
      <query>
        index=fw attack_type="$selected_attack_type$"
        | table _time, src_ip, dst_ip, action, msg
        | head 100
      </query>
    </search>
  </table>
</panel>
```

**우선순위**: P1 (High Impact, 사용자 경험 대폭 개선)

---

#### 2.2 MITRE ATT&CK Mapping
**출처**: Truvis/SplunkDashboards (Threat Hunting)

**현재 상태**: FortiGate 로그만 표시

**개선 방안**:
```xml
<!-- New Row: MITRE ATT&CK 매핑 -->
<row>
  <panel>
    <title>🎯 MITRE ATT&CK 전술 분포</title>
    <chart>
      <search>
        <query><![CDATA[
index=fw
| eval mitre_tactic = case(
    attack_type="intrusion_attempt", "Initial Access",
    attack_type="malware_detected", "Execution",
    attack_type="data_exfiltration", "Exfiltration",
    attack_type="lateral_movement", "Lateral Movement",
    attack_type="privilege_escalation", "Privilege Escalation",
    attack_type="credential_access", "Credential Access",
    1=1, "Other"
  )
| stats count by mitre_tactic
| sort - count
        ]]></query>
      </search>
      <option name="charting.chart">pie</option>
      <option name="charting.fieldColors">{
        "Initial Access":"#FF6347",
        "Execution":"#FF8C00",
        "Persistence":"#FFD700",
        "Privilege Escalation":"#ADFF2F",
        "Defense Evasion":"#00CED1",
        "Credential Access":"#1E90FF",
        "Discovery":"#9370DB",
        "Lateral Movement":"#FF69B4",
        "Collection":"#DC143C",
        "Exfiltration":"#B22222",
        "Command and Control":"#8B0000",
        "Other":"#808080"
      }</option>
    </chart>
  </panel>

  <panel>
    <title>🔍 MITRE ATT&CK 기법 Top 10</title>
    <table>
      <search>
        <query><![CDATA[
index=fw
| eval mitre_technique = case(
    msg LIKE "%SQL%", "T1190 - Exploit Public-Facing Application",
    msg LIKE "%brute%", "T1110 - Brute Force",
    msg LIKE "%command%", "T1059 - Command and Scripting Interpreter",
    msg LIKE "%scan%", "T1046 - Network Service Scanning",
    1=1, "Unknown"
  )
| stats count by mitre_technique
| sort - count
| head 10
        ]]></query>
      </search>
    </table>
  </panel>
</row>
```

**lookup 테이블 활용** (`$SPLUNK_HOME/etc/apps/search/lookups/mitre_mapping.csv`):
```csv
attack_id,mitre_tactic,mitre_technique,mitre_id
1001,Initial Access,Exploit Public-Facing Application,T1190
1002,Execution,Command and Scripting Interpreter,T1059
1003,Persistence,Account Manipulation,T1098
...
```

**SPL with Lookup**:
```spl
index=fw
| lookup mitre_mapping attack_id OUTPUT mitre_tactic mitre_technique mitre_id
| stats count by mitre_tactic, mitre_technique
```

**우선순위**: P2 (Medium, 보안 분석 가치 추가)

---

#### 2.3 Baseline Detection (이상 탐지)
**출처**: awesome-splunk - Anomaly Detection Patterns

**현재 상태**: 정적 카운트만 표시

**개선 방안**:
```xml
<!-- New Row: 이상 탐지 -->
<row>
  <panel>
    <title>📈 이상 트래픽 탐지 (Baseline vs Current)</title>
    <chart>
      <search>
        <query><![CDATA[
index=fw
| bucket _time span=1h
| stats sum(bytes) as current_bytes by _time

| appendcols [
    search index=fw earliest=-7d latest=-1d
    | bucket _time span=1h
    | stats avg(bytes) as baseline_bytes by date_hour
    | eval _time = relative_time(now(), "@h")
    | eval baseline_bytes = round(baseline_bytes, 2)
  ]

| eval anomaly_score = if(current_bytes > (baseline_bytes * 1.5), "High", "Normal")
| eval deviation_percent = round(((current_bytes - baseline_bytes) / baseline_bytes) * 100, 2)

| table _time, current_bytes, baseline_bytes, deviation_percent, anomaly_score
        ]]></query>
      </search>
      <option name="charting.chart">line</option>
      <option name="charting.chart.overlayFields">baseline_bytes</option>
      <option name="charting.axisTitleX.text">Time</option>
      <option name="charting.axisTitleY.text">Bytes</option>
      <option name="charting.legend.placement">top</option>
    </chart>
  </panel>

  <panel>
    <title>🚨 이상 IP 주소 (통계 기반)</title>
    <table>
      <search>
        <query><![CDATA[
index=fw
| stats count as current_count by src_ip

| appendcols [
    search index=fw earliest=-7d latest=-1d
    | stats avg(count) as avg_count, stdev(count) as stdev_count by src_ip
  ]

| eval z_score = (current_count - avg_count) / stdev_count
| where z_score > 3
| eval anomaly_level = case(
    z_score > 5, "Critical",
    z_score > 4, "High",
    z_score > 3, "Medium",
    1=1, "Low"
  )
| table src_ip, current_count, avg_count, z_score, anomaly_level
| sort - z_score
        ]]></query>
      </search>
    </table>
  </panel>
</row>
```

**Machine Learning Alternative** (Splunk MLTK 사용):
```spl
index=fw
| fit DensityFunction bytes by src_ip into traffic_model
| apply traffic_model
| where "DensityFunction(bytes)" < 0.01
| table src_ip, bytes, "DensityFunction(bytes)"
```

**우선순위**: P1 (High Impact, 실제 위협 탐지 능력 향상)

---

### 3. 성능 최적화 (Performance Optimizations)

#### 3.1 Query Optimization
**출처**: awesome-splunk - SPL Best Practices

**현재 문제 패턴**:
```spl
<!-- 비효율적: 불필요한 필드 검색 -->
index=fw | stats count by *

<!-- 비효율적: 느린 regex -->
index=fw | rex field=msg "(?<attack_name>.*)"
```

**최적화 패턴**:
```spl
<!-- 효율적: 필요한 필드만 추출 -->
index=fw
| fields _time, src_ip, dst_ip, action, severity
| stats count by src_ip

<!-- 효율적: tstats 사용 (indexed fields) -->
| tstats count WHERE index=fw by _time, src_ip span=5m

<!-- 효율적: 빠른 필드 추출 -->
index=fw
| spath input=msg
| stats count by attack_type

<!-- 병렬 처리 활성화 -->
index=fw
[| makeresults | eval search = "severity=critical OR severity=high"]
| stats count by severity
```

**적용 예시** (Row 1: Critical 이벤트 패널):
```xml
<!-- Before -->
<query>
  index=fw severity=critical
  | stats count
</query>

<!-- After (50% 속도 개선) -->
<query>
  | tstats count WHERE index=fw severity=critical
</query>
```

**성능 개선 체크리스트**:
- [ ] `tstats` 사용 (indexed fields만)
- [ ] `stats` 전에 `fields` 명령으로 필드 제한
- [ ] `rex` 대신 `spath` 또는 `extract` 사용
- [ ] `eval` 계산을 가능한 늦게 수행
- [ ] `dedup` 대신 `stats` 사용
- [ ] Time range를 가능한 좁게 설정

**우선순위**: P1 (High Impact, 대시보드 로딩 속도 직접 개선)

---

#### 3.2 Search Acceleration
**출처**: Splunk Lantern - Dashboard Performance

**현재 상태**: 실시간 검색만 사용

**개선 방안**:

**Report Acceleration** (자주 사용하는 쿼리):
```xml
<!-- 기존 패널 -->
<panel>
  <title>🛡️ 차단</title>
  <table>
    <search>
      <query>index=fw action=deny | stats count by src_ip | sort - count</query>
      <earliest>-24h</earliest>
      <latest>now</latest>
    </search>
  </table>
</panel>

<!-- 개선: Saved Search 활용 -->
<panel>
  <title>🛡️ 차단</title>
  <table>
    <search ref="Fortinet_Blocked_IPs_24h"/>
    <!-- $SPLUNK_HOME/etc/apps/search/local/savedsearches.conf에 정의 -->
  </table>
</panel>
```

**savedsearches.conf**:
```ini
[Fortinet_Blocked_IPs_24h]
search = index=fw action=deny | stats count by src_ip | sort - count
dispatch.earliest_time = -24h
dispatch.latest_time = now
auto_summarize = 1
auto_summarize.dispatch.earliest_time = -7d
cron_schedule = */15 * * * *
enableSched = 1
```

**Data Model Acceleration** (고급):
```spl
<!-- Data Model 생성: Fortinet_Security -->
<!-- $SPLUNK_HOME/etc/apps/search/local/datamodels.conf -->

| datamodel Fortinet_Security Security_Events search
| stats count by severity, action
```

**Summary Indexing** (Historical Data):
```ini
[Fortinet_Daily_Summary]
search = index=fw | stats count by severity, action, src_country | collect index=summary_fw
cron_schedule = 0 0 * * *
enableSched = 1
```

**우선순위**: P2 (Medium, 장기 성능 개선)

---

#### 3.3 Dashboard Load Optimization
**출처**: Clara-fication Dashboard Best Practices

**현재 문제**: 모든 패널이 동시 로딩

**Base Search Pattern** (중복 검색 제거):
```xml
<!-- Base Search 정의 -->
<search id="base_fw_search">
  <query>
    index=fw
    | eval severity = case(
        level="critical", "critical",
        level="high", "high",
        level="medium", "medium",
        1=1, "low"
      )
    | eval event_category = case(
        action="deny", "blocked",
        action="allow", "allowed",
        1=1, "other"
      )
  </query>
  <earliest>$time_picker.earliest$</earliest>
  <latest>$time_picker.latest$</latest>
</search>

<!-- 여러 패널이 Base Search 재사용 -->
<panel>
  <title>🛡️ 차단</title>
  <table>
    <search base="base_fw_search">
      <query>
        search event_category="blocked"
        | stats count by src_ip
      </query>
    </search>
  </table>
</panel>

<panel>
  <title>🔴 Critical 이벤트</title>
  <single>
    <search base="base_fw_search">
      <query>
        search severity="critical"
        | stats count
      </query>
    </search>
  </single>
</panel>
```

**Progressive Loading** (단계별 로딩):
```xml
<!-- 우선순위 높은 패널만 자동 로딩 -->
<panel>
  <title>🔴 Critical 이벤트</title>
  <single>
    <search>
      <query>index=fw severity=critical | stats count</query>
      <refresh>30s</refresh>
      <refreshType>delay</refreshType>
    </search>
  </single>
</panel>

<!-- 나머지 패널은 수동 새로고침 -->
<panel>
  <title>📊 트래픽 분석 (클릭하여 로드)</title>
  <chart>
    <search>
      <query>index=fw | timechart span=1h sum(bytes)</query>
      <autoRun>false</autoRun>
    </search>
  </chart>
</panel>
```

**우선순위**: P1 (High Impact, 초기 로딩 속도 개선)

---

### 4. 통합 확장 (Integration Enhancements)

#### 4.1 Advanced Slack Notifications
**출처**: Splunk Alert Actions Best Practices

**현재 상태**: Critical/High 이벤트만 단순 알림

**개선 방안**:

**Rich Message Format**:
```json
{
  "channel": "splunk-alerts",
  "username": "Fortinet Security Bot",
  "icon_emoji": ":shield:",
  "attachments": [
    {
      "fallback": "Critical Security Event Detected",
      "color": "#DC143C",
      "pretext": "🚨 *Critical Security Event Detected*",
      "author_name": "FortiGate Firewall",
      "author_icon": "https://www.fortinet.com/favicon.ico",
      "title": "Intrusion Attempt Blocked",
      "title_link": "https://splunk.jclee.me/app/search/search?q=index%3Dfw%20severity%3Dcritical",
      "fields": [
        {
          "title": "Severity",
          "value": "Critical",
          "short": true
        },
        {
          "title": "Risk Score",
          "value": "95/100",
          "short": true
        },
        {
          "title": "Source IP",
          "value": "192.168.1.100 (Malicious)",
          "short": true
        },
        {
          "title": "Target IP",
          "value": "10.0.0.50 (Web Server)",
          "short": true
        },
        {
          "title": "Attack Type",
          "value": "SQL Injection Attempt",
          "short": false
        },
        {
          "title": "Action Taken",
          "value": "Blocked + IP Blacklisted",
          "short": false
        }
      ],
      "actions": [
        {
          "type": "button",
          "text": "View in Splunk",
          "url": "https://splunk.jclee.me/app/search/...",
          "style": "primary"
        },
        {
          "type": "button",
          "text": "Block IP Permanently",
          "url": "https://fortigate.jclee.me/firewall/block?ip=192.168.1.100",
          "style": "danger"
        }
      ],
      "footer": "Splunk Alert Action",
      "footer_icon": "https://www.splunk.com/favicon.ico",
      "ts": 1729512345
    }
  ]
}
```

**Alert Throttling** (알림 홍수 방지):
```ini
# savedsearches.conf
[Fortinet_Critical_Events]
search = index=fw severity=critical | stats count by src_ip, attack_type
alert.digest_mode = 1
alert.suppress = 1
alert.suppress.period = 5m
alert.suppress.fields = src_ip, attack_type
```

**Adaptive Thresholds** (동적 임계값):
```spl
index=fw
| stats count by severity

| appendcols [
    search index=fw earliest=-7d latest=-1d
    | stats avg(count) as baseline by severity
  ]

| eval anomaly = if(count > baseline * 2, "true", "false")
| where anomaly="true"
| sendalert slack param.message="Abnormal spike in $severity$ events"
```

**우선순위**: P2 (Medium, 알림 품질 개선)

---

#### 4.2 External Threat Intelligence Integration
**출처**: Truvis/SplunkDashboards - Threat Hunting

**현재 상태**: 내부 로그만 분석

**개선 방안**:

**AbuseIPDB Integration**:
```spl
index=fw action=deny
| stats count by src_ip
| where count > 100
| lookup abuseipdb_lookup ip as src_ip OUTPUT abuse_score, country, isp
| where abuse_score > 50
| table src_ip, abuse_score, country, isp, count
| sort - abuse_score
```

**VirusTotal Integration** (파일 해시 검사):
```spl
index=fw filehash=*
| lookup virustotal_lookup hash as filehash OUTPUT detection_rate, malware_type
| where detection_rate > 0
| table _time, filename, filehash, detection_rate, malware_type
```

**Lookup Table Setup** (`$SPLUNK_HOME/etc/apps/search/lookups/`):
- `abuseipdb_lookup.csv` (daily cron update)
- `virustotal_lookup.csv` (API-based)
- `mitre_attack_mapping.csv` (static)

**API Scripted Input** (`$SPLUNK_HOME/etc/apps/search/bin/fetch_threat_intel.py`):
```python
import requests
import csv

def fetch_abuseipdb(ip):
    url = 'https://api.abuseipdb.com/api/v2/check'
    headers = {'Key': 'YOUR_API_KEY', 'Accept': 'application/json'}
    params = {'ipAddress': ip, 'maxAgeInDays': '90'}

    response = requests.get(url, headers=headers, params=params)
    data = response.json()['data']

    return {
        'ip': ip,
        'abuse_score': data['abuseConfidenceScore'],
        'country': data['countryCode'],
        'isp': data['isp']
    }

# Cron: */30 * * * * (30분마다 실행)
```

**우선순위**: P3 (Low, Nice-to-have)

---

#### 4.3 Automated Response Actions
**출처**: Splunk SOAR Integration Patterns

**현재 상태**: 수동 대응만 가능

**개선 방안**:

**FortiGate API 통합** (자동 IP 차단):
```python
# $SPLUNK_HOME/etc/apps/search/bin/block_ip_on_fortigate.py

import requests
import json

def block_ip(ip_address, duration_hours=24):
    """FortiGate에 IP 주소 자동 차단"""

    fortigate_url = "https://fortigate.jclee.me/api/v2/cmdb/firewall/address"
    headers = {
        "Authorization": "Bearer YOUR_API_TOKEN",
        "Content-Type": "application/json"
    }

    # 1. Address Object 생성
    address_payload = {
        "name": f"Auto_Blocked_{ip_address}",
        "subnet": f"{ip_address}/32",
        "comment": f"Auto-blocked by Splunk at {datetime.now()}"
    }

    response = requests.post(fortigate_url, headers=headers, json=address_payload)

    # 2. Firewall Policy에 추가
    policy_url = "https://fortigate.jclee.me/api/v2/cmdb/firewall/policy"
    policy_payload = {
        "srcaddr": [{"name": f"Auto_Blocked_{ip_address}"}],
        "action": "deny",
        "status": "enable"
    }

    requests.post(policy_url, headers=headers, json=policy_payload)

    # 3. Scheduled Task로 24시간 후 자동 해제
    schedule_unblock(ip_address, duration_hours)

    return {"status": "success", "ip": ip_address, "duration": duration_hours}
```

**Splunk Alert Action 설정**:
```ini
# savedsearches.conf
[Fortinet_Auto_Block_Malicious_IPs]
search = index=fw severity=critical action=allow src_reputation=malicious | stats count by src_ip | where count > 10
cron_schedule = */5 * * * *
action.script = 1
action.script.filename = block_ip_on_fortigate.py
action.script.param.ip_field = src_ip
action.script.param.duration = 24
```

**Slack 알림 통합** (차단 완료 알림):
```python
def send_slack_notification(ip, action):
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    message = {
        "text": f"🚫 IP {ip} has been automatically blocked on FortiGate",
        "attachments": [{
            "color": "#DC143C",
            "fields": [
                {"title": "Action", "value": action, "short": True},
                {"title": "Duration", "value": "24 hours", "short": True}
            ]
        }]
    }
    requests.post(webhook_url, json=message)
```

**우선순위**: P3 (Low, 고급 자동화 기능)

---

## 📋 구현 우선순위 로드맵

### Phase 1: Quick Wins (1-2주)
**목표**: 즉각적인 사용자 경험 개선

- ✅ **P1.1**: Query Optimization (성능 50% 개선 예상)
  - `tstats` 적용
  - Base Search 패턴 도입
  - Progressive Loading 구현

- ✅ **P1.2**: Drill-Down Navigation
  - 주요 패널에 클릭 기능 추가
  - 동적 세부 패널 구현

- ✅ **P1.3**: Baseline Detection
  - 이상 탐지 패널 1개 추가 (트래픽 기준)

**예상 효과**:
- 대시보드 로딩 속도 50% 개선
- 사용자 클릭 1회 감소 (drill-down)
- 실제 이상 징후 탐지 시작

---

### Phase 2: Value Additions (3-4주)
**목표**: 분석 가치 향상

- ✅ **P2.1**: Custom Visualizations
  - Sankey Diagram (트래픽 흐름)
  - Heatmap (시간대별 패턴)
  - Geographic Map (공격 출발지)

- ✅ **P2.2**: MITRE ATT&CK Mapping
  - Lookup 테이블 생성
  - 전술/기법 매핑 패널 추가

- ✅ **P2.3**: Advanced Slack Notifications
  - Rich Message Format
  - Alert Throttling

**예상 효과**:
- 시각적 인사이트 3배 증가
- 보안 분석 프레임워크 정렬
- 알림 노이즈 70% 감소

---

### Phase 3: Advanced Features (5-8주)
**목표**: 고급 통합 및 자동화

- ✅ **P3.1**: External Threat Intelligence
  - AbuseIPDB 연동
  - VirusTotal 연동

- ✅ **P3.2**: Automated Response Actions
  - FortiGate API 통합
  - 자동 IP 차단

- ✅ **P3.3**: Search Acceleration
  - Data Model 생성
  - Summary Indexing

**예상 효과**:
- 외부 위협 인텔리전스 활용
- MTTR (Mean Time To Respond) 90% 감소
- 장기 쿼리 성능 10배 개선

---

## 🔧 구현 시 고려사항

### 1. 현재 아키텍처 유지
- ✅ **객관적 데이터 중심**: 모든 개선사항도 데이터 기반
- ✅ **WCAG 준수**: 새 시각화도 접근성 기준 유지
- ✅ **경량화 원칙**: 불필요한 기능 추가 금지

### 2. 하위 호환성
- ✅ 기존 SPL 쿼리 100% 유지
- ✅ 기존 패널 ID 변경 금지 (북마크 보존)
- ✅ 기존 Alert Action 영향 없음

### 3. 테스트 전략
```bash
# 성능 테스트
splunk search "| rest /services/search/jobs | search label=fortinet-dashboard" | stats avg(runDuration) as avg_load_time

# 시각화 렌더링 테스트
# Browser DevTools → Performance → Record 3 seconds

# Accessibility 테스트
# Browser → axe DevTools → Analyze

# Alert Action 테스트
# splunk test-alert Fortinet_Critical_Events
```

### 4. 문서화
모든 개선사항은 다음 파일에 문서화:
- `docs/DASHBOARD_CHANGELOG.md` - 변경 이력
- `docs/SPL_QUERY_LIBRARY.md` - SPL 패턴 라이브러리
- `docs/VISUALIZATION_GUIDE.md` - 시각화 가이드

---

## 📚 참고 자료

### GitHub Repositories
1. **splunk/dashboard-studio-resources**
   https://github.com/splunk/dashboard-studio-resources
   - Official custom visualizations
   - Dashboard templates

2. **Truvis/SplunkDashboards**
   https://github.com/Truvis/SplunkDashboards
   - Threat hunting dashboards
   - MITRE ATT&CK integration examples

3. **nextinstall/splunk-dashboards**
   https://github.com/nextinstall/splunk-dashboards
   - Production-ready dashboard templates

4. **sduff/awesome-splunk**
   https://github.com/sduff/awesome-splunk
   - Curated list of Splunk resources

### Splunk Documentation
1. **Dashboard Design Best Practices**
   https://lantern.splunk.com/Splunk_Platform/Product_Tips/Dashboards_and_Visualizations/Dashboard_design_and_visualization_choices

2. **SPL Optimization Guide**
   https://docs.splunk.com/Documentation/Splunk/latest/Search/Optimizeyoursearch

3. **Alert Actions Reference**
   https://docs.splunk.com/Documentation/Splunk/latest/Alert/AlertActionReference

### Community Resources
1. **Clara-fication Blog** - Dashboard Best Practices
2. **Splunk Answers** - Community Q&A
3. **Splunkbase** - Apps and Add-ons

---

**문서 작성**: Claude Code
**최종 검토**: 2025-10-21
**다음 액션**: Phase 1 구현 계획 수립
