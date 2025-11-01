# 📢 FortiGate 7.4.5 Slack Real-time Alerts - Web UI Guide

> **대상**: Splunk Web UI 사용자 (conf 파일 수정 불필요)
> **소요 시간**: 알림 1개당 5분
> **환경**: Splunk 9 + FortiGate 7.4.5
> **⚠️ 주의**: Real-time 알림은 CPU/메모리 사용량이 높습니다 - 배포 후 반드시 모니터링

---

## ✅ 사전 준비 (1회만)

### 1. Slack Webhook URL 획득

1. https://api.slack.com/apps → **Create New App**
2. **From scratch** 선택
3. App Name: `FortiGate Alerts`
4. Workspace 선택 → **Create App**
5. 좌측 메뉴 **Incoming Webhooks** → **Activate Incoming Webhooks** (ON)
6. **Add New Webhook to Workspace**
7. Channel 선택: `#security-firewall-alert` → **Allow**
8. **Webhook URL 복사** (예: `https://hooks.slack.com/services/T.../B.../xyz`)

### 2. Splunk에 Webhook 등록

Splunk Web → **Settings** → **Alert actions** → **Slack**

| 필드 | 값 |
|------|-----|
| Webhook URL | 복사한 URL 붙여넣기 |
| Channel | `#security-firewall-alert` |

**Save** 클릭

---

## 🚀 Alert 1: 설정 변경 알림 (Real-time) ⭐

### Settings → Searches, reports, and alerts → New Alert

#### Step 1: Search

**Title**: `FortiGate_Config_Change_Alert`

**Search** 필드에 붙여넣기:

```spl
index=fw earliest=rt-30s latest=rt type=event subtype=system (logid=0100044546 OR logid=0100044547 OR cfgpath=*)
| dedup devname, user, cfgpath, action
| eval 변경유형 = case(
    match(cfgpath, "firewall\.policy"), "정책",
    match(cfgpath, "firewall\.address"), "주소객체",
    match(cfgpath, "firewall\.service"), "서비스객체",
    match(cfgpath, "system\."), "시스템설정",
    match(cfgpath, "log\."), "로그설정",
    1=1, "기타설정")
| eval 관리자 = coalesce(user, "system")
| eval 접속 = coalesce(ui, "N/A")
| eval 객체 = coalesce(cfgobj, "N/A")
| eval 변경내용 = if(isnotnull(cfgattr) AND len(cfgattr)<200, cfgattr, "상세 내용 생략")
| eval alert_msg = "*FortiGate " + 변경유형 + " 변경: " + action + "*" + " | " + "관리자: " + 관리자 + " | " + "장비: " + devname + " | " + "접속: " + 접속 + " | " + "객체: " + 객체 + " | " + "경로: " + cfgpath + " | " + "변경내용: " + 변경내용
| table alert_msg, devname, user, cfgpath
```

**⚠️ 중요**: Time range를 **반드시 rt-30s to rt**로 설정

#### Step 2: Schedule

| 필드 | 값 |
|------|-----|
| **Alert type** | Real-time |
| **Schedule Priority** | Highest |

**Next** 클릭

#### Step 3: Trigger Condition

| 필드 | 값 |
|------|-----|
| **Trigger alert when** | Number of Results |
| **is** | greater than |
| **Value** | `0` |

**Throttle** (중복 방지):
- ☑️ **Suppress triggering for**: `15s`
- **Suppress based on fields**: `user, cfgpath`

**Next** 클릭

#### Step 4: Trigger Actions

**Add Actions** → **Slack** 선택

| 필드 | 값 |
|------|-----|
| **Channel** | `#security-firewall-alert` |
| **Message** | `$result.alert_msg$` |

**Save** 클릭

---

## 🚨 Alert 2: Critical 이벤트 알림 (Real-time)

### 같은 방식으로 New Alert 생성

#### Search

**Title**: `FortiGate_Critical_Event_Alert`

