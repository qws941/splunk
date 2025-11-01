# 📢 FortiGate Slack 알림 설정 가이드

> FortiGate 7.4.5 로그 기반 Slack 알림 자동화

---

## ✅ 사전 준비

### 1. Slack App 생성 및 Webhook URL 획득

1. https://api.slack.com/apps → **Create New App**
2. **From scratch** 선택
3. App Name: `FortiGate Alerts` (임의)
4. Workspace 선택
5. **Incoming Webhooks** 활성화
6. **Add New Webhook to Workspace**
7. Channel 선택 (예: `#fortigate-alerts`)
8. **Webhook URL 복사** (예: `https://hooks.slack.com/services/T...`)

### 2. Splunk에 Webhook URL 등록

**Settings** → **Alert actions** → **Slack**
- Webhook URL: (위에서 복사한 URL 붙여넣기)
- Save

---

## 📋 알림 생성 (4개)

### 방법 1: Web UI로 수동 생성 (권장)

**Settings** → **Searches, reports, and alerts** → **New Alert**

각 알림마다:
1. **Title**: 알림 이름 (예: `FortiGate_Config_Change_Alert`)
2. **Search**: 쿼리 복사/붙여넣기 (아래 참조)
3. **Schedule**: `*/5 * * * *` (5분마다)
4. **Trigger Condition**: Number of Results → greater than → 0
5. **Trigger Actions**: Add Actions → **Slack**
   - Channel: `#fortigate-alerts`
   - Message: `$result.alert_msg$`
6. **Throttle**:
   - Suppress for: 5m
   - Field values: (알림마다 다름)

---

### 알림 1: 설정 변경 알림 ⭐

**Title**: `FortiGate_Config_Change_Alert`

**Search**:
```spl
index=fortianalyzer earliest=-5m latest=now type=event subtype=system (logid=0100044546 OR logid=0100044547 OR cfgpath=*)
| eval 변경유형 = case(
    match(cfgpath, "firewall\.policy"), "🔥 정책",
    match(cfgpath, "firewall\.address"), "📍 주소객체",
    match(cfgpath, "firewall\.service"), "🔧 서비스객체",
    match(cfgpath, "system\."), "⚙️ 시스템설정",
    match(cfgpath, "log\."), "📋 로그설정",
    1=1, "📝 기타설정")
| eval 작업색 = case(
    action="Add", "🆕",
    action="Delete", "🗑️",
    action="Edit", "✏️",
    1=1, "🔄")
| eval 관리자 = coalesce(user, "system")
| eval 접속 = coalesce(ui, "N/A")
| eval 객체 = coalesce(cfgobj, "N/A")
| eval 변경내용 = if(isnotnull(cfgattr) AND len(cfgattr)<200, cfgattr, "상세 내용 생략")
| eval alert_msg = "*" + 변경유형 + " " + 작업색 + " " + action + "*\n"
    + "👤 관리자: `" + 관리자 + "`\n"
    + "🖥️ 장비: `" + devname + "`\n"
    + "🔌 접속: " + 접속 + "\n"
    + "📦 객체: `" + 객체 + "`\n"
    + "📝 경로: `" + cfgpath + "`\n"
    + "🔄 변경: " + 변경내용
| table alert_msg, devname, user, cfgpath
```

**Throttle Fields**: `user`, `cfgpath`

**Slack 메시지 예시**:
```
*🔥 정책 ✏️ Edit*
👤 관리자: `admin`
🖥️ 장비: `FGT-HQ-01`
🔌 접속: GUI(192.168.1.100)
📦 객체: `Policy-Web-Access`
📝 경로: `firewall.policy`
🔄 변경: srcaddr[any->Internal-Network]
```

---

### 알림 2: Critical 운영 이벤트

**Title**: `FortiGate_Critical_Event_Alert`

**Search**:
```spl
index=fortianalyzer earliest=-5m latest=now type=event subtype=system
    (level=critical OR level=error OR level=emergency OR level=alert)
    logid!=0100044546 logid!=0100044547
| eval 심각도색 = case(
    level="emergency", "🚨",
    level="alert", "🚨",
    level="critical", "🔴",
    level="error", "⚠️",
    1=1, "ℹ️")
| eval 이벤트유형 = case(
    match(logid, "^0103"), "HA",
    match(logid, "^0104"), "시스템",
    match(logid, "^0105"), "인터페이스",
    match(logid, "^0106"), "성능",
    1=1, "기타")
| eval 설명 = coalesce(logdesc, msg, "N/A")
| eval alert_msg = "*" + 심각도색 + " " + upper(level) + " - " + 이벤트유형 + " 이벤트*\n"
    + "🖥️ 장비: `" + devname + "`\n"
    + "🆔 LogID: `" + logid + "`\n"
    + "📝 설명: " + 설명
| table alert_msg, devname, level, logid
```

**Throttle Fields**: `devname`, `logid`

**Slack 메시지 예시**:
```
*🔴 CRITICAL - 시스템 이벤트*
🖥️ 장비: `FGT-HQ-01`
🆔 LogID: `0104032768`
📝 설명: System performance critical
```

---

### 알림 3: HA 이벤트

**Title**: `FortiGate_HA_Event_Alert`

**Search**:
```spl
index=fortianalyzer earliest=-5m latest=now type=event subtype=system logid=0103*
| eval 설명 = coalesce(logdesc, msg, "N/A")
| eval alert_msg = "*🔄 HA 이벤트 발생*\n"
    + "🖥️ 장비: `" + devname + "`\n"
    + "🆔 LogID: `" + logid + "`\n"
    + "⚠️ 심각도: " + level + "\n"
    + "📝 설명: " + 설명
| table alert_msg, devname, logid, level
```

