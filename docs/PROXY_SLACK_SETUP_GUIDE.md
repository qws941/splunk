# Fortinet Dashboard Slack Webhook (Proxy) 설정 가이드

## 🎯 개요

Splunk 대시보드 클릭 → **Proxy 서버** → Slack 알림 전송

### 핵심 특징
- ✅ **Splunk 재기동 불필요** - Web UI에서 alert_actions.conf 설정
- ✅ **index=fw 기반** - FAZ/FMG 로그 직접 활용
- ✅ **중복 제거** - dedup으로 깔끔한 데이터
- ✅ **Proxy 지원** - HTTP/HTTPS 프록시 서버 경유
- ✅ **Hidden Panel + sendalert** - 클릭 → 즉시 Slack 전송

---

## 🚀 배포 단계

### 1. Splunk Webhook Alert Action 설정

#### 1.1. Alert Actions 설정 파일 편집

**경로**: `$SPLUNK_HOME/etc/apps/search/local/alert_actions.conf`

```ini
[webhook]
# Webhook Alert Action 활성화
disabled = 0

# Proxy 서버 설정
http_proxy = http://your-proxy-server:3128
https_proxy = https://your-proxy-server:3128

# Proxy 인증 (필요 시)
# http_proxy = http://username:password@your-proxy-server:3128
# https_proxy = https://username:password@your-proxy-server:3128

# SSL 검증 (자체 서명 인증서 사용 시)
# ssl_verify = false
```

**또는** Web UI에서 설정:

1. **Settings** → **Alert actions**
2. **Webhook** 클릭
3. **Proxy Settings** 섹션:
   - HTTP Proxy: `http://your-proxy-server:3128`
   - HTTPS Proxy: `https://your-proxy-server:3128`
   - SSL Verification: Enable/Disable
4. **Save**

#### 1.2. Slack Webhook 생성

1. Slack 워크스페이스 → **Apps** → **Incoming Webhooks**
2. **Add to Slack** 클릭
3. 채널 선택 (예: `#splunk-alerts`)
4. Webhook URL 복사:
   ```
   https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
   ```

#### 1.3. Custom Alert Action 생성 (fortinet_slack)

**경로**: `$SPLUNK_HOME/etc/apps/search/local/alert_actions.conf`

```ini
[fortinet_slack]
disabled = 0
is_custom = 1
label = Fortinet Slack Alert
description = Send Fortinet events to Slack via Proxy
icon_path = alert_webhook.png

# Slack Webhook URL (환경 변수로 관리 권장)
param.webhook_url = https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Proxy 설정 (webhook action 설정 상속)
# http_proxy = http://your-proxy-server:3128
# https_proxy = https://your-proxy-server:3128

# Command
alert.execute.cmd = sendalert
alert.execute.cmd.arg.1 = fortinet_slack
```

**또는** Slack App을 통한 방법:

```ini
[fortinet_slack]
disabled = 0
is_custom = 1
label = Fortinet Slack Alert

# Slack App 사용
param.slack_token = xoxb-your-slack-bot-token
param.channel = #splunk-alerts

# Proxy 설정
http_proxy = http://your-proxy-server:3128
https_proxy = https://your-proxy-server:3128
```

---

### 2. Splunk Webhook Script 생성 (선택 사항)

더 정교한 메시지 포맷을 위해 Python 스크립트 사용:

**경로**: `$SPLUNK_HOME/etc/apps/search/bin/fortinet_slack.py`

