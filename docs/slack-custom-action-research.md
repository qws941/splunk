# Splunk Custom Alert Action 연구 - Slack Integration

## 표준 Splunk Custom Alert Action 구조

### 1. alert_actions.conf (필수 필드)

**위치**: `default/alert_actions.conf`

**필수 구성**:
```ini
[action_name]
command = script_name.py           # ⭐ 필수 - 실행할 스크립트
is_custom = 1                       # Custom action 표시
label = Display Name                # UI에 표시될 이름
description = Description text      # 설명
icon_path = icon.png                # 아이콘 (선택)
payload_format = json               # 데이터 포맷 (json 또는 xml)
python.version = python3            # Python 버전

# Custom Parameters
param.parameter_name = default_value
```

**중요 사항**:
- `command` 필드가 없으면 Splunk가 스크립트를 실행하지 못함
- `param.*` 필드는 setup.xml과 매칭되어야 함
- `python.version = python3` 권장 (Splunk 8.0+)

### 2. alert_actions.conf.spec (파라미터 스키마)

**위치**: `README/alert_actions.conf.spec`

**역할**:
- Custom parameters 정의
- Splunk btool 검증용
- 파라미터 타입 및 설명 제공

**형식**:
```
[action_name]
param.parameter_name = <type>
* Parameter description
* Required/Optional
* Default: value
```

**없으면 발생하는 문제**:
```
Invalid key in stanza [action_name] in alert_actions.conf: param.xxx
```

### 3. setup.xml (Setup UI 구성)

**위치**: `default/setup.xml`

**기본 구조**:
```xml
<setup>
  <block title="Configuration Title"
         endpoint="admin/alert_actions"
         entity="action_name">

    <!-- 텍스트 입력 -->
    <input field="param.text_field">
      <label>Label Text</label>
      <type>text</type>
    </input>

    <!-- 패스워드 입력 -->
    <input field="param.password_field">
      <label>Password</label>
      <type>password</type>
    </input>

    <!-- 체크박스 -->
    <input field="param.checkbox_field">
      <label>Enable Feature</label>
      <type>checkbox</type>
    </input>

    <!-- 설명 텍스트 -->
    <text>
      <![CDATA[
      <p>HTML formatted instructions</p>
      ]]>
    </text>
  </block>
</setup>
```

**중요 속성**:
- `endpoint="admin/alert_actions"` - 설정을 저장할 REST 엔드포인트
- `entity="action_name"` - alert_actions.conf의 [stanza_name]과 동일
- `field="param.xxx"` - alert_actions.conf의 param.xxx와 동일

### 4. Python Script (Alert 실행 로직)

**위치**: `bin/script_name.py`

**표준 구조**:
```python
#!/usr/bin/env python3
import sys
import json
import gzip

def main():
    # 1. Splunk에서 전달받은 설정 읽기
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        # Payload는 stdin으로 gzip 압축되어 전달됨
        payload = json.loads(gzip.decompress(sys.stdin.buffer.read()))

        # 2. 설정 추출
        config = payload.get('configuration', {})
        bot_token = config.get('bot_token', '')
        webhook_url = config.get('webhook_url', '')

        # 3. Alert 결과 추출
        results = payload.get('result', {})

        # 4. 외부 서비스 호출 (Slack 등)
        # ...

        # 5. 성공/실패 반환
        sys.exit(0)  # 성공
        # sys.exit(1)  # 실패

if __name__ == "__main__":
    main()
```

**Payload 구조**:
```json
{
  "server_uri": "https://localhost:8089",
  "sid": "scheduler__admin__search__RMD...",
  "search_name": "Alert Name",
  "app": "app_name",
  "owner": "admin",
  "results_file": "/path/to/results.csv.gz",
  "configuration": {
    "bot_token": "xoxb-...",
    "webhook_url": "https://hooks.slack.com/...",
    "param_name": "value"
  },
  "result": {
    "_time": "2025-11-04T12:00:00",
    "field1": "value1",
    "field2": "value2"
  }
}
```

---

## Splunk 공식 Slack Addon 참조

### 공식 앱
- **Splunkbase**: https://splunkbase.splunk.com/app/2878
- **GitHub**: https://github.com/splunk/slack-alerts
- **License**: Apache 2.0

### 주요 특징
1. **Modular Alert Framework** (Splunk 6.3+)
2. **Bot Token OAuth 지원**
3. **Webhook URL 지원**
4. **Proxy 설정 지원**
5. **Message formatting** (text, markdown, attachments)

### 파라미터 예시
```ini
[slack]
command = slack.py
param.webhook_url =
param.from_user = Splunk
param.from_user_icon = https://...
param.channel = #general
param.message = Alert: $name$
```

---

## 우리 구현 vs. 표준 비교

### ✅ 준수 사항

1. **파일 구조**
   - ✅ alert_actions.conf에 `command` 필드 포함
   - ✅ alert_actions.conf.spec 파일 존재
   - ✅ setup.xml에 endpoint/entity 설정
   - ✅ Python3 스크립트 (slack_blockkit_alert.py)

2. **파라미터 정의**
   - ✅ 7개 custom parameters (2 인증 + 5 프록시)
   - ✅ 모든 param이 spec 파일에 정의됨
   - ✅ setup.xml과 alert_actions.conf 매칭

3. **인증 방식**
   - ✅ Bot Token OAuth (Method 1 - 권장)
   - ✅ Webhook URL (Method 2 - 대체)
   - ✅ Dual authentication 지원

4. **추가 기능**
   - ✅ HTTP/HTTPS Proxy 지원
   - ✅ Block Kit formatting (고급 메시지 포맷)
   - ✅ Gzip payload 처리
   - ✅ Error handling

### 📋 표준 형식 준수

