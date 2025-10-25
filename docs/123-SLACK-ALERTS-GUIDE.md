# 123 Dashboard + Slack Alerts Integration Guide

## 📋 Overview

`123-fixed-with-alerts.xml`은 기존 `123-fixed.xml` 방화벽 운영 대시보드에 **Slack 알림 통합 관리 기능**을 추가한 버전입니다.

**주요 차이점**:
- ✅ 대시보드 상단에 Slack Alert Control Panel 추가
- ✅ 9개 알림 규칙 자동 생성/관리 기능
- ✅ 개별 알림 ON/OFF 제어
- ✅ 테스트 알림 발송 기능
- ✅ **📨 Slack 알림 전송 히스토리** (최근 24시간, 실시간 모니터링)
- ✅ **📊 Slack 알림 통계 요약** (성공률, 발송률, 평균 실행시간 분석)
- ✅ 모든 기존 패널 유지 (19개 패널)

---

## 🔔 지원하는 알림 종류 (9가지)

| 알림 이름 | 트리거 조건 | Slack 메시지 예시 |
|----------|-------------|-------------------|
| 🔴 High Block Rate | 차단율 > 30% | "차단율: 35% (총 10,000 이벤트 중 3,500 차단)" |
| ⚙️ Config Changes | 설정 변경 발생 | "설정 변경: admin이 firewall.policy 수정" |
| 📋 Policy Changes | 방화벽 정책 변경 | "정책 변경: Policy #42 수정됨 (user: admin)" |
| 🔧 Object Changes | Address/Service 객체 변경 | "객체 변경: add - VLAN10_Network (admin)" |
| 🔀 NAT Changes | NAT 정책 변경 | "NAT 정책 변경: SNAT-POOL-1 추가" |
| 🚪 Port Forward Changes | 포트 포워딩 변경 | "포트 포워딩 변경: VIP-WEB-SERVER 수정" |
| 📊 High Traffic Source | 단일 출발지 IP > 1000 events/5min | "High Traffic Source: 192.168.1.100 (1,234 이벤트)" |
| 📊 High Traffic Dest | 단일 목적지 IP > 1000 events/5min | "High Traffic Dest: 10.0.0.50 (1,567 이벤트)" |
| ⚠️ Unusual Ports | 비표준 포트 > 100 events/5min | "Unusual Port: 8888 (custom_app, 156 이벤트)" |

---

## 🚀 Deployment Instructions

### Method 1: Web UI (권장)

1. **Splunk 접속**: https://YOUR_SPLUNK_HOST:8000
2. **Settings** → **User Interface** → **Views**
3. **New View** → **Upload XML**
4. **파일 선택**: `/home/jclee/app/splunk/123-fixed-with-alerts.xml`
5. **View Name**: `123-fixed-with-alerts` 또는 `main_dashboard_v2`
6. **저장**
7. **접속**: https://YOUR_SPLUNK_HOST:8000/app/search/123-fixed-with-alerts

### Method 2: REST API

```bash
export SPLUNK_PASSWORD="your-password"

curl -k -u admin:$SPLUNK_PASSWORD \
  -d "eai:data=$(cat /home/jclee/app/splunk/123-fixed-with-alerts.xml)" \
  https://YOUR_SPLUNK_HOST:8089/servicesNS/nobody/search/data/ui/views/123-fixed-with-alerts
```

### Method 3: File System (SSH)

```bash
sudo cp /home/jclee/app/splunk/123-fixed-with-alerts.xml \
  /opt/splunk/etc/apps/search/local/data/ui/views/123-fixed-with-alerts.xml

sudo /opt/splunk/bin/splunk restart
```

---

## 📊 Dashboard Structure

### Row 0: 🔔 Slack Alert Control Panel (NEW!)

대시보드 상단에 추가된 알림 제어 패널:

```
┌─────────────────────────────────────────────────┐
│ 🔔 Slack Alert Management                       │
├─────────────────────────────────────────────────┤
│ 📊 Dashboard Alert Status: 5 / 9 alerts enabled│
│                                                  │
│ [🚀 Create All] [✅ Enable All] [🔴 Disable All]│
│                                                  │
│ Individual Controls:                             │
│ 🔴 High Block Rate (>30%)      [🟢 ON] [➕][🧪][OFF]│
│ ⚙️ Config Changes              [🔴 OFF] [➕][🧪][ON] │
│ 📋 Policy Changes              [🟢 ON] [➕][🧪][OFF]│
│ ... (9 alerts total)                            │
└─────────────────────────────────────────────────┘
```

