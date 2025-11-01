# Web UI에서 Slack 알림 만들기 (간단버전)

## 알림 1개 만드는 법 (5분)

### 1. Search & Reporting 앱 열기

### 2. 검색창에 쿼리 입력 후 실행
```spl
index=fortianalyzer sourcetype=fw_log severity=critical
```

### 3. "Save As" → "Alert" 클릭

### 4. 알림 설정

**Title:** `FAZ_Critical_Alerts`

**Alert type:** Scheduled

**Schedule:**
- Run every: `5 minutes`

**Trigger condition:**
- Number of Results
- is greater than `0`

**Trigger Actions:**
- Add Actions → **Slack**
- Channel: `#splunk-alerts`
- Message: (기본값 그대로)

### 5. Save 클릭

---

## 4개 알림 만들기 (반복)

같은 방법으로 4번 반복:

### 알림 1: Critical 이벤트
```spl
index=fortianalyzer sourcetype=fw_log severity=critical
```
Title: `FAZ_Critical_Alerts`

### 알림 2: 정책 설치
```spl
index=fortianalyzer sourcetype=fw_log action=install msg="*policy*"
```
Title: `FMG_Policy_Install`

### 알림 3: 설정 변경
```spl
index=fortianalyzer sourcetype=fw_log msg="*config*"
```
Title: `FMG_Policy_CRUD`

### 알림 4: 로그인
```spl
index=fortianalyzer sourcetype=fw_log action=login
```
Title: `FMG_Admin_Login`

---

## 끝

**ON/OFF:** Settings → Searches, reports, and alerts → Enable 체크박스
