# 🚀 Quick Deploy: 123 Dashboard + Slack Alerts

## ⚡ 1-Minute Deployment

### What This Adds

기존 `123-fixed.xml` 대시보드 + **Slack 알림 제어 기능** 통합

**추가 기능**:
- ✅ 대시보드 상단에 Slack Alert Control Panel
- ✅ 9개 알림 규칙 (차단율, 설정 변경, 정책 변경 등)
- ✅ 버튼 클릭으로 ON/OFF 제어
- ✅ 테스트 알림 발송
- ✅ **📨 Slack 알림 전송 히스토리** (최근 24시간, 30초 자동 갱신)
- ✅ **📊 Slack 알림 통계 요약** (성공률, 발송률, 평균 실행시간)
- ✅ 기존 모든 패널 유지

---

## 🎯 Supported Alerts (9 Types)

| Icon | Alert Name | Trigger |
|------|------------|---------|
| 🔴 | High Block Rate | 차단율 > 30% |
| ⚙️ | Config Changes | 설정 변경 발생 |
| 📋 | Policy Changes | 방화벽 정책 변경 |
| 🔧 | Object Changes | Address/Service 객체 변경 |
| 🔀 | NAT Changes | NAT 정책 변경 |
| 🚪 | Port Forward Changes | 포트 포워딩 변경 |
| 📊 | High Traffic Source | 단일 출발지 > 1000 events/5min |
| 📊 | High Traffic Dest | 단일 목적지 > 1000 events/5min |
| ⚠️ | Unusual Ports | 비표준 포트 > 100 events/5min |

---

## 🚀 Deploy (Choose One)

### Option 1: Web UI (가장 쉬움)

```
1. https://YOUR_SPLUNK_HOST:8000 접속
2. Settings → User Interface → Views
3. New View → Upload XML
4. Select: /home/jclee/app/splunk/123-fixed-with-alerts.xml
5. Name: "123-fixed-with-alerts"
6. Save
```

### Option 2: REST API (가장 빠름)

```bash
export SPLUNK_PASSWORD="your-password"

curl -k -u admin:$SPLUNK_PASSWORD \
  -d "eai:data=$(cat /home/jclee/app/splunk/123-fixed-with-alerts.xml)" \
  https://YOUR_SPLUNK_HOST:8089/servicesNS/nobody/search/data/ui/views/123-fixed-with-alerts
```

### Option 3: Replace Existing 123.xml

```bash
export SPLUNK_PASSWORD="your-password"

# Backup first
curl -k -u admin:$SPLUNK_PASSWORD \
  https://YOUR_SPLUNK_HOST:8089/servicesNS/nobody/search/data/ui/views/123 \
  > 123.xml.backup.$(date +%Y%m%d)

# Replace
curl -k -u admin:$SPLUNK_PASSWORD \
  -d "eai:data=$(cat /home/jclee/app/splunk/123-fixed-with-alerts.xml)" \
  https://YOUR_SPLUNK_HOST:8089/servicesNS/nobody/search/data/ui/views/123
```

---

## ✅ After Deployment

### Step 1: Open Dashboard

```
https://YOUR_SPLUNK_HOST:8000/app/search/123-fixed-with-alerts
```

### Step 2: Create All Alerts (One-Click)

대시보드 상단의 Slack Alert Control Panel에서:

```
🚀 Create All Alerts 버튼 클릭
```

**대기 시간**: ~5초 (9개 알림 규칙 자동 생성)

### Step 3: Enable Alerts

```
✅ Enable All 버튼 클릭
```

**결과**: 모든 알림이 Slack으로 전송 시작

### Step 4: Test (Optional)

```
🧪 Test 버튼 클릭 (각 알림별로)
```

Slack 채널 `#splunk-alerts`에서 테스트 메시지 확인

---

## 🎨 Dashboard Preview

```
┌────────────────────────────────────────────────────────┐
│ 🔔 Slack Alert Management                              │
├────────────────────────────────────────────────────────┤
│ Status: 0 / 9 alerts enabled                           │
│                                                         │
│ [🚀 Create All] [✅ Enable All] [🔴 Disable All] [🔄]   │
│                                                         │
│ 🔴 High Block Rate (>30%)     [⚪ NOT FOUND] [➕][🧪][-] │
│ ⚙️ Config Changes              [⚪ NOT FOUND] [➕][🧪][-] │
│ 📋 Policy Changes              [⚪ NOT FOUND] [➕][🧪][-] │
│ ... (9 alerts total)                                    │
├────────────────────────────────────────────────────────┤
│ 📨 Slack Alert Transmission History (Last 24 Hours)    │
├────────────────────────────────────────────────────────┤
│ 전송시간          알림종류        상태    이벤트수        │
│ 2025-10-25 14:35 🔴 차단율 높음   ✅ 성공  12           │
│ 2025-10-25 14:30 ⚙️ 설정 변경    ✅ 성공   3           │
│ 2025-10-25 14:25 📋 정책 변경    ✅ 성공   1           │
│ ... (최근 20개 전송 기록, 30초 자동 갱신)               │
├────────────────────────────────────────────────────────┤
│ 📊 Slack Alert Statistics (Last 24 Hours)              │
├────────────────────────────────────────────────────────┤
│ 알림종류         총실행 성공 실패 발송 성공률 발송률    │
│ 🔴 차단율 높음    288   285   3   24   98.9%  8.3%    │
│ ⚙️ 설정 변경      288   288   0   15  100.0%  5.2%    │
│ 📋 정책 변경      288   287   1    8   99.6%  2.8%    │
│ ... (9개 알림 통계, 1분 자동 갱신)                      │
├────────────────────────────────────────────────────────┤
│                                                         │
│ [기존 123-fixed.xml의 모든 패널들...]                   │
│ • 전체 트래픽, 허용/차단 통계                            │
│ • 방화벽 정책 사용 현황                                  │
│ • 정책/객체 변경 이력                                    │
│ • 차단 트래픽 분석                                       │
│ • NAT/포트 포워딩 현황                                   │
│ • Top 10 통신 현황                                       │
│ • 실시간 이벤트 스트림                                   │
└────────────────────────────────────────────────────────┘
```