```spl
index=fw earliest=rt-30s latest=rt type=event subtype=system (level=critical OR level=error OR level=emergency OR level=alert) logid!=0100044546 logid!=0100044547 NOT cfgpath=*
| dedup devname, logid, level
| eval 이벤트유형 = case(
    match(logid, "^0103"), "HA",
    match(logid, "^0104"), "시스템",
    match(logid, "^0105"), "인터페이스",
    match(logid, "^0106"), "성능",
    1=1, "기타")
| eval 설명 = coalesce(logdesc, msg, "N/A")
| eval alert_msg = "*FortiGate " + upper(level) + " - " + 이벤트유형 + "*" + " | " + "장비: " + devname + " | " + "LogID: " + logid + " | " + "설명: " + 설명
| table alert_msg, devname, level, logid
```

#### 나머지 설정

| 항목 | 값 |
|------|-----|
| **Alert type** | Real-time |
| **Schedule Priority** | Highest |
| **Trigger** | Number of Results > 0 |
| **Throttle** | 15s, fields: `devname, logid` |
| **Channel** | `#security-firewall-alert` |
| **Message** | `$result.alert_msg$` |

---

## 🔄 Alert 3: HA 이벤트 알림 (Real-time)

#### Search

**Title**: `FortiGate_HA_Event_Alert`

```spl
index=fw earliest=rt-30s latest=rt type=event subtype=system logid=0103* NOT cfgpath=*
| dedup devname, logid, level
| eval 설명 = coalesce(logdesc, msg, "N/A")
| eval alert_msg = "*FortiGate HA 이벤트*" + " | " + "장비: " + devname + " | " + "LogID: " + logid + " | " + "심각도: " + level + " | " + "설명: " + 설명
| table alert_msg, devname, logid, level
```

#### 설정

| 항목 | 값 |
|------|-----|
| **Alert type** | Real-time |
| **Schedule Priority** | Highest |
| **Throttle** | 15s, fields: `devname, logid` |
| **Channel** | `#security-firewall-alert` |
| **Message** | `$result.alert_msg$` |

---

## ⚙️ Alert ON/OFF

### Web UI

**Settings** → **Searches, reports, and alerts**

1. Alert 이름 클릭
2. **Enable** 체크박스 → ON/OFF
3. **Save**

### REST API

```bash
# ON
curl -k -u admin:password \
  -d 'disabled=0' \
  https://splunk.jclee.me:8089/servicesNS/nobody/search/saved/searches/FortiGate_Config_Change_Alert

# OFF
curl -k -u admin:password \
  -d 'disabled=1' \
  https://splunk.jclee.me:8089/servicesNS/nobody/search/saved/searches/FortiGate_Config_Change_Alert
```

---

## 🧪 테스트

### 1. 수동 실행

Alert 편집 화면 → **Run** 버튼 클릭

### 2. 실행 로그 확인

```spl
index=_internal source=*scheduler.log savedsearch_name="FortiGate_Config_Change_Alert"
| table _time, savedsearch_name, status, result_count
```

### 3. 상태 대시보드

```spl
| rest /services/saved/searches
| search title="FortiGate_*"
| eval 상태 = if(disabled=0, "✅", "🔴")
| table title, 상태, realtime_schedule
```

---

## ⚠️ 성능 모니터링 (필수!)

### CPU/메모리 사용률 체크

```spl
index=_internal source=*metrics.log group=search_concurrency
| stats avg(active_hist_searches) as avg_concurrent by host
| eval 상태 = case(
    avg_concurrent > 10, "🔴 위험",
    avg_concurrent > 5, "⚠️ 주의",
    1=1, "✅ 정상")
| table host, avg_concurrent, 상태
```

**기준**:
- ✅ 정상: avg_concurrent < 5
- ⚠️ 주의: 5-10 (모니터링 강화)
- 🔴 위험: > 10 (Real-time 비활성화 고려)

### Indexing 성능 확인

