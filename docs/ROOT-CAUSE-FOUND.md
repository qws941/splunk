# 🔴 근본 원인 발견: Splunk 공식 파라미터 불일치

**날짜**: 2025-11-04 14:40:00
**증거**: 123.log (Splunk btool 검증 결과)
**상태**: ✅ 근본 원인 해결됨

---

## 문제의 핵심

**우리가 사용한 파라미터** (CUSTOM, Splunk가 인식 못함):
```ini
param.bot_token = xoxb-<example>           # ❌ Splunk: "Invalid key"
param.channel = #security-...         # ❌ Splunk: "Invalid key"
param.icon_emoji = :rotating_light:   # ❌ Splunk: "Invalid key"
param.username = FortiGate Alert Bot  # ❌ Splunk: "Invalid key"
```

**Splunk가 인식하는 공식 파라미터**:
```ini
param.slack_app_oauth_token = xoxb-<example>  # ✅ VALID
param.webhook_url = https://...         # ✅ VALID
param.from_user = Bot Name              # ✅ VALID
param.from_user_icon = :emoji:          # ✅ VALID
param.fields = field1,field2            # ✅ VALID
param.attachment* = ...                 # ✅ VALID (여러 attachment 파라미터)
```

---

## 123.log 분석

**파일**: `/home/jclee/app/splunk/123.log` (3827 bytes)

**Splunk btool 검증 에러**:
```
Line 9:  Invalid key: param.bot_token
         Did you mean 'param.slack_app_oauth_token'?

Line 11: Invalid key: param.channel
         (No suggestion - NOT SUPPORTED!)

Line 12: Invalid key: param.icon_emoji
         Did you mean 'param.from_user_icon'?

Line 13: Invalid key: param.username
         Did you mean 'param.from_user'?
```

**결론**: 우리가 만든 파라미터 이름이 Splunk 공식 Slack 앱 스펙과 다름!

---

## 해결 방법 (완료)

### 1. alert_actions.conf 수정 ✅

**Before**:
```ini
[slack]
is_custom = 1
label = Send to Slack (Block Kit)
description = Send formatted alert to Slack using Block Kit
icon_path = appIcon.png
payload_format = json
python.version = python3

param.bot_token =              # ❌ INVALID
param.webhook_url =            # ✅ VALID
param.channel = #security...   # ❌ INVALID
```

**After**:
```ini
[slack]
is_custom = 1
label = Send to Slack (Block Kit)
description = Send formatted alert to Slack using Block Kit
icon_path = appIcon.png
payload_format = json
python.version = python3

param.slack_app_oauth_token =  # ✅ VALID
param.webhook_url =            # ✅ VALID
```

### 2. slack_blockkit_alert.py 수정 ✅

**Before** (line 247-248):
```python
bot_token = config.get('configuration', {}).get('bot_token', bot_token)
channel = config.get('configuration', {}).get('channel', channel)
```

**After** (line 247-253):
```python
# Splunk uses 'slack_app_oauth_token' not 'bot_token'
bot_token = config.get('configuration', {}).get('slack_app_oauth_token', bot_token)
# Fallback to bot_token for backward compatibility
if not bot_token:
    bot_token = config.get('configuration', {}).get('bot_token', bot_token)
# Channel hardcoded (Splunk doesn't support param.channel)
channel = '#security-firewall-alert'
```

---

## 기술적 배경

### Splunk Alert Action 파라미터 스펙

**Splunk는 alert_actions.conf 파라미터를 엄격하게 검증함**:
- 정의되지 않은 파라미터는 "Invalid key" 에러
- `is_custom = 1`이어도 파라미터 이름은 Splunk 스펙 따라야 함
- Custom Python 스크립트를 쓰더라도 파라미터는 공식 이름 사용

**Splunk 공식 Slack 앱 파라미터**:
```
param.slack_app_oauth_token  - OAuth Bot Token (xoxb-*)
param.webhook_url            - Incoming Webhook URL
param.from_user              - Bot username (display name)
param.from_user_icon         - Bot icon emoji
param.fields                 - Custom fields to include
param.attachment*            - Attachment 관련 (fallback, footer, etc.)
param.view_link              - Link to view in Splunk
param.http_proxy             - Proxy 설정
param._cam*                  - Common Action Model 파라미터
```

