# Fixes Applied (2025-11-04)

## 문제 요약

사용자 보고: "unable to find alert action script for action 'slack'"

## 근본 원인

**Splunk 공식 명명 규칙 미준수:**
- Splunk는 alert action `[slack]` 스탠자에 대해 자동으로 `bin/slack.py` 스크립트를 찾음
- 우리는 `slack_blockkit_alert.py`로 다른 이름 사용
- `command` 필드가 있어도 Splunk가 무시하거나 올바르게 해석하지 못함

## 적용된 수정

### 1. 스크립트 이름 변경 (Splunk 공식 형식)
```bash
security_alert/bin/slack_blockkit_alert.py → security_alert/bin/slack.py
```

**Why**: Splunk naming convention - `[slack]` stanza는 자동으로 `bin/slack.py` 매칭

### 2. alert_actions.conf에서 command 필드 제거
```ini
# Before:
[slack]
command = slack_blockkit_alert.py
is_custom = 1
...

# After:
[slack]
is_custom = 1
...
```

**Why**: Splunk 공식 플러그인은 command 필드 사용 안 함 (자동 매칭)

### 3. 기능 유지
✅ Block Kit formatting 유지
✅ 이중 인증 (Bot Token + Webhook) 유지
✅ 프록시 설정 유지
✅ 7개 파라미터 모두 유지

## 검증 결과

### ✅ 파일 구조
```
security_alert/
├── bin/
│   └── slack.py                        ✅ 이름 변경됨
├── default/
│   └── alert_actions.conf              ✅ command 필드 제거됨
└── README/
    └── alert_actions.conf.spec         ✅ 모든 파라미터 정의됨
```

### ✅ 파라미터 일치 확인
```bash
=== alert_actions.conf 파라미터 (7개) ===
param.slack_app_oauth_token =
param.webhook_url =
param.proxy_enabled = 0
param.proxy_url =
param.proxy_port =
param.proxy_username =
param.proxy_password =

=== spec 파일 파라미터 (7개) ===
param.slack_app_oauth_token = <string>
param.webhook_url = <string>
param.proxy_enabled = <boolean>
param.proxy_url = <string>
param.proxy_port = <string>
param.proxy_username = <string>
param.proxy_password = <string>

✅ 100% 일치
```

### ✅ Python 문법 검증
```bash
$ python3 -m py_compile security_alert/bin/*.py
✅ All files: Syntax OK
```

### ✅ 배포 패키지
```bash
$ ls -lh release/security_alert.tar.gz
-rw-r--r-- 1 jclee jclee 71K 11월 4 20:34 release/security_alert.tar.gz

$ tar -tzf release/security_alert.tar.gz | grep -E "slack|alert_actions"
security_alert/default/alert_actions.conf
security_alert/bin/slack.py
security_alert/README/alert_actions.conf.spec

✅ 모든 필수 파일 포함
```

## 배포 후 예상 동작

### Splunk가 자동으로:
1. `[slack]` 스탠자 발견
2. `bin/slack.py` 스크립트 찾기
3. `README/alert_actions.conf.spec`에서 파라미터 스키마 로드
4. Setup 페이지에 7개 필드 표시

### btool 예상 출력:
```bash
$ /opt/splunk/bin/splunk btool alert_actions list slack

[slack]
is_custom = 1
label = Send to Slack (Block Kit)
description = Send formatted alert to Slack using Block Kit
icon_path = appIcon.png
payload_format = json
python.version = python3
param.slack_app_oauth_token =
param.webhook_url =
param.proxy_enabled = 0
param.proxy_url =
param.proxy_port =
param.proxy_username =
param.proxy_password =
```

## Splunk 공식 플러그인과의 비교