```python
#!/usr/bin/env python3
import sys
import json
import os
import urllib.request
import urllib.error

def send_slack_alert(config):
    """
    Send alert to Slack via Proxy
    """
    # Proxy 설정
    proxy_support = urllib.request.ProxyHandler({
        'http': os.environ.get('http_proxy', config.get('http_proxy', '')),
        'https': os.environ.get('https_proxy', config.get('https_proxy', ''))
    })
    opener = urllib.request.build_opener(proxy_support)
    urllib.request.install_opener(opener)

    # Slack Webhook URL
    webhook_url = config.get('webhook_url', os.environ.get('SLACK_WEBHOOK_URL'))

    if not webhook_url:
        print("ERROR: No webhook URL configured", file=sys.stderr)
        sys.exit(1)

    # Slack 메시지 포맷
    severity = config.get('severity', 'medium')
    message = config.get('message', 'Fortinet Event Detected')

    # 색상 매핑
    color_map = {
        'critical': '#D93F3C',  # Red
        'high': '#F58F39',      # Orange
        'medium': '#F7BC38',    # Yellow
        'low': '#6DB7C6'        # Blue
    }

    # Attachment 구성
    attachment = {
        'fallback': message,
        'color': color_map.get(severity, '#6DB7C6'),
        'title': '🔔 Fortinet Dashboard Alert',
        'text': message,
        'fields': []
    }

    # 추가 필드
    for key, value in config.items():
        if key.startswith('param.') and key not in ['param.webhook_url', 'param.message', 'param.severity']:
            field_name = key.replace('param.', '').replace('_', ' ').title()
            attachment['fields'].append({
                'title': field_name,
                'value': value,
                'short': True
            })

    # Slack Payload
    payload = {
        'attachments': [attachment],
        'username': 'Fortinet Dashboard',
        'icon_emoji': ':shield:'
    }

    # HTTP POST
    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print("✅ Slack alert sent successfully")
                sys.exit(0)
            else:
                print(f"❌ Slack API returned status {response.status}", file=sys.stderr)
                sys.exit(1)

    except urllib.error.URLError as e:
        print(f"❌ Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    # Splunk passes alert configuration via STDIN
    config = {}

    # Read from environment or STDIN
    if len(sys.argv) > 1:
        # Arguments passed as command-line
        for i in range(1, len(sys.argv), 2):
            if i+1 < len(sys.argv):
                config[sys.argv[i]] = sys.argv[i+1]

    # Read from alert_actions.conf
    # (Splunk automatically passes configured params)

    send_slack_alert(config)
```

**실행 권한 부여**:
```bash
chmod +x $SPLUNK_HOME/etc/apps/search/bin/fortinet_slack.py
```

---

### 3. 환경 변수 설정 (선택 사항)

**방법 1**: Splunk 시작 스크립트에 추가

`$SPLUNK_HOME/etc/splunk-launch.conf`:
```bash
# Proxy 설정
http_proxy=http://your-proxy-server:3128
https_proxy=https://your-proxy-server:3128

# Slack Webhook URL (보안상 파일 권한 주의)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**방법 2**: 시스템 환경 변수

```bash
# /etc/environment 또는 ~/.bashrc
export http_proxy=http://your-proxy-server:3128
export https_proxy=https://your-proxy-server:3128
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

### 4. 대시보드 배포

```bash
# 환경 변수 설정
export SPLUNK_HOST=splunk.jclee.me
export SPLUNK_PORT=8089
export SPLUNK_USERNAME=admin
export SPLUNK_PASSWORD=your_password

# 대시보드 배포
node scripts/deploy-dashboards.js
```

**출력 예시:**
```
🚀 Deploying Splunk Dashboards via REST API...

📡 Target: https://splunk.jclee.me:8089
📦 App: search
👤 User: admin

📊 Deploying: Fortinet 설정 관리 (PRD - Proxy Slack 통합)...
✅ Dashboard deployed: Fortinet 설정 관리 (PRD - Proxy Slack 통합)

🌐 Access dashboards at:
   https://splunk.jclee.me/app/search/dashboards
```

---

## 📊 대시보드 사용법

### Slack 알림 테스트

1. Splunk 접속: `https://splunk.jclee.me`
2. **Dashboards** → **Fortinet 설정 관리 (PRD - Proxy Slack 통합)**
3. 알림 지원 패널 (📢 아이콘):
   - **📢 설정 변경 이력** (클릭 → Slack 알림)
   - **🛡️ 방화벽 정책 변경** (클릭 → Slack 알림)
   - **🚨 Critical 이벤트** (클릭 → Slack 알림)
