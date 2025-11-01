# Splunk Web UI - sendalert 방식 설정 가이드

## 🎯 목표
대시보드에서 버튼 클릭 → `| sendalert` 명령으로 Slack 테스트 알림 전송

---

## 📋 전체 프로세스 (Web UI 기준)

### Step 1: Slack Alert Action 설정 확인

#### 1-1. Settings → Alert actions 이동
```
Splunk Web UI (http://localhost:8000)
  ↓
Settings (상단 메뉴)
  ↓
Alert actions
```

#### 1-2. "Slack" 또는 "Send to Slack" 찾기
- **있는 경우**: 이미 Slack 플러그인 설치됨 ✅
- **없는 경우**: Splunk App 설치 필요 ⚠️

#### 1-3. Slack Alert Action 설정 클릭
```
Alert actions 페이지
  ↓
"Slack" 또는 "Send to Slack" 클릭
  ↓
우측 상단 "Setup" 또는 "Configure" 버튼 클릭
```

#### 1-4. 필수 정보 입력
| 필드 | 값 예시 | 설명 |
|------|---------|------|
| **Webhook URL** | `https://hooks.slack.com/services/T.../B.../xxx` | Slack Incoming Webhook URL |
| **Default Channel** | `#splunk` | 기본 채널 (# 포함) |
| **Bot Name** | `Splunk Alert` | 발신자 이름 |
| **Icon** | `:bell:` | 아이콘 이모지 |

**저장 버튼 클릭**

---

### Step 2: Saved Search (Alert) 생성

#### 2-1. Settings → Searches, reports, and alerts 이동
```
Settings (상단 메뉴)
  ↓
Searches, reports, and alerts
```

#### 2-2. 우측 상단 "New Alert" 클릭

#### 2-3. Search 정보 입력

**기본 정보:**
| 필드 | 값 |
|------|-----|
| **Title** | `Slack_Test_Alert` |
| **Description** | `Send test alert to Slack channel #splunk` |
| **App** | `Search & Reporting` |
| **Permissions** | `Shared in App` |

**Search 쿼리:**
```spl
| makeresults count=1
| eval test_time=strftime(now(), "%Y-%m-%d %H:%M:%S"),
       device="FortiGate-TEST",
       status="정상",
       message="🧪 *테스트 알림*\n시간: " + test_time + "\n장비: " + device + "\n상태: " + status + "\n\n✅ Slack 알림 정상 작동"
| table test_time, device, status, message
```

#### 2-4. Alert Type 설정

**Schedule 탭:**
| 옵션 | 값 |
|------|-----|
| **Schedule Type** | `Run on Cron Schedule` |
| **Cron Expression** | (비워둠 - 수동 실행만) |
| **Enable** | ☑️ **체크 해제** (자동 실행 안 함) |

**Time Range:**
| 옵션 | 값 |
|------|-----|
| **Earliest** | `-1m` |
| **Latest** | `now` |

#### 2-5. Alert Actions 설정

**Trigger Conditions 탭:**
| 옵션 | 값 |
|------|-----|
| **Trigger alert when** | `Number of Results` |
| **is greater than** | `0` |

**Trigger Actions 탭:**

1. **Add Actions → Slack** 클릭

2. Slack 설정:
   | 필드 | 값 |
   |------|-----|
   | **Channel** | `#splunk` |
   | **Message** | `$result.message$` |

3. **저장 (Save) 버튼** 클릭

---

### Step 3: 대시보드에서 sendalert 사용

#### 3-1. Dashboard 편집 모드

```
Dashboards 메뉴
  ↓
"SECURITY TEAM DASHBOARD" 선택
  ↓
우측 상단 "Edit" 버튼 클릭
```

#### 3-2. 새 패널 추가

**Edit 모드에서:**
1. **Add Panel** 클릭
2. **New** → **Single Value** 또는 **Table** 선택
3. 패널 제목 입력: `🧪 Slack 테스트 알림`

#### 3-3. Search 쿼리 입력

**Panel의 Search 영역에 입력:**
```spl
| makeresults count=1
| eval trigger_time=strftime(now(), "%Y-%m-%d %H:%M:%S"),
       status="대기 중...",
       instruction="아래 '검색' 버튼을 클릭하여 테스트 알림 전송"
| table trigger_time, status, instruction
| sendalert slack param.channel="#splunk" param.message="🧪 테스트 알림 - $(now())"
```

**중요:** `sendalert`는 **Alert 컨텍스트**에서만 작동하므로 일반 Search에서는 실행 안 됩니다.

#### 3-4. 대안: REST API 방식 (권장)

**Search 쿼리:**
```spl
| rest /servicesNS/nobody/search/saved/searches/Slack_Test_Alert/dispatch splunk_server=local
| eval trigger_time=strftime(now(), "%Y-%m-%d %H:%M:%S")
| eval status="✅ Slack 테스트 알림이 전송되었습니다!"
| eval channel="#splunk"
| table trigger_time, status, channel
```

**작동 원리:**
1. `| rest .../dispatch` → Saved Search "Slack_Test_Alert" 실행
2. Saved Search가 Slack Alert Action 트리거
3. Slack 메시지 전송

#### 3-5. 패널 저장

1. 패널 하단 **Apply** 버튼 클릭
2. Dashboard 상단 **Save** 버튼 클릭

---

### Step 4: 테스트 실행

#### 4-1. Dashboard에서 테스트

```
Dashboard 보기 모드
  ↓
"🧪 Slack 테스트 알림" 패널 찾기
  ↓
패널 우측 상단 "🔍 돋보기 아이콘" 클릭 (검색 실행)
  ↓
5초 대기
  ↓
Slack 채널 #splunk 확인
```

#### 4-2. Saved Search에서 직접 테스트

```
Settings → Searches, reports, and alerts
  ↓
"Slack_Test_Alert" 클릭
  ↓
우측 상단 "Run" 버튼 클릭
  ↓
"Open in Search" 클릭
  ↓
검색 완료 후 Slack 확인
```

---

## 🚨 중요한 제약사항

### sendalert 명령의 한계

❌ **일반 Dashboard Search에서 직접 실행 안 됨:**
```spl
# ❌ 작동 안 함 (Dashboard Search 패널)
| makeresults
| sendalert slack param.channel="#splunk"
```

이유: `sendalert`는 **Alert/Saved Search 컨텍스트**에서만 실행됩니다.

✅ **해결 방법 1: REST API로 Saved Search 트리거**
```spl
# ✅ 작동함 (Dashboard Search 패널)
| rest /servicesNS/nobody/search/saved/searches/Slack_Test_Alert/dispatch splunk_server=local
```

✅ **해결 방법 2: Custom Alert Action Script**
```spl
# ✅ 작동함 (Dashboard Search 패널)
| makeresults
| sendalert custom_slack_script
```

---

## 📊 Web UI 설정 체크리스트

### ☑️ Step 1: Slack 플러그인 설치 확인
- [ ] Settings → Alert actions → "Slack" 존재 확인
- [ ] Webhook URL 설정 완료
- [ ] Default Channel 설정 완료

### ☑️ Step 2: Saved Search 생성
- [ ] Settings → Searches, reports, and alerts → New Alert
- [ ] Title: `Slack_Test_Alert`
- [ ] Search 쿼리 입력
- [ ] Trigger Condition: `count > 0`
- [ ] Alert Action: **Slack** 추가
- [ ] Slack Channel: `#splunk`
- [ ] Slack Message: `$result.message$`
- [ ] **저장 완료**

### ☑️ Step 3: Dashboard 패널 추가
- [ ] Dashboard Edit 모드 진입
- [ ] 새 패널 추가
- [ ] REST API 방식 Search 쿼리 입력:
      ```
      | rest /servicesNS/.../Slack_Test_Alert/dispatch splunk_server=local
      ```
- [ ] 패널 저장, Dashboard 저장

### ☑️ Step 4: 테스트
- [ ] Dashboard에서 패널 검색 실행 (🔍 아이콘)
- [ ] Slack 채널 #splunk에서 메시지 확인
- [ ] 정상 작동 확인 ✅

---

## 🔧 트러블슈팅

### 문제 1: "Slack" Alert Action이 없음

**해결:**
```
Apps → Find More Apps
  ↓
검색: "Slack"
  ↓
"Slack Notification Alert" 설치
  ↓
Splunk 재시작
```

### 문제 2: Saved Search 실행되지만 Slack 메시지 안 옴

**확인 사항:**
1. Webhook URL 유효성
   ```bash
   curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
     -H 'Content-Type: application/json' \
     -d '{"text":"Test from curl"}'
   ```

2. Slack App이 채널에 초대되었는지 확인
   ```
   Slack 채널 #splunk
     ↓
   /invite @your-bot
   ```

3. Alert Action 로그 확인
   ```
   Settings → Monitoring Console
     ↓
   Alert Actions
     ↓
   최근 실행 로그 확인
   ```

### 문제 3: Dashboard에서 "| rest" 명령 오류

**오류 메시지:**
```
Error in 'rest' command: Access is denied
```

**해결:**
1. Saved Search의 Permissions 확인
   ```
   Saved Search → Edit → Permissions
     ↓
   "Shared in App" 선택
     ↓
   Everyone: Read 권한 부여
   ```

2. 현재 사용자 권한 확인
   ```
   Settings → Access controls → Roles
     ↓
   현재 role에 "edit_search_schedule_priority" 권한 있는지 확인
   ```

---

## 📸 Web UI 스크린샷 가이드

### 1. Alert Actions 설정 화면
```
[Settings] → [Alert actions] → [Slack] → [Setup]

┌─────────────────────────────────────────┐
│ Slack Configuration                     │
├─────────────────────────────────────────┤
│ Webhook URL: https://hooks.slack.com... │
│ Default Channel: #splunk                │
│ Bot Name: Splunk Alert                  │
│ Icon: :bell:                            │
│                                         │
│ [Cancel]              [Save]            │
└─────────────────────────────────────────┘
```

### 2. New Alert 생성 화면
```
[Settings] → [Searches, reports, and alerts] → [New Alert]

┌─────────────────────────────────────────┐
│ Save As Alert                           │
├─────────────────────────────────────────┤
│ Title: Slack_Test_Alert                 │
│ Description: Send test to #splunk       │
│                                         │
│ [Search]                    [Schedule]  │
│                                         │
│ | makeresults count=1                   │
│ | eval message="Test"                   │
│                                         │
│ [Trigger Conditions]  [Trigger Actions] │
│                                         │
│ Actions:                                │
│   ☑ Slack                               │
│     Channel: #splunk                    │
│     Message: $result.message$           │
│                                         │
│ [Cancel]              [Save]            │
└─────────────────────────────────────────┘
```

### 3. Dashboard Edit 화면
```
[SECURITY TEAM DASHBOARD] → [Edit]

┌─────────────────────────────────────────┐
│ 🧪 Slack 테스트 알림                      │
├─────────────────────────────────────────┤
│ Search:                                 │
│ | rest /servicesNS/nobody/search/...    │
│                                         │
│ Results:                                │
│ ┌──────────────────┬─────────────────┐ │
│ │ trigger_time     │ status          │ │
│ ├──────────────────┼─────────────────┤ │
│ │ 2025-01-23 14:30 │ ✅ 전송됨       │ │
│ └──────────────────┴─────────────────┘ │
│                                         │
│ [Apply]                                 │
└─────────────────────────────────────────┘
```

---

## 🎯 최종 권장 방식

### ✅ REST API 방식 (가장 안정적)

**Dashboard XML:**
```xml
<panel>
  <title>🧪 Slack 테스트 알림</title>
  <table>
    <search>
      <query>
| rest /servicesNS/nobody/search/saved/searches/Slack_Test_Alert/dispatch splunk_server=local
| eval trigger_time=strftime(now(), "%Y-%m-%d %H:%M:%S")
| eval status="✅ Slack 테스트 알림이 전송되었습니다!"
| table trigger_time, status
      </query>
      <earliest>-1m</earliest>
      <latest>now</latest>
    </search>
  </table>
</panel>
```

**장점:**
- ✅ Dashboard에서 직접 실행 가능
- ✅ 버튼 클릭만으로 Slack 전송
- ✅ JavaScript 불필요
- ✅ 외부 포트(8065) 접근 불필요 (서버 내부 통신)

---

## 📝 요약

| 방식 | Web UI 설정 | 난이도 | 안정성 |
|------|-------------|--------|--------|
| **sendalert 직접 호출** | Alert Action만 | ⭐ | ❌ (Dashboard에서 작동 안 함) |
| **REST API + Saved Search** | Alert Action + Saved Search | ⭐⭐ | ✅ 권장 |
| **Custom Script** | Alert Action + Python | ⭐⭐⭐ | ✅ 고급 |

**최종 권장:** REST API + Saved Search 방식
