# Web UI에서 sendalert 알림 만들기 (간단)

**Slack 설정 이미 되어 있음 → sendalert 사용**

---

## 알림 1개 만들기 (2분)

### 1. Search & Reporting 검색창에 쿼리 입력

```spl
index=fortianalyzer sourcetype=fw_log severity=critical
| head 10
| eval message="🔴 Critical Alert
출발지: ".coalesce(srcip, src, "N/A")."
목적지: ".coalesce(dstip, dst, "N/A")
| sendalert slack param.channel="#splunk-alerts" param.message=message
```

### 2. Save As → Alert

- **Title**: `FAZ_Critical_Alerts`
- **Alert type**: Scheduled
- **Schedule**: Every `5 minutes`
- **Trigger condition**: Number of Results > 0
- **Trigger Actions**: (아무것도 선택 안 함, sendalert가 쿼리에 이미 있음)

### 3. Save

---

## 4개 알림 쿼리

### 알림 1: Critical 이벤트
```spl
index=fortianalyzer sourcetype=fw_log severity=critical
| head 10
| eval message="🔴 FAZ Critical
출발지: ".coalesce(srcip, src, "N/A")."
목적지: ".coalesce(dstip, dst, "N/A")
| sendalert slack param.channel="#splunk-alerts" param.message=message
```

### 알림 2: 정책 설치
```spl
index=fortianalyzer sourcetype=fw_log (action=install OR msg="*policy*install*")
| head 10
| eval message="📦 FMG Policy Install
사용자: ".coalesce(user, "N/A")."
작업: ".coalesce(action, "N/A")
| sendalert slack param.channel="#splunk-alerts" param.message=message
```

### 알림 3: 설정 변경
```spl
index=fortianalyzer sourcetype=fw_log msg="*config*" (action=create OR action=update OR action=delete)
| head 10
| eval message="🔧 FMG Config Change
사용자: ".coalesce(user, "N/A")."
작업: ".coalesce(action, "N/A")
| sendalert slack param.channel="#splunk-alerts" param.message=message
```

### 알림 4: 로그인
```spl
index=fortianalyzer sourcetype=fw_log (action=login OR msg="*login*")
| head 10
| eval message="👤 Admin Login
사용자: ".coalesce(user, "N/A")."
출발지: ".coalesce(srcip, src, "N/A")
| sendalert slack param.channel="#splunk-alerts" param.message=message
```

---

## 테스트

### 즉시 테스트 (검색창에 입력)
```spl
| makeresults | eval message="테스트" | sendalert slack param.channel="#splunk-alerts" param.message=message
```

**Enter** → Slack 확인

---

## ON/OFF

**Settings → Searches, reports, and alerts → Enable 체크박스**

---

## 끝!

**sendalert가 쿼리 안에 있어서 Trigger Actions 설정 필요 없음!**