#### alert_actions.conf
```ini
[slack]
command = slack_blockkit_alert.py      # ✅ 추가 완료
is_custom = 1                           # ✅
label = Send to Slack (Block Kit)       # ✅
description = ...                       # ✅
icon_path = appIcon.png                 # ✅
payload_format = json                   # ✅
python.version = python3                # ✅

param.slack_app_oauth_token =           # ✅
param.webhook_url =                     # ✅
param.proxy_enabled = 0                 # ✅
param.proxy_url =                       # ✅
param.proxy_port =                      # ✅
param.proxy_username =                  # ✅
param.proxy_password =                  # ✅
```

#### setup.xml
```xml
<setup>
  <block title="Slack Configuration"
         endpoint="admin/alert_actions"    # ✅
         entity="slack">                   # ✅
    <!-- 2 authentication fields -->      # ✅
    <!-- 5 proxy fields -->                # ✅
  </block>
  <block title="Setup Instructions">       # ✅
    <!-- HTML instructions -->             # ✅
  </block>
</setup>
```

#### Python Script
```python
# ✅ Gzip payload 처리
# ✅ Configuration 추출
# ✅ Bot Token OAuth 호출
# ✅ Webhook URL 호출
# ✅ Proxy 설정 적용
# ✅ Block Kit 포맷팅
# ✅ Error handling
```

---

## 발견된 문제와 수정

### 문제 1: command 필드 누락 (수정 완료)
**증상**: Action이 X 아이콘으로 표시됨

**원인**: alert_actions.conf에 `command` 필드 없음

**수정**:
```ini
[slack]
command = slack_blockkit_alert.py  # 추가
```

### 문제 2: spec 파일 누락 (수정 완료)
**증상**: btool validation 오류
```
Invalid key in stanza [slack]: param.slack_app_oauth_token
```

**원인**: alert_actions.conf.spec 파일 없음

**수정**: README/alert_actions.conf.spec 파일 생성

### 문제 3: setup.xml 구조 (수정 완료)
**증상**: Proxy 설정이 Setup 페이지에서 안 보임

**원인**: Proxy 설정이 별도 block으로 분리되어 endpoint/entity 속성 없음

**수정**: Proxy 설정을 main Slack block 안으로 병합

---

## 배포 검증 체크리스트

### 1. 파일 존재 확인
```bash
ls -la /opt/splunk/etc/apps/security_alert/default/alert_actions.conf
ls -la /opt/splunk/etc/apps/security_alert/README/alert_actions.conf.spec
ls -la /opt/splunk/etc/apps/security_alert/default/setup.xml
ls -la /opt/splunk/etc/apps/security_alert/bin/slack_blockkit_alert.py
```

### 2. btool 검증
```bash
/opt/splunk/bin/splunk btool alert_actions list slack
```

**Expected output**:
```
[slack]
command = slack_blockkit_alert.py
is_custom = 1
label = Send to Slack (Block Kit)
param.slack_app_oauth_token =
param.webhook_url =
param.proxy_enabled = 0
param.proxy_url =
param.proxy_port =
param.proxy_username =
param.proxy_password =
python.version = python3
```

### 3. Setup 페이지 접근
```
URL: https://your-splunk:8000/en-US/manager/security_alert/apps/local/security_alert/setup
```

**Expected**:
- Slack Configuration 섹션
  - Slack App OAuth Token (password field)
  - Slack Webhook URL (password field)
  - Enable Proxy (checkbox)
  - Proxy Server (text field)
  - Proxy Port (text field)
  - Proxy Username (text field)
  - Proxy Password (password field)
- Setup Instructions 섹션

### 4. Alert Action 등록 확인
```bash
# REST API로 확인
curl -k -u admin:password \
  "https://localhost:8089/services/admin/alert_actions?output_mode=json" \
  | jq '.entry[] | select(.name == "slack")'
```

### 5. Python 스크립트 권한
```bash
ls -la /opt/splunk/etc/apps/security_alert/bin/slack_blockkit_alert.py
# Expected: -rwxr-xr-x (755)
```

### 6. 로그 확인
```bash
# 배포 후 에러 확인
tail -100 /opt/splunk/var/log/splunk/splunkd.log | grep security_alert

# Alert 실행 로그
tail -100 /opt/splunk/var/log/splunk/alert_actions.log | grep slack
```

---

## 참고 자료

### Splunk 공식 문서
- Custom Alert Actions: https://dev.splunk.com/enterprise/docs/devtools/customalertactions/
- alert_actions.conf: https://docs.splunk.com/Documentation/Splunk/latest/Admin/Alert_actionsconf
- Modular Alerts Tutorial: https://www.splunk.com/en_us/blog/tips-and-tricks/how-to-create-a-modular-alert.html

### Slack API
- Bot Token OAuth: https://api.slack.com/authentication/oauth-v2
- Incoming Webhooks: https://api.slack.com/messaging/webhooks
- Block Kit: https://api.slack.com/block-kit

### 우리 구현
- GitHub: https://github.com/jclee-homelab/splunk.git
- Version: v2.0.4
- Last Updated: 2025-11-04

---

## 결론

현재 구현은 **Splunk 공식 Custom Alert Action 표준을 완전히 준수**합니다:

✅ 모든 필수 필드 포함 (command, is_custom, label, etc.)
✅ alert_actions.conf.spec 파일 존재
✅ setup.xml 구조 정확 (endpoint/entity 설정)
✅ Python3 스크립트 (Splunk 8.0+ 호환)
✅ Dual authentication (Bot Token + Webhook)
✅ Proxy 지원 (enterprise 환경)
✅ Block Kit formatting (고급 메시지)

**배포 준비 완료** - release/security_alert.tar.gz (71KB)