4. 테이블 행 클릭
5. Slack 채널에서 알림 수신 확인 (#splunk-alerts)

### Slack 알림 예시

**1. 설정 변경 알림:**
```
*[설정변경]* 방화벽 정책
━━━━━━━━━
🖥️ 장비: `FW-01`
🔄 변경유형: *삭제*
📋 대상: `policy-001`
🔗 경로: `firewall.policy / policy-001 [srcaddr]`
👤 관리자: admin
🌐 접속IP: 203.0.113.50
🔌 접속방법: GUI
🕒 시간: 2025-10-15 14:30:22
⚠️ 심각도: *high*
```

**2. 방화벽 정책 변경 알림:**
```
*[방화벽정책변경]*
━━━━━━━━━
🖥️ 장비: `FW-01`
📋 정책명: `policy-001`
🔄 변경유형: *수정*
🔗 경로: `firewall.policy [action]`
👤 관리자: admin
🕒 시간: 2025-10-15 14:30:22
⚠️ 심각도: *high*
```

**3. Critical 이벤트 알림:**
```
🚨 *[CRITICAL 이벤트]*
━━━━━━━━━
🖥️ 장비: `FW-01`
🔴 레벨: *critical*
📋 카테고리: 하드웨어
🔔 이벤트타입: System Event
💬 메시지: ```Disk failure detected on /dev/sda1```
🕒 시간: 2025-10-15 14:35:10
⚠️ 심각도: *critical*
```

**Slack 포맷팅 설명:**
- `*text*`: **볼드** (헤더, 변경유형, 심각도 강조)
- `` `text` ``: `코드 스타일` (장비명, 대상, 경로)
- ` ```text``` `: 코드 블록 (긴 메시지)
- `━━━━━━━━━`: 구분선 (가독성 향상)

---

## 🔧 Troubleshooting

### Q1: Proxy 연결 실패

**A1: Proxy 서버 확인**
```bash
# Proxy 연결 테스트
curl -x http://your-proxy-server:3128 https://hooks.slack.com/services/TEST

# Splunk에서 환경 변수 확인
$SPLUNK_HOME/bin/splunk show config
```

### Q2: Slack 알림이 전송되지 않음

**A2-1: Splunk 로그 확인**
```bash
tail -f $SPLUNK_HOME/var/log/splunk/splunkd.log | grep -i webhook
```

**A2-2: Alert Action 상태 확인**
```bash
# Web UI
Settings → Alert actions → fortinet_slack → Enable
```

**A2-3: sendalert 수동 테스트**
```spl
| makeresults
| eval message="Test Alert"
| eval severity="medium"
| sendalert fortinet_slack param.message="$result.message$"
```

### Q3: Proxy 인증 실패

**A3: 인증 정보 포함**
```ini
# alert_actions.conf
[webhook]
http_proxy = http://username:password@your-proxy-server:3128
https_proxy = https://username:password@your-proxy-server:3128
```

**또는 환경 변수**:
```bash
export http_proxy=http://username:password@your-proxy-server:3128
```

### Q4: SSL 인증서 오류

**A4: SSL 검증 비활성화** (내부 프록시 사용 시)
```ini
# alert_actions.conf
[webhook]
ssl_verify = false
```

**Python 스크립트**:
```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

---

## 📈 Proxy 모니터링

### Proxy 로그 확인

대부분의 프록시 서버는 access log를 제공합니다:

**Squid Proxy**:
```bash
tail -f /var/log/squid/access.log | grep hooks.slack.com
```

**NGINX Proxy**:
```bash
tail -f /var/log/nginx/access.log | grep hooks.slack.com
```

### Splunk에서 Proxy 성공률 모니터링

```spl
index=_internal source=*splunkd.log* webhook
| rex field=_raw "status=(?<status>\d+)"
| stats count by status
| eval success_rate = round(count / sum(count) * 100, 2)
```

---

## 🛠️ 고급 설정

### 1. 여러 Slack 채널로 분기

```ini
# alert_actions.conf
[fortinet_slack_critical]
param.webhook_url = https://hooks.slack.com/services/CRITICAL/CHANNEL

[fortinet_slack_medium]
param.webhook_url = https://hooks.slack.com/services/MEDIUM/CHANNEL
```

대시보드에서:
```xml
| sendalert fortinet_slack_critical (for critical events)
| sendalert fortinet_slack_medium (for medium events)
```

### 2. 조건부 알림

```spl
| makeresults
| eval severity="high"
| eval device="FW-01"
| eval should_alert=if(severity="high" OR severity="critical", 1, 0)
| where should_alert=1
| sendalert fortinet_slack
```

### 3. Rate Limiting (알림 빈도 제한)

```spl
| makeresults
| eval _time=now()
| eval device="FW-01"
| lookup last_alert_time device OUTPUT last_time
| eval time_diff = _time - last_time
| where isnull(time_diff) OR time_diff > 300  # 5분 이상 경과
| outputlookup append=t last_alert_time
| sendalert fortinet_slack
```

---

## 📝 Summary

| 항목 | 상태 |
|------|------|
| Splunk 재기동 | ❌ 불필요 |
| Proxy 지원 | ✅ HTTP/HTTPS |
| index=fw 활용 | ✅ 완료 |
| 중복 제거 | ✅ dedup 적용 |
| Slack 알림 | ✅ 클릭 → Proxy → Slack |
| 설정 방법 | ✅ Web UI 또는 alert_actions.conf |
| PRD 배포 | ✅ 즉시 가능 |

---

**작성일**: 2025-10-15
**버전**: 1.0.0 (Proxy Support)
**작성자**: Claude Code