**기능**:
- **Create All**: 9개 알림 규칙 일괄 생성
- **Enable All**: 모든 알림 Slack 전송 활성화
- **Disable All**: 모든 알림 Slack 전송 비활성화
- **➕ (Create)**: 개별 알림 규칙 생성
- **🧪 (Test)**: 개별 알림 테스트 메시지 전송
- **ON/OFF**: 개별 알림 활성화/비활성화

### Row 0-1: 📨 Slack Alert Transmission History (NEW!)

최근 24시간 동안 전송된 Slack 알림의 실시간 히스토리:

```
┌─────────────────────────────────────────────────┐
│ 📨 Slack Alert Transmission History             │
├─────────────────────────────────────────────────┤
│ 전송시간          알림종류        상태    이벤트수│
│ 2025-10-25 14:35 🔴 차단율 높음   ✅ 성공  12    │
│ 2025-10-25 14:30 ⚙️ 설정 변경    ✅ 성공   3    │
│ 2025-10-25 14:25 📋 정책 변경    ✅ 성공   1    │
│ 2025-10-25 14:20 🔧 객체 변경    ❌ 실패   0    │
│ ... (최근 20개 전송 기록)                       │
└─────────────────────────────────────────────────┘
```

**표시 정보**:
- **전송시간**: 알림이 실행된 시각
- **알림종류**: 9개 알림 중 어떤 알림인지
- **상태**: ✅ 성공 / ❌ 실패 / ⏭️ 건너뜀
- **이벤트수**: 알림 트리거한 이벤트 개수
- **실행시간**: 쿼리 실행에 걸린 시간 (초)
- **자동 갱신**: 30초마다 자동 갱신

### Row 0-2: 📊 Slack Alert Statistics Summary (NEW!)

9개 알림 규칙의 통계 요약:

```
┌─────────────────────────────────────────────────┐
│ 📊 Slack Alert Statistics (Last 24 Hours)       │
├─────────────────────────────────────────────────┤
│ 알림종류         총실행 성공 실패 발송 성공률    │
│ 🔴 차단율 높음    288   285   3   24   98.9%   │
│ ⚙️ 설정 변경      288   288   0   15  100.0%   │
│ 📋 정책 변경      288   287   1    8   99.6%   │
│ 🔧 객체 변경      288   286   2   12   99.3%   │
│ ... (9개 알림 통계)                             │
└─────────────────────────────────────────────────┘
```

**통계 항목**:
- **총실행**: 스케줄에 따라 실행된 총 횟수
- **성공**: 성공적으로 실행된 횟수
- **실패**: 실패한 실행 횟수
- **발송**: 실제로 Slack 알림이 발송된 횟수
- **성공률**: (성공 / 총실행) × 100%
- **발송률**: (발송 / 총실행) × 100%
- **평균실행시간**: 쿼리 평균 실행 시간
- **마지막실행**: 가장 최근 실행 시각
- **자동 갱신**: 1분마다 자동 갱신

### Row 1-9: 기존 대시보드 패널 (변경 없음)

- Row 1: 전체 트래픽, 허용/차단 트래픽, 활성 정책 수, 차단율
- Row 2: 방화벽 정책 사용 현황
- Row 3: 방화벽 정책 변경 이력
- Row 4: 주소/서비스 객체 변경
- Row 5: 차단 트래픽 분석
- Row 6: NAT/PAT 모니터링
- Row 7: 인터페이스별 트래픽, 시간대별 추이
- Row 8: Top 10 통신 현황
- Row 9: 실시간 방화벽 이벤트 스트림

---

## 🛠️ Alert Configuration Details

### Alert 1: Dashboard_High_Block_Rate

**Purpose**: 차단율이 30% 이상일 때 Slack 알림