```spl
index=_internal source=*metrics.log group=queue name=indexqueue
| timechart avg(current_size_kb) as queue_size
```

**기준**:
- Real-time 알림 실행 후 queue_size가 급증하면 문제

---

## 🚨 문제 해결

### Webhook 테스트

Settings → Alert actions → Slack → **Test webhook**

### Bot 초대

Slack에서:
```
/invite @봇이름
```

### Real-time 검색이 실행 안 됨

1. **권한 확인**: `schedule_rtsearch` capability 필요
   ```bash
   | rest /services/authorization/roles
   | search title=your_role
   | table title, srchJobsQuota, rtSrchJobsQuota
   ```

2. **Real-time quota 확인**:
   ```spl
   | rest /services/search/jobs
   | search isRealTimeSearch=1
   | stats count
   ```

### 도배 문제 (중복 알림)

**원인**: Real-time 검색이 과거 이벤트를 반복 탐지

**해결**:
1. ✅ **이미 적용됨**: `dedup` 명령어로 중복 제거
2. ✅ **이미 적용됨**: `rt-30s` (짧은 윈도우)
3. ✅ **이미 적용됨**: 15초 suppress period

**추가 조치**:
```spl
# 과거 데이터 제외 (필요 시)
index=fw earliest=rt-30s latest=rt ...
| where _indextime > relative_time(now(), "-30s")
```

### CPU 사용률 급증

**즉시 조치**:
1. Real-time 알림 비활성화
2. 1분 cron으로 다시 변경 (참고: 기존 설정 백업)
3. Splunk 재시작 고려

---

## 📦 필수 플러그인

| 플러그인 | 버전 | 다운로드 |
|---------|------|----------|
| **Fortinet FortiGate Add-on for Splunk** | 1.6.9 | [Splunkbase](https://splunkbase.splunk.com/app/2846) |
| **Slack Notification Alert** | 2.3.2 | [Splunkbase](https://splunkbase.splunk.com/app/2878) |
| **Splunk Common Information Model (CIM)** | 6.2.0 | [Splunkbase](https://splunkbase.splunk.com/app/1621) |

### 설치 방법

1. Splunk Web → **Apps** → **Find More Apps**
2. "FortiGate Add-on" 검색 → **Install**
3. "Slack Notification Alert" 검색 → **Install**
4. Splunk 재시작

---

## 📝 요약

**3개 Real-time 알림 생성 완료**:

| 알림 | 채널 | 윈도우 | Dedup | Suppress |
|------|------|--------|-------|----------|
| Config Change | #security-firewall-alert | rt-30s | devname,user,cfgpath,action | 15초 (user, cfgpath) |
| Critical Event | #security-firewall-alert | rt-30s | devname,logid,level | 15초 (devname, logid) |
| HA Event | #security-firewall-alert | rt-30s | devname,logid,level | 15초 (devname, logid) |

**핵심 설정**:
- ✅ Real-time (earliest=rt-30s latest=rt)
- ✅ Dedup로 중복 제거 (도배 방지)
- ✅ 중복 알림 차단 (15초 suppress)
- ✅ 단일 채널 통합 (#security-firewall-alert)
- ⚠️ **성능 모니터링 필수**

**주의사항**:
- Real-time 알림은 Splunk 리소스 소모가 큽니다
- 배포 후 반드시 성능 모니터링 실시
- CPU 사용률이 급증하면 1분 cron으로 변경 고려
- `dedup` 명령어가 도배 문제를 해결합니다

**도배 방지 원리**:
1. `rt-30s` → 짧은 윈도우 (과거 이벤트 재탐지 최소화)
2. `dedup` → 같은 이벤트 한 번만 처리
3. `suppress 15s` → 15초간 동일 필드 조합 차단

**작성일**: 2025-10-28
**환경**: Splunk 9 + FortiGate 7.4.5
**버전**: Real-time v2.0 (Dedup Edition)