### Splunk 공식 (github.com/splunk/slack-alerts):
```ini
[slack]
is_custom = 1
label = Slack
python.version = python3
payload_format = json
param.webhook_url =
param.from_user = Splunk
param.from_user_icon = https://...
param.attachment = none
```
- ❌ `command` 필드 없음
- ✅ Naming convention 사용: `bin/slack.py`
- ❌ Bot Token 미지원 (Webhook만)
- ❌ 프록시 미지원

### 우리 구현 (수정 후):
```ini
[slack]
is_custom = 1
label = Send to Slack (Block Kit)
python.version = python3
payload_format = json
param.slack_app_oauth_token =
param.webhook_url =
param.proxy_enabled = 0
param.proxy_url =
param.proxy_port =
param.proxy_username =
param.proxy_password =
```
- ❌ `command` 필드 없음 (공식과 동일)
- ✅ Naming convention 사용: `bin/slack.py` (공식과 동일)
- ✅ Bot Token + Webhook 이중 지원 (추가 기능)
- ✅ 프록시 지원 (추가 기능)
- ✅ Block Kit 포맷팅 (고급 메시지 형식)

## 이전 문제들 (모두 해결됨)

### ~~문제 1: command 필드 누락~~ (commit fb66e11)
- ✅ 수정: `command = slack_blockkit_alert.py` 추가
- ⚠️ 하지만 Splunk가 naming convention을 더 선호

### ~~문제 2: spec 파일 중복~~ (commit c66a13d)
- ✅ 수정: `default/alert_actions.conf.spec` 삭제
- ✅ 유지: `README/alert_actions.conf.spec` (올바른 위치)

### ~~문제 3: 스크립트 이름 불일치~~ (commit a6237e2 - 최신)
- ✅ 수정: `slack_blockkit_alert.py` → `slack.py`
- ✅ 수정: `command` 필드 제거

## 배포 후 테스트 절차

### 1. 파일 확인
```bash
ls -la /opt/splunk/etc/apps/security_alert/bin/slack.py
ls -la /opt/splunk/etc/apps/security_alert/README/alert_actions.conf.spec
ls -la /opt/splunk/etc/apps/security_alert/default/alert_actions.conf
```

### 2. btool 검증
```bash
/opt/splunk/bin/splunk btool alert_actions list slack
# Expected: [slack] 섹션, 7개 파라미터, command 필드 없음
```

### 3. Setup 페이지 접속
```
URL: https://your-splunk:8000/en-US/manager/security_alert/apps/local/security_alert/setup

Expected:
- Slack App OAuth Token (password)
- Slack Webhook URL (password)
- Enable Proxy (checkbox)
- Proxy Server (text)
- Proxy Port (text)
- Proxy Username (text)
- Proxy Password (password)
```

### 4. Alert Action 등록 확인
```bash
curl -k -u admin:password \
  "https://localhost:8089/services/admin/alert_actions?output_mode=json" \
  | jq '.entry[] | select(.name == "slack")'

# Expected: JSON object with slack action details
```

### 5. 로그 확인
```bash
tail -100 /opt/splunk/var/log/splunk/splunkd.log | grep -i "security_alert\|slack"
# Expected: No "unable to find script" errors
```

## 관련 문서

- Splunk 공식 Slack 플러그인: https://github.com/splunk/slack-alerts
- Custom Alert Actions: https://dev.splunk.com/enterprise/docs/devtools/customalertactions/
- alert_actions.conf spec: https://docs.splunk.com/Documentation/Splunk/latest/Admin/Alert_actionsconf

## Git 커밋 히스토리

```
a6237e2 (HEAD -> master) fix: Use Splunk official parameter names for Slack integration
c66a13d fix: Remove duplicate outdated alert_actions.conf.spec from default/
fb66e11 fix: Add command field to alert_actions.conf for Slack action
eb80dfb docs: Add comprehensive Slack custom action research document
```

---

**최종 상태**: ✅ 배포 준비 완료
**패키지 크기**: 71KB
**마지막 수정**: 2025-11-04 20:34 KST
**커밋**: a6237e2
