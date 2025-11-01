# Splunk Web UI 기준 Slack Alert 생성 가이드

## 📋 목차
1. [사전 준비](#사전-준비)
2. [Alert 생성 상세 과정](#alert-생성-상세-과정)
3. [Alert 관리 (ON/OFF/테스트)](#alert-관리)
4. [트러블슈팅](#트러블슈팅)

---

## 사전 준비

### 1. Slack Alert Plugin 설치 확인
```bash
# SSH로 Splunk 서버 접속 후
ls /opt/splunk/etc/apps/ | grep slack

# 결과: slack_alerts 폴더가 보여야 함
```

없으면 설치:
```bash
cd /opt/splunk/etc/apps/
tar -xzf /path/to/slack-notification-alert_232.tgz
sudo /opt/splunk/bin/splunk restart
```

### 2. Slack 설정 확인
```bash
# Alert Actions 설정 파일 확인
cat /opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf

# 아래 내용이 있어야 함:
[slack]
param.token = xoxb-YOUR-SLACK-BOT-TOKEN
param.channel = #splunk-alerts
```

설정 안되어 있으면:
```bash
sudo vi /opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf

# 위 내용 추가 후 저장
sudo /opt/splunk/bin/splunk restart
```

### 3. Splunk Web UI 접속
- URL: `https://splunk.jclee.me:8000`
- Username: `admin`
- Password: `[your-password]`

---

## Alert 생성 상세 과정

### 🔴 Alert 1: FAZ_Critical_Alerts

#### Step 1: New Alert 화면 열기
1. 상단 메뉴 **"Settings"** 클릭
2. **"Searches, reports, and alerts"** 클릭
3. 우측 상단 **"New Alert"** 버튼 클릭

#### Step 2: 기본 정보 입력 (Search 탭)
**필드 위치:** 화면 상단부터 순서대로

1. **Title** (필수):
   ```
   FAZ_Critical_Alerts
   ```

2. **Description** (선택):
   ```
   FortiAnalyzer 크리티컬 이벤트 (Update Fail, Login Fail 제외)
   ```

3. **Permissions** 라디오 버튼:
   - **"Shared in App"** 선택 (기본값)

4. **Search** (큰 텍스트박스):
   ```
   index=fortianalyzer sourcetype=fw_log earliest=-5m latest=now | search (severity=critical OR level=critical) | search NOT msg="*Update Fail*" | search NOT msg="*login*fail*" | search NOT msg="*authentication*fail*" | eval src_ip=coalesce(srcip, src, "N/A") | eval dst_ip=coalesce(dstip, dst, "N/A") | eval severity_level=coalesce(severity, level, "N/A") | eval message=coalesce(msg, "N/A") | eval alert_text="🔴 *FAZ Critical Alert*\n출발지: ".src_ip."\n목적지: ".dst_ip."\n심각도: ".severity_level."\n메시지: ".message | head 1 | table alert_text
   ```

   **주의:** 전체 한 줄로 복사 (줄바꿈 없이)

#### Step 3: 스케줄 설정
**필드 위치:** Search 입력란 아래

1. **"Alert type"** 라디오 버튼:
   - **"Scheduled"** 선택

2. **"Cron Schedule"** 입력란:
   ```
   */5 * * * *
   ```
   (5분마다 실행)

3. **"Time Range"** 드롭다운:
   - **"Run on Cron Schedule"** 선택

4. 하단 **"Next"** 버튼 클릭

#### Step 4: Trigger Condition 설정
**화면:** Trigger Conditions 탭

1. **"Trigger alert when"** 섹션:
   - 첫 번째 드롭다운: **"Number of Results"** 선택
   - 두 번째 드롭다운: **"is greater than"** 선택
   - 숫자 입력란: `0` 입력

2. **"Throttle"** 섹션 (선택사항):
   - 체크박스 **체크 안 함** (모든 이벤트 알림받으려면)

3. 하단 **"Next"** 버튼 클릭

#### Step 5: Trigger Actions 설정
**화면:** Trigger Actions 탭

1. **"Add Actions"** 드롭다운 클릭

2. 목록에서 **"Slack"** 찾아서 클릭 (체크 표시됨)

3. Slack 설정 섹션이 펼쳐짐:

   **"Webhook URL"** 입력란:
   - 비워둠 (alert_actions.conf에 설정되어 있으면)
   - 또는 직접 입력: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`

   **"Channel"** 입력란:
   ```
   #splunk-alerts
   ```

   **"Message"** 입력란:
   ```
   $result.alert_text$
   ```

   **"Bot Name"** (선택):
   ```
   Splunk FortiGate Alert
   ```

   **"Icon"** (선택):
   - Emoji: `:fire:` 또는 `:rotating_light:`

4. 하단 **"Save"** 버튼 클릭

#### Step 6: 생성 확인
- 자동으로 Alerts 목록으로 이동
- `FAZ_Critical_Alerts` 이름이 목록에 보임
- Status 컬럼에 "Enabled" 표시

---

### 📦 Alert 2: FMG_Policy_Install

**같은 방식으로 New Alert 클릭 후:**

#### Search 탭:
- **Title:** `FMG_Policy_Install`
- **Description:** `FortiManager 정책 설치 이벤트`
- **Search:**
  ```
  index=fortianalyzer sourcetype=fw_log earliest=-5m latest=now | search (action=install OR msg="*install*policy*") | eval user_name=coalesce(user, "N/A") | eval src_ip=coalesce(srcip, src, "N/A") | eval message=coalesce(msg, "N/A") | eval alert_text="📦 *FMG Policy Install*\n사용자: ".user_name."\n출발지: ".src_ip."\n메시지: ".message | head 1 | table alert_text
  ```
- **Cron Schedule:** `*/5 * * * *`
- **Next**

#### Trigger Conditions 탭:
- Number of Results > 0
- **Next**

#### Trigger Actions 탭:
- Add Actions → Slack
- Channel: `#splunk-alerts`
- Message: `$result.alert_text$`
- **Save**

---

### ✏️ Alert 3: FMG_Policy_CRUD

#### Search 탭:
- **Title:** `FMG_Policy_CRUD`
- **Description:** `FortiManager 정책 CRUD 작업`
- **Search:**
  ```
  index=fortianalyzer sourcetype=fw_log earliest=-5m latest=now | search object="*policy*" operation IN (add,set,delete,create,modify,remove) | eval operation_type=coalesce(operation, action, "N/A") | eval user_name=coalesce(user, "N/A") | eval object_name=coalesce(object, "N/A") | eval message=coalesce(msg, "N/A") | eval alert_text="✏️ *FMG Policy CRUD*\n작업: ".operation_type."\n사용자: ".user_name."\n객체: ".object_name."\n메시지: ".message | head 1 | table alert_text
  ```
- **Cron Schedule:** `*/5 * * * *`

#### Trigger Conditions:
- Number of Results > 0

#### Trigger Actions:
- Slack → #splunk-alerts → `$result.alert_text$`

---

### 🔧 Alert 4: FMG_Object_CRUD

#### Search 탭:
- **Title:** `FMG_Object_CRUD`
- **Description:** `FortiManager 객체 CRUD 작업`
- **Search:**
  ```
  index=fortianalyzer sourcetype=fw_log earliest=-5m latest=now | search object IN (address,service,vip,addrgrp,servgrp) operation IN (add,set,delete,create,modify,remove) | eval operation_type=coalesce(operation, action, "N/A") | eval user_name=coalesce(user, "N/A") | eval object_type=coalesce(object, "N/A") | eval message=coalesce(msg, "N/A") | eval alert_text="🔧 *FMG Object CRUD*\n작업: ".operation_type."\n사용자: ".user_name."\n객체 유형: ".object_type."\n메시지: ".message | head 1 | table alert_text
  ```
- **Cron Schedule:** `*/5 * * * *`

#### Trigger Conditions:
- Number of Results > 0

#### Trigger Actions:
- Slack → #splunk-alerts → `$result.alert_text$`

---

### ⚠️ Alert 5: Security_High_Severity

#### Search 탭:
- **Title:** `Security_High_Severity`
- **Description:** `높은 심각도 보안 이벤트`
- **Search:**
  ```
  index=fortianalyzer sourcetype=fw_log earliest=-5m latest=now | search (severity=high OR level=high) | eval src_ip=coalesce(srcip, src, "N/A") | eval dst_ip=coalesce(dstip, dst, "N/A") | eval severity_level=coalesce(severity, level, "N/A") | eval message=coalesce(msg, "N/A") | eval alert_text="⚠️ *Security High Alert*\n출발지: ".src_ip."\n목적지: ".dst_ip."\n심각도: ".severity_level."\n메시지: ".message | head 1 | table alert_text
  ```
- **Cron Schedule:** `*/5 * * * *`

#### Trigger Conditions:
- Number of Results > 0

#### Trigger Actions:
- Slack → #splunk-alerts → `$result.alert_text$`

---

## Alert 관리

### ✅ Alert 켜기 (Enable)

1. **Settings → Searches, reports, and alerts**
2. Alert 목록에서 해당 Alert 이름 클릭
3. 우측 상단 **"Edit"** 버튼 클릭
4. **"Trigger Actions"** 탭 클릭
5. **Slack 체크박스 체크**
6. **"Save"** 클릭

### 🔴 Alert 끄기 (Disable)

1. 같은 방법으로 Edit 화면 진입
2. Trigger Actions 탭
3. **Slack 체크박스 해제**
4. Save

### 🧪 Alert 테스트

#### 방법 1: Run Test (권장)
1. Alert 편집 화면 (Edit)
2. Trigger Actions 탭
3. Slack 섹션 우측에 **"▶ Run"** 버튼 클릭
4. Slack 채널에서 테스트 메시지 확인

#### 방법 2: Trigger Manually
1. Alert 편집 화면
2. 하단 **"Trigger Actions"** 버튼 클릭
3. 확인 대화상자에서 **"Yes"** 클릭

#### 방법 3: Search 직접 실행
1. 상단 **"Search & Reporting"** 앱 클릭
2. Search 바에 다음 입력:
   ```
   | makeresults | eval alert_text="🧪 Test Alert\nTime: ".strftime(now(), "%Y-%m-%d %H:%M:%S") | table alert_text | sendalert slack param.channel="#splunk-alerts"
   ```
3. 실행 (돋보기 아이콘 또는 Enter)

### 📊 Alert 실행 이력 확인

1. **Settings → Searches, reports, and alerts**
2. Alert 이름 클릭
3. **"View Recent Alerts"** 링크 클릭
4. 실행 시간, 결과 개수, Status 확인

### 🔍 Alert 로그 확인

1. **Search & Reporting** 앱
2. Search 바에 입력:
   ```
   index=_internal source=*scheduler.log savedsearch_name="FAZ_Critical_Alerts" | table _time, savedsearch_name, status, result_count
   ```
3. 실행 시간, 성공/실패 여부 확인

---

## 트러블슈팅

### ❌ Slack 액션이 목록에 없음

**원인:** Slack Alert Plugin 미설치

**해결:**
```bash
# SSH 접속 후
ls /opt/splunk/etc/apps/ | grep slack

# slack_alerts 폴더 없으면 설치
cd /opt/splunk/etc/apps/
tar -xzf /path/to/slack-notification-alert_232.tgz
sudo /opt/splunk/bin/splunk restart
```

Web UI 새로고침 후 다시 확인

---

### ❌ Alert 생성은 되는데 Slack 메시지 안 옴

**원인 1: Slack Bot Token 미설정**

확인:
```bash
cat /opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf
```

없으면 생성:
```bash
sudo vi /opt/splunk/etc/apps/slack_alerts/local/alert_actions.conf

# 내용:
[slack]
param.token = xoxb-YOUR-SLACK-BOT-TOKEN
param.channel = #splunk-alerts

# 저장 후
sudo /opt/splunk/bin/splunk restart
```

**원인 2: Bot이 채널에 초대 안됨**

Slack에서:
```
/invite @your-bot-name
```

**원인 3: OAuth Scope 부족**

Slack App 설정에서 다음 권한 추가:
- `chat:write`
- `chat:write.public`
- `channels:read`

---

### ❌ Search 문법 오류

**증상:** Alert 저장 시 "Search is invalid" 에러

**해결:**
1. Search 바에서 직접 테스트:
   ```
   index=fortianalyzer sourcetype=fw_log earliest=-5m latest=now | head 10
   ```
2. 결과 나오는지 확인
3. 점진적으로 조건 추가해서 테스트

**자주 하는 실수:**
- `index=fw` 뒤에 시간 범위 필수 (`earliest=-5m latest=now`)
- 파이프(`|`) 앞뒤 공백 필요
- 큰따옴표(`"`) 안에 작은따옴표(`'`) 사용 불가 (역슬래시 이스케이프)

---

### ❌ Alert는 실행되는데 결과가 0개

**원인:** 실제 데이터가 없음

**확인:**
```
index=fortianalyzer earliest=-1h | stats count
```

count가 0이면:
1. Syslog 설정 확인
2. FortiAnalyzer/FortiManager가 Splunk로 로그 전송 중인지 확인
3. `index=fw`가 맞는지 확인 (다른 index면 변경)

---

### ❌ Cron Schedule 안 맞음

**증상:** 5분마다 실행 안 됨

**확인:**
```
*/5 * * * *
```
정확히 이 형식인지 확인 (공백, 별표 개수)

**실행 이력 확인:**
```
index=_internal source=*scheduler.log savedsearch_name="FAZ_Critical_Alerts" | stats count by _time
```

---

### 🆘 긴급 문제 해결

**모든 Alert 일시 중지:**
```bash
# SSH 접속
sudo /opt/splunk/bin/splunk disable app slack_alerts
sudo /opt/splunk/bin/splunk restart
```

**Alert 개별 삭제:**
1. Settings → Searches, reports, and alerts
2. Alert 이름 옆 체크박스 선택
3. 상단 **"Delete"** 버튼 클릭

**설정 초기화:**
```bash
sudo rm /opt/splunk/etc/apps/search/local/savedsearches.conf
sudo /opt/splunk/bin/splunk restart
```

---

## 📝 체크리스트

Alert 생성 완료 후 확인:

- [ ] Settings → Searches, reports, and alerts에서 5개 Alert 보임
- [ ] 각 Alert Status가 "Enabled"
- [ ] Alert 편집 화면에서 Slack 체크박스 체크됨
- [ ] Test 실행 시 Slack 채널에 메시지 옴
- [ ] Alert 실행 이력에 성공 기록 있음
- [ ] 실제 이벤트 발생 시 Slack 알림 수신

---

**작성일:** 2025-10-25
**대상:** Splunk Web UI 8000 포트
**참고:** `configs/SYSLOG_SLACK_ALERT_COMPLETE.conf`