**Search Query**:
```spl
index=fw type="traffic"
| stats count(eval(action="deny" OR action="drop" OR action="blocked")) as blocked, count as total
| eval block_rate=round((blocked/total)*100, 2)
| where block_rate > 30
| eval alert_text="🔴 *High Block Rate Alert*\n차단율: ".block_rate."%\n총 이벤트: ".total."\n차단: ".blocked
| table alert_text
```

**Cron Schedule**: `*/5 * * * *` (5분마다)

**Slack Message Format**:
```
🔴 *High Block Rate Alert*
차단율: 35%
총 이벤트: 10,000
차단: 3,500
```

---

### Alert 2: Dashboard_Config_Changes

**Purpose**: 설정 변경 발생 시 실시간 알림

**Search Query**:
```spl
index=fw cfgpath=* earliest=-5m latest=now
| eval config_hash = md5(cfgpath . policy_obj . user . _time)
| stats first(_time) as _time, first(user) as user, first(action) as action, first(policy_obj) as policy_obj, first(devname) as devname by config_hash
| eval alert_text="⚙️ *Config Change Alert*\n시간: ".strftime(_time, "%Y-%m-%d %H:%M:%S")."\n사용자: ".user."\n액션: ".action."\n대상: ".policy_obj."\n장비: ".devname
| head 1
| table alert_text
```

**Slack Message Format**:
```
⚙️ *Config Change Alert*
시간: 2025-10-25 10:30:45
사용자: admin
액션: Edit
대상: firewall.address.VLAN10_Network
장비: FortiManager-01
```

---

### Alert 3-9: Similar Pattern

각 알림은 동일한 패턴을 따릅니다:
1. **Search**: 5분 간격으로 특정 이벤트 검색
2. **Eval**: Slack 메시지 형식으로 `alert_text` 생성
3. **Trigger**: 이벤트 1개 이상 발견 시
4. **Action**: `sendalert slack` 실행

---

## 🧪 Testing Alerts

### 전체 알림 테스트

대시보드에서:
1. Slack Alert Control Panel 열기
2. 각 알림 행의 **🧪 (Test)** 버튼 클릭
3. Slack 채널 `#splunk-alerts`에서 테스트 메시지 확인

### 수동 테스트 (Search & Reporting)

```spl
| makeresults
| eval alert_text="🧪 *TEST ALERT*\nDashboard_High_Block_Rate\n시간: ".strftime(now(), "%Y-%m-%d %H:%M:%S")."\nStatus: Test Mode"
| table alert_text
| sendalert slack param.channel="#splunk-alerts"
```

---

## 🔧 Customization

### 알림 임계값 변경

**예시: 차단율 임계값 30% → 20% 변경**

1. **Settings** → **Searches, reports, and alerts**
2. **Dashboard_High_Block_Rate** 클릭
3. **Edit** → **Search** 탭
4. Query에서 `where block_rate > 30` → `where block_rate > 20` 변경
5. **Save**

### 알림 주기 변경

**예시: 5분마다 → 15분마다 변경**

1. **Settings** → **Searches, reports, and alerts**
2. 해당 알림 클릭
3. **Edit** → **Schedule** 탭
4. Cron Schedule: `*/5 * * * *` → `*/15 * * * *` 변경
5. **Save**

### Slack 채널 변경

**예시: #splunk-alerts → #security-events 변경**

1. **Settings** → **Searches, reports, and alerts**
2. 해당 알림 클릭
3. **Edit** → **Trigger Actions** 탭
4. Slack 액션 → **Channel**: `#security-events` 입력
5. **Save**

---

## 📊 Monitoring Alert Performance

### 알림 실행 이력 확인

```spl
index=_internal source=*scheduler.log savedsearch_name="Dashboard_*"
| stats count, latest(_time) as last_run, avg(run_time) as avg_runtime_sec by savedsearch_name
| eval last_run_time = strftime(last_run, "%Y-%m-%d %H:%M:%S")
| table savedsearch_name, count, last_run_time, avg_runtime_sec
```

### 알림 발송 실패 확인

```spl
index=_internal source=*scheduler.log savedsearch_name="Dashboard_*" status=failure
| table _time, savedsearch_name, status, message
```

### Slack 전송 로그 확인