---

## 🔧 Quick Controls

### Enable All Alerts

```
대시보드에서 "✅ Enable All" 버튼 클릭
```

### Disable All Alerts

```
대시보드에서 "🔴 Disable All" 버튼 클릭
```

### Enable Single Alert

```
해당 알림 행의 "ON" 버튼 클릭
```

### Disable Single Alert

```
해당 알림 행의 "OFF" 버튼 클릭
```

### Test Single Alert

```
해당 알림 행의 "🧪" 버튼 클릭
→ Slack에서 테스트 메시지 확인
```

---

## 📊 Expected Slack Messages

### 차단율 높음 알림

```
🔴 *High Block Rate Alert*
차단율: 35%
총 이벤트: 10,000
차단: 3,500
```

### 설정 변경 알림

```
⚙️ *Config Change Alert*
시간: 2025-10-25 10:30:45
사용자: admin
액션: Edit
대상: firewall.address.VLAN10_Network
장비: FortiManager-01
```

### 정책 변경 알림

```
📋 *Policy Change Alert*
시간: 2025-10-25 10:32:12
정책ID: 42
사용자: admin
액션: Set
장비: FortiGate-HQ
```

---

## ⚠️ Prerequisites

### 1. Slack Plugin 설치 필수

```bash
ls /opt/splunk/etc/apps/ | grep slack

# 결과: slack_alerts 폴더가 있어야 함
# 없으면 설치:
cd /opt/splunk/etc/apps/
tar -xzf /path/to/slack-notification-alert_232.tgz
sudo /opt/splunk/bin/splunk restart
```

### 2. Slack Bot Token 설정 필수

```bash
cat /opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf

# 아래 내용 있어야 함:
[slack]
param.token = xoxb-YOUR-SLACK-BOT-TOKEN
param.channel = #splunk-alerts
```

없으면 생성:
```bash
sudo vi /opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf

# 위 내용 추가 후 저장
sudo /opt/splunk/bin/splunk restart
```

### 3. Slack 채널에 Bot 초대

```
Slack에서: /invite @your-bot-name
채널: #splunk-alerts
```

---

## 🐛 Troubleshooting

### Create All 버튼 클릭했는데 반응 없음

**원인**: JavaScript 오류 또는 권한 부족

**해결**:
```
1. 브라우저 콘솔 (F12) 열기
2. 오류 메시지 확인
3. Splunk 권한 확인: edit_search_schedule_priority 필요
```

### 알림 생성됐는데 Status가 "NOT FOUND"

**원인**: 새로고침 필요

**해결**:
```
"🔄 Refresh" 버튼 클릭
```

### 알림 생성됐는데 Slack 메시지 안 옴

**원인**: Slack Bot Token 미설정 또는 Bot이 채널에 초대 안됨

**해결**:
```bash
# Token 확인
cat /opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf

# Bot 초대 확인
# Slack에서: /invite @your-bot-name
```

### 알림이 너무 많이 옴

**해결 1**: 개별 알림 OFF
```
해당 알림 행의 "OFF" 버튼 클릭
```

**해결 2**: 임계값 조정
```
Settings → Searches, reports, and alerts
→ 해당 알림 클릭 → Edit → Search 탭
→ where block_rate > 30 → where block_rate > 50 변경
```

---

## 🔄 Rollback

### 원래 대시보드로 복구

```bash
# Backup에서 복구
curl -k -u admin:$SPLUNK_PASSWORD \
  -d "eai:data=$(cat 123.xml.backup.YYYYMMDD)" \
  https://YOUR_SPLUNK_HOST:8089/servicesNS/nobody/search/data/ui/views/123
```

### 알림 규칙만 삭제

```bash
# Settings → Searches, reports, and alerts
# Dashboard_* 로 시작하는 알림 선택
# Delete 버튼 클릭
```

---

## 📚 Complete Documentation

- **Full Guide**: `docs/123-SLACK-ALERTS-GUIDE.md`
- **Dashboard Fix**: `docs/DASHBOARD_FIX_123.md`
- **Comparison**: `docs/123-COMPARISON.md`
- **Slack Alert Setup**: `docs/WEBUI_SLACK_ALERT_GUIDE.md`

---

**File**: `123-fixed-with-alerts.xml`
**Panels**: 20 (19 기존 + 1 Alert Control)
**Alert Rules**: 9개
**Deployment Time**: ~1 minute
**Setup Time**: ~30 seconds (Create All + Enable All)
**Status**: ✅ Ready to deploy
