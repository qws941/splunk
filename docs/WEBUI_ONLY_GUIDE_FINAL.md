# Web UI만으로 Slack 알림 설정 (재시작 없음)

## 알림 1개 만들기 (2분)

### 1. Splunk Web → Search & Reporting

### 2. 검색창에 입력:

```spl
index=fortianalyzer sourcetype=fw_log severity=critical
| head 10
| eval message="🔴 Critical Alert"
| sendalert slack param.channel="#splunk-alerts" param.message=message
```

### 3. Save As → Alert

**Title**: `FAZ_Critical_Alerts`

**Alert type**: Scheduled

**Cron Expression**: `*/5 * * * *`

**Time Range**: Last 5 minutes

**Trigger Conditions**:
- Number of Results
- is greater than: 0

**Trigger Actions**: (선택 안 함!)

### 4. Save

---

## 4개 알림 쿼리 (복사-붙여넣기)

### 알림 1: FAZ_Critical_Alerts
```spl
index=fortianalyzer sourcetype=fw_log severity=critical | head 10 | eval src=coalesce(srcip,src,"N/A"), dst=coalesce(dstip,dst,"N/A"), msg="🔴 FAZ Critical: ".src." → ".dst | sendalert slack param.channel="#splunk-alerts" param.message=msg
```

### 알림 2: FMG_Policy_Install
```spl
index=fortianalyzer sourcetype=fw_log action=install | head 10 | eval msg="📦 FMG Policy Install: ".coalesce(user,"N/A") | sendalert slack param.channel="#splunk-alerts" param.message=msg
```

### 알림 3: FMG_Policy_CRUD
```spl
index=fortianalyzer sourcetype=fw_log msg="*config*" | head 10 | eval msg="🔧 FMG Config Change: ".coalesce(user,"N/A") | sendalert slack param.channel="#splunk-alerts" param.message=msg
```

### 알림 4: FMG_Admin_Login
```spl
index=fortianalyzer sourcetype=fw_log action=login | head 10 | eval msg="👤 Admin Login: ".coalesce(user,"N/A")." from ".coalesce(srcip,src,"N/A") | sendalert slack param.channel="#splunk-alerts" param.message=msg
```

---

## 테스트 (즉시 발송)

```spl
| makeresults | eval message="테스트" | sendalert slack param.channel="#splunk-alerts" param.message=message
```

**Enter → Slack 확인**

---

## 끝!

**재시작 없음, CLI 없음, 100% Web UI만 사용**
