# Syslog → Slack 알림 (초간단)

## Web UI에서 알림 1개 만들기 (1분)

### 1. Search & Reporting 검색창

```spl
index=fortianalyzer | head 10 | sendalert slack param.channel="#splunk-alerts" param.message="Syslog 이벤트 발생"
```

### 2. Save As → Alert

- Title: `Syslog_Alert`
- Schedule: `*/5 * * * *` (5분마다)
- Trigger: Number of Results > 0
- **Actions: 선택 안 함**
- Save

---

## 끝!

5분마다 Slack에 메시지 갑니다.

---

## 조건 추가하고 싶으면:

### Critical만:
```spl
index=fortianalyzer severity=critical | head 10 | sendalert slack param.channel="#splunk-alerts" param.message="Critical 이벤트"
```

### 특정 IP만:
```spl
index=fortianalyzer srcip="192.168.1.100" | head 10 | sendalert slack param.channel="#splunk-alerts" param.message="특정 IP 이벤트"
```

### 키워드 포함:
```spl
index=fortianalyzer msg="*error*" | head 10 | sendalert slack param.channel="#splunk-alerts" param.message="에러 발생"
```

---

**이게 전부입니다!**