**Throttle Fields**: `devname`, `logid`

---

### 알림 4: 정책 변경 (중요도 높음)

**Title**: `FortiGate_Policy_Change_Alert`

**Search**:
```spl
index=fortianalyzer earliest=-5m latest=now type=event subtype=system
    (match(cfgpath, "firewall\.policy") OR match(cfgpath, "firewall\.rule"))
| eval 작업색 = case(
    action="Add", "🆕 추가",
    action="Delete", "🗑️ 삭제",
    action="Edit", "✏️ 수정",
    1=1, "🔄 변경")
| eval 관리자 = coalesce(user, "system")
| eval 접속 = coalesce(ui, "N/A")
| eval 객체 = coalesce(cfgobj, "N/A")
| eval 변경내용 = if(isnotnull(cfgattr), cfgattr, "N/A")
| eval alert_msg = "*🔥 방화벽 정책 " + 작업색 + "*\n"
    + "👤 관리자: `" + 관리자 + "`\n"
    + "🖥️ 장비: `" + devname + "`\n"
    + "🔌 접속: " + 접속 + "\n"
    + "📦 정책: `" + 객체 + "`\n"
    + "🔄 변경: " + 변경내용
| table alert_msg, devname, user, action
```

**Throttle Fields**: `user`, `cfgobj`

**Channel**: `#fortigate-policy` (또는 별도 채널)

---

## 🎛️ 알림 ON/OFF 제어

### 방법 1: Splunk Web UI (권장)

**Settings** → **Searches, reports, and alerts**
1. 알림 이름 클릭 (예: `FortiGate_Config_Change_Alert`)
2. **Enable** 체크박스 → ON/OFF
3. **Save**

### 방법 2: REST API

```bash
# 알림 ON (활성화)
curl -k -u admin:password \
  -d 'disabled=0' \
  https://splunk.jclee.me:8089/servicesNS/nobody/search/saved/searches/FortiGate_Config_Change_Alert

# 알림 OFF (비활성화)
curl -k -u admin:password \
  -d 'disabled=1' \
  https://splunk.jclee.me:8089/servicesNS/nobody/search/saved/searches/FortiGate_Config_Change_Alert
```

### 방법 3: 대시보드에서 상태 확인

**Search에서 실행**:
```spl
| rest /services/saved/searches
| search title="FortiGate_*"
| eval status=if(disabled=0, "✅ Enabled", "🔴 Disabled")
| table title status cron_schedule next_scheduled_time
| rename title as "Alert Name", status as "Status", cron_schedule as "Schedule", next_scheduled_time as "Next Run"
```

---

## 📊 알림 테스트

### 1. 수동 실행으로 테스트

**Settings** → **Searches, reports, and alerts** → 알림 이름 클릭 → **Run**

**또는 Search**:
```spl
| savedsearch FortiGate_Config_Change_Alert
```

### 2. 로그 확인

```spl
index=_internal source=*scheduler.log savedsearch_name="FortiGate_Config_Change_Alert"
| table _time, savedsearch_name, status, result_count
```

### 3. Slack 채널 확인

`#fortigate-alerts` 채널에 메시지가 도착하는지 확인

---

## ⚙️ 커스터마이징

### 알림 주기 변경

**Schedule** 필드 수정:
- 5분마다: `*/5 * * * *`
- 10분마다: `*/10 * * * *`
- 15분마다: `*/15 * * * *`
- 1시간마다: `0 * * * *`

### 채널 변경

**Slack Action** → **Channel** 필드 수정:
- `#fortigate-alerts`
- `#fortigate-policy`
- `#security-operations`

### Throttle 기간 변경

**Suppress for** 필드 수정:
- 5분: `5m`
- 10분: `10m`
- 1시간: `1h`

### 메시지 포맷 변경

`alert_msg` eval 수식 수정:
- 이모지 추가/변경
- 필드 추가/제거
- 정렬 순서 변경

---

## 🚨 문제 해결

### 알림이 발송되지 않음

1. **Webhook URL 확인**:
   - Settings → Alert actions → Slack
   - Test webhook 클릭

2. **알림 활성화 확인**:
   - Settings → Searches, reports, and alerts
   - Enable 체크박스 확인

3. **Trigger 조건 확인**:
   - Search 결과가 0보다 큰지 확인
   - `| savedsearch Alert이름` 실행해서 결과 확인

4. **Slack Bot 권한 확인**:
   - Bot이 채널에 초대되어 있는지 확인
   - `/invite @봇이름`

### 중복 알림 발송

**Throttle 설정 확인**:
- Suppress for: `5m`
- Field values: 알림마다 다름 (user, devname, cfgpath 등)

### Slack 메시지 깨짐

**Markdown 문법 확인**:
- `*굵게*` - 별표로 감싸기
- `` `코드` `` - 백틱으로 감싸기
- `\n` - 줄바꿈

---

## 📁 파일 참조

**Slack 알림 설정 파일**:
- `configs/savedsearches-fortigate-alerts.conf` (4개 알림)

**테스트 쿼리**:
```bash
cat configs/savedsearches-fortigate-alerts.conf
```

---

**버전**: v1.0
**날짜**: 2025-10-28
**기반**: FortiGate 7.4.5 실제 로그 구조
**검증**: ✅ Slack Markdown 포맷 적용