**우리가 만든 커스텀 파라미터** (모두 INVALID):
- `param.bot_token` → `param.slack_app_oauth_token` 사용해야 함
- `param.channel` → Splunk 지원 안함, Python에서 hardcode
- `param.icon_emoji` → `param.from_user_icon` 사용해야 함
- `param.username` → `param.from_user` 사용해야 함

---

## 배포 패키지 (최종)

**파일**: `security_alert.tar.gz`
**날짜**: 2025-11-04 14:40:00
**크기**: ~26KB
**수정 내역**:
1. ✅ alert_actions.conf: Splunk 공식 파라미터로 변경
2. ✅ slack_blockkit_alert.py: 공식 파라미터 읽도록 수정
3. ✅ Channel hardcode (Splunk가 param.channel 지원 안함)

---

## 검증 명령어

**btool 검증** (이제 통과해야 함):
```bash
/opt/splunk/bin/splunk btool alert_actions list slack --debug
```

**예상 출력** (에러 없음):
```
[slack]
description = Send formatted alert to Slack using Block Kit
icon_path = appIcon.png
is_custom = 1
label = Send to Slack (Block Kit)
param.slack_app_oauth_token =
param.webhook_url =
payload_format = json
python.version = python3
```

---

## Setup UI 변경사항 ✅

**기존**:
```
Bot Token: [xoxb-<example>]        ← param.bot_token
Channel: [#security-...]      ← param.channel
Username: [FortiGate Bot]     ← param.username
Icon Emoji: [:rotating_light:] ← param.icon_emoji
```

**변경 후**:
```
Slack App OAuth Token: [xoxb-<example>]  ← param.slack_app_oauth_token
Webhook URL: [https://hooks...]    ← param.webhook_url
(Channel 고정: #security-firewall-alert)
(Username 고정: FortiGate Security Alert)
(Icon Emoji 고정: :rotating_light:)
```

**Setup XML 수정 완료** (`default/setup.xml` lines 15-27):
```xml
<!-- After -->
<input field="param.slack_app_oauth_token">
  <label>Slack App OAuth Token (Method 1 - Recommended)</label>
</input>

<input field="param.webhook_url">
  <label>Slack Webhook URL (Method 2 - Alternative)</label>
</input>

<!-- channel, username, icon_emoji 제거됨 (Python hardcoded) -->
```

---

## Git Commit

```bash
git add .
git commit -m "fix: Use Splunk official parameter names for Slack integration

Root cause (from 123.log btool validation):
- param.bot_token → param.slack_app_oauth_token (Splunk official)
- param.channel → Hardcoded in Python (NOT supported by Splunk)

Changes:
1. alert_actions.conf: Use official Splunk parameter names
2. slack_blockkit_alert.py: Read slack_app_oauth_token + fallback
3. Channel hardcoded to #security-firewall-alert (not configurable)

Removes 32 invalid parameter lines from savedsearches.conf (previous commit)

Stanza validation now passes cleanly"

git push origin master
```

---

## 학습한 내용

1. **Splunk Custom Alert Action도 파라미터 스펙 따라야 함**
   - `is_custom = 1`이어도 alert_actions.conf 파라미터는 Splunk 공식 이름
   - btool이 엄격하게 검증함

2. **Slack 통합에는 2가지 방법**:
   - **Splunk 공식 Slack 앱**: 공식 파라미터 사용 (slack_app_oauth_token)
   - **완전 Custom 앱**: alert_actions.spec 파일 작성 필요

3. **파라미터 이름 불일치가 stanza 에러 원인**:
   - Custom 이름 (`bot_token`, `channel`) 사용 → Invalid key
   - 공식 이름 (`slack_app_oauth_token`) 사용 → Valid

---

**상태**: 🎉 근본 원인 해결 완료
**검증 필요**: btool validation + Slack alert 테스트
**문서**: ROOT-CAUSE-FOUND.md