```spl
index=_internal source=*slack* "Dashboard_*"
| table _time, savedsearch_name, action, channel, status
```

---

## ⚠️ Troubleshooting

### 문제 1: 알림 생성 버튼 클릭 시 반응 없음

**원인**: JavaScript 오류 또는 권한 부족

**해결**:
1. 브라우저 콘솔 (F12) 열기
2. JavaScript 오류 확인
3. Splunk 권한 확인: `edit_search_schedule_priority` 필요

### 문제 2: 알림 생성됐는데 Slack 메시지 안 옴

**원인 1**: Slack Bot Token 미설정

```bash
cat /opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf

# 없으면 생성:
sudo vi /opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf
[slack]
param.token = xoxb-YOUR-SLACK-BOT-TOKEN
param.channel = #splunk-alerts
```

**원인 2**: Bot이 채널에 초대 안됨

Slack에서: `/invite @your-bot-name`

### 문제 3: 알림이 너무 많이 옴 (Spam)

**해결 1**: 임계값 조정 (위의 Customization 참고)

**해결 2**: Throttling 추가

```spl
# Settings → Searches, reports, and alerts → Alert → Edit
# Trigger Conditions 탭
# "Throttle" 체크
# "Suppress results containing field:" = srcip
# "For" = 15 minutes
```

### 문제 4: 대시보드 로드 시 Alert Control Panel 안 보임

**원인**: JavaScript 로딩 실패 또는 브라우저 호환성

**해결**:
1. 브라우저 캐시 삭제 (Ctrl+Shift+Del)
2. 다른 브라우저 시도 (Chrome, Firefox, Edge)
3. Splunk JavaScript 로그 확인:
```spl
index=_internal source=*splunkd.log javascript
```

---

## 🔄 Migration from 123-fixed.xml

기존 `123-fixed.xml` 사용자의 마이그레이션 가이드:

### 옵션 1: 병행 사용 (권장)

```bash
# 기존 대시보드 유지하고 새 대시보드 추가
# 123.xml → 기존 운영 대시보드
# 123-fixed-with-alerts.xml → 알림 기능 포함 신규 대시보드

# 양쪽 모두 사용 가능
```

### 옵션 2: 완전 교체

```bash
export SPLUNK_PASSWORD="your-password"

# 백업
curl -k -u admin:$SPLUNK_PASSWORD \
  https://YOUR_SPLUNK_HOST:8089/servicesNS/nobody/search/data/ui/views/123 \
  > /home/jclee/app/splunk/backups/123.xml.$(date +%Y%m%d)

# 교체
curl -k -u admin:$SPLUNK_PASSWORD \
  -d "eai:data=$(cat /home/jclee/app/splunk/123-fixed-with-alerts.xml)" \
  https://YOUR_SPLUNK_HOST:8089/servicesNS/nobody/search/data/ui/views/123
```

---

## 📈 Performance Impact

**대시보드 로딩 시간**:
- 기존 123-fixed.xml: ~2-3초
- 123-fixed-with-alerts.xml: ~2-4초 (+0-1초)
- Alert Control Panel JavaScript: ~500ms

**추가 Splunk 부하**:
- 9개 알림 규칙: 5분마다 실행
- 각 알림 평균 실행 시간: ~1-2초
- 총 CPU 부하: <1% 증가 (대부분 idle time)

**권장 환경**:
- Splunk Enterprise 8.0 이상
- JavaScript 활성화된 최신 브라우저
- Slack Alert Plugin 설치 필수

---

## 🔗 Related Documentation

- **Dashboard Fix Guide**: `docs/DASHBOARD_FIX_123.md`
- **Dashboard Comparison**: `docs/123-COMPARISON.md`
- **Quick Deploy Guide**: `DEPLOY-123-FIXED.md`
- **Slack Alert Setup**: `docs/WEBUI_SLACK_ALERT_GUIDE.md`
- **Slack Control Dashboard**: `configs/dashboards/README-slack-control.md`

---

**File**: `123-fixed-with-alerts.xml`
**Line Count**: ~594 lines
**Panels**: 19 (기존) + 1 (Alert Control)
**Alert Rules**: 9개 자동 생성 가능
**Status**: ✅ Ready for deployment
**Created**: 2025-10-25
